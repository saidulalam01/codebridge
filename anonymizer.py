#!/usr/bin/env python3
"""
anonymizer.py — CLI toolkit for the CodeBridge Agent

Each subcommand outputs structured JSON to stdout.
AI agent orchestrates the pipeline by calling these subcommands
and reasoning about the output.

Usage:
    python3 anonymizer.py scan /path/to/project
    python3 anonymizer.py suggest-mapping project-name
    python3 anonymizer.py save-mapping project-name --json '{...}'
    python3 anonymizer.py copy project-name /path/to/source [--force]
    python3 anonymizer.py apply project-name
    python3 anonymizer.py generate-supporting project-name --type webapp_db
    python3 anonymizer.py verify project-name
    python3 anonymizer.py verify-snippet project-name --file relative/path.py
    python3 anonymizer.py publish project-name [--repo-name name]
    python3 anonymizer.py status [project-name]

    # Update pipeline (for already-published projects)
    python3 anonymizer.py update-scan project-name /path/to/source
    python3 anonymizer.py update-apply project-name /path/to/source
    python3 anonymizer.py update-push project-name [--confirm] [--message "..."]
"""

import argparse
import json
import sys
from pathlib import Path

from lib.scanner import ProjectScanner
from lib.mapper import MappingBuilder
from lib.anonymize import CodeAnonymizer
from lib.sample_data import SampleDataGenerator
from lib.supporting import SupportingFileGenerator
from lib.verifier import Verifier
from lib.publisher import Publisher
from lib.status import StatusTracker
from lib.utils import (
    MAPPINGS_DIR, PROJECTS_DIR, output_json, log,
)


# ─── Subcommand Handlers ─────────────────────────────────────────────────────

def cmd_scan(args):
    """Scan a project and output JSON report."""
    project_path = Path(args.project_path).resolve()
    if not project_path.exists():
        output_json({"error": f"Path does not exist: {project_path}"})
        sys.exit(1)

    scanner = ProjectScanner(project_path)
    report = scanner.scan()

    # Cache the scan report for later commands
    project_name = args.name or project_path.name
    cache_path = MAPPINGS_DIR / f".scan-cache-{project_name}.json"
    cache_path.write_text(json.dumps(report, default=str))

    output_json(report)


def cmd_suggest_mapping(args):
    """Output detected items that need mapping (tables, columns, secrets).

    AI agent reads this and suggests replacement names.
    """
    # Try to load cached scan report
    cache_path = MAPPINGS_DIR / f".scan-cache-{args.project_name}.json"
    if not cache_path.exists():
        output_json({"error": f"No scan cache for '{args.project_name}'. Run 'scan' first."})
        sys.exit(1)

    report = json.loads(cache_path.read_text())

    # Compile items needing mapping
    output_json({
        "project_name": args.project_name,
        "project_type": report.get("project_type"),
        "items_to_map": {
            "tables": report.get("sql", {}).get("tables", []),
            "columns": report.get("sql", {}).get("columns", []),
            "secrets": [
                {"pattern": s["pattern"], "file": s["file"], "line": s["line"]}
                for s in report.get("secrets", {}).get("items", [])
            ],
        },
        "context_snippets": report.get("context_snippets", []),
        "instructions": (
            "Review these items and suggest replacement names. "
            "Then use 'save-mapping' to save the mapping."
        ),
    })


def cmd_save_mapping(args):
    """Save a mapping from JSON input."""
    try:
        mapping = json.loads(args.json)
    except json.JSONDecodeError as e:
        output_json({"error": f"Invalid JSON: {e}"})
        sys.exit(1)

    builder = MappingBuilder(args.project_name)
    builder.load_from_json(mapping)

    md_path = builder.save()
    json_path = builder.save_json()

    output_json({
        "status": "saved",
        "markdown_path": str(md_path),
        "json_path": str(json_path),
        "summary": {
            "tables": len(mapping.get("tables", {})),
            "columns": len(mapping.get("columns", {})),
            "business_terms": len(mapping.get("business_terms", {})),
            "secrets": len(mapping.get("secrets", {})),
            "ignore": len(mapping.get("ignore", [])),
        },
    })


def cmd_copy(args):
    """Create a clean copy of the source project."""
    source_path = Path(args.source_path).resolve()
    if not source_path.exists():
        output_json({"error": f"Source path does not exist: {source_path}"})
        sys.exit(1)

    # Load mapping (needed by CodeAnonymizer init, but copy doesn't use it)
    json_path = MAPPINGS_DIR / f"{args.project_name}.json"
    if json_path.exists():
        mapping = json.loads(json_path.read_text())
    else:
        mapping = {}

    anonymizer = CodeAnonymizer(args.project_name, source_path, mapping)
    result = anonymizer.create_clean_copy(force=args.force)
    output_json(result)


def cmd_apply(args):
    """Apply the mapping to the clean copy."""
    json_path = MAPPINGS_DIR / f"{args.project_name}.json"
    if not json_path.exists():
        output_json({"error": f"No mapping found for '{args.project_name}'. Run 'save-mapping' first."})
        sys.exit(1)

    project_path = PROJECTS_DIR / args.project_name
    if not project_path.exists():
        output_json({"error": f"No clean copy found. Run 'copy' first."})
        sys.exit(1)

    mapping = json.loads(json_path.read_text())

    # Source path doesn't matter for apply — we work on the copy
    anonymizer = CodeAnonymizer(args.project_name, project_path, mapping)
    anonymizer.output_path = project_path  # Already the copy

    exact_result = anonymizer.apply_exact_replacements()
    contextual_result = anonymizer.apply_contextual_replacements()

    output_json({
        "status": "applied",
        "exact_replacements": exact_result,
        "contextual_replacements": contextual_result,
        "total_files_changed": exact_result["files_changed"] + contextual_result["files_changed"],
    })


def cmd_generate_supporting(args):
    """Generate supporting files (.gitignore, README, etc.)."""
    project_path = PROJECTS_DIR / args.project_name
    if not project_path.exists():
        output_json({"error": f"No clean copy found for '{args.project_name}'."})
        sys.exit(1)

    generator = SupportingFileGenerator(args.project_name, args.type)
    result = generator.generate_all()
    output_json(result)


def cmd_verify(args):
    """Run verification checklist + prepare review batch for AI agent."""
    project_path = PROJECTS_DIR / args.project_name
    if not project_path.exists():
        output_json({"error": f"No clean copy found for '{args.project_name}'."})
        sys.exit(1)

    # Load scan report and mapping
    scan_cache = MAPPINGS_DIR / f".scan-cache-{args.project_name}.json"
    json_mapping = MAPPINGS_DIR / f"{args.project_name}.json"

    scan_report = json.loads(scan_cache.read_text()) if scan_cache.exists() else {}
    mapping = json.loads(json_mapping.read_text()) if json_mapping.exists() else {}

    verifier = Verifier(args.project_name, scan_report, mapping)
    verify_result = verifier.verify()
    review_batch = verifier.get_review_batch(batch_size=args.batch_size)

    output_json({
        "verification": verify_result,
        "review_batch": review_batch,
    })


def cmd_verify_snippet(args):
    """Output a specific file from the anonymized project for AI agent to review."""
    project_path = PROJECTS_DIR / args.project_name
    file_path = project_path / args.file

    if not file_path.exists():
        output_json({"error": f"File not found: {args.file}"})
        sys.exit(1)

    try:
        content = file_path.read_text(errors="ignore")
        output_json({
            "file": args.file,
            "content": content,
            "size": len(content),
            "lines": content.count("\n") + 1,
        })
    except Exception as e:
        output_json({"error": str(e)})
        sys.exit(1)


def cmd_publish(args):
    """Publish to GitHub."""
    project_path = PROJECTS_DIR / args.project_name
    if not project_path.exists():
        output_json({"error": f"No clean copy found for '{args.project_name}'."})
        sys.exit(1)

    publisher = Publisher(args.project_name)
    result = publisher.publish(args.repo_name or args.project_name)
    output_json(result)


def cmd_status(args):
    """Show current status."""
    if args.project_name:
        tracker = StatusTracker(args.project_name)
        result = tracker.get_status()
    else:
        # Show all status
        from lib.utils import STATUS_FILE
        if STATUS_FILE.exists():
            result = {"content": STATUS_FILE.read_text()}
        else:
            result = {"content": "No status file found."}

    output_json(result)


def cmd_generate_sample_data(args):
    """Generate sample data seed script."""
    json_path = MAPPINGS_DIR / f"{args.project_name}.json"
    mapping = json.loads(json_path.read_text()) if json_path.exists() else {}

    generator = SampleDataGenerator(args.project_name, mapping)
    result = generator.generate_seed_script()
    output_json(result)


# ─── Update Pipeline Handlers ─────────────────────────────────────────────────

def cmd_update_scan(args):
    """Re-scan original source and diff against existing mapping."""
    source_path = Path(args.source_path).resolve()
    if not source_path.exists():
        output_json({"error": f"Source path does not exist: {source_path}"})
        sys.exit(1)

    project_path = PROJECTS_DIR / args.project_name
    if not project_path.exists():
        output_json({"error": f"No published project at {project_path}. Use the full pipeline for first-time anonymization."})
        sys.exit(1)

    json_path = MAPPINGS_DIR / f"{args.project_name}.json"
    if not json_path.exists():
        output_json({"error": f"No mapping found at {json_path}. Cannot diff without existing mapping."})
        sys.exit(1)

    git_dir = project_path / ".git"
    if not git_dir.exists():
        output_json({"error": f"No .git directory in {project_path}. Project must be published first."})
        sys.exit(1)

    # Run fresh scan on the original source
    scanner = ProjectScanner(source_path)
    scan_report = scanner.scan()

    # Diff against existing mapping
    from lib.differ import UpdateDiffer
    differ = UpdateDiffer(args.project_name, scan_report)
    diff_result = differ.diff()

    # Save updated scan cache AFTER diffing (so next diff compares against this scan)
    cache_path = MAPPINGS_DIR / f".scan-cache-{args.project_name}.json"
    cache_path.write_text(json.dumps(scan_report, default=str))

    if diff_result.get("has_new_items"):
        action = "New items detected. Update the mapping with 'save-mapping' before running 'update-apply'."
        instructions = (
            "Review the new items above. Design mappings for any real tables/columns/secrets. "
            "Add noise items to the 'ignore' list. Then use 'save-mapping' to update. "
            "After mapping is updated, run 'update-apply'."
        )
    else:
        action = "No new items. Mapping is current."
        instructions = "Proceed to 'update-apply' to re-copy and re-anonymize with the existing mapping."

    output_json({
        "scan_summary": {
            "files_scanned": scan_report.get("files_scanned", 0),
            "total_files": scan_report.get("total_files", 0),
            "secrets_found": scan_report.get("secrets", {}).get("count", 0),
            "tables_found": scan_report.get("sql", {}).get("table_count", 0),
            "columns_found": scan_report.get("sql", {}).get("column_count", 0),
        },
        "diff": diff_result,
        "action_required": action,
        "instructions": instructions,
    })


def cmd_update_apply(args):
    """Re-copy source (preserving .git) and re-apply full mapping."""
    source_path = Path(args.source_path).resolve()
    if not source_path.exists():
        output_json({"error": f"Source path does not exist: {source_path}"})
        sys.exit(1)

    project_path = PROJECTS_DIR / args.project_name
    json_path = MAPPINGS_DIR / f"{args.project_name}.json"

    if not json_path.exists():
        output_json({"error": f"No mapping found for '{args.project_name}'."})
        sys.exit(1)

    if not project_path.exists():
        output_json({"error": f"No project directory at {project_path}."})
        sys.exit(1)

    git_dir = project_path / ".git"
    if not git_dir.exists():
        output_json({"error": "No .git directory. Project must be published first."})
        sys.exit(1)

    import tempfile
    import shutil

    # Back up .git to temp location before re-copy destroys it
    git_backup_parent = Path(tempfile.mkdtemp())
    git_backup = git_backup_parent / ".git"
    try:
        shutil.move(str(git_dir), str(git_backup))
        log(f"Backed up .git to {git_backup}")

        # Delete old copy and re-copy fresh from source
        mapping = json.loads(json_path.read_text())
        anonymizer = CodeAnonymizer(args.project_name, source_path, mapping)
        copy_result = anonymizer.create_clean_copy(force=True)

        # Restore .git
        shutil.move(str(git_backup), str(project_path / ".git"))
        log("Restored .git directory")

        # Re-apply full mapping
        anonymizer.output_path = project_path
        exact_result = anonymizer.apply_exact_replacements()
        contextual_result = anonymizer.apply_contextual_replacements()

        # Run full verification
        scan_cache = MAPPINGS_DIR / f".scan-cache-{args.project_name}.json"
        scan_report = {}
        if scan_cache.exists():
            try:
                scan_report = json.loads(scan_cache.read_text())
            except (json.JSONDecodeError, OSError):
                pass

        verifier = Verifier(args.project_name, scan_report, mapping)
        verify_result = verifier.verify()
        review_batch = verifier.get_review_batch(batch_size=args.batch_size)

        output_json({
            "copy": copy_result,
            "exact_replacements": exact_result,
            "contextual_replacements": contextual_result,
            "total_files_changed": exact_result["files_changed"] + contextual_result["files_changed"],
            "verification": verify_result,
            "review_batch": review_batch,
            "next_step": (
                "Review verification results and the review batch above. "
                "Do the Manual Fixup Pass (Step 4.5). "
                "When clean, run 'update-push' to see the diff before pushing."
            ),
        })
    except Exception as e:
        # If something went wrong, try to restore .git if it's still in temp
        if git_backup.exists() and not (project_path / ".git").exists():
            if project_path.exists():
                shutil.move(str(git_backup), str(project_path / ".git"))
                log("Restored .git after error")
        output_json({"error": f"Update-apply failed: {e}"})
        sys.exit(1)
    finally:
        # Clean up temp directory
        if git_backup_parent.exists():
            shutil.rmtree(git_backup_parent, ignore_errors=True)


def cmd_update_push(args):
    """Show diff for review, or commit and push if --confirm is set."""
    project_path = PROJECTS_DIR / args.project_name
    if not project_path.exists():
        output_json({"error": f"No project at {project_path}."})
        sys.exit(1)

    publisher = Publisher(args.project_name)

    if args.confirm:
        result = publisher.push_update(commit_message=args.message)
    else:
        result = publisher.update()

    output_json(result)


# ─── CLI Setup ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="CodeBridge Toolkit — CLI for AI agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 anonymizer.py scan /path/to/project --name my-project
  python3 anonymizer.py suggest-mapping my-project
  python3 anonymizer.py save-mapping my-project --json '{"tables": {...}}'
  python3 anonymizer.py copy my-project /path/to/source --force
  python3 anonymizer.py apply my-project
  python3 anonymizer.py verify my-project
  python3 anonymizer.py publish my-project --repo-name my-public-repo
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # scan
    p_scan = subparsers.add_parser("scan", help="Scan a project for sensitive content")
    p_scan.add_argument("project_path", help="Path to the project to scan")
    p_scan.add_argument("--name", help="Project name (default: directory name)")

    # suggest-mapping
    p_suggest = subparsers.add_parser("suggest-mapping", help="Show items needing mapping")
    p_suggest.add_argument("project_name", help="Project name (must have been scanned first)")

    # save-mapping
    p_save = subparsers.add_parser("save-mapping", help="Save a mapping from JSON")
    p_save.add_argument("project_name", help="Project name")
    p_save.add_argument("--json", required=True, help="JSON mapping string")

    # copy
    p_copy = subparsers.add_parser("copy", help="Create clean copy of source project")
    p_copy.add_argument("project_name", help="Project name")
    p_copy.add_argument("source_path", help="Path to the source project")
    p_copy.add_argument("--force", action="store_true", help="Overwrite existing output")

    # apply
    p_apply = subparsers.add_parser("apply", help="Apply mapping to the clean copy")
    p_apply.add_argument("project_name", help="Project name")

    # generate-supporting
    p_support = subparsers.add_parser("generate-supporting", help="Generate supporting files")
    p_support.add_argument("project_name", help="Project name")
    p_support.add_argument("--type", required=True, help="Project type (e.g., webapp_db)")

    # generate-sample-data
    p_sample = subparsers.add_parser("generate-sample-data", help="Generate sample data seed script")
    p_sample.add_argument("project_name", help="Project name")

    # verify
    p_verify = subparsers.add_parser("verify", help="Run verification + prepare review batch")
    p_verify.add_argument("project_name", help="Project name")
    p_verify.add_argument("--batch-size", type=int, default=5, help="Files for semantic review (default: 5)")

    # verify-snippet
    p_snippet = subparsers.add_parser("verify-snippet", help="Output a file for AI agent to review")
    p_snippet.add_argument("project_name", help="Project name")
    p_snippet.add_argument("--file", required=True, help="Relative path to file in anonymized project")

    # publish
    p_publish = subparsers.add_parser("publish", help="Publish to GitHub")
    p_publish.add_argument("project_name", help="Project name")
    p_publish.add_argument("--repo-name", help="GitHub repo name (default: project name)")

    # status
    p_status = subparsers.add_parser("status", help="Show current status")
    p_status.add_argument("project_name", nargs="?", help="Project name (optional)")

    # update-scan
    p_uscan = subparsers.add_parser("update-scan", help="Re-scan source and diff against existing mapping")
    p_uscan.add_argument("project_name", help="Project name (must be already published)")
    p_uscan.add_argument("source_path", help="Path to the original source project")

    # update-apply
    p_uapply = subparsers.add_parser("update-apply", help="Re-copy and re-apply mapping for an update")
    p_uapply.add_argument("project_name", help="Project name")
    p_uapply.add_argument("source_path", help="Path to the original source project")
    p_uapply.add_argument("--batch-size", type=int, default=5, help="Files for semantic review (default: 5)")

    # update-push
    p_upush = subparsers.add_parser("update-push", help="Show diff and optionally push update")
    p_upush.add_argument("project_name", help="Project name")
    p_upush.add_argument("--confirm", action="store_true", help="Actually commit and push (default: only show diff)")
    p_upush.add_argument("--message", default=None, help="Custom commit message")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Dispatch to handler
    handlers = {
        "scan": cmd_scan,
        "suggest-mapping": cmd_suggest_mapping,
        "save-mapping": cmd_save_mapping,
        "copy": cmd_copy,
        "apply": cmd_apply,
        "generate-supporting": cmd_generate_supporting,
        "generate-sample-data": cmd_generate_sample_data,
        "verify": cmd_verify,
        "verify-snippet": cmd_verify_snippet,
        "publish": cmd_publish,
        "status": cmd_status,
        "update-scan": cmd_update_scan,
        "update-apply": cmd_update_apply,
        "update-push": cmd_update_push,
    }

    handler = handlers.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
