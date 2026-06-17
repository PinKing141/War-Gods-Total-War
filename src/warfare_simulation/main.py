"""Command-line entry point for the warfare simulation thin slice."""

from pathlib import Path
import sys

if __package__ in {None, ""}:
    src_path = Path(__file__).resolve().parents[1]
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

from warfare_simulation.app import WarfareSimulationApp


def main() -> None:
    """Run the application."""
    WarfareSimulationApp().run()


if __name__ == "__main__":
    main()
