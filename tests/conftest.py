import sys
import os

# Add the project root directory (the parent of tests) to the sys.path.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print(project_root)
if project_root not in sys.path:
    sys.path.insert(0, project_root)