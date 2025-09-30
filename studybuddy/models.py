"""Core data models for questions, passages, and tests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional


@dataclass
class Question:
    """Represents a single ACT/SAT-style question."""

    id: str
    text: str
    choices: List[str] = field(default_factory=list)
    answer: Optional[str] = None
    explanation: Optional[str] = None
    passage_id: Optional[str] = None

    def format_for_prompt(self) -> str:
        """Format the question for display or AI prompting."""
        numbered_choices = "\n".join(
            f"{chr(65 + idx)}. {choice}" for idx, choice in enumerate(self.choices)
        )
        return f"Question {self.id}:\n{self.text}\n\n{numbered_choices if numbered_choices else ''}".strip()


@dataclass
class Passage:
    """A reading passage that may be linked to multiple questions."""

    id: str
    title: str
    text: str
    question_ids: List[str] = field(default_factory=list)


@dataclass
class Test:
    """A collection of passages and questions sourced from a practice test."""

    id: str
    title: str
    source_pdf: str
    subject: str
    questions: List[Question]
    passages: List[Passage] = field(default_factory=list)

    def get_question(self, question_id: str) -> Question:
        for question in self.questions:
            if question.id == question_id:
                return question
        raise KeyError(f"Question {question_id!r} not found in test {self.id!r}")

    def iter_passage_questions(self, passage: Passage) -> Iterable[Question]:
        for question_id in passage.question_ids:
            yield self.get_question(question_id)

    def get_passage(self, passage_id: str) -> Passage:
        for passage in self.passages:
            if passage.id == passage_id:
                return passage
        raise KeyError(f"Passage {passage_id!r} not found in test {self.id!r}")
