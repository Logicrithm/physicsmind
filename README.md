# PhysicsMind — Chat-first Phase 1

A friendly, chat-style physics learning prototype for Windows.

## Included
- Chat-first Streamlit interface with colourful, student-friendly styling.
- Quick starter questions and session chat history.
- Checked answers to maximum-height questions: a question reader converts units (km/h, cm/s, degrees, radians...),
  works out what each number means, checks the formula applies, and SymPy plus the direct formula must agree.
  When a question is unclear it asks instead of guessing.
- Optional OpenRouter AI tutor for general physics questions.
- Feedback after each assistant response, saved locally in SQLite.
- No local GPU or local LLM required.

## Setup (Windows PowerShell)

```powershell
py --version
py -3.11 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\\.venv\\Scripts\\Activate.ps1
```

## Enable AI chat (optional)
1. Create a free API key at https://openrouter.ai/keys
2. Copy `.env.example` to `.env`
3. Add your key after `OPENROUTER_API_KEY=`
4. Keep `OPENROUTER_MODEL=openrouter/free`
5. Restart Streamlit

No paid fallback is configured. Free-model availability and quotas can change.

## Run the tests
```powershell
python -m pytest -q
```

## Current limitations
- General chat requires the optional API key.
- The checked solver answers only maximum-height questions (one object in free flight, straight up or at an angle,
  from the ground or a raised point). Everything else goes to the AI tutor and is labelled unchecked.
- Other numerical problems are not yet automatically parsed into solver inputs.
- Feedback is stored locally and is not automatically used to train the model.
- The current solver is not a complete physics verification engine.

## Next milestone
Extend the checked solver to the rest of projectile motion (time of flight, range) and to straight-line motion,
reusing the same question reader. See PROJECT_STATUS.md.
