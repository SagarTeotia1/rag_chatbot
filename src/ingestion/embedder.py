"""Embed chunks with multilingual model and store in ChromaDB Cloud."""
import os
import sys
from pathlib import Path

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

import chromadb
from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import COLLECTION_NAME, EMBEDDING_MODEL

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"Loading embedding model: {EMBEDDING_MODEL}")
        _model = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
    return _model


def get_chroma_client() -> chromadb.CloudClient:
    return chromadb.CloudClient(
        api_key=os.environ["CHROMA_API_KEY"],
        tenant=os.environ["CHROMA_TENANT"],
        database=os.environ["CHROMA_DATABASE"],
    )


def get_chroma_collection() -> chromadb.Collection:
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def embed_and_store(chunks: list[dict], batch_size: int = 64) -> None:
    """Embed all chunks and upsert into ChromaDB Cloud."""
    if not chunks:
        print("No chunks to embed.")
        return

    model = _get_model()
    collection = get_chroma_collection()

    existing = collection.count()
    if existing > 0:
        print(f"Collection has {existing} docs. Clearing for fresh ingest...")
        collection.delete(where={"page": {"$gte": 1}})

    texts = [c["text"] for c in chunks]
    ids = [c["chunk_id"] for c in chunks]
    metadatas = [{"page": c["page"]} for c in chunks]

    print(f"Embedding {len(texts)} chunks (batch_size={batch_size})...")
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        batch_ids = ids[i : i + batch_size]
        batch_meta = metadatas[i : i + batch_size]

        embeddings = model.encode(batch_texts, show_progress_bar=False).tolist()
        collection.upsert(
            ids=batch_ids,
            embeddings=embeddings,
            documents=batch_texts,
            metadatas=batch_meta,
        )
        print(f"  Stored {min(i + batch_size, len(texts))}/{len(texts)}")

    print(f"Done. ChromaDB Cloud '{COLLECTION_NAME}' has {collection.count()} docs.")
