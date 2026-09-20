"""InsightEngine package root alias."""

import sys
from pathlib import Path

# Add project root to sys.path so both `from app...` and `from insightengine.app...` resolve
root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))
