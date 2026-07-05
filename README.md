# Warfare Simulation Campaign Engine

A **production-grade, domain-driven campaign engine** for medieval warfare simulation.

> **Status**: Phases 1–10 Complete ✓ | Living Chronicle Phase 9 (Content expansion and balance) — Seed content pack and balance health ✓

## Quick Start

### Prerequisites
- Python 3.10 or later
- pip

### Installation
```bash
# Clone the repository
cd "Warfare Simulation"

# Install dependencies
pip install -r requirements.txt
```

### Run Campaign Engine
```bash
python src/warfare_simulation/main.py
```


### Web Observer — The Frontier Chronicle (GitHub Pages)

A fully static, CK-style observer world lives in [`docs/`](docs/): a painted
political map of the Rov Basin frontier where the eight seed factions wage
wars, besiege fortresses, sign peaces, die, and crown heirs entirely on their
own. There is no player — you can only watch, pan, zoom, and read.

Run it locally (no build step needed):
```bash
# either open docs/index.html directly in a browser, or:
python -m http.server 8000   # then visit http://localhost:8000 or /docs/
```

Publish it with GitHub Pages:
1. Push this repository to GitHub (the app is already in `docs/`).
2. On GitHub: **Settings → Pages → Build and deployment**.
3. Set **Source** to *Deploy from a branch*, pick your branch, and select
   the **`/docs`** folder. Save.
4. Your world goes live at `https://<user>.github.io/<repo>/` a minute later.

The world is seeded from the lore CSVs. After editing them, regenerate the
web seed with:
```bash
python scripts/export_web_seed.py
```

### Export Workbook Directly
```bash
python scripts/run_export.py
```

This will:
1. Initialize the campaign from JSON configs
2. Create/populate SQLite database
3. Generate `Auster_Campaign_Engine.xlsx` spreadsheet
4. Display campaign status

## Architecture Overview

The engine uses **Domain-Driven Design** with clear separation of concerns:

```
Application Layer (app.py, main.py)
    ↓
Orchestration Layer (CampaignOrchestrator, GameState)
    ↓
Domain Layer (Kingdom, Military, Geography, Diplomacy, Logistics, Events)
    ↓
Persistence Layer (Repositories, SQLite)
    ↓
Export Layer (SheetGenerators, WorkbookFactory)
```

### Key Concepts

1. **Domains**: Each game system is isolated
   - `kingdom/` — Treasury, morale, turn advancement
   - `military/` — Units, commanders, tactics
   - `geography/` — Provinces, borders, resources
   - `diplomacy/` — Factions, relations, spies
   - `logistics/` — Resources, projects, supply routes
   - `events/` — Campaign events and logging

2. **Data Management**
   - **JSON Configs**: Campaign definitions (human-editable)
   - **SQLite Database**: Runtime state (queryable, persistent)

3. **Validation Strategy** (3-tier)
   - **Tier 1** (Load): Pydantic validates JSON schema
   - **Tier 2** (Runtime): `ValidationService` checks invariants before mutations
   - **Tier 3** (Orchestration): `CampaignOrchestrator` validates entire state

4. **Extensibility**
   - Add new domains without touching existing code
   - Placeholder interfaces for future systems (Combat, etc.)

## Project Structure

```
docs/
├── roadmaps/            # Ordered planning docs and build sequence
├── ARCHITECTURE.md      # Architecture overview
├── API.md               # Public API reference
├── EXTENDING.md         # System extension guide
└── RULES_FRAMEWORK.md   # Observer-sim rules contract

scripts/                 # Preferred runnable entrypoints
src/warfare_simulation/
├── core/              # Shared abstractions (base classes, constants, exceptions)
├── config/            # Configuration management & JSON data files
├── domain/            # Business logic (6 domains)
├── persistence/       # Database layer (repositories, SQLite)
├── export/            # Spreadsheet generation
├── orchestration/     # Campaign coordination
├── app.py             # Main application
└── main.py            # CLI entry point

tests/                 # Unit & integration tests
```

## Roadmap

See [docs/roadmaps/README.md](docs/roadmaps/README.md) for the roadmap reading order. Current focus: **Living Chronicle Phase 9 — Content expansion and balance** (initial seed content pack and non-mutating balance health report complete; long-run tuning remains future work).

### ✓ Phase 1: Foundation (Complete)
- [x] Package structure
- [x] Abstract base classes
- [x] Constants and enums
- [x] Exception hierarchy
- [x] Centralized logging
- [x] Validation service

### ✓ Phase 2: Domain Implementation (Complete)
- [x] Kingdom models, repository, service
- [x] Geography models, repository, service
- [x] Military models, repository, service
- [x] Diplomacy models, repository, service
- [x] Logistics models, repository, service
- [x] Events models, repository, service

### ✓ Phase 3: Data & Persistence (Complete)
- [x] JSON config files
- [x] Pydantic schemas
- [x] SQLite database & schema
- [x] Generic repository pattern
- [x] `CampaignBootstrap` — JSON → SQLite seeding + repo hydration
- [x] `test_phase3_persistence.py` (config, DB, migrations, seeding)

**Verify locally**: `pip install -r requirements.txt` then `PYTHONPATH=src python test_phase3_persistence.py`

### ✓ Phase 4: Spreadsheet Export (Complete)
- [x] `tests/test_export_parity.py` (integration test first)
- [x] Style manager
- [x] Sheet generators (8 sheets)
- [x] Workbook factory
- [x] Excel output parity with monolith

### ✓ Phase 5: Application Layer (Thin Slice) (Complete)
- [x] Minimal app: load config → seed DB → export
- [x] Export-only orchestrator stub
- [x] Stub `GameState` with current turn tracking
- [x] CLI entry point (`main.py`)
- Turn simulation deferred to post–Phase 6

### ✓ Phase 6: Verification & Docs (Complete)
- [x] Domain tests (`test_phase2_domains.py`)
- [x] Persistence tests (`test_phase3_persistence.py`)
- [x] Full export parity test (cell-level)
- [x] Deprecate `campaign_engine_initialiser.py` as golden reference before removal
- [x] Architecture documentation
- [x] Extension examples

### ✓ Phase 7: Runtime State (Complete)
- [x] `CampaignOrchestrator.advance_turn()` updates campaign clock
- [x] Kingdom economy applies monthly net income
- [x] Logistics resources apply monthly net production
- [x] `GameState` save/load checkpoints
- [x] Persist advanced turn state back to SQLite

### ✓ Phase 8: Observer Calendar (Complete)
- [x] Canonical `SimDate` calendar model
- [x] Day/month/year advancement and `DD/MM/YYYY` formatting
- [x] Dashboard pause/resume plus `1x`, `2x`, `5x`, and `fast` speed controls
- [x] Checkpoint round-trip for date and simulation speed

### ✓ Phase 9: Pulse Scheduler (Complete)
- [x] Add daily, weekly, monthly, seasonal, and yearly pulse boundaries
- [x] Prevent duplicate system execution at pulse boundaries
- [x] Preserve monthly economy/logistics totals through daily progression

### ✓ Phase 10: Observer Logs and Causality Backbone
- [x] Add structured event metadata for date, actor, target, source system, cause chain, and effect summary
- [x] Persist and rehydrate event metadata through SQLite
- [x] Surface observer-readable causal details in the Event Log export without breaking legacy workbook shape
- [x] Add dedicated logs for economics, diplomacy, construction, conflict, and random resolution
- [x] Add summary generators for daily/weekly/monthly observer output
- [x] Update dashboard event feed for long-run readability


### ✓ Living Chronicle Phase 1A: Autonomous Faction Intent Skeleton
- [x] Evaluate monthly faction pressure from stability, wealth, military power, and hostile relations
- [x] Generate deterministic autonomous strategic intents
- [x] Validate intents before mutation hooks are allowed
- [x] Record faction-intent events, audits, and diplomacy observer logs
- [x] Include faction-intent notes in monthly observer summaries

### Living Chronicle Phase 1B: Chronicle Summary Surfaces
- [x] Generate observer-facing yearly chronicle summaries from event, audit, and observer-log streams
- [x] Expose daily, weekly, monthly, and yearly summary cards through the campaign service
- [x] Verify a 12-month unattended run produces an auditable yearly chronicle

### Living Chronicle Phase 2A: Scheduled Event Queue
- [x] Add deterministic day-level scheduled events with due date, actor, target, type, payload, and status
- [x] Resolve due scheduled events once per in-world day after pulse hooks
- [x] Checkpoint and restore scheduler queue state for pending and completed events
- [x] Persist scheduled events to SQLite for long-running campaign reloads
- [x] Resolve army arrival, spy mission, harvest, and monthly report events on distinct in-month days

### ✓ Living Chronicle Phase 9A: Balance Health Report
- Added a non-mutating balance analyzer for soak-test plausibility checks.
- Added a UI/service-facing health report that counts factions, provinces, events, and impossible-state warnings.
- Added coverage for 100-year balance-report warnings before larger content packs are introduced.

### ✓ Living Chronicle Phase 9B: Seed Content Pack
- [x] Expanded the default observer scenario from 3 to 5 factions with additional border and trade powers
- [x] Expanded the province map from 4 to 6 provinces with frontier and harbor pressure points
- [x] Added matching commanders and army units so the richer seed can be inspected immediately
- [x] Verified expanded seed content remains within current balance-health invariants.

### ✓ Living Chronicle Phase 7A: Historian Account Skeleton
- [x] Generate master-truth, public, faction, and later-historian accounts from a canonical event
- [x] Track account confidence, rumor state, age, cited events, cited observer logs, and contradiction notes
- [x] Verify differing accounts stay tied to the same hidden truth event

## Usage Examples

### Import Core Abstractions
```python
from src.warfare_simulation.core import (
    GameEntity, GameSystem, ValidationService,
    UnitType, InvalidCampaignStateError
)

# Use enums
unit_type = UnitType.HEAVY_SPEARMEN
print(unit_type.value)  # "Heavy Spearmen"

# Use validation
validator = ValidationService()
validator.validate_percent_value(75, "morale")  # ✓ Valid
```

### Extend with New Domain (Coming in Phase 2)
```python
from src.warfare_simulation.core import GameSystem

class CombatService(GameSystem):
    def __init__(self):
        super().__init__("Combat")
    
    def initialize(self):
        print("Combat system initialized")
    
    def advance_turn(self, turn_number):
        # Implement combat logic
        pass
    
    def validate_state(self):
        return []  # No errors
```

## Development

### Run Tests
```bash
pytest tests/
```

### Code Style
```bash
# Format code
black src/

# Sort imports
isort src/

# Lint
flake8 src/
```

### ✓ Living Chronicle Phase 4: Logistics and Movement v1
- [x] Group units into auditable army movement orders
- [x] Advance route progress by day with weather and road modifiers
- [x] Track supply endurance through supplied/strained/hungry/starving shortage levels
- [x] Surface contact detection while marching and allow starving armies in bad weather to turn back

## Documentation

- [docs/roadmaps/UNIFIED_ROADMAP.md](docs/roadmaps/UNIFIED_ROADMAP.md) — **Canonical roadmap.** Merges the technical, product, and content roadmaps under the Prime Law of conservation ("nothing appears without its inputs") and the character-founded-kingdoms vision
- [docs/roadmaps/README.md](docs/roadmaps/README.md) — Linear roadmap reading order and execution priority
- [docs/roadmaps/MODULARIZATION_ROADMAP.md](docs/roadmaps/MODULARIZATION_ROADMAP.md) — Detailed technical roadmap and implementation history
- [docs/roadmaps/LIVING_CHRONICLE_ROADMAP.md](docs/roadmaps/LIVING_CHRONICLE_ROADMAP.md) — Product roadmap for the no-player-agency Living Chronicle Simulator direction
- [docs/roadmaps/CONTENT_ROADMAP.md](docs/roadmaps/CONTENT_ROADMAP.md) — Parked content-expansion backlog
- [docs/RULES_FRAMEWORK.md](docs/RULES_FRAMEWORK.md) — Spreadsheet-first campaign operating rules
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Architecture deep-dive (Phase 6)
- [docs/EXTENDING.md](docs/EXTENDING.md) — How to add new systems (Phase 6)
- [docs/API.md](docs/API.md) — Public API reference (Phase 6)
- [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) — Repository layout and folder rules

## Key Files

- [docs/roadmaps/MODULARIZATION_ROADMAP.md](docs/roadmaps/MODULARIZATION_ROADMAP.md) — Complete technical modularization roadmap with code examples
- [docs/roadmaps/LIVING_CHRONICLE_ROADMAP.md](docs/roadmaps/LIVING_CHRONICLE_ROADMAP.md) — Full product roadmap for the autonomous historical chronicle simulator
- [docs/RULES_FRAMEWORK.md](docs/RULES_FRAMEWORK.md) — Enforceable campaign rules framework
- [scripts/run_export.py](scripts/run_export.py) — Preferred export launcher
- [src/warfare_simulation/core/base.py](src/warfare_simulation/core/base.py) — Abstract base classes
- [src/warfare_simulation/core/constants.py](src/warfare_simulation/core/constants.py) — Enums and constants
- [src/warfare_simulation/core/exceptions.py](src/warfare_simulation/core/exceptions.py) — Exception hierarchy
- [src/warfare_simulation/core/validation.py](src/warfare_simulation/core/validation.py) — Validation service

## License

MIT License

## Author

Favour
