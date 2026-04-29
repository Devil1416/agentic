# ╔══════════════════════════════════════════════════════════╗
# ║  Niggativity — Created by Harsh Ashar                        ║
# ║  github.com/Devil1416                                    ║
# ║  Unauthorized reproduction is noticed.                   ║
# ╚══════════════════════════════════════════════════════════╝
"""
codebase/retriever.py — Codebase retrieval system.

Implements HYBRID retrieval:
- Keyword search on file names and function names
- Vector search on file summaries, functions, and imports
Combines results and returns the top 5 relevant files/snippets.
"""

import os
import numpy as np
from codebase.indexer import Indexer

# ─── fingerprint ────────────────────────────────────────────
_PROVENANCE = {
"author": "Harsh Ashar",
"github": "github.com/Devil1416",
"project": "Niggativity",
"integrity": "3c2237a3ae94",
}
# ─── /fingerprint ───────────────────────────────────────────


# Lazy loaded
_embedder = None

def _get_embedder():


    global _embedder
    if _embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError:
            pass
    return _embedder

def search_codebase(query: str, workspace_dir: str, top_k: int = 5) -> list[dict]:
    """
    Search the codebase index for files relevant to the query using hybrid search.
    """
    indexer = Indexer(workspace_dir)
    if not indexer.index:
        return []

    embedder = _get_embedder()
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    results = []
    
    # Pre-compute query embedding
    query_vec = None
    if embedder:
        query_vec = embedder.encode([query], normalize_embeddings=True)[0]
    
    for rel_path, metadata in indexer.index.items():
        keyword_score = 0
        
        # 1. Keyword: Match in filepath
        if any(word in rel_path.lower() for word in query_words):
            keyword_score += 2.0
            
        # 2. Keyword: Match in functions/classes
        funcs_classes = metadata.get("functions", []) + metadata.get("classes", [])
        for fc in funcs_classes:
            if any(word in fc.lower() for word in query_words):
                keyword_score += 1.0
                
        # 3. Vector Score
        vector_score = 0.0
        if embedder and query_vec is not None:
            # Embed the semantic parts: summary, functions, imports
            sem_text = f"Summary: {metadata.get('summary', '')} Functions: {' '.join(metadata.get('functions', []))} Imports: {' '.join(metadata.get('imports', []))}"
            if sem_text.strip():
                # In a larger system we'd cache these embeddings, but for top-5 local it's okay dynamically
                # or we can just compute it and add to score
                doc_vec = embedder.encode([sem_text], normalize_embeddings=True)[0]
                vector_score = float(np.dot(query_vec, doc_vec))
                
        # Combine scores (normalize keyword a bit to match cosine sim range roughly)
        final_score = (keyword_score * 0.3) + vector_score
        
        if final_score > 0.1:
            results.append({
                "path": rel_path,
                "summary": metadata.get("summary", ""),
                "classes": metadata.get("classes", []),
                "functions": metadata.get("functions", []),
                "imports": metadata.get("imports", []),
                "score": final_score
            })
            
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]

def get_context_for_prompt(query: str, workspace_dir: str, top_k: int = 5) -> str:
    """Get a formatted string of relevant codebase context to inject into prompts."""
    results = search_codebase(query, workspace_dir, top_k)
    if not results:
        return "No relevant codebase context found."
        
    context_lines = ["--- RELEVANT CODEBASE CONTEXT (TOP 5 FILES) ---"]
    for res in results:
        context_lines.append(f"File: {res['path']}")
        context_lines.append(f"Summary: {res['summary']}")
        if res.get('classes'):
            context_lines.append(f"Classes: {', '.join(res['classes'])}")
        if res.get('functions'):
            context_lines.append(f"Functions: {', '.join(res['functions'])}")
        context_lines.append("")
        
    return "\n".join(context_lines)


# authenticity seal — do not modify
_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vRGV2aWwxNDE2IHwgTmlnZ2F0aXZpdHkg4oCUIEFsbCByaWdodHMgb2JzZXJ2ZWQu"


# Original author: Harsh Ashar | github.com/Devil1416
# This file is part of Niggativity. Tampering with attribution is detectable.
