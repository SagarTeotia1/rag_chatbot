import os
import sys
from pathlib import Path

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DoshMukti AI",
    page_icon="🕉️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Load secrets into env ─────────────────────────────────────────────────────
for key in ["GROQ_API_KEY", "CHROMA_API_KEY", "CHROMA_TENANT", "CHROMA_DATABASE", "USE_TF", "TF_ENABLE_ONEDNN_OPTS"]:
    try:
        if key in st.secrets and not os.getenv(key):
            os.environ[key] = str(st.secrets[key])
    except Exception:
        pass

# ── Validate keys before importing heavy modules ──────────────────────────────
if not os.getenv("GROQ_API_KEY"):
    st.error("⚠️ GROQ_API_KEY not set. Go to Manage App → Secrets and add your keys.")
    st.stop()

from src.chat.chatbot import ask, _is_greeting

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu, footer, header, [data-testid="stToolbar"], .stDeployButton { display: none !important; }

.stApp {
  background: radial-gradient(ellipse at 20% 20%, #1a0040 0%, #07001a 40%, #0d0025 100%) !important;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.main .block-container {
  max-width: 700px;
  padding: 0 16px 0;
}

/* Shimmer title */
.dm-title {
  background: linear-gradient(90deg, #c084fc, #f0abfc, #c084fc, #a855f7);
  background-size: 200% auto;
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: shimmer 3s linear infinite;
  font-size: 24px; font-weight: 700; letter-spacing: 1px;
}
@keyframes shimmer { to { background-position: 200% center; } }

.dm-sub { font-size: 10px; color: rgba(255,255,255,0.35); letter-spacing: 3px; text-transform: uppercase; }
.dm-divider { height: 1px; background: linear-gradient(90deg, transparent, rgba(147,51,234,0.5), transparent); margin: 8px 0 12px; }

/* Messages */
.msg-user {
  display: flex; justify-content: flex-end; margin: 6px 0;
}
.msg-user-bubble {
  max-width: 75%;
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  padding: 10px 14px; border-radius: 16px 16px 4px 16px;
  font-size: 14px; line-height: 1.6; color: white;
  box-shadow: 0 4px 20px rgba(124,58,237,0.4);
  word-wrap: break-word;
}
.msg-ai { display: flex; gap: 10px; align-items: flex-start; margin: 6px 0; }
.msg-avatar {
  width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0;
  background: linear-gradient(135deg, rgba(147,51,234,0.4), rgba(109,40,217,0.2));
  border: 1px solid rgba(147,51,234,0.5);
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; box-shadow: 0 0 10px rgba(147,51,234,0.3);
}
.msg-ai-bubble {
  max-width: 82%;
  background: linear-gradient(135deg, rgba(255,255,255,0.07), rgba(255,255,255,0.02));
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.1);
  padding: 10px 14px; border-radius: 0 16px 16px 16px;
  font-size: 14px; line-height: 1.7; color: rgba(255,255,255,0.88);
  word-wrap: break-word;
}

/* Typing dots */
.typing-dots { display: flex; gap: 5px; align-items: center; padding: 2px 0; }
.dot { width: 7px; height: 7px; border-radius: 50%; background: #a855f7; animation: dotPulse 1.4s ease-in-out infinite; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes dotPulse { 0%,60%,100% { opacity:0.2; transform:scale(0.8); } 30% { opacity:1; transform:scale(1.2); } }

/* Input */
[data-testid="stTextInput"] input {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(147,51,234,0.35) !important;
  border-radius: 14px !important;
  color: white !important;
  font-size: 14px !important;
}
[data-testid="stTextInput"] input:focus {
  border-color: rgba(147,51,234,0.7) !important;
  box-shadow: 0 0 16px rgba(147,51,234,0.2) !important;
}
[data-testid="stTextInput"] input::placeholder { color: rgba(255,255,255,0.3) !important; }

/* Button */
.stButton > button {
  background: linear-gradient(135deg, #7c3aed, #a855f7) !important;
  border: none !important; border-radius: 14px !important;
  color: white !important; font-weight: 600 !important;
  box-shadow: 0 0 16px rgba(147,51,234,0.4) !important;
  width: 100% !important;
}
.stButton > button:hover { box-shadow: 0 0 28px rgba(147,51,234,0.6) !important; }

/* Suggestion chips */
[data-testid="column"] .stButton > button {
  font-size: 11px !important; padding: 6px 8px !important;
  background: linear-gradient(135deg, rgba(147,51,234,0.15), rgba(109,40,217,0.05)) !important;
  border: 1px solid rgba(147,51,234,0.25) !important;
  box-shadow: none !important; color: rgba(255,255,255,0.7) !important;
  border-radius: 20px !important;
}
[data-testid="column"] .stButton > button:hover {
  border-color: rgba(147,51,234,0.5) !important;
  color: white !important;
}

/* Form submit row */
[data-testid="stForm"] { background: transparent !important; border: none !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending" not in st.session_state:
    st.session_state.pending = None

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:20px 0 8px;">
  <div style="width:46px;height:46px;border-radius:50%;background:linear-gradient(135deg,#7c3aed,#a855f7);
    display:flex;align-items:center;justify-content:center;font-size:19px;margin:0 auto 6px;
    box-shadow:0 0 28px rgba(147,51,234,0.7);">ॐ</div>
  <div class="dm-title">DoshMukti AI</div>
  <div class="dm-sub">Vedic Wisdom · ज्योतिष सहायक</div>
  <div class="dm-divider"></div>
</div>
""", unsafe_allow_html=True)

# ── Message renderer ──────────────────────────────────────────────────────────
def render_msg(role: str, content: str):
    if role == "user":
        st.markdown(f'<div class="msg-user"><div class="msg-user-bubble">{content}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="msg-ai"><div class="msg-avatar">ॐ</div><div class="msg-ai-bubble">{content}</div></div>', unsafe_allow_html=True)

# ── Chat history ──────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    render_msg(msg["role"], msg["content"])

# ── Welcome (empty state) ──────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="msg-ai">
      <div class="msg-avatar">ॐ</div>
      <div class="msg-ai-bubble">
        नमस्ते 🙏 मैं <strong style="color:#c084fc;">Pandit Rameshwar Das Ji</strong> हूँ।<br>
        दोष, उपाय, ग्रह दशा, आर्थिक या रिश्तों की समस्या — कुछ भी पूछें।
      </div>
    </div>
    <div style="height:8px;"></div>
    """, unsafe_allow_html=True)

    SUGGESTIONS = [
        ("मंगल दोष उपाय", "मंगल दोष के उपाय क्या हैं?"),
        ("काल सर्प दोष", "काल सर्प दोष से मुक्ति कैसे पाएं?"),
        ("आर्थिक समस्या", "पैसे की समस्या का ज्योतिष उपाय बताएं"),
        ("शनि साढ़ेसाती", "शनि की साढ़ेसाती में क्या करें?"),
    ]
    cols = st.columns(4)
    for i, (label, question) in enumerate(SUGGESTIONS):
        with cols[i]:
            if st.button(label, key=f"sug_{i}"):
                st.session_state.pending = question
                st.rerun()

# ── Process pending question (suggestion click) ───────────────────────────────
if st.session_state.pending:
    q = st.session_state.pending
    st.session_state.pending = None
    st.session_state.messages.append({"role": "user", "content": q})
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
    render_msg("user", q)

    with st.spinner("Pandit Ji सोच रहे हैं..."):
        response = ask(q, chat_history=history, stream=False)

    st.session_state.messages.append({"role": "assistant", "content": response})
    render_msg("assistant", response)

# ── Input form ────────────────────────────────────────────────────────────────
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

with st.form("chat_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input(
            label="input",
            placeholder="अपना प्रश्न पूछें... (Hindi / English)",
            label_visibility="collapsed",
        )
    with col2:
        submitted = st.form_submit_button("भेजें")

if submitted and user_input.strip():
    q = user_input.strip()
    st.session_state.messages.append({"role": "user", "content": q})
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
    render_msg("user", q)

    with st.spinner("Pandit Ji सोच रहे हैं..."):
        response = ask(q, chat_history=history, stream=False)

    st.session_state.messages.append({"role": "assistant", "content": response})
    render_msg("assistant", response)
