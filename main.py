"""Entry point for the StudyBuddy CLI."""
from __future__ import annotations

from studybuddy import config
from studybuddy.session import PracticeCLI


def main() -> None:
    config.ensure_directories()
    PracticeCLI().app()


if __name__ == "__main__":
    main()
