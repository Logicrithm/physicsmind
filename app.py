import os
import re
import uuid
import streamlit as st
from dotenv import load_dotenv

from physicsmind.solver import solve_kinematics
from physicsmind.tutor import ask_tutor
from physicsmind.feedback import init_db, save_feedback, feedback_count

load_dotenv(override=True)
init_db()

st.set_page_config(
    page_title="PhysicsMind | Your Physics Buddy",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded",
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

def start_new_chat():
    st.session_state.messages = []
    st.session_state.chat_id = str(uuid.uuid4())
    st.rerun()

def try_vertical_motion(question: str):
    """Small deterministic demo parser for a common maximum-height question."""
    q = question.lower()
    if not any(term in q for term in ("maximum height", "max height", "highest point")):
        return None
    velocity_match = re.search(r"(?:initial velocity|velocity|speed|u)\D{0,25}(-?\d+(?:\.\d+)?)\s*(?:m/s|ms-1)?", q)
    gravity_match = re.search(r"(?:g\s*=?|gravity(?:\s*=?))\s*(9?\.?\d+(?:\.\d+)?)\s*(?:m/s(?:\^?2|²)|ms-2)?", q)
    if not velocity_match:
        velocity_match = re.search(r"(\d+(?:\.\d+)?)\s*m/s", q)
    if not velocity_match:
        return None
    initial = float(velocity_match.group(1))
    gravity = float(gravity_match.group(1)) if gravity_match else 9.8
    if gravity <= 0:
        return None
    result = solve_kinematics({"u": initial, "v": 0, "a": -gravity}, "s")
    if result["status"] != "solved":
        return None
    height = result["value"]
    return (
        "This is vertical motion under gravity. At the highest point, the object's "
        "instantaneous velocity is zero.\n\n"
        "We use the equation:\n\n"
        r"\[v^2 = u^2 + 2as\]" + "\n\n"
        f"**Given:**  u = {initial:g} m/s,  v = 0 m/s,  a = −{gravity:g} m/s²\n\n"
        f"**Substitute:**  0 = ({initial:g})² + 2(−{gravity:g})s\n\n"
        f"**Solve:**  s = {initial:g}² / (2 × {gravity:g})\n\n"
        f"**Answer: {height:.3f} m**\n\n"
        "This assumes constant gravitational acceleration and negligible air resistance."
    ), "SymPy kinematics solver", "symbolic equation solve; assumptions stated"

def make_answer(question):
    parsed = try_vertical_motion(question)
    if parsed:
        answer, model, verification = parsed
        return answer, model, verification, None
    answer, model, error = ask_tutor(question)
    if error:
        return (
            "I’m ready to help! The AI tutor needs a free OpenRouter API key before it can answer general physics questions. "
            "The numerical solver can still handle its supported kinematics calculations.\n\n"
            "To enable chat, add your key to the local `.env` file. See README.md.",
            model or "Not connected", "not verified", None
        )
    return answer, model or "unknown", "LLM response; not independently verified", None

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
    st.caption(f"💬 Feedback saved locally: {feedback_count()}")
    st.caption("Phase 1 • Learning prototype")

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
            st.caption(f"PhysicsMind • {message.get('model', 'AI')} ")
            fid = message.get("id", f"msg_{index}")
            if fid not in st.session_state.feedback_done:
                with st.form(key=f"feedback_form_{fid}"):
                    st.markdown("**Was this explanation helpful?**")
                    rating = st.radio("Your feedback", ["👍 Yes, helpful", "👎 Not quite"], horizontal=True, label_visibility="collapsed")
                    issue = st.selectbox(
                        "Anything we should improve?",
                        ["No issue", "Incorrect formula", "Calculation error", "Explanation unclear", "Missing steps", "Units error", "Other"],
                        label_visibility="collapsed"
                    )
                    comment = st.text_input("Optional note", placeholder="What could we do better?")
                    if st.form_submit_button("Send feedback"):
                        save_feedback(
                            response_id=fid,
                            response_type="chat",
                            question=message.get("question", ""),
                            answer=message["content"],
                            rating="helpful" if rating.startswith("👍") else "not_helpful",
                            issue_category=issue,
                            comment=comment,
                            model=message.get("model", ""),
                            verification_status=message.get("verification", "")
                        )
                        st.session_state.feedback_done.add(fid)
                        st.rerun()
            else:
                st.caption("💚 Thanks — feedback saved!")

# Chat input
pending = st.session_state.pop("pending_prompt", None)
user_prompt = st.chat_input("Ask me a physics question…")
if pending:
    user_prompt = pending

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user", avatar="🧑‍🚀"):
        st.markdown(user_prompt)
    with st.chat_message("assistant", avatar="⚛️"):
        with st.spinner("Thinking it through… ✨"):
            answer, model, verification, _ = make_answer(user_prompt)
        st.markdown(answer)
        st.caption(f"PhysicsMind • {model}")
        st.info("You can rate this answer below. Your feedback is saved locally for later review.")
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "id": str(uuid.uuid4()),
        "question": user_prompt,
        "model": model,
        "verification": verification,
    })
    st.rerun()

if not st.session_state.messages:
    st.markdown('<p class="small-note">💡 Tip: There are no silly questions here. Ask “why?”, ask for an example, or ask us to explain it more simply.</p>', unsafe_allow_html=True)
