"""Phase 4: CodeBridge Anonymizer — Applies mapping to create an anonymized copy."""

import shutil
from pathlib import Path

from .utils import (
    PROJECTS_DIR, EXACT_REPLACE_EXTENSIONS, CONTEXTUAL_REPLACE_EXTENSIONS, log,
)


class CodeAnonymizer:
    """Applies the mapping to create an anonymized copy of the project."""

    def __init__(self, project_name, source_path, mapping):
        self.project_name = project_name
        self.source_path = Path(source_path)
        self.output_path = PROJECTS_DIR / project_name
        self.mapping = mapping
        self.changes_made = []

    def create_clean_copy(self, force=False):
        """Copy the project to output directory.

        Returns a dict with status info (no interactive prompts).
        Pass force=True to overwrite an existing output folder.
        """
        if self.output_path.exists():
            if not force:
                return {
                    "status": "exists",
                    "path": str(self.output_path),
                    "message": "Output folder already exists. Use --force to overwrite.",
                }
            shutil.rmtree(self.output_path)

        shutil.copytree(
            self.source_path,
            self.output_path,
            ignore=shutil.ignore_patterns(
                ".git", "__pycache__", "*.pyc", ".env",
                "node_modules", ".venv", "venv", "*.sqlite3",
            ),
        )
        log(f"Project copied to {self.output_path}")
        return {
            "status": "created",
            "path": str(self.output_path),
            "message": f"Clean copy created at {self.output_path}",
        }

    def apply_exact_replacements(self):
        """Apply exact string replacements (tables, columns, secrets).

        Returns dict with count of files changed and list of changed files.
        """
        all_replacements = {}
        all_replacements.update(self.mapping.get("tables", {}))
        all_replacements.update(self.mapping.get("columns", {}))
        all_replacements.update(self.mapping.get("secrets", {}))

        if not all_replacements:
            log("No exact replacements to apply.")
            return {"files_changed": 0, "files": []}

        # Sort by length (longest first) to avoid partial replacements
        sorted_replacements = sorted(
            all_replacements.items(), key=lambda x: len(x[0]), reverse=True
        )

        files_changed = 0
        for fpath in self.output_path.rglob("*"):
            if fpath.is_file() and fpath.suffix in EXACT_REPLACE_EXTENSIONS:
                try:
                    content = fpath.read_text(errors="ignore")
                    original = content
                    for old, new in sorted_replacements:
                        content = content.replace(old, new)
                    if content != original:
                        fpath.write_text(content)
                        files_changed += 1
                        self.changes_made.append(str(fpath.relative_to(self.output_path)))
                except Exception as e:
                    log(f"Error processing {fpath}: {e}", "WARN")

        log(f"Exact replacements applied to {files_changed} files.")
        return {"files_changed": files_changed, "files": list(self.changes_made)}

    def apply_contextual_replacements(self):
        """Apply business term replacements in comments and docs.

        Performs case-sensitive replacement first, then a lowercase pass
        to catch terms in SQL ILIKE patterns and other case variants.

        Returns dict with count of files changed.
        """
        terms = self.mapping.get("business_terms", {})
        if not terms:
            return {"files_changed": 0}

        sorted_terms = sorted(terms.items(), key=lambda x: len(x[0]), reverse=True)
        ignore_list = self.mapping.get("ignore", [])

        # Build lowercase variants for terms that differ in case
        lowercase_variants = []
        for old, new in sorted_terms:
            lower_old = old.lower()
            lower_new = new.lower()
            if lower_old != old and lower_old != lower_new:
                lowercase_variants.append((lower_old, lower_new))

        files_changed = 0
        for fpath in self.output_path.rglob("*"):
            if fpath.is_file() and fpath.suffix in CONTEXTUAL_REPLACE_EXTENSIONS:
                try:
                    content = fpath.read_text(errors="ignore")
                    original = content
                    for old, new in sorted_terms:
                        should_skip = False
                        for ignore_phrase in ignore_list:
                            if old.lower() in ignore_phrase.lower():
                                should_skip = True
                                break
                        if not should_skip:
                            content = content.replace(old, new)
                    # Second pass: lowercase variants for SQL ILIKE patterns etc.
                    for old_lower, new_lower in lowercase_variants:
                        content = content.replace(old_lower, new_lower)
                    if content != original:
                        fpath.write_text(content)
                        files_changed += 1
                except Exception as e:
                    log(f"Error in contextual replacement for {fpath}: {e}", "WARN")

        log(f"Contextual replacements applied to {files_changed} files.")
        return {"files_changed": files_changed}
