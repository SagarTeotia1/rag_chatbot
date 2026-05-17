import os
import sys
from pathlib import Path

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="DoshMukti AI",
    page_icon="🕉️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Load secrets ──────────────────────────────────────────────────────────────
for key in ["GROQ_API_KEY", "CHROMA_API_KEY", "CHROMA_TENANT", "CHROMA_DATABASE", "USE_TF", "TF_ENABLE_ONEDNN_OPTS"]:
    try:
        if key in st.secrets and not os.getenv(key):
            os.environ[key] = str(st.secrets[key]).strip()
    except Exception:
        pass

if not os.getenv("GROQ_API_KEY"):
    st.error("⚠️ GROQ_API_KEY missing. Go to Manage App → Secrets and add it.")
    st.stop()

from src.chat.chatbot import ask, _is_greeting

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu, footer, header, [data-testid="stToolbar"], .stDeployButton,
[data-testid="stDecoration"] { display: none !important; }

html, body, .stApp {
  height: 100%;
  background: radial-gradient(ellipse at 20% 20%, #1a0040 0%, #07001a 40%, #0d0025 100%) !important;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* Remove all default padding */
.main .block-container {
  max-width: 700px !important;
  padding: 0 16px !important;
  padding-bottom: 100px !important;  /* space for fixed input */
}

/* Shimmer */
@keyframes shimmer { to { background-position: 200% center; } }
@keyframes dotPulse { 0%,60%,100%{opacity:.2;transform:scale(.8);}30%{opacity:1;transform:scale(1.2);} }

/* Messages */
.msg-user { display:flex; justify-content:flex-end; margin:6px 0; }
.msg-user-bubble {
  max-width: 72%;
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  padding: 10px 14px; border-radius: 16px 16px 4px 16px;
  font-size: 14px; line-height: 1.6; color: white;
  box-shadow: 0 4px 20px rgba(124,58,237,0.4);
  word-wrap: break-word;
}
.msg-ai { display:flex; gap:10px; align-items:flex-start; margin:6px 0; }
.msg-avatar {
  width:30px; height:30px; border-radius:50%; flex-shrink:0;
  background: linear-gradient(135deg,rgba(147,51,234,0.5),rgba(109,40,217,0.3));
  border: 1px solid rgba(147,51,234,0.6);
  display:flex; align-items:center; justify-content:center;
  font-size:12px; box-shadow:0 0 12px rgba(147,51,234,0.4);
  margin-top: 2px;
}
.msg-ai-bubble {
  max-width: 80%;
  background: linear-gradient(135deg,rgba(255,255,255,0.07),rgba(255,255,255,0.02));
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.1);
  padding: 10px 14px; border-radius: 0 16px 16px 16px;
  font-size: 14px; line-height: 1.7; color: rgba(255,255,255,0.9);
  word-wrap: break-word;
}
.msg-ai-bubble strong { color: #c084fc; }

/* Typing dots */
.typing-dots{display:flex;gap:5px;align-items:center;padding:4px 0;}
.dot{width:7px;height:7px;border-radius:50%;background:#a855f7;animation:dotPulse 1.4s ease-in-out infinite;}
.dot:nth-child(2){animation-delay:.2s;}.dot:nth-child(3){animation-delay:.4s;}

/* ── FIXED BOTTOM INPUT ─────────────────────────────────────────────────── */
[data-testid="stBottom"] {
  position: fixed !important;
  bottom: 0 !important;
  left: 50% !important;
  transform: translateX(-50%) !important;
  width: 100% !important;
  max-width: 700px !important;
  padding: 12px 16px 16px !important;
  background: linear-gradient(to top, #07001a 80%, transparent) !important;
  z-index: 999 !important;
}

/* Input field */
[data-testid="stBottom"] [data-testid="stTextInput"] input,
[data-testid="stChatInput"] textarea,
section[data-testid="stBottom"] input {
  background: rgba(255,255,255,0.05) !important;
  border: 1px solid rgba(147,51,234,0.4) !important;
  border-radius: 14px !important;
  color: white !important;
  font-size: 14px !important;
  padding: 12px 16px !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: rgba(255,255,255,0.3) !important; }
[data-testid="stChatInput"] textarea:focus {
  border-color: rgba(147,51,234,0.7) !important;
  box-shadow: 0 0 20px rgba(147,51,234,0.2) !important;
}

/* Chat input send button */
[data-testid="stChatInput"] button {
  background: linear-gradient(135deg,#7c3aed,#a855f7) !important;
  border: none !important;
  border-radius: 10px !important;
  box-shadow: 0 0 14px rgba(147,51,234,0.5) !important;
}
[data-testid="stChatInput"] button svg { fill: white !important; }

/* Suggestion buttons */
.stButton > button {
  font-size: 11px !important;
  padding: 6px 10px !important;
  background: linear-gradient(135deg,rgba(147,51,234,0.15),rgba(109,40,217,0.05)) !important;
  border: 1px solid rgba(147,51,234,0.3) !important;
  box-shadow: none !important;
  color: rgba(255,255,255,0.75) !important;
  border-radius: 20px !important;
  width: 100% !important;
}
.stButton > button:hover {
  border-color: rgba(147,51,234,0.6) !important;
  color: white !important;
  background: linear-gradient(135deg,rgba(147,51,234,0.25),rgba(109,40,217,0.1)) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending" not in st.session_state:
    st.session_state.pending = None

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:20px 0 10px;">
  <div style="width:48px;height:48px;border-radius:50%;
    background:linear-gradient(135deg,#7c3aed,#a855f7);
    display:flex;align-items:center;justify-content:center;
    font-size:20px;margin:0 auto 8px;
    box-shadow:0 0 30px rgba(147,51,234,0.7),0 0 60px rgba(147,51,234,0.2);">ॐ</div>
  <div style="font-size:24px;font-weight:700;letter-spacing:1px;
    background:linear-gradient(90deg,#c084fc,#f0abfc,#c084fc,#a855f7);
    background-size:200% auto;-webkit-background-clip:text;
    -webkit-text-fill-color:transparent;background-clip:text;
    animation:shimmer 3s linear infinite;">DoshMukti AI</div>
  <div style="font-size:10px;color:rgba(255,255,255,0.35);letter-spacing:3px;text-transform:uppercase;margin-top:3px;">
    Vedic Wisdom · ज्योतिष सहायक</div>
  <div style="height:1px;background:linear-gradient(90deg,transparent,rgba(147,51,234,0.5),transparent);margin:10px 0 4px;"></div>
</div>
""", unsafe_allow_html=True)


def render_msg(role: str, content: str):
    if role == "user":
        st.markdown(f'<div class="msg-user"><div class="msg-user-bubble">{content}</div></div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="msg-ai"><div class="msg-avatar">ॐ</div>'
                    f'<div class="msg-ai-bubble">{content}</div></div>',
                    unsafe_allow_html=True)


# ── Welcome ───────────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="msg-ai">
      <div class="msg-avatar">ॐ</div>
      <div class="msg-ai-bubble">
        नमस्ते 🙏 मैं <strong>Pandit Rameshwar Das Ji</strong> हूँ।<br>
        दोष, उपाय, ग्रह दशा, आर्थिक या रिश्तों की समस्या — कुछ भी पूछें।<br>
        <span style="color:rgba(255,255,255,0.4);font-size:12px;">Hindi या English — दोनों में।</span>
      </div>
    </div>
    <div style="height:10px"></div>
    """, unsafe_allow_html=True)

    SUGGESTIONS = [
        ("मंगल दोष उपाय", "मंगल दोष के उपाय क्या हैं?"),
        ("काल सर्प दोष", "काल सर्प दोष से मुक्ति कैसे?"),
        ("आर्थिक समस्या", "पैसे की समस्या का ज्योतिष उपाय"),
        ("शनि साढ़ेसाती", "शनि साढ़ेसाती में क्या करें?"),
    ]
    cols = st.columns(4)
    for i, (label, question) in enumerate(SUGGESTIONS):
        with cols[i]:
            if st.button(label, key=f"sug_{i}"):
                st.session_state.pending = question
                st.rerun()

# ── History ───────────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    render_msg(msg["role"], msg["content"])

# ── Process pending ───────────────────────────────────────────────────────────
if st.session_state.pending:
    q = st.session_state.pending
    st.session_state.pending = None
    st.session_state.messages.append({"role": "user", "content": q})
    render_msg("user", q)
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
    with st.spinner(""):
        response = ask(q, chat_history=history, stream=False)
    st.session_state.messages.append({"role": "assistant", "content": response})
    render_msg("assistant", response)

# ── Fixed bottom input via st.chat_input ──────────────────────────────────────
user_input = st.chat_input("अपना प्रश्न पूछें... (Hindi / English)")

if user_input and user_input.strip():
    q = user_input.strip()
    st.session_state.messages.append({"role": "user", "content": q})
    render_msg("user", q)
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
    with st.spinner(""):
        response = ask(q, chat_history=history, stream=False)
    st.session_state.messages.append({"role": "assistant", "content": response})
    render_msg("assistant", response)
