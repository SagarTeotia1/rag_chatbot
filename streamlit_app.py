import os
import sys
import html as _html
from pathlib import Path

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="DoshMukti AI",
    page_icon="🕉️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Load secrets ───────────────────────────────────────────────────────────────
for key in ["GROQ_API_KEY", "CHROMA_API_KEY", "CHROMA_TENANT", "CHROMA_DATABASE", "USE_TF", "TF_ENABLE_ONEDNN_OPTS"]:
    try:
        if key in st.secrets and not os.getenv(key):
            os.environ[key] = str(st.secrets[key]).strip()
    except Exception:
        pass

if not os.getenv("GROQ_API_KEY"):
    st.error("⚠️ GROQ_API_KEY missing — Manage App → Secrets → add it.")
    st.stop()

from src.chat.chatbot import ask, _is_greeting

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""<style>
/* ── Hide Streamlit chrome ───────────────────────────────────────────── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
.stDeployButton { display: none !important; }

/* ── Global background ───────────────────────────────────────────────── */
html, body, .stApp {
  height: 100%;
  background: #06001a !important;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
/* ambient light layers */
.stApp::before {
  content: '';
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(ellipse 70% 55% at 15% 10%,  rgba(109,40,217,.18) 0%, transparent 60%),
    radial-gradient(ellipse 50% 40% at 85% 85%,  rgba(88,28,135,.14)  0%, transparent 55%),
    radial-gradient(ellipse 35% 25% at 50% 45%,  rgba(60,0,100,.10)   0%, transparent 50%);
}

/* ── Scroll ──────────────────────────────────────────────────────────── */
section.main { overflow-y: auto !important; height: 100vh !important; }

/* ── Block container — BIG bottom padding so msgs clear fixed input ───── */
.main .block-container {
  max-width: 740px !important;
  margin: 0 auto !important;
  padding: 0 20px 220px !important;   /* 220px clears the fixed bar */
  position: relative; z-index: 1;
}

/* ── Keyframes ────────────────────────────────────────────────────────── */
@keyframes shimmer {
  0%   { background-position: -200% center; }
  100% { background-position:  200% center; }
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0);    }
}
@keyframes orbGlow {
  0%,100% { box-shadow: 0 0 22px rgba(147,51,234,.55), 0 0 44px rgba(147,51,234,.18); }
  50%     { box-shadow: 0 0 32px rgba(192,100,255,.75), 0 0 66px rgba(147,51,234,.28); }
}
@keyframes dotPulse {
  0%,60%,100% { opacity:.22; transform: scale(.72); }
  30%         { opacity:1;   transform: scale(1.18); }
}

/* ── Header ──────────────────────────────────────────────────────────── */
.dm-header { text-align:center; padding: 28px 0 14px; animation: fadeUp .55s ease both; }

.dm-orb {
  width:58px; height:58px; border-radius:50%;
  background: linear-gradient(140deg, #5b21b6, #9333ea, #7c3aed);
  display:flex; align-items:center; justify-content:center;
  font-size:22px; margin:0 auto 12px;
  animation: orbGlow 3.2s ease-in-out infinite;
  position: relative;
}
.dm-orb::after {
  content:''; position:absolute; inset:-5px; border-radius:50%;
  border:1px solid rgba(192,100,255,.28);
  box-shadow: inset 0 0 12px rgba(147,51,234,.12);
}

.dm-title {
  font-size:27px; font-weight:800; letter-spacing:.4px;
  background: linear-gradient(90deg, #c084fc 0%, #f0abfc 35%, #e879f9 65%, #a855f7 100%);
  background-size:220% auto;
  -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  background-clip:text;
  animation: shimmer 4s linear infinite;
}
.dm-sub {
  font-size:10px; color:rgba(255,255,255,.3);
  letter-spacing:3.5px; text-transform:uppercase; margin-top:5px;
}
.dm-line {
  height:1px; margin:14px 0 4px;
  background: linear-gradient(90deg, transparent, rgba(147,51,234,.6), rgba(232,121,249,.35), transparent);
}

/* ── Message rows ─────────────────────────────────────────────────────── */
.msg-row {
  display:flex; gap:10px; margin:9px 0;
  animation: fadeUp .3s ease both;
}
.msg-row.user { justify-content:flex-end; }
.msg-row.ai   { justify-content:flex-start; align-items:flex-start; }

/* Avatar */
.msg-av {
  width:36px; height:36px; border-radius:50%; flex-shrink:0;
  background: linear-gradient(135deg, rgba(109,40,217,.65), rgba(147,51,234,.35));
  border:1px solid rgba(192,100,255,.45);
  display:flex; align-items:center; justify-content:center;
  font-size:13px; margin-top:3px;
  box-shadow: 0 0 14px rgba(147,51,234,.3);
}

/* Bubbles */
.msg-bub {
  max-width:78%; padding:11px 15px;
  font-size:14px; line-height:1.78;
  word-wrap:break-word; white-space:pre-wrap;
}
.msg-row.user .msg-bub {
  background: linear-gradient(140deg, #5b21b6 0%, #7c3aed 60%, #9333ea 100%);
  border-radius:18px 18px 4px 18px;
  color:#fff;
  box-shadow: 0 4px 22px rgba(109,40,217,.45), inset 0 1px 0 rgba(255,255,255,.1);
}
.msg-row.ai .msg-bub {
  background: linear-gradient(135deg, rgba(255,255,255,.075), rgba(255,255,255,.025));
  border:1px solid rgba(255,255,255,.1);
  border-radius:4px 18px 18px 18px;
  color:rgba(255,255,255,.92);
  backdrop-filter:blur(22px);
  box-shadow: 0 4px 28px rgba(0,0,0,.32);
}
.msg-row.ai .msg-bub strong { color:#d8b4fe; }
.msg-row.ai .msg-bub ol,
.msg-row.ai .msg-bub ul    { padding-left:18px; margin:5px 0; }
.msg-row.ai .msg-bub li    { margin:4px 0; }

/* ── Typing dots ──────────────────────────────────────────────────────── */
.typing-row { display:flex; gap:10px; align-items:flex-start; margin:9px 0; }
.typing-bub {
  background: linear-gradient(135deg, rgba(255,255,255,.065), rgba(255,255,255,.02));
  border:1px solid rgba(255,255,255,.1);
  border-radius:4px 18px 18px 18px;
  padding:14px 18px; backdrop-filter:blur(22px);
}
.typing-dots { display:flex; gap:7px; align-items:center; }
.dot {
  width:8px; height:8px; border-radius:50%;
  background:linear-gradient(135deg,#9333ea,#c084fc);
  animation:dotPulse 1.4s ease-in-out infinite;
  box-shadow:0 0 7px rgba(147,51,234,.5);
}
.dot:nth-child(2){ animation-delay:.22s; }
.dot:nth-child(3){ animation-delay:.44s; }

/* ── Welcome ──────────────────────────────────────────────────────────── */
.welcome-bub {
  background: linear-gradient(135deg, rgba(109,40,217,.12), rgba(147,51,234,.06));
  border:1px solid rgba(192,100,255,.22);
  border-radius:4px 18px 18px 18px;
  padding:14px 17px; max-width:82%;
  font-size:14px; line-height:1.78;
  color:rgba(255,255,255,.88);
  animation:fadeUp .5s ease both;
}
.welcome-bub strong { color:#d8b4fe; }

/* ── Suggestion chips ─────────────────────────────────────────────────── */
.stButton > button {
  font-size:11.5px !important; padding:7px 10px !important;
  background:linear-gradient(135deg,rgba(109,40,217,.18),rgba(147,51,234,.08)) !important;
  border:1px solid rgba(192,100,255,.35) !important;
  color:rgba(255,255,255,.78) !important;
  border-radius:22px !important; width:100% !important;
  box-shadow:none !important;
  transition:all .2s ease !important;
}
.stButton > button:hover {
  border-color:rgba(192,100,255,.65) !important;
  color:#f0abfc !important;
  background:linear-gradient(135deg,rgba(109,40,217,.28),rgba(147,51,234,.15)) !important;
  box-shadow:0 0 18px rgba(147,51,234,.22) !important;
  transform:translateY(-1px) !important;
}

/* ── Fixed bottom input ───────────────────────────────────────────────── */
[data-testid="stBottom"] {
  position:fixed !important;
  bottom:0 !important;
  left:50% !important; transform:translateX(-50%) !important;
  width:100% !important; max-width:740px !important;
  padding:0 20px 22px !important;
  background:linear-gradient(to top, #06001a 72%, rgba(6,0,26,0)) !important;
  z-index:999 !important;
}

/* Input container */
[data-testid="stChatInput"] {
  background:rgba(255,255,255,.05) !important;
  border:1px solid rgba(192,100,255,.38) !important;
  border-radius:16px !important;
  backdrop-filter:blur(18px) !important;
  box-shadow:0 8px 32px rgba(0,0,0,.28) !important;
  transition:border-color .2s, box-shadow .2s !important;
}
[data-testid="stChatInput"]:focus-within {
  border-color:rgba(192,100,255,.72) !important;
  box-shadow:0 0 0 3px rgba(147,51,234,.18), 0 8px 32px rgba(0,0,0,.28) !important;
}
[data-testid="stChatInput"] textarea {
  background:transparent !important;
  color:rgba(255,255,255,.92) !important;
  font-size:14px !important; caret-color:#a855f7 !important;
}
[data-testid="stChatInput"] textarea::placeholder {
  color:rgba(255,255,255,.28) !important;
}
[data-testid="stChatInput"] button {
  background:linear-gradient(135deg,#5b21b6,#9333ea) !important;
  border:none !important; border-radius:10px !important;
  box-shadow:0 0 16px rgba(147,51,234,.5) !important;
  transition:box-shadow .2s !important;
}
[data-testid="stChatInput"] button:hover {
  box-shadow:0 0 26px rgba(147,51,234,.8) !important;
}
[data-testid="stChatInput"] button svg { fill:white !important; }
</style>""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending" not in st.session_state:
    st.session_state.pending = None


def scroll_bottom():
    components.html("""<script>
      (function(){
        var m = window.parent.document.querySelector('section.main');
        if (m) m.scrollTop = m.scrollHeight + 9999;
      })();
    </script>""", height=0, scrolling=False)


def render_msg(role: str, content: str):
    if role == "user":
        safe = _html.escape(content)
        st.markdown(
            f'<div class="msg-row user"><div class="msg-bub">{safe}</div></div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="msg-row ai">'
            f'<div class="msg-av">ॐ</div>'
            f'<div class="msg-bub">{content}</div>'
            f'</div>',
            unsafe_allow_html=True)


def show_typing():
    return st.empty()


def render_typing(slot):
    slot.markdown("""
<div class="typing-row">
  <div class="msg-av">ॐ</div>
  <div class="typing-bub">
    <div class="typing-dots">
      <div class="dot"></div><div class="dot"></div><div class="dot"></div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dm-header">
  <div class="dm-orb">ॐ</div>
  <div class="dm-title">DoshMukti AI</div>
  <div class="dm-sub">Vedic Wisdom &nbsp;·&nbsp; ज्योतिष सहायक</div>
  <div class="dm-line"></div>
</div>""", unsafe_allow_html=True)


# ── Welcome (only when no history) ────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
<div style="display:flex;gap:10px;align-items:flex-start;margin:8px 0 14px;">
  <div class="msg-av">ॐ</div>
  <div class="welcome-bub">
    नमस्ते 🙏 मैं <strong>Pandit Rameshwar Das Ji</strong> हूँ।<br>
    दोष, उपाय, ग्रह दशा, आर्थिक या रिश्तों की कोई भी समस्या — खुलकर पूछें।<br>
    <span style="color:rgba(255,255,255,.35);font-size:12px;">Hindi या English — दोनों में बात करें।</span>
  </div>
</div>""", unsafe_allow_html=True)

    SUGGESTIONS = [
        ("मंगल दोष उपाय", "मंगल दोष के उपाय क्या हैं?"),
        ("काल सर्प दोष",  "काल सर्प दोष से मुक्ति कैसे?"),
        ("आर्थिक समस्या", "पैसे की समस्या का ज्योतिष उपाय"),
        ("शनि साढ़ेसाती", "शनि साढ़ेसाती में क्या करें?"),
    ]
    cols = st.columns(4)
    for i, (label, q) in enumerate(SUGGESTIONS):
        with cols[i]:
            if st.button(label, key=f"sug_{i}"):
                st.session_state.pending = q
                st.rerun()


# ── Render history ─────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    render_msg(msg["role"], msg["content"])

if st.session_state.messages:
    scroll_bottom()


# ── Process pending (suggestion click) ────────────────────────────────────────
if st.session_state.pending:
    q = st.session_state.pending
    st.session_state.pending = None
    st.session_state.messages.append({"role": "user", "content": q})
    render_msg("user", q)

    history = list(st.session_state.messages[:-1])
    slot = show_typing()
    render_typing(slot)
    scroll_bottom()

    response = ask(q, chat_history=history, stream=False)
    slot.empty()

    st.session_state.messages.append({"role": "assistant", "content": response})
    render_msg("assistant", response)
    scroll_bottom()


# ── Chat input (pinned to bottom by Streamlit) ─────────────────────────────────
user_input = st.chat_input("अपना प्रश्न पूछें… (Hindi / English)")

if user_input and user_input.strip():
    q = user_input.strip()
    st.session_state.messages.append({"role": "user", "content": q})
    render_msg("user", q)

    history = list(st.session_state.messages[:-1])
    slot = show_typing()
    render_typing(slot)
    scroll_bottom()

    response = ask(q, chat_history=history, stream=False)
    slot.empty()

    st.session_state.messages.append({"role": "assistant", "content": response})
    render_msg("assistant", response)
    scroll_bottom()
