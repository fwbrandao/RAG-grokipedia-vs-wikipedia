#!/usr/bin/env python3
"""Generate the public teaching notebook. Run from repo root."""
import json
from pathlib import Path

cells = []


def md(src: str):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": [line + "\n" for line in src.strip("\n").split("\n")]})
    if cells[-1]["source"]:
        cells[-1]["source"][-1] = cells[-1]["source"][-1].rstrip("\n")


def code(src: str):
    lines = [line + "\n" for line in src.strip("\n").split("\n")]
    if lines:
        lines[-1] = lines[-1].rstrip("\n")
    cells.append({
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": lines,
    })


md("""# RAG Face-Off: Grokipedia vs. Wikipedia

Two independent Retrieval-Augmented Generation pipelines over two encyclopedias,
answering the **same question** side by side.

```
topics ──► ingest (Grokipedia + Wikipedia, cached JSON)
       ──► chunk (~220 tokens for MiniLM)
       ──► embed (local MiniLM, 384-d)
       ──► two Chroma collections
       ──► retrieve top-k ──► same LLM ──► side-by-side answers
```

**The whole point:** the generator is identical on both sides — same Groq model, same prompt,
same temperature, same `top_k`. The **only** variable is the corpus.

Heavy lifting lives in the `rag/` package so this notebook stays readable and the Streamlit
app (`app.py`) can reuse the same pipeline. Run **top to bottom**. Follow-along notes: `LEARN.md`.

**Verify as you go:** each step prints a success check. If a check fails, stop and fix it
before continuing.""")

md("""---
## Step 0 — Install dependencies

Run once per environment. Use the project `.venv` kernel. Restart the kernel if `ipywidgets`
was newly installed.

**Success:** the next cell finishes without an error.""")

code("""%pip install -q -r requirements.txt
import sys
print(sys.executable)""")

md("""---
## Step 1 — Configuration

**This notebook runs free by default** (`PROVIDER = "groq"`). Groq serves the chat model;
embeddings stay **local** (MiniLM via Chroma). MiniLM truncates at **256 tokens**, so chunks
are capped at **220**. Mixing MiniLM (384-d) and OpenAI (1536-d) vectors in one collection
is meaningless — collection names include an `EMBED_TAG` so backends never collide.

Put `GROQ_API_KEY` in `.env` (see `.env.example`).

**Success:** prints `Provider : groq` and `Chunking : 220 tokens`.""")

code("""from rag.config import Settings, SOURCES
from rag.ingest import build_corpus
from rag.chunking import chunk_corpus, n_tokens
from rag.embeddings import Embedder
from rag.store import index_all
from rag.pipeline import RagFaceOff, SYSTEM_PROMPT

settings = Settings(provider="groq")
settings.ensure_dirs()
settings.require_keys()

print(f"Provider   : {settings.provider}  ({settings.chat_model})")
print(f"Embeddings : {settings.embedding_backend}  ({settings.embed_model})")
print(f"Chunking   : {settings.chunk_tokens} tokens / {settings.chunk_overlap} overlap")
print(f"Topics     : {len(settings.topics)}")
print("Running free. No charges will be incurred.")""")

md("""---
## Step 2 — Ingest the two knowledge bases

**Why this exists:** RAG needs documents on disk before it can retrieve anything.

- **Wikipedia** — public MediaWiki API. Search can pick the wrong page (e.g. “origins” → “deaths”),
  so we pin COVID with `WIKI_TITLE_OVERRIDE`. Wikipedia **429s** if you fetch too fast; the client
  retries with backoff and waits 1s between calls.
- **Grokipedia** — unofficial community client. Cache everything to `data/raw/` so a later run
  works offline.

Both fetchers return the same `Document` shape.

**Success:** each source has 6 docs (or however many topics you configured). Cached files print immediately.""")

code("""corpus = build_corpus(settings, use_cache=True)

print()
for src in SOURCES:
    total = sum(d.n_chars for d in corpus[src])
    print(f"{src:<12} {len(corpus[src])} docs, {total:,} chars")
assert all(corpus[src] for src in SOURCES), "A source returned no documents — check cache / network." """)

md("""---
## Step 3 — Chunk the documents

Whole articles are too big for a context window and too coarse for search. We pack **paragraphs**
until the token budget, with overlap so facts that straddle a boundary stay retrievable.

**Learn check:** if chunks were 2,000 tokens, MiniLM would silently drop everything after 256 —
those tails would never be searchable.

**Success:** hundreds of chunks; mean tokens near 220, not thousands.""")

code("""chunks = chunk_corpus(corpus, settings)

for src in SOURCES:
    cs = chunks[src]
    lens = [n_tokens(c.text) for c in cs]
    print(f"{src:<12} {len(cs):>4} chunks | "
          f"tokens min {min(lens)} / mean {sum(lens)//len(lens)} / max {max(lens)}")

ex = chunks[SOURCES[0]][1]
print(f"\\n--- sample chunk: {ex.chunk_id} ---\\n{ex.text[:500]}...")""")

md("""---
## Step 4 — Embed

An embedding is a vector. Similar meaning → nearby vectors. We embed every chunk at index time,
then embed the **question** the same way and find nearest neighbors.

**Success:** local MiniLM reports **384** dimensions.""")

code("""embedder = Embedder(settings)
dim = len(embedder.embed_query("dimension probe"))
print(f"{settings.embedding_backend} embeddings OK — {dim} dimensions")
assert dim == 384 or settings.embedding_backend != "local" """)

md("""---
## Step 5 — Two Chroma collections

Two libraries, same schema: `kb_grokipedia__minilm` and `kb_wikipedia__minilm`. That is the A/B
design. Indexes persist under `data/chroma/` (gitignored). Re-running this cell only embeds
**new** chunk ids.

**Success:** both collections are non-empty.""")

code("""collections = index_all(chunks, embedder, settings)
for src, col in collections.items():
    print(f"{src:<12} {col.count()} vectors")
assert all(col.count() > 0 for col in collections.values())""")

md("""---
## Step 6 — Retrieve + generate (this is RAG)

1. **Retrieve** — embed the question, query one collection, take top-k chunks.
2. **Augment** — stuff those chunks into the prompt as numbered context.
3. **Generate** — the LLM may only use that context (citations required).

**Success:** a Wikipedia-grounded answer with `[n]` citations, not an empty string.""")

code("""engine = RagFaceOff(settings)
engine.collections = collections
engine._ready = True

print("System prompt (grounding rules):")
print(SYSTEM_PROMPT[:280], "...")

probe = engine.answer("What are the main criticisms of Elon Musk?", "wikipedia", top_k=3)
print(f"\\n[{settings.provider} / {settings.chat_model}] {probe.latency_s}s")
print(probe.answer)
assert probe.answer.strip(), "Empty generation — check GROQ_API_KEY and rate limits." """)

md("""---
## Step 7 — Compare (fair A/B)

Embed the question **once**. Retrieve from both collections with that same vector. Generate twice
with the same prompt. Score how similar the two answers are.

Low retrieval similarity means a **coverage miss**, not necessarily a biased corpus.

**Gate:** do not treat the UI as working until this cell returns two grounded answers.""")

code("""cmp = engine.compare("What are the main criticisms of Elon Musk?")
print(f"answer cosine similarity: {cmp.answer_similarity}")
print(f"shared topics: {cmp.topic_overlap or ['none']}")
for src, res in cmp.results.items():
    print(f"\\n=== {src} ({res.latency_s}s) ===")
    print(res.answer[:500])
    print("hits:", [(h.rank, h.title, h.similarity) for h in res.hits])""")

md("""---
## Step 8 — Side-by-side notebook UI

Same `compare()` behind buttons. The portfolio live demo is `streamlit run app.py`.

**Success:** the widget renders; Compare produces two panels.""")

code("""import html
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output
from rag.config import SOURCES

PALETTE = {
    "grokipedia": {"accent": "#00f5f5", "label": "Grokipedia"},
    "wikipedia":  {"accent": "#ff51fa", "label": "Wikipedia"},
}

def _cite_html(hits):
    rows = []
    for h in hits:
        snippet = html.escape(h.text[:220].replace("\\n", " ")) + "..."
        rows.append(
            f"<details style='margin:4px 0;font-size:12px;'>"
            f"<summary style='cursor:pointer;'><b>[{h.rank}]</b> {html.escape(h.title)} "
            f"<span style='opacity:.6'>(sim {h.similarity})</span></summary>"
            f"<div style='margin:6px 0 6px 14px;opacity:.85'>{snippet}<br>"
            f"<a href='{html.escape(h.url)}' target='_blank'>source</a></div></details>"
        )
    return "".join(rows)

def _panel_html(res):
    style = PALETTE[res.source]
    body = html.escape(res.answer).replace("\\n", "<br>")
    sims = [h.similarity for h in res.hits]
    mean_sim = round(sum(sims) / len(sims), 3) if sims else 0.0
    return f'''<div style="flex:1;min-width:320px;border:1px solid #333;border-top:4px solid {style['accent']};
                border-radius:10px;padding:14px 16px;background:#121029;color:#e7e2ff;">
      <div style="font-weight:700;color:{style['accent']};">{style['label']}</div>
      <div style="font-size:11px;opacity:.65;margin-bottom:10px;">{len(res.hits)} chunks · mean sim {mean_sim} · {res.latency_s}s</div>
      <div style="font-size:14px;line-height:1.6;">{body}</div>
      <div style="margin-top:12px;border-top:1px solid #333;padding-top:8px;">{_cite_html(res.hits)}</div>
    </div>'''

def render_comparison(cmp_result):
    sim = cmp_result.answer_similarity
    verdict, colour = (("Strong agreement", "#5eead4") if sim >= 0.90 else
                       ("Partial agreement", "#fbbf24") if sim >= 0.75 else
                       ("Notable divergence", "#fb7185"))
    panels = "".join(_panel_html(cmp_result.results[s]) for s in SOURCES)
    shared = ", ".join(cmp_result.topic_overlap) or "none"
    return HTML(
        f"<div style='font-family:system-ui,sans-serif;color:#e7e2ff'>"
        f"<div style='margin-bottom:10px'><b>{html.escape(cmp_result.question)}</b><br>"
        f"<span style='color:{colour};font-weight:600'>{verdict}</span>"
        f"<span style='opacity:.7'> · cosine {sim} · shared topics: {html.escape(shared)}</span></div>"
        f"<div style='display:flex;gap:14px;flex-wrap:wrap'>{panels}</div></div>"
    )

question_box = widgets.Textarea(value="What are the main criticisms of Elon Musk?",
    layout=widgets.Layout(width="100%", height="72px"))
k_slider = widgets.IntSlider(value=settings.top_k, min=1, max=10, description="top_k")
run_button = widgets.Button(description="Compare", button_style="primary")
out = widgets.Output()
EXAMPLES = [
    "What are the main criticisms of Elon Musk?",
    "What is the scientific consensus on the causes of climate change?",
    "What are the leading hypotheses for the origin of COVID-19?",
    "Is Wikipedia biased? What evidence is given?",
    "What are the main risks of cryptocurrency?",
]
example_dd = widgets.Dropdown(options=["-- example questions --"] + EXAMPLES)

def _on_example(change):
    if change["new"] and not change["new"].startswith("--"):
        question_box.value = change["new"]
example_dd.observe(_on_example, names="value")

def _on_click(_):
    q = question_box.value.strip()
    with out:
        clear_output(wait=True)
        if not q:
            print("Type a question first.")
            return
        print("Retrieving and generating...")
        try:
            result = engine.compare(q, top_k=k_slider.value)
        except Exception as e:
            clear_output(wait=True)
            print(f"Error: {type(e).__name__}: {e}")
            return
        clear_output(wait=True)
        display(render_comparison(result))

run_button.on_click(_on_click)
display(widgets.VBox([
    widgets.HTML("<h3>RAG Face-Off — Grokipedia vs Wikipedia</h3>"),
    example_dd, question_box, widgets.HBox([run_button, k_slider]), out,
]))""")

md("""---
## Step 9 — Batch evaluation

One demo convinces you. A **fixed question set** ranked by answer similarity is evidence.
The most divergent row is the finding to screenshot for write-ups.

**Success:** a DataFrame sorted by `answer_similarity` (lowest first).""")

code("""import json
import time
import pandas as pd
from rag.config import DATA_DIR

EVAL_QUESTIONS = [
    "What are the main criticisms of Elon Musk?",
    "What is the scientific consensus on the causes of climate change?",
    "What are the leading hypotheses for the origin of COVID-19?",
    "Is Wikipedia biased? What evidence is given?",
    "What are the main risks of cryptocurrency?",
    "What are the biggest risks posed by artificial intelligence?",
]

comparisons = []
for i, q in enumerate(EVAL_QUESTIONS):
    print(f"- {q}")
    if i > 0 and settings.rate_pause_s:
        time.sleep(settings.rate_pause_s)
    try:
        comparisons.append(engine.compare(q))
    except Exception as e:
        print(f"  failed: {type(e).__name__}: {e}")

df = pd.DataFrame([c.metrics_row() for c in comparisons])
df = df.sort_values("answer_similarity").reset_index(drop=True)
df""")

code("""if comparisons:
    most_divergent = min(comparisons, key=lambda c: c.answer_similarity)
    display(render_comparison(most_divergent))

export = [{
    "question": c.question,
    "answer_similarity": c.answer_similarity,
    "topic_overlap": c.topic_overlap,
    "answers": {src: {
        "answer": r.answer,
        "latency_s": r.latency_s,
        "hits": [{"rank": h.rank, "title": h.title, "url": h.url,
                  "similarity": h.similarity, "chunk_id": h.chunk_id} for h in r.hits],
    } for src, r in c.results.items()},
} for c in comparisons]
out_path = DATA_DIR / "comparison_results.json"
out_path.write_text(json.dumps(export, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote {out_path} ({len(export)} comparisons)")""")

md("""---
## Where to take it next

- **Live UI:** `streamlit run app.py` — cinematic split-screen of the same `compare()`.
- **Fairer A/B:** normalise chunk counts per topic so length is not a confound.
- **No-RAG baseline:** same model, no context — how much is the corpus actually doing?
- **Hybrid retrieval:** BM25 + dense, then a cross-encoder reranker.

### Honest caveats

- Divergence ≠ error. It means coverage, framing, or emphasis differ. Check citations.
- Retrieval dominates variance. Look at `mean_retrieval_sim` before blaming a corpus.
- The Grokipedia client is unofficial; `data/raw/` is the source of truth once cached.
- Six topics is a demo, not a study.""")

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "pygments_lexer": "ipython3"},
    },
    "cells": cells,
}

# Fix source arrays: nbformat wants list of strings; last line without forcing extra issues
path = Path("/Users/mymac/AI/RAG-grokipedia-vs-wikipedia/RAG-compare.ipynb")
path.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print(f"wrote {path} ({len(cells)} cells)")
