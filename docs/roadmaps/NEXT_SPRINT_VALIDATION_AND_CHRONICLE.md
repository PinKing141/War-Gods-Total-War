# Next sprint: validation and chronicle clarity

This is the next sprint after old map decommission and the first observer inspector upgrades.

## Current status

The old map has been removed from the normal load path. The app now loads `map_base.js` and `map_layers.js` instead of `map.js`, and the old procedural map is only available through the optional `?oldMap` debug path.

The observer panels have started to show richer province, faction and war information.

## Decision

Do not return to map cosmetics yet.

The next sprint is:

```text
1. validate the world data
2. improve monthly/yearly chronicle readability
3. make wars easier to follow over time
4. add smoke tests so map/sim changes do not silently break the world
```

## Priority 1: validation tests

Add validation tests before adding more simulation depth.

Tests should check:

```text
all province IDs are unique
all faction IDs are unique
all province controllers exist
all army locations are valid province IDs
all adjacency edges point to valid provinces
all wars have valid attackers and defenders
all war goals target valid provinces
all characters belong to valid factions
all rulers belong to their factions
all heirs/parents/children resolve when referenced
all province values are non-negative
all army sizes are non-negative
all garrisons/populations are non-negative
all river feature province references resolve if river data exists
```

Suggested file targets:

```text
tests/data_validation/test_web_seed_integrity.py
tests/data_validation/test_map_integrity.py
tests/data_validation/test_observer_runtime_integrity.py
```

## Priority 2: monthly recap panel

The observer needs summaries that make the world readable over time.

Add a monthly recap panel or improve the existing chronicle feed so each month can answer:

```text
what wars started?
what wars ended?
what battles happened?
what sieges started or progressed?
which provinces changed hands?
which rulers died or inherited?
which realms are rising?
which realms are collapsing?
what should the observer watch next?
```

## Priority 3: yearly recap

A yearly recap should feel like a history book entry.

It should summarize:

```text
largest war
bloodiest battle
most successful realm
most endangered realm
largest territorial change
major deaths/successions
major rebellions/crises if present
map/world trend for the year
```

## Priority 4: war timeline clarity

Wars should not only show their current state. They should show how they got there.

Add or improve:

```text
war timeline entries
battle list
siege list
occupation changes
casualty totals
turning point explanation
current reason one side is winning
```

## Priority 5: simulation guardrails

Add guardrails that prevent the simulation from drifting into nonsense.

Examples:

```text
armies cannot move to invalid provinces
wars cannot start against missing factions
sieges cannot target missing provinces
dead commanders cannot lead armies unless explicitly allowed by a bug test
landless factions should be marked inactive or special-case handled
no negative manpower/treasury/army sizes unless intentionally supported
```

## Do not do in this sprint

```text
new river masks
new tree masks
new terrain masks
final map art
full public map editor
huge lore database expansion
major folder migration
```

## Immediate Codex task

```text
Start the next sprint: validation and chronicle clarity.

Tasks:
1. Add data validation tests for provinces, factions, armies, adjacency, wars, characters, rulers and river feature references.
2. Add a runtime smoke test that can advance the observer simulation for at least 12 months without invalid IDs or negative critical values.
3. Improve or add a monthly recap panel/feed section that summarizes wars, battles, sieges, occupations, ruler changes and realms to watch.
4. Add a yearly recap summary if the date reaches a new year.
5. Improve the war inspector timeline so battles, sieges, casualties and occupation changes are easy to follow.
6. Add clear "why this matters" text to monthly/yearly recaps.
7. Do not add any new river, tree or terrain cosmetic work.
```
