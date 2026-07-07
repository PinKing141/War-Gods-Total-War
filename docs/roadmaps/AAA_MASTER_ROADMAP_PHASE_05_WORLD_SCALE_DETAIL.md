# Phase 5 World Scale Gate 1 detail

This is the first safe country expansion gate.

## 5A. Faction tier support — DONE

Add tiers:

```text
Tier 1 = great power / major realm
Tier 2 = regional power
Tier 3 = minor state / city-state / march / hold
Tier 4 = background or non-state actor
```

Closing gate:

```text
Every faction has a valid tier and the tier affects simulation depth safely.
```

Completed with:

```text
- tier field added to authored seed factions
- tier exported into docs/assets/data.js
- tier preserved in SQLite seed and runtime faction rows
- tier validation added to static and runtime checks
- polished tier labels shown in world and realm UI
- faction tier gently affects war-declaration ambition
- no new factions or provinces added
- full test suite passing
```

## 5B. Add 8-12 new major or regional powers — DONE

Potential slots:

```text
Lanter Sea naval league
northern highland realm
southern salt-road realm
eastern river confederation
western marcher realm
great religious protectorate
large forest court
large stone hold
orc war confederation
mage-law state
wealthy free-city league
nomad successor confederation
```

Closing gate:

```text
World has 16-20 serious powers, each with a distinct role and valid data.
```

Completed with:

```text
- 8 new regional powers added to the authored seed faction CSV
- expanded world now has 16 serious powers
- every new power has valid tier, culture, faith, government, role and pressure
- web seed export supports presentation style for every new power
- default frontier scenario includes the expanded active faction list
- validation tests assert the 16-20 faction gate
- no new provinces, terrain masks, river art or map cosmetics added
- 25-year observer validation passes
- full test suite passing
```

## 5C. Regional balance pass — DONE

Run 25-50 years and check:

```text
snowballing
no-war dead world
total collapse
lack of regional tension
lack of cross-region contact
```

Closing gate:

```text
50-year run produces believable politics without total chaos or total silence.
```

Completed with:

```text
- added rulers, claims and relationship pressure hooks for the 8 new powers
- regenerated the web seed so the expanded powers participate in the observer sim
- added scripts/validate_observer_balance.py as a repeatable 50-year multi-seed balance gate
- balance gate checks no-war silence, unresolved chaos, snowballing, collapse and passive expanded powers
- tested seeds 101, 202, 303, 404 and 505 for 50 years each
- all balance samples passed with resolved wars, restored powers, active holders and chronicle activity
- no new provinces, terrain masks, river art or map cosmetics added
- 25-year observer validation passes
- full test suite passing
```

## Phase 5 closing gate — DONE

```text
World has 16-20 serious powers, each power has a distinct role and valid data,
and 50-year balance samples avoid total chaos, total silence and runaway snowballing.
```
