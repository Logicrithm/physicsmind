# PhysicsMind — Chat-first Phase 1

A friendly, chat-style physics learning prototype for Windows.

## Included
- Chat-first Streamlit interface with colourful, student-friendly styling.
- Quick starter questions and session chat history.
- SymPy-powered answer for a narrow vertical maximum-height question pattern.
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

## Current limitations
- General chat requires the optional API key.
- The built-in deterministic parser currently recognizes a narrow vertical maximum-height question pattern.
- Other numerical problems are not yet automatically parsed into solver inputs.
- Feedback is stored locally and is not automatically used to train the model.
- The current solver is not a complete physics verification engine.

## Next milestone
Natural-language question extraction, formula applicability checks, broader topic coverage, and independently verified worked solutions.
