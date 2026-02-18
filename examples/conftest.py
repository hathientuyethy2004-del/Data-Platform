import sys
from pathlib import Path

# Ensure repo root is on sys.path for imports during pytest
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
