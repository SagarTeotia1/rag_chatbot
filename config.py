import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Load from Streamlit secrets if available (cloud deployment)
try:
    import streamlit as st
    _secrets = st.secrets
    for key in ["GROQ_API_KEY", "CHROMA_API_KEY", "CHROMA_TENANT", "CHROMA_DATABASE", "USE_TF", "TF_ENABLE_ONEDNN_OPTS"]:
        if key in _secrets and not os.getenv(key):
            os.environ[key] = str(_secrets[key])
except Exception:
    pass

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
EXTRACTED_DIR = DATA_DIR / "extracted"
CHROMA_DIR = DATA_DIR / "chroma_db"

PDF_PATH = BASE_DIR.parent / "Dosh Mukti Book (1).pdf"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

OCR_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
CHAT_MODEL = "llama-3.3-70b-versatile"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
TOP_K = 5

COLLECTION_NAME = "dosh_mukti"

OCR_BATCH_SIZE = 1
OCR_DELAY_SEC = 2
PDF_DPI = 150
