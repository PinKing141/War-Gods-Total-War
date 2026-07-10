# Current next order

This is the order to follow right now.

```text
1. Phase 2: Data validation and technical quality — DONE
2. Phase 3: UI copy, SPAG and presentation language — DONE
3. Phase 4: Data architecture and scenario foundation — DONE
4. Phase 5: World Scale Gate 1 — 16-20 serious powers — DONE
5. Phase 6: Core simulation depth Phase 2 — DONE
6. Phase 7: Character life, traits, relationships and personal ambition — DONE
7. Phase 8: Family trees, houses, dynasties and inheritance — DONE
8. Phase 9: Courts, social groups, law and justice — CURRENT
```

## Why this order

```text
Validation prevents broken content.
UI copy stops debug language spreading.
Data architecture gives content a clean home.
World Scale Gate 1 adds more major powers safely.
Core Simulation Depth then makes those powers behave properly.
Character life makes rulers, commanders and heirs personal.
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
Phase 6-D: Succession and ruler death expansion — DONE
Phase 6-E: Simple survival economy — DONE
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

Phase 6-D closed with:
- succession state added to every runtime faction
- inheritance law, heir legitimacy, regency, crisis state, pretenders and last transition are tracked
- ruler death can produce stable succession, regency or succession crisis
- succession crisis records pretenders, backing factions, pretender claims and chronicle events
- severe succession pressure can trigger a pretender revolt in the capital
- realm inspector shows succession law, heir legitimacy, crisis risk, regency, crisis and pretenders
- validation covers broken succession state and pretender references
- 50-year balance validation passing
- 25-year observer validation passing
- full test suite passing

Phase 6-E closed with:
- explicit runtime economy state added to every faction
- tracked war debt, food stress, trade value, devastation loss, tribute due and last survival decision
- monthly survival decisions can raise taxes, lower taxes, borrow money, sell privileges, dismiss armies and squeeze conquered land
- survival decisions affect tax burden, loyalty, debt, treasury, devastation, unrest and revolt risk
- war debt and unaffordable war economy can push factions toward peace
- realm inspector uses polished Economy, Treasury, Taxation, Food, Trade, War Debt and Tribute labels
- validation covers broken economy state
- 50-year balance validation passing
- 25-year observer validation passing
- full test suite passing
```

## Current Phase 8 substep

```text
Phase 7-A: Character schema expansion — DONE
Phase 7-B: Ambitions and fears — DONE
Phase 7-C: Relationship system — DONE
Phase 7-D: Personal memories and military record — DONE
Phase 8-A: Family tree data — DONE
Phase 8-B: Dynasty and house system — DONE
Phase 8-C: Cadet branches, bastards and legitimacy — DONE
```

## Phase 7 notes

```text
Phase 7-A closed with:
- runtime character hydration added for seeded and generated characters
- tracked birth year, death year, faith, ambition, fear, loyalties, stress, health, wealth, legitimacy and reputation
- generated captains, children, distant heirs and pretenders now use the same schema
- battle, aging and death update stress, health, reputation, wealth and death year
- succession normalizes heirs before inheritance
- character inspector shows expanded core identity clearly
- JS and Python validation check expanded character state
- 50-year balance validation passing
- 25-year observer validation passing
- full test suite passing

Phase 7-B closed with:
- ambition and fear drive profiles now affect ruler war decisions
- war intent summaries explain ruler ambition/fear pressure
- character inspector shows ambition, fear, burden and drive summary
- JS and Python validation reject invalid ambition/fear values
- tests cover ambition/fear behavior and invalid states
- 50-year balance validation passing
- 25-year observer validation passing
- full test suite passing

Phase 7-C closed with:
- runtime relationship records added with reciprocal links
- seeded ruler relationships derive from realm diplomacy
- parent/child and ruler/commander relationships are created during births and musters
- relationships affect succession legitimacy and diplomacy pressure
- character inspector displays important relationships
- JS and Python validation check relationship references, types, strength and reciprocity
- tests cover relationship behavior, validation and inspector wiring
- 50-year balance validation passing
- 25-year observer validation passing
- full test suite passing

Phase 7-D closed with:
- character memories added for major command, battle, wound, province-loss and family-death events
- military records track battles fought, wins, losses, sieges led, wounds and notable battles
- memories can affect reputation, prestige, stress and grudges
- character inspector displays military record and recent memories
- JS and Python validation check memory and military-record state
- tests cover memory behavior, validation and inspector wiring
- 50-year balance validation passing
- 25-year observer validation passing
- full test suite passing

Phase 8-A closed with:
- every character now has explicit family fields for father, mother, spouses, lovers, children, siblings, dynasty, house, legitimacy, inheritance rank and claim strength
- old parentId compatibility is preserved for children, heirs and family memories
- generated children and emergency heirs receive normalized family data
- family sync keeps parent, child and sibling links coherent
- heir selection can use inheritance rank before age
- character inspector shows house, dynasty, inheritance, claim strength and close family
- JS and Python validation catch broken family references, invalid lists, invalid legitimacy/rank/claim strength and parent loops
- tests cover valid family trees, heir ordering, broken references, impossible loops and inspector wiring
- 50-year balance validation passing
- 25-year observer validation passing
- full test suite passing

Phase 8-B closed with:
- runtime dynasty and house records derive from character family fields
- dynasty records track founder, head, home province, prestige, renown, famous ancestors, rivals, alliances, bloodline traits, cadet branches, houses and members
- house records track dynasty, founder, head, home province, legitimacy, prestige and living members
- characters connect to dynasty and house records through family dynastyId and houseId
- house heads refresh after births, spawned captains and succession
- realm inspector shows dynasty, house, founder, head, living members, claims and rivals
- JS and Python validation check broken dynasty/house references and head/member consistency
- tests cover dynasty/house records, succession head updates, UI wiring and broken validation states
- 50-year balance validation passing
- 25-year observer validation passing
- full test suite passing

Phase 8-C closed with:
- family data tracks branch type, branch founder, parent house, cadet reason, bastard status and legitimised status
- cadet branches can form from legitimised bastards and eligible younger children receiving land in multi-province realms
- cadet branch creation keeps descendants in the same dynasty while moving them into a valid branch house
- dynasty and house records expose cadet branch metadata
- legitimacy, bastard status, claim strength and faction support affect heir selection and succession legitimacy
- weak or illegitimate heirs increase succession pressure and crisis risk through faction support
- character and realm inspectors show cadet branches and birth status where data exists
- JS and Python validation check branch and bastard state
- tests cover cadet branch formation, legitimised bastards, legitimacy-driven heir order, support effects and broken validation state
- 25-year observer validation passing
- full test suite passing
```

## Current Phase 9 substep

```text
Phase 9-A: Court and office system — DONE
Phase 9-B: Social groups inside provinces — DONE
Phase 9-C: Law, crime and justice — NEXT
```

## Phase 9 notes

```text
Phase 9-A closed with:
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

Phase 9-B closed with:
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
