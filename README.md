# StudyBuddy Practice CLI

A command-line assistant for studying for the ACT or SAT. The tool can import
practice tests from PDFs, let you run question-by-question drills or full-length
practice sessions, and request explanations from a local language model (such as
an Ollama model running on your machine).

## Features

- Import ACT/SAT practice PDFs and transform them into structured question
  banks.
- Run practice sessions that shuffle questions or simulate full test sections.
- Request AI-generated explanations per question or per passage via a local LLM.
- Store your imported materials in JSON for easy editing or sharing.

## Project Layout

```
practice_pdfs/         # Place your ACT/SAT PDFs here before importing them
studybuddy/
  ai.py                # Ollama/local LLM integration helpers
  config.py            # Directory definitions and setup helpers
  models.py            # Dataclasses for passages, questions, tests
  pdf_loader.py        # PDF parsing helpers
  repository.py        # JSON persistence
  session.py           # CLI session logic
main.py                # CLI entry point
requirements.txt       # Python dependencies
```

## Getting Started

1. **Install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Add practice PDFs**

   Copy your ACT/SAT practice PDFs into the `practice_pdfs/` directory. The
   parser expects PDFs that contain selectable text (scanned images need to be
   OCR'd first).

3. **Import a test**

   ```bash
   python main.py load-pdf practice_test_1.pdf \
     --test-id="sat-official-2020" \
     --title="Official SAT Practice Test 2020" \
     --subject="SAT"
   ```

   The command extracts question text, choices, and passages into
   `studybuddy/data/tests/sat-official-2020.json`. Review and edit the JSON file
   as needed to fix parsing quirks or add answer keys.

4. **Start practicing**

   - Shuffle questions for a quick drill:

     ```bash
     python main.py start-practice sat-official-2020
     ```

   - Run through every question in order:

     ```bash
     python main.py start-test sat-official-2020
     ```

   During each question you can reveal the answer and optionally request an AI
   explanation.

5. **Request explanations outside of a session**

   ```bash
   python main.py explain sat-official-2020 12
   ```

   This uses the configured Ollama host/model to generate an explanation for the
   question. Ensure your local model is running (for Ollama the default is
   `ollama serve`).

## Configuring AI Explanations

The default integration targets an Ollama server at `http://localhost:11434`
with the `llama3` model. You can change these defaults by editing
`studybuddy/ai.py` or by calling `explain_with_ollama` directly in your own
scripts. The prompt automatically includes the question text, answer choices, and
any associated passage text if available.

## Roadmap / DIY Extensions

- Enhance the PDF parser by adding section-aware heuristics for math, reading,
  and science passages.
- Store scoring rubrics and timing utilities for realistic test simulations.
- Surface accuracy statistics and spaced repetition scheduling.
- Integrate additional local model backends (LM Studio, text-generation-webui,
  etc.) by replicating the interface in `studybuddy/ai.py`.

Contributions and tweaks to suit your study style are welcome!
