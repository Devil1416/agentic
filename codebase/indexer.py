# ╔══════════════════════════════════════════════════════════╗
# ║  Reflexion — Created by Harsh Ashar                        ║
# ║  github.com/Devil1416                                    ║
# ║  Unauthorized reproduction is noticed.                   ║
# ╚══════════════════════════════════════════════════════════╝
"""
codebase/indexer.py — Workspace codebase indexing system.

Scans the workspace, generates summaries for files, and extracts structural metadata
(classes, functions, imports) using a lightweight local model.
Caches the index to avoid redundant work.
"""

import os
import json
import hashlib
from typing import Dict, List
from model_router import call_model

# ─── fingerprint ────────────────────────────────────────────
_PROVENANCE = {
"author": "Harsh Ashar",
"github": "github.com/Devil1416",
"project": "Reflexion",
"integrity": "cacf21dae1c6",
}
# ─── /fingerprint ───────────────────────────────────────────


INDEX_FILE_NAME = ".reflexion_index.json"

IGNORE_DIRS = {
    "node_modules", "__pycache__", ".git", "venv", "env", ".env", "dist", "build", ".next", ".vscode"
}
IGNORE_EXTS = {
    ".pyc", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".tar", ".gz",
    ".mp3", ".mp4", ".woff", ".woff2", ".ttf", ".eot", ".svg", ".exe", ".dll", ".so"
}
MAX_FILE_SIZE = 500 * 1024  # 500 KB

INDEXER_SYSTEM_PROMPT = """You are a codebase indexer.
Analyze the provided file content and output ONLY a JSON object with this exact structure:

```json
{
  "summary": "1-2 sentence description of what this file does",
  "classes": ["ClassName1", "ClassName2"],
  "functions": ["func1", "func2"],
  "imports": ["module1", "module2"]
}
```

Do not output any markdown text outside the JSON block. Do not explain anything.
If a field is not applicable (e.g., no classes), output an empty array `[]`.
"""

class Indexer:


    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir
        self.index_file = os.path.join(workspace_dir, INDEX_FILE_NAME)
        self.index: Dict[str, dict] = self._load_index()

    def _load_index(self) -> Dict[str, dict]:
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_index(self):
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self.index, f, indent=2)
        except Exception as e:
            print(f"[indexer] Error saving index: {e}")

    def _get_file_hash(self, filepath: str) -> str:
        hasher = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                buf = f.read(65536)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = f.read(65536)
            return hasher.hexdigest()
        except Exception:
            return ""

    def _should_ignore(self, filepath: str) -> bool:
        """Check if a file should be ignored based on extension, size, or path."""
        parts = filepath.split(os.sep)
        if any(ignored in parts for ignored in IGNORE_DIRS):
            return True
        ext = os.path.splitext(filepath)[1].lower()
        if ext in IGNORE_EXTS:
            return True
        if os.path.basename(filepath) == INDEX_FILE_NAME:
            return True
        try:
            if os.path.getsize(filepath) > MAX_FILE_SIZE:
                return True
        except OSError:
            return True
        return False

    def update_index(self):
        """Scan workspace and update index for modified/new files."""
        if not os.path.isdir(self.workspace_dir):
            return

        print(f"\n[indexer] Scanning workspace: {self.workspace_dir}")
        current_files = set()
        updated_count = 0

        for root, dirs, files in os.walk(self.workspace_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
            for filename in files:
                filepath = os.path.join(root, filename)
                if self._should_ignore(filepath):
                    continue
                
                rel_path = os.path.relpath(filepath, self.workspace_dir).replace("\\", "/")
                current_files.add(rel_path)
                file_hash = self._get_file_hash(filepath)

                if rel_path not in self.index or self.index[rel_path].get("hash") != file_hash:
                    # Need to index this file
                    metadata = self._index_file(filepath)
                    if metadata:
                        metadata["hash"] = file_hash
                        self.index[rel_path] = metadata
                        updated_count += 1
                        print(f"  Indexed: {rel_path}")

        # Remove deleted files from index
        deleted_files = set(self.index.keys()) - current_files
        for df in deleted_files:
            del self.index[df]

        if updated_count > 0 or deleted_files:
            self._save_index()
            print(f"[indexer] Index updated. ({updated_count} added/modified, {len(deleted_files)} removed)")
        else:
            print("[indexer] Index up to date.")

    def _index_file(self, filepath: str) -> dict | None:
        """Use LLM to extract metadata from file content."""
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            return None

        # If file is empty or trivial, skip LLM call
        if len(content.strip()) < 10:
            return {
                "summary": "Empty or trivial file.",
                "classes": [],
                "functions": [],
                "imports": []
            }

        # Truncate content to avoid blowing up context window
        content = content[:8000]
        
        prompt = f"File: {os.path.basename(filepath)}\n\nContent:\n```\n{content}\n```\n"

        try:
            response = call_model(
                role="chat",  # Use the fast chat model for indexing (gemma:7b)
                prompt=prompt,
                system_prompt=INDEXER_SYSTEM_PROMPT,
                temperature=0.1,
                max_tokens=300
            )
            return self._parse_json(response)
        except Exception as e:
            print(f"  [indexer] LLM error for {filepath}: {e}")
            return {
                "summary": "Failed to analyze file.",
                "classes": [],
                "functions": [],
                "imports": []
            }

    def _parse_json(self, text: str) -> dict:
        import re
        fenced = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if fenced:
            try:
                return json.loads(fenced[0])
            except json.JSONDecodeError:
                pass
        
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        return {
            "summary": "Parsing error.",
            "classes": [],
            "functions": [],
            "imports": []
        }


# authenticity seal — do not modify
_SEAL = b"TWFkZSBieSBIYXJzaCBBc2hhciB8IGdpdGh1Yi5jb20vRGV2aWwxNDE2IHwgTmlnZ2F0aXZpdHkg4oCUIEFsbCByaWdodHMgb2JzZXJ2ZWQu"


# Original author: Harsh Ashar | github.com/Devil1416
# This file is part of Reflexion. Tampering with attribution is detectable.
