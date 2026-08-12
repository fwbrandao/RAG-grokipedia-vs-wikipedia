from __future__ import annotations

import time
from typing import Dict, List, Optional

import numpy as np

from rag.chunking import chunk_corpus, n_tokens
from rag.config import SOURCES, Settings
from rag.embeddings import Embedder, make_llm_client
from rag.ingest import build_corpus
from rag.models import Comparison, RagAnswer, Retrieved
from rag.store import get_client, index_all, collection_name

SYSTEM_PROMPT = (
    "You are a careful research assistant. Answer the user's question using ONLY the numbered "
    "context passages provided. Follow these rules strictly:\n"
    "1. Every factual claim must be supported by a passage, cited inline as [1], [2], etc.\n"
    "2. If the context does not contain enough information, say so explicitly instead of "
    "guessing or drawing on outside knowledge.\n"
    "3. If passages disagree with one another, surface the disagreement rather than smoothing "
    "it over.\n"
    "4. Match the framing and emphasis of the passages. Do not add caveats the sources do not "
    "make, and do not drop caveats the sources do make.\n"
    "5. Be concise: 3-6 sentences unless the question demands more."
)

USER_TEMPLATE = (
    "Context passages:\n"
    "{context}\n\n"
    "Question: {question}\n\n"
    "Answer using only the passages above, with inline [n] citations."
)


def cosine(a, b) -> float:
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom else 0.0


def format_context(hits: List[Retrieved], max_chars_each: int = 1800) -> str:
    parts = []
    for h in hits:
        body = h.text[:max_chars_each]
        parts.append(f"[{h.rank}] (from \"{h.title}\", similarity {h.similarity})\n{body}")
    return "\n\n".join(parts)


class RagFaceOff:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.settings.ensure_dirs()
        self.settings.require_keys()
        self.embedder = Embedder(self.settings)
        self.llm = make_llm_client(self.settings)
        self.collections = {}
        self._ready = False

    def ensure_indexes(self, use_cache: bool = True, reset: bool = False) -> Dict[str, int]:
        chroma = get_client()
        counts = {}
        missing = False
        for src in SOURCES:
            name = collection_name(src, self.settings)
            try:
                col = chroma.get_collection(name)
                counts[src] = col.count()
                if col.count() == 0:
                    missing = True
            except Exception:
                counts[src] = 0
                missing = True

        if missing or reset:
            corpus = build_corpus(self.settings, use_cache=use_cache)
            chunks = chunk_corpus(corpus, self.settings)
            self.collections = index_all(chunks, self.embedder, self.settings, reset=reset)
        else:
            self.collections = {
                src: chroma.get_collection(collection_name(src, self.settings))
                for src in SOURCES
            }
        self._ready = True
        return {src: self.collections[src].count() for src in SOURCES}

    def retrieve(
        self,
        question: str,
        source: str,
        top_k: Optional[int] = None,
        query_vector: Optional[List[float]] = None,
    ) -> List[Retrieved]:
        if not self._ready:
            self.ensure_indexes()
        top_k = top_k or self.settings.top_k
        col = self.collections[source]
        if col.count() == 0:
            return []
        qv = query_vector if query_vector is not None else self.embedder.embed_query(question)
        res = col.query(
            query_embeddings=[qv],
            n_results=min(top_k, col.count()),
            include=["documents", "metadatas", "distances"],
        )
        out = []
        for i, (doc, meta, dist) in enumerate(
            zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
        ):
            out.append(
                Retrieved(
                    rank=i + 1,
                    chunk_id=res["ids"][0][i],
                    title=meta.get("title", ""),
                    url=meta.get("url", ""),
                    topic=meta.get("topic", ""),
                    text=doc,
                    similarity=round(1.0 - float(dist), 4),
                )
            )
        return out

    def chat(self, messages: List[dict], max_retries: int = 5):
        for attempt in range(max_retries):
            try:
                return self.llm.chat.completions.create(
                    model=self.settings.chat_model,
                    temperature=self.settings.temperature,
                    messages=messages,
                )
            except Exception as e:
                msg = str(e).lower()
                transient = any(
                    s in msg
                    for s in ("rate limit", "429", "timeout", "overloaded", "503", "502")
                )
                if attempt == max_retries - 1 or not transient:
                    raise
                wait = min(2 ** attempt * 3, 60)
                print(f"  {type(e).__name__} (likely rate limit) - retrying in {wait}s")
                time.sleep(wait)

    def answer(
        self,
        question: str,
        source: str,
        top_k: Optional[int] = None,
        query_vector: Optional[List[float]] = None,
    ) -> RagAnswer:
        t0 = time.time()
        hits = self.retrieve(question, source, top_k=top_k, query_vector=query_vector)
        if not hits:
            return RagAnswer(
                source,
                question,
                "_No indexed content for this knowledge base._",
                [],
                round(time.time() - t0, 2),
            )
        resp = self.chat(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": USER_TEMPLATE.format(
                        context=format_context(hits), question=question
                    ),
                },
            ]
        )
        usage = getattr(resp, "usage", None)
        return RagAnswer(
            source=source,
            question=question,
            answer=(resp.choices[0].message.content or "").strip(),
            hits=hits,
            latency_s=round(time.time() - t0, 2),
            prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
        )

    def compare(self, question: str, top_k: Optional[int] = None) -> Comparison:
        if not self._ready:
            self.ensure_indexes()
        qv = self.embedder.embed_query(question)
        results = {}
        for i, src in enumerate(SOURCES):
            if i > 0 and self.settings.rate_pause_s:
                time.sleep(self.settings.rate_pause_s)
            results[src] = self.answer(question, src, top_k=top_k, query_vector=qv)

        texts = [r.answer for r in results.values()]
        if all(t.strip() for t in texts) and len(texts) == 2:
            va, vb = self.embedder.embed_texts(texts, verbose=False)
            sim = round(cosine(va, vb), 4)
        else:
            sim = 0.0

        topic_sets = [{h.topic for h in r.hits} for r in results.values()]
        overlap = sorted(set.intersection(*topic_sets)) if all(topic_sets) else []
        return Comparison(question, results, sim, overlap)


def summarize_chunks(chunks) -> None:
    for src, cs in chunks.items():
        if not cs:
            print(f"{src:<12} 0 chunks")
            continue
        lens = [n_tokens(c.text) for c in cs]
        print(
            f"{src:<12} {len(cs):>4} chunks | "
            f"tokens min {min(lens)} / mean {sum(lens)//len(lens)} / max {max(lens)}"
        )
