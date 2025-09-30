"""Integration helpers for calling a local LLM (e.g., Ollama) for explanations."""
from __future__ import annotations

from dataclasses import asdict
from typing import Optional

import requests

from .models import Passage, Question

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_MODEL = "llama3"


class ExplanationError(RuntimeError):
    """Raised when an AI explanation cannot be generated."""


def build_prompt(
    question: Question,
    *,
    passage: Optional[Passage] = None,
    context_instructions: str = "You are a helpful ACT/SAT tutor. Explain the reasoning clearly."
) -> str:
    """Construct a prompt for the language model."""
    prompt_lines = [context_instructions, "", question.format_for_prompt()]
    if passage is not None:
        prompt_lines.insert(1, "Passage:")
        prompt_lines.insert(2, passage.text.strip())
        prompt_lines.insert(3, "")
    if question.answer:
        prompt_lines.append("")
        prompt_lines.append(f"Correct answer: {question.answer}")
    return "\n".join(prompt_lines)


def explain_with_ollama(
    question: Question,
    *,
    passage: Optional[Passage] = None,
    model: str = DEFAULT_MODEL,
    host: str = DEFAULT_OLLAMA_HOST,
    stream: bool = False,
) -> str:
    """Generate an explanation for the provided question using Ollama."""
    payload = {
        "model": model,
        "prompt": build_prompt(question, passage=passage),
        "stream": stream,
    }
    response = requests.post(f"{host}/api/generate", json=payload, timeout=120)
    if response.status_code != 200:
        raise ExplanationError(
            f"Ollama call failed with status {response.status_code}: {response.text[:200]}"
        )
    data = response.json()
    if stream:
        return data
    return data.get("response", "")


def explanation_payload(question: Question, passage: Optional[Passage] = None) -> dict:
    """Return a serializable payload useful for debugging prompts."""
    return {
        "question": asdict(question),
        "passage": asdict(passage) if passage else None,
        "prompt": build_prompt(question, passage=passage),
    }
