"""
RAG Chatbot Backend — Multi-Module
Hybrid search (FAISS + BM25) → Jina Reranker → OpenRouter LLM.
Supports both Handbook and Directions modules.
"""

import os
import re
import pickle
import json
import numpy as np
import requests as http_requests

try:
    import faiss
    from sentence_transformers import SentenceTransformer
    from openai import OpenAI
    from rank_bm25 import BM25Okapi
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("   Run: pip install openai faiss-cpu sentence-transformers rank_bm25")
    exit(1)

# Configuration
INDEX_BASE_DIR = os.path.join("data", "faiss_index")
MODEL_NAME = "all-MiniLM-L6-v2"
OPENROUTER_MODEL = "openrouter/free"
FAISS_TOP_K = 10
BM25_TOP_K = 10
RERANK_TOP_N = 5
RRF_K = 60

# Jina Reranker config
JINA_RERANK_URL = "https://api.jina.ai/v1/rerank"
JINA_RERANK_MODEL = "jina-reranker-v3"

# Module-specific system prompts
SYSTEM_PROMPTS = {
    "handbook": """You are **GitLab Handbook Assistant**, a helpful AI that answers questions about GitLab's company handbook.

## Your Role
- You answer questions ONLY based on the provided handbook context.
- You are friendly, professional, and thorough.
- You help GitLab employees and aspiring employees learn about the company.

## Rules
1. **Only use the provided context** to answer questions. Do not make up information.
2. **If the context doesn't contain the answer**, say: "I couldn't find specific information about that in the handbook sections I have access to. You can search the full handbook at https://handbook.gitlab.com"
3. **Always cite your sources** by mentioning the section name and linking to the URL.
4. **Be concise but complete**. Use bullet points and formatting for readability.
5. **For follow-up questions**, use the conversation history to maintain context.
6. **Refuse off-topic questions** politely: "I'm designed to help with GitLab's handbook. Could you ask me something about GitLab's values, processes, or policies?"

## Format
- Use markdown formatting for clear responses
- Include source links at the end
- Use bullet points for lists
- Bold important terms
""",
    "directions": """You are **GitLab Direction Assistant**, a helpful AI that answers questions about GitLab's product direction and strategy.

## Your Role
- You answer questions ONLY based on the provided direction/strategy context.
- You are friendly, professional, and thorough.
- You help users understand GitLab's product vision, strategy, investment themes, and roadmap.

## Rules
1. **Only use the provided context** to answer questions. Do not make up information.
2. **If the context doesn't contain the answer**, say: "I couldn't find specific information about that in the direction pages I have access to. You can browse the full direction at https://about.gitlab.com/direction/"
3. **Always cite your sources** by mentioning the section name and linking to the URL.
4. **Be concise but complete**. Use bullet points and formatting for readability.
5. **For follow-up questions**, use the conversation history to maintain context.
6. **Refuse off-topic questions** politely: "I'm designed to help with GitLab's product direction and strategy. Could you ask me something about GitLab's roadmap, investment themes, or product vision?"

## Format
- Use markdown formatting for clear responses
- Include source links at the end
- Use bullet points for lists
- Bold important terms
""",
}


def tokenize(text):
    """Simple tokenizer for BM25."""
    return re.findall(r'\w+', text.lower())


class HandbookChatbot:
    """RAG-based chatbot with hybrid search and Jina reranking. Supports multiple modules."""

    def __init__(self, api_key=None, module="handbook"):
        self.module = module
        self.index = None
        self.bm25 = None
        self.metadata = None
        self.embed_model = None
        self.client = None
        self.jina_api_key = None
        self.is_ready = False
        self._load_components(api_key)

    def _load_components(self, api_key=None):
        """Load FAISS, BM25, embedding model, and OpenRouter client."""
        try:
            index_dir = os.path.join(INDEX_BASE_DIR, self.module)

            # Also try legacy path for backward compatibility
            legacy_dir = INDEX_BASE_DIR
            use_legacy = False

            # Load FAISS index
            index_path = os.path.join(index_dir, "index.faiss")
            legacy_path = os.path.join(legacy_dir, "handbook.index")

            if os.path.exists(index_path):
                self.index = faiss.read_index(index_path)
                print(f"✓ FAISS index loaded ({self.index.ntotal} vectors) [{self.module}]")
            elif self.module == "handbook" and os.path.exists(legacy_path):
                # Backward compat: old-style single index
                self.index = faiss.read_index(legacy_path)
                use_legacy = True
                print(f"✓ FAISS index loaded (legacy) ({self.index.ntotal} vectors)")
            else:
                print(f"⚠ FAISS index not found for module '{self.module}'")
                print(f"  Run: python build_vectorstore.py --module {self.module}")
                return

            # Load BM25 index
            bm25_path = os.path.join(index_dir, "bm25.pkl")
            legacy_bm25 = os.path.join(legacy_dir, "bm25.pkl")

            if os.path.exists(bm25_path):
                with open(bm25_path, 'rb') as f:
                    self.bm25 = pickle.load(f)
                print(f"✓ BM25 index loaded [{self.module}]")
            elif use_legacy and os.path.exists(legacy_bm25):
                with open(legacy_bm25, 'rb') as f:
                    self.bm25 = pickle.load(f)
                print(f"✓ BM25 index loaded (legacy)")
            else:
                print("⚠ BM25 index not found — keyword search disabled")

            # Load metadata
            metadata_path = os.path.join(index_dir, "metadata.pkl")
            legacy_meta = os.path.join(legacy_dir, "metadata.pkl")

            if os.path.exists(metadata_path):
                with open(metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
            elif use_legacy and os.path.exists(legacy_meta):
                with open(legacy_meta, 'rb') as f:
                    self.metadata = pickle.load(f)

            print(f"✓ Metadata loaded ({len(self.metadata)} entries)")

            # Load embedding model
            print(f"📦 Loading embedding model: {MODEL_NAME}")
            self.embed_model = SentenceTransformer(MODEL_NAME)
            print(f"✓ Embedding model loaded")

            # Load Jina API key
            self.jina_api_key = os.getenv("JINA_API_KEY", "")
            if not self.jina_api_key:
                try:
                    import streamlit as st
                    self.jina_api_key = st.secrets.get("JINA_API_KEY", "")
                except Exception:
                    pass
            if self.jina_api_key:
                print(f"✓ Jina Reranker configured ({JINA_RERANK_MODEL})")
            else:
                print("⚠ No JINA_API_KEY — reranking disabled")

            # Configure OpenRouter
            resolved_key = api_key or os.getenv("OPENROUTER_API_KEY")
            if not resolved_key:
                print("⚠ No OpenRouter API key found.")
                return

            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=resolved_key,
                default_headers={
                    "HTTP-Referer": "https://gitlab-handbook-chatbot.streamlit.app",
                    "X-OpenRouter-Title": "GitLab Handbook Assistant",
                }
            )
            print(f"✓ OpenRouter client configured (model: {OPENROUTER_MODEL})")

            self.is_ready = True
            module_label = self.module.upper()
            print(f"✅ Chatbot ready! [{module_label}] (Hybrid: FAISS + BM25 → Jina Rerank)")

        except Exception as e:
            print(f"❌ Error initializing chatbot: {e}")
            self.is_ready = False

    def _faiss_search(self, query, k=FAISS_TOP_K):
        """Semantic similarity search using FAISS."""
        if not self.index or not self.embed_model:
            return []

        query_embedding = self.embed_model.encode(
            [query], normalize_embeddings=True
        ).astype('float32')

        scores, indices = self.index.search(query_embedding, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if 0 <= idx < len(self.metadata):
                results.append((int(idx), float(score)))
        return results

    def _bm25_search(self, query, k=BM25_TOP_K):
        """Keyword search using BM25."""
        if not self.bm25:
            return []

        tokens = tokenize(query)
        scores = self.bm25.get_scores(tokens)

        top_indices = np.argsort(scores)[-k:][::-1]
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((int(idx), float(scores[idx])))
        return results

    def hybrid_search(self, query):
        """Combine FAISS and BM25 results using Reciprocal Rank Fusion."""
        faiss_results = self._faiss_search(query, k=FAISS_TOP_K)
        bm25_results = self._bm25_search(query, k=BM25_TOP_K)

        print("\n" + "=" * 60)
        print(f"🔍 HYBRID SEARCH [{self.module.upper()}] for: \"{query}\"")
        print("=" * 60)

        print(f"\n📊 FAISS Semantic Results (Top {len(faiss_results)}):")
        for i, (idx, score) in enumerate(faiss_results):
            m = self.metadata[idx]
            print(f"  [{i+1}] Score: {score:.4f} | {m['section']} — {m['header']}")

        print(f"\n🔤 BM25 Keyword Results (Top {len(bm25_results)}):")
        for i, (idx, score) in enumerate(bm25_results):
            m = self.metadata[idx]
            print(f"  [{i+1}] Score: {score:.4f} | {m['section']} — {m['header']}")

        # Reciprocal Rank Fusion
        rrf_scores = {}

        for rank, (idx, _) in enumerate(faiss_results):
            rrf_scores[idx] = rrf_scores.get(idx, 0) + 1.0 / (RRF_K + rank + 1)

        for rank, (idx, _) in enumerate(bm25_results):
            rrf_scores[idx] = rrf_scores.get(idx, 0) + 1.0 / (RRF_K + rank + 1)

        sorted_indices = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        top_n = FAISS_TOP_K

        merged = []
        print(f"\n🔀 RRF Merged Results (Top {min(top_n, len(sorted_indices))}):")
        for i, (idx, rrf_score) in enumerate(sorted_indices[:top_n]):
            m = self.metadata[idx]
            result = m.copy()
            result['relevance_score'] = rrf_score
            merged.append(result)

            in_faiss = any(fi == idx for fi, _ in faiss_results)
            in_bm25 = any(bi == idx for bi, _ in bm25_results)
            source = "BOTH" if (in_faiss and in_bm25) else ("FAISS" if in_faiss else "BM25")
            print(f"  [{i+1}] RRF: {rrf_score:.4f} | [{source}] | {m['section']} — {m['header']}")

        print("=" * 60)
        return merged

    def rerank(self, query, chunks, top_n=RERANK_TOP_N):
        """Rerank chunks using Jina Reranker API."""
        if not self.jina_api_key or not chunks:
            return chunks[:top_n]

        try:
            documents = [
                f"{chunk['section']} — {chunk['header']}: {chunk['text']}"
                for chunk in chunks
            ]

            response = http_requests.post(
                JINA_RERANK_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.jina_api_key}"
                },
                json={
                    "model": JINA_RERANK_MODEL,
                    "query": query,
                    "top_n": top_n,
                    "documents": documents,
                    "return_documents": False
                },
                timeout=10
            )
            response.raise_for_status()
            result = response.json()

            reranked = []
            for item in result.get("results", []):
                idx = item["index"]
                if idx < len(chunks):
                    chunk = chunks[idx].copy()
                    chunk['rerank_score'] = item["relevance_score"]
                    reranked.append(chunk)

            print(f"\n🎯 JINA RERANKED (Top {len(reranked)}):")
            for i, chunk in enumerate(reranked):
                print(f"  [{i+1}] Score: {chunk['rerank_score']:.4f} | {chunk['section']} — {chunk['header']}")
            print("=" * 60 + "\n")

            return reranked

        except Exception as e:
            print(f"⚠ Jina reranker failed ({e}), using RRF order")
            return chunks[:top_n]

    def generate_response(self, query, history=None):
        """RAG pipeline: hybrid search → rerank → generate."""
        if not self.is_ready:
            return {
                'response': "⚠ The chatbot is not fully initialized.",
                'sources': [], 'confidence': 0
            }

        # Step 1: Hybrid search
        merged_chunks = self.hybrid_search(query)

        if not merged_chunks:
            return {
                'response': "I couldn't find any relevant information. Please try rephrasing.",
                'sources': [], 'confidence': 0
            }

        # Step 2: Rerank with Jina
        final_chunks = self.rerank(query, merged_chunks, top_n=RERANK_TOP_N)

        # Step 3: Build context
        context_parts = []
        sources = []
        seen_urls = set()

        for i, chunk in enumerate(final_chunks):
            context_parts.append(
                f"[Source {i+1}: {chunk['section']} — {chunk['header']}]\n{chunk['text']}"
            )
            if chunk['url'] not in seen_urls:
                sources.append({
                    'section': chunk['section'],
                    'header': chunk['header'],
                    'url': chunk['url'],
                    'relevance': chunk.get('rerank_score', chunk['relevance_score'])
                })
                seen_urls.add(chunk['url'])

        context = "\n\n---\n\n".join(context_parts)

        # Step 4: Build messages with module-specific prompt
        system_prompt = SYSTEM_PROMPTS.get(self.module, SYSTEM_PROMPTS["handbook"])
        messages = [{"role": "system", "content": system_prompt}]

        if history:
            for msg in history[-6:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        source_label = "handbook" if self.module == "handbook" else "direction"
        user_message = f"""Based on the following {source_label} context, answer the user's question.

## Retrieved {source_label.title()} Context:
{context}

## User Question:
{query}

Remember to cite the sources and be helpful. If the context doesn't fully answer the question, say so."""

        messages.append({"role": "user", "content": user_message})

        # Step 5: Generate with OpenRouter
        try:
            response = self.client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=messages,
                max_tokens=2048,
                temperature=0.7,
            )

            response_text = response.choices[0].message.content

            avg_relevance = sum(
                c.get('rerank_score', c['relevance_score']) for c in final_chunks
            ) / len(final_chunks)
            confidence = min(avg_relevance * 100, 100)

            return {
                'response': response_text,
                'sources': sources,
                'confidence': round(confidence, 1),
                'chunks_retrieved': len(final_chunks)
            }

        except Exception as e:
            return {
                'response': f"Error generating response: {str(e)}. Please try again.",
                'sources': sources, 'confidence': 0
            }

    def get_suggested_questions(self):
        if self.module == "directions":
            return [
                "What is GitLab's 3-year product strategy?",
                "What are GitLab's strategic challenges?",
                "What are the FY26 R&D investment themes?",
                "How does GitLab approach DevSecOps?",
                "What is GitLab's AI/ML direction?",
                "What are GitLab's key product investment themes?",
                "How does GitLab plan releases?",
                "What is GitLab's approach to platform completeness?",
                "What are GitLab's quarterly OKRs?",
                "How does GitLab mitigate low-end disruption?",
            ]
        return [
            "What are GitLab's core values?",
            "How does GitLab's hiring process work?",
            "What is GitLab's communication style?",
            "Tell me about GitLab's remote work culture",
            "What are GitLab's product principles?",
            "How does GitLab handle diversity and inclusion?",
            "What is GitLab's engineering workflow?",
            "How does GitLab approach security?",
            "What are GitLab's total rewards?",
            "Tell me about GitLab's leadership principles",
        ]

    def get_available_topics(self):
        if not self.metadata:
            return []
        return sorted(set(m['section'] for m in self.metadata))
