"""
conftest.py — SQA Automation learning path
==========================================
Shared fixtures and pytest configuration for all levels.

The collect_ignore list excludes files that are not pytest tests:
- Locust load test scripts (run with `locust -f ...`)
- k6 JavaScript scripts
- Feature files (handled by pytest-bdd scenarios() calls)
"""

import sys
from pathlib import Path

# Ensure each level's python/ directory is on sys.path so that
# relative imports and fixtures work correctly.
collect_ignore_glob = [
    "*/02_performance_locust.py",   # Locust script — run with `locust` CLI
    "*/k6_script.js",               # k6 script — run with `k6 run`
]
