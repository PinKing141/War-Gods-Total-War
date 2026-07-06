# UI copy, SPAG and presentation pass

## Purpose

The UI should read like a finished historical grand-strategy game, not like a debug screen or developer console.

This pass removes awkward labels, internal wording, inconsistent casing, long explanatory phrases and system-language that should not be visible to the player.

## Core rule

Player-facing UI must use polished game language.

```text
internal system wording = allowed in code, debug tools and validation reports
player-facing wording = clear, short, formal and immersive
```

## Problem examples

Avoid UI labels like:

```text
Why it matters
Likely Goal
Economy pressure
Institution pressure
Conflict pressure
Simulation
world-map province
mapped placeholder
not active in the war loop
intent reason
current chance
seeded risk
river data
```

These sound like debug or design notes, not final game UI.

## Preferred label style

Use short title-case labels.

```text
Goal
Status
Economy
Treasury
Army
Wars
Claims
Ruler
Heir
House
Dynasty
Faith
Culture
Lands
Strength
Unrest
Risk
Strategic Value
Notable Features
Relations
Treaties
Sieges
Battles
Casualties
```

## Specific replacements

```text
Why it matters -> Strategic Value
Likely Goal -> Goal
Primary Goal -> Goal
Secondary Goal -> Secondary Aim
Economy pressure -> Economy
Conflict pressure -> Conflict
Institution pressure -> Institutions
Faction AI intent -> Intent
Intent reason -> Reason
Current status -> Status
Current chance -> Chance
Seeded risk -> Risk
River data -> Rivers
Mapped provinces -> Provinces
Observer state -> Status
mapped placeholder -> remove from player UI
not active in the war loop -> remove from player UI
Simulation -> remove from normal player UI
world-map province -> remove from normal player UI
```

If a label still sounds like a spreadsheet or debug variable, rewrite it.

## Tone target

The tone should feel closer to CK-style grand-strategy UI:

```text
short labels
clear nouns
formal but readable phrasing
no developer jokes
no debug explanations
no raw variable names
no snake_case
no camelCase
no overly long labels
no questions as panel labels
```

## Casing rules

Use consistent title case for panel labels.

Good:

```text
Strategic Value
Active Siege
War Goal
Army Strength
Treasury
Held Provinces
```

Bad:

```text
why it matters
Likely goal
Economy pressure
current war relevance
armyStrength
river_trade_value
```

## Event text rules

Event text can be more flavourful than labels, but it must still be readable.

Good:

```text
The Crown of Rov Halem declares war on the Red Bog Hearth League to press its claim on Halem Bridge.
```

Bad:

```text
The Crown of Rov Halem declares war due to seeded risk 42 current chance 3.4 percent.
```

Internal scoring can exist, but it belongs in debug mode only.

## Debug separation

Create a strict split between:

```text
normal UI
advanced tooltip
map debug mode
simulation debug mode
validation output
```

Normal UI should never show raw system wording.

Debug mode may show:

```text
province_id
faction_id
RGB
map index
seeded risk
AI score
intent reason
source CSV row
validation reference
```

## Panel audit list

Audit these player-facing areas:

```text
province inspector
realm/faction inspector
war inspector
character inspector
chronicle/events
monthly recap
world panel
tooltips
map hover text
faction strip titles
scenario screens
validation banners
```

## Province panel target labels

```text
Controller
Status
Population
Garrison
Fort Level
Roads
Harbour
Mana Site
Devastation
Biome
Terrain
Economy
Region
Strategic Value
Rivers
Armies
Claims
```

## Realm panel target labels

```text
Ruler
Heir
House
Dynasty
Provinces
Army Strength
Treasury
Manpower
Wars
Treaties
Claims
Relations
Economy
Unrest
Risks
Notable Figures
```

## War panel target labels

```text
Attackers
Defenders
War Goal
Targets
War Score
Occupation
Army Strength
Exhaustion
Battles
Casualties
Active Sieges
Outcome
Peace Terms
```

## Character panel target labels

```text
House
Dynasty
Age
Faith
Culture
Species
Role
Traits
Ambition
Fear
Family
Spouse
Children
Rivals
Friends
Claims
Titles
Reputation
Military Record
Memories
Current Scheme
```

## Copy quality checklist

Before accepting the UI pass, check:

```text
no snake_case visible to player
no camelCase visible to player
no debug placeholders visible in normal UI
no labels written as questions
no awkward long labels
no unexplained internal terms
consistent title case
short labels where possible
all generated event text reads naturally
all UI text could plausibly appear in a grand-strategy game
```

## Codex task

```text
Run a full UI copy, SPAG and presentation pass.

Tasks:
1. Audit all player-facing text in docs/assets/ui.js, docs/assets/main.js, docs/index.html and related UI files.
2. Remove debug/developer wording from normal UI.
3. Keep technical details only in explicit debug modes.
4. Replace awkward labels:
   - Why it matters -> Strategic Value
   - Likely Goal -> Goal
   - Economy pressure -> Economy
   - Conflict pressure -> Conflict
   - Institution pressure -> Institutions
   - River data -> Rivers
   - Current status -> Status
5. Remove player-facing phrases such as:
   - mapped placeholder
   - not active in the war loop
   - world-map province
   - seeded risk
   - current chance
6. Use consistent title case for UI labels.
7. Convert snake_case and raw IDs into readable names before display.
8. Keep event text natural and immersive.
9. Add a simple copy quality checklist or test if practical.
10. Do not change simulation logic unless needed to separate debug text from player text.
```
