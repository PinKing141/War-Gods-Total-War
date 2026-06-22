"""Launch the War Gods campaign dashboard.

Run from the project root:
    python run_ui.py
"""
import sys
from pathlib import Path

# Put src/ and the project root on the import path
_ROOT = Path(__file__).parent
for _p in (_ROOT / "src", _ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from warfare_simulation.ui.app import run  # noqa: E402

if __name__ == "__main__":
    run()
