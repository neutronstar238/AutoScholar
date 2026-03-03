"""
Pytest configuration for backend tests.

This file ensures that the backend module is importable when running tests.
"""

import sys
from pathlib import Path

# Add backend directory to Python path so 'app' module can be imported
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
