"""Phase 5: Supporting File Generator — .gitignore, README, requirements.txt, etc."""

from .utils import PROJECTS_DIR, log


class SupportingFileGenerator:
    """Generates .env.example, .gitignore, requirements.txt, README, etc."""

    def __init__(self, project_name, project_type):
        self.project_name = project_name
        self.project_type = project_type
        self.output_path = PROJECTS_DIR / project_name

    def generate_all(self):
        """Generate all supporting files based on project type.

        Returns dict listing files generated.
        """
        generated = []
        self.generate_gitignore()
        generated.append(".gitignore")
        self.generate_env_example()
        generated.append(".env.example")
        self.generate_requirements()
        generated.append("requirements.txt")
        self.generate_readme()
        generated.append("README.md")

        if self.project_type in ("streamlit", "webapp_db"):
            self.generate_streamlit_config()
            generated.append(".streamlit/config.toml")

        log("Supporting files generated.")
        return {"files_generated": generated}

    def generate_gitignore(self):
        content = """# Environment
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.venv/
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Data (if using real DB)
*.sqlite3
*.db
"""
        (self.output_path / ".gitignore").write_text(content)

    def generate_env_example(self):
        content = """# Copy this file to .env and fill in your values
# cp .env.example .env

# Database (optional — app runs with sample data if not set)
DATABASE_URL=postgresql://user:password@localhost:5432/mydb

# API Keys (optional)
# API_KEY=your-api-key-here
"""
        (self.output_path / ".env.example").write_text(content)

    def generate_requirements(self):
        """Scan the project for imports and build requirements.txt."""
        imports = set()
        known_packages = {
            "streamlit": "streamlit",
            "pandas": "pandas",
            "plotly": "plotly",
            "numpy": "numpy",
            "psycopg2": "psycopg2-binary",
            "sqlalchemy": "sqlalchemy",
            "fastapi": "fastapi",
            "flask": "flask",
            "requests": "requests",
            "dotenv": "python-dotenv",
            "openai": "openai",
            "sklearn": "scikit-learn",
            "matplotlib": "matplotlib",
            "seaborn": "seaborn",
            "yaml": "pyyaml",
            "jinja2": "jinja2",
            "schedule": "schedule",
        }

        for fpath in self.output_path.rglob("*.py"):
            try:
                for line in fpath.read_text(errors="ignore").splitlines():
                    line = line.strip()
                    if line.startswith("import ") or line.startswith("from "):
                        parts = line.replace("import ", "").replace("from ", "").split(".")
                        module = parts[0].split()[0]
                        if module in known_packages:
                            imports.add(known_packages[module])
            except Exception:
                pass

        if imports:
            content = "\n".join(sorted(imports)) + "\n"
            (self.output_path / "requirements.txt").write_text(content)

    def generate_readme(self):
        """Generate a generic README."""
        lines = [
            f"# {self.project_name.replace('-', ' ').title()}",
            "",
        ]

        if self.project_type in ("streamlit", "webapp_db"):
            lines.extend([
                "A data dashboard built with Streamlit.",
                "",
                "## Quick Start",
                "",
                "```bash",
                "# Clone the repo",
                f"git clone https://github.com/YOUR_USERNAME/{self.project_name}.git",
                f"cd {self.project_name}",
                "",
                "# Install dependencies",
                "pip install -r requirements.txt",
                "",
                "# Run with sample data (no database needed)",
                "streamlit run app.py",
                "",
                "# Or connect your own database",
                "cp .env.example .env",
                "# Edit .env with your database credentials",
                "streamlit run app.py",
                "```",
                "",
                "## Sample Data",
                "",
                "The app includes sample data in `data/` so you can run it immediately.",
                "To regenerate sample data: `python data/seed.py`",
                "",
            ])
        elif self.project_type in ("script_db",):
            lines.extend([
                "A data analysis tool.",
                "",
                "## Quick Start",
                "",
                "```bash",
                f"git clone https://github.com/YOUR_USERNAME/{self.project_name}.git",
                f"cd {self.project_name}",
                "pip install -r requirements.txt",
                "",
                "# Run with sample data",
                "python main.py",
                "",
                "# Or connect your own database",
                "cp .env.example .env",
                "python main.py",
                "```",
                "",
            ])
        elif self.project_type == "notebook":
            lines.extend([
                "A data analysis notebook.",
                "",
                "## Quick Start",
                "",
                "```bash",
                f"git clone https://github.com/YOUR_USERNAME/{self.project_name}.git",
                f"cd {self.project_name}",
                "pip install -r requirements.txt",
                "jupyter notebook",
                "```",
                "",
                "Sample data is included in `data/`.",
                "",
            ])
        else:
            lines.extend([
                "",
                "## Quick Start",
                "",
                "```bash",
                f"git clone https://github.com/YOUR_USERNAME/{self.project_name}.git",
                f"cd {self.project_name}",
                "pip install -r requirements.txt",
                "python main.py",
                "```",
                "",
            ])

        lines.extend([
            "## Project Structure",
            "",
            "```",
        ])

        for fpath in sorted(self.output_path.rglob("*")):
            if fpath.is_file() and ".git" not in str(fpath):
                rel = fpath.relative_to(self.output_path)
                depth = len(rel.parts) - 1
                prefix = "    " * depth + "|- "
                lines.append(f"{prefix}{fpath.name}")

        lines.extend([
            "```",
            "",
            "## Configuration",
            "",
            "Copy `.env.example` to `.env` and update with your values.",
            "The app works with the included sample data — no external setup needed.",
            "",
        ])

        (self.output_path / "README.md").write_text("\n".join(lines))

    def generate_streamlit_config(self):
        """Generate Streamlit config for deployment."""
        config_dir = self.output_path / ".streamlit"
        config_dir.mkdir(exist_ok=True)

        config = """[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"

[server]
headless = true
port = 8501
"""
        (config_dir / "config.toml").write_text(config)
