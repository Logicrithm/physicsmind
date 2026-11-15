"""Scores PhysicsMind's checked solver against evals/questions.json.

    python -m evals.run_eval                 print the report
    python -m evals.run_eval --save FILE     also write it as Markdown

Only the question reader and the solver run here: the AI tutor is never called, so this is free and offline.
Every result is one of three kinds:
- correct: the right number, a question back when the question is unclear, or a hand-off to the AI when the
  question is outside what the solver handles;
- safe miss: no wrong number was given, but the student was asked something needlessly or sent to the unchecked AI;
- dangerous: a wrong number, or a checked-looking number where none should be given. The target is zero.
The exit code is 1 when anything is dangerous, so this can guard a release.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from physicsmind.projectile import solve_max_height  # noqa: E402
from physicsmind.reader import NOT_MINE, SOLVABLE, UNCLEAR, read_question  # noqa: E402
from physicsmind.version import app_version  # noqa: E402

QUESTIONS = Path(__file__).resolve().parent / "questions.json"
RELATIVE_TOLERANCE = 1e-3  # the solver's float must match the hand-worked height to 0.1 %

CORRECT, SAFE_MISS, DANGEROUS = "correct", "safe miss", "dangerous"
CATEGORIES = ("straightforward", "units_and_angles", "ambiguous", "outside")


@dataclass
class Result:
    item: dict
    kind: str        # CORRECT, SAFE_MISS or DANGEROUS
    what: str        # what PhysicsMind did, in words


def load(path: Path = QUESTIONS) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["items"]


def _close(got, want) -> bool:
    return got is not None and abs(got - want) <= RELATIVE_TOLERANCE * max(1.0, abs(want))


def score(item: dict) -> Result:
    reading = read_question(item["question"])
    status = reading.status
    reason = reading.reasons[0] if reading.reasons else ""
    solution = solve_max_height(reading) if status == SOLVABLE else None
    gave_number = solution is not None and solution.ok
    if gave_number:
        numbers = f"rise {solution.rise:.4g} m" + (f", {solution.above_ground:.4g} m above the ground"
                                                    if solution.above_ground is not None else "")
    expect = item["expect"]
    also_fine = set(item.get("also_fine", []))

    if expect == SOLVABLE:
        if gave_number:
            right = _close(solution.rise, item["rise"])
            if "above_ground" in item:
                right = right and _close(solution.above_ground, item["above_ground"])
            want = f"rise {item['rise']:.4g} m" + (f", {item['above_ground']:.4g} m above the ground"
                                                    if "above_ground" in item else "")
            return Result(item, CORRECT if right else DANGEROUS,
                          f"answered {numbers}" if right else f"WRONG NUMBER: gave {numbers}, expected {want}")
        if status == SOLVABLE:
            return Result(item, SAFE_MISS, f"understood it but could not check the result: {solution.problem}")
        if status == UNCLEAR:
            return Result(item, SAFE_MISS, f"asked instead of answering: {reason}")
        return Result(item, SAFE_MISS, f"sent to the unchecked AI instead of solving: {reason or 'not recognised'}")

    if gave_number:
        return Result(item, DANGEROUS, f"GAVE A NUMBER it should not have: {numbers}")
    if status == expect or status in also_fine:
        return Result(item, CORRECT, f"{'asked' if status == UNCLEAR else 'sent to the AI'}: {reason or 'not recognised'}")
    if expect == UNCLEAR:
        return Result(item, SAFE_MISS, f"sent to the AI instead of asking: {reason or 'not recognised'}")
    return Result(item, SAFE_MISS, f"asked a question the AI should have answered: {reason}")


def run(items: list[dict] | None = None) -> list[Result]:
    return [score(item) for item in (items if items is not None else load())]


def report(results: list[Result], title: str = "PhysicsMind evaluation") -> str:
    by_category = {c: Counter(r.kind for r in results if r.item["category"] == c) for c in CATEGORIES}
    total = Counter(r.kind for r in results)
    lines = [f"# {title}", "",
             f"Version {app_version()}, run {date.today().isoformat()}. {len(results)} questions; the AI is not called.", "",
             "| Group | Questions | Correct | Safe misses | Dangerous |", "|---|---|---|---|---|"]
    for category in CATEGORIES:
        counts = by_category[category]
        n = sum(counts.values())
        lines.append(f"| {category.replace('_', ' ')} | {n} | {counts[CORRECT]} | {counts[SAFE_MISS]} | {counts[DANGEROUS]} |")
    lines.append(f"| **all** | **{len(results)}** | **{total[CORRECT]}** | **{total[SAFE_MISS]}** | **{total[DANGEROUS]}** |")
    for kind, heading in ((DANGEROUS, "Dangerous (wrong or unwanted numbers)"), (SAFE_MISS, "Safe misses")):
        chosen = [r for r in results if r.kind == kind]
        lines += ["", f"## {heading}: {len(chosen)}", ""]
        lines += [f"- **{r.item['id']}** {r.item['question']}  \n  {r.what}" for r in chosen] or ["None."]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--save", type=Path, help="also write the report to this Markdown file")
    parser.add_argument("--title", default="PhysicsMind evaluation")
    args = parser.parse_args(argv)
    results = run()
    text = report(results, args.title)
    sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    if args.save:
        args.save.write_text(text, encoding="utf-8")
    return 1 if any(r.kind == DANGEROUS for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
