# UI copy replacement table

Use this as the direct replacement table for the SPAG and player-facing copy pass.

## Hard removals from normal UI

These phrases should not appear in normal player-facing UI:

```text
mapped placeholder
not active in the war loop
world-map province
seeded risk
current chance
raw AI score
intent reason
source CSV
province_id
faction_id
RGB
map index
```

They may appear only in debug modes.

## Label replacements

```text
Why it matters -> Strategic Value
Likely Goal -> Goal
Primary Goal -> Goal
Secondary Goal -> Secondary Aim
Current status -> Status
Economy pressure -> Economy
Conflict pressure -> Conflict
Institution pressure -> Institutions
Military pressure -> Army
Tax pressure -> Taxation
Religious pressure -> Faith
Cultural pressure -> Culture
Court pressure -> Court
Succession pressure -> Succession
River data -> Rivers
Mapped provinces -> Provinces
Observer state -> Status
Simulation -> remove unless in debug
AI intent -> Intent
Intent reason -> Reason
Current chance -> Chance, debug only
Seeded risk -> Risk, debug only
```

## Better panel words

Use these as standard nouns:

```text
Strategic Value
Notable Features
Status
Goal
Ruler
Heir
House
Dynasty
Treasury
Manpower
Army Strength
Economy
Unrest
Risk
Relations
Treaties
Claims
Wars
Sieges
Battles
Casualties
Rivers
Ports
Roads
Faith
Culture
Lands
```

## Sentence cleanup rules

```text
Use short labels.
Do not use questions as labels.
Do not expose raw IDs unless debug mode is on.
Do not expose snake_case.
Do not expose camelCase.
Do not expose AI scoring or probability language in normal UI.
Do not use design-note language in normal UI.
```

## Event text examples

Bad:

```text
Intent: Crown sees usable claim; seeded risk 44 current chance 2.7 percent.
```

Good:

```text
The Crown of Rov Halem goes to war to press its claim on Halem Bridge.
```

Bad:

```text
This faction is a mapped placeholder and is not active in the war loop.
```

Good:

```text
This realm is not active in the current scenario.
```

Bad:

```text
Why it matters: high strategic value, river crossing, claim count 2.
```

Good:

```text
Strategic Value: River crossing, strong fort, contested claims.
```
