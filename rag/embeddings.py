from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from openai import OpenAI

from rag.config import Settings


def make_llm_client(settings: Settings) -> OpenAI:
    kwargs: Dict[str, Any] = {}
    if settings.base_url:
        kwargs["base_url"] = settings.base_url
    kwargs["api_key"] = os.environ.get(settings.key_env or "", "") or "not-needed"
    return OpenAI(**kwargs)


class Embedder:
    def __init__(self, settings: Settings):
        self.settings = settings
        if settings.embedding_backend == "local":
            from chromadb.utils import embedding_functions

            self._local_ef = embedding_functions.DefaultEmbeddingFunction()
            self.batch_size = 64
        else:
            self._embed_client = OpenAI()
            self.batch_size = 96

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        if self.settings.embedding_backend == "local":
            return [[float(x) for x in vec] for vec in self._local_ef(texts)]
        resp = self._embed_client.embeddings.create(
            model=self.settings.embed_model, input=texts
        )
        return [d.embedding for d in resp.data]

    def embed_texts(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        verbose: bool = False,
    ) -> List[List[float]]:
        batch_size = batch_size or self.batch_size
        vectors: List[List[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            for attempt in range(5):
                try:
                    vectors.extend(self._embed_batch(batch))
                    break
                except Exception as e:
                    if attempt == 4:
                        raise
                    wait = 2 ** attempt
                    print(
                        f"  embed retry {attempt + 1}/4 after {type(e).__name__} - sleeping {wait}s"
                    )
                    time.sleep(wait)
            if verbose:
                print(f"  embedded {min(start + batch_size, len(texts))}/{len(texts)}")
        return vectors

    def embed_query(self, text: str) -> List[float]:
        return self.embed_texts([text], verbose=False)[0]
