# PhysicsMind — Chat-first Phase 1

A friendly, chat-style physics learning prototype for Windows.

## Included
- Chat-first Streamlit interface with colourful, student-friendly styling.
- Quick starter questions and session chat history.
- Checked answers to maximum-height questions: a question reader converts units (km/h, cm/s, degrees, radians...),
  works out what each number means, checks the formula applies, and SymPy plus the direct formula must agree.
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
- The checked solver answers only maximum-height questions (one object in free flight, straight up or at an angle,
  from the ground or a raised point). Everything else goes to the AI tutor and is labelled unchecked.
- Other numerical problems are not yet automatically parsed into solver inputs.
- Feedback is stored locally and is not automatically used to train the model.
- The current solver is not a complete physics verification engine.

## Next milestone
Extend the checked solver to the rest of projectile motion (time of flight, range) and to straight-line motion,
reusing the same question reader. See PROJECT_STATUS.md.
