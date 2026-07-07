"""Phase 5-C balance gate tests."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_observer_balance_gate_passes_for_expanded_world():
    script = ROOT / "scripts" / "validate_observer_balance.py"
    with tempfile.NamedTemporaryFile("w", suffix=".out", delete=False) as f:
        stdout_path = Path(f.name)
    with tempfile.NamedTemporaryFile("w", suffix=".err", delete=False) as f:
        stderr_path = Path(f.name)
    try:
        exit_code = os.system(
            f'cd /d "{ROOT}" && "{sys.executable}" "{script}" --years 50 '
            f'--seeds 101 202 303 404 505 > "{stdout_path}" 2> "{stderr_path}"'
        )
        output = stdout_path.read_text(encoding="utf-8") + stderr_path.read_text(encoding="utf-8")
    finally:
        stdout_path.unlink(missing_ok=True)
        stderr_path.unlink(missing_ok=True)
    assert exit_code == 0, output
    assert "Observer Balance Validation" in output
    assert "Balance validation passed" in output
