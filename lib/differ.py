"""Update Differ — Compares a fresh scan against an existing mapping to find gaps."""

import json
from pathlib import Path

from .utils import MAPPINGS_DIR, log


class UpdateDiffer:
    """Compares a fresh scan report against an existing mapping to find unmapped items."""

    def __init__(self, project_name, scan_report):
        self.project_name = project_name
        self.scan_report = scan_report
        self.mapping = self._load_mapping()

    def _load_mapping(self):
        """Load the existing mapping JSON."""
        json_path = MAPPINGS_DIR / f"{self.project_name}.json"
        if not json_path.exists():
            return None
        return json.loads(json_path.read_text())

    def diff(self):
        """Compare scan results against existing mapping.

        Returns dict with new/unmapped items and file changes.
        """
        if self.mapping is None:
            return {"error": f"No mapping found for '{self.project_name}'."}

        # Load previous scan cache for file comparison
        prev_cache_path = MAPPINGS_DIR / f".scan-cache-{self.project_name}.json"
        prev_scan = {}
        if prev_cache_path.exists():
            try:
                prev_scan = json.loads(prev_cache_path.read_text())
            except (json.JSONDecodeError, OSError):
                pass

        mapped_tables = set(self.mapping.get("tables", {}).keys())
        mapped_columns = set(self.mapping.get("columns", {}).keys())
        mapped_secrets = set(self.mapping.get("secrets", {}).keys())
        ignored = set(self.mapping.get("ignore", []))
        all_known = mapped_tables | mapped_columns | mapped_secrets | ignored

        # --- New tables ---
        scan_tables = set(self.scan_report.get("sql", {}).get("tables", []))
        new_tables = sorted(scan_tables - all_known)

        # --- New columns ---
        scan_columns = set(self.scan_report.get("sql", {}).get("columns", []))
        new_columns = sorted(scan_columns - all_known)

        # --- New secrets ---
        new_secrets = []
        for s in self.scan_report.get("secrets", {}).get("items", []):
            content_key = s["content"][:120]
            pattern = s.get("pattern", "")
            if content_key not in mapped_secrets and pattern not in ignored:
                new_secrets.append({
                    "file": s["file"],
                    "line": s["line"],
                    "pattern": pattern,
                    "content": content_key,
                })

        # --- File changes ---
        prev_files = set(prev_scan.get("file_list", []))
        curr_files = set(self.scan_report.get("file_list", []))
        added_files = sorted(curr_files - prev_files)
        removed_files = sorted(prev_files - curr_files)

        has_new = bool(new_tables or new_columns or new_secrets)

        summary_parts = []
        if new_tables:
            summary_parts.append(f"{len(new_tables)} new table(s)")
        if new_columns:
            summary_parts.append(f"{len(new_columns)} new column(s)")
        if new_secrets:
            summary_parts.append(f"{len(new_secrets)} new secret(s)")
        if added_files:
            summary_parts.append(f"{len(added_files)} file(s) added")
        if removed_files:
            summary_parts.append(f"{len(removed_files)} file(s) removed")
        if not summary_parts:
            summary_parts.append("No new items detected — mapping is current")

        return {
            "new_tables": new_tables,
            "new_columns": new_columns,
            "new_secrets": new_secrets,
            "added_files": added_files,
            "removed_files": removed_files,
            "has_new_items": has_new,
            "summary": ", ".join(summary_parts),
            "existing_mapping_stats": {
                "tables": len(self.mapping.get("tables", {})),
                "columns": len(self.mapping.get("columns", {})),
                "business_terms": len(self.mapping.get("business_terms", {})),
                "secrets": len(self.mapping.get("secrets", {})),
                "ignore": len(self.mapping.get("ignore", [])),
            },
        }
