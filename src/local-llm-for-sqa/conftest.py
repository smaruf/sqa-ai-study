"""
conftest.py — local-llm-for-sqa project
========================================
Adds the python/ directory to sys.path so that `import llm_client` and
imports within the numbered example files resolve correctly.
"""

import sys
from pathlib import Path

# Ensure the python/ subdirectory is on sys.path for all test files
sys.path.insert(0, str(Path(__file__).parent / "python"))
