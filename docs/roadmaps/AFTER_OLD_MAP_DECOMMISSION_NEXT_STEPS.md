# After old map decommission: next steps

This roadmap defines what comes after the old procedural map is removed from normal gameplay.

## Goal

Once the old map is decommissioned, stop map cosmetic work and move into game-readability and simulation quality.

```text
old map removed from normal gameplay
→ verify new map stability
→ improve observer UI clarity
→ deepen simulation systems
→ add validation tests
```

## Step 1: map stability gate

Before adding new systems, confirm the new layered map is stable.

Acceptance checks:

```text
main page loads without docs/assets/map.js
LayeredWorldMap is the only normal map implementation
province clicking works from the unique-RGB province map
pan/zoom/hover/click all work
province labels and realm labels still render
army and siege markers use correct province centers
sim.adjacency is populated from layered map adjacency
old procedural map appears only through optional debug fallback, if kept
```

If any of these fail, fix them before continuing.

## Step 2: freeze map cosmetics

Do not restart work on:

```text
river art
tree art
new masks
terrain polish
map frame cosmetics
province colour tuning
```

Existing map assets can stay, but they are placeholders until gameplay systems need them.

## Step 3: province inspector upgrade

The province panel should become the first major gameplay-readability upgrade.

It should show:

```text
province name
controller
occupier if occupied
terrain type
region
population
garrison
fort level
economy/value
resource
road/port/river/floodplain/crossing features if present
active siege status
nearby/standing armies
current war relevance
why this province matters
```

## Step 4: realm/faction inspector upgrade

The faction panel should clearly answer:

```text
who rules this faction?
how many provinces do they hold?
how strong are their armies?
who are they at war with?
what do they want?
what is their economy pressure?
are they unstable?
what crisis could happen next?
```

## Step 5: war inspector upgrade

The war panel should clearly show:

```text
war name
attackers
defenders
war goal
current target provinces
battles fought
sieges underway
casualties
occupation score
who is winning
why they are winning
what could change the war
```

## Step 6: monthly and yearly recap

The observer needs readable history summaries.

Add or improve:

```text
monthly recap
yearly recap
major wars summary
realm rise/fall summary
battle and siege highlights
political crisis summary
```

Each recap should explain what changed and why it matters.

## Step 7: data validation tests

Before more content expansion, add validation.

Tests should check:

```text
all province IDs resolve
all faction IDs resolve
all army locations are valid provinces
all adjacency links point to valid provinces
all wars have valid attackers and defenders
all characters belong to valid factions/cultures/religions
all province controllers exist
no negative population, garrison, economy or army size
no missing required CSV headers
```

## Step 8: simulation depth pass

After UI readability and validation, deepen the world systems.

Priority systems:

```text
war goals
army supply
movement cost by terrain
siege logic
faction AI intent
claims and legitimacy
internal politics
succession and ruler death
economy/tax pressure
revolt risk
alliances and relations
```

## Do not do yet

```text
full public map editor
final rivers
final trees
huge content database expansion
major folder migration
new art pipeline
```

## Immediate Codex task after old map decommission

```text
After decommissioning the old procedural map, run a stability and readability pass.

Tasks:
1. Verify the app loads without docs/assets/map.js.
2. Verify LayeredWorldMap is the only normal map implementation.
3. Verify province clicking, hover, pan and zoom still work.
4. Verify army/siege markers use province centers from the layered province definitions.
5. Verify sim.adjacency is populated from the layered map.
6. Improve the province inspector with controller, terrain, region, pop, garrison, fort, resource, value, occupation, siege and army information.
7. Improve the faction/realm inspector with ruler, held provinces, wars, army strength, economy pressure and instability/crisis risks.
8. Improve the war inspector with attackers, defenders, goal, battles, sieges, casualties, occupation score and who is winning/why.
9. Add validation tests for province IDs, faction IDs, army locations, adjacency, wars and characters.
10. Do not add any new river, tree or terrain cosmetic work.
```
