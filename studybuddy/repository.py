"""Persistence layer for storing and retrieving practice tests."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Optional

from . import config
from .models import Passage, Question, Test


def _test_path(test_id: str) -> Path:
    return config.TEST_ARCHIVE_DIR / f"{test_id}.json"


def list_tests() -> List[str]:
    config.ensure_directories()
    return sorted(path.stem for path in config.TEST_ARCHIVE_DIR.glob("*.json"))


def save_test(test_data: Test) -> None:
    config.ensure_directories()
    destination = _test_path(test_data.id)
    serialized = {
        "id": test_data.id,
        "title": test_data.title,
        "source_pdf": test_data.source_pdf,
        "subject": test_data.subject,
        "passages": [
            {
                "id": passage.id,
                "title": passage.title,
                "text": passage.text,
                "question_ids": passage.question_ids,
            }
            for passage in test_data.passages
        ],
        "questions": [
            {
                "id": question.id,
                "text": question.text,
                "choices": question.choices,
                "answer": question.answer,
                "explanation": question.explanation,
                "passage_id": question.passage_id,
            }
            for question in test_data.questions
        ],
    }
    destination.write_text(json.dumps(serialized, indent=2, ensure_ascii=False))


def load_test(test_id: str) -> Test:
    path = _test_path(test_id)
    if not path.exists():
        raise FileNotFoundError(
            f"Test {test_id!r} does not exist. Import it with the 'load-pdf' command."
        )
    payload = json.loads(path.read_text())
    questions = [
        Question(
            id=item["id"],
            text=item["text"],
            choices=item.get("choices", []),
            answer=item.get("answer"),
            explanation=item.get("explanation"),
            passage_id=item.get("passage_id"),
        )
        for item in payload.get("questions", [])
    ]
    passages = [
        Passage(
            id=item["id"],
            title=item.get("title", ""),
            text=item.get("text", ""),
            question_ids=item.get("question_ids", []),
        )
        for item in payload.get("passages", [])
    ]
    return Test(
        id=payload["id"],
        title=payload.get("title", payload["id"]),
        source_pdf=payload.get("source_pdf", ""),
        subject=payload.get("subject", ""),
        questions=questions,
        passages=passages,
    )


def load_all_tests(subject: Optional[str] = None) -> Iterable[Test]:
    for test_id in list_tests():
        test = load_test(test_id)
        if subject is None or test.subject.lower() == subject.lower():
            yield test
