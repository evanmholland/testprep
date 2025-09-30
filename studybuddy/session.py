"""Logic for interactive practice sessions."""
from __future__ import annotations

import random
from typing import Iterator, List, Optional

import typer

from .ai import explain_with_ollama
from .models import Passage, Question, Test


class StudySession:
    """Base class for practice/test sessions."""

    def __init__(self, test: Test, *, shuffle: bool = False) -> None:
        self.test = test
        self.questions: List[Question] = list(test.questions)
        if shuffle:
            random.shuffle(self.questions)
        self.responses: dict[str, str] = {}
        self.revealed: set[str] = set()

    def iter_questions(self) -> Iterator[Question]:
        yield from self.questions

    def record_response(self, question: Question, answer: str) -> None:
        self.responses[question.id] = answer

    def reveal_answer(self, question: Question) -> None:
        self.revealed.add(question.id)

    def is_correct(self, question: Question) -> Optional[bool]:
        if question.answer is None:
            return None
        user_answer = self.responses.get(question.id)
        if user_answer is None:
            return None
        return user_answer.strip().upper() == question.answer.strip().upper()


class PracticeCLI:
    """Command-line interface for practice/test sessions."""

    def __init__(self) -> None:
        self.app = typer.Typer(add_completion=False)
        self.register_commands()

    def register_commands(self) -> None:
        self.app.command()(self.list_tests)
        self.app.command("load-pdf")(self.load_pdf)
        self.app.command("start-practice")(self.start_practice)
        self.app.command("start-test")(self.start_test)
        self.app.command("explain")(self.explain_question)

    def list_tests(self) -> None:
        """List every imported practice test."""
        from . import repository

        tests = repository.list_tests()
        if not tests:
            typer.echo(
                "No tests found. Add PDF files to the 'practice_pdfs' folder and run load-pdf."
            )
            return
        for test_id in tests:
            test = repository.load_test(test_id)
            typer.echo(f"- {test.id}: {test.title} ({test.subject})")

    def load_pdf(
        self,
        pdf_filename: str,
        test_id: str = typer.Option(..., prompt=True, help="Unique identifier for the test"),
        title: str = typer.Option(..., prompt=True, help="Display title for the test"),
        subject: str = typer.Option(..., prompt=True, help="Exam label, e.g., SAT or ACT"),
    ) -> None:
        """Import a PDF file from the practice_pdfs directory."""
        from pathlib import Path

        from . import config, pdf_loader, repository

        config.ensure_directories()
        pdf_path = Path(pdf_filename)
        if not pdf_path.is_absolute():
            pdf_path = config.PDF_IMPORT_DIR / pdf_path
        typer.echo(f"Importing {pdf_path} ...")
        test = pdf_loader.import_pdf(pdf_path, test_id=test_id, title=title, subject=subject)
        repository.save_test(test)
        typer.echo(f"Imported {len(test.questions)} questions into test '{test.id}'.")

    def _prompt_for_answer(self, question: Question) -> str:
        typer.echo(question.format_for_prompt())
        answer = typer.prompt("Your answer", default="")
        return answer.strip()

    def _present_question(self, session: StudySession, question: Question) -> None:
        typer.echo("".ljust(60, "-"))
        user_answer = self._prompt_for_answer(question)
        if user_answer:
            session.record_response(question, user_answer)
        show_answer = typer.confirm("Show correct answer?", default=False)
        if show_answer and question.answer:
            session.reveal_answer(question)
            typer.echo(f"Correct answer: {question.answer}")
            correctness = session.is_correct(question)
            if correctness is True:
                typer.echo("You got it right! 🎉")
            elif correctness is False:
                typer.echo("Not quite. Review the explanation for more help.")
        if typer.confirm("Generate AI explanation?", default=False):
            self._generate_explanation(session.test, question)

    def _generate_explanation(self, test: Test, question: Question) -> None:
        passage = None
        if question.passage_id:
            try:
                passage = test.get_passage(question.passage_id)
            except KeyError:
                passage = None
        try:
            typer.echo("Contacting local model ...")
            explanation = explain_with_ollama(question, passage=passage)
        except Exception as exc:  # pragma: no cover - defensive output
            typer.echo(f"Failed to generate explanation: {exc}")
            return
        typer.echo("\n" + explanation + "\n")

    def start_practice(
        self,
        test_id: str,
        shuffle: bool = typer.Option(
            True,
            help="Shuffle questions for mixed practice (use --no-shuffle to keep order)",
        ),
    ) -> None:
        """Start a practice session that can shuffle questions."""
        from . import repository

        test = repository.load_test(test_id)
        session = StudySession(test, shuffle=shuffle)
        for question in session.iter_questions():
            self._present_question(session, question)
            if not typer.confirm("Continue to next question?", default=True):
                break

    def start_test(self, test_id: str) -> None:
        """Run through the entire test in order."""
        from . import repository

        test = repository.load_test(test_id)
        session = StudySession(test, shuffle=False)
        typer.echo(f"Starting full test: {test.title}")
        for question in session.iter_questions():
            self._present_question(session, question)
        typer.echo("Test complete! Review your responses above.")

    def explain_question(self, test_id: str, question_id: str) -> None:
        """Request an AI explanation for a specific question."""
        from . import repository

        test = repository.load_test(test_id)
        question = test.get_question(question_id)
        passage: Optional[Passage] = None
        if question.passage_id:
            try:
                passage = test.get_passage(question.passage_id)
            except KeyError:
                passage = None
        typer.echo(explain_with_ollama(question, passage=passage))


def run() -> None:
    PracticeCLI().app()
