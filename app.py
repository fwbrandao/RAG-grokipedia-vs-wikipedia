from __future__ import annotations

import html
import os
from pathlib import Path

import streamlit as st

from rag.config import SOURCES, Settings
from rag.pipeline import RagFaceOff


def _apply_streamlit_secrets() -> None:
    """Copy Streamlit secrets into os.environ so rag/ can stay framework-free."""
    try:
        secrets = st.secrets
    except Exception:
        return
    for key in ("GROQ_API_KEY", "OPENAI_API_KEY"):
        value = secrets.get(key)
        if value and not os.environ.get(key):
            os.environ[key] = str(value).strip().strip('"').strip("'")

ROOT = Path(__file__).resolve().parent
CSS = (ROOT / "assets" / "app.css").read_text(encoding="utf-8")

st.set_page_config(
    page_title="RAG Face-Off — Grokipedia vs Wikipedia",
    page_icon="◈",
    layout="wide",
)

st.markdown(f"<style>{CSS}</style><div class='mesh'></div>", unsafe_allow_html=True)

EXAMPLES = [
    "What are the main criticisms of Elon Musk?",
    "What is the scientific consensus on the causes of climate change?",
    "What are the leading hypotheses for the origin of COVID-19?",
    "Is Wikipedia biased? What evidence is given?",
    "What are the main risks of cryptocurrency?",
    "What are the biggest risks posed by artificial intelligence?",
]


@st.cache_resource(show_spinner=False)
def load_engine() -> RagFaceOff:
    _apply_streamlit_secrets()
    engine = RagFaceOff(Settings(provider="groq"))
    engine.ensure_indexes(use_cache=True)
    return engine


def verdict(sim: float) -> tuple[str, str]:
    if sim >= 0.90:
        return "Strong agreement", "#5eead4"
    if sim >= 0.75:
        return "Partial agreement", "#fbbf24"
    return "Notable divergence", "#fb7185"


def passage_html(source: str, hits) -> str:
    klass = "g" if source == "grokipedia" else "w"
    rows = []
    for h in hits:
        width = max(4, min(100, int(h.similarity * 100)))
        snippet = html.escape(h.text[:220].replace("\n", " "))
        rows.append(
            f"<div class='chip'>"
            f"<b>[{h.rank}]</b> {html.escape(h.title)} "
            f"<span class='meta'>(sim {h.similarity})</span>"
            f"<div class='simbar'><span style='width:{width}%'></span></div>"
            f"<div class='meta' style='margin-top:6px'>{snippet}… "
            f"<a href='{html.escape(h.url)}' target='_blank'>source</a></div>"
            f"</div>"
        )
    return f"<div class='{klass}'>{''.join(rows)}</div>"


def panel_html(source: str, result) -> str:
    klass = "g" if source == "grokipedia" else "w"
    label = "Grokipedia" if source == "grokipedia" else "Wikipedia"
    sims = [h.similarity for h in result.hits]
    mean_sim = round(sum(sims) / len(sims), 3) if sims else 0.0
    body = html.escape(result.answer).replace("\n", "<br>")
    return (
        f"<div class='glass edition {klass}'>"
        f"<div class='edition-label'>{label}</div>"
        f"<div class='meta'>{len(result.hits)} chunks · mean sim {mean_sim} · {result.latency_s}s</div>"
        f"<div class='answer'>{body}</div>"
        f"<div class='meta' style='margin-top:14px;text-transform:uppercase;letter-spacing:.08em'>Retrieved passages</div>"
        f"{passage_html(source, result.hits)}"
        f"</div>"
    )


st.markdown(
    """
<div class="hud-wrap">
  <div class="hud-kicker">Dual-corpus retrieval · identical generator</div>
  <h1 class="hud-title">RAG Face-Off</h1>
  <p class="hud-sub">
    Same model, same prompt, same top-k. The only variable is the knowledge base —
    Grokipedia on the left, Wikipedia on the right.
  </p>
</div>
""",
    unsafe_allow_html=True,
)

_apply_streamlit_secrets()

with st.spinner("Warming indexes (cached articles + local MiniLM)…"):
    try:
        engine = load_engine()
        ready = True
        err = ""
    except Exception as e:
        ready = False
        err = f"{type(e).__name__}: {e}"

if not ready:
    st.error(
        "Could not start the RAG engine. Add `GROQ_API_KEY` to `.env` locally "
        "or to Streamlit secrets in the cloud.\n\n" + err
    )
    st.stop()

left, mid, right = st.columns([1.4, 0.7, 0.9])
with left:
    example = st.selectbox("Example questions", ["— pick an example —"] + EXAMPLES)
with mid:
    top_k = st.slider("top_k", 1, 10, 5)
with right:
    st.write("")
    st.caption("Free stack: Groq llama-3.3-70b + local MiniLM")

question = st.text_area(
    "Question",
    value=example if example and not example.startswith("—") else EXAMPLES[0],
    height=90,
)

run = st.button("Compare", type="primary", use_container_width=False)

if run:
    q = question.strip()
    if not q:
        st.warning("Type a question first.")
    else:
        with st.spinner("Retrieving both corpora and generating…"):
            st.session_state["last_cmp"] = engine.compare(q, top_k=top_k)

if "last_cmp" in st.session_state:
    cmp = st.session_state["last_cmp"]
    label, colour = verdict(cmp.answer_similarity)
    split = int(max(4, min(96, cmp.answer_similarity * 100)))
    shared = ", ".join(cmp.topic_overlap) or "none"
    st.markdown(
        f"""
<div class="glass" style="margin: 0.6rem 0 1.1rem;">
  <div class="verdict" style="color:{colour}">{label}</div>
  <div class="meta">answer cosine similarity {cmp.answer_similarity} · shared topics: {html.escape(shared)}</div>
  <div class="meter" style="margin-top:10px"><div class="split" style="left:{split}%"></div></div>
</div>
""",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(panel_html("grokipedia", cmp.results["grokipedia"]), unsafe_allow_html=True)
    with c2:
        st.markdown(panel_html("wikipedia", cmp.results["wikipedia"]), unsafe_allow_html=True)
else:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            "<div class='glass edition g'><div class='edition-label'>Grokipedia</div>"
            "<div class='meta'>Waiting for a question</div></div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            "<div class='glass edition w'><div class='edition-label'>Wikipedia</div>"
            "<div class='meta'>Waiting for a question</div></div>",
            unsafe_allow_html=True,
        )
