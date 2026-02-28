"""Phase 8: Status Tracker — Updates status.md for session handoff."""

from datetime import datetime

from .utils import STATUS_FILE, log


class StatusTracker:
    """Updates status.md for session handoff."""

    def __init__(self, project_name):
        self.project_name = project_name

    def update(self, step, status, notes=""):
        """Update the status file.

        Returns dict confirming the update.
        """
        content = STATUS_FILE.read_text() if STATUS_FILE.exists() else "# Project Status\n"

        if f"## {self.project_name}" not in content:
            content = content.replace("_No projects started yet._", "")
            content += f"\n## {self.project_name}\n"
            content += f"- Started: {datetime.now().strftime('%Y-%m-%d')}\n\n"
            content += "| Step | Status | Notes |\n"
            content += "|------|--------|-------|\n"

        timestamp = datetime.now().strftime("%H:%M")
        entry = f"| {step} | {status} | {notes} ({timestamp}) |\n"

        content += entry
        STATUS_FILE.write_text(content)
        log(f"Status updated: {step} = {status}")
        return {"step": step, "status": status, "notes": notes}

    def get_status(self):
        """Read current status.

        Returns dict with status content.
        """
        if STATUS_FILE.exists():
            return {"exists": True, "content": STATUS_FILE.read_text()}
        return {"exists": False, "content": "No status file found."}
