# Current next order

This is the order to follow right now.

```text
1. Phase 2: Data validation and technical quality — DONE
2. Phase 3: UI copy, SPAG and presentation language — DONE
3. Phase 4: Data architecture and scenario foundation — DONE
4. Phase 5: World Scale Gate 1 — 16-20 serious powers — DONE
5. Phase 6: Core simulation depth Phase 2 — CURRENT
```

## Why this order

```text
Validation prevents broken content.
UI copy stops debug language spreading.
Data architecture gives content a clean home.
World Scale Gate 1 adds more major powers safely.
Core Simulation Depth then makes those powers behave properly.
```

## Completed gate notes

```text
Phase 2 closed with:
- shared observer validation helpers
- readable file/row/field failure output
- static seed and CSV checks
- runtime simulation self-checks
- bad-data regression tests
- CLI validation command
- 25-year smoke validation gate
- full test suite passing

Phase 3 closed with:
- normal observer labels cleaned up
- debug validation details hidden outside debug mode
- raw seeded probability wording removed from war causes
- player-facing war causes use readable Cause wording
- copy regression test for banned UI/debug phrases
- full test suite passing

Phase 4 closed with:
- current web seed, lore CSV, map CSV and river-feature data sources inventoried
- default scenario manifest added
- scenario ID/reference/path validation added
- default scenario validation tests added
- no new factions, provinces or map cosmetics added
- full test suite passing

Phase 5-A closed with:
- faction tiers added to existing seed factions
- tier export added to the web seed
- tier preserved in SQLite seed/runtime faction rows
- tier validation added to static and runtime checks
- polished tier labels shown in world and realm UI
- tier weight gently affects faction war ambition
- no new factions, provinces or map cosmetics added
- full test suite passing

Phase 5-B closed with:
- 8 new regional powers added to the authored seed faction CSV
- expanded world now has 16 serious powers
- every new power has valid tier, culture, faith, government, role and pressure
- web seed export supports presentation style for every new power
- default frontier scenario includes the expanded active faction list
- validation tests assert the 16-20 faction gate
- no new provinces, terrain masks, river art or map cosmetics added
- 25-year observer validation passing
- full test suite passing

Phase 5-C closed with:
- rulers, claims and relationship hooks added for the 8 new powers
- web seed regenerated so expanded powers participate in the observer sim
- repeatable 50-year multi-seed balance gate added
- balance gate checks no-war silence, unresolved chaos, snowballing, collapse and passive expanded powers
- seeds 101, 202, 303, 404 and 505 passed 50-year samples
- no new provinces, terrain masks, river art or map cosmetics added
- 25-year observer validation passing
- full test suite passing
```

## Current Phase 5 substep

```text
Phase 5: World Scale Gate 1 — DONE
```

## Current Phase 6 substep

```text
Phase 6-A: Faction AI priorities — DONE
Phase 6-B: Internal politics first pass — DONE
Phase 6-C: Revolts and instability — DONE
Phase 6-D: Succession and ruler death expansion — NEXT
```

## Phase 6 notes

```text
Phase 6-A closed with:
- live faction AI priority scoring added
- priorities consider faction profile, ruler traits, claims, relations, army strength, treasury, manpower, wars, exhaustion, strategic holdings, ports and passes
- war declaration chance now uses attacker priorities
- war cause text names the court priority behind major decisions
- realm inspector shows top priorities and reasons
- regression tests prove raider, trade, pass and faith archetypes score differently
- runtime stress shifts priorities toward survival and war avoidance
- 50-year balance validation passing
- 25-year observer validation passing
- full test suite passing

Phase 6-B closed with:
- internal politics state added to every runtime faction
- monthly updates track court tension, succession tension, army influence, tax burden, faith tension, culture tension, regional autonomy, noble loyalty, merchant loyalty, revolt risk and succession pressure
- internal politics responds to wars, deficits, exhaustion, occupations, sieges, manpower pressure, weak succession and realm structure
- internal state affects monthly income and war willingness
- realm inspector explains internal stability, revolt risk, succession pressure and stress causes
- validation covers missing, invalid and out-of-range internal politics state
- 50-year balance validation passing
- 25-year observer validation passing
- full test suite passing

Phase 6-C closed with:
- province instability scoring added from devastation, occupation, recent conquest, low garrison, internal politics, famine, weak ruler and foreign support
- revolt type selection added for peasant revolt, noble revolt, separatist revolt, religious uprising, pretender revolt, military coup and frontier independence
- revolts can start, spread, be suppressed or win as recorded runtime conflicts
- winning revolts can transfer province control to a strong claimant and create recent conquest pressure
- province inspector shows instability causes and active revolt progress
- realm inspector shows active revolt count
- validation covers broken revolt references and values
- 50-year balance validation passing
- 25-year observer validation passing
- full test suite passing
```
