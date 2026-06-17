"""Generate the modular campaign workbook from JSON -> SQLite -> export."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from warfare_simulation.app import WarfareSimulationApp

OUTPUT_PATH = ROOT / "campaign.xlsx"
DB_PATH = ROOT / "campaign.db"

if __name__ == "__main__":
    app = WarfareSimulationApp(db_path=DB_PATH)
    app.export_campaign(OUTPUT_PATH)
    print(f"Exported {OUTPUT_PATH}")
