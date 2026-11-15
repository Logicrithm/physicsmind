# PhysicsMind — Project Status

## Decisions
- ₹0 starting budget; free API quota only.
- Windows, 8 GB RAM, no dedicated GPU.
- Streamlit chat-first MVP.
- OpenRouter optional free-model API; no paid fallback.
- SymPy for deterministic calculations.
- SQLite feedback after each assistant response.
- Never train automatically on raw feedback.
- Token efficiency: deterministic code first, LLM only when needed.
- A wrong number presented as checked is worse than no number: when the question reader is unsure, it asks instead of guessing (15 Nov 2026).
- Git restore point: `b149334` (baseline, 14 Nov 2026). `.env` and `physicsmind.db` are never committed.

## Current implementation
- Friendly chat-style interface with session conversation history and three quick-start questions.
- **Question reader** (`physicsmind/reader.py`, no AI involved): reads every number with its unit and converts it to SI
  (m/s, km/h, kmph, cm/s, mph, ft/s, knots; m/s², N/kg; m, cm, km; s, min; degrees, radians, π/6), works out what each
  number is from the words around it (launch speed, vertical component, angle and whether it is measured from the
  horizontal or the vertical, g, launch height, time to reach the top, mass), and checks that the maximum-height
  formula applies. Gives one of three verdicts:
  - solvable — answered by the solver;
  - unclear — no number; the reply says exactly what is missing or contradictory;
  - not handled — sent to the AI tutor with a note saying why the checked solver did not answer.
- **Maximum-height solver** (`physicsmind/projectile.py`): straight up or at an angle, from the ground or a raised
  point, from a launch speed, its vertical part, or the time to reach the top. SymPy solves the kinematics equations
  and the direct formula h = u_y²/2g must agree before a number is shown.
- **Answer routing** (`physicsmind/answer.py`): every answer is labelled solver, clarification, ai_tutor or
  ai_unavailable, and that label is saved with feedback.
- Optional LLM tutor (OpenRouter) for everything else, labelled "not independently verified".
- Per-answer feedback with issue category and optional comment, stored locally in SQLite.

## Verified
- 92 automated tests pass (15 Nov 2026), including the two wrong answers found on 14 Nov:
  30 m/s at 45° now gives 22.96 m (was 45.92 m) and 72 km/h now gives 20.41 m (was 264.49 m).
- Checked in the running app: the starter question (20.41 m), both former failures, a raised launch
  (5.10 m above the launch point, 25.10 m above the ground) and an unclear question (asked which way it is thrown).

## Limitations
- The checked solver answers only maximum-height questions for one object in free flight. Time of flight, range,
  inverse questions ("what speed reaches 20 m?") and every other topic go to the AI tutor, unchecked.
- A question that asks for the maximum height and something else (e.g. the time) goes wholly to the AI tutor.
- Numbers written as words ("twenty") are not read; the reader asks for digits.
- A reply to a clarification is not combined with the earlier question: the student sends the full question again.
- The reader works by word patterns, so unusual wording can still be misread; it is built to refuse rather than
  guess, but it has only been tested on the questions in `tests/test_reader.py`.
- General chat needs an OpenRouter key; free-model availability and quotas can change.
- No image upload, broad RAG, simulations or adaptive learning yet. Conversation history is session-only.

## Next tasks
1. Use it with real questions and rate the answers; read the saved feedback by response type.
2. Extend the checked solver to the rest of the same projectile (time to the top, time of flight, range), reusing the reader.
3. Straight-line constant-acceleration questions (the solver already supports u, v, a, s, t).
4. Independent checking of AI tutor answers where a formula applies.
5. Image input and visual learning later.

## Token/cost policy
- Use Python/SymPy for deterministic work; a clarification never calls the AI.
- Keep LLM prompts compact.
- No paid model fallback.
- Validate feedback before adding examples to evaluation data.
