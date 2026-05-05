import sys
import os
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "test-secret-key")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
