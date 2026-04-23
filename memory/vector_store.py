"""
memory/vector_store.py — Persistent memory via FAISS + sentence-transformers.

Falls back to simple cosine-similarity JSON store if FAISS unavailable.
"""

import json
import os
import time
import numpy as np
from typing import Optional

MEMORY_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "memory")
MEMORY_JSON = os.path.join(MEMORY_DIR, "entries.json")

# Lazy-loaded globals
_embedder = None
_index = None
_entries: list[dict] = []
_USE_FAISS = False


def _init():
    """Initialize the memory system (lazy)."""
    global _embedder, _index, _entries, _USE_FAISS
    if _embedder is not None:
        return

    os.makedirs(MEMORY_DIR, exist_ok=True)

    # Load existing entries
    if os.path.exists(MEMORY_JSON):
        with open(MEMORY_JSON, "r", encoding="utf-8") as f:
            _entries = json.load(f)
    else:
        _entries = []

    # Try FAISS + sentence-transformers
    try:
        import faiss
        from sentence_transformers import SentenceTransformer

        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        dim = _embedder.get_sentence_embedding_dimension()

        faiss_path = os.path.join(MEMORY_DIR, "index.faiss")
        if os.path.exists(faiss_path) and _entries:
            _index = faiss.read_index(faiss_path)
        else:
            _index = faiss.IndexFlatL2(dim)
            # Re-index existing entries
            if _entries:
                texts = [e["text"] for e in _entries]
                vecs = _embedder.encode(texts, normalize_embeddings=True)
                _index.add(np.array(vecs, dtype=np.float32))

        _USE_FAISS = True
        print("[memory] ✓ FAISS + sentence-transformers loaded")

    except ImportError:
        print("[memory] ⚠ FAISS not available, using JSON fallback")
        _USE_FAISS = False
        # Fallback: use a simple embedding approach
        try:
            from sentence_transformers import SentenceTransformer
            _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError:
            _embedder = None
            print("[memory] ⚠ sentence-transformers not available, using keyword matching")


def _save():
    """Persist entries to disk."""
    global _index
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(MEMORY_JSON, "w", encoding="utf-8") as f:
        json.dump(_entries, f, indent=2)

    if _USE_FAISS and _index is not None:
        import faiss
        faiss_path = os.path.join(MEMORY_DIR, "index.faiss")
        faiss.write_index(_index, faiss_path)


def add_memory(text: str, category: str = "general", metadata: Optional[dict] = None) -> str:
    """
    Store a memory entry.

    Args:
        text: The content to remember.
        category: One of 'error', 'fix', 'success', 'plan', 'general'.
        metadata: Optional extra data to store.

    Returns:
        Confirmation string.
    """
    _init()

    entry = {
        "text": text,
        "category": category,
        "timestamp": time.time(),
        "metadata": metadata or {},
    }
    _entries.append(entry)

    # Add to FAISS index
    if _USE_FAISS and _embedder is not None:
        vec = _embedder.encode([text], normalize_embeddings=True)
        _index.add(np.array(vec, dtype=np.float32))

    _save()
    return f"Memory stored ({category}): {text[:80]}..."


def search_memory(query: str, top_k: int = 5) -> list[dict]:
    """
    Search memory for relevant past entries.

    Args:
        query: Search query.
        top_k: Number of results to return.

    Returns:
        List of matching entries with scores.
    """
    _init()

    if not _entries:
        return []

    if _USE_FAISS and _embedder is not None and _index is not None and _index.ntotal > 0:
        return _faiss_search(query, top_k)
    elif _embedder is not None:
        return _embedding_search(query, top_k)
    else:
        return _keyword_search(query, top_k)


def _faiss_search(query: str, top_k: int) -> list[dict]:
    """Search using FAISS."""
    vec = _embedder.encode([query], normalize_embeddings=True)
    k = min(top_k, _index.ntotal)
    distances, indices = _index.search(np.array(vec, dtype=np.float32), k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < len(_entries):
            entry = dict(_entries[idx])
            entry["score"] = float(1.0 / (1.0 + dist))
            results.append(entry)
    return results


def _embedding_search(query: str, top_k: int) -> list[dict]:
    """Search using cosine similarity without FAISS."""
    query_vec = _embedder.encode([query], normalize_embeddings=True)[0]
    texts = [e["text"] for e in _entries]
    vecs = _embedder.encode(texts, normalize_embeddings=True)

    scores = np.dot(vecs, query_vec)
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        entry = dict(_entries[idx])
        entry["score"] = float(scores[idx])
        results.append(entry)
    return results


def _keyword_search(query: str, top_k: int) -> list[dict]:
    """Fallback keyword-based search."""
    query_words = set(query.lower().split())
    scored = []

    for entry in _entries:
        text_words = set(entry["text"].lower().split())
        overlap = len(query_words & text_words)
        if overlap > 0:
            scored.append((overlap / max(len(query_words), 1), entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, entry in scored[:top_k]:
        e = dict(entry)
        e["score"] = score
        results.append(e)
    return results


def get_relevant_context(query: str, top_k: int = 3) -> str:
    """Get formatted memory context for agent prompts."""
    results = search_memory(query, top_k)
    if not results:
        return ""

    lines = ["## Relevant Past Memories:"]
    for r in results:
        cat = r.get("category", "general")
        text = r["text"][:300]
        lines.append(f"- [{cat}] {text}")
    return "\n".join(lines)
