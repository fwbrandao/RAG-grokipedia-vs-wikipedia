# Learn RAG by building: Grokipedia vs Wikipedia

Follow this top to bottom. Each step has: **concept → do this → success looks like → if stuck**.

Your finished notebook is [`RAG-compare.ipynb`](RAG-compare.ipynb).  
[`reference/rag_compare_ANSWER_KEY.ipynb`](reference/rag_compare_ANSWER_KEY.ipynb) is a backup. Live UI: `streamlit run app.py`.

---

## The one mental model

```
Question
   │
   ▼
Embed question ──► search vector DB ──► top-k text chunks
                                           │
                                           ▼
                              LLM answers USING only those chunks
```

**RAG = Retrieval + Augmented + Generation.**  
You do not dump a whole encyclopedia into the prompt. You retrieve a few relevant passages, then generate.

In this project the **generator is identical** on both sides (same Groq model, prompt, `top_k`).  
The **only** variable is the knowledge base (Grokipedia vs Wikipedia). Differences you see come from the corpus, not from “two different chatbots.”

---

## Day 0 — Environment (15 min)

### Concept
A virtualenv isolates packages. Free generation uses **Groq**. Free embeddings use **MiniLM** (bundled with Chroma) — no embedding API key.

### Do this

```bash
cd /Users/mymac/AI/RAG-grokipedia-vs-wikipedia
source .venv/bin/activate
pip install -r requirements.txt
```

1. Get a free key: https://console.groq.com/keys  
2. Confirm `.env` has `GROQ_API_KEY=...` (copy from `.env.example` if needed).  
3. Start Jupyter:

```bash
jupyter lab
```

4. Open `reference/rag_compare_ANSWER_KEY.ipynb`.  
5. Kernel → select the `.venv` interpreter if asked.

### Success
Kernel starts; no import errors on Step 0 (`%pip install` cell).

### If stuck
- Wrong Python: `which python` should show `.../RAG-grokipedia-vs-wikipedia/.venv/bin/python`
- Missing key: `assert` on `GROQ_API_KEY` will fail in config — fix `.env`, restart kernel

---

## Step 1 — Config (10 min)

### Concept
Separate concerns:

| Piece | Role |
|---|---|
| `PROVIDER` | Who runs the **chat** model (Groq / Ollama / OpenAI) |
| Embedding backend | Turns text → vectors (local MiniLM here) |
| `CHUNK_TOKENS` / `TOP_K` | How big pieces are / how many you feed the LLM |
| `TOPICS` | What articles you index |

**Critical free-stack fact:** MiniLM truncates at **256 tokens**. Chunks must stay ~**220** tokens or the tail of each chunk is invisible to search.

### Do this
Run the Step 1 config cell. Read every printed line (`PROVIDER`, embed backend, chunk size).

### Success
Prints `PROVIDER=groq`, local embeddings, chunk size ≤ 220.

---

## Step 2 — Ingest (20 min) — “build the library”

### Concept
**Ingestion** = pull documents into a consistent shape and cache them.

- Wikipedia: public MediaWiki API  
- Grokipedia: unofficial client (`grokipedia-api`)  
- Cache: `data/raw/*.json` so you can re-run offline

You are not “doing RAG” yet — you are building the **knowledge base files**.

### Do this
Run ingest cells. Confirm files under `data/raw/` for both `grokipedia__...` and `wikipedia__...`.

### Success
For each topic, both sources have non-empty `text`. Char counts can differ a lot (that’s fine — and it’s part of the experiment).

### If stuck
- Grokipedia API flaky → use existing files in `data/raw/` (already committed). Set `use_cache=True`.
- **HTTP 429 Too Many Requests** from Wikipedia: you asked too fast. Wait ~60 seconds, then **re-run the same ingest cell**. Cache skips topics already saved in `data/raw/`, so only the failed topic is fetched again. The fetch helper retries 429s with backoff.

**Learn check:** Why cache raw JSON instead of re-fetching every run?

---

## Step 3 — Chunk (20 min) — “tear pages into search cards”

### Concept
Whole articles are too big for the context window and too coarse for search.  
**Chunking** splits text into overlapping windows so retrieval can return a tight passage.

- Size ≈ embedding model limit  
- Overlap keeps sentences from being cut mid-thought  
- Prefer splitting on paragraphs when possible

### Do this
Run chunking cells. Print: docs per source, chunks per source, avg tokens/chunk.

### Success
Hundreds of chunks; average tokens near `CHUNK_TOKENS` (not thousands).

**Learn check:** What goes wrong if chunks are 2,000 tokens with MiniLM?

---

## Step 4 — Embed (15 min) — “turn text into coordinates”

### Concept
An **embedding** is a vector of numbers. Similar meaning → nearby vectors.  
You embed every chunk once at index time; later you embed the **question** the same way and find nearest neighbors.

### Do this
Run the embed helper cells. Embed a tiny list like `["hello world"]` and print `len(vector)` (expect **384** for MiniLM).

### Success
Vectors length 384; no API error (local path should not need OpenAI).

**Learn check:** Why can’t you mix MiniLM vectors and OpenAI vectors in one Chroma collection?

---

## Step 5 — Vector store (20 min) — “two separate libraries”

### Concept
**Chroma** stores (embedding, text, metadata).  
This project uses **two collections**: `kb_grokipedia` and `kb_wikipedia`, same schema, different corpora. That is the A/B design.

### Do this
Build/persist collections under `data/chroma/`. Count items in each collection.

### Success
Both collections non-empty; counts match chunk counts from Step 3.

**Learn check:** Why two collections instead of one collection with a `source` filter? (Either works; two collections make the “fair face-off” obvious.)

---

## Step 6 — Retrieve + generate (25 min) — “this is RAG”

### Concept
1. **Retrieve:** embed question → query one collection → top-k chunks + similarity  
2. **Augment:** stuff those chunks into the prompt as numbered context  
3. **Generate:** LLM answers **only** from context (system prompt forces citations)

Without retrieval, the model answers from memory. With RAG, answers are grounded in *your* docs.

### Do this
Call `retrieve("What are the main criticisms of Elon Musk?", "wikipedia")` and inspect texts + scores.  
Then call `answer(...)` for **one** source. Read the prompt construction in code.

### Success
- Retrieved chunks look topically relevant  
- Answer cites passage numbers  
- If you remove context, the prompt should be empty/unusable (grounding works)

**Learn check:** What does a low similarity score suggest — model failure or missing coverage?

---

## Step 7 — Compare (20 min) — “fair A/B”

### Concept
`compare(question)`:

1. Embed the question **once**  
2. Retrieve from Grokipedia and Wikipedia with that same vector  
3. Generate twice with the **same** system prompt / temperature  
4. Score how similar the two answers are (divergence)

### Do this
Run `compare(...)` on one question. Print both answers and mean retrieval similarities.

### Success
Two answers + citations. You can explain *why* they differ (coverage vs framing vs retrieval miss).

**Gate:** Do not build UI until this works.

---

## Step 8 — Notebook UI (15 min)

### Concept
Same `compare()` behind buttons — UX for demos, not new ML.

### Do this
Run the ipywidgets cells. Ask 2–3 questions covered by your topics.

### Success
Side-by-side answers + passages render without errors.

---

## Step 9 — Batch eval (20 min)

### Concept
One-off demos convince *you*. A **fixed question set** + table of divergence metrics is evidence.

### Do this
Run eval questions → DataFrame. Sort by lowest answer similarity. Export JSON if the notebook does.

### Success
You can point to the “most divergent” question and open both answers.

---

## After RAG works (later phases)

Not required to *learn* RAG, but part of the project plan:

1. Clean `RAG-compare.ipynb` with markdown between cells (repo-ready).  
2. Streamlit `app.py` for portfolio / Projects dashboard.  
3. Draft an X article and a LinkedIn post using real divergence findings.

---

## Glossary (keep this nearby)

| Term | Meaning |
|---|---|
| Document | Full article |
| Chunk | Slice of a document you index |
| Embedding | Vector representation of text |
| Collection / index | Vector DB table of chunks |
| top-k | How many chunks you retrieve |
| Grounding | Forcing the LLM to use retrieved text |
| Hallucination | Fluent answer not supported by retrieved context |
| Divergence | Two grounded answers disagree because corpora differ |

---

## Suggested study rhythm

| Session | Steps | Time |
|---|---|---|
| 1 | Day 0 + Steps 1–3 | ~1 hour |
| 2 | Steps 4–7 + gate test | ~1.5 hours |
| 3 | Steps 8–9 + write 3 takeaways | ~45 min |

After session 2, write in your own words:

1. What RAG adds vs a naked LLM call  
2. Why chunk size matters with MiniLM  
3. Why identical generator settings matter for this face-off
