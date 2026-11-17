# PhysicsMind — Project Status

## Product vision (15 Nov 2026)
PhysicsMind is to become an interactive physics learning companion, not a collection of numerical solvers. In time
a student should be able to learn concepts from the basics, see why formulas work (derivations), see diagrams and
visual explanations, solve problems step by step, ask follow-up questions in context, practise similar problems
with hints, and find and improve weak areas.

For now the checked solver and its reliability come first, and the roadmap stays as it is. Rules for decisions:
- Choose designs that serve the larger learning experience, not one numerical question type at a time.
- Every milestone gives students something they can see and use, not only internal improvements.
- Reassess regularly whether the work is moving towards this vision.

How today's design fits, and what it will need:
- The reader turns a question into a structured Reading (quantities, roles, what is asked), and the solver works
  from that, not from the text. The same structure can later generate practice variants (change the numbers,
  check them with the same solver), drive hints (reveal one step at a time) and answer follow-ups.
- Still missing: explanations are built as finished text. Follow-ups, hints and diagrams need them kept as steps
  (each with its formula, numbers and reason) and turned into text at the end. Do this when the next feature needs it.
- Still missing: a conversation memory (the reply to a clarification and follow-up questions need the earlier question).
- Feedback already stores which part answered (`response_type`); weak-area tracking will also need the topic
  and the step a student struggled with.

## Decisions
- ₹0 starting budget; free API quota only.
- Windows, 8 GB RAM, no dedicated GPU.
- Streamlit chat-first MVP.
- Free AI providers only, no paid fallback: Groq first (`openai/gpt-oss-120b`, 1,000 requests/day and 8,000
  tokens/minute, read from Groq's headers on 15 Nov 2026), OpenRouter free models second (50/day).
- SymPy for deterministic calculations.
- SQLite feedback after each assistant response.
- Never train automatically on raw feedback.
- Token efficiency: deterministic code first, LLM only when needed.
- A wrong number presented as checked is worse than no number: when the question reader is unsure, it asks instead of guessing (15 Nov 2026).
- Git restore points: `c21253f` (baseline, 14 Nov 2026), `c9bcb78` (question reader, 15 Nov 2026),
  `f375056` (ready for a public site). Commits use GitHub's no-reply email, not a personal address.
  `.env` and `physicsmind.db` are never committed.
- Online (15 Nov 2026): Streamlit Community Cloud from the public GitHub repo github.com/Logicrithm/physicsmind
  (no keys or personal data in it); `main` is live, `dev` is work in
  progress, and a change reaches `main` only after the tests pass. Feedback goes to Supabase online, because the
  host's disk is wiped on every restart. See DEPLOY.md.

## Current implementation
- Friendly chat-style interface with session conversation history and three quick-start questions.
- **Question reader** (`physicsmind/reader.py`, no AI involved): reads every number with its unit and converts it to SI
  (m/s, km/h, kmph, cm/s, mph, ft/s, knots; m/s², N/kg; m, cm, km; s, min; degrees, radians, π/6), works out what each
  number is from the words around it (launch speed, vertical component, angle and whether it is measured from the
  horizontal or the vertical, g, launch height, time to reach the top, mass), works out what is asked (maximum
  height, time to the top, time of flight, range, or several), and checks that the formulas apply. Gives one of
  three verdicts:
  - solvable — answered by the solver;
  - unclear — no number; the reply says exactly what is missing or contradictory;
  - not handled — sent to the AI tutor with a note saying why the checked solver did not answer.
- **Projectile solver** (`physicsmind/projectile.py`): straight up, at an angle or horizontally, from the ground or a
  raised point, landing on the ground. Each quantity is worked out two ways that must agree before a number is shown:
  height (SymPy v² = u² + 2as and h = u_y²/2g), time to the top (SymPy v = u + at and u_y/g), time of flight (SymPy
  s = ut + ½at² with s = −h₀, and the quadratic formula), range (SymPy on the path equation, and u_x × T).
- **Answer routing** (`physicsmind/answer.py`): every answer is labelled solver, clarification, ai_tutor or
  ai_unavailable, and that label is saved with feedback.
- **AI tutor** (`physicsmind/tutor.py`) for everything else, labelled "not independently verified": free providers
  tried in order, each visit limited to `AI_QUESTIONS_PER_VISIT` questions, plain messages when the free answers
  run out, and `\( \)` maths from the model converted so Streamlit renders it.
- **Settings** (`physicsmind/config.py`) come from `.env` locally and from the host's Secrets page online.
- **Version label** (`physicsmind/version.py`): release number plus git commit, shown in the sidebar and saved
  with every piece of feedback.
- Per-answer feedback with issue category, optional comment and app version: SQLite on this computer, Supabase
  online (the app's key may only add rows). Testers are asked not to include personal details.

## Verified
- 126 automated tests pass (15 Nov 2026). No test can reach the real feedback file, the online database or an AI
  provider (tests/conftest.py removes every key). They include the two wrong answers found on 14 Nov:
  30 m/s at 45° now gives 22.96 m (was 45.92 m) and 72 km/h now gives 20.41 m (was 264.49 m).
- Checked in the running app: the starter question (20.41 m), both former failures, a raised launch
  (5.10 m above the launch point, 25.10 m above the ground) and an unclear question (asked which way it is thrown).
- Checked in the running app after the online preparation: version label and privacy note shown, a real Groq answer
  with its maths rendered (21 formulas, none left raw), the solver starter still 20.41 m, and the real feedback file
  still holding its 2 rows (backup: physicsmind.db.backup-2026-11-15).
- **Live since 15 Nov 2026 at https://physicsmind.streamlit.app** (version 0.2.1). Checked on the live site: the
  solver (22.96 m for 30 m/s at 45°), a Groq answer, feedback saved to Supabase, the sidebar closed on a 375 px
  phone screen with the chat box tappable, no sideways scrolling. The Supabase publishable key was tested: it can add
  feedback but cannot read, change or delete it, and the table refuses bad ratings and oversized text.
- Not verified on the live site: the hidden error details (no safe way to cause an error there; the setting is
  tested in tests/test_app.py).

- 0.3.0 live since 15 Nov 2026 (after a reboot): the checked solver answers a range question there (91.84 m).
- Testers reported AI explanations full of raw symbols (15 Nov 2026). Cause: Streamlit draws a maths block only
  between lines holding nothing but "$$". The AI writes display maths over several lines, so the converted
  "$$v_x = ..." lost its first line and never closed; and "$$...$$" on one line is drawn as inline maths, where
  equation numbers (	ag) and aligned steps fail. Fixed in 0.3.1: every display formula becomes a real block ("$$",
  the formula on one line, "$$"), keeping the indent of its numbered step. Three real AI answers (two saved in
  tests/data) went from up to 36 raw "$" signs and 5 broken formulas to none, checked in a Streamlit page, in the
  app itself, and at 375 px phone width (no sideways page scroll; two very long formulas scroll inside their own box).
  The testers' feedback rows themselves were not read: the app's key can only add rows, and the Supabase dashboard
  needs his sign-in.
- Found while checking that fix (15 Nov 2026): "Explain how the range formula R = u² sin 2θ / g is derived" was read
  as a range calculation and asked for a launch speed. Questions that ask to derive, prove or explain a formula,
  without measured quantities, now go to the AI tutor (tests in tests/test_flight.py).

## Feedback review and readable AI answers (0.4, 16-17 Nov 2026)
- Feedback read from a CSV export he made (kept in his Downloads, never in the repo; the database was not touched).
  4 rows: 2 from real testers, 1 setup check, 1 live test of our own. Both real reports were the same problem: AI
  answers that could not be read (56 and 94 raw "$" signs as they saw them; one had lost a whole table). 0.3.1
  already shows them with none; their AI answer texts are regression tests (tests/data/tester_report_*.md). No
  wrong answers or feature requests were reported.
- The deeper problem behind the reports: AI answers written like a reference book. Measured with
  `python -m evals.readability` (10 student questions, calls the real AI, run by hand):

  | | Median words | Median formulas | Tables | Headings | Ends with an offer |
  |---|---|---|---|---|---|
  | Before (0.3.1) | 326 | 26 | 1 | 5.5 | 1 of 10 |
  | After (0.4) | 129 | 9 | 0 | 0 | 10 of 10 |

  Reports: evals/readability-before-2026-11-17.md and evals/readability-after-2026-11-17.md. Maths drew correctly
  in 10 of 10 both times.
- What changed: new AI instructions (physicsmind/tutor.py) with two formats — an idea question starts with a plain
  answer; a calculation starts with "Given:", then the formula with its symbols in words, numbered steps, and the
  result once, in bold, at the end. Code now also fixes the AI's writing habits (answer.tidy_text): LaTeX quotes,
  stray "*" bullets, and units like "m s⁻¹" written as "m/s". The feedback choices gained "Hard to read / looks
  broken" and "Too long".
- Found on the way (17 Nov 2026):
  - With the first two drafts of the instructions, calculations still opened with a result, sometimes a wrong one
    later corrected ("50 m" then 25 m; "75 W" then 300 W): 4 of 5 answers. With the two formats, 0 of 5; all five
    results were right (300 W, 40 m, 9 J, 3 m/s², 270 kJ).
  - One answer claimed Earth's gravity is stronger than Jupiter's (false). The instructions now allow comparisons of
    real things only when the facts are certain; two re-asks gave correct figures (Mars 3.7 m/s²).
  - "A car slows from 20 m/s to rest in 4 s. How far does it travel while stopping?" was read as a projectile range
    question and asked which way the car is thrown. A time-of-flight or range question with nothing thrown or
    launched now goes to the AI. The evaluation set stays 140 / 140; the 25 fresh wordings still give 0 wrong.
- Still true: AI answers are not checked. They are shorter and clearer, but one in ten "why" explanations was still
  loosely worded (kinetic energy), and answers vary from run to run.

## Evaluation set (15 Nov 2026)
- 100 questions in `evals/questions.json`, written before PhysicsMind was run on them; expected heights worked out
  by hand and rechecked with plain arithmetic in `tests/test_eval.py`.
- First, blind run: 96 correct, 2 safe misses, **2 dangerous**: "thrown vertically" was assumed upward, and "from a
  height ... above the ground" was answered with the rise only. Safe misses: "vertical velocity" not recognised,
  km/s unknown.
- After fixing the reader: 100 correct; the fixes were also checked on 11 fresh wordings not in the set. The set is
  no longer blind, so new questions from testers or someone else are the next real measure.
- The app's "What PhysicsMind can do" panel shows the score; a test keeps it equal to the real result.
- Time to the top, time of flight and range (later on 15 Nov 2026): 40 questions added before the solver could
  answer them (30 in a new flight_and_range group, 4 of them moved from outside; 10 ambiguous; 4 outside), 140 in
  all. First run: 139 correct, 1 safe miss ("hits a golf ball at 20 m/s" read as a landing speed), 0 dangerous
  (evals/first-run-flight-2026-11-15.md). Because the same person wrote the questions and the reader, 25 fresh
  wordings were then tried: one gave a **wrong number** ("the horizontal distance at that moment", i.e. at the top,
  was answered with the full range) and one was missed ("how far ... does it hit the ground"). All three fixed;
  140 / 140 now, and the fresh wordings are tests in tests/test_flight.py.

## Limitations
- The checked solver answers maximum height, time to the top, time of flight and range for one object in free
  flight that lands on the ground. Throws downward, drops, landing at another level (a roof, a table), the
  greatest possible range, the position at a given time, inverse questions ("what speed reaches 20 m?") and every
  other topic go to the AI tutor, unchecked.
- A question that also asks for something the solver doesn't cover (e.g. the landing speed) goes wholly to the AI tutor.
- "Time of flight" and "range" mean until it reaches the ground; from a raised point, "back to the launch height"
  is asked about instead of guessed.
- Numbers written as words ("twenty") are not read; the reader asks for digits.
- A reply to a clarification is not combined with the earlier question: the student sends the full question again.
- The reader works by word patterns, so unusual wording can still be misread; it is built to refuse rather than
  guess, but it has only been tested on the questions in `tests/` and `evals/questions.json`.
- General chat needs an OpenRouter key; free-model availability and quotas can change.
- No image upload, broad RAG, simulations or adaptive learning yet. Conversation history is session-only.

## Next tasks
1. Keep reading testers' feedback (a CSV export) after each release; turn every wrong checked answer into a test
   and an evaluation question, and re-run `python -m evals.readability` whenever the AI instructions change.
2. Throws downward and drops (time to fall, range of a downward throw), then landing at another level.
3. Straight-line constant-acceleration questions (the solver already supports u, v, a, s, t).
4. Independent checking of AI tutor answers where a formula applies.
5. Image input and visual learning later.

## Token/cost policy
- Use Python/SymPy for deterministic work; a clarification never calls the AI.
- Keep LLM prompts compact.
- No paid model fallback.
- Validate feedback before adding examples to evaluation data.
