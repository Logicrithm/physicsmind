import uuid
import streamlit as st
from dotenv import load_dotenv

from physicsmind.about import ABOUT, TITLE as ABOUT_TITLE
from physicsmind.answer import MAX_QUESTION_CHARS, make_answer
from physicsmind.config import use_only_own_keys, whole_number
from physicsmind.feedback import FeedbackNotSaved, choose_store
from physicsmind.version import app_version

use_only_own_keys()  # a Groq key set in Windows for another project must not be used here
load_dotenv(override=True)
store = choose_store()  # Supabase when SUPABASE_URL and SUPABASE_KEY are set, else physicsmind.db on this computer
VERSION = app_version()
# Each visit may ask the AI tutor this many questions, so the free daily allowance lasts for every tester. 0 = AI off.
AI_PER_VISIT = whole_number("AI_QUESTIONS_PER_VISIT", 10)
# Each visit may send this much feedback, so a script can't flood the free feedback database.
FEEDBACK_PER_VISIT = 40
NOTE_CHARS = 500
PRIVACY_NOTE = ("Questions and feedback you send are saved to improve PhysicsMind, and general questions are sent to an "
                "outside AI service (Groq or OpenRouter) to be answered. Please don’t include your name, contact details "
                "or anything personal.")

st.set_page_config(
    page_title="PhysicsMind | Your Physics Buddy",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="auto",  # open on computers, closed on phones so it does not cover the chat
)

# ---------- Visual design ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800;900&display=swap');
:root {
  --ink: #0f172a;
  --muted: #475569;
  --blue: #2563eb;
  --purple: #7657e8;
  --mint: #dff8ef;
  --paper: #f8faff;
}
html, body, [class*="css"] {
  font-family: 'Nunito', sans-serif;
}
.stApp {
  background: linear-gradient(135deg, #f8faff 0%, #f0f4ff 55%, #eef8ff 100%);
  color: #0f172a !important;
}
[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 1120px; padding-top: 1.35rem; padding-bottom: 7rem; }

/* Sidebar styling */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #172554 0%, #243b75 100%) !important;
  border-right: 0;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] label {
  color: #f8fbff !important;
  -webkit-text-fill-color: #f8fbff !important;
}
[data-testid="stSidebar"] .stButton button {
  background: rgba(255, 255, 255, 0.18) !important;
  border: 1px solid rgba(255, 255, 255, 0.35) !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  font-weight: 800 !important;
}
[data-testid="stSidebar"] .stButton button:hover {
  background: rgba(255, 255, 255, 0.3) !important;
}

/* Brand & Hero */
.brand-card {
  background: linear-gradient(135deg, #3b82f6, #7c3aed);
  color: white !important; padding: 1.1rem 1.15rem; border-radius: 22px;
  box-shadow: 0 12px 28px rgba(70,104,220,.25); margin-bottom: 1rem;
}
.brand-card h1 { color:white !important; -webkit-text-fill-color: white !important; font-size:1.65rem; margin:0; font-weight:900; }
.brand-card p { color:#edf3ff !important; -webkit-text-fill-color: #edf3ff !important; margin:.2rem 0 0 0; font-size:.95rem; }
.hero {
  background: linear-gradient(115deg, #dbeafe 0%, #ede9fe 55%, #d1fae5 100%);
  border: 1px solid #bfdbfe; border-radius: 24px; padding: 1.2rem 1.5rem;
  margin-bottom: 1.1rem; box-shadow: 0 8px 25px rgba(80,105,170,.08);
}
.hero h2 { color:#1e3a8a !important; -webkit-text-fill-color: #1e3a8a !important; margin:0; font-size:1.65rem; font-weight:900; }
.hero p { color:#334155 !important; -webkit-text-fill-color: #334155 !important; margin:.25rem 0 0 0; font-weight:600; }
.pill {
  display:inline-block; background:#ffffff; color:#4338ca !important;
  -webkit-text-fill-color: #4338ca !important;
  padding:.3rem .75rem; border-radius:999px; font-size:.8rem;
  font-weight:800; margin:.2rem .25rem .1rem 0; border:1px solid #cbd5e1;
}

/* Feature cards */
.feature-card {
  background:#ffffff !important; border:1px solid #cbd5e1; border-radius:18px;
  padding:.95rem 1.05rem; min-height:108px; box-shadow:0 6px 16px rgba(30,60,120,.06);
}
.feature-card b { color:#1e293b !important; -webkit-text-fill-color: #1e293b !important; font-size:1rem; }
.feature-card span { color:#475569 !important; -webkit-text-fill-color: #475569 !important; font-size:.85rem; font-weight:500; }
.small-note { color:#475569 !important; -webkit-text-fill-color: #475569 !important; font-size:.85rem; }

/* Chat Input: clearly visible typed text and placeholder */
div[data-testid="stChatInput"] {
  background-color: #ffffff !important;
  border: 2px solid #93c5fd !important;
  border-radius: 22px !important;
  box-shadow: 0 8px 26px rgba(37,99,235,.15) !important;
}
div[data-testid="stChatInput"] textarea {
  font-family: 'Nunito', sans-serif !important;
  color: #0f172a !important;
  -webkit-text-fill-color: #0f172a !important;
  background-color: transparent !important;
  font-size: 1.02rem !important;
  font-weight: 600 !important;
  caret-color: #2563eb !important;
}
div[data-testid="stChatInput"] textarea::placeholder {
  color: #64748b !important;
  -webkit-text-fill-color: #64748b !important;
  opacity: 1 !important;
}
div[data-testid="stChatInput"] button {
  color: #2563eb !important;
}
div[data-testid="stChatInput"] button svg {
  fill: #2563eb !important;
}

/* Chat Messages: high-contrast card style with dark text */
[data-testid="stChatMessage"] {
  background-color: #ffffff !important;
  border: 1px solid #cbd5e1 !important;
  border-radius: 18px !important;
  padding: 1.1rem 1.35rem !important;
  margin-bottom: 0.95rem !important;
  box-shadow: 0 4px 18px rgba(30,50,110,.06) !important;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] span,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] div,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] strong,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] b {
  color: #0f172a !important;
  -webkit-text-fill-color: #0f172a !important;
  font-size: 1.02rem !important;
  line-height: 1.65 !important;
}
[data-testid="stChatMessage"] code {
  color: #1e3a8a !important;
  -webkit-text-fill-color: #1e3a8a !important;
  background-color: #eff6ff !important;
  padding: 0.18rem 0.45rem !important;
  border-radius: 6px !important;
  border: 1px solid #bfdbfe !important;
}
[data-testid="stChatMessage"] .katex,
[data-testid="stChatMessage"] .katex * {
  color: #0f172a !important;
  -webkit-text-fill-color: #0f172a !important;
}
[data-testid="stChatMessage"] [data-testid="stCaptionContainer"] p {
  color: #475569 !important;
  -webkit-text-fill-color: #475569 !important;
  font-size: 0.85rem !important;
}

/* Buttons */
.stButton button {
  border-radius: 14px !important;
  border: 1px solid #94a3b8 !important;
  font-weight: 800 !important;
  color: #1e3a8a !important;
  -webkit-text-fill-color: #1e3a8a !important;
  background: #ffffff !important;
  transition: all .15s ease !important;
}
.stButton button:hover {
  border-color: #2563eb !important;
  color: #2563eb !important;
  -webkit-text-fill-color: #2563eb !important;
  background: #eff6ff !important;
}

/* Feedback Form Controls */
div[data-testid="stForm"] {
  background: #f8faff !important;
  border: 1px solid #cbd5e1 !important;
  padding: 1rem !important;
  border-radius: 16px !important;
  margin-top: 0.8rem !important;
}
div[data-testid="stForm"] label,
div[data-testid="stForm"] p,
div[data-testid="stForm"] span,
div[data-testid="stForm"] strong {
  color: #0f172a !important;
  -webkit-text-fill-color: #0f172a !important;
}
div[data-testid="stForm"] input[type="text"] {
  color: #0f172a !important;
  -webkit-text-fill-color: #0f172a !important;
  background-color: #ffffff !important;
  border: 1px solid #94a3b8 !important;
  border-radius: 10px !important;
  font-size: 0.95rem !important;
}
div[data-testid="stForm"] input[type="text"]::placeholder {
  color: #64748b !important;
  -webkit-text-fill-color: #64748b !important;
}
div[data-testid="stForm"] div[data-baseweb="select"] {
  background-color: #ffffff !important;
  border: 1px solid #94a3b8 !important;
  border-radius: 10px !important;
}
div[data-testid="stForm"] div[data-baseweb="select"] * {
  color: #0f172a !important;
  -webkit-text-fill-color: #0f172a !important;
}
hr { border-color: #cbd5e1 !important; }
</style>
""", unsafe_allow_html=True)

# ---------- State and helpers ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_id" not in st.session_state:
    st.session_state.chat_id = str(uuid.uuid4())
if "feedback_done" not in st.session_state:
    st.session_state.feedback_done = set()
if "ai_used" not in st.session_state:
    st.session_state.ai_used = 0
if "feedback_sent" not in st.session_state:
    st.session_state.feedback_sent = 0

def start_new_chat():
    st.session_state.messages = []
    st.session_state.chat_id = str(uuid.uuid4())
    st.rerun()

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("""
    <div class="brand-card">
      <h1>⚛️ PhysicsMind</h1>
      <p>Your curious physics buddy</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("＋  New chat", use_container_width=True):
        start_new_chat()
    st.markdown("#### 🗂️ Your chats")
    if st.session_state.messages:
        first_user = next((m["content"] for m in st.session_state.messages if m["role"] == "user"), "Physics chat")
        st.caption(first_user[:42] + ("…" if len(first_user) > 42 else ""))
    else:
        st.caption("Your conversations will appear here.")
    st.markdown("---")
    st.markdown("#### 🧰 Study corner")
    st.markdown("📘 Formula explorer  \n🧪 Physics topics  \n🎯 Practice questions")
    st.markdown("---")
    saved = store.count()
    st.caption(f"💬 Feedback saved on this computer: {saved}" if saved is not None else "💬 Feedback is saved online for review")
    st.caption(f"Phase 1 • Learning prototype • version {VERSION}")

# ---------- Main header ----------
st.markdown("""
<div class="hero">
  <h2>Hey there, future scientist! ✨</h2>
  <p>Ask anything about physics. We’ll figure it out together — one step at a time.</p>
  <span class="pill">🧠 Understand concepts</span>
  <span class="pill">🧮 Solve problems</span>
  <span class="pill">🚀 Learn by asking</span>
</div>
""", unsafe_allow_html=True)

# What it can do and how testers can help. On the main page, not the sidebar, because phones keep the sidebar closed.
with st.expander(ABOUT_TITLE, expanded=False):
    st.markdown(ABOUT)

# Quick starters when chat is empty
if not st.session_state.messages:
    st.markdown("### What are we curious about today?")
    cols = st.columns(3)
    starters = [
        ("🍎", "Why do things fall?", "Why do objects fall towards Earth? Explain gravity simply."),
        ("🚀", "Solve a motion problem", "An object is thrown vertically upward with an initial velocity of 20 m/s. Find its maximum height. Take g = 9.8 m/s^2."),
        ("⚡", "Explain electricity", "Explain the difference between voltage and current with a simple example."),
    ]
    for col, (emoji, title, prompt) in zip(cols, starters):
        with col:
            st.markdown(f'<div class="feature-card"><b>{emoji} {title}</b><br><span>Tap below to explore this question.</span></div>', unsafe_allow_html=True)
            if st.button("Try this ↗", key=f"starter_{title}", use_container_width=True):
                st.session_state.pending_prompt = prompt
                st.rerun()

# Render conversation
for index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"], avatar="🧑‍🚀" if message["role"] == "user" else "⚛️"):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            st.caption(f"PhysicsMind • {message.get('model', 'AI')} • {message.get('verification', 'not verified')}")
            fid = message.get("id", f"msg_{index}")
            if fid not in st.session_state.feedback_done and st.session_state.feedback_sent >= FEEDBACK_PER_VISIT:
                st.caption("Thanks for all your feedback this visit! You've reached the limit for one visit.")
            elif fid not in st.session_state.feedback_done:
                with st.form(key=f"feedback_form_{fid}"):
                    st.markdown("**Was this explanation helpful?**")
                    rating = st.radio("Your feedback", ["👍 Yes, helpful", "👎 Not quite"], horizontal=True, label_visibility="collapsed")
                    issue = st.selectbox(
                        "Anything we should improve?",
                        ["No issue", "Incorrect formula", "Calculation error", "Explanation unclear", "Missing steps", "Units error", "Other"],
                        label_visibility="collapsed"
                    )
                    comment = st.text_input("Optional note", placeholder="What could we do better?", max_chars=NOTE_CHARS)
                    if st.form_submit_button("Send feedback"):
                        try:
                            store.save(
                                response_id=fid,
                                response_type=message.get("response_type", "chat"),
                                question=message.get("question", ""),
                                answer=message["content"],
                                rating="helpful" if rating.startswith("👍") else "not_helpful",
                                issue_category=issue,
                                comment=comment,
                                model=message.get("model", ""),
                                verification_status=message.get("verification", ""),
                                app_version=message.get("app_version", VERSION),
                            )
                        except FeedbackNotSaved as problem:
                            st.error(f"Sorry, your feedback wasn't saved because {problem}. Please try sending it again.")
                        else:
                            st.session_state.feedback_done.add(fid)
                            st.session_state.feedback_sent += 1
                            st.rerun()
            else:
                st.caption("💚 Thanks — feedback saved!")

# Chat input
pending = st.session_state.pop("pending_prompt", None)
user_prompt = st.chat_input("Ask me a physics question…", max_chars=MAX_QUESTION_CHARS)
if pending:
    user_prompt = pending

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user", avatar="🧑‍🚀"):
        st.markdown(user_prompt)
    with st.chat_message("assistant", avatar="⚛️"):
        with st.spinner("Thinking it through… ✨"):
            answer = make_answer(user_prompt, ai_allowed=st.session_state.ai_used < AI_PER_VISIT)
        if answer.used_ai:
            st.session_state.ai_used += 1
        st.markdown(answer.text)
        st.caption(f"PhysicsMind • {answer.source} • {answer.verification}")
        st.info(f"You can rate this answer below. Feedback is saved {store.where}. {PRIVACY_NOTE}")
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer.text,
        "id": str(uuid.uuid4()),
        "question": user_prompt,
        "model": answer.source,
        "verification": answer.verification,
        "response_type": answer.response_type,
        "app_version": VERSION,
    })
    st.rerun()

if not st.session_state.messages:
    st.markdown('<p class="small-note">💡 Tip: There are no silly questions here. Ask “why?”, ask for an example, or ask us to explain it more simply.</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="small-note">🔒 {PRIVACY_NOTE}</p>', unsafe_allow_html=True)  # fixed text only
