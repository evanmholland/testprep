"""Utilities for importing practice tests from PDF files."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Tuple

from pypdf import PdfReader

from . import config
from .models import Passage, Question, Test

QUESTION_HEADER = re.compile(r"^(?P<number>\d{1,3})[).]\s*")
CHOICE_HEADER = re.compile(r"^([A-H])[).]\s*")
PASSAGE_HEADER = re.compile(r"^Passage\s+(?P<number>\d+)", re.IGNORECASE)


class PdfImportError(RuntimeError):
    """Raised when a PDF cannot be imported cleanly."""


def _extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def _split_passages(text: str) -> List[Tuple[str, str]]:
    """Return a list of (passage_id, passage_text) tuples."""
    passages: List[Tuple[str, str]] = []
    current_id = "passage-free"
    buffer: List[str] = []
    for line in text.splitlines():
        match = PASSAGE_HEADER.match(line.strip())
        if match:
            if buffer:
                passages.append((current_id, "\n".join(buffer).strip()))
                buffer = []
            current_id = f"passage-{match.group('number')}"
            continue
        buffer.append(line)
    if buffer:
        passages.append((current_id, "\n".join(buffer).strip()))
    return passages


def _split_questions(text: str) -> List[Tuple[str, List[str]]]:
    """Return raw question chunks keyed by their numeric identifier."""
    chunks: List[Tuple[str, List[str]]] = []
    current_id: str | None = None
    buffer: List[str] = []
    for line in text.splitlines():
        header = QUESTION_HEADER.match(line.strip())
        if header:
            if current_id is not None:
                chunks.append((current_id, buffer))
                buffer = []
            current_id = header.group("number")
            line = QUESTION_HEADER.sub("", line, count=1)
        if current_id is None:
            continue
        buffer.append(line)
    if current_id is not None:
        chunks.append((current_id, buffer))
    return chunks


def _extract_choices(lines: Iterable[str]) -> Tuple[List[str], List[str]]:
    """Split question text and answer choices."""
    prompt_lines: List[str] = []
    choices: List[str] = []
    for line in lines:
        stripped = line.strip()
        match = CHOICE_HEADER.match(stripped)
        if match:
            label = match.group(1)
            content = CHOICE_HEADER.sub("", stripped, count=1).strip()
            index = ord(label) - 65
            while len(choices) <= index:
                choices.append("")
            choices[index] = content
        else:
            prompt_lines.append(line)
    # Trim trailing empty placeholders
    while choices and not choices[-1]:
        choices.pop()
    return prompt_lines, choices


def import_pdf(
    pdf_path: Path, *,
    test_id: str,
    title: str,
    subject: str,
) -> Test:
    """Parse a PDF practice test into a structured :class:`Test`."""
    if not pdf_path.exists():
        raise PdfImportError(f"PDF {pdf_path} does not exist")

    raw_text = _extract_pdf_text(pdf_path)
    if not raw_text.strip():
        raise PdfImportError("No extractable text found in the PDF")

    question_chunks = _split_questions(raw_text)
    if not question_chunks:
        raise PdfImportError(
            "Could not identify any question headers. Adjust the regex or clean the PDF."
        )

    passages = [
        Passage(id=pid, title=pid.replace("-", " ").title(), text=ptext)
        for pid, ptext in _split_passages(raw_text)
        if ptext
    ]
    questions: List[Question] = []
    for qid, lines in question_chunks:
        prompt, choices = _extract_choices(lines)
        questions.append(
            Question(
                id=qid,
                text="\n".join(line.strip() for line in prompt if line.strip()),
                choices=[choice for choice in choices if choice],
            )
        )

    try:
        relative_source = pdf_path.relative_to(config.PROJECT_ROOT)
    except ValueError:
        relative_source = pdf_path

    test = Test(
        id=test_id,
        title=title,
        subject=subject,
        source_pdf=str(relative_source),
        passages=passages,
        questions=questions,
    )

    return test
