"""
Vector Store Builder — Multi-Module
Generates embeddings and builds FAISS + BM25 indices per module.
Usage:
    python build_vectorstore.py --module handbook
    python build_vectorstore.py --module directions
    python build_vectorstore.py                      # builds both
"""

import json
import os
import re
import sys
import pickle
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    from rank_bm25 import BM25Okapi
except ImportError:
    print("❌ Missing dependencies. Run: pip install sentence-transformers faiss-cpu rank_bm25")
    exit(1)

SCRAPED_DIR = os.path.join("data", "scraped")
INDEX_BASE_DIR = os.path.join("data", "faiss_index")
MODEL_NAME = "all-MiniLM-L6-v2"

# Module configs (must match scraper.py output names)
MODULE_FILES = {
    "handbook": "handbook_chunks.json",
    "directions": "directions_chunks.json",
}


def load_chunks(module_key):
    """Load scraped chunks for a specific module."""
    filename = MODULE_FILES.get(module_key)
    if not filename:
        print(f"❌ Unknown module: {module_key}")
        exit(1)

    data_path = os.path.join(SCRAPED_DIR, filename)
    if not os.path.exists(data_path):
        print(f"❌ Scraped data not found at {data_path}")
        print(f"   Run scraper.py first: python scraper.py --module {module_key}")
        exit(1)

    with open(data_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    print(f"✓ Loaded {len(chunks)} chunks from {data_path}")
    return chunks


def tokenize(text):
    """Simple tokenizer for BM25."""
    return re.findall(r'\w+', text.lower())


def build_faiss_index(chunks):
    """Generate embeddings and build FAISS index."""
    print(f"\n📦 Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    texts = []
    for chunk in chunks:
        combined = f"{chunk['section']} - {chunk['header']}: {chunk['text']}"
        texts.append(combined)

    print(f"\n🔄 Generating embeddings for {len(texts)} chunks...")
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        batch_size=32,
        normalize_embeddings=True
    )

    embeddings = np.array(embeddings, dtype='float32')
    dimension = embeddings.shape[1]

    print(f"✓ Embeddings shape: {embeddings.shape}")

    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    print(f"✓ FAISS index built with {index.ntotal} vectors")
    return index


def build_bm25_index(chunks):
    """Build BM25 keyword index from chunks."""
    print(f"\n🔤 Building BM25 keyword index...")

    tokenized_corpus = []
    for chunk in chunks:
        combined = f"{chunk['section']} {chunk['header']} {chunk['text']}"
        tokens = tokenize(combined)
        tokenized_corpus.append(tokens)

    bm25 = BM25Okapi(tokenized_corpus)

    print(f"✓ BM25 index built with {len(tokenized_corpus)} documents")
    return bm25


def save_all(faiss_index, bm25_index, chunks, module_key):
    """Save FAISS index, BM25 index, and metadata to module-specific directory."""
    index_dir = os.path.join(INDEX_BASE_DIR, module_key)
    os.makedirs(index_dir, exist_ok=True)

    # Save FAISS index
    index_path = os.path.join(index_dir, "index.faiss")
    faiss.write_index(faiss_index, index_path)
    print(f"✓ FAISS index saved to {index_path}")

    # Save BM25 index
    bm25_path = os.path.join(index_dir, "bm25.pkl")
    with open(bm25_path, 'wb') as f:
        pickle.dump(bm25_index, f)
    print(f"✓ BM25 index saved to {bm25_path}")

    # Save metadata
    metadata = []
    for chunk in chunks:
        metadata.append({
            'id': chunk['id'],
            'text': chunk['text'],
            'header': chunk['header'],
            'url': chunk['url'],
            'section': chunk['section'],
            'module': module_key,
        })

    metadata_path = os.path.join(index_dir, "metadata.pkl")
    with open(metadata_path, 'wb') as f:
        pickle.dump(metadata, f)
    print(f"✓ Metadata saved to {metadata_path}")

    # Save summary
    summary = {
        'module': module_key,
        'total_vectors': len(chunks),
        'model': MODEL_NAME,
        'search_type': 'hybrid (FAISS + BM25)',
        'sections': list(set(c['section'] for c in chunks)),
        'total_sections': len(set(c['section'] for c in chunks))
    }
    summary_path = os.path.join(index_dir, "index_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Summary saved to {summary_path}")


def build_module(module_key):
    """Build vector store for a single module."""
    print(f"\n🔧 Building Vector Store for: {module_key.upper()}")
    print("=" * 50)

    chunks = load_chunks(module_key)
    faiss_index = build_faiss_index(chunks)
    bm25_index = build_bm25_index(chunks)
    save_all(faiss_index, bm25_index, chunks, module_key)

    print(f"\n{'=' * 50}")
    print(f"✅ {module_key.upper()} vector store built successfully!")


def main():
    # Parse --module argument
    module_key = None
    if "--module" in sys.argv:
        idx = sys.argv.index("--module")
        if idx + 1 < len(sys.argv):
            module_key = sys.argv[idx + 1].lower()
        else:
            print("❌ --module requires a value: handbook, directions, or omit for both")
            exit(1)

    if module_key:
        if module_key not in MODULE_FILES:
            print(f"❌ Unknown module: {module_key}. Choose from: {list(MODULE_FILES.keys())}")
            exit(1)
        build_module(module_key)
    else:
        # Build all available modules
        for key in MODULE_FILES:
            data_path = os.path.join(SCRAPED_DIR, MODULE_FILES[key])
            if os.path.exists(data_path):
                build_module(key)
            else:
                print(f"⚠ Skipping {key} — no scraped data found at {data_path}")

    print(f"\n✅ All done!")


if __name__ == "__main__":
    main()
