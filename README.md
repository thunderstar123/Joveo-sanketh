# GitLab Assistant — RAG Chatbot

A premium **Retrieval-Augmented Generation (RAG)** chatbot that answers questions from two GitLab knowledge bases:

| Module | Source | Description |
|--------|--------|-------------|
| 📖 **Handbook** | [handbook.gitlab.com](https://handbook.gitlab.com) | Company culture, values, processes, hiring, engineering |
| 🧭 **Direction** | [about.gitlab.com/direction](https://about.gitlab.com/direction/) | Product strategy, roadmap, investment themes, DevSecOps |

## Architecture

```
Scraper → Chunks (JSON) → Embeddings → FAISS + BM25 Index
                                              ↓
                    Streamlit UI ← OpenRouter LLM ← Hybrid Search → Jina Rerank
```

**Powered by:**
- 🧠 OpenRouter AI (Gemini 2.0 Flash) — LLM generation
- 📚 FAISS — Semantic vector search
- 🔤 BM25 — Keyword search
- 🎯 Jina Reranker — Result reranking
- 🔀 Reciprocal Rank Fusion — Hybrid merge

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file:

```env
OPENROUTER_API_KEY=sk-or-...
JINA_API_KEY=jina_...
```

### 3. Scrape Data

```bash
# Scrape GitLab Handbook
python scraper.py --module handbook

# Scrape GitLab Direction
python scraper.py --module directions
```

### 4. Build Vector Stores

```bash
# Build for a specific module
python build_vectorstore.py --module handbook
python build_vectorstore.py --module directions

# Or build all available at once
python build_vectorstore.py
```

### 5. Run the App

```bash
streamlit run app.py
```

Use the **dropdown in the sidebar** to switch between Handbook and Direction knowledge bases.

## Optional: Generate PDFs

```bash
python generate_pdf.py --module handbook
python generate_pdf.py --module directions
```

## Project Structure

```
├── app.py                  # Streamlit UI with module selector
├── chatbot.py              # RAG backend (hybrid search + rerank)
├── scraper.py              # Multi-module web scraper
├── build_vectorstore.py    # FAISS + BM25 index builder
├── generate_pdf.py         # PDF book generator
├── styles.py               # Custom CSS theme
├── requirements.txt        # Python dependencies
├── .env                    # API keys (not committed)
└── data/
    ├── scraped/
    │   ├── handbook_chunks.json
    │   └── directions_chunks.json
    └── faiss_index/
        ├── handbook/       # Handbook FAISS + BM25 + metadata
        └── directions/     # Directions FAISS + BM25 + metadata
```

## Features

- 🔀 **Module Selector** — Switch between Handbook and Direction with a dropdown
- 🔍 **Hybrid Search** — Combines semantic (FAISS) and keyword (BM25) search
- 🎯 **Jina Reranking** — Cross-encoder reranking for better relevance
- 📚 **Source Citations** — Every answer includes source links
- 🗂️ **Quick Topics** — Pre-built topic buttons per module
- 📄 **PDF Export** — Generate PDF books from scraped data
- 🎨 **Premium UI** — Dark theme with GitLab branding
