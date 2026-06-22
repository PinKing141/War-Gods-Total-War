# Roadmap Reading Order

This folder is the single place to read and manage project roadmaps.

## Read In This Order

1. `../RULES_FRAMEWORK.md`
   Read first. This is the contract for how the observer simulation is allowed to work.

2. `MODULARIZATION_ROADMAP.md`
   Read second. This is the technical implementation roadmap and historical record of what foundation work already exists.

3. `LIVING_CHRONICLE_ROADMAP.md`
   Read third. This is the product roadmap for the autonomous observer-simulation direction.

4. `CONTENT_ROADMAP.md`
   Read last. This is the future content-expansion backlog and should only drive work after the simulation loop is stable.

## How To Use These Roadmaps

- Use `../RULES_FRAMEWORK.md` to reject ideas that break the observer-sim contract.
- Use `MODULARIZATION_ROADMAP.md` to understand what the codebase already supports and what technical phases still need implementation.
- Use `LIVING_CHRONICLE_ROADMAP.md` to decide the next major product milestone.
- Use `CONTENT_ROADMAP.md` only after a system already exists and needs more factions, events, histories, or scenarios.

## Linear Build Order

1. Stabilize the current runtime foundation: persistence, UI shell, daily clock, export, and restart safety.
2. Build the simulation loop: daily, weekly, monthly, seasonal, and yearly pulse ordering.
3. Add autonomous faction intent and constraint resolution.
4. Expand causality and explainability: audit logs, event logs, summaries, and chronicle generation.
5. Deepen systemic simulation: logistics, movement, diplomacy pressure, collapse, succession, war, and recovery.
6. Add content only after the above layers produce readable history on their own.

## Current Practical Priority

The practical execution path is:

1. Finish the remaining Phase 8 observer-pivot work in `MODULARIZATION_ROADMAP.md`.
2. Start the MVP simulation milestones in `LIVING_CHRONICLE_ROADMAP.md`.
3. Keep `CONTENT_ROADMAP.md` as parked future work until the simulation loop and chronicle layers are trustworthy.
