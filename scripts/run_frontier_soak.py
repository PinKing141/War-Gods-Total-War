"""Run a deterministic activated-frontier soak simulation."""

from __future__ import annotations

import argparse
import json
import logging
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from warfare_simulation.app import WarfareSimulationApp  # noqa: E402


CONFIG_DIR = ROOT / "src" / "warfare_simulation" / "config" / "data"
DEFAULT_DB_PATH = ROOT / "frontier_soak.db"
DEFAULT_WORKBOOK_PATH = ROOT / "frontier_soak.xlsx"


@dataclass(frozen=True)
class FrontierSoakMetrics:
    """Summary metrics from one frontier soak run."""

    seed: int
    years_simulated: int
    months_simulated: int
    factions: int
    wars_started: int
    raids: int
    claims_pressed: int
    rejected_intents: int
    province_damage_events: int
    mage_events: int
    treaty_crises: int
    major_deaths: int
    historical_actions: int
    chronicle_entries: int
    workbook_exported: bool
    db_path: Path
    workbook_path: Path | None = None

    def lines(self) -> list[str]:
        workbook_status = "yes" if self.workbook_exported else "no"
        if self.workbook_exported and self.workbook_path is not None:
            workbook_status = f"yes ({self.workbook_path})"
        return [
            f"Seed: {self.seed}",
            f"Years simulated: {self.years_simulated}",
            f"Months simulated: {self.months_simulated}",
            f"Factions: {self.factions}",
            f"Wars started: {self.wars_started}",
            f"Raids: {self.raids}",
            f"Claims pressed: {self.claims_pressed}",
            f"Rejected intents: {self.rejected_intents}",
            f"Province damage events: {self.province_damage_events}",
            f"Mage events: {self.mage_events}",
            f"Treaty crises: {self.treaty_crises}",
            f"Major deaths: {self.major_deaths}",
            f"Historical actions: {self.historical_actions}",
            f"Chronicle entries: {self.chronicle_entries}",
            f"Workbook exported: {workbook_status}",
            f"Database: {self.db_path}",
        ]

    def print(self) -> None:
        for line in self.lines():
            print(line)


def run_frontier_soak(
    *,
    years: int = 10,
    seed: int = 123,
    db_path: str | Path = DEFAULT_DB_PATH,
    workbook_path: str | Path | None = DEFAULT_WORKBOOK_PATH,
    export_workbook: bool = True,
    reset: bool = True,
    verbose: bool = False,
) -> FrontierSoakMetrics:
    """Run the activated seed frontier for N years and return measured metrics."""
    if years < 1:
        raise ValueError("years must be at least 1")

    _set_logging_level(logging.INFO if verbose else logging.WARNING)
    random.seed(seed)
    db_path = Path(db_path)
    workbook = Path(workbook_path) if workbook_path is not None else None

    if reset and db_path.exists():
        db_path.unlink()
    if reset and workbook is not None and workbook.exists():
        workbook.unlink()

    app = WarfareSimulationApp(
        config_path=CONFIG_DIR,
        db_path=db_path,
        activate_seed_frontier=True,
    )
    months = years * 12
    for _ in range(months):
        app.campaign.advance_turn()

    exported = False
    if export_workbook and workbook is not None:
        app.export_campaign(workbook)
        exported = workbook.exists()

    metrics = collect_metrics(
        app,
        seed=seed,
        years=years,
        months=months,
        db_path=db_path,
        workbook_path=workbook if exported else None,
        workbook_exported=exported,
    )
    app.db_mgr.close()
    return metrics


def collect_metrics(
    app: WarfareSimulationApp,
    *,
    seed: int,
    years: int,
    months: int,
    db_path: Path,
    workbook_path: Path | None,
    workbook_exported: bool,
) -> FrontierSoakMetrics:
    """Collect soak metrics from the runtime database and hydrated logs."""
    db = app.db_mgr
    historical_payloads = _historical_loop_payloads(db)
    accepted_payloads = [
        payload for payload in historical_payloads if payload["action"].get("accepted")
    ]
    action_types = [payload["action"].get("action_type", "") for payload in accepted_payloads]
    event_rows = db.execute(
        "SELECT source_system, description, effect_summary FROM event"
    ).fetchall()

    factions = db.execute(
        "SELECT COUNT(*) FROM faction WHERE seed_faction_id IS NOT NULL"
    ).fetchone()[0]
    chronicle_entries = db.execute("SELECT COUNT(*) FROM observer_log").fetchone()[0]

    return FrontierSoakMetrics(
        seed=seed,
        years_simulated=years,
        months_simulated=months,
        factions=factions,
        wars_started=sum(1 for action in action_types if action == "declare_war"),
        raids=sum(1 for action in action_types if "raid" in action),
        claims_pressed=sum(1 for action in action_types if "claim" in action),
        rejected_intents=sum(
            1
            for payload in historical_payloads
            if not payload["validation"].get("accepted", False)
        ),
        province_damage_events=sum(1 for action in action_types if action in {"raid_border", "siege"}),
        mage_events=sum(
            1
            for source_system, description, effect_summary in event_rows
            if source_system.startswith("Mage")
            or _contains_word(f"{description} {effect_summary}", "mage")
        ),
        treaty_crises=sum(
            1
            for action in action_types
            if action in {"demand_recognition", "enforce_contract", "refuse_tax"}
        ),
        major_deaths=sum(
            1
            for source_system, description, effect_summary in event_rows
            if any(
                token in f"{source_system} {description} {effect_summary}".lower()
                for token in ("death", "died", "killed", "succession")
            )
        ),
        historical_actions=len(historical_payloads),
        chronicle_entries=chronicle_entries,
        workbook_exported=workbook_exported,
        db_path=db_path,
        workbook_path=workbook_path,
    )


def _historical_loop_payloads(db: Any) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT new_value
        FROM audit_log
        WHERE system = ?
        ORDER BY id
        """,
        ("HistoricalLoop",),
    ).fetchall()
    payloads: list[dict[str, Any]] = []
    for (raw_payload,) in rows:
        if not raw_payload:
            continue
        payload = json.loads(raw_payload)
        if isinstance(payload, dict):
            payloads.append(payload)
    return payloads


def _contains_word(text: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word)}\b", text, flags=re.IGNORECASE) is not None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", type=int, default=10)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--workbook-path", type=Path, default=DEFAULT_WORKBOOK_PATH)
    parser.add_argument(
        "--no-workbook",
        action="store_true",
        help="Skip workbook export after the soak run.",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Do not delete an existing DB/workbook before running.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show engine INFO logs before the metrics summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    metrics = run_frontier_soak(
        years=args.years,
        seed=args.seed,
        db_path=args.db_path,
        workbook_path=args.workbook_path,
        export_workbook=not args.no_workbook,
        reset=not args.keep_existing,
        verbose=args.verbose,
    )
    metrics.print()


def _set_logging_level(level: int) -> None:
    logger = logging.getLogger("warfare_simulation")
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)


if __name__ == "__main__":
    main()
