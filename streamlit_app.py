import os
import sys
import time
from pathlib import Path

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.chat.chatbot import ask, _is_greeting

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DoshMukti AI",
    page_icon="🕉️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
[data-testid="stToolbar"] { display: none; }
.stApp > header { display: none; }

/* Body */
.stApp {
  background: radial-gradient(ellipse at 20% 20%, #1a0040 0%, #07001a 40%, #0d0025 100%);
  font-family: 'Inter', sans-serif;
}

/* Stars canvas */
#stars-bg {
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(1px 1px at 10% 15%, rgba(255,255,255,0.6) 0%, transparent 100%),
    radial-gradient(1px 1px at 25% 40%, rgba(255,255,255,0.4) 0%, transparent 100%),
    radial-gradient(1.5px 1.5px at 40% 8%, rgba(255,255,255,0.7) 0%, transparent 100%),
    radial-gradient(1px 1px at 55% 60%, rgba(255,255,255,0.3) 0%, transparent 100%),
    radial-gradient(2px 2px at 70% 20%, rgba(255,255,255,0.5) 0%, transparent 100%),
    radial-gradient(1px 1px at 80% 75%, rgba(255,255,255,0.6) 0%, transparent 100%),
    radial-gradient(1.5px 1.5px at 90% 35%, rgba(255,255,255,0.4) 0%, transparent 100%),
    radial-gradient(1px 1px at 15% 80%, rgba(255,255,255,0.5) 0%, transparent 100%),
    radial-gradient(1px 1px at 35% 55%, rgba(255,255,255,0.3) 0%, transparent 100%),
    radial-gradient(2px 2px at 60% 90%, rgba(255,255,255,0.4) 0%, transparent 100%),
    radial-gradient(1px 1px at 5% 50%, rgba(255,255,255,0.6) 0%, transparent 100%),
    radial-gradient(1.5px 1.5px at 48% 30%, rgba(255,255,255,0.5) 0%, transparent 100%),
    radial-gradient(1px 1px at 75% 50%, rgba(255,255,255,0.3) 0%, transparent 100%),
    radial-gradient(2px 2px at 88% 10%, rgba(255,255,255,0.6) 0%, transparent 100%),
    radial-gradient(1px 1px at 20% 95%, rgba(255,255,255,0.4) 0%, transparent 100%),
    radial-gradient(ellipse at 10% 10%, rgba(124,58,237,0.25) 0%, transparent 50%),
    radial-gradient(ellipse at 90% 80%, rgba(168,85,247,0.2) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 50%, rgba(109,40,217,0.1) 0%, transparent 70%);
}

/* Main container */
.main .block-container {
  max-width: 720px;
  padding: 0 16px 20px;
  position: relative; z-index: 1;
}

/* Header */
.dm-header {
  text-align: center;
  padding: 24px 0 12px;
}
.dm-logo {
  width: 48px; height: 48px;
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px;
  box-shadow: 0 0 28px rgba(147,51,234,0.7), 0 0 56px rgba(147,51,234,0.2);
  margin: 0 auto 8px;
}
.dm-title {
  font-size: 26px; font-weight: 700; letter-spacing: 1px;
  background: linear-gradient(90deg, #c084fc, #f0abfc, #c084fc, #a855f7);
  background-size: 200% auto;
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: shimmer 3s linear infinite;
}
.dm-sub {
  font-size: 11px; color: rgba(255,255,255,0.35);
  letter-spacing: 3px; text-transform: uppercase; margin-top: 4px;
}
.dm-divider {
  height: 1px; margin: 10px 0;
  background: linear-gradient(90deg, transparent, rgba(147,51,234,0.5), transparent);
}
@keyframes shimmer { to { background-position: 200% center; } }

/* Chat messages */
.msg-user {
  display: flex; justify-content: flex-end; margin: 8px 0;
}
.msg-user-bubble {
  max-width: 75%;
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  padding: 10px 14px; border-radius: 16px 16px 4px 16px;
  font-size: 14px; line-height: 1.6; color: white;
  box-shadow: 0 4px 20px rgba(124,58,237,0.4);
}
.msg-ai {
  display: flex; gap: 10px; align-items: flex-start; margin: 8px 0;
}
.msg-avatar {
  width: 32px; height: 32px; border-radius: 50%;
  background: linear-gradient(135deg, rgba(147,51,234,0.4), rgba(109,40,217,0.2));
  border: 1px solid rgba(147,51,234,0.5);
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; flex-shrink: 0;
  box-shadow: 0 0 12px rgba(147,51,234,0.3);
}
.msg-ai-bubble {
  max-width: 82%;
  background: linear-gradient(135deg, rgba(255,255,255,0.07), rgba(255,255,255,0.02));
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.1);
  padding: 12px 16px; border-radius: 0 16px 16px 16px;
  font-size: 14px; line-height: 1.7; color: rgba(255,255,255,0.88);
}

/* Typing dots */
.typing-dots { display: flex; gap: 5px; align-items: center; padding: 4px 0; }
.dot {
  width: 8px; height: 8px; border-radius: 50%; background: #a855f7;
  animation: dotPulse 1.4s ease-in-out infinite;
}
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes dotPulse {
  0%, 60%, 100% { opacity: 0.2; transform: scale(0.8); }
  30% { opacity: 1; transform: scale(1.2); }
}

/* Input area */
[data-testid="stTextInput"] input,
.stTextInput input {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(147,51,234,0.3) !important;
  border-radius: 14px !important;
  color: white !important;
  font-size: 14px !important;
  padding: 12px 16px !important;
}
[data-testid="stTextInput"] input:focus {
  border-color: rgba(147,51,234,0.6) !important;
  box-shadow: 0 0 20px rgba(147,51,234,0.15) !important;
}
[data-testid="stTextInput"] input::placeholder { color: rgba(255,255,255,0.3) !important; }

/* Send button */
.stButton > button {
  background: linear-gradient(135deg, #7c3aed, #a855f7) !important;
  border: none !important;
  border-radius: 14px !important;
  color: white !important;
  font-weight: 600 !important;
  padding: 12px 24px !important;
  box-shadow: 0 0 20px rgba(147,51,234,0.4) !important;
  transition: all 0.2s !important;
  width: 100% !important;
}
.stButton > button:hover {
  box-shadow: 0 0 30px rgba(147,51,234,0.6) !important;
  transform: translateY(-1px) !important;
}

/* Suggestion chips */
.chip-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0 16px 42px; }
.chip {
  font-size: 11px; padding: 5px 12px; border-radius: 20px;
  border: 1px solid rgba(147,51,234,0.25);
  background: linear-gradient(135deg, rgba(147,51,234,0.1), rgba(109,40,217,0.05));
  color: rgba(255,255,255,0.65); cursor: pointer;
  display: inline-block;
}

/* Scrollable chat area */
.chat-area { max-height: 60vh; overflow-y: auto; padding-right: 4px; }
.chat-area::-webkit-scrollbar { width: 3px; }
.chat-area::-webkit-scrollbar-thumb { background: rgba(147,51,234,0.4); border-radius: 2px; }
</style>

<div id="stars-bg"></div>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending" not in st.session_state:
    st.session_state.pending = None


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dm-header">
  <div class="dm-logo">ॐ</div>
  <div class="dm-title">DoshMukti AI</div>
  <div class="dm-sub">Vedic Wisdom · ज्योतिष सहायक</div>
  <div class="dm-divider"></div>
</div>
""", unsafe_allow_html=True)


# ── Render chat history ───────────────────────────────────────────────────────
def render_message(role: str, content: str):
    if role == "user":
        st.markdown(f"""
        <div class="msg-user">
          <div class="msg-user-bubble">{content}</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="msg-ai">
          <div class="msg-avatar">ॐ</div>
          <div class="msg-ai-bubble">{content}</div>
        </div>""", unsafe_allow_html=True)


for msg in st.session_state.messages:
    render_message(msg["role"], msg["content"])


# ── Welcome + suggestions (first load) ───────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="msg-ai">
      <div class="msg-avatar">ॐ</div>
      <div class="msg-ai-bubble">
        नमस्ते 🙏 मैं <strong style="color:#c084fc;">Pandit Rameshwar Das Ji</strong> हूँ — आपका Vedic ज्योतिष सहायक।<br>
        दोष, उपाय, ग्रह दशा, आर्थिक या रिश्तों की समस्या — कुछ भी पूछें।<br>
        <span style="color:rgba(255,255,255,0.4);font-size:12px;">Hindi या English — दोनों में।</span>
      </div>
    </div>
    <div class="chip-row">
      <span class="chip">मंगल दोष उपाय</span>
      <span class="chip">काल सर्प दोष</span>
      <span class="chip">आर्थिक समस्या</span>
      <span class="chip">शनि साढ़ेसाती</span>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    suggestions = ["मंगल दोष के उपाय क्या हैं?", "काल सर्प दोष से मुक्ति?", "पैसे की समस्या का उपाय", "शनि साढ़ेसाती में क्या करें?"]
    for i, col in enumerate(cols):
        with col:
            if st.button(suggestions[i].split("?")[0][:18] + "?", key=f"sug_{i}"):
                st.session_state.pending = suggestions[i]
                st.rerun()


# ── Process pending (from suggestion click) ───────────────────────────────────
if st.session_state.pending:
    question = st.session_state.pending
    st.session_state.pending = None
    st.session_state.messages.append({"role": "user", "content": question})
    render_message("user", question)

    with st.spinner(""):
        st.markdown("""<div class="msg-ai"><div class="msg-avatar">ॐ</div>
        <div class="msg-ai-bubble"><div class="typing-dots">
          <div class="dot"></div><div class="dot"></div><div class="dot"></div>
        </div></div></div>""", unsafe_allow_html=True)
        history = st.session_state.messages[:-1]
        response = ask(question, chat_history=history, stream=False)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()


# ── Input bar ─────────────────────────────────────────────────────────────────
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

with st.form("chat_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input(
            label="",
            placeholder="अपना प्रश्न पूछें... (Hindi / English)",
            label_visibility="collapsed",
        )
    with col2:
        submitted = st.form_submit_button("भेजें →")

if submitted and user_input.strip():
    question = user_input.strip()
    st.session_state.messages.append({"role": "user", "content": question})
    render_message("user", question)

    st.markdown("""<div class="msg-ai"><div class="msg-avatar">ॐ</div>
    <div class="msg-ai-bubble"><div class="typing-dots">
      <div class="dot"></div><div class="dot"></div><div class="dot"></div>
    </div></div></div>""", unsafe_allow_html=True)

    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
    response = ask(question, chat_history=history, stream=False)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
