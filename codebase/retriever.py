# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                        ║
# ║  github.com/doriangraypng                                    ║
# ║  Unauthorized reproduction is noticed.                   ║
# ╚══════════════════════════════════════════════════════════╝
"""
codebase/retriever.py — Codebase retrieval system.

Implements HYBRID retrieval:
- Keyword search on file names and function names
- Vector search on file summaries, functions, and imports
Combines results and returns the top 5 relevant files/snippets.
"""

import json
import os
import numpy as np
from codebase.indexer import Indexer

# ─── fingerprint ────────────────────────────────────────────
_PROVENANCE = {
"author": "Harsh Ashar",
"github": "github.com/doriangraypng",
"project": "Reflexion",
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


def get_tree_context(workspace_dir: str, max_files: int = 30) -> str:
    """Read codebase structure from the Graphify index (.reflexion_index.json)
    and return a compact dependency-graph representation.

    This is the PRIMARY context source for planners and builders.
    It avoids re-scanning or embedding full source files, reading only
    pre-computed structural metadata (classes, functions, imports) from
    the cached index.  Token usage is minimised while maintaining full
    codebase awareness.

    Returns a formatted string suitable for injection into LLM prompts.
    """
    from codebase.indexer import INDEX_FILE_NAME
    index_path = os.path.join(workspace_dir, INDEX_FILE_NAME)

    # Try loading the cached index directly (fast path)
    index_data: dict = {}
    if os.path.exists(index_path):
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                index_data = json.load(f)
        except Exception:
            pass

    # If no cached index, build one quickly
    if not index_data:
        try:
            indexer = Indexer(workspace_dir)
            indexer.update_index()
            index_data = indexer.index
        except Exception:
            return "No codebase index available."

    if not index_data:
        return "Empty codebase — no files indexed."

    # Build compact structural representation
    lines = ["--- CODEBASE STRUCTURE (Graphify Index) ---"]
    lines.append(f"Total files indexed: {len(index_data)}")
    lines.append("")

    # Build dependency edges:  file → imports
    dep_graph: dict[str, list[str]] = {}
    all_modules: dict[str, str] = {}  # module_name → file_path

    for rel_path, meta in list(index_data.items())[:max_files]:
        # Register module name from filename
        basename = os.path.splitext(os.path.basename(rel_path))[0]
        all_modules[basename] = rel_path

    for rel_path, meta in list(index_data.items())[:max_files]:
        imports = meta.get("imports", [])
        local_deps = []
        for imp in imports:
            imp_base = imp.split(".")[0]
            if imp_base in all_modules and all_modules[imp_base] != rel_path:
                local_deps.append(all_modules[imp_base])
        dep_graph[rel_path] = local_deps

        # Compact per-file summary
        summary = meta.get("summary", "")
        classes = meta.get("classes", [])
        functions = meta.get("functions", [])
        imports_list = meta.get("imports", [])

        lines.append(f"## {rel_path}")
        if summary:
            lines.append(f"  Summary: {summary}")
        if classes:
            lines.append(f"  Classes: {', '.join(classes)}")
        if functions:
            lines.append(f"  Functions: {', '.join(functions[:10])}{'...' if len(functions) > 10 else ''}")
        if local_deps:
            lines.append(f"  Local deps: {', '.join(local_deps)}")
        if imports_list:
            external = [i for i in imports_list if i.split('.')[0] not in all_modules]
            if external:
                lines.append(f"  External imports: {', '.join(external[:8])}")
        lines.append("")

    # Dependency graph summary
    if dep_graph:
        lines.append("--- DEPENDENCY GRAPH ---")
        for src, deps in dep_graph.items():
            if deps:
                lines.append(f"  {src} → {', '.join(deps)}")
        lines.append("")

    return "\n".join(lines)


# authenticity seal — do not modify
_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vRGV2aWwxNDE2IHwgTmlnZ2F0aXZpdHkg4oCUIEFsbCByaWdodHMgb2JzZXJ2ZWQu"


# Original author: Harsh Ashar | github.com/doriangraypng
# This file is part of Reflexion. Tampering with attribution is detectable.
