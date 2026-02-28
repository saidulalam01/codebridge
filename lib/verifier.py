"""Phase 6: Verifier — Pre-publish safety checklist + semantic review support."""

from .utils import PROJECTS_DIR, SECRET_PATTERNS, log


class Verifier:
    """Runs the pre-publish checklist against the anonymized project."""

    def __init__(self, project_name, scan_report, mapping):
        self.project_name = project_name
        self.output_path = PROJECTS_DIR / project_name
        self.scan_report = scan_report
        self.mapping = mapping
        self.issues = []

    def verify(self):
        """Run all verification checks.

        Returns a structured dict (not just a bool) so AI agent can reason about results.
        """
        log("Running verification checklist...")
        self._check_secrets()
        self._check_original_names()
        self._check_env_files()

        if self.issues:
            log(f"VERIFICATION FAILED — {len(self.issues)} issues found:", "ERROR")
            for issue in self.issues:
                log(f"  - {issue}", "ERROR")
        else:
            log("VERIFICATION PASSED — no issues found.")

        return {
            "passed": len(self.issues) == 0,
            "issue_count": len(self.issues),
            "issues": self.issues,
        }

    def get_review_batch(self, batch_size=5):
        """Return priority files for AI agent to review semantically.

        These are files most likely to contain leaks that regex missed:
        1. Files containing SQL queries
        2. Files with the most content (more opportunity for leaks)
        3. Documentation files (comments, README)
        4. Configuration files
        """
        priority_files = []
        file_scores = []

        for fpath in self.output_path.rglob("*"):
            if not fpath.is_file() or ".git" in str(fpath):
                continue
            if fpath.suffix not in (".py", ".md", ".sql", ".txt", ".yaml", ".json", ".html"):
                continue

            try:
                content = fpath.read_text(errors="ignore")
                score = 0
                rel_path = str(fpath.relative_to(self.output_path))

                # SQL files and files with SQL score highest
                if fpath.suffix == ".sql":
                    score += 10
                if any(kw in content.upper() for kw in ["SELECT ", "FROM ", "INSERT ", "JOIN "]):
                    score += 8

                # Larger files have more opportunity for leaks
                score += min(len(content) // 1000, 5)

                # Documentation files
                if fpath.suffix in (".md", ".txt", ".html"):
                    score += 3

                # Config files
                if fpath.suffix in (".yaml", ".json", ".toml"):
                    score += 2

                file_scores.append((score, rel_path, content))
            except Exception:
                pass

        # Sort by score descending, take top batch_size
        file_scores.sort(key=lambda x: x[0], reverse=True)

        for score, rel_path, content in file_scores[:batch_size]:
            # Truncate very large files
            if len(content) > 5000:
                content = content[:5000] + f"\n\n... [truncated, {len(content)} chars total]"

            priority_files.append({
                "path": rel_path,
                "content": content,
                "priority_score": score,
                "reason": self._score_reason(score, rel_path),
            })

        return {
            "files_for_review": priority_files,
            "total_files": len(file_scores),
            "batch_size": batch_size,
        }

    def _score_reason(self, score, path):
        """Explain why this file is high priority for review."""
        reasons = []
        if path.endswith(".sql"):
            reasons.append("SQL file")
        if score >= 8:
            reasons.append("contains SQL queries")
        if path.endswith((".md", ".txt")):
            reasons.append("documentation")
        if score >= 5:
            reasons.append("large file")
        return ", ".join(reasons) if reasons else "general review"

    def _check_secrets(self):
        """Search for any remaining secret patterns in all text files."""
        _SECRET_CHECK_EXTS = (
            ".py", ".sql", ".md", ".yaml", ".json", ".jsonl",
            ".toml", ".sh", ".html", ".txt", ".cfg", ".ini",
        )
        for fpath in self.output_path.rglob("*"):
            if fpath.is_file() and fpath.suffix in _SECRET_CHECK_EXTS:
                try:
                    content = fpath.read_text(errors="ignore").lower()
                    for pattern in SECRET_PATTERNS:
                        if pattern.lower() in content:
                            if fpath.name in (".env.example", "requirements.txt"):
                                continue
                            self.issues.append(
                                f"Possible secret pattern '{pattern}' in {fpath.relative_to(self.output_path)}"
                            )
                except Exception:
                    pass

    def _check_original_names(self):
        """Search for original table/column/business names — case-insensitive."""
        all_originals = set()
        all_originals.update(self.mapping.get("tables", {}).keys())
        all_originals.update(self.mapping.get("columns", {}).keys())
        all_originals.update(self.mapping.get("business_terms", {}).keys())

        _NAME_CHECK_EXTS = (".py", ".sql", ".md", ".jsonl", ".sh", ".html", ".txt")
        for fpath in self.output_path.rglob("*"):
            if fpath.is_file() and fpath.suffix in _NAME_CHECK_EXTS:
                try:
                    content = fpath.read_text(errors="ignore")
                    content_lower = content.lower()
                    for original in all_originals:
                        if len(original) > 3:
                            # Check both exact case and lowercase
                            if original in content or original.lower() in content_lower:
                                self.issues.append(
                                    f"Original term '{original}' still in {fpath.relative_to(self.output_path)}"
                                )
                except Exception:
                    pass

    def _check_env_files(self):
        """Make sure no .env file exists in output."""
        env_file = self.output_path / ".env"
        if env_file.exists():
            self.issues.append(".env file exists in output — must be removed")

        gitignore = self.output_path / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text()
            if ".env" not in content:
                self.issues.append(".gitignore does not exclude .env")
        else:
            self.issues.append("No .gitignore file found")
