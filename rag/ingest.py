from __future__ import annotations

import hashlib
import json
import re
import time
from typing import Dict, List, Optional

import requests

from rag.config import RAW_DIR, SOURCES, USER_AGENT, WIKI_API, WIKI_TITLE_OVERRIDE, Settings
from rag.models import Document


def _cache_path(source: str, topic: str):
    key = hashlib.sha1(f"{source}::{topic}".encode()).hexdigest()[:12]
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:40]
    return RAW_DIR / f"{source}__{slug}__{key}.json"


def _save(doc: Document) -> None:
    _cache_path(doc.source, doc.topic).write_text(
        json.dumps(doc.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _load(source: str, topic: str) -> Optional[Document]:
    p = _cache_path(source, topic)
    if p.exists():
        return Document.from_dict(json.loads(p.read_text(encoding="utf-8")))
    return None


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]*\[\d{1,3}\](?=\W|$)", "", text)
    return text.strip()


def _wiki_get(session: requests.Session, params: dict, timeout: int) -> requests.Response:
    last = None
    for attempt in range(5):
        last = session.get(WIKI_API, params=params, timeout=timeout)
        if last.status_code != 429:
            last.raise_for_status()
            return last
        wait = int(last.headers.get("Retry-After", 2 ** (attempt + 2)))
        print(f"  [wikipedia] 429 rate limit — waiting {wait}s (attempt {attempt + 1}/5)")
        time.sleep(wait)
    last.raise_for_status()
    return last


def fetch_wikipedia(topic: str, settings: Settings, use_cache: bool = True) -> Optional[Document]:
    if use_cache:
        cached = _load("wikipedia", topic)
        if cached:
            return cached

    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})

    title = WIKI_TITLE_OVERRIDE.get(topic)
    if not title:
        r = _wiki_get(s, {
            "action": "query", "list": "search", "srsearch": topic,
            "srlimit": 1, "format": "json", "formatversion": 2,
        }, timeout=30)
        hits = r.json().get("query", {}).get("search", [])
        if not hits:
            print(f"  [wikipedia] no match for {topic!r}")
            return None
        title = hits[0]["title"]

    r = _wiki_get(s, {
        "action": "query", "prop": "extracts|info", "explaintext": 1,
        "redirects": 1, "titles": title, "inprop": "url",
        "format": "json", "formatversion": 2,
    }, timeout=60)
    pages = r.json().get("query", {}).get("pages", [])
    if not pages or "extract" not in pages[0]:
        print(f"  [wikipedia] no extract for {title!r}")
        return None
    page = pages[0]

    doc = Document(
        doc_id=f"wikipedia::{page['title'].replace(' ', '_')}",
        source="wikipedia",
        topic=topic,
        title=page["title"],
        url=page.get("fullurl", f"https://en.wikipedia.org/wiki/{page['title'].replace(' ', '_')}"),
        text=clean_text(page["extract"])[: settings.max_chars_per_doc],
        citations=[],
    )
    _save(doc)
    return doc


def fetch_grokipedia(topic: str, settings: Settings, use_cache: bool = True) -> Optional[Document]:
    if use_cache:
        cached = _load("grokipedia", topic)
        if cached:
            return cached

    try:
        from grokipedia_api import GrokipediaClient
        from grokipedia_api.exceptions import GrokipediaError
    except ImportError:
        print("  [grokipedia] package not installed — pip install grokipedia-api")
        return None

    try:
        with GrokipediaClient(timeout=45) as client:
            results = client.search(topic, limit=1).get("results", [])
            if not results:
                print(f"  [grokipedia] no match for {topic!r}")
                return None
            hit = results[0]
            slug = hit.get("slug") or hit.get("title", "").replace(" ", "_")

            payload = client.get_page(slug, include_content=True)
            page = payload.get("page", {}) or {}
            content = page.get("content") or ""
            if not content.strip():
                print(f"  [grokipedia] empty content for {slug!r}")
                return None

            citations = [
                {"title": str(c.get("title", ""))[:200], "url": str(c.get("url", ""))}
                for c in (page.get("citations") or [])
            ][:100]

            doc = Document(
                doc_id=f"grokipedia::{slug}",
                source="grokipedia",
                topic=topic,
                title=page.get("title") or hit.get("title") or topic,
                url=f"https://grokipedia.com/page/{slug}",
                text=clean_text(content)[: settings.max_chars_per_doc],
                citations=citations,
            )
            _save(doc)
            return doc
    except GrokipediaError as e:
        print(f"  [grokipedia] API error for {topic!r}: {e}")
        return None
    except Exception as e:
        print(f"  [grokipedia] unexpected error for {topic!r}: {type(e).__name__}: {e}")
        return None


FETCHERS = {"wikipedia": fetch_wikipedia, "grokipedia": fetch_grokipedia}


def build_corpus(
    settings: Settings,
    topics: Optional[List[str]] = None,
    use_cache: bool = True,
) -> Dict[str, List[Document]]:
    topics = list(topics or settings.topics)
    corpus = {src: [] for src in SOURCES}
    for topic in topics:
        print(f"Fetching: {topic}")
        for src in SOURCES:
            doc = FETCHERS[src](topic, settings, use_cache=use_cache)
            if doc:
                corpus[src].append(doc)
                print(f"  [{src}] {doc.title!r} - {doc.n_chars:,} chars")
            time.sleep(1.0)
    return corpus
