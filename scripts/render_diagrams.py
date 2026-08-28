#!/usr/bin/env python3
"""Write HUD-style SVG diagrams (ASCII + numeric entities) and HTML frames."""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "diagrams"

DEFS = r"""
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0a0818"/>
      <stop offset="55%" stop-color="#0d0b21"/>
      <stop offset="100%" stop-color="#14081c"/>
    </linearGradient>
    <radialGradient id="glowC" cx="16%" cy="18%" r="42%">
      <stop offset="0%" stop-color="#00f5f5" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="#00f5f5" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glowM" cx="86%" cy="16%" r="40%">
      <stop offset="0%" stop-color="#ff51fa" stop-opacity="0.20"/>
      <stop offset="100%" stop-color="#ff51fa" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glowV" cx="50%" cy="90%" r="48%">
      <stop offset="0%" stop-color="#a68cff" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="#a68cff" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="ink" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#00f5f5"/>
      <stop offset="50%" stop-color="#a68cff"/>
      <stop offset="100%" stop-color="#ff51fa"/>
    </linearGradient>
    <linearGradient id="rail" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#00f5f5" stop-opacity="0.18"/>
      <stop offset="50%" stop-color="#a68cff" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="#ff51fa" stop-opacity="0.18"/>
    </linearGradient>
    <linearGradient id="gStroke" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0.06"/>
    </linearGradient>
    <linearGradient id="spine" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#a68cff" stop-opacity="0"/>
      <stop offset="20%" stop-color="#a68cff" stop-opacity="0.75"/>
      <stop offset="80%" stop-color="#a68cff" stop-opacity="0.75"/>
      <stop offset="100%" stop-color="#a68cff" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="1920" height="1080" fill="url(#bg)"/>
  <rect width="1920" height="1080" fill="url(#glowC)"/>
  <rect width="1920" height="1080" fill="url(#glowM)"/>
  <rect width="1920" height="1080" fill="url(#glowV)"/>
"""

FONT = "Avenir Next, Segoe UI, Helvetica Neue, sans-serif"


def svg(inner: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" '
        'width="1920" height="1080" role="img">\n'
        f"{DEFS}\n{inner}\n</svg>\n"
    )


def card(x, y, w, h, accent, kicker, title, lines, footer=""):
    texts = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="#191631" fill-opacity="0.82" stroke="url(#gStroke)"/>',
        f'<rect x="{x}" y="{y}" width="6" height="{h}" rx="3" fill="{accent}"/>',
        f'<text x="{x+28}" y="{y+36}" fill="{accent}" font-size="12" letter-spacing="3" font-weight="600">{kicker}</text>',
        f'<text x="{x+28}" y="{y+78}" fill="#e7e2ff" font-size="28" font-weight="700">{title}</text>',
    ]
    yy = y + 112
    for line in lines:
        texts.append(
            f'<text x="{x+28}" y="{yy}" fill="#8b86a8" font-size="15">{line}</text>'
        )
        yy += 26
    if footer:
        texts.append(
            f'<text x="{x+28}" y="{y+h-26}" fill="#c9c4e4" font-size="14">{footer}</text>'
        )
    return "\n".join(texts)


def flow() -> str:
    return f"""
  <g font-family="{FONT}">
    <text x="80" y="78" fill="#00f5f5" font-size="13" letter-spacing="6" font-weight="600">RAG FACE-OFF</text>
    <text x="80" y="128" fill="url(#ink)" font-size="42" font-weight="700">Implementation flow</text>
    <text x="80" y="168" fill="#8b86a8" font-size="18">Two phases. One generator. The corpus is the only variable.</text>

    <text x="80" y="240" fill="#aca8c5" font-size="12" letter-spacing="4" font-weight="600">01  BUILD TIME  &#183;  RUN ONCE</text>
    <rect x="80" y="258" width="1760" height="4" rx="2" fill="url(#rail)"/>

    {card(80, 290, 380, 200, "#00f5f5", "STEP 2", "Ingest",
          ["Grokipedia API + MediaWiki", "429 backoff + title override"],
          "cache &#8594; data/raw/*.json")}
    {card(500, 290, 380, 200, "#5ce8ff", "STEP 3", "Chunk",
          ["Paragraph-aware splitter", "MiniLM ceiling is 256 tokens"],
          "220 tokens &#183; 40 overlap")}
    {card(920, 290, 380, 200, "#a68cff", "STEP 4", "Embed",
          ["Local MiniLM via Chroma", "Same encoder for both KBs"],
          "384-d vectors")}
    {card(1340, 290, 500, 200, "#ff51fa", "STEP 5", "Index  &#215;  2",
          ["Two isolated Chroma collections"],
          "kb_grokipedia   /   kb_wikipedia")}

    <g fill="none" stroke="#a68cff" stroke-width="1.5" stroke-opacity="0.55">
      <path d="M460 390 H494"/><path d="M880 390 H914"/><path d="M1300 390 H1334"/>
    </g>

    <text x="80" y="560" fill="#aca8c5" font-size="12" letter-spacing="4" font-weight="600">02  QUERY TIME  &#183;  EVERY QUESTION</text>
    <rect x="80" y="578" width="1760" height="4" rx="2" fill="url(#rail)"/>

    {card(80, 610, 300, 210, "#8b86a8", "INPUT", "Question",
          ["Embedded once.", "Vector reused on both", "collections."])}
    {card(430, 610, 300, 210, "#00f5f5", "STEP 6", "Retrieve",
          ["top_k = 5 per corpus", "Grokipedia hits", "Wikipedia hits"])}
    {card(780, 610, 340, 210, "#a68cff", "STEP 6", "Ground + generate",
          ["Same system prompt", "Same temperature 0.1"],
          "Groq  llama-3.3-70b")}
    {card(1170, 610, 310, 210, "#ff51fa", "STEP 7", "Compare",
          ["Answer cosine similarity", "Topic-set overlap"],
          "Divergence is a signal")}

    <rect x="1530" y="610" width="310" height="210" rx="18" fill="#12102a" stroke="#a68cff" stroke-opacity="0.45"/>
    <text x="1554" y="650" fill="#a68cff" font-size="12" letter-spacing="3" font-weight="600">LOCKED</text>
    <text x="1554" y="690" fill="#e7e2ff" font-size="20" font-weight="700">Fair A/B</text>
    <text x="1554" y="726" fill="#8b86a8" font-size="14">model &#183; prompt &#183; temp</text>
    <text x="1554" y="750" fill="#8b86a8" font-size="14">top_k &#183; query vector</text>
    <text x="1554" y="786" fill="#00f5f5" font-size="14">only the corpus moves</text>

    <g fill="none" stroke="#a68cff" stroke-width="1.5" stroke-opacity="0.55">
      <path d="M380 715 H424"/><path d="M730 715 H774"/><path d="M1120 715 H1164"/><path d="M1480 715 H1524"/>
    </g>

    <text x="80" y="880" fill="#6d6888" font-size="13">Notebook steps map 1:1 onto rag/  &#183;  Streamlit HUD is the same pipeline</text>
    <text x="80" y="1008" fill="#4e4a66" font-size="12">github.com/fwbrandao/RAG-grokipedia-vs-wikipedia</text>
  </g>
"""


def dual() -> str:
    return f"""
  <g font-family="{FONT}">
    <text x="960" y="72" text-anchor="middle" fill="#8b86a8" font-size="13" letter-spacing="6" font-weight="600">ARCHITECTURE</text>
    <text x="960" y="122" text-anchor="middle" fill="url(#ink)" font-size="40" font-weight="700">Two rails. One generator.</text>
    <text x="960" y="162" text-anchor="middle" fill="#8b86a8" font-size="17">Identical retrieve &#8594; ground &#8594; generate. Isolated corpora.</text>

    <rect x="956" y="200" width="8" height="720" rx="4" fill="url(#spine)"/>

    <rect x="710" y="200" width="500" height="86" rx="16" fill="#191631" fill-opacity="0.88" stroke="#a68cff" stroke-opacity="0.45"/>
    <text x="960" y="236" text-anchor="middle" fill="#a68cff" font-size="11" letter-spacing="3" font-weight="600">SHARED  &#183;  QUERY VECTOR</text>
    <text x="960" y="266" text-anchor="middle" fill="#e7e2ff" font-size="20" font-weight="700">MiniLM embed(question)  &#8594;  384-d</text>

    <text x="360" y="230" text-anchor="middle" fill="#00f5f5" font-size="13" letter-spacing="5" font-weight="700">GROKIPEDIA</text>
    <text x="1560" y="230" text-anchor="middle" fill="#ff51fa" font-size="13" letter-spacing="5" font-weight="700">WIKIPEDIA</text>

    <rect x="80" y="320" width="560" height="120" rx="16" fill="#12242a" fill-opacity="0.88" stroke="#00f5f5" stroke-opacity="0.35"/>
    <text x="108" y="360" fill="#00f5f5" font-size="12" letter-spacing="2">CORPUS</text>
    <text x="108" y="396" fill="#e7e2ff" font-size="22" font-weight="700">grokipedia-api  &#183;  unofficial</text>
    <text x="108" y="422" fill="#7aa8ad" font-size="14">6 topics cached in data/raw/</text>

    <rect x="80" y="460" width="560" height="120" rx="16" fill="#12242a" fill-opacity="0.88" stroke="#00f5f5" stroke-opacity="0.35"/>
    <text x="108" y="500" fill="#00f5f5" font-size="12" letter-spacing="2">INDEX</text>
    <text x="108" y="536" fill="#e7e2ff" font-size="22" font-weight="700">Chroma  kb_grokipedia</text>
    <text x="108" y="562" fill="#7aa8ad" font-size="14">cosine over MiniLM space</text>

    <rect x="80" y="600" width="560" height="120" rx="16" fill="#12242a" fill-opacity="0.88" stroke="#00f5f5" stroke-opacity="0.35"/>
    <text x="108" y="640" fill="#00f5f5" font-size="12" letter-spacing="2">RETRIEVE</text>
    <text x="108" y="676" fill="#e7e2ff" font-size="22" font-weight="700">top_k = 5 passages</text>
    <text x="108" y="702" fill="#7aa8ad" font-size="14">similarity = 1 &#8722; distance</text>

    <rect x="80" y="740" width="560" height="130" rx="16" fill="#0e2a2c" stroke="#00f5f5" stroke-opacity="0.55"/>
    <text x="108" y="782" fill="#00f5f5" font-size="12" letter-spacing="2">ANSWER A</text>
    <text x="108" y="820" fill="#e7e2ff" font-size="22" font-weight="700">Grounded + [n] citations</text>
    <text x="108" y="848" fill="#7aa8ad" font-size="14">Framing follows this corpus only</text>

    <rect x="1280" y="320" width="560" height="120" rx="16" fill="#2a1224" fill-opacity="0.88" stroke="#ff51fa" stroke-opacity="0.35"/>
    <text x="1308" y="360" fill="#ff51fa" font-size="12" letter-spacing="2">CORPUS</text>
    <text x="1308" y="396" fill="#e7e2ff" font-size="22" font-weight="700">MediaWiki API  &#183;  official</text>
    <text x="1308" y="422" fill="#b07aab" font-size="14">title override for COVID origins</text>

    <rect x="1280" y="460" width="560" height="120" rx="16" fill="#2a1224" fill-opacity="0.88" stroke="#ff51fa" stroke-opacity="0.35"/>
    <text x="1308" y="500" fill="#ff51fa" font-size="12" letter-spacing="2">INDEX</text>
    <text x="1308" y="536" fill="#e7e2ff" font-size="22" font-weight="700">Chroma  kb_wikipedia</text>
    <text x="1308" y="562" fill="#b07aab" font-size="14">same embedding space, other docs</text>

    <rect x="1280" y="600" width="560" height="120" rx="16" fill="#2a1224" fill-opacity="0.88" stroke="#ff51fa" stroke-opacity="0.35"/>
    <text x="1308" y="640" fill="#ff51fa" font-size="12" letter-spacing="2">RETRIEVE</text>
    <text x="1308" y="676" fill="#e7e2ff" font-size="22" font-weight="700">top_k = 5 passages</text>
    <text x="1308" y="702" fill="#b07aab" font-size="14">same query vector as left rail</text>

    <rect x="1280" y="740" width="560" height="130" rx="16" fill="#2c0e24" stroke="#ff51fa" stroke-opacity="0.55"/>
    <text x="1308" y="782" fill="#ff51fa" font-size="12" letter-spacing="2">ANSWER B</text>
    <text x="1308" y="820" fill="#e7e2ff" font-size="22" font-weight="700">Grounded + [n] citations</text>
    <text x="1308" y="848" fill="#b07aab" font-size="14">Framing follows this corpus only</text>

    <rect x="710" y="430" width="500" height="200" rx="18" fill="#191631" fill-opacity="0.94" stroke="#a68cff" stroke-opacity="0.5"/>
    <text x="960" y="470" text-anchor="middle" fill="#a68cff" font-size="11" letter-spacing="3" font-weight="600">LOCKED INVARIANT</text>
    <text x="960" y="512" text-anchor="middle" fill="#e7e2ff" font-size="24" font-weight="700">Groq  llama-3.3-70b</text>
    <text x="960" y="548" text-anchor="middle" fill="#8b86a8" font-size="15">same system prompt &#183; temp 0.1 &#183; top_k 5</text>
    <text x="960" y="578" text-anchor="middle" fill="#8b86a8" font-size="15">cite [n] &#183; refuse to invent &#183; surface disagreement</text>
    <text x="960" y="606" text-anchor="middle" fill="#c9c4e4" font-size="14">called twice &#8212; once per rail</text>

    <rect x="710" y="900" width="500" height="88" rx="16" fill="#191631" fill-opacity="0.92" stroke="url(#gStroke)"/>
    <text x="960" y="936" text-anchor="middle" fill="#e7e2ff" font-size="18" font-weight="700">compare()  &#183;  answer cosine  &#183;  topic overlap</text>
    <text x="960" y="964" text-anchor="middle" fill="#8b86a8" font-size="13">Low similarity is not "wrong." Check retrieval scores first.</text>

    <path d="M360 870 C360 910, 360 920, 710 944" fill="none" stroke="#00f5f5" stroke-width="1.6" stroke-opacity="0.45"/>
    <path d="M1560 870 C1560 910, 1560 920, 1210 944" fill="none" stroke="#ff51fa" stroke-width="1.6" stroke-opacity="0.45"/>
  </g>
"""


def sequence() -> str:
    return f"""
  <g font-family="{FONT}">
    <text x="80" y="70" fill="#00f5f5" font-size="13" letter-spacing="6" font-weight="600">QUERY TIME</text>
    <text x="80" y="118" fill="url(#ink)" font-size="38" font-weight="700">compare() sequence</text>
    <text x="80" y="156" fill="#8b86a8" font-size="16">One embedding. Two retrievals. Two grounded completions. One cosine.</text>

    <g font-size="13" font-weight="600">
      <text x="280" y="220" text-anchor="middle" fill="#c9c4e4">App</text>
      <text x="560" y="220" text-anchor="middle" fill="#a68cff">MiniLM</text>
      <text x="860" y="220" text-anchor="middle" fill="#00f5f5">kb_grokipedia</text>
      <text x="1160" y="220" text-anchor="middle" fill="#ff51fa">kb_wikipedia</text>
      <text x="1480" y="220" text-anchor="middle" fill="#e7e2ff">Groq 70B</text>
      <text x="1760" y="220" text-anchor="middle" fill="#c9c4e4">Metric</text>
    </g>
    <g stroke="#2a2744" stroke-width="1">
      <line x1="280" y1="240" x2="280" y2="960"/>
      <line x1="560" y1="240" x2="560" y2="960"/>
      <line x1="860" y1="240" x2="860" y2="960"/>
      <line x1="1160" y1="240" x2="1160" y2="960"/>
      <line x1="1480" y1="240" x2="1480" y2="960"/>
      <line x1="1760" y1="240" x2="1760" y2="960"/>
    </g>

    <text x="48" y="300" fill="#5a5674" font-size="12">01</text>
    <line x1="280" y1="292" x2="560" y2="292" stroke="#a68cff" stroke-width="2"/>
    <polygon points="560,292 548,287 548,297" fill="#a68cff"/>
    <rect x="300" y="262" width="220" height="28" rx="8" fill="#1b1733"/>
    <text x="410" y="281" text-anchor="middle" fill="#d8d2ff" font-size="13">embed_query(q)</text>
    <rect x="500" y="318" width="200" height="26" rx="8" fill="#1b1733"/>
    <text x="600" y="336" text-anchor="middle" fill="#a68cff" font-size="12">qv  &#183;  384-d  reused</text>

    <text x="48" y="400" fill="#5a5674" font-size="12">02</text>
    <line x1="560" y1="392" x2="860" y2="392" stroke="#00f5f5" stroke-width="2"/>
    <polygon points="860,392 848,387 848,397" fill="#00f5f5"/>
    <rect x="590" y="362" width="230" height="28" rx="8" fill="#102226"/>
    <text x="705" y="381" text-anchor="middle" fill="#7ef6f6" font-size="13">query(qv, k=5)</text>
    <line x1="860" y1="392" x2="280" y2="452" stroke="#00f5f5" stroke-width="1.4" stroke-opacity="0.7"/>
    <polygon points="280,452 290,446 292,456" fill="#00f5f5"/>
    <text x="520" y="430" fill="#6ec8c8" font-size="12">hits_g + similarities</text>

    <text x="48" y="520" fill="#5a5674" font-size="12">03</text>
    <line x1="560" y1="512" x2="1160" y2="512" stroke="#ff51fa" stroke-width="2"/>
    <polygon points="1160,512 1148,507 1148,517" fill="#ff51fa"/>
    <rect x="720" y="482" width="280" height="28" rx="8" fill="#26101f"/>
    <text x="860" y="501" text-anchor="middle" fill="#ffb0fb" font-size="13">query(same qv, k=5)</text>
    <line x1="1160" y1="512" x2="280" y2="572" stroke="#ff51fa" stroke-width="1.4" stroke-opacity="0.7"/>
    <polygon points="280,572 290,566 292,576" fill="#ff51fa"/>
    <text x="620" y="550" fill="#d48ad0" font-size="12">hits_w + similarities</text>

    <text x="48" y="640" fill="#5a5674" font-size="12">04</text>
    <line x1="280" y1="632" x2="1480" y2="632" stroke="#00f5f5" stroke-width="2"/>
    <polygon points="1480,632 1468,627 1468,637" fill="#00f5f5"/>
    <rect x="700" y="602" width="420" height="28" rx="8" fill="#102226"/>
    <text x="910" y="621" text-anchor="middle" fill="#7ef6f6" font-size="13">system + context(hits_g) + question</text>
    <line x1="1480" y1="632" x2="280" y2="688" stroke="#00f5f5" stroke-width="1.4" stroke-dasharray="4 4" stroke-opacity="0.75"/>
    <text x="880" y="672" fill="#6ec8c8" font-size="12">answer_g  &#183;  citations [n]</text>

    <text x="48" y="760" fill="#5a5674" font-size="12">05</text>
    <line x1="280" y1="752" x2="1480" y2="752" stroke="#ff51fa" stroke-width="2"/>
    <polygon points="1480,752 1468,747 1468,757" fill="#ff51fa"/>
    <rect x="700" y="722" width="420" height="28" rx="8" fill="#26101f"/>
    <text x="910" y="741" text-anchor="middle" fill="#ffb0fb" font-size="13">same prompt  &#183;  context(hits_w)</text>
    <line x1="1480" y1="752" x2="280" y2="808" stroke="#ff51fa" stroke-width="1.4" stroke-dasharray="4 4" stroke-opacity="0.75"/>
    <text x="880" y="792" fill="#d48ad0" font-size="12">answer_w  &#183;  citations [n]  &#183;  rate-limit pause</text>

    <text x="48" y="880" fill="#5a5674" font-size="12">06</text>
    <line x1="280" y1="872" x2="560" y2="872" stroke="#a68cff" stroke-width="2"/>
    <polygon points="560,872 548,867 548,877" fill="#a68cff"/>
    <rect x="300" y="842" width="240" height="28" rx="8" fill="#1b1733"/>
    <text x="420" y="861" text-anchor="middle" fill="#d8d2ff" font-size="13">embed(answer_g, answer_w)</text>
    <line x1="560" y1="872" x2="1760" y2="872" stroke="#a68cff" stroke-width="2"/>
    <polygon points="1760,872 1748,867 1748,877" fill="#a68cff"/>
    <rect x="1500" y="842" width="220" height="28" rx="8" fill="#1b1733"/>
    <text x="1610" y="861" text-anchor="middle" fill="#d8d2ff" font-size="13">cosine + topic overlap</text>

    <rect x="80" y="980" width="1760" height="54" rx="12" fill="#191631" fill-opacity="0.8"/>
    <text x="960" y="1014" text-anchor="middle" fill="#8b86a8" font-size="15">The query vector is computed once and passed into both retrieve() calls. The A/B does not re-embed the question.</text>
  </g>
"""


def fair() -> str:
    return f"""
  <g font-family="{FONT}">
    <text x="80" y="78" fill="#a68cff" font-size="13" letter-spacing="6" font-weight="600">EXPERIMENTAL DESIGN</text>
    <text x="80" y="128" fill="url(#ink)" font-size="42" font-weight="700">Fair A/B contract</text>
    <text x="80" y="168" fill="#8b86a8" font-size="18">If it is not the corpus, it is locked. That is the whole experiment.</text>

    <rect x="80" y="220" width="860" height="720" rx="22" fill="#191631" fill-opacity="0.74" stroke="url(#gStroke)"/>
    <text x="120" y="280" fill="#a68cff" font-size="13" letter-spacing="4" font-weight="700">LOCKED  &#183;  CONTROL</text>
    <text x="120" y="328" fill="#e7e2ff" font-size="32" font-weight="700">Held constant</text>
    <g fill="#c9c4e4" font-size="20">
      <circle cx="140" cy="400" r="6" fill="#a68cff"/><text x="168" y="408">Generator &#183; Groq openai/gpt-oss-120b</text>
      <circle cx="140" cy="460" r="6" fill="#a68cff"/><text x="168" y="468">System prompt &#183; cite [n], no invention</text>
      <circle cx="140" cy="520" r="6" fill="#a68cff"/><text x="168" y="528">Temperature &#183; 0.1</text>
      <circle cx="140" cy="580" r="6" fill="#a68cff"/><text x="168" y="588">top_k &#183; 5 passages / corpus</text>
      <circle cx="140" cy="640" r="6" fill="#a68cff"/><text x="168" y="648">Query vector &#183; embed once, reuse</text>
      <circle cx="140" cy="700" r="6" fill="#a68cff"/><text x="168" y="708">Chunk budget &#183; 220 tokens / 40 overlap</text>
      <circle cx="140" cy="760" r="6" fill="#a68cff"/><text x="168" y="768">Encoder &#183; local MiniLM, 384-d</text>
    </g>
    <text x="120" y="880" fill="#6d6888" font-size="15">These are not "settings." They are the control group.</text>

    <rect x="980" y="220" width="860" height="720" rx="22" fill="#191631" fill-opacity="0.74" stroke="url(#gStroke)"/>
    <text x="1020" y="280" fill="#ff51fa" font-size="13" letter-spacing="4" font-weight="700">FREE  &#183;  TREATMENT</text>
    <text x="1020" y="328" fill="#e7e2ff" font-size="32" font-weight="700">Allowed to move</text>

    <rect x="1020" y="380" width="780" height="150" rx="16" fill="#102226" stroke="#00f5f5" stroke-opacity="0.4"/>
    <text x="1050" y="430" fill="#00f5f5" font-size="14" letter-spacing="3" font-weight="700">CORPUS A</text>
    <text x="1050" y="472" fill="#e7e2ff" font-size="24" font-weight="700">Grokipedia</text>
    <text x="1050" y="504" fill="#7aa8ad" font-size="16">unofficial client &#183; cached JSON</text>

    <rect x="1020" y="550" width="780" height="150" rx="16" fill="#2a1224" stroke="#ff51fa" stroke-opacity="0.4"/>
    <text x="1050" y="600" fill="#ff51fa" font-size="14" letter-spacing="3" font-weight="700">CORPUS B</text>
    <text x="1050" y="642" fill="#e7e2ff" font-size="24" font-weight="700">Wikipedia</text>
    <text x="1050" y="674" fill="#b07aab" font-size="16">MediaWiki API &#183; 429 backoff</text>

    <text x="1020" y="760" fill="#c9c4e4" font-size="20">Observed, not judged</text>
    <text x="1020" y="800" fill="#8b86a8" font-size="16">answer cosine &#183; topic overlap &#183; retrieval sim</text>
    <text x="1020" y="836" fill="#8b86a8" font-size="16">Divergence is coverage and framing &#8212; not a verdict.</text>
    <text x="1020" y="880" fill="#6d6888" font-size="15">If mean_retrieval_sim is low, you measured a miss, not bias.</text>
  </g>
"""


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <style>
    html, body {{ margin: 0; background: #0d0b21; width: 1920px; height: 1080px; overflow: hidden; }}
    svg {{ display: block; width: 1920px; height: 1080px; }}
  </style>
</head>
<body>
{svg}
</body>
</html>
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    diagrams = {
        "01-implementation-flow": flow(),
        "02-dual-corpus": dual(),
        "03-query-sequence": sequence(),
        "04-fair-ab": fair(),
    }
    for name, inner in diagrams.items():
        body = svg(inner)
        (OUT / f"{name}.svg").write_text(body, encoding="utf-8")
        # strip xml prolog for inline HTML
        inline = body.split("?>", 1)[-1].lstrip()
        (OUT / f"{name}.html").write_text(HTML.format(svg=inline), encoding="utf-8")
        print("wrote", name)


if __name__ == "__main__":
    main()
