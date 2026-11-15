# PhysicsMind — Chat-first Phase 1

A friendly, chat-style physics learning prototype for Windows.

## Included
- Chat-first Streamlit interface with colourful, student-friendly styling.
- Quick starter questions and session chat history.
- Checked answers for a launched object: maximum height, time to reach the top, time of flight and horizontal
  range, alone or together; straight up, at an angle or horizontally from a height. A question reader converts
  units (km/h, cm/s, degrees, radians...), works out what each number means, checks the formulas apply, and each
  answer is worked out two ways (SymPy and a direct formula) that must agree.
  When a question is unclear it asks instead of guessing.
- Optional free AI tutor for general physics questions: Groq first, OpenRouter as the second choice, with a
  per-visit allowance so the free daily answers last. It is labelled unchecked.
- Feedback after each answer, saved with the part that answered and the app version: in SQLite on this
  computer, or in a Supabase table when the app is online.
- No local GPU or local LLM required.

## Setup (Windows PowerShell)

```powershell
py --version
py -3.11 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
streamlit run app.py
```

If PowerShell blocks activation:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\\.venv\\Scripts\\Activate.ps1
```

## Enable AI chat (optional)
1. Create a free key at https://console.groq.com/keys (about 1,000 answers a day) and/or
   https://openrouter.ai/keys (50 a day).
2. Copy `.env.example` to `.env` and add the key(s) after `GROQ_API_KEY=` / `OPENROUTER_API_KEY=`.
   Only keys in this folder's `.env` are used: a key set in Windows for another project is
   deliberately ignored.
3. Restart Streamlit.

No paid fallback is configured. Free-model availability and quotas can change.

## Evaluation set
`evals/questions.json` holds 100 questions with independently worked expected outcomes: 30 straightforward, 30 with
other units and angles, 20 ambiguous or incomplete (must get no number), 20 outside the solver (must go to the AI).

```powershell
python -m evals.run_eval
```

Results are correct, safe miss (no wrong number, but asked or passed to the AI needlessly) or dangerous (a wrong or
unwanted number; must be zero). The first, blind run scored 96 with 2 dangerous (`evals/first-run-2026-11-15.md`);
after fixing the reader it scores 100 (`evals/latest.md`). Since the set has now been fixed against, new questions
written by someone else are the real test. `tests/test_eval.py` stops any change that lowers the score.

## Put it online
See [DEPLOY.md](DEPLOY.md): Streamlit Community Cloud for the app, Supabase for feedback, `main` = live,
`dev` = work in progress.

## Run the tests
```powershell
pip install -r requirements-dev.txt
python -m pytest -q
```

## Current limitations
- General chat requires a free AI key. Each visit may ask `AI_QUESTIONS_PER_VISIT` AI questions (default 10);
  reloading the page starts a new visit, so this slows heavy use rather than stopping it.
- The checked solver answers only projectile questions about one object in free flight that lands on the ground:
  maximum height, time to the top, time of flight and range. Throws downward, drops, landing on a roof or table,
  and every other topic go to the AI tutor and are labelled unchecked.
- Other numerical problems are not yet automatically parsed into solver inputs.
- Feedback is stored locally and is not automatically used to train the model.
- The current solver is not a complete physics verification engine.

## Next milestone
Extend the checked solver to throws downward and drops, and then to straight-line motion, reusing the same
question reader. See PROJECT_STATUS.md.
