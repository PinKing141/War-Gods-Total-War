# Project Structure

This repository is organized to separate engine code, runnable scripts, and planning documents.

## Top Level Layout

```text
.
├── docs/
│   ├── roadmaps/          # All planning and execution roadmaps
│   ├── ARCHITECTURE.md    # System architecture overview
│   ├── API.md             # Public API reference
│   ├── EXTENDING.md       # Guide for adding new systems
│   └── RULES_FRAMEWORK.md # Observer-simulation rules contract
├── scripts/               # Preferred runnable entrypoints
├── src/                   # Python package source
├── tests/                 # Automated tests
├── campaign_engine_initialiser.py  # Deprecated legacy export reference
└── run_new_export.py      # Compatibility wrapper -> scripts/run_export.py
```

## Folder Roles

- `docs/roadmaps/`: Read here when deciding what to build next.
- `docs/`: Read here when you need rules, architecture, or extension guidance.
- `scripts/`: Use these to run the project manually without digging into package internals.
- `src/warfare_simulation/`: The Python campaign engine package.
- `tests/`: Regression coverage for persistence, export, orchestration, and runtime behavior.

## Roadmap Rule

If a file is a roadmap, backlog, milestone plan, or execution-order document, it belongs in `docs/roadmaps/`.

## Script Rule

If a file exists only to launch or export the project, it belongs in `scripts/`. Root-level wrappers may stay only for compatibility.
