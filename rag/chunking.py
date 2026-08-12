from __future__ import annotations

import re
from typing import Dict, List

import tiktoken

from rag.config import Settings
from rag.models import Chunk, Document

ENC = tiktoken.get_encoding("cl100k_base")


def n_tokens(text: str) -> int:
    return len(ENC.encode(text))


def chunk_text(text: str, max_tokens: int, overlap: int) -> List[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: List[str] = []
    buf: List[str] = []
    buf_tokens = 0

    def flush():
        nonlocal buf, buf_tokens
        if buf:
            chunks.append("\n\n".join(buf))
            buf, buf_tokens = [], 0

    for para in paragraphs:
        t = n_tokens(para)
        if t > max_tokens:
            flush()
            ids = ENC.encode(para)
            step = max(1, max_tokens - overlap)
            for i in range(0, len(ids), step):
                piece = ENC.decode(ids[i : i + max_tokens]).strip()
                if piece:
                    chunks.append(piece)
            continue

        if buf_tokens + t > max_tokens and buf:
            prev = "\n\n".join(buf)
            chunks.append(prev)
            tail_ids = ENC.encode(prev)[-overlap:] if overlap > 0 else []
            tail = ENC.decode(tail_ids).strip()
            buf = [tail] if tail else []
            buf_tokens = len(tail_ids)

        buf.append(para)
        buf_tokens += t

    flush()
    return [c for c in chunks if c.strip()]


def chunk_corpus(corpus: Dict[str, List[Document]], settings: Settings) -> Dict[str, List[Chunk]]:
    out = {src: [] for src in corpus}
    for src, docs in corpus.items():
        for doc in docs:
            for i, piece in enumerate(
                chunk_text(doc.text, settings.chunk_tokens, settings.chunk_overlap)
            ):
                out[src].append(
                    Chunk(
                        chunk_id=f"{doc.doc_id}::{i:04d}",
                        doc_id=doc.doc_id,
                        source=doc.source,
                        topic=doc.topic,
                        title=doc.title,
                        url=doc.url,
                        position=i,
                        text=piece,
                    )
                )
    return out
