# Putting PhysicsMind online

Everything here is free. The app runs on Streamlit Community Cloud, feedback is saved in a Supabase table, and the
AI tutor uses free Groq and OpenRouter keys. Keys go only into the host's Secrets page, never into GitHub.

## How versions work
- `main` is the live version. Streamlit picks up a change to `main` by itself, but when only code changed (not
  `requirements.txt`) the running app can keep the old code: on 15 Nov 2026 it still showed 0.2.2 five minutes
  after 0.3.0 was pushed. After every release, check the version label at the bottom of the live page; if it is
  old, open share.streamlit.io, click ⋮ next to the app and choose **Reboot**.
- `dev` is where work happens. A change moves to `main` only after `python -m pytest -q` passes (and, once it
  exists, the evaluation set), so testers never see half-finished work.
- Every feedback row stores the app version that gave the answer (the number in `physicsmind/__init__.py`,
  plus the git commit when the host has it). Raise that number with each release to `main`.

## One-time setup (about 15 minutes)

### 1. GitHub repository (done 15 Nov 2026)
The code is at https://github.com/Logicrithm/physicsmind, **public** by choice: it holds no keys, passwords or
personal data (checked before the first upload), Streamlit then only needs to read public code, and it can be
shown on the portfolio. Anyone can read the code; nobody can change it without your GitHub account.

### 2. Supabase (where online feedback is kept)
1. Sign in at https://supabase.com (signing in with GitHub works) and create a **New project**. Pick the region
   nearest your testers (for India: Mumbai). Keep the database password somewhere safe; the app does not need it.
2. Open **SQL Editor**, then **New query**. Paste all of `deploy/supabase_feedback.sql`, then click **Run**.
   The result should say "Success. No rows returned".
3. Open **Project Settings → API Keys**. Copy the **Project URL** and the **publishable** key (it starts with
   `sb_publishable_`; on older projects it is called the `anon` key). Do **not** use the secret / service_role key:
   the app only needs to add feedback, and the setup script allows that key nothing else.

Free Supabase projects pause after a week with no activity. If testing stops for a while, open the project in
the dashboard and press **Restore** before sharing the link again. While a project is paused the app tells
the tester their feedback wasn't saved instead of losing it silently.

### 3. Groq key (more free AI answers)
Sign in at https://console.groq.com, open **API Keys**, then **Create API Key** and name it `PhysicsMind`.
No card is needed. Use a new key, not one that belongs to another project: then either app's key can be revoked without breaking
the other, and the Groq dashboard shows which app made which requests. Paste it after `GROQ_API_KEY=` in this
folder's `.env` for local use, and into the Secrets page below for the online app. Your existing OpenRouter key
stays as the second choice.

Groq's free limits apply to the whole Groq account, not to each key, so if both keys are in the same account,
the apps share the same 1,000 answers a day.

PhysicsMind ignores a `GROQ_API_KEY` set in Windows (for example one that belongs to another project), so it is never
used here even though it is set on this computer.

### 4. Streamlit Community Cloud
1. Sign in at https://share.streamlit.io with GitHub and allow it to see the `physicsmind` repository.
2. **Create app** → **Deploy a public app from GitHub**. Repository `<your-user>/physicsmind`, branch `main`,
   main file `app.py`. Choose a link name, for example `physicsmind`.
3. Open **Advanced settings**: choose **Python 3.11**, and paste this into **Secrets**, with your own values:

   ```toml
   GROQ_API_KEY = "gsk_..."
   GROQ_MODEL = "openai/gpt-oss-120b"
   OPENROUTER_API_KEY = "sk-or-..."
   OPENROUTER_MODEL = "openrouter/free"
   AI_QUESTIONS_PER_VISIT = "10"
   SUPABASE_URL = "https://<your-project>.supabase.co"
   SUPABASE_KEY = "sb_publishable_..."
   ```
4. Click **Deploy**. The first build takes a few minutes.

### 5. Check it works
1. Open the app's link. The sidebar should say "Feedback is saved online for review" and show the version.
2. Tap **Solve a motion problem**. It should answer 20.41 m.
3. Send feedback on that answer. In Supabase, open **Table Editor → response_feedback**; the row should be there.
4. Ask a general question, such as "Why is the sky blue?". The caption under the answer should name the model
   and "via Groq".

## Reading the feedback
In Supabase **Table Editor → response_feedback**, sort by `created_at`. Filter `rating = not_helpful` to see the
complaints. `response_type` says which part answered (`solver`, `clarification`, `ai_tutor`, `ai_unavailable`
or `ai_limit`), and `app_version` says which release gave the answer.

## Security checklist
What protects the app, and what you must keep doing:

- **The repository is public, so never commit a secret.** `.gitignore` keeps `.env`, databases and backups out.
  Before each release, `git status` should list no `.env`, `.db` or `secrets` file. If a key is ever committed,
  treat it as leaked even if you delete it again: replace the key (below).
- **Turn on two-factor sign-in for GitHub** (Settings → Password and authentication). Streamlit and Supabase
  can be signed into through GitHub, so your GitHub account protects all three.
- **Never add a payment card to Groq or OpenRouter.** On free plans a leaked key can only use up free answers;
  it can never cost money.
- **Keys live in two places only:** `.env` on this computer and the Streamlit Secrets page. Never paste a key into
  a chat, an issue, a screenshot, or a file in the repository.
- **If a key ever leaks:** delete it on the provider's site (Groq → API Keys, OpenRouter → Keys, or Supabase →
  API Keys), create a new one, and paste the new one into `.env` and the Secrets page. Nothing in the code changes.
- **Supabase:** give the app only the publishable key. The setup script lets that key add feedback rows and
  nothing else, so even someone holding it cannot read, change or delete feedback. Never use the
  `service_role` / secret key anywhere in PhysicsMind.

Built into the app:
- Questions over 1,500 characters are refused before anything runs. Each visit may ask 10 AI questions and send
  40 pieces of feedback. Long text is cut before it is stored.
- Visitors never see error details, code or file paths. The developer menu is hidden.
- Text from visitors and from the AI is shown as plain formatted text, never as HTML.
- Keys never reach the browser, and technical errors are logged with keys removed.
- Keys set in Windows for other projects are ignored.
- The live site installs exact, tested library versions (`requirements.txt`).

## Limits to know about
- **AI answers are shared.** Groq's free plan allows 1,000 answers a day on `openai/gpt-oss-120b` (and 8,000 tokens a
  minute, so a burst of long answers can briefly spill over to OpenRouter), and OpenRouter's free models 50 a day
  for the whole account. These are 15 Nov 2026 figures; providers change them. Each visit may ask
  `AI_QUESTIONS_PER_VISIT` AI questions. Reloading the page starts a new visit, so this slows heavy use rather
  than stopping it. Checked projectile answers and clarifications never use the AI.
- **The app sleeps** after 12 hours with no visitors. The next visitor waits about a minute while it wakes.
- **Testers' questions are stored.** The app asks them not to include personal details. It collects no names or
  emails.
