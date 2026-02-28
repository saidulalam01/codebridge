"""Phase 3: Sample Data Generator — Creates realistic sample data for anonymized projects."""

from .utils import PROJECTS_DIR, log


class SampleDataGenerator:
    """Generates realistic sample data for anonymized projects."""

    def __init__(self, project_name, mapping):
        self.project_name = project_name
        self.mapping = mapping
        self.output_dir = PROJECTS_DIR / project_name / "data"

    def generate_seed_script(self, data_profile=None):
        """Generate a seed.py script based on the data profile.

        Returns dict with path to generated script.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        seed_content = '''"""
Seed script — generates sample data for this project.
Run: python data/seed.py

This creates realistic sample CSV files for running the app without a database.
"""

import csv
import random
import os
from datetime import datetime, timedelta

random.seed(42)  # Reproducible data

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def random_date(start, end):
    """Generate a random date between start and end."""
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)


def generate_sample_data():
    """Generate all sample CSV files."""
    print("Generating sample data...")

    # TODO: This function will be customized per project
    # based on the data profile. The agent will fill in
    # the actual generation logic during anonymization.

    print(f"Sample data written to {OUTPUT_DIR}/")


if __name__ == "__main__":
    generate_sample_data()
'''
        seed_path = self.output_dir / "seed.py"
        seed_path.write_text(seed_content)
        log(f"Seed script created at {seed_path}")
        return {"status": "created", "path": str(seed_path)}
