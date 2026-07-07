# Current next order

This is the order to follow right now.

```text
1. Phase 2: Data validation and technical quality — DONE
2. Phase 3: UI copy, SPAG and presentation language — DONE
3. Phase 4: Data architecture and scenario foundation — DONE
4. Phase 5: World Scale Gate 1 — 16-20 serious powers — CURRENT
5. Phase 6: Core simulation depth Phase 2
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
```

## Current Phase 5 substep

```text
Phase 5-C: Regional balance pass — NEXT
```
