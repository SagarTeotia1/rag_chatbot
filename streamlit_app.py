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

# ── Secrets ────────────────────────────────────────────────────────────────────
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
/* ── Hide Streamlit chrome ──────────────────────────────────────────── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
.stDeployButton { display: none !important; }

/* ── App background ─────────────────────────────────────────────────── */
html, body, .stApp {
  background: #06001a !important;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
.stApp::before {
  content: '';
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(ellipse 70% 55% at 12% 8%,  rgba(109,40,217,.2)  0%, transparent 60%),
    radial-gradient(ellipse 50% 40% at 88% 88%,  rgba(88,28,135,.15) 0%, transparent 55%),
    radial-gradient(ellipse 35% 25% at 50% 48%,  rgba(60,0,100,.1)   0%, transparent 50%);
}

/* ── Block container ─────────────────────────────────────────────────── */
.main .block-container {
  max-width: 740px !important;
  margin: 0 auto !important;
  padding: 0 20px 16px !important;
  position: relative; z-index: 1;
}

/* ── Message scroll container — make height viewport-relative ───────── */
[data-testid="stVerticalBlockBorderWrapper"][style*="height"] {
  height: calc(100vh - 230px) !important;
  max-height: calc(100vh - 230px) !important;
  min-height: 280px !important;
  border: none !important;
  background: transparent !important;
}
/* hide the scrollbar track but keep scroll function */
[data-testid="stVerticalBlockBorderWrapper"][style*="height"]::-webkit-scrollbar {
  width: 4px;
}
[data-testid="stVerticalBlockBorderWrapper"][style*="height"]::-webkit-scrollbar-track {
  background: transparent;
}
[data-testid="stVerticalBlockBorderWrapper"][style*="height"]::-webkit-scrollbar-thumb {
  background: rgba(147,51,234,.35); border-radius: 4px;
}

/* ── Keyframes ───────────────────────────────────────────────────────── */
@keyframes shimmer {
  0%   { background-position: -200% center; }
  100% { background-position:  200% center; }
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes orbGlow {
  0%,100% { box-shadow: 0 0 24px rgba(147,51,234,.55), 0 0 48px rgba(147,51,234,.18); }
  50%     { box-shadow: 0 0 34px rgba(192,100,255,.75), 0 0 68px rgba(147,51,234,.28); }
}
@keyframes dotPulse {
  0%,60%,100% { opacity:.22; transform: scale(.72); }
  30%         { opacity: 1;  transform: scale(1.18); }
}

/* ── Header ──────────────────────────────────────────────────────────── */
.dm-header { text-align: center; padding: 22px 0 12px; animation: fadeUp .55s ease both; }
.dm-orb {
  width: 54px; height: 54px; border-radius: 50%;
  background: linear-gradient(140deg, #5b21b6, #9333ea, #7c3aed);
  display: flex; align-items: center; justify-content: center;
  font-size: 21px; margin: 0 auto 10px;
  animation: orbGlow 3.2s ease-in-out infinite;
  position: relative;
}
.dm-orb::after {
  content: ''; position: absolute; inset: -5px; border-radius: 50%;
  border: 1px solid rgba(192,100,255,.28);
}
.dm-title {
  font-size: 26px; font-weight: 800; letter-spacing: .4px;
  background: linear-gradient(90deg, #c084fc 0%, #f0abfc 35%, #e879f9 65%, #a855f7 100%);
  background-size: 220% auto;
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: shimmer 4s linear infinite;
}
.dm-sub {
  font-size: 10px; color: rgba(255,255,255,.3);
  letter-spacing: 3.5px; text-transform: uppercase; margin-top: 4px;
}
.dm-line {
  height: 1px; margin: 12px 0 4px;
  background: linear-gradient(90deg, transparent, rgba(147,51,234,.6), rgba(232,121,249,.35), transparent);
}

/* ── Message rows ─────────────────────────────────────────────────────── */
.msg-row {
  display: flex; gap: 10px; margin: 8px 0;
  animation: fadeUp .3s ease both;
}
.msg-row.user { justify-content: flex-end; }
.msg-row.ai   { justify-content: flex-start; align-items: flex-start; }

.msg-av {
  width: 34px; height: 34px; border-radius: 50%; flex-shrink: 0;
  background: linear-gradient(135deg, rgba(109,40,217,.65), rgba(147,51,234,.35));
  border: 1px solid rgba(192,100,255,.45);
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; margin-top: 3px;
  box-shadow: 0 0 14px rgba(147,51,234,.3);
}

.msg-bub {
  max-width: 78%; padding: 11px 15px;
  font-size: 14px; line-height: 1.78;
  word-wrap: break-word; white-space: pre-wrap;
}
.msg-row.user .msg-bub {
  background: linear-gradient(140deg, #5b21b6 0%, #7c3aed 55%, #9333ea 100%);
  border-radius: 18px 18px 4px 18px; color: #fff;
  box-shadow: 0 4px 22px rgba(109,40,217,.45), inset 0 1px 0 rgba(255,255,255,.1);
}
.msg-row.ai .msg-bub {
  background: linear-gradient(135deg, rgba(255,255,255,.075), rgba(255,255,255,.025));
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 4px 18px 18px 18px;
  color: rgba(255,255,255,.92);
  backdrop-filter: blur(22px);
  box-shadow: 0 4px 28px rgba(0,0,0,.3);
}
.msg-row.ai .msg-bub strong { color: #d8b4fe; }
.msg-row.ai .msg-bub ol,
.msg-row.ai .msg-bub ul { padding-left: 18px; margin: 5px 0; }
.msg-row.ai .msg-bub li { margin: 4px 0; }

/* ── Typing dots ──────────────────────────────────────────────────────── */
.typing-row { display: flex; gap: 10px; align-items: flex-start; margin: 8px 0; }
.typing-bub {
  background: linear-gradient(135deg, rgba(255,255,255,.065), rgba(255,255,255,.02));
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 4px 18px 18px 18px;
  padding: 14px 18px; backdrop-filter: blur(22px);
}
.typing-dots { display: flex; gap: 7px; align-items: center; }
.dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: linear-gradient(135deg, #9333ea, #c084fc);
  animation: dotPulse 1.4s ease-in-out infinite;
  box-shadow: 0 0 7px rgba(147,51,234,.5);
}
.dot:nth-child(2){ animation-delay: .22s; }
.dot:nth-child(3){ animation-delay: .44s; }

/* ── Welcome bubble ───────────────────────────────────────────────────── */
.welcome-bub {
  background: linear-gradient(135deg, rgba(109,40,217,.12), rgba(147,51,234,.06));
  border: 1px solid rgba(192,100,255,.22);
  border-radius: 4px 18px 18px 18px;
  padding: 13px 16px; max-width: 82%;
  font-size: 14px; line-height: 1.78;
  color: rgba(255,255,255,.88);
  animation: fadeUp .5s ease both;
}
.welcome-bub strong { color: #d8b4fe; }

/* ── Suggestion chips ─────────────────────────────────────────────────── */
.stButton > button {
  font-size: 11.5px !important; padding: 7px 10px !important;
  background: linear-gradient(135deg, rgba(109,40,217,.18), rgba(147,51,234,.08)) !important;
  border: 1px solid rgba(192,100,255,.35) !important;
  color: rgba(255,255,255,.78) !important;
  border-radius: 22px !important; width: 100% !important;
  box-shadow: none !important;
  transition: all .2s ease !important;
}
.stButton > button:hover {
  border-color: rgba(192,100,255,.65) !important;
  color: #f0abfc !important;
  background: linear-gradient(135deg, rgba(109,40,217,.28), rgba(147,51,234,.15)) !important;
  box-shadow: 0 0 18px rgba(147,51,234,.22) !important;
  transform: translateY(-1px) !important;
}

/* ── Chat input styling (NOT repositioned — let Streamlit handle it) ─── */
[data-testid="stBottom"] {
  background: linear-gradient(to top, #06001a 78%, rgba(6,0,26,0)) !important;
  padding-bottom: 12px !important;
}
[data-testid="stChatInput"] {
  background: rgba(255,255,255,.05) !important;
  border: 1px solid rgba(192,100,255,.38) !important;
  border-radius: 16px !important;
  backdrop-filter: blur(18px) !important;
  box-shadow: 0 8px 32px rgba(0,0,0,.28) !important;
  transition: border-color .2s, box-shadow .2s !important;
}
[data-testid="stChatInput"]:focus-within {
  border-color: rgba(192,100,255,.72) !important;
  box-shadow: 0 0 0 3px rgba(147,51,234,.18), 0 8px 32px rgba(0,0,0,.28) !important;
}
[data-testid="stChatInput"] textarea {
  background: transparent !important;
  color: rgba(255,255,255,.92) !important;
  font-size: 14px !important; caret-color: #a855f7 !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: rgba(255,255,255,.28) !important; }
[data-testid="stChatInput"] button {
  background: linear-gradient(135deg, #5b21b6, #9333ea) !important;
  border: none !important; border-radius: 10px !important;
  box-shadow: 0 0 16px rgba(147,51,234,.5) !important;
}
[data-testid="stChatInput"] button svg { fill: white !important; }
</style>""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending" not in st.session_state:
    st.session_state.pending = None


def scroll_chat_box():
    """Scroll the message container to the bottom."""
    components.html("""<script>
      (function() {
        var wraps = window.parent.document.querySelectorAll(
          '[data-testid="stVerticalBlockBorderWrapper"]'
        );
        wraps.forEach(function(w) { w.scrollTop = w.scrollHeight + 99999; });
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


TYPING_HTML = """
<div class="typing-row">
  <div class="msg-av">ॐ</div>
  <div class="typing-bub">
    <div class="typing-dots">
      <div class="dot"></div><div class="dot"></div><div class="dot"></div>
    </div>
  </div>
</div>"""

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dm-header">
  <div class="dm-orb">ॐ</div>
  <div class="dm-title">DoshMukti AI</div>
  <div class="dm-sub">Vedic Wisdom &nbsp;·&nbsp; ज्योतिष सहायक</div>
  <div class="dm-line"></div>
</div>""", unsafe_allow_html=True)

# ── Scrollable message container ──────────────────────────────────────────────
# height=560 is overridden by CSS to calc(100vh - 230px) — viewport-responsive
chat_box = st.container(height=560, border=False)

with chat_box:
    if not st.session_state.messages:
        # Welcome
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
    else:
        for msg in st.session_state.messages:
            render_msg(msg["role"], msg["content"])
        scroll_chat_box()

# ── Process pending ───────────────────────────────────────────────────────────
if st.session_state.pending:
    q = st.session_state.pending
    st.session_state.pending = None
    st.session_state.messages.append({"role": "user", "content": q})

    with chat_box:
        render_msg("user", q)
        typing_slot = st.empty()
        typing_slot.markdown(TYPING_HTML, unsafe_allow_html=True)
        scroll_chat_box()

    response = ask(q, chat_history=list(st.session_state.messages[:-1]), stream=False)
    st.session_state.messages.append({"role": "assistant", "content": response})

    with chat_box:
        typing_slot.empty()
        render_msg("assistant", response)
        scroll_chat_box()

# ── Chat input ────────────────────────────────────────────────────────────────
user_input = st.chat_input("अपना प्रश्न पूछें… (Hindi / English)")

if user_input and user_input.strip():
    q = user_input.strip()
    st.session_state.messages.append({"role": "user", "content": q})

    with chat_box:
        render_msg("user", q)
        typing_slot = st.empty()
        typing_slot.markdown(TYPING_HTML, unsafe_allow_html=True)
        scroll_chat_box()

    response = ask(q, chat_history=list(st.session_state.messages[:-1]), stream=False)
    st.session_state.messages.append({"role": "assistant", "content": response})

    with chat_box:
        typing_slot.empty()
        render_msg("assistant", response)
        scroll_chat_box()
