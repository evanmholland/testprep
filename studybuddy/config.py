"""Configuration helpers for the StudyBuddy application."""
from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "studybuddy" / "data"
TEST_ARCHIVE_DIR = DATA_DIR / "tests"
PDF_IMPORT_DIR = PROJECT_ROOT / "practice_pdfs"


def ensure_directories() -> None:
    """Ensure that all application directories exist."""
    for directory in (DATA_DIR, TEST_ARCHIVE_DIR, PDF_IMPORT_DIR):
        directory.mkdir(parents=True, exist_ok=True)
