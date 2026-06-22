"""Compatibility wrapper for the dashboard launcher.

Preferred entrypoint:
    python scripts/run_ui.py
Legacy entrypoint retained:
    python run_ui.py
"""

from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(Path(__file__).parent / "scripts" / "run_ui.py", run_name="__main__")
