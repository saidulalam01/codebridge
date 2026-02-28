"""Phase 7: Publisher — GitHub repo creation, pushing, and incremental updates."""

import os

from .utils import PROJECTS_DIR, log, run_cmd


class Publisher:
    """Handles GitHub repo creation and pushing."""

    def __init__(self, project_name, github_username=None):
        self.project_name = project_name
        self.output_path = PROJECTS_DIR / project_name
        self.github_username = github_username

    def check_gh_auth(self):
        """Check if GitHub CLI is authenticated.

        Returns dict with auth status.
        """
        try:
            result = run_cmd("gh auth status 2>&1", check=False)
            if "Logged in" in (result or ""):
                log("GitHub CLI is authenticated.")
                return {"authenticated": True, "details": result}
        except Exception:
            pass
        log("GitHub CLI is NOT authenticated. Run: gh auth login", "ERROR")
        return {"authenticated": False, "message": "Run: gh auth login"}

    def publish(self, repo_name=None):
        """Create repo and push.

        Returns dict with publish result.
        """
        repo_name = repo_name or self.project_name

        auth = self.check_gh_auth()
        if not auth["authenticated"]:
            return {"status": "failed", "reason": "GitHub CLI not authenticated"}

        log(f"Creating GitHub repo: {repo_name}")

        original_dir = os.getcwd()
        try:
            os.chdir(self.output_path)

            run_cmd("git init")
            run_cmd("git add .")
            run_cmd('git commit -m "Initial commit — anonymized project"')

            run_cmd(f'gh repo create {repo_name} --public --source=. --push')
            log(f"Published to GitHub: {repo_name}")
            return {"status": "published", "repo_name": repo_name}
        except Exception as e:
            log(f"Failed to publish: {e}", "ERROR")
            return {"status": "failed", "reason": str(e)}
        finally:
            os.chdir(original_dir)

    def update(self):
        """Stage all changes and return the diff for review. Does NOT commit.

        Requires .git and origin remote to exist.
        Returns dict with diff_stat, diff_full, and status.
        """
        auth = self.check_gh_auth()
        if not auth["authenticated"]:
            return {"status": "failed", "reason": "GitHub CLI not authenticated"}

        git_dir = self.output_path / ".git"
        if not git_dir.exists():
            return {
                "status": "failed",
                "reason": f"No .git directory in {self.output_path}. Use 'publish' for first-time publishing.",
            }

        original_dir = os.getcwd()
        try:
            os.chdir(self.output_path)

            remote = run_cmd("git remote get-url origin 2>/dev/null", check=False)
            if not remote or not remote.strip():
                return {"status": "failed", "reason": "No 'origin' remote configured."}

            run_cmd("git add -A")

            status_output = run_cmd("git status --porcelain", check=False)
            if not status_output or not status_output.strip():
                return {"status": "no_changes", "message": "No changes detected in anonymized output."}

            diff_stat = run_cmd("git diff --cached --stat", check=False) or ""
            diff_full = run_cmd("git diff --cached", check=False) or ""

            if len(diff_full) > 50000:
                diff_full = diff_full[:50000] + f"\n\n... [truncated, {len(diff_full)} total chars]"

            return {
                "status": "diff_ready",
                "diff_stat": diff_stat.strip(),
                "diff_full": diff_full,
                "remote": remote.strip(),
                "message": "Review the diff above. If clean, run 'update-push --confirm' to commit and push.",
            }
        except Exception as e:
            log(f"Failed to prepare update: {e}", "ERROR")
            return {"status": "failed", "reason": str(e)}
        finally:
            os.chdir(original_dir)

    def push_update(self, commit_message=None):
        """Commit staged changes and push to existing remote.

        Only call after reviewing the diff from update().
        Returns dict with push result.
        """
        auth = self.check_gh_auth()
        if not auth["authenticated"]:
            return {"status": "failed", "reason": "GitHub CLI not authenticated"}

        original_dir = os.getcwd()
        try:
            os.chdir(self.output_path)

            status_output = run_cmd("git status --porcelain", check=False)
            if not status_output or not status_output.strip():
                return {"status": "no_changes", "message": "Nothing to commit."}

            # Stage if not already staged
            run_cmd("git add -A")

            msg = commit_message or "Update anonymized project"
            run_cmd(f'git commit -m "{msg}"')

            # Try main first, fall back to master
            push_result = run_cmd("git push origin main 2>&1", check=False)
            if push_result and "error" in push_result.lower():
                push_result = run_cmd("git push origin master 2>&1", check=False)

            log("Update pushed to remote.")
            return {
                "status": "pushed",
                "commit_message": msg,
                "message": "Changes committed and pushed to remote.",
            }
        except Exception as e:
            log(f"Failed to push update: {e}", "ERROR")
            return {"status": "failed", "reason": str(e)}
        finally:
            os.chdir(original_dir)
