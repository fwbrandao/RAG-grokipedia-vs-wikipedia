# LinkedIn post (publish after the X article)

I built a RAG face-off as part of leveling up toward an AI Engineer role: the **same** LLM answers the **same** question from two encyclopedias — Grokipedia and Wikipedia.

What I wanted to prove to myself:

- RAG is retrieve → stuff context into the prompt → generate. Not “dump the internet into the model.”
- A fair A/B means identical model, prompt, temperature, and `top_k`. Only the corpus may change.
- Chunk size is a product decision. MiniLM silently truncates at 256 tokens; I chunk at 220.
- Divergence ≠ accuracy. If retrieval similarity is low, you may be looking at a coverage miss, not a biased article.

Stack: Python, Groq (free), Chroma + local MiniLM, Jupyter, Streamlit.

Notebook (step-by-step) and live split-screen UI:
https://github.com/fwbrandao/RAG-grokipedia-vs-wikipedia
https://rag-grokipedia-vs-wikipedia.streamlit.app

Next: hybrid search and a no-RAG baseline so I can see how much the corpus actually moves the answer.

#RAG #AIEngineering #LLM #MachineLearning #Python
