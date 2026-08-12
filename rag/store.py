from __future__ import annotations

from typing import Dict, List

import chromadb

from rag.config import CHROMA_DIR, Settings
from rag.embeddings import Embedder
from rag.models import Chunk


def collection_name(source: str, settings: Settings) -> str:
    return f"kb_{source}__{settings.embed_tag}"


def get_client():
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def index_source(
    chroma,
    source: str,
    source_chunks: List[Chunk],
    embedder: Embedder,
    settings: Settings,
    reset: bool = False,
):
    name = collection_name(source, settings)
    if reset:
        try:
            chroma.delete_collection(name)
        except Exception:
            pass

    col = chroma.get_or_create_collection(name, metadata={"hnsw:space": "cosine"})
    existing = set()
    if col.count() > 0:
        existing = set(col.get(include=[])["ids"])

    todo = [c for c in source_chunks if c.chunk_id not in existing]
    if not todo:
        print(f"{name}: up to date ({col.count()} chunks)")
        return col

    print(f"{name}: embedding {len(todo)} new chunks...")
    vectors = embedder.embed_texts([c.text for c in todo], verbose=True)
    col.add(
        ids=[c.chunk_id for c in todo],
        documents=[c.text for c in todo],
        embeddings=vectors,
        metadatas=[
            {
                "doc_id": c.doc_id,
                "source": c.source,
                "topic": c.topic,
                "title": c.title,
                "url": c.url,
                "position": c.position,
            }
            for c in todo
        ],
    )
    print(f"{name}: now {col.count()} chunks")
    return col


def index_all(
    chunks: Dict[str, List[Chunk]],
    embedder: Embedder,
    settings: Settings,
    reset: bool = False,
):
    chroma = get_client()
    return {
        src: index_source(chroma, src, chunks[src], embedder, settings, reset=reset)
        for src in chunks
    }
