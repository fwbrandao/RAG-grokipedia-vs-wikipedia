# RAG learning + project build

## Learning path (you follow along)

- [x] Day 0: venv, `pip install -r requirements.txt`, Groq key, open notebook
- [x] Step 1: Config — understand PROVIDER vs embeddings vs CHUNK_TOKENS
- [x] Step 2: Ingest — both sources cached in `data/raw/`
- [ ] Step 3: Chunk — sizes fit MiniLM (~220 tokens)
- [ ] Step 4: Embed — vector dim 384 locally
- [ ] Step 5: Chroma — two collections built
- [ ] Step 6: Retrieve + answer — one source grounded
- [ ] Step 7: `compare()` works (RAG gate before UI)
- [ ] Step 8: ipywidgets side-by-side
- [ ] Step 9: Batch eval + most divergent question
- [ ] Write 3 takeaways in your own words

## Build phases

- [x] Clean `RAG-compare.ipynb` with markdown between cells
- [x] Extract `rag/` package
- [x] Streamlit `app.py`
- [x] README / git hygiene
- [x] `content/x-article.md` + `content/linkedin-post.md` drafts
- [x] Dashboard card in `projects_dashboard` (local clone; push separately)

## Review

Polished teaching notebook, shared pipeline, cinematic Streamlit HUD, dashboard catalog entry, social drafts. GitHub push and Streamlit Cloud deploy are manual.
