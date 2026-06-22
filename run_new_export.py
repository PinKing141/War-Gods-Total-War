"""Compatibility wrapper for workbook export.

Preferred entrypoint:
    python scripts/run_export.py
Legacy entrypoint retained:
    python run_new_export.py
"""

from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(Path(__file__).parent / "scripts" / "run_export.py", run_name="__main__")
