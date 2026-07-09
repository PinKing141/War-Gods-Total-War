# Phase 7 Character life, traits, relationships and personal ambition detail

This phase makes history personal. Factions should not be the only actors.

## 7A. Character schema expansion — DONE

Build:

```text
age
birth year
death year
culture
species
faith
role
faction
traits
ambition
fear
loyalties
stress
health
wealth
legitimacy
reputation
```

Closing gate:

```text
Characters validate correctly.
Character inspector can show core identity cleanly.
Runtime snapshots preserve character state.
```

Completed with:

```text
- runtime character hydration added for seeded and generated characters
- tracked birth year, death year, faith, ambition, fear, loyalties, stress, health, wealth, legitimacy and reputation
- generated captains, children, distant heirs and pretenders now use the same schema
- battle, aging and death update stress, health, reputation, wealth and death year
- succession normalizes heirs before inheritance
- character inspector shows faith, birth/death year, ambition, fear, loyalties, stress, health, wealth, legitimacy and reputation
- JS and Python validation check the expanded character schema
- tests cover seeded, generated, dead and broken characters
- 50-year balance validation passing
- 25-year observer validation passing
- full test suite passing
```

## 7B. Ambitions and fears — DONE

Build:

```text
become ruler
protect dynasty
win glory
secure wealth
defend faith
restore old claims
keep peace
master the court

fears:
dying forgotten
losing legitimacy
court betrayal
dynasty failure
poverty
magical scandal
foreign conquest
open revolt
```

Closing gate:

```text
Ambitions and fears influence at least one decision or event type.
Character inspector explains ambition, fear and pressure clearly.
Validation catches missing or invalid ambition/fear state.
```

Completed with:

```text
- ambitions and fears now create a character drive profile for war, caution, economy and court pressure
- ruler ambition/fear affects war declaration probability
- war intent summaries explain the ruler's ambition/fear pressure
- character inspector shows ambition, fear, burden and drive summary
- JS validation rejects missing and invalid ambition/fear values
- Python snapshot validation rejects missing and invalid ambition/fear values
- tests cover aggressive/cautious ambition effects and invalid ambition/fear state
- 50-year balance validation passing
- 25-year observer validation passing
- full test suite passing
```

## 7C. Relationship system — DONE

Build:

```text
parent
child
sibling
spouse
lover
friend
rival
enemy
mentor
student
commander
vassal
patron
hostage
betrayer
rescuer
```

Closing gate:

```text
Relationships validate both ends.
Relationships affect loyalty, schemes, succession and diplomacy.
Character panel displays important relationships.
```

Completed with:

```text
- runtime relationship records added with type, source, strength and reciprocal links
- seeded ruler relationships now derive from realm diplomacy
- parent/child and ruler/commander relationships are created during births and musters
- relationships affect succession legitimacy and diplomacy pressure
- character inspector displays important relationships
- JS and Python validation check relationship references, types, strength and reciprocal state
- tests cover relationship behavior, validation and inspector wiring
- 50-year balance validation passing
- 25-year observer validation passing
- full test suite passing
```

## 7D. Personal memories and military record — DONE

Build:

```text
family death
battle victory
battle defeat
promotion
betrayal
humiliation
wound
lost province
saved life
first command
exile

Military record:
battles fought
battles won
battles lost
sieges led
wounds
notable victories
notable defeats
```

Closing gate:

```text
Characters remember major events.
Memories can create grudges, loyalty and reputation.
Character biographies become possible later.
```

Completed with:

```text
- character memories added for family death, battle victory, battle defeat, wound, lost province, first command and siege command milestones
- military records now track battles fought, battles won, battles lost, sieges led, wounds, notable victories and notable defeats
- battle memories affect reputation, prestige, stress and grudges
- lost-province memories create ruler stress, reputation loss and personal rivalry pressure
- family deaths create memories for close kin
- character inspector shows military record and recent memories
- JS and Python validation check memory type, text, day, references and military record totals
- tests cover battle/death memory behavior, grudges, records, inspector wiring and broken memory state
- 50-year balance validation passing
- 25-year observer validation passing
- full test suite passing
```
