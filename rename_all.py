import os
import re

ROOT = r"d:\n1ggaman\reflexion"

def process_directory(directory):
    for root, dirs, files in os.walk(directory):
        # Skip node_modules, .git, __pycache__, workspace
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__", "workspace", "venv", ".gemini")]
        
        for file in files:
            if file.endswith((".py", ".js", ".html", ".css", ".json", ".md")):
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Find and replace "Reflexion" and "Reflexion" (case-insensitive for general use)
                    # But maintain casing if possible. For simplicity, we can do explicit replacements:
                    
                    new_content = content
                    
                    # Exact matches to preserve case exactly where known
                    new_content = new_content.replace("Reflexion", "Reflexion")
                    new_content = new_content.replace("reflexion", "reflexion")
                    new_content = new_content.replace("REFLEXION", "REFLEXION")
                    
                    new_content = new_content.replace("Reflexion", "Reflexion")
                    new_content = new_content.replace("reflexion", "reflexion")
                    new_content = new_content.replace("REFLEXION", "REFLEXION")
                    
                    if new_content != content:
                        with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
                            f.write(new_content)
                        print(f"Updated {filepath}")
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")

if __name__ == "__main__":
    process_directory(ROOT)
