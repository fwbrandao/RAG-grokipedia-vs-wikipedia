from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any, Dict, List, Optional


@dataclass
class Document:
    doc_id: str
    source: str
    topic: str
    title: str
    url: str
    text: str
    citations: List[Dict[str, str]] = field(default_factory=list)

    @property
    def n_chars(self) -> int:
        return len(self.text)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    source: str
    topic: str
    title: str
    url: str
    position: int
    text: str


@dataclass
class Retrieved:
    rank: int
    chunk_id: str
    title: str
    url: str
    topic: str
    text: str
    similarity: float


@dataclass
class RagAnswer:
    source: str
    question: str
    answer: str
    hits: List[Retrieved]
    latency_s: float
    prompt_tokens: int = 0
    completion_tokens: int = 0


@dataclass
class Comparison:
    question: str
    results: Dict[str, RagAnswer]
    answer_similarity: float
    topic_overlap: List[str]

    def metrics_row(self) -> Dict[str, Any]:
        row: Dict[str, Any] = {
            "question": self.question,
            "answer_similarity": self.answer_similarity,
        }
        for src, r in self.results.items():
            sims = [h.similarity for h in r.hits]
            row[f"{src}_mean_retrieval_sim"] = round(sum(sims) / len(sims), 4) if sims else 0.0
            row[f"{src}_answer_words"] = len(r.answer.split())
            row[f"{src}_latency_s"] = r.latency_s
        return row
