# Warfare Simulation Campaign Engine — Modularization Roadmap

**Document Version**: 2.0  
**Last Updated**: 2026-06-20  
**Status**: Foundations Complete; Observer Simulation Pivot Approved; Phase 10 Started

---

## Executive Summary

The project is no longer primarily a player-order campaign engine. It is now a **living-world observer simulation** with spreadsheet export and desktop dashboard presentation layers.

The original modularization goal has been achieved well enough to support the pivot:

- Domain-driven package structure exists.
- SQLite runtime state exists.
- JSON seed configuration exists.
- Workbook export exists.
- A PySide6 dashboard shell exists.
- Deterministic monthly advancement for the active kingdom and resources exists.

The new target is a **synthetic-history simulation engine** that:

1. Advances an in-world `DD/MM/YYYY` calendar automatically.
2. Resolves daily, weekly, monthly, seasonal, and yearly pulses.
3. Simulates autonomous factions rather than accepting player orders.
4. Produces auditable, explainable history through logs and summaries.
5. Exposes world state through workbook exports and the desktop observatory UI.

This roadmap preserves completed work while redefining the upcoming phases around the observer model documented in [../RULES_FRAMEWORK.md](../RULES_FRAMEWORK.md).

---

## Current Status

| Phase | Status | Notes |
| --- | --- | --- |
| 1 — Foundation | ✓ Complete | Core abstractions, constants, exceptions, logging, validation |
| 2 — Domains | ✓ Complete | All six domains (models, repository, service) |
| 3 — Data & Persistence | ✓ Complete | JSON configs, schemas, SQLite, migrations, `CampaignBootstrap` |
| 4 — Export | ✓ Complete | Workbook factory, style manager, repository-backed sheet generators |
| 5 — Application | ✓ Complete | Thin app loads JSON, seeds SQLite, hydrates repos, exports state |
| 6 — Verification & Docs | ✓ Complete | Tests, architecture docs, API docs, extension docs |
| 7 — Runtime State | ✓ Complete | Kingdom/resource persistence, checkpoints, startup state hydration |
| 8 — Observer Pivot | ✓ Complete | Calendar model, dashboard speed controls, date checkpointing, and initial pulse loop are complete; autonomous actors and observer summaries remain next |
| 9 — Pulse Scheduler | ✓ Complete | Daily, weekly, monthly, seasonal, and yearly cadence boundaries are implemented and tested |
| 10 — Observer Logs | In Progress | Structured event metadata now records date, actor, target, source system, cause chain, and effect summary |

**Reference implementation**: `campaign_engine_initialiser.py` remains deprecated. It is now only a historical export reference, not a target design for future behavior.

---

## Guiding Principles (v2.0 Observer Pivot)

1. **The simulation is the product.** Workbook exports and the desktop dashboard are observer surfaces, not the place where the world is authored by hand.
2. **Time is continuous in-world, not turn-only.** The primary observer clock is `DD/MM/YYYY`.
3. **Autonomy comes before content sprawl.** Build faction decision loops, pulse scheduling, and causal logs before adding large numbers of new mechanics.
4. **Explainability is non-negotiable.** Every major rise, collapse, war, famine, treaty, rebellion, and succession event must be traceable through logs.
5. **Keep UI and engine separate.** The service layer and read-model boundary already added for the dashboard should remain strict.
6. **Ship in pulses, not fantasies.** Add daily, weekly, monthly, seasonal, and yearly systems incrementally with tests at each layer.
7. **Use the rules document as contract.** The observer rules framework defines the allowed architecture and feature ordering for future work.

---

## High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  app.py / main.py                                         │   │
│  │  - Initialize system                                       │   │
│  │  - Orchestrate domains                                     │   │
│  │  - Trigger exports                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       ORCHESTRATION LAYER                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  GameState / CampaignOrchestrator                        │   │
│  │  - Coordinates all domains                               │   │
│  │  - Manages turn advancement                              │   │
│  │  - Validates system state                                │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
    ↓                ↓                ↓               ↓
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ KINGDOM  │   │ MILITARY │   │ GEOGRAPHY│   │DIPLOMACY │
│  Domain  │   │  Domain  │   │  Domain  │   │  Domain  │
│          │   │          │   │          │   │          │
│ -Models  │   │ -Models  │   │ -Models  │   │ -Models  │
│ -Repo    │   │ -Repo    │   │ -Repo    │   │ -Repo    │
│ -Service │   │ -Service │   │ -Service │   │ -Service │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
    ↓                ↓                ↓               ↓
┌─────────────────────────────────────────────────────────────────┐
│                     PERSISTENCE LAYER                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Repository Pattern (SQLite)                             │   │
│  │  - Generic CRUD operations                               │   │
│  │  - Domain-specific queries                               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      EXPORT LAYER                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  WorkbookFactory                                          │   │
│  │  - Orchestrates sheet generators                          │   │
│  │  - Each generator knows only its domain                   │   │
│  │  - No cross-domain dependencies                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓                                   │
│  ┌─────────────┬─────────────┬──────────────┬────────────────┐  │
│  │  Dashboard  │   Provinces │     Army     │   Diplomacy    │  │
│  │ Generator   │  Generator  │  Generator   │   Generator    │  │
│  └─────────────┴─────────────┴──────────────┴────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    Auster_Campaign_Engine.xlsx
```

---

## Startup Flow (Initialization Sequence)

```text
1. main.py starts app.py
   ↓
2. ConfigManager loads JSON files from config/data/
   ├─ initial_kingdom.json
   ├─ provinces.json
   ├─ units.json
   ├─ commanders.json
   ├─ diplomacy.json
   ├─ resources.json
   └─ (validated by Pydantic schemas)
   ↓
3. DatabaseManager initializes SQLite (warfare_simulation.db)
   ├─ Creates tables if missing
   ├─ Runs migrations if needed
   ↓
4. DomainRepositories populated from JSON → DB
   ├─ KingdomRepository.create_from_config(config)
   ├─ ProvinceRepository.create_from_config(config)
   ├─ MilitaryRepository.create_from_config(config)
   └─ (other domains...)
   ↓
5. CampaignOrchestrator initialized with all domains
   ↓
6. WorkbookFactory triggers all SheetGenerators
   ├─ DashboardGenerator.generate() → queries Kingdom domain
   ├─ ProvinceGenerator.generate() → queries Geography domain
   ├─ ArmyGenerator.generate() → queries Military domain
   └─ (other generators...)
   ↓
7. Workbook saved as Auster_Campaign_Engine.xlsx
   ↓
8. App ready for campaign simulation / turn advancement
```

**Key Principle**: JSON is the "campaign definition" (immutable seed), SQLite is the "campaign state" (mutable runtime). On startup, populate SQLite from JSON. After that, all mutations go to the database.

---

## Project Structure

```text
Warfare Simulation/
├── src/warfare_simulation/          # Main package
│   ├── __init__.py                  # Package marker, version info
│   │
│   ├── core/                        # Shared abstractions & utilities
│   │   ├── __init__.py
│   │   ├── base.py                  # GameEntity, GameSystem, SheetGenerator
│   │   ├── constants.py             # Enums: UnitType, FactionStatus, ProjectType, etc.
│   │   ├── exceptions.py            # InvalidCampaignStateError, ResourceError, etc.
│   │   ├── logger.py                # Centralized logging
│   │   └── validation.py            # ValidationService (cross-domain validation rules)
│   │
│   ├── config/                      # Configuration management
│   │   ├── __init__.py
│   │   ├── config.py                # ConfigManager (loads JSON files)
│   │   ├── loaders.py               # Data loaders for each domain
│   │   ├── schema.py                # Pydantic models (validated config schema)
│   │   └── data/                    # Configuration files (JSON)
│   │       ├── initial_kingdom.json
│   │       ├── provinces.json
│   │       ├── units.json
│   │       ├── commanders.json
│   │       ├── diplomacy.json
│   │       ├── resources.json
│   │       └── README.md            # Config format documentation
│   │
│   ├── domain/                      # Business logic for each game system
│   │   ├── __init__.py
│   │   │
│   │   ├── kingdom/                 # Kingdom management
│   │   │   ├── __init__.py
│   │   │   ├── models.py            # Kingdom, Treasury, Morale, Ruler classes
│   │   │   ├── repository.py        # KingdomRepository (CRUD + queries)
│   │   │   └── service.py           # KingdomService (business logic, turn advancement)
│   │   │
│   │   ├── geography/               # Provinces & spatial logic
│   │   │   ├── __init__.py
│   │   │   ├── models.py            # Province, Location, Border classes
│   │   │   ├── repository.py        # ProvinceRepository
│   │   │   └── service.py           # GeographyService (population, borders, etc.)
│   │   │
│   │   ├── military/                # Units, armies, commanders
│   │   │   ├── __init__.py
│   │   │   ├── models.py            # Unit, Commander, UnitType (enums), Garrison classes
│   │   │   ├── repository.py        # MilitaryRepository
│   │   │   ├── service.py           # MilitaryService (morale, fatigue, training)
│   │   │   ├── tactics.py           # (Placeholder) Combat system interface
│   │   │   └── combat/              # (Future) Combat simulation
│   │   │       ├── __init__.py
│   │   │       ├── interface.py     # ICombatSystem (abstract methods)
│   │   │       └── resolver.py      # (TBD) Combat outcome calculation
│   │   │
│   │   ├── diplomacy/               # Factions, relations, espionage
│   │   │   ├── __init__.py
│   │   │   ├── models.py            # Faction, Relation, Spy, Mission classes
│   │   │   ├── repository.py        # DiplomacyRepository
│   │   │   └── service.py           # DiplomacyService (opinion shifts, spies)
│   │   │
│   │   ├── logistics/               # Resources, projects, supply chains
│   │   │   ├── __init__.py
│   │   │   ├── models.py            # Resource, Project, SupplyRoute classes
│   │   │   ├── repository.py        # LogisticsRepository
│   │   │   └── service.py           # LogisticsService (production, consumption)
│   │   │
│   │   └── events/                  # Event system (prepared for expansion)
│   │       ├── __init__.py
│   │       ├── models.py            # Event, EventType classes
│   │       ├── repository.py        # EventRepository
│   │       └── service.py           # EventService (trigger, resolve, log)
│   │
│   ├── persistence/                 # Data access & database
│   │   ├── __init__.py
│   │   ├── database.py              # SQLite connection, schema, initialization
│   │   ├── migrations.py            # Database versioning & migrations
│   │   └── repository.py            # Generic Repository base class (all repos inherit)
│   │
│   ├── export/                      # Spreadsheet generation
│   │   ├── __init__.py
│   │   ├── styles.py                # StyleManager (fonts, fills, colors, alignment)
│   │   ├── base_generator.py        # SheetGenerator abstract base class
│   │   ├── dashboard_generator.py   # Kingdom dashboard sheet
│   │   ├── provinces_generator.py   # Provinces sheet
│   │   ├── army_generator.py        # Army register sheet
│   │   ├── diplomacy_generator.py   # Diplomacy & Intel sheet
│   │   ├── resources_generator.py   # Resources sheet
│   │   ├── commanders_generator.py  # Commanders sheet
│   │   ├── logistics_generator.py   # Logistics & Projects sheet
│   │   ├── events_generator.py      # Event Log sheet
│   │   └── workbook_factory.py      # Orchestrates all generators
│   │
│   ├── orchestration/               # Campaign-level coordination
│   │   ├── __init__.py
│   │   ├── campaign.py              # CampaignOrchestrator (coordinates all domains)
│   │   └── game_state.py            # GameState (snapshot of current turn)
│   │
│   ├── app.py                       # Main application logic (initialization, orchestration)
│   │
│   └── main.py                      # Entry point (CLI, simple runner)
│
├── tests/                           # Unit & integration tests (future)
│   ├── __init__.py
│   ├── test_kingdom.py
│   ├── test_military.py
│   ├── test_export.py
│   └── ...
│
├── docs/                            # Documentation
│   ├── roadmaps/                    # Planning and execution order docs
│   ├── ARCHITECTURE.md              # Detailed architecture guide
│   ├── EXTENDING.md                 # How to add new domains/systems
│   └── API.md                       # Public API reference
│
├── scripts/                         # Launchers and manual run helpers
├── docs/roadmaps/MODULARIZATION_ROADMAP.md
├── README.md                        # Project overview, quick start
├── requirements.txt                 # Dependencies: openpyxl, pydantic, etc.
├── pyproject.toml                   # Package metadata
├── .gitignore                       # Exclude generated files, DB, __pycache__
│
└── war_sim.db                       # (Generated at runtime) SQLite database
```

---

## Observer Simulation Pivot Roadmap

The sections below define the forward plan from the current foundation to a full autonomous observer simulation.

### Product Goal

Build a living world that advances automatically on a simulated `DD/MM/YYYY` calendar, resolves autonomous faction behavior through deterministic and stochastic systems, and surfaces its history through workbook exports, logs, and the PySide6 observatory UI.

### Delivery Horizon

| Horizon | Outcome |
| --- | --- |
| Horizon 1 | Stable real-time-in-sim calendar, initial pulse engine, pause/speed controls |
| Horizon 2 | Autonomous faction loop, province pressure, and observer-grade event logs |
| Horizon 3 | Emergent wars, rebellions, diplomacy arcs, and multi-year replayable history |
| Horizon 4 | Synthetic-history sandbox with scenarios, balancing, and long-run stability tooling |

### Phase 8: Calendar and Time Engine (Complete)

**Goal**: Replace the month-only state model with a real simulation calendar and support pausable real-time progression.

**Tasks**:

1. [x] Introduce a canonical `SimDate` or equivalent date model with `day`, `month`, and `year`.
2. [x] Add calendar utilities for month lengths, year rollover, and formatting as `DD/MM/YYYY`.
3. [x] Replace `GameState`'s turn-centric assumptions with date-centric state while preserving optional turn counters for aggregation.
4. [x] Add simulation speed states: `paused`, `1x`, `2x`, `5x`, and `fast`.
5. [x] Add desktop dashboard controls for pause/resume and speed changes.
6. [x] Persist simulation date and speed-safe checkpoint state.

**Deliverables**:

1. [x] Date model integrated into `GameState` and orchestration.
2. [x] Dashboard live date display.
3. [x] Checkpoint round-trip for day/month/year state.

**Exit criteria**:

1. [x] The simulation can advance day by day without corrupting month/year rollover.
2. [x] The UI shows the live in-world date.
3. [x] Checkpoint load resumes from the exact stored date.

### Phase 9: Pulse Scheduler and System Cadence (Estimated: 2-3 weeks)

**Goal**: Create the engine loop that schedules daily, weekly, monthly, seasonal, and yearly work without entangling domain code.

**Tasks**:

1. [x] Introduce a pulse scheduler in orchestration.
2. [x] Define per-pulse hooks for domain services.
3. [x] Implement daily, weekly, monthly, seasonal, and yearly execution boundaries.
4. [x] Add deterministic ordering for all pulse types, aligned with [../RULES_FRAMEWORK.md](../RULES_FRAMEWORK.md).
5. [x] Add focused tests for pulse boundaries and duplicate-run prevention.

**Deliverables**:

1. [x] `advance_day()` orchestration path.
2. [x] Registered pulse hooks for implemented daily calendar sync and monthly economy/logistics domains.
3. [x] Verified monthly and yearly boundary behavior.

**Exit criteria**:

1. [x] No system executes twice at the same boundary.
2. [x] Monthly economy and logistics still match expected totals after daily progression.
3. [x] Year transitions are deterministic and tested.

### Phase 10: Observer Logs and Causality Backbone (Estimated: 2-3 weeks)

**Goal**: Make the world explain itself before making it more complicated.

**Tasks**:

1. [x] Expand the events domain into a structured historical log system.
2. [x] Add event metadata: date, actor, target, source system, cause chain, and effect summary.
3. [ ] Add dedicated logs for economics, diplomacy, construction, conflict, and random resolution.
4. [ ] Add summary generators for daily/weekly/monthly observer output.
5. [x] Update exports to surface causal event history clearly while preserving the current workbook contract.
6. [ ] Update the dashboard to surface the latest history clearly.

**Deliverables**:

1. [x] Typed event records with causal metadata for core systems.
2. [ ] Observer-readable event feed in the dashboard.
3. [x] Exported Event Log rows driven by recorded logs and causal metadata.

**Exit criteria**:

1. Any major state change can be traced back through recorded causes.
2. The dashboard event feed remains readable over long runs.
3. Logs survive checkpoint save/load.

### Phase 11: Autonomous Faction Decision Loop (Estimated: 3-5 weeks)

**Goal**: Replace player orders with AI state actors that make validated strategic choices.

**Tasks**:

1. Define faction goals, pressures, and risk appetites.
2. Build a decision-evaluation layer for diplomacy, military posture, and internal stabilization.
3. Add decision validation so impossible intent is rejected and logged.
4. Add short-horizon and long-horizon reassessment cadence.
5. Add tuning parameters for aggressiveness, consolidation preference, and threat response.

**Deliverables**:

1. Autonomous decision service or services.
2. Logged accepted and rejected decisions.
3. Dashboard views for faction summaries and current world tensions.

**Exit criteria**:

1. Factions change posture without human input.
2. Decisions respect treasury, supply, and political constraints.
3. The world shows divergent behavior across different seeds.

### Phase 12: Province Pressure and Material World Model (Estimated: 3-5 weeks)

**Goal**: Give the world internal motion through food, tax pressure, loyalty, unrest, and administrative drag.

**Tasks**:

1. Expand province state to support unrest, prosperity, and pressure metrics.
2. Refine food and resource consumption to operate on smaller pulses.
3. Model taxation, shortage effects, and local stability drift.
4. Add construction and recruitment progress as ongoing systems rather than single-step updates.
5. Add administrative-capacity penalties for overextended realms.

**Deliverables**:

1. Province pressure model.
2. Monthly economy that emerges from provincial state rather than only static kingdom values.
3. Dashboard hotspots for instability and shortages.

**Exit criteria**:

1. Provinces diverge in meaningful ways over time.
2. Shortages and overtaxation cause visible downstream effects.
3. Internal pressure can destabilize even militarily strong states.

### Phase 13: Conflict Emergence, Rebellions, and War Resolution (Estimated: 4-6 weeks)

**Goal**: Let conflict emerge from state pressure and autonomous decisions rather than scripted commands.

**Tasks**:

1. Introduce war declaration and hostility escalation rules.
2. Add rebellion triggers from province and realm pressure.
3. Build campaign-level conflict resolution for raids, battles, sieges, and pursuit.
4. Apply post-conflict effects to morale, manpower, legitimacy, diplomacy, and logistics.
5. Record all conflicts as auditable historical events.

**Deliverables**:

1. War and rebellion trigger systems.
2. First-pass battle and siege resolver.
3. Conflict summaries in logs and exports.

**Exit criteria**:

1. Wars and rebellions can begin, resolve, and alter world state without human control.
2. Losses and victories propagate into economy and politics.
3. Conflict outcomes are explainable from recorded inputs.

### Phase 14: Historical Memory, Leadership, and Long-Run Stability (Estimated: 4-8 weeks)

**Goal**: Make the world feel historical rather than stateless.

**Tasks**:

1. Add persistent diplomatic memory of wars, treaties, betrayals, and border loss.
2. Add ruler or leadership lifecycle mechanics: aging, death, succession, instability.
3. Add long-horizon cultural, religious, or institutional drift where appropriate.
4. Add regime-fragility mechanics so collapse and recovery have inertia.
5. Add replay and timeline inspection tools for long simulations.

**Deliverables**:

1. Historical memory model.
2. Succession and leadership events.
3. Multi-year timeline viewer requirements captured in UI and export surfaces.

**Exit criteria**:

1. States remember the consequences of earlier history.
2. Leadership change creates real but legible instability.
3. Long-run simulations produce distinct eras, not repeated loops.

### Phase 15: Observatory Experience and Scenario Tooling (Estimated: 3-6 weeks)

**Goal**: Turn the engine into a compelling observer product.

**Tasks**:

1. Expand the desktop dashboard into a world observatory.
2. Add trend panels, hotspot views, and timeline navigation.
3. Improve workbook outputs for historical reporting rather than player control.
4. Add scenario presets and seed controls.
5. Add balancing dashboards and simulation batch runs.

**Deliverables**:

1. Observer-first dashboard UX.
2. Scenario configuration flow.
3. Better exports for history, tensions, and long-term trends.

**Exit criteria**:

1. A user can watch, pause, inspect, and understand a long run without developer help.
2. Exported reports explain the world rather than merely listing raw values.
3. Different seeds and scenario presets produce recognizable world archetypes.

### Phase 16: Scale, Balancing, and Synthetic History Platform (Estimated: ongoing)

**Goal**: Make the simulation robust enough for long horizons, alternate scenarios, and repeated study.

**Tasks**:

1. Add simulation profiling and bottleneck detection.
2. Add statistical run analysis and balance tooling.
3. Add richer scenario packages, alternate starts, and regional archetypes.
4. Add curator tools carefully, without undermining observer integrity.
5. Add replay export and historical archive tooling.

**Deliverables**:

1. Long-run stability benchmarks.
2. Scenario packs.
3. Balance reports and anomaly detection.

**Exit criteria**:

1. The simulation can run for long spans without degenerating into nonsense or total stasis.
2. The project supports multiple starting worlds with consistent observer-quality output.
3. Historical logs remain interpretable at scale.

### Immediate Build Order

The next practical implementation order should be:

1. Phase 8 — Calendar and Time Engine.
2. Phase 9 — Pulse Scheduler and System Cadence.
3. Phase 10 — Observer Logs and Causality Backbone.
4. Phase 11 — Autonomous Faction Decision Loop.
5. Phase 12 — Province Pressure and Material World Model.

That order enforces the observer rules: time first, then system cadence, then explainability, then autonomy, then world pressure.

---

## Historical Modularization Archive

### Phase 1: Project Foundation ✓ Complete (Estimated: 2-3 hours)

**Goals**: Set up package structure, define base classes and constants.


**Tasks**:
1. Create `src/warfare_simulation/` package structure with `__init__.py`
2. Create `core/base.py` with abstract classes:
   - `GameEntity` (base for all game objects: units, provinces, factions)
   - `GameSystem` (base for all domain services: military, diplomacy, etc.)
   - `SheetGenerator` (base for all spreadsheet generators with shared formatting logic)
   - `IValidationRule` (interface for domain-specific validation)


3. Create `core/constants.py` with enums:
   ```python
   class UnitType(Enum):
       HEAVY_SPEARMEN = "Heavy Spearmen"
       RANGED = "Ranged"
       HEAVY_INFANTRY = "Heavy Infantry"
       MEDIUM_CAVALRY = "Medium Cavalry"
   
   class ProjectType(Enum):
       FORTIFICATION = "Fortification"
       INFRASTRUCTURE = "Infrastructure"
       CONVOY = "Convoy"
   
   class FactionStatus(Enum):
       ALLY = "Ally"
       RIVAL = "Rival"
       NEUTRAL = "Neutral"
       VASSAL = "Vassal"
   ```

4. Create `core/exceptions.py` with custom exceptions:

   - `InvalidCampaignStateError` (state violation)
   - `ResourceError` (insufficient resources)
   - `ValidationError` (config validation failed)
   - `DatabaseError` (persistence layer issue)

5. Create `core/logger.py` for centralized logging (use `logging` stdlib)
6. Create `core/validation.py` with `ValidationService` class:

   - Method: `validate_kingdom_state(kingdom) -> List[ValidationError]`
   - Method: `validate_resource_transaction(source, target, amount) -> bool`
   - Method: `validate_military_deployment(unit, location) -> bool`

**Deliverable**: Importable core module with base abstractions.

---

### Phase 2: Core Domain Implementation ✓ Complete (Estimated: 4-5 hours)

**Goals**: Implement business logic for each game system.

**For each domain (Kingdom, Geography, Military, Diplomacy, Logistics, Events)**:
1. Create `domain/{domain_name}/models.py`:
   - Define data classes (use `@dataclass` or Pydantic `BaseModel`)
   - Include validation methods where appropriate
   - Example (Kingdom):
     ```python
     class Kingdom(GameEntity):
         name: str
         ruler_name: str
         population: int
         treasury_silver: int
         
         def advance_turn(self):
             """Calculate income/expenses, update state"""
             net_income = self.monthly_income - self.monthly_expenses
             self.treasury_silver += net_income
             
         def spend_silver(self, amount):
             if amount > self.treasury_silver:
                 raise ResourceError("Insufficient silver")
             self.treasury_silver -= amount
     ```

2. Create `domain/{domain_name}/repository.py`:
   - Inherit from generic `Repository` base class
   - Implement domain-specific queries
   - Example (KingdomRepository):
     ```python
     class KingdomRepository(Repository):
         def get_by_name(self, name: str) -> Kingdom:
             """Fetch kingdom by name"""
         
         def update_treasury(self, kingdom_id: int, amount: int):
             """Atomic treasury update"""
         
         def get_all_with_morale_above(self, threshold: int) -> List[Kingdom]:
             """Query optimization example"""
     ```

3. Create `domain/{domain_name}/service.py`:
   - Orchestrate business logic using repository + validation
   - Example (KingdomService):
     ```python
     class KingdomService(GameSystem):
         def __init__(self, repo: KingdomRepository, validator: ValidationService):
             self.repo = repo
             self.validator = validator
         
         def advance_kingdom_turn(self, kingdom_id: int):
             kingdom = self.repo.get(kingdom_id)
             self.validator.validate_kingdom_state(kingdom)
             kingdom.advance_turn()
             self.repo.update(kingdom)
     ```

**Key Principle**: Models = pure data. Repositories = data access. Services = business logic (orchestration).

**Deliverable**: All domains importable with full CRUD operations and business logic.

---

### Phase 3: Data & Persistence ✓ Complete (Estimated: 3-4 hours)

**Verified by**: `python test_phase3_persistence.py` (requires `pip install -r requirements.txt`; Python 3.10–3.11 recommended)

**Goals**: Externalize hardcoded data, implement SQLite database layer, seed runtime state from JSON.

**Tasks**:


1. Create `config/data/` JSON files:
   - `initial_kingdom.json`: Kingdom name, ruler, population, treasury, etc.
   - `provinces.json`: List of provinces with population, garrison, loyalty
   - `units.json`: Unit templates (type, base morale, armor, etc.)
   - `commanders.json`: Commander data with skills and traits
   - `diplomacy.json`: Initial faction relations
   - `resources.json`: Resource definitions and storage amounts


   Example structure:
   ```json
   {
     "kingdom": {
       "name": "The Dominion of Auster",
       "ruler": "Lord Protector Favour",
       "population": 450000,
       "treasury_silver": 520000,
       "monthly_income": 18500,
       "monthly_expenses": 12800
     },
     "provinces": [
       {"name": "Highreach", "population": 150000, "loyalty": 95},
       {"name": "Oakhaven", "population": 180000, "loyalty": 90}
     ]
   }
   ```

2. Create `config/schema.py` with Pydantic models:
   - `KingdomConfig`, `ProvinceConfig`, `UnitConfig`, etc.
   - Validates JSON structure on load
   - Provides type hints for IDE support

3. Create `config/config.py` (ConfigManager):
   ```python
   class ConfigManager:
       def load_kingdom_config(self) -> KingdomConfig:
           """Load & validate initial_kingdom.json"""
       
       def load_all_configs(self) -> FullCampaignConfig:
           """Load all JSON files"""
   ```

4. Create `persistence/database.py`:
   - Initialize SQLite connection
   - Define schema (tables for each entity)
   - Example:
     ```python
     class DatabaseManager:
         def __init__(self, db_path: str = "war_sim.db"):
             self.conn = sqlite3.connect(db_path)
         
         def initialize_schema(self):
             """Create tables if missing"""
             self.conn.execute("""
                 CREATE TABLE IF NOT EXISTS kingdom (
                     id INTEGER PRIMARY KEY,
                     name TEXT UNIQUE,
                     ruler TEXT,
                     population INTEGER,
                     treasury_silver INTEGER
                 )
             """)
     ```

5. Create `persistence/repository.py` (Generic base):
   ```python
   class Repository(Generic[T]):
       def create(self, entity: T) -> T:
           """Insert, return with ID"""
       
       def get(self, id: int) -> T:
           """Fetch by ID"""
       
       def update(self, entity: T) -> T:
           """Update and return"""
       
       def delete(self, id: int) -> bool:
           """Remove by ID"""
       
       def list_all(self) -> List[T]:
           """Fetch all"""
   ```

6. Create `persistence/migrations.py`:
   - Version-track database schema
   - Support future schema changes

6. Create `persistence/campaign_bootstrap.py` (CampaignBootstrap):
   - `seed_from_config()`: load JSON via ConfigManager → insert into SQLite (idempotent)
   - `load_repositories()`: hydrate in-memory domain repos from SQLite
   - `initialize()`: seed + hydrate in one call

**Initialization Flow**:
```python
config_mgr = ConfigManager()
db_mgr = DatabaseManager()
db_mgr.connect()
db_mgr.initialize_schema()

from warfare_simulation.persistence.campaign_bootstrap import CampaignBootstrap
repos = CampaignBootstrap.initialize(config_mgr, db_mgr)
```

**Deliverable**: SQLite database with all entities, JSON configs, and working data loaders.

---

### Phase 4: Spreadsheet Generation (Refactored) — **CURRENT PRIORITY** (Estimated: 3-4 hours)

**Goals**: Break monolithic spreadsheet function into domain-aware, composable generators and prove end-to-end parity with `campaign_engine_initialiser.py`.


**Success criteria** (all must pass before moving to Phase 5):

- [ ] JSON configs load and populate SQLite without errors
- [ ] `WorkbookFactory.create_workbook()` produces all 8 sheets
- [ ] Sheet names, row counts, and key cell values match the monolith output
- [ ] `tests/test_export_parity.py` passes (stub acceptable at Phase 4 start; tighten in Phase 6)


**Tasks**:

0. **Create integration test first** (`tests/test_export_parity.py`):
   ```python
   def test_export_sheet_names_match_monolith(tmp_path):
       """New export must produce the same sheets as campaign_engine_initialiser.py."""
       from campaign_engine_initialiser import create_campaign_workbook
       from warfare_simulation.export.workbook_factory import WorkbookFactory
       # ... wire repos from test DB seeded from config ...

       legacy_wb = create_campaign_workbook()
       new_wb = factory.create_workbook()

       assert [ws.title for ws in legacy_wb.worksheets] == [ws.title for ws in new_wb.worksheets]

   def test_export_row_counts_match_monolith(tmp_path):
       """Each sheet should have the same number of data rows as the monolith."""
       # Compare ws.max_row per sheet; expand to cell-level parity in Phase 6
   ```

1. Create `export/styles.py` (StyleManager):
   ```python
   class StyleManager:
       @staticmethod
       def header_style():
           return Font(bold=True, color="FFFFFF"), \
                  PatternFill(start_color="333333", fill_type="solid")
       
       @staticmethod
       def center_alignment():
           return Alignment(horizontal="center", vertical="center")
   ```

2. Create `export/base_generator.py` (Abstract SheetGenerator):
   ```python
   class SheetGenerator(ABC):
       def __init__(self, workbook, style_manager):
           self.wb = workbook
           self.styles = style_manager
       
       @abstractmethod
       def generate(self) -> None:
           """Subclasses implement sheet creation"""
       
       def _format_header_row(self, ws, headers):
           """Shared formatting logic"""
           ws.append(headers)
           for col_num, cell in enumerate(ws[1], 1):
               cell.font, cell.fill = self.styles.header_style()
               cell.alignment = self.styles.center_alignment()
   ```

3. Create individual generators:
   - `dashboard_generator.py`: Queries `KingdomRepository`, builds "Kingdom Dashboard" sheet
   - `provinces_generator.py`: Queries `ProvinceRepository`, builds "Provinces" sheet
   - `army_generator.py`: Queries `MilitaryRepository`, builds "Army Register" sheet
   - `diplomacy_generator.py`: Queries `DiplomacyRepository`, builds "Diplomacy & Intel" sheet
   - `resources_generator.py`: Queries `LogisticsRepository`, builds "Resources" sheet
   - `commanders_generator.py`: Queries `MilitaryRepository`, builds "Commanders" sheet
   - `logistics_generator.py`: Queries `LogisticsRepository`, builds "Logistics & Projects" sheet
   - `events_generator.py`: Queries `EventRepository`, builds "Event Log" sheet


   Example (DashboardGenerator):
   ```python
   class DashboardGenerator(SheetGenerator):
       def __init__(self, workbook, style_manager, kingdom_repo):
           super().__init__(workbook, style_manager)
           self.kingdom_repo = kingdom_repo
       
       def generate(self):
           ws = self.wb.create_sheet("Kingdom Dashboard")
           kingdom = self.kingdom_repo.get(1)  # Fetch current kingdom
           
           headers = ["Category", "Value", "Notes"]
           self._format_header_row(ws, headers)
           
           data = [
               ["Kingdom", kingdom.name, ""],
               ["Ruler", kingdom.ruler_name, ""],
               ["Treasury", kingdom.treasury_silver, ""],
               # ... etc
           ]
           for row in data:
               ws.append(row)
   ```

4. Create `export/workbook_factory.py`:
   ```python
   class WorkbookFactory:
       def __init__(self, kingdom_repo, military_repo, province_repo, etc.):
           self.repos = {...}
       
       def create_workbook(self) -> Workbook:
           wb = openpyxl.Workbook()
           wb.remove(wb.active)  # Remove default sheet
           
           styles = StyleManager()
           
           generators = [
               DashboardGenerator(wb, styles, self.repos['kingdom']),
               ProvinceGenerator(wb, styles, self.repos['province']),
               ArmyGenerator(wb, styles, self.repos['military']),
               # ... all others
           ]
           
           for gen in generators:
               gen.generate()
           
           return wb
   ```

**Key Benefit**: No generator depends on another generator's data. Each only knows its own domain. Adding a new sheet = adding one generator class. No existing code changes.

**Monolith policy**: Use `campaign_engine_initialiser.py` as the reference when implementing each generator. Compare output sheet-by-sheet as you go. Do **not** remove the monolith file until Phase 6 parity verification passes.

**Deliverable**: Spreadsheet generation exactly matches original output, organized into composable, domain-aware generators, with `test_export_parity.py` green.

---

### Phase 5: Entry Points & Application Layer — **Thin Slice** (Estimated: 1-2 hours)

**Goals**: Minimal runnable app — load config, seed DB, export spreadsheet. No full turn loop yet.


**Scope (Phase 5)**:
- ✓ `WarfareSimulationApp`: init config + DB + repos, seed from JSON, call export
- ✓ `main.py`: one-line entry point (`app.run()`)
- ✓ `CampaignOrchestrator.export_campaign()` only (delegates to `WorkbookFactory`)
- Stub `GameState` with `current_turn = 1` — no save/load yet
- Stub `CampaignOrchestrator.advance_turn()` with `pass` or `NotImplementedError`


**Deferred to post–Phase 6** (see "Next Steps After Phase 6"):
- Full turn advancement across all domains
- `GameState.save_checkpoint()` / load
- Interactive CLI
- Combat system wiring


**Tasks**:


1. Create `orchestration/campaign.py` (minimal `CampaignOrchestrator`):
   ```python
   class CampaignOrchestrator:
       def __init__(self, repos: dict):
           self.repos = repos
   
       def export_campaign(self, filename: str):
           """Generate current state as Excel"""
           factory = WorkbookFactory(self.repos)
           wb = factory.create_workbook()
           wb.save(filename)
   
       def advance_turn(self):
           """Deferred — implement after Phase 6 verification."""
           raise NotImplementedError("Turn simulation comes after export parity is verified")
   ```

2. Create `orchestration/game_state.py` (stub):
   ```python
   class GameState:
       def __init__(self, current_turn: int = 1):
           self.current_turn = current_turn
   ```

3. Create `src/warfare_simulation/app.py`:
   ```python
   class WarfareSimulationApp:
       def __init__(self, config_path: str = "config/data/"):
           # Load configuration
           self.config_mgr = ConfigManager(config_path)
           
           # Initialize database
           self.db_mgr = DatabaseManager("war_sim.db")
           self.db_mgr.initialize_schema()
           
           # Initialize repositories
           self.kingdom_repo = KingdomRepository(self.db_mgr)
           self.military_repo = MilitaryRepository(self.db_mgr)
           # ... etc for all domains
           
           # Load JSON → populate SQLite (one-time)
           self._initialize_from_config()
           
           # Create orchestrator (export-only for Phase 5)
           self.repos = {
               'kingdom': self.kingdom_repo,
               'military': self.military_repo,
               # ... etc
           }
           self.campaign = CampaignOrchestrator(self.repos)
           self.game_state = GameState()
       
       def _initialize_from_config(self):
           """Load JSON configs into SQLite (idempotent)"""
           configs = self.config_mgr.load_all_configs()
           
           kingdom = Kingdom(**configs.kingdom.dict())
           self.kingdom_repo.create(kingdom)
           
           for prov_config in configs.provinces:
               province = Province(**prov_config.dict())
               self.province_repo.create(province)
           
           # ... repeat for all domains
       
       def export_campaign(self, filename: str = "Auster_Campaign_Engine.xlsx"):
           """Generate spreadsheet"""
           self.campaign.export_campaign(filename)
       
       def run(self):
           """Main application flow — init + export only (Phase 5)"""
           print("Campaign engine initialized.")
           self.export_campaign()
           print("Spreadsheet exported.")
   ```

4. Create `src/warfare_simulation/main.py`:
   ```python
   if __name__ == "__main__":
       app = WarfareSimulationApp()
       app.run()
   ```

5. Verify `requirements.txt`, `pyproject.toml`, and `.gitignore` (already exist — confirm entries are correct)

**Deliverable**: `python src/warfare_simulation/main.py` loads JSON, populates SQLite, and exports the spreadsheet. Turn simulation explicitly deferred.

---

### Phase 6: Verification & Documentation (Estimated: 2-3 hours)

**Goals**: Harden tests, document architecture, demonstrate extensibility, and **retire the monolith**.


**Monolith retirement criteria** (all required):

- [x] `tests/test_export_parity.py` passes with cell-level comparison (not just sheet names / row counts)
- [x] All 8 sheets match `campaign_engine_initialiser.py` output
- [x] `WarfareSimulationApp.run()` produces identical `.xlsx` via the modular path
- [x] Monolith file marked deprecated in a comment, then removed in a follow-up commit


**Tasks**:

1. **Verification Tests** (extend existing tests in `tests/`):
   - ✓ Domain tests: `test_phase2_domains.py` (exists)
   - ✓ Persistence tests: `test_phase3_persistence.py` (exists)
   - ✓ Expand `test_export_parity.py`: full sheet-by-sheet comparison (old monolith vs. new export)
   - ✓ Test config loading: Load JSON → verify all fields parsed correctly
   - ✓ Test SQLite: Run app → verify DB created with correct schema
   - Test turn advancement: **deferred** until post–Phase 6 turn simulation work

   Example test:
   ```python
   def test_kingdom_domain_isolation():
       """Verify military module can import without kingdom dependencies"""
       from src.warfare_simulation.domain.military import MilitaryService
       assert MilitaryService is not None  # Should not trigger kingdom imports
   ```

2. **Documentation**:
   - Create `docs/ARCHITECTURE.md`:
     - Explain domain structure
     - Show dependency graph (text ASCII art)
     - Describe data flow (JSON → SQLite → Export)
   
   - Create `docs/EXTENDING.md`:
     - Example: "How to add Combat System"
     - Step 1: Create `domain/combat/models.py` with `CombatSystem` interface
     - Step 2: Create `domain/combat/service.py` implementing combat logic
     - Step 3: Inject `CombatService` into `CampaignOrchestrator.advance_turn()`
     - Step 4: (Optional) Create `export/combat_generator.py` for reporting
   
   - Create `docs/API.md`:
     - List public methods on each service
     - Example usage snippets
   
   - Update root `README.md`:
     - Quick start: `python src/warfare_simulation/main.py`
     - Architecture overview (link to ARCHITECTURE.md)
     - Project status and next steps

3. **Combat System Placeholder**:
   - Create `src/warfare_simulation/domain/military/combat/interface.py`:
     ```python
     class ICombatSystem(ABC):
         @abstractmethod
         def resolve_battle(self, attacker: Unit, defender: Unit) -> BattleResult:
             """Calculate battle outcome"""
         
         @abstractmethod
         def apply_casualties(self, unit: Unit, casualties: int):
             """Update unit strength"""
     ```
   - Create stub implementation in `resolver.py` (just `pass` for now)
   - In `CampaignOrchestrator`, add placeholder:
     ```python
     self.combat_system: Optional[ICombatSystem] = None  # Will be set when implemented
     ```
   - Document in `EXTENDING.md` how to wire it in

4. **Final Checklist**:
   - [ ] All domains import independently
   - [ ] `ConfigManager` loads all JSON files
   - [ ] `DatabaseManager` creates SQLite schema
   - [ ] All repositories can CRUD entities
   - [ ] Generated Excel matches original output (sheet-by-sheet comparison)
   - [ ] `CampaignOrchestrator.advance_turn()` executes without errors
   - [ ] Documentation is complete and accurate
   - [ ] `.gitignore` prevents committing generated files

**Deliverable**: Fully tested, documented, production-ready modular campaign engine.

---

## Validation Strategy

**Problem**: As domains grow, invalid states can emerge (e.g., spending more silver than available, deploying units to non-existent provinces).

**Solution**: Implement three-tier validation.

### Tier 1: Schema Validation (Load-time)
Pydantic models validate JSON structure on load:
```python
class KingdomConfig(BaseModel):
    name: str
    population: int  # Must be > 0
    treasury_silver: int  # Must be >= 0
    
    @field_validator('population')
    def population_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Population must be positive')
        return v

# Load and validate
config = KingdomConfig(**json.load(...))  # Raises if invalid
```

### Tier 2: Service-Level Validation (Runtime)
Before any state mutation, `ValidationService` checks invariants:
```python
class ValidationService:
    def validate_silver_transaction(self, kingdom: Kingdom, amount: int) -> bool:
        if amount > kingdom.treasury_silver:
            raise ResourceError(f"Need {amount} silver, only have {kingdom.treasury_silver}")
        return True
    
    def validate_unit_deployment(self, unit: Unit, location: Province) -> bool:
        if location.garrison_capacity < unit.soldiers:
            raise InvalidCampaignStateError(f"Location {location.name} too small for {unit.name}")
        return True

# Usage in service
class KingdomService:
    def spend_silver(self, kingdom_id: int, amount: int):
        kingdom = self.kingdom_repo.get(kingdom_id)
        self.validator.validate_silver_transaction(kingdom, amount)  # Throws if invalid
        kingdom.spend_silver(amount)  # State mutation
        self.kingdom_repo.update(kingdom)
```

### Tier 3: Cross-Domain Validation (Orchestration)
`CampaignOrchestrator.advance_turn()` validates the entire system state before and after:
```python
class CampaignOrchestrator:
    def advance_turn(self):
        # Snapshot current state
        kingdom_before = self.kingdom_repo.get(1)
        
        # Execute all domain updates
        self.kingdom_svc.advance_kingdom_turn(1)
        self.military_svc.update_all_units()
        
        # Validate consistency
        kingdom_after = self.kingdom_repo.get(1)
        assert kingdom_after.population >= 0, "Population cannot go negative"
        assert kingdom_after.treasury_silver >= 0, "Treasury corrupted"
        # ... etc
```

**Best Practice**: Fail fast. If validation fails, log the error and roll back the transaction (or don't commit to DB). Never let invalid state persist.

---

## Extension Pattern: Adding a New Domain (Combat System Example)

### Scenario
You want to add turn-based combat that resolves when armies clash.

### Steps

**1. Create domain structure**:
```
src/warfare_simulation/domain/combat/
├── __init__.py
├── models.py           # BattleUnit, BattleResult, CombatModifier
├── repository.py       # BattleRepository (log outcomes)
├── service.py          # CombatService (orchestration)
└── resolver.py         # Combat resolution algorithms
```

**2. Define models** (`models.py`):
```python
from dataclasses import dataclass
from enum import Enum

class BattleOutcome(Enum):
    ATTACKER_WIN = "attacker_win"
    DEFENDER_WIN = "defender_win"
    DRAW = "draw"

@dataclass
class BattleResult(GameEntity):
    attacker_unit_id: int
    defender_unit_id: int
    outcome: BattleOutcome
    attacker_casualties: int
    defender_casualties: int
    timestamp: datetime
```

**3. Implement service** (`service.py`):
```python
class CombatService(GameSystem):
    def __init__(self, combat_repo, military_repo, resolver):
        self.combat_repo = combat_repo
        self.military_repo = military_repo
        self.resolver = resolver
    
    def resolve_combat(self, attacker_id: int, defender_id: int) -> BattleResult:
        attacker = self.military_repo.get(attacker_id)
        defender = self.military_repo.get(defender_id)
        
        # Use resolver algorithm
        result = self.resolver.calculate_outcome(attacker, defender)
        
        # Apply casualties
        attacker.soldiers -= result.attacker_casualties
        defender.soldiers -= result.defender_casualties
        
        # Persist updates
        self.military_repo.update(attacker)
        self.military_repo.update(defender)
        self.combat_repo.create(result)
        
        return result
```

**4. Wire into orchestrator** (`orchestration/campaign.py`):
```python
class CampaignOrchestrator:
    def __init__(self, kingdom_svc, military_svc, combat_svc):  # Add combat_svc
        self.services = {
            'kingdom': kingdom_svc,
            'military': military_svc,
            'combat': combat_svc,
        }
    
    def advance_turn(self):
        self.services['kingdom'].advance_kingdom_turn(1)
        self.services['military'].update_all_units()
        self.services['combat'].process_scheduled_battles()  # NEW
        self.services['events'].log_turn()
```

**5. (Optional) Add export** (`export/combat_results_generator.py`):
```python
class CombatResultsGenerator(SheetGenerator):
    def __init__(self, workbook, style_manager, combat_repo):
        super().__init__(workbook, style_manager)
        self.combat_repo = combat_repo
    
    def generate(self):
        ws = self.wb.create_sheet("Battle Log")
        results = self.combat_repo.list_all()
        # ... format and append battle results
```

**6. Update factory** (`export/workbook_factory.py`):
```python
generators = [
    DashboardGenerator(...),
    # ... existing generators ...
    CombatResultsGenerator(wb, styles, self.repos['combat']),  # NEW
]
```

**Result**: Combat system added without modifying existing domain code. Clean separation of concerns.

---

## Database Schema Overview

### Tables (SQLite)
```sql
-- Kingdom
CREATE TABLE kingdom (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    ruler TEXT,
    population INTEGER,
    treasury_silver INTEGER,
    monthly_income INTEGER,
    monthly_expenses INTEGER,
    morale_percentage INTEGER,
    created_at TIMESTAMP
);

-- Provinces
CREATE TABLE province (
    id INTEGER PRIMARY KEY,
    kingdom_id INTEGER,
    name TEXT,
    population INTEGER,
    fort_level INTEGER,
    food_stored INTEGER,
    monthly_tax INTEGER,
    loyalty_percentage INTEGER,
    garrison_size INTEGER,
    governor TEXT,
    FOREIGN KEY (kingdom_id) REFERENCES kingdom(id)
);

-- Units
CREATE TABLE unit (
    id INTEGER PRIMARY KEY,
    kingdom_id INTEGER,
    name TEXT,
    type TEXT,
    soldiers INTEGER,
    veterans INTEGER,
    morale_percentage INTEGER,
    fatigue_percentage INTEGER,
    armor TEXT,
    location_id INTEGER,
    commander_id INTEGER,
    FOREIGN KEY (kingdom_id) REFERENCES kingdom(id),
    FOREIGN KEY (location_id) REFERENCES province(id),
    FOREIGN KEY (commander_id) REFERENCES commander(id)
);

-- Commanders
CREATE TABLE commander (
    id INTEGER PRIMARY KEY,
    kingdom_id INTEGER,
    name TEXT,
    role TEXT,
    leadership_skill INTEGER,
    tactics_skill INTEGER,
    logistics_skill INTEGER,
    loyalty_percentage INTEGER,
    status TEXT,
    traits TEXT,
    FOREIGN KEY (kingdom_id) REFERENCES kingdom(id)
);

-- Events (audit log)
CREATE TABLE event (
    id INTEGER PRIMARY KEY,
    turn INTEGER,
    category TEXT,
    description TEXT,
    impact TEXT,
    created_at TIMESTAMP
);
```

---

## Recommended Dependencies

```txt
openpyxl==3.10.5          # Excel generation
pydantic==2.0+             # Data validation & schemas
click==8.1+                # CLI (optional, for future features)
pytest==7.0+               # Testing
python-dotenv==1.0+        # Environment config (optional)
```

Install with:
```bash
pip install -r requirements.txt
```

---

## Testing Strategy

### Phase 4 — Start Here (Integration Test First)

Create `tests/test_export_parity.py` **before** implementing generators. Minimum assertions:
1. Sheet names match monolith
2. Row counts per sheet match monolith
3. (Phase 6) Key cell values and formulas match monolith

This is the primary safety net for the export refactor.

### Unit Tests
Test each domain in isolation:
- ✓ `test_phase2_domains.py`: Domain models and services (exists)
- ✓ `test_phase3_persistence.py`: Config loading and DB (exists)
- `test_kingdom.py`: Kingdom state transitions, silver transactions (Phase 6)
- `test_military.py`: Unit morale decay, fatigue calculation (Phase 6)

### Integration Tests
Test cross-domain interactions:
- `test_export_parity.py`: Generated Excel matches monolith (**Phase 4 — priority**)
- `test_turn_advancement.py`: Full turn cycle (post–Phase 6)
- `test_campaign_orchestration.py`: All services coordinate (post–Phase 6)

### Example:
```python
def test_kingdom_silver_transaction():
    """Kingdom cannot spend more silver than it has"""
    kingdom = Kingdom(name="Test", treasury_silver=1000)
    
    with pytest.raises(ResourceError):
        kingdom.spend_silver(2000)
    
    assert kingdom.treasury_silver == 1000  # Unchanged
```

---

## Phase 7: Turn Simulation

**Goal**: Replace the post-Phase 6 turn stub with a deterministic monthly advancement loop.

- [x] `CampaignOrchestrator.advance_turn()` executes without errors
- [x] Global `GameState` advances turn/month/year
- [x] Kingdom treasury applies monthly income minus expenses
- [x] Logistics resources apply production minus consumption
- [x] `GameState.save_checkpoint()` / `load_checkpoint()` round trip JSON state
- [x] Persist advanced turn state back to SQLite
- [x] Persist turn summaries from event and audit logs
- [ ] Add richer domain systems to each turn: diplomacy, combat, events
- [ ] Add interactive CLI turn controls

## Historical Next Steps After Phase 7 (Superseded)

1. **Diplomacy Engine**: Add NPC faction behavior, opinion shifts, treaty mechanics
2. **Combat System**: Full turn-based combat with unit matchups, morale effects
3. **Event System**: Dynamic events (raids, natural disasters, diplomatic crises)
4. **Persistence**: Persist full mutable game state to SQLite/file checkpoints
5. **CLI**: Interactive command-line interface for campaign control
6. **Visualization**: Web dashboard or ASCII map for campaign map

---

## Decisions Rationale

| Decision | Why |
|----------|-----|
| **Domain-Driven Design** | Each game system (Kingdom, Army, etc.) is isolated. Enables parallel development, easy to test, hard to break accidentally. |
| **JSON + SQLite** | JSON = human-editable configs (non-programmers can create campaigns). SQLite = queryable, persistent runtime state. Best of both worlds. |
| **Repository Pattern** | Generic CRUD base class reduces boilerplate across 6 domains. Easier to switch databases later if needed. |
| **Factory Pattern (Sheets)** | Each generator depends only on its domain. Adding a new sheet = new generator class. No ripple effects. |
| **Service Layer** | Business logic separated from data access. Easier to unit test, easier to reason about. |
| **Validation Service** | Centralized rules prevent invalid states. Fails fast. Clear audit trail. |
| **Placeholder Interfaces** | Combat system designed before implementation so the rest of the code is ready to integrate it. |

---

## Common Pitfalls & How to Avoid Them

| Pitfall | Solution |
|---------|----------|
| **Circular imports** | Keep `models.py` import-light. Put shared constants in `core/constants.py`. |
| **God objects** | Each service has a single responsibility. If a service does too much, split it. |
| **Hardcoded data** | All data in JSON configs. If you see a string in a `.py` file, it should be in `constants.py`. |
| **Database without schema** | Define schema upfront. Use migrations from day one. |
| **No validation** | Validate at load time (Pydantic), before mutations (ValidationService), and after turn (CampaignOrchestrator). |
| **Tightly coupled tests** | Test each domain in isolation. Mock repositories for service tests. |
| **Missing error handling** | Custom exceptions for each error category. Log everything. |
| **Deleting monolith too early** | Keep `campaign_engine_initialiser.py` until `test_export_parity.py` passes with full cell-level comparison. |

---

## Progress Tracking

Use this checklist to track completion:

### Phase 1: Foundation ✓ Complete
- [x] `src/warfare_simulation/core/base.py` created with abstract classes
- [x] `core/constants.py` with all enums
- [x] `core/exceptions.py` with custom exception classes
- [x] `core/logger.py` with logging setup
- [x] `core/validation.py` with ValidationService
- [x] All imports work without errors

### Phase 2: Domains ✓ Complete
- [x] `domain/kingdom/` with models, repository, service
- [x] `domain/geography/` with models, repository, service
- [x] `domain/military/` with models, repository, service
- [x] `domain/diplomacy/` with models, repository, service
- [x] `domain/logistics/` with models, repository, service
- [x] `domain/events/` with models, repository, service

### Phase 3: Data & Persistence ✓ Complete
- [x] `config/data/` with all JSON files
- [x] `config/schema.py` with Pydantic models
- [x] `config/config.py` with ConfigManager
- [x] `persistence/database.py` with schema
- [x] `persistence/repository.py` with generic base
- [x] `persistence/campaign_bootstrap.py` with JSON→SQLite seeding
- [x] Repository `hydrate()` for loading from SQLite
- [x] Data loads without validation errors
- [x] `test_phase3_persistence.py` includes seeding + hydration tests

### Phase 4: Export ✓ Complete
- [x] `tests/test_export_parity.py` created (stub OK to start)
- [x] `export/styles.py` with StyleManager
- [x] `export/base_generator.py` with SheetGenerator
- [x] Individual generators for all 8 sheets
- [x] `export/workbook_factory.py` orchestrating all
- [x] End-to-end: JSON → SQLite → export works
- [x] Generated Excel matches original output (sheet names + row counts)

### Phase 5: Application (Thin Slice)
- [x] `orchestration/campaign.py` with export-only `CampaignOrchestrator`
- [x] `orchestration/game_state.py` with stub `GameState`
- [x] `app.py` with minimal `WarfareSimulationApp` (init + export)
- [x] `main.py` entry point
- [x] `requirements.txt` and `pyproject.toml` (exist)
- [x] `.gitignore` configured (exists)

### Phase 6: Verification & Docs
- [x] Unit tests for key domains (`test_phase2_domains.py`)
- [x] Persistence tests (`test_phase3_persistence.py`)
- [x] `test_export_parity.py` full cell-level parity
- [ ] Monolith retired after parity verified
- [ ] `docs/ARCHITECTURE.md` written
- [ ] `docs/EXTENDING.md` with Combat example
- [ ] `README.md` updated
- [ ] All checkpoints pass

---

## Conclusion

Phases 1–3 built the foundation. **Phase 4 is the critical path** — prove the modular export matches `campaign_engine_initialiser.py`, guarded by `test_export_parity.py`. Phase 5 wires a thin runnable app; Phase 6 hardens tests, documents the architecture, and retires the monolith. Turn simulation, CLI, and combat come after Phase 6.

**Start Phase 4 with the integration test, then implement generators sheet-by-sheet against the monolith reference.**
