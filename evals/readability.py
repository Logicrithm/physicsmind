"""How readable are the AI tutor's answers? Asks 10 typical student questions and measures what a student would see.

    python -m evals.readability                    print the report
    python -m evals.readability --save FILE        also write it as Markdown

This calls the real AI tutor (about 10 of the free daily answers), so it is run by hand, never by the tests.
Each answer goes through the same path as in the app (make_answer), so the clean-up and maths conversion are
included. Answers vary from run to run; compare runs, not single answers.

Measured for each answer:
- words: the prose, with formulas left out;
- formulas: display and inline formulas;
- tables and headings;
- symbols per 100 words: formulas per 100 words of prose, a rough sense of how dense it is;
- ends with an offer: the last paragraph asks the student a question (e.g. "Want a worked example?");
- maths blocks OK: every "$$" stands alone on its line, so Streamlit can draw it (see tests/test_math_display.py).
"""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import statistics
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from physicsmind.answer import AI_TUTOR, make_answer  # noqa: E402
from physicsmind.version import app_version  # noqa: E402

QUESTIONS = [
    "What are the formulas for speed, distance and time? Explain with an example.",
    "Why is gravity different on different planets?",
    "What is Newton's first law? Give an everyday example.",
    "What is the difference between speed and velocity?",
    "How is the equation v = u + at derived?",
    "What is a projectile?",
    "Why does a ball thrown upwards slow down?",
    "What is kinetic energy and how do I calculate it?",
    "Explain momentum in simple words.",
    "A car accelerates from rest at 2 m/s² for 5 s. How far does it go?",
]


def measure(text: str) -> dict:
    lines = text.splitlines()
    display = sum(1 for i, line in enumerate(lines) if line.strip() == "$$") // 2
    prose = re.sub(r"\$\$\n.*?\n\s*\$\$", " ", text, flags=re.S)
    inline = len(re.findall(r"(?<!\$)\$(?!\$)[^$\n]+?\$", prose))
    prose = re.sub(r"\$[^$\n]+?\$", " ", prose)
    words = len(re.findall(r"[A-Za-z]{2,}", prose))
    fences = [i for i, line in enumerate(lines) if "$$" in line]
    blocks_ok = all(lines[i].strip() == "$$" for i in fences) and len(fences) % 2 == 0
    paragraphs = [p for p in text.strip().split("\n\n") if p.strip()]
    return {"words": words, "formulas": display + inline,
            "tables": len(re.findall(r"^\s*\|(?:\s*:?-{3,}:?\s*\|)+\s*$", text, flags=re.M)),  # header rules of tables
            "headings": len(re.findall(r"^#{1,6} ", text, flags=re.M)),
            "per100": round(100 * (display + inline) / max(words, 1), 1),
            "offer": bool(paragraphs) and "?" in paragraphs[-1], "blocks_ok": blocks_ok}


def run(questions=QUESTIONS) -> list[tuple[str, dict | None, str, str]]:
    """(question, measurements or None, note, the answer text shown)."""
    results = []
    for question in questions:
        answer = make_answer(question)
        if answer.response_type != AI_TUTOR:
            results.append((question, None, f"not answered by the AI: {answer.response_type}", answer.text))
        else:
            results.append((question, measure(answer.text), answer.source, answer.text))
    return results


def report(results, title: str) -> str:
    lines = [f"# {title}", "", f"Version {app_version()}, run {date.today().isoformat()}. "
             f"{len(results)} questions to the real AI tutor.", "",
             "| Question | Words | Formulas | Per 100 words | Tables | Headings | Ends with an offer | Maths blocks OK |",
             "|---|---|---|---|---|---|---|---|"]
    measured = [m for _, m, _, _ in results if m]
    for question, m, note, _ in results:
        if m is None:
            lines.append(f"| {question} | {note} | | | | | | |")
        else:
            lines.append(f"| {question} | {m['words']} | {m['formulas']} | {m['per100']} | {m['tables']} | "
                         f"{m['headings']} | {'yes' if m['offer'] else 'no'} | {'yes' if m['blocks_ok'] else '**NO**'} |")
    if measured:
        median = lambda key: statistics.median(m[key] for m in measured)  # noqa: E731
        lines += ["", f"**Median:** {median('words'):g} words, {median('formulas'):g} formulas, "
                      f"{median('per100'):g} formulas per 100 words, {median('tables'):g} tables, {median('headings'):g} headings. "
                      f"Ends with an offer: {sum(m['offer'] for m in measured)} of {len(measured)}. "
                      f"Maths blocks OK: {sum(m['blocks_ok'] for m in measured)} of {len(measured)}."]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--save", type=Path, help="also write the report to this Markdown file")
    parser.add_argument("--title", default="PhysicsMind AI-answer readability")
    parser.add_argument("--answers", type=Path, help="also save the answer texts (JSON) so they can be measured again")
    args = parser.parse_args(argv)
    from physicsmind.config import use_only_own_keys
    from dotenv import load_dotenv
    use_only_own_keys()
    load_dotenv(override=True)
    results = run()
    text = report(results, args.title)
    if args.answers:
        args.answers.write_text(json.dumps([{"question": q, "answer": a} for q, _, _, a in results], ensure_ascii=False,
                                           indent=1), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    if args.save:
        args.save.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
