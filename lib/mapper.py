"""Phase 2: Mapping Builder — Creates and manages anonymization mappings."""

import json
from datetime import datetime
from pathlib import Path

from .utils import MAPPINGS_DIR, log


class MappingBuilder:
    """Builds and manages the anonymization mapping."""

    def __init__(self, project_name):
        self.project_name = project_name
        self.mapping = {
            "tables": {},
            "columns": {},
            "business_terms": {},
            "secrets": {},
            "ignore": [],
        }

    def add_table(self, original, replacement):
        self.mapping["tables"][original] = replacement

    def add_column(self, original, replacement):
        self.mapping["columns"][original] = replacement

    def add_business_term(self, original, replacement):
        self.mapping["business_terms"][original] = replacement

    def add_secret(self, original, replacement):
        self.mapping["secrets"][original] = replacement

    def add_ignore(self, term):
        self.mapping["ignore"].append(term)

    def load_from_json(self, json_mapping):
        """Load mapping from a JSON dict (from AI agent)."""
        self.mapping = json_mapping

    def to_json(self):
        """Export mapping as JSON dict."""
        return self.mapping

    def save(self):
        """Save mapping as markdown to mappings directory."""
        filepath = MAPPINGS_DIR / f"{self.project_name}.md"
        lines = [
            f"# Mapping: {self.project_name}",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "> WARNING: This file contains real names. NEVER push to GitHub.",
            "",
        ]

        if self.mapping["tables"]:
            lines.append("## Tables\n")
            lines.append("| Original | Replacement |")
            lines.append("|----------|-------------|")
            for orig, repl in sorted(self.mapping["tables"].items()):
                lines.append(f"| `{orig}` | `{repl}` |")
            lines.append("")

        if self.mapping["columns"]:
            lines.append("## Columns\n")
            lines.append("| Original | Replacement |")
            lines.append("|----------|-------------|")
            for orig, repl in sorted(self.mapping["columns"].items()):
                lines.append(f"| `{orig}` | `{repl}` |")
            lines.append("")

        if self.mapping["business_terms"]:
            lines.append("## Business Terms\n")
            lines.append("| Original | Replacement |")
            lines.append("|----------|-------------|")
            for orig, repl in sorted(self.mapping["business_terms"].items()):
                lines.append(f"| `{orig}` | `{repl}` |")
            lines.append("")

        if self.mapping["secrets"]:
            lines.append("## Secrets\n")
            lines.append("| Original Pattern | Replacement |")
            lines.append("|-----------------|-------------|")
            for orig, repl in sorted(self.mapping["secrets"].items()):
                lines.append(f"| `{orig}` | `{repl}` |")
            lines.append("")

        if self.mapping["ignore"]:
            lines.append("## Ignore List\n")
            for term in self.mapping["ignore"]:
                lines.append(f"- {term}")
            lines.append("")

        filepath.write_text("\n".join(lines))
        log(f"Mapping saved to {filepath}")
        return filepath

    def save_json(self):
        """Save mapping as JSON for machine consumption."""
        filepath = MAPPINGS_DIR / f"{self.project_name}.json"
        filepath.write_text(json.dumps(self.mapping, indent=2))
        log(f"JSON mapping saved to {filepath}")
        return filepath

    def load(self):
        """Check if existing mapping exists (markdown)."""
        filepath = MAPPINGS_DIR / f"{self.project_name}.md"
        if filepath.exists():
            log(f"Found existing mapping at {filepath}")
            return True
        return False

    def load_json(self):
        """Load mapping from JSON file if it exists."""
        filepath = MAPPINGS_DIR / f"{self.project_name}.json"
        if filepath.exists():
            self.mapping = json.loads(filepath.read_text())
            log(f"Loaded mapping from {filepath}")
            return True
        return False
