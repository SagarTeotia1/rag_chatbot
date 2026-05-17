"""FastAPI backend for DoshMukti AI — deploy on Render."""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from groq import Groq

from config import GROQ_API_KEY, CHAT_MODEL, EXTRACTED_DIR
from src.ingestion.embedder import get_chroma_collection, embed_and_store
from src.ingestion.text_chunker import build_chunks_with_metadata
from src.retrieval.retriever import retrieve
from src.chat.chatbot import (
    _translate_to_hindi,
    _is_greeting,
    build_context_string,
    SYSTEM_PROMPT,
)

app = FastAPI(title="DoshMukti AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_groq_client: Groq | None = None


def get_groq() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client


def ensure_db_ready():
    col = get_chroma_collection()
    if col.count() > 0:
        return
    ocr_path = EXTRACTED_DIR / "pages_ocr.json"
    if not ocr_path.exists():
        raise RuntimeError("OCR JSON not found. Cannot build knowledge base.")
    print("ChromaDB empty — rebuilding from OCR JSON...")
    with open(ocr_path, encoding="utf-8") as f:
        raw = json.load(f)
    pages = {int(k): v for k, v in raw.items()}
    chunks = build_chunks_with_metadata(pages)
    embed_and_store(chunks)
    print("ChromaDB ready.")


@app.on_event("startup")
async def startup():
    ensure_db_ready()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str
    history: list[ChatMessage] = []


def _build_messages(req: ChatRequest, user_message: str) -> list[dict]:
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in req.history[-6:]:
        msgs.append({"role": m.role, "content": m.content})
    msgs.append({"role": "user", "content": user_message})
    return msgs


def _retrieve_context(question: str, top_k: int = 8) -> tuple[list[dict], str]:
    """Returns (all_hits, context_string)."""
    hindi_query = _translate_to_hindi(question)
    hits_orig = retrieve(question, top_k=top_k // 2)
    hits_hindi = retrieve(hindi_query, top_k=top_k)

    seen, all_hits = set(), []
    for h in hits_hindi + hits_orig:
        key = h["text"][:80]
        if key not in seen:
            seen.add(key)
            all_hits.append(h)

    context = build_context_string(all_hits[:top_k])
    return all_hits, context


def _make_user_message(question: str, context: str) -> str:
    if context:
        return (
            f"Relevant passages from the Dosh Mukti book:\n{context}\n\n"
            f"User question: {question}\n\n"
            f"Answer as Pandit Ji — ONLY use remedies from the passages above. "
            f"Numbered list, warm tone, no page numbers."
        )
    return f"User question: {question}\n\nNo relevant passages found."


@app.get("/health")
def health():
    col = get_chroma_collection()
    return {"status": "ok", "chunks": col.count()}


@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(400, "Question cannot be empty")

    client = get_groq()

    # Greeting — skip retrieval
    if _is_greeting(req.question):
        msgs = _build_messages(req, req.question)

        def greet_stream():
            yield f"data: {json.dumps({'type': 'pages', 'pages': []})}\n\n"
            stream = client.chat.completions.create(
                model=CHAT_MODEL, messages=msgs, temperature=0.8, max_tokens=100, stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    yield f"data: {json.dumps({'type': 'token', 'content': delta})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(greet_stream(), media_type="text/event-stream")

    # Astrology question — retrieve + answer
    all_hits, context = _retrieve_context(req.question)
    user_message = _make_user_message(req.question, context)
    msgs = _build_messages(req, user_message)

    def rag_stream():
        yield f"data: {json.dumps({'type': 'pages', 'pages': []})}\n\n"
        stream = client.chat.completions.create(
            model=CHAT_MODEL, messages=msgs, temperature=0.7, max_tokens=1024, stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield f"data: {json.dumps({'type': 'token', 'content': delta})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(rag_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
