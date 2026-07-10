# Phases 9-12 politics and society detail

## Phase 9. Courts, social groups, law and justice

Subphases:

```text
9A Court and office system
9B Social groups inside provinces
9C Law, crime and justice
```

Closing gate:

```text
Realms are no longer only rulers and armies. Courts, offices, social groups and law affect succession, taxation, unrest and legitimacy.
```

## Phase 9A. Court and office system — DONE

Completed with:

```text
- runtime court state added to factions
- office slots added for ruler, heir, chancellor, marshal, steward, spymaster, court mage, high priest, captain of guard, governor and regent
- offices are assigned to existing living characters where possible
- office effectiveness is derived from character prestige, reputation, legitimacy, role, traits, mage status and relevant military record
- offices affect internal politics, income and AI priorities at a first-pass level
- courts refresh during monthly simulation and after character death or succession
- realm inspector shows court stability and office holders
- character inspector shows offices held by the character
- JS and Python validation catch missing court state, missing/invalid offices, broken holders, wrong-faction holders, dead holders and invalid effectiveness
- tests cover office assignment, inspector wiring, office effects and broken validation state
- 25-year observer validation passing
- full test suite passing
```

## Phase 9B. Social groups inside provinces — DONE

Completed with:

```text
- province society state added for nobles, clergy, merchants, peasants, craftsmen, soldiers, mages, scholars, minorities, tribes, foreign settlers, refugees and urban poor
- each social group tracks size, loyalty, unrest, needs, wealth and influence
- social groups affect province tax, recruitment, unrest, culture tension and faith tension
- monthly province society drift responds to devastation, occupation, siege pressure, tax burden, prosperity and internal politics
- province instability now includes social unrest causes
- province inspector shows readable Society summaries with social pressure, restive groups and dominant groups
- JS and Python validation catch missing society state, missing groups, invalid groups, invalid values and missing needs text
- tests cover social state creation, UI wiring, mechanical effects and broken validation state
- 25-year observer validation passing
- full test suite passing
```

## Phase 10. Historical memory and living chronicle

Subphases:

```text
10A Memory object system
10B Grievances and loyalties
10C Chronicle generation
10D Province/faction/character history panels
```

Closing gate:

```text
The world remembers major events, uses those memories in future decisions and displays readable history to the player.
```

## Phase 11. Culture, faith, identity and sects

Subphases:

```text
11A Culture system
11B Faith and sect system
11C Identity conflict and integration
```

Closing gate:

```text
Culture and faith affect unrest, diplomacy, marriage, recruitment, legitimacy, institutions and war goals.
```

## Phase 12. Institutions and power structures

Subphases:

```text
12A Institution schema
12B Institution actions
12C Institution memory and rivalries
```

Closing gate:

```text
Power exists outside rulers. Institutions can support, oppose, fund, demand and remember.
```
