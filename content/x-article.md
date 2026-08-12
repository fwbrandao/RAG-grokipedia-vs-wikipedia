# RAG Face-Off: two encyclopedias, one model

**Talking points**
- Same Groq `llama-3.3-70b`, same prompt, same `top_k`. Only the corpus changes.
- Free stack: Groq chat + local MiniLM (384-d) + Chroma. MiniLM truncates at 256 tokens → 220-token chunks.
- Live UI: split-screen HUD (Grokipedia cyan / Wikipedia magenta).
- Repo: https://github.com/fwbrandao/RAG-grokipedia-vs-wikipedia
- Demo: https://rag-grokipedia-vs-wikipedia.streamlit.app
- Finding to fill after Step 9: most divergent question + `answer_similarity`.

---

Two knowledge bases. One generator. Ask the same question and watch them disagree.

I built a small RAG face-off: Grokipedia vs Wikipedia. Retrieval-augmented generation usually means “chat with your docs.” Here the experiment is stricter. Both sides use the **same** model, **same** system prompt, **same** temperature, **same** `top_k`. The only variable is the corpus.

That sounds obvious until you see the answers. One side cites a different article, frames a controversy harder, or simply has no good chunk to retrieve. Divergence is not a verdict on which encyclopedia is “true.” It is a signal that coverage, emphasis, and retrieval quality differ. The similarity bars under each passage tell you whether the model even had material to work with.

Stack (all free):

- Ingest: Wikipedia MediaWiki API + unofficial Grokipedia client, cached to JSON
- Chunk: paragraph-aware, ~220 tokens (MiniLM’s 256-token ceiling is a silent footgun)
- Embed: local MiniLM via Chroma
- Generate: Groq `llama-3.3-70b-versatile`
- UI: Streamlit split-screen, cyan vs magenta

If you are learning RAG for an AI engineering role, this is the loop that matters: ingest → chunk → embed → retrieve → ground the prompt → measure. The notebook walks each step; the app is the demo.

Repo + live compare: linked above.

*(After you run notebook Step 9, paste the most divergent question and its cosine score here.)*
