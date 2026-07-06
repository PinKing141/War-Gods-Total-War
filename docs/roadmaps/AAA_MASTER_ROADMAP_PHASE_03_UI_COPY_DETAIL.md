# Phase 3 UI copy and SPAG detail

This phase prevents debug speech and awkward labels from spreading through the whole project.

## 3A. Player-facing copy audit

Audit:

```text
province inspector
realm inspector
war inspector
character inspector
chronicle/events
monthly recap
world panel
map hover text
tooltips
scenario screens
validation banners
```

Closing gate:

```text
Normal UI has no question labels, no raw variable language and no spreadsheet-style debug labels.
```

## 3B. Label replacement pass

Replace:

```text
Why it matters -> Strategic Value
Likely Goal -> Goal
Primary Goal -> Goal
Secondary Goal -> Secondary Aim
Economy pressure -> Economy
Conflict pressure -> Conflict
Institution pressure -> Institutions
River data -> Rivers
Current status -> Status
```

Closing gate:

```text
All common labels are title case, concise and grand-strategy appropriate.
```

## 3C. Debug-only separation

Debug-only terms:

```text
province_id
faction_id
RGB
map index
seeded values
AI score
source CSV row
validation reference
```

Closing gate:

```text
Raw IDs and internal scores only appear in debug or validation views.
```

## 3D. Event text polish

Bad:

```text
Faction declares due to seeded risk and current chance.
```

Good:

```text
The Crown of Rov Halem goes to war to press its claim on Halem Bridge.
```

Closing gate:

```text
Major events explain visible causes in readable player-facing language.
```
