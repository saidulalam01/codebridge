"""Phase 1: Project Scanner — Detects secrets, SQL identifiers, and project type."""

import os
import re
from pathlib import Path

from .utils import (
    SECRET_PATTERNS, SKIP_DIRS, SKIP_EXTENSIONS, log,
)


class ProjectScanner:
    """Scans a project directory for sensitive content and detects project type."""

    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.secrets_found = []
        self.table_names = []
        self.business_terms = []
        self.project_type = None
        self.files_scanned = 0
        self.all_files = []

    def scan(self):
        """Run the full scan. Returns a JSON-serializable report dict."""
        log("Starting scan...")
        self._collect_files()
        self._detect_project_type()
        self._scan_for_secrets()
        self._scan_for_sql_identifiers()
        log(f"Scan complete. {self.files_scanned} files scanned.")
        return self.get_report()

    def _collect_files(self):
        """Collect all scannable files."""
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in files:
                fpath = Path(root) / fname
                if fpath.suffix.lower() not in SKIP_EXTENSIONS:
                    self.all_files.append(fpath)

    def _detect_project_type(self):
        """Detect what kind of project this is."""
        file_names = {f.name for f in self.all_files}
        file_contents_hint = set()

        for f in self.all_files:
            if f.suffix == ".py":
                try:
                    content = f.read_text(errors="ignore")[:5000]
                    file_contents_hint.add(content)
                except Exception:
                    pass

        has_streamlit = any("streamlit" in c for c in file_contents_hint)
        has_sql = any(
            kw in c.upper()
            for c in file_contents_hint
            for kw in ["SELECT ", "INSERT ", "CREATE TABLE", "pd.read_sql"]
        )
        has_fastapi = any("fastapi" in c.lower() for c in file_contents_hint)
        has_flask = any("flask" in c.lower() for c in file_contents_hint)
        has_notebook = any(f.suffix == ".ipynb" for f in self.all_files)
        has_django = "manage.py" in file_names

        if has_streamlit and has_sql:
            self.project_type = "webapp_db"
        elif has_streamlit:
            self.project_type = "streamlit"
        elif has_fastapi:
            self.project_type = "fastapi"
        elif has_flask:
            self.project_type = "flask"
        elif has_django:
            self.project_type = "django"
        elif has_notebook:
            self.project_type = "notebook"
        elif has_sql:
            self.project_type = "script_db"
        else:
            self.project_type = "pure_python"

        log(f"Detected project type: {self.project_type}")

    def _scan_for_secrets(self):
        """Scan files for secrets and credentials."""
        for fpath in self.all_files:
            try:
                content = fpath.read_text(errors="ignore")
                self.files_scanned += 1
                for line_num, line in enumerate(content.splitlines(), 1):
                    for pattern in SECRET_PATTERNS:
                        if pattern.lower() in line.lower():
                            self.secrets_found.append({
                                "file": str(fpath.relative_to(self.project_path)),
                                "line": line_num,
                                "pattern": pattern,
                                "content": line.strip()[:120],
                            })
            except Exception:
                pass

    def _scan_for_sql_identifiers(self):
        """Scan for SQL table and column names."""
        sql_table_pattern = re.compile(
            r'(?:FROM|JOIN|INTO|UPDATE|TABLE)\s+([a-zA-Z_][a-zA-Z0-9_.]*)',
            re.IGNORECASE,
        )
        sql_column_pattern = re.compile(
            r'(?:SELECT|WHERE|AND|OR|ON|SET|ORDER BY|GROUP BY)\s+([a-zA-Z_][a-zA-Z0-9_.]*)',
            re.IGNORECASE,
        )

        found_tables = set()
        found_columns = set()

        for fpath in self.all_files:
            try:
                content = fpath.read_text(errors="ignore")
                for match in sql_table_pattern.finditer(content):
                    name = match.group(1)
                    if name.upper() not in ("SELECT", "FROM", "WHERE", "SET", "AND", "OR"):
                        found_tables.add(name)
                for match in sql_column_pattern.finditer(content):
                    name = match.group(1)
                    if "." in name or len(name) > 3:
                        found_columns.add(name)
            except Exception:
                pass

        self.table_names = sorted(found_tables)
        self.column_names = sorted(found_columns)
        log(f"Found {len(found_tables)} potential table names, {len(found_columns)} column references")

    def _get_context_snippets(self):
        """Get surrounding lines for each secret, giving AI agent context to reason about."""
        snippets = []
        seen = set()
        for secret in self.secrets_found:
            # Deduplicate by file+line
            key = (secret["file"], secret["line"])
            if key in seen:
                continue
            seen.add(key)

            fpath = self.project_path / secret["file"]
            try:
                lines = fpath.read_text(errors="ignore").splitlines()
                line_num = secret["line"] - 1  # 0-indexed
                start = max(0, line_num - 2)
                end = min(len(lines), line_num + 3)
                snippets.append({
                    "file": secret["file"],
                    "detected": secret["pattern"],
                    "line_range": [start + 1, end],
                    "content": "\n".join(lines[start:end]),
                })
            except Exception:
                pass
        return snippets

    def get_report(self):
        """Generate scan report as a JSON-serializable dict."""
        return {
            "project_path": str(self.project_path),
            "project_type": self.project_type,
            "files_scanned": self.files_scanned,
            "total_files": len(self.all_files),
            "secrets": {
                "count": len(self.secrets_found),
                "items": self.secrets_found,
            },
            "sql": {
                "tables": self.table_names,
                "table_count": len(self.table_names),
                "columns": getattr(self, "column_names", []),
                "column_count": len(getattr(self, "column_names", [])),
            },
            "file_list": [str(f.relative_to(self.project_path)) for f in self.all_files],
            "context_snippets": self._get_context_snippets(),
        }
