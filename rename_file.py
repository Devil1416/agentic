import os

root = r"d:\n1ggaman\agentic"
agentic_self = os.path.join(root, "AGENTIC_SELF.md")
reflexion_self = os.path.join(root, "REFLEXION_SELF.md")
niggativity_self = os.path.join(root, "NIGGATIVITY_SELF.md")

if os.path.exists(agentic_self):
    os.rename(agentic_self, reflexion_self)
    print("Renamed AGENTIC_SELF.md to REFLEXION_SELF.md")

if os.path.exists(niggativity_self):
    os.remove(niggativity_self)
    print("Removed NIGGATIVITY_SELF.md")
