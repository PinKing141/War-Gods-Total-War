# Phases 7-8 character and dynasty detail

## Phase 7A. Character schema expansion

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
Characters validate, save/load and display cleanly in the character inspector.
```

## Phase 7B. Ambitions and fears

Ambitions:

```text
become ruler
protect dynasty
avenge family
win glory
gain wealth
restore claim
serve faith
destroy rival
protect child
gain title
control province
```

Fears:

```text
death
disgrace
poverty
betrayal
exile
magical corruption
loss of family
loss of power
```

Closing gate:

```text
Rulers and commanders use ambition/fear in decisions and readable events explain the result.
```

## Phase 7C. Relationships

Relationships:

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
Relationships validate both ends and affect loyalty, succession, schemes and diplomacy.
```

## Phase 8A. Family tree data — DONE

Build:

```text
father
mother
spouses
lovers
children
siblings
dynasty
house
legitimacy
inheritance rank
claim strength
```

Closing gate:

```text
Family links validate and no impossible parent/child loops exist.
```

Completed with:

```text
- explicit family fields added to every runtime character
- parentId compatibility preserved
- generated children and emergency heirs get normalized family data
- parent, child and sibling links sync from family fields and legacy parentId
- heir selection respects inheritance rank before age
- character inspector shows close family, house, dynasty, inheritance rank and claim strength
- JS and Python validation catch broken family references, invalid lists, bad legitimacy/rank/claim strength and parent loops
- tests cover valid family trees, broken links, impossible loops and inspector wiring
- 50-year balance validation passing
- 25-year observer validation passing
- full test suite passing
```

## Phase 8B. Dynasty and house system — DONE

Build dynasties and houses with:

```text
founder
head
home province
prestige
renown
famous ancestors
rivals
alliances
bloodline traits
cadet branches
```

Closing gate:

```text
Dynasty and house panels can show founder, head, members, claims and rivals.
```

Completed with:

```text
- runtime dynasty and house records derive from character family fields
- dynasty records track founder, head, home province, prestige, renown, famous ancestors, rivals, alliances, bloodline traits, cadet branches, houses and members
- house records track dynasty, founder, head, home province, legitimacy, prestige and living members
- characters now connect to dynasty and house records through family dynastyId and houseId
- house heads refresh after births, spawned captains and succession
- realm inspector shows dynasty, house, founder, head, living members, claims and rivals
- JS and Python validation check broken dynasty/house references and head/member consistency
- tests cover dynasty/house records, succession head updates, UI wiring and broken validation states
- 50-year balance validation passing
- 25-year observer validation passing
- full test suite passing
```

## Phase 8C. Cadet branches and legitimacy — DONE

Cadet branches form from:

```text
younger children receiving land
exiled princes surviving
bastards being legitimised
succession splits
rulers losing capital but keeping land
marriages creating merged claims
```

Closing gate:

```text
Cadet branches, legitimacy and claims affect inheritance and faction support.
```

Completed with:

```text
- family data now tracks branch type, branch founder, parent house, cadet reason, bastard status and legitimised status
- cadet branches can form from legitimised bastards and eligible younger children receiving land in multi-province realms
- cadet branch creation keeps descendants inside the same dynasty while moving them into a valid branch house
- dynasty records expose cadet branch summaries and house records track branch metadata
- legitimacy, bastard status, claim strength and faction support affect heir selection and succession legitimacy
- weak or illegitimate heirs increase succession pressure and crisis risk through faction support
- character and realm inspectors show cadet branches and birth status where data exists
- JS and Python validation catch invalid branch type, broken branch founders, broken parent houses and invalid bastard/legitimised state
- tests cover cadet branch formation, legitimised bastards, legitimacy-driven heir order, support effects and broken validation state
- 25-year observer validation passing
- full test suite passing
```
