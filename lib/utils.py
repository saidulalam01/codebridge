"""Shared constants and utility functions for the CodeBridge toolkit."""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

# ─── Directory Configuration ─────────────────────────────────────────────────

AGENT_DIR = Path(__file__).parent.parent
MAPPINGS_DIR = AGENT_DIR / "mappings"
DATA_PROFILES_DIR = AGENT_DIR / "data-profiles"
PROJECTS_DIR = AGENT_DIR / "projects"
MEMORY_DIR = AGENT_DIR / "memory"
STATUS_FILE = AGENT_DIR / "status.md"
CHECKLIST_FILE = AGENT_DIR / "checklist.md"

# Ensure directories exist
MAPPINGS_DIR.mkdir(exist_ok=True)
DATA_PROFILES_DIR.mkdir(exist_ok=True)
PROJECTS_DIR.mkdir(exist_ok=True)
MEMORY_DIR.mkdir(exist_ok=True)

# ─── Scan Configuration ──────────────────────────────────────────────────────

SECRET_PATTERNS = [
    # Environment variables
    "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD", "DATABASE_URL",
    "API_KEY", "SECRET_KEY", "ACCESS_TOKEN", "REFRESH_TOKEN",
    "AWS_ACCESS_KEY", "AWS_SECRET_KEY",
    "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
    # Patterns in code
    "password", "passwd", "secret", "token",
    "sk-ant-", "sk-", "ghp_", "gho_",
    # Connection strings
    "postgresql://", "mysql://", "mongodb://", "redis://",
    "amazonaws.com", "rds.amazonaws.com",
]

SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "env", ".env", ".mypy_cache", ".pytest_cache", "dist", "build",
    ".streamlit", ".idea", ".vscode",
}

SKIP_EXTENSIONS = {
    ".pyc", ".pyo", ".so", ".dll", ".exe", ".bin",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".zip", ".tar", ".gz", ".whl",
    ".db", ".sqlite", ".sqlite3",
}

# File extensions for replacement passes
EXACT_REPLACE_EXTENSIONS = {
    ".py", ".sql", ".md", ".txt", ".yaml", ".yml",
    ".json", ".jsonl", ".toml", ".cfg", ".ini", ".sh", ".env.example",
}

CONTEXTUAL_REPLACE_EXTENSIONS = {".py", ".md", ".txt", ".html", ".jsonl", ".sh"}

# ─── Utility Functions ────────────────────────────────────────────────────────

def log(msg, level="INFO"):
    """Log a message to stderr (keeps stdout clean for JSON output)."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}", file=sys.stderr)


def run_cmd(cmd, capture=True, check=True):
    """Run a shell command and return output."""
    result = subprocess.run(
        cmd, shell=True, capture_output=capture, text=True, check=check
    )
    return result.stdout.strip() if capture else None


def output_json(data):
    """Print JSON to stdout for AI agent to parse."""
    import json
    print(json.dumps(data, indent=2, default=str))
