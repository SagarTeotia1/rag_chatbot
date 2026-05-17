"""Retrieve relevant chunks from ChromaDB Cloud for a query."""
import os
import sys
from pathlib import Path

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import EMBEDDING_MODEL, TOP_K
from src.ingestion.embedder import get_chroma_collection

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
    return _model


def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """Embed query, search ChromaDB Cloud, return top_k results."""
    model = _get_model()
    collection = get_chroma_collection()

    query_embedding = model.encode([query])[0].tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({
            "text": doc,
            "page": meta.get("page", "?"),
            "score": round(1 - dist, 4),
        })

    return hits
