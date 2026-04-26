"""
memory/vector_store.py - Persistent memory via FAISS + sentence-transformers.

Falls back to cosine similarity or keyword matching when heavy dependencies
are unavailable, and supports background warmup to reduce first-request lag.
"""

import json
import os
import threading
import time
from typing import Optional

import numpy as np

MEMORY_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "memory")
MEMORY_JSON = os.path.join(MEMORY_DIR, "entries.json")

_embedder = None
_index = None
_entries: list[dict] = []
_USE_FAISS = False
_init_lock = threading.Lock()
_warm_thread = None


def _load_entries():
    """Load persisted memory entries without loading embedding models."""
    global _entries
    os.makedirs(MEMORY_DIR, exist_ok=True)
    if os.path.exists(MEMORY_JSON):
        with open(MEMORY_JSON, "r", encoding="utf-8") as handle:
            _entries = json.load(handle)
    else:
        _entries = []


def _init(allow_heavy: bool = True):
    """Initialize the memory system lazily."""
    global _embedder, _index, _entries, _USE_FAISS

    with _init_lock:
        if _embedder is not None:
            return

        if not _entries:
            _load_entries()

        if not allow_heavy:
            return

        try:
            import faiss
            from sentence_transformers import SentenceTransformer

            try:
                _embedder = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
            except Exception as e:
                _USE_FAISS = False
                _embedder = None
                print(f"[memory] Offline model missing, memory disabled. ({e})")
                return
            try:
                dim = _embedder.get_embedding_dimension()
            except AttributeError:
                dim = _embedder.get_sentence_embedding_dimension()

            faiss_path = os.path.join(MEMORY_DIR, "index.faiss")
            if os.path.exists(faiss_path) and _entries:
                _index = faiss.read_index(faiss_path)
            else:
                _index = faiss.IndexFlatL2(dim)
                if _entries:
                    texts = [entry["text"] for entry in _entries]
                    vecs = _embedder.encode(texts, normalize_embeddings=True)
                    _index.add(np.array(vecs, dtype=np.float32))

            _USE_FAISS = True
            print("[memory] FAISS + sentence-transformers loaded")
        except ImportError:
            _USE_FAISS = False
            try:
                from sentence_transformers import SentenceTransformer
                try:
                    _embedder = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
                    print("[memory] sentence-transformers loaded without FAISS")
                except Exception:
                    _embedder = None
                    print("[memory] using keyword memory fallback")
            except ImportError:
                _embedder = None
                print("[memory] using keyword memory fallback")


def _save():
    """Persist entries to disk."""
    global _index
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(MEMORY_JSON, "w", encoding="utf-8") as handle:
        json.dump(_entries, handle, indent=2)

    if _USE_FAISS and _index is not None:
        import faiss

        faiss_path = os.path.join(MEMORY_DIR, "index.faiss")
        faiss.write_index(_index, faiss_path)


def warm_memory_system():
    """Warm the heavy memory stack on a background thread."""
    global _warm_thread

    def _warm():
        try:
            _init(allow_heavy=True)
        except Exception as e:
            print(f"[memory] warmup skipped: {e}")

    if _embedder is not None:
        return
    if _warm_thread and _warm_thread.is_alive():
        return

    _warm_thread = threading.Thread(target=_warm, daemon=True)
    _warm_thread.start()


def add_memory(text: str, category: str = "general", metadata: Optional[dict] = None) -> str:
    """Store a memory entry."""
    _init()

    entry = {
        "text": text,
        "category": category,
        "timestamp": time.time(),
        "metadata": metadata or {},
    }
    _entries.append(entry)

    if _USE_FAISS and _embedder is not None and _index is not None:
        vec = _embedder.encode([text], normalize_embeddings=True)
        _index.add(np.array(vec, dtype=np.float32))

    _save()
    return f"Memory stored ({category}): {text[:80]}..."


def search_memory(query: str, top_k: int = 5) -> list[dict]:
    """Search memory for relevant past entries."""
    _init(allow_heavy=False)

    if not _entries:
        return []

    if _USE_FAISS and _embedder is not None and _index is not None and _index.ntotal > 0:
        return _faiss_search(query, top_k)
    if _embedder is not None:
        return _embedding_search(query, top_k)
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
    texts = [entry["text"] for entry in _entries]
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

    scored.sort(key=lambda item: item[0], reverse=True)
    results = []
    for score, entry in scored[:top_k]:
        result = dict(entry)
        result["score"] = score
        results.append(result)
    return results


def get_relevant_context(query: str, top_k: int = 3) -> str:
    """Get formatted memory context for agent prompts."""
    results = search_memory(query, top_k)
    if not results:
        return ""

    lines = ["## Relevant Past Memories:"]
    for result in results:
        category = result.get("category", "general")
        text = result["text"][:300]
        lines.append(f"- [{category}] {text}")
    return "\n".join(lines)
