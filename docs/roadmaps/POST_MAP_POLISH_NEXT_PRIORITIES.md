# Post-map-polish next priorities

This roadmap intentionally pauses map beauty work.

## Decision

The map is good enough for development. Rivers and trees can stay as data/debug assets for now. Do not spend more core development time trying to make final river art, tree art, or hand-painted terrain polish.

```text
map beauty = paused
map function = required
simulation/game loop = priority
```

## Why

The project is at risk of getting stuck in asset polish before the actual game/simulation is strong enough. A beautiful map is useful, but it does not matter if the world does not produce interesting history, readable wars, meaningful factions, and clear observer feedback.

## What to stop doing for now

```text
final river art
final tree bitmap polish
perfect terrain masks
more generated visual previews
major folder migrations
new map cosmetics
```

Keep all generated assets and manifests, but treat them as future material.

## What still matters on the map

Only these map tasks are important right now:

```text
province clicking works
province panels show useful data
army markers are readable
wars and sieges are visible
realm ownership/tint is readable
map debug tools do not break normal play
rivers/trees can exist as data without needing final visuals
```

## Priority 1: playable observer loop

The main screen should answer these questions without opening raw files:

```text
who controls this province?
why is this province important?
who is at war?
where are armies moving?
what changed this month?
what changed this year?
who is winning and why?
what is about to collapse?
```

Tasks:

```text
improve province inspector
improve realm/faction inspector
improve war inspector
make army movement and battle outcomes easier to read
show monthly/yearly summaries clearly
add "why this happened" explanations to major events
```

## Priority 2: simulation depth

Improve the actual world systems before visuals.

Focus systems:

```text
war goals
army supply
terrain movement cost
sieges
claims
faction AI priorities
internal politics
succession/death/rulers
economy and tax pressure
revolt risk
relations and alliances
```

The world should create interesting stories even if the map art is simple.

## Priority 3: data validation

Before adding more content, validate the current data.

Tasks:

```text
every province has valid controller
all faction IDs resolve
all army locations are valid province IDs
all adjacency links point to real provinces
all characters belong to valid factions/cultures/religions
all wars have valid attackers/defenders/goals
no negative population/garrison/economy values
no orphan generated map assets
```

## Priority 4: UX/readability

The observer needs better explanation.

Tasks:

```text
better tooltips
clearer event log filters
war summaries
realm summaries
province importance tags
army route/status display
battle aftermath cards
siege progress cards
```

## Priority 5: content expansion only after systems work

Do not add thousands of new provinces, names, traits, religions, rivers or trees just because they are cool.

Add content only when the sim can use it.

Good content next:

```text
more faction goals
more event templates
more war outcomes
more internal crisis types
more ruler personality effects
more province strategic traits
```

Bad content next:

```text
more cosmetic masks
more unused map layers
more unused name databases
more unused lore CSVs
```

## Current river/tree policy

```text
rivers = data/debug only for now
trees = generated first-pass asset, do later
terrain masks = keep, but do not polish further now
```

Rivers can still affect gameplay through province/tile data later, but visible CK-style river rendering should wait.

Trees should not block development. The generated tree bitmap pack is enough as a placeholder/future source.

## Immediate Codex task

```text
Pause map cosmetic work and move to observer gameplay clarity.

Tasks:
1. Do not add more terrain masks, river masks, or tree masks.
2. Keep existing map assets available but treat them as placeholders.
3. Audit the current observer loop.
4. Improve the province inspector so it clearly shows:
   - controller
   - terrain
   - population
   - garrison
   - fort level
   - economy/value
   - current war/siege/occupation status
   - strategic features such as river/floodplain/crossing if data exists
5. Improve the faction/realm inspector so it clearly shows:
   - ruler
   - held provinces
   - wars
   - army strength
   - economy pressure
   - instability/crisis risks
6. Improve the war inspector so it clearly shows:
   - attackers
   - defenders
   - war goal
   - battles
   - sieges
   - casualties
   - who is winning and why
7. Add a monthly recap panel if one does not already exist.
8. Add validation tests for province IDs, faction IDs, army locations, adjacency, wars and characters.
```
