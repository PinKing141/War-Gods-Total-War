# War Gods: Total War — AAA Master Development Roadmap

## Purpose

This roadmap turns the project from a collection of good feature ideas into a staged production plan. It is organised like a large game-development roadmap: pillars, tracks, dependencies, sub-phases, closing gates, acceptance criteria, quality bars, risk checks and integration rules.

The aim is not to add features randomly. The aim is to build a living observer grand-strategy simulation where the player watches a civilisation produce history through people, families, states, institutions, wars, trade, disasters, culture, faith, memory and long-term consequence.

## Product pillars

Every feature must support at least one pillar.

```text
1. Living History
   The world must remember what happened and let that history shape the future.

2. People Drive Politics
   Rulers, heirs, generals, nobles, priests, merchants, mages and families must matter.

3. Land Has Meaning
   Provinces should matter because of food, roads, rivers, ports, forts, holy sites, mines, cultures, memories and claims.

4. Power Is Not Only the State
   Noble houses, temples, guilds, military orders, mage circles, cities, clans and rebels must influence events.

5. Observer Readability
   The player must always understand what changed, why it changed and why it matters.

6. Data Safety First
   Every expansion must pass validation before it becomes part of the simulation.

7. Build Vertically Before Scaling Horizontally
   Prove one deep working slice before adding 100 shallow things.
```

## Roadmap structure

Each phase is divided into smaller sub-phases.

```text
Phase X-A = first system slice
Phase X-B = integration with existing systems
Phase X-C = UI/readability pass
Phase X-D = tests, validation and closing gate
```

A phase is not closed because code exists. A phase is closed only when it passes its gate.

## Closing gate standard

Every closing gate should answer these questions:

```text
1. Does it work in the simulation?
2. Does it connect to existing systems?
3. Does the UI explain it clearly?
4. Does validation catch broken data?
5. Does save/load preserve it?
6. Does the chronicle/reporting mention important outcomes?
7. Does it avoid leaking debug language into player-facing UI?
8. Can it survive a 25-50 year test run without breaking?
9. Does it avoid adding unrelated scope?
10. Is the feature fun or useful to observe?
```

## Production tracks

The roadmap uses these tracks:

```text
TRACK A — Foundation, Validation and Stability
TRACK B — UI Copy, Readability and Player Presentation
TRACK C — Core War Simulation
TRACK D — Character, Family and Dynasty Simulation
TRACK E — Internal Politics, Society, Law and Revolt
TRACK F — Memory, Chronicle and History
TRACK G — Culture, Faith, Institutions and Ideology
TRACK H — Diplomacy and International Politics
TRACK I — Economy, Trade, Resources and Settlement Growth
TRACK J — Non-State Actors, Espionage and Irregular Power
TRACK K — Technology, Knowledge, Magic and Disasters
TRACK L — Naval Power and Coastal Systems
TRACK M — World Scale, Major Powers and 100+ Political Entities
TRACK N — Scenario Tools, Debug Tools and Modding Pipeline
TRACK O — Final Presentation, Art, Audio and Release
```

---

# PHASE 0 — Current Prototype Lock and Baseline Audit

## Goal

Freeze what already works and establish a safe baseline before adding more systems.

## Current state recognised

```text
Old map decommission: done
Layered map foundation: done
Observer readability: mostly done
Army supply: done
Movement depth: done
Basic attrition: done
Siege depth: partly done / good enough first pass
AI intent reasons: done
Peace summaries: done
Data validation gate: missing
UI copy/SPAG polish: missing
```

## Phase 0-A — Baseline inventory

Tasks:

```text
1. List core simulation files.
2. List UI files.
3. List data files.
4. List test files.
5. Mark systems as Done / Partial / Missing.
6. Record known issues.
```

## Phase 0-B — Prototype lock

Tasks:

```text
1. Do not add new countries yet.
2. Do not add new map art yet.
3. Do not add naval systems yet.
4. Do not add huge content packs yet.
5. Use the current prototype as the baseline for validation and polish.
```

## Phase 0 Closing Gate

Closed when:

```text
- The baseline is documented.
- Current completed systems are not being rewritten unnecessarily.
- The next phase is validation, not new content.
```

---

# PHASE 1 — Data Validation Gate

## Goal

Make the project safe to expand. Nothing large should be added until broken IDs, missing references and invalid values are caught automatically.

## Phase 1-A — Validation module

Tasks:

```text
1. Create a dedicated validation module.
2. Create validation helpers for IDs, references, numeric ranges and required fields.
3. Make validation output readable failure messages.
4. Make failures name the exact broken file, row, object, ID and field.
```

## Phase 1-B — Core ID validation

Validate:

```text
province IDs are unique
faction IDs are unique
character IDs are unique
army IDs are unique
war IDs are unique
claim IDs are unique
institution IDs are unique when institutions exist
dynasty IDs are unique when dynasties exist
house IDs are unique when houses exist
```

## Phase 1-C — Reference validation

Validate:

```text
every province controller exists
every character faction exists
every army location is a valid province
every adjacency link points to a valid province
every war attacker exists
every war defender exists
every war participant exists
every war goal province exists
every claim claimant exists
every claim target province exists
every mage character exists
every mage patron exists
every ruler/heir reference exists
every capital province exists
every culture/religion reference exists
```

## Phase 1-D — Numeric validation

Validate no invalid values for:

```text
population
garrison
army size
treasury
manpower
supply
morale
war score
exhaustion
fort level
road level
port level
food
income
prestige
legitimacy
```

## Phase 1-E — Validation test suite

Tasks:

```text
1. Add tests for valid seed data.
2. Add tests for duplicate IDs.
3. Add tests for missing references.
4. Add tests for invalid negative values.
5. Add tests for broken war, claim, army and province links.
6. Ensure test failures are human-readable.
```

## Phase 1 Closing Gate

Closed when:

```text
- Validation runs locally.
- Validation catches bad province, faction, character, army, war, claim and adjacency data.
- Tests exist for both valid and invalid examples.
- Failure messages are clear enough to fix data without searching the codebase.
- No new gameplay systems were added during this phase.
```

---

# PHASE 2 — UI Copy, SPAG and Player-Facing Presentation Pass

## Goal

Remove debug speech, awkward labels, internal system wording and unreadable text from normal UI before the project scales.

## Rule

```text
Debug language belongs in debug mode.
Player-facing UI must sound like a grand-strategy game.
```

## Phase 2-A — UI text audit

Audit:

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

## Phase 2-B — Remove bad player-facing wording

Remove or hide from normal UI:

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
snake_case
camelCase
```

## Phase 2-C — Replace awkward labels

Use these replacements:

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
Intent reason -> Reason, debug only
Simulation -> Status or remove from normal UI
```

## Phase 2-D — Label style guide

Use short title-case labels:

```text
Goal
Status
Economy
Ruler
Heir
House
Dynasty
Army Strength
Treasury
Claims
Wars
Sieges
Strategic Value
Relations
Treaties
Faith
Culture
Lands
Unrest
Risk
```

## Phase 2-E — Debug separation

Create strict UI layers:

```text
Normal UI = polished labels and readable summaries
Advanced tooltip = extra explanation
Debug mode = raw IDs, scores, references and validation info
```

## Phase 2 Closing Gate

Closed when:

```text
- Normal UI has no raw IDs unless intentionally displayed as lore names.
- No snake_case or camelCase appears in normal UI.
- No debug placeholders appear in normal UI.
- No panel labels are written as questions.
- UI labels use consistent title case.
- Event text reads naturally.
- Debug information still exists, but only in debug mode.
```

---

# PHASE 3 — Core War Simulation Hardening

## Goal

Finish the first combat/siege/army loop before adding political scale.

## Phase 3-A — Army supply closure

Already mostly done. Finalise by checking:

```text
army supply
max supply
daily supply use
resupply
undersupply
attrition
morale loss
exhaustion gain
```

Gate 3-A:

```text
- Armies lose supply away from safe supply sources.
- Armies resupply in valid friendly areas.
- Undersupplied armies suffer visible consequences.
- UI displays army condition without debug wording.
```

## Phase 3-B — Movement and terrain closure

Already mostly done. Finalise:

```text
terrain flags
mountain movement
marsh movement
roads
enemy territory
province adjacency
movement ETA
```

Gate 3-B:

```text
- Mountains, marshes, roads and hostile land affect movement.
- Armies do not teleport.
- Movement results can be explained in event logs or tooltips.
```

## Phase 3-C — Siege first-pass closure

Tasks:

```text
1. Finish siege duration logic.
2. Keep fort level meaningful.
3. Keep army condition meaningful.
4. Track investment, breach and surrender/fall events.
5. Make coastal siege hooks available later, but do not build naval yet.
```

Gate 3-C:

```text
- Sieges take time.
- Fort level matters.
- Supply and morale affect siege progress.
- Siege events appear in the chronicle/event log.
- Province ownership changes correctly after siege resolution.
```

## Phase 3-D — Battle readability

Tasks:

```text
1. Make battle outcomes readable.
2. Track casualties.
3. Track commander involvement if characters exist.
4. Track battle location.
5. Add battle memory hooks for later.
```

Gate 3-D:

```text
- Battles create clear events.
- Casualties are recorded.
- The player can tell who won and why at a basic level.
- Battle hooks are ready for character reputation and memory later.
```

## Phase 3 Closing Gate

Closed when a 25-year test run produces:

```text
wars
army movement
supply problems
sieges
battles
peace outcomes
no broken references
readable event logs
```

---

# PHASE 4 — Faction AI, Strategic Priorities and Survival Logic

## Goal

Make factions act like political bodies with goals, not random coloured map blobs.

## Phase 4-A — Faction priority profiles

Add priorities:

```text
expand territory
protect homeland
recover claims
raid for wealth
avoid war
defend faith
secure trade routes
hold mountain passes
control ports
destroy rival faction
survive internal crisis
```

Gate 4-A:

```text
- Every faction has weighted priorities.
- Priorities can be inspected in debug mode.
- Normal UI shows only polished terms such as Goal and Strategy.
```

## Phase 4-B — Ruler and state decision scoring

Score decisions using:

```text
ruler traits
claims
relations
army strength
treasury
manpower
current wars
war exhaustion
province value
neighbour weakness
old grievances once memory exists
```

Gate 4-B:

```text
- Declarations of war have understandable causes.
- Peace decisions have understandable causes.
- Defensive behaviour exists, not only aggression.
```

## Phase 4-C — Event explanation pass

Tasks:

```text
1. Replace raw scoring text with readable event summaries.
2. Keep raw scoring in debug mode only.
3. Make action causes concise.
```

Gate 4-C:

```text
- The player sees Goal, Cause and Outcome.
- The player does not see seeded scores or internal probability language.
```

## Phase 4 Closing Gate

Closed when:

```text
- Factions make visibly different choices.
- Expansionist, defensive, raiding, religious and trade-focused factions behave differently.
- Event text explains major actions clearly.
- Validation covers new AI profile fields.
```

---

# PHASE 5 — Character Core: Traits, Ambitions, Relationships and Personal Actions

## Goal

Make people matter before the world starts recording history.

## Phase 5-A — Character data model expansion

Add:

```text
age
culture
species
faith
role
traits
ambition
fear
loyalties
rivals
friends
personal wealth
legitimacy
health
stress
```

Gate 5-A:

```text
- Important characters have readable profiles.
- Missing character fields are validated.
- Character UI uses polished labels.
```

## Phase 5-B — Ambitions and fears

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
escape court politics
found a house
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
losing family
losing power
```

Gate 5-B:

```text
- Ambitions influence at least one decision type.
- Fears influence at least one decision type.
- UI shows Ambition and Fear clearly.
```

## Phase 5-C — Relationships

Relationship types:

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

Gate 5-C:

```text
- Characters can have relationships with other characters.
- Invalid relationship references are caught by validation.
- Relationship labels are readable in the character panel.
```

## Phase 5-D — Personal memories

Characters remember:

```text
family death
battle victory
battle defeat
betrayal
promotion
humiliation
lost province
saved life
wound
exile
```

Gate 5-D:

```text
- Major character events can create personal memories.
- Personal memories can later connect to historical memory.
- Character panel can show memories without becoming cluttered.
```

## Phase 5-E — Simple schemes and personal actions

Schemes:

```text
support claimant
undermine rival
seek marriage
forge claim
bribe commander
spread rumour
defect
raise private troops
betray fortress
hide claimant
```

Gate 5-E:

```text
- At least 3 simple schemes exist.
- Schemes have clear start, progress and outcome states.
- Schemes create readable events.
- Failed schemes can create memories or rivalries.
```

## Phase 5 Closing Gate

Closed when:

```text
- Characters are more than names.
- Rulers and commanders can make decisions affected by traits, ambition, fear, relationships and memories.
- Character inspector is useful and readable.
- Character references are validated.
```

---

# PHASE 6 — Family Trees, Dynasties, Houses, Bloodlines and Succession Claims

## Goal

Make long-term history personal across generations.

## Phase 6-A — Family tree model

Add to characters:

```text
father_id
mother_id
spouse_ids
lover_ids
children_ids
dynasty_id
house_id
birth_year
death_year
legitimacy
inheritance_status
```

Gate 6-A:

```text
- Family links validate correctly.
- No impossible family references pass validation.
- Character panel shows parents, spouse, children and siblings.
```

## Phase 6-B — Dynasty records

Dynasty fields:

```text
dynasty_id
name
founder
culture
religion
home_province
prestige
renown
living_members
dead_members
ruling_members
claims
rivals
alliances
dynasty_traits
famous_ancestors
cadet_branches
```

Gate 6-B:

```text
- Dynasties exist independently of factions.
- A faction can change ruler without deleting the dynasty.
- Dynasty panel shows identity, members, claims and prestige.
```

## Phase 6-C — Houses and cadet branches

Cadet branches form when:

```text
younger child gains land
exile survives
bastard is legitimised
succession splits
ruler loses capital but keeps another province
marriage creates merged claim
```

Gate 6-C:

```text
- Houses can branch from dynasties.
- Cadet branch creation creates an event.
- Branches can hold claims and rivalries.
```

## Phase 6-D — Trait categories

Trait layers:

```text
personality
education/lifestyle
physical/health
reputation
bloodline
```

Gate 6-D:

```text
- Traits are categorised.
- Traits influence at least some decisions or outcomes.
- Reputation traits can be earned from events.
- Bloodline traits can be inherited with rules.
```

## Phase 6-E — Inheritance and claims

Claim sources:

```text
parents
marriage
dynasty history
lost titles
religious blessing
adoption
bastard legitimisation
old treaties
fabricated documents
```

Claim strengths:

```text
weak claim
pressed claim
strong claim
dynastic claim
sacred claim
fabricated claim
popular claim
```

Gate 6-E:

```text
- Succession order can be calculated.
- Claims can be inherited.
- Claim strength affects war/diplomacy decisions.
- Invalid claim references are caught.
```

## Phase 6 Closing Gate

Closed when:

```text
- Family trees work.
- Dynasty trees work.
- Houses and cadet branches exist.
- Succession claims connect to war, diplomacy and internal politics.
- Dynasty extinction and branch survival can happen.
```

---

# PHASE 7 — Internal Politics, Courts, Offices and Social Groups

## Goal

Make realms unstable from within, not only through external war.

## Phase 7-A — Court structure

Add:

```text
ruler court
heir circle
council offices
commander offices
governors/local lords
court factions
favourite/disfavoured characters
```

Gate 7-A:

```text
- Important realms have courts.
- Court offices affect realm behaviour.
- Court changes create readable events.
```

## Phase 7-B — Internal faction groups

Add internal groups:

```text
noble faction
military faction
merchant faction
religious faction
mage faction
regional faction
claimant faction
reform faction
traditionalist faction
```

Gate 7-B:

```text
- Internal factions can support or oppose rulers.
- Internal groups influence at least one decision type.
- Realm inspector shows internal politics clearly.
```

## Phase 7-C — Province population groups

Province groups:

```text
nobles
clergy
merchants
peasants
soldiers
craftsmen
mages
scholars
minorities
tribes
foreign settlers
refugees
urban poor
```

Gate 7-C:

```text
- Provinces can track important population groups.
- Population groups affect unrest, income, manpower or legitimacy.
- Province panel remains readable.
```

## Phase 7-D — Internal survival decisions

Decisions:

```text
raise taxes
lower taxes
call council
appease nobles
support clergy
fund merchants
purge rivals
appoint governor
dismiss commander
recognise heir
suppress unrest
```

Gate 7-D:

```text
- Internal politics can stabilise or destabilise a realm.
- Strong realms can collapse from within.
- Event text explains internal crises naturally.
```

## Phase 7 Closing Gate

Closed when:

```text
- A realm can suffer internal trouble without external war.
- Characters, houses, offices and population groups connect.
- Internal politics can feed revolts, succession and diplomacy.
```

---

# PHASE 8 — Law, Justice, Crime, Imprisonment and Revolts

## Goal

Make unrest and rebellion more than random province explosions.

## Phase 8-A — Law systems

Add laws:

```text
inheritance law
tax law
military obligation law
religious law
city charter law
noble privilege law
mage law
trade law
criminal law
```

Gate 8-A:

```text
- Laws exist as realm settings.
- Laws affect at least one system.
- Law names are player-readable.
```

## Phase 8-B — Crime and justice

Add:

```text
treason
corruption
banditry
heresy
smuggling
forged claims
illegal magic
murder
rebellion
trial
exile
execution
imprisonment
pardon
hostage
```

Gate 8-B:

```text
- Characters can be accused, punished or pardoned.
- Punishment affects relationships, memory and unrest.
- Justice events are readable and not overly graphic.
```

## Phase 8-C — Revolt risk model

Revolt sources:

```text
devastation
occupation
culture mismatch
faith mismatch
recent conquest
low garrison
famine
high taxes
weak ruler
foreign support
claimant support
religious agitation
noble anger
```

Gate 8-C:

```text
- Province revolt risk exists internally.
- Normal UI shows Unrest/Risk, not debug formula text.
- Causes of unrest can be inspected.
```

## Phase 8-D — Revolt types

Types:

```text
peasant revolt
noble revolt
religious uprising
separatist revolt
pretender revolt
military coup
frontier independence
city commune revolt
mage revolt
slave/serf revolt if the setting uses that system carefully
```

Gate 8-D:

```text
- Revolts have leaders where appropriate.
- Revolts can become factions if they survive.
- Revolts connect to claims, culture, faith, law and internal politics.
```

## Phase 8 Closing Gate

Closed when:

```text
- Revolts have causes.
- Revolts have leaders or social groups where appropriate.
- Revolts create memories and chronicle entries.
- Suppression or concessions have consequences.
```

---

# PHASE 9 — Living Chronicle, Historical Memory and Reputation

## Goal

Make the world remember, then make memory shape the future.

## Phase 9-A — Memory model

Memory fields:

```text
id
type
date
location
actors
victims
importance
decay
description
future_effect
```

Memory owners:

```text
characters
families
houses
dynasties
factions
provinces
wars
institutions
```

Gate 9-A:

```text
- Memories can be created by major events.
- Memories validate references.
- Memories persist through save/load.
```

## Phase 9-B — Major memory events

Track:

```text
province conquest
ruler death
battle victory
battle defeat
siege victory
broken treaty
betrayal
revolt
succession crisis
restoration war
sack of city
heroic defence
religious scandal
dynasty extinction
```

Gate 9-B:

```text
- Major events create memory entries.
- Memory importance is calculated or assigned.
- Low-importance spam is controlled.
```

## Phase 9-C — Grievances and rivalries

Faction/dynasty/character AI remembers:

```text
who took land
who killed family
who broke treaty
who humiliated them
who helped them
who saved them
who betrayed them
```

Gate 9-C:

```text
- Old memories can influence future choices.
- War causes can reference old grievances in polished language.
```

## Phase 9-D — Chronicle generation

Chronicles:

```text
monthly chronicle
yearly annals
war histories
ruler biographies
faction rise/fall records
battle summaries
province history
dynasty records
```

Gate 9-D:

```text
- Yearly annals summarise major events.
- Province panels can show history.
- Realm panels can show history.
- Character panels can show reputation and memories.
```

## Phase 9 Closing Gate

Closed when:

```text
- The world can explain its past.
- The past affects future behaviour.
- Chronicles are readable and not debug logs.
- The same event can matter to a province, a dynasty, a character and a faction.
```

---

# PHASE 10 — Culture, Identity, Language Drift and Faith/Sect Systems

## Goal

Make culture and religion active historical forces instead of static labels.

## Phase 10-A — Culture model

Culture fields:

```text
id
name
language_family
customs
martial_tradition
naming_style
honour_code
food_customs
burial_customs
festival_tags
elite_variant
common_variant
```

Gate 10-A:

```text
- Culture data validates.
- Characters and provinces can reference culture.
- Culture names display cleanly.
```

## Phase 10-B — Culture change

Add:

```text
assimilation
hybrid cultures
diaspora groups
frontier cultures
elite/common culture split
cultural friction
cultural prestige
```

Gate 10-B:

```text
- Culture can shift slowly over time.
- Culture affects unrest, marriage, diplomacy or military custom.
- Hybrid cultures can appear under controlled rules.
```

## Phase 10-C — Religion and sects

Add:

```text
sects
heresies
holy sites
pilgrimages
religious law
prophets
saints
martyrs
schisms
temple wealth
priest politics
miracle claims
persecution
conversion
```

Gate 10-C:

```text
- Religions can have internal divisions.
- Sects can affect politics and revolt risk.
- Holy sites matter.
```

## Phase 10-D — Rituals and social texture

Add flavour events for:

```text
festivals
coronations
funerals
pilgrimages
marriage rites
coming-of-age ceremonies
victory parades
public oaths
market fairs
seasonal gatherings
```

Gate 10-D:

```text
- Rituals create character/culture/institution memories where important.
- They add texture without flooding the event log.
```

## Phase 10 Closing Gate

Closed when:

```text
- Culture and faith influence politics.
- Culture and faith appear in character, province and faction identity.
- Sects and hybrid cultures can emerge without breaking validation.
```

---

# PHASE 11 — Institutions and Power Structures

## Goal

Make power exist outside rulers and formal factions.

## Phase 11-A — Institution model

Institution fields:

```text
id
name
type
home_province
influence
wealth
loyalty
ideology_or_goal
supported_faction
supported_ruler
rivals
memory_refs
```

Institution types:

```text
noble house
religious authority
merchant guild
military order
mage college
city charter
tribal council
imperial court
scholarly order
law court
```

Gate 11-A:

```text
- Institutions exist as separate actors.
- Institutions validate references.
- Province and realm panels can show relevant institutions.
```

## Phase 11-B — Institution influence

Institutions affect:

```text
succession
revolts
war support
taxation
legitimacy
province unrest
coups
treaty pressure
claim support
```

Gate 11-B:

```text
- Institutions influence events without directly owning all land.
- Institution involvement is explained in event text.
```

## Phase 11-C — Institution memories and rivalry

Tasks:

```text
1. Institutions remember favours, persecution, broken promises and patronage.
2. Institutions can become rivals.
3. Institutions can back claimants, revolts or reforms.
```

Gate 11-C:

```text
- Institution memory connects to Phase 9.
- Institutions can shape long-term politics.
```

## Phase 11 Closing Gate

Closed when:

```text
- Realms are influenced by actors beyond the ruler.
- Institutions can support or destabilise states.
- Institution UI is readable and not overloaded.
```

---

# PHASE 12 — Diplomacy, Treaties, Coalitions and International Politics

## Goal

Make factions negotiate, scheme and survive without always needing open war.

## Phase 12-A — Treaty object model

Treaty fields:

```text
id
type
parties
start_date
end_date
terms
obligations
tribute
marriage_link
hostages
breaking_penalty
memory_entry
```

Treaty types:

```text
alliance
defensive pact
non-aggression pact
truce
tributary
protectorate
trade privilege
military access
religious guarantee
marriage pact
hostage pact
```

Gate 12-A:

```text
- Treaties validate references.
- Treaties expire or break cleanly.
- Active treaties show in realm panels.
```

## Phase 12-B — Diplomacy AI

AI considers:

```text
ally need
fear of neighbours
grievance
military strength
treasury
depleted manpower
war exhaustion
ruler traits
institutions
religion/culture
trade needs
succession crisis
```

Gate 12-B:

```text
- Factions can seek allies, tribute, protection and peace.
- Diplomacy does not always collapse into war.
- Causes are readable.
```

## Phase 12-C — Coalitions and containment

Coalition triggers:

```text
rapid expansion
broken treaties
religious threat
high infamy
holding sacred land
sacking important cities
murdering rulers
oppressing institutions
```

Gate 12-C:

```text
- Growing powers face diplomatic resistance.
- Coalitions use treaties/memories rather than arbitrary punishment.
```

## Phase 12-D — Foreign meddling

Actions:

```text
fund rebels
back pretender
shelter exiles
send weapons
bribe nobles
support religious unrest
hire raiders
sabotage trade
```

Gate 12-D:

```text
- Factions can hurt enemies without direct war.
- Meddling creates risks, memories and diplomatic consequences.
```

## Phase 12 Closing Gate

Closed when:

```text
- Treaties work.
- Alliances and protectorates can change survival outcomes.
- Coalitions can form.
- Foreign meddling connects to revolts, claims and schemes.
- Diplomacy history appears in chronicles.
```

---

# PHASE 13 — Economy, Food, Trade, Resources and Settlement Growth

## Goal

Make land valuable for reasons beyond colour on the map.

## Phase 13-A — Province resources

Resources:

```text
grain
livestock
fish
timber
iron
stone
salt
horses
cloth
silver
gems
mana crystals
spices
luxury goods
herbs
```

Gate 13-A:

```text
- Provinces have primary and optional secondary resources.
- Resources validate.
- Province panel shows resources cleanly.
```

## Phase 13-B — Food and survival economy

Track:

```text
food production
food demand
food storage
famine risk
army food drain
siege starvation
devastation loss
trade/import relief
```

Gate 13-B:

```text
- Food shortage can affect unrest, armies and diplomacy.
- Famine events can happen but are not spammed.
- UI says Food/Economy, not internal pressure wording.
```

## Phase 13-C — Trade routes

Route types:

```text
capital to port
mine to city
farm region to city
oasis to desert market
pass to trade town
river/canal province to market
holy site pilgrimage route
```

Disruption from:

```text
war
siege
occupation
raiders
bad relations
rebellion
devastation
blockades later
```

Gate 13-C:

```text
- Trade routes link valid provinces.
- Disruption affects income, food or diplomacy.
- Route information is visible but not overwhelming.
```

## Phase 13-D — Strategic resource dependency

Effects:

```text
grain = stability and army supply
iron = army quality
horses = mobility/cavalry
timber = siege engines and later shipbuilding
salt = preservation/trade wealth
mana = mage institutions and magical risk
silver = treasury strength
```

Gate 13-D:

```text
- Factions care about resources.
- War/diplomacy target selection can value resources.
- Resource shortages create meaningful events.
```

## Phase 13-E — Settlement growth

Settlement levels:

```text
village
town
market town
fortress town
city
capital
holy city
trade city
ruined city
ghost town
```

Gate 13-E:

```text
- Settlements can grow, decline, burn or recover.
- Cities connect to trade, institutions, culture and unrest.
- Province history records major settlement changes.
```

## Phase 13 Closing Gate

Closed when:

```text
- Economy explains why land matters.
- Food, resources and trade affect war, diplomacy and unrest.
- Settlement growth creates long-term history.
- The economy remains lightweight and readable.
```

---

# PHASE 14 — Major Power Expansion and Scalable Political Map

## Goal

Expand beyond the small test core without creating a spreadsheet graveyard.

## Phase 14-A — Faction tier system

Tiers:

```text
Tier 1 = great power / major realm
Tier 2 = regional power
Tier 3 = minor state / city-state / march / hold
Tier 4 = background or non-state actor
```

Gate 14-A:

```text
- Every political entity has a tier.
- Simulation depth can scale by tier.
- Validation requires tier data.
```

## Phase 14-B — First major expansion: 16-20 serious powers

Add 8-12 new Tier 1/Tier 2 powers first.

Suggested slots:

```text
Lanter Sea naval league
Northern highland kingdom
Southern salt-road kingdom
Eastern river confederation
Western marcher kingdom
Great religious protectorate
Large elven forest court
Large dwarf stone league
Orc war confederation
Mage-law state
Wealthy free-city league
Nomad successor confederation
```

Gate 14-B:

```text
- Total serious powers reaches roughly 16-20.
- Every new power has a region, capital, provinces, ruler, heir, commander, rival, ally and goal.
- Validation passes.
- 25-50 year test run does not instantly collapse.
```

## Phase 14-C — Regional expansion: 35-50 powers

Add:

```text
regional kingdoms
duchies
marches
city-states
merchant republics
tribal confederations
clan holds
religious states
mage domains
frontier forts
free cities
nomad rings
```

Gate 14-C:

```text
- Minor powers use lighter simulation.
- They can become important if events elevate them.
- Performance remains stable.
```

## Phase 14-D — CK-style scale: 100+ entities

Add:

```text
minor lordships
city communes
small clans
tribal bands
frontier polities
island holdings
holy orders
pirate havens
rebel successor states
guild-controlled towns
```

Gate 14-D:

```text
- 100+ entities exist without every one needing full detail.
- Tier 3 and Tier 4 actors do not melt performance.
- The world feels crowded but readable.
- Scenario tools can filter or highlight important actors.
```

## Phase 14 Closing Gate

Closed when:

```text
- Political scale is large enough to feel CK-like.
- Major powers remain distinct.
- Minor powers are lightweight but functional.
- Validation catches missing province, ruler, culture, faith, claim and relation references.
```

---

# PHASE 15 — Mercenaries, Bandits, Pirates and Non-State Violence

## Goal

Make violence exist outside formal wars.

## Phase 15-A — Mercenary companies

Add:

```text
company name
captain
home region
strength
cost
loyalty
reputation
contract holder
rivals
```

Gate 15-A:

```text
- Factions can hire mercenaries.
- Mercenaries can switch sides or become unpaid threats.
- Mercenary actions create memories.
```

## Phase 15-B — Bandits and raider bands

Add:

```text
bandit kings
raider bands
frontier warbands
exiled princes
disgraced knights
rebel captains
```

Gate 15-B:

```text
- Bandits/raiders disrupt roads, trade and province stability.
- They can be suppressed, hired or become political actors.
```

## Phase 15-C — Pirates and coastal raiders

Add hooks only if naval base exists:

```text
pirate haven
raider fleet
convoy attack
port ransom
coastal raid
```

Gate 15-C:

```text
- Pirates interact with sea routes and ports.
- Pirate threat can affect diplomacy and trade.
```

## Phase 15 Closing Gate

Closed when:

```text
- Non-state violence can threaten realms.
- Non-state actors can become remembered figures.
- These systems connect to trade, law, diplomacy and chronicles.
```

---

# PHASE 16 — Espionage, Secrets, Rumours and Schemes

## Goal

Make politics less clean and more personal.

## Phase 16-A — Secret model

Secret types:

```text
illegitimate child
secret lover
forged claim
heresy
treason
murder
illegal magic
bribe
hidden heir
stolen treaty
```

Gate 16-A:

```text
- Secrets can be attached to characters, houses, institutions or factions.
- Secrets validate references.
- Secrets can remain hidden or be exposed.
```

## Phase 16-B — Spy networks

Add:

```text
spy network
spymaster
informants
foreign agents
court rumours
merchant informants
temple informants
```

Gate 16-B:

```text
- Spy networks affect discovery and scheme success.
- Spy systems do not flood the event log.
```

## Phase 16-C — Advanced schemes

Schemes:

```text
assassination plot
poisoning
blackmail
sabotage peace talks
sabotage trade
bribe commander
betray fortress
fabricate claim
kidnap hostage
spread rumour
```

Gate 16-C:

```text
- Schemes have risk and consequence.
- Discovery creates scandal, justice events or war causes.
- Schemes connect to character traits and relationships.
```

## Phase 16 Closing Gate

Closed when:

```text
- Politics can be shaped by secrets.
- Exposed secrets affect reputation, law, memory and diplomacy.
- Schemes are readable and not purely random.
```

---

# PHASE 17 — Technology, Knowledge, Doctrine and Education

## Goal

Add slow historical development without making a generic 4X tech tree.

## Phase 17-A — Knowledge domains

Domains:

```text
military doctrine
siege engineering
shipbuilding
administration
tax records
medicine
agriculture
road building
fortification style
magic theory
scholar schools
lost knowledge
```

Gate 17-A:

```text
- Knowledge domains exist.
- Institutions, cultures or cities can hold knowledge.
- Knowledge affects systems lightly.
```

## Phase 17-B — Education and training

Character education:

```text
war-trained
court-trained
merchant-trained
temple-trained
mage-trained
hunter
scholar
duelist
administrator
siege engineer
diplomat
intriguer
```

Gate 17-B:

```text
- Education traits affect character roles.
- Mentors and institutions can shape education.
```

## Phase 17-C — Doctrine and reform

Add:

```text
army doctrine
naval doctrine
administrative reform
legal reform
religious reform
mage regulation reform
```

Gate 17-C:

```text
- Reforms have benefits and opposition.
- Institutions and internal politics react to reforms.
```

## Phase 17 Closing Gate

Closed when:

```text
- Long-term development changes realms over generations.
- Knowledge connects to institutions, characters and cities.
- No bloated tech-tree UI is required.
```

---

# PHASE 18 — Magic Consequences and Rare Mana Politics

## Goal

Make fantasy mechanically important without turning the setting into generic spell spam.

## Phase 18-A — Mana sites and mage power

Add:

```text
mana site strength
mana site instability
mage patronage
court mage
mage college
forbidden school
anti-mage faction
```

Gate 18-A:

```text
- Mana sites matter politically.
- Mage systems connect to institutions, faith, law and economy.
```

## Phase 18-B — Magical risk

Risks:

```text
mana sickness
magical disaster
battlefield trauma
corrupted province
forbidden experiment
mage revolt
anti-mage purge
religious panic
```

Gate 18-B:

```text
- Magic has consequence.
- Magic risk creates events, not just bonuses.
```

## Phase 18-C — Bloodlines and magical inheritance

Add:

```text
mana-touched line
cursed house
saintly lineage
dragon-scarred blood
old imperial blood
mage bloodline decline
```

Gate 18-C:

```text
- Magical bloodlines connect to dynasty systems.
- Inheritance is controlled and validated.
```

## Phase 18 Closing Gate

Closed when:

```text
- Magic affects politics, law, religion, dynasties and provinces.
- Magic remains rare and dangerous.
- Magical events are memorable, not spammed.
```

---

# PHASE 19 — Disasters, Climate, Disease and Environmental History

## Goal

Make history happen from forces beyond politics.

## Phase 19-A — Disaster model

Disasters:

```text
plague
famine
drought
flood
earthquake
harsh winter
locusts
crop failure
mana storm
volcanic winter
river drying
coastal storm
```

Gate 19-A:

```text
- Disasters have location, duration, severity and effects.
- Disasters validate references.
- Disaster UI is readable.
```

## Phase 19-B — Disease and plague

Track:

```text
origin province
spread routes
trade route spread
army spread
mortality
recovery
quarantine
religious response
social blame
```

Gate 19-B:

```text
- Disease can spread through connected systems.
- Plague affects characters, population, economy and succession.
```

## Phase 19-C — Climate and long-term environment

Add:

```text
regional climate trend
soil exhaustion
forest loss
river shift
coastal damage
pasture decline
resource depletion
```

Gate 19-C:

```text
- Environmental change can reshape strategic value.
- Long-term changes are recorded in province history.
```

## Phase 19 Closing Gate

Closed when:

```text
- Non-political forces can reshape the world.
- Disaster effects connect to economy, migration, revolt, succession and memory.
- Events are serious but not constant noise.
```

---

# PHASE 20 — Naval Power, Sea Trade and Coastal Warfare

## Goal

Make seas, ports and coastal cities strategically dangerous and valuable.

## Phase 20-A — Port system

Port fields:

```text
port_level
dock_capacity
trade_value
shipbuilding_value
naval_supply
coastal_defense
merchant_presence
```

Gate 20-A:

```text
- Coastal provinces can be marked as ports.
- Ports validate.
- Port data appears in province UI.
- Ports connect to trade and economy.
```

## Phase 20-B — Sea routes

Sea route states:

```text
safe
contested
raided
blockaded
closed by war
controlled by treaty
```

Gate 20-B:

```text
- Sea routes connect valid ports.
- Sea routes affect trade and food/import flow.
- Routes can be disrupted.
```

## Phase 20-C — Fleet objects

Fleet fields:

```text
id
owner
home_port
location
ships
quality
commander
mission
supply
```

Missions:

```text
patrol
escort trade
raid coast
blockade port
transport army
intercept enemy fleet
protect strait
```

Gate 20-C:

```text
- Fleets exist and validate.
- Fleets have missions.
- Fleets connect to commanders if character systems exist.
```

## Phase 20-D — Blockades and coastal pressure

Blockades affect:

```text
trade income
food supply
war exhaustion
merchant opinion
city unrest
coastal siege progress
```

Gate 20-D:

```text
- Blockades have visible consequences.
- Blockades connect to war, trade and city unrest.
- Coastal provinces feel different from inland provinces.
```

## Phase 20-E — Coastal raids and piracy

Events:

```text
pirate raid
coastal village burned
merchant convoy seized
port ransom demanded
naval ambush
raider fleet vanishes
```

Gate 20-E:

```text
- Coastal raids create economic and political consequences.
- Pirate and raider systems connect to non-state actors.
```

## Phase 20-F — Amphibious movement

Rules:

```text
armies need transport capacity
fleet must be at valid port
landing target must be coastal or port province
landing causes supply risk
enemy fleets can intercept later
```

Gate 20-F:

```text
- Armies cannot teleport across water.
- Naval transport links fleets, armies and ports.
- Amphibious movement is readable and testable.
```

## Phase 20 Closing Gate

Closed when:

```text
- Ports matter.
- Fleets matter.
- Sea trade matters.
- Blockades matter.
- Armies cross water only through valid transport rules.
- Naval events appear in chronicles.
```

---

# PHASE 21 — Scenario Tools, Debug Controls, Balance Dashboard and Modding Pipeline

## Goal

Make the project controllable, testable, expandable and moddable.

## Phase 21-A — Scenario definition files

Scenarios define:

```text
start year
active factions
province ownership
starting rulers
starting wars
treaties
institutions
resources
crises
culture/faith setup
major characters
```

Gate 21-A:

```text
- Scenarios load from data files.
- Scenario data validates before simulation starts.
- Broken scenario data fails clearly.
```

## Phase 21-B — Debug controls

Controls:

```text
start war
end war
kill ruler
trigger succession
spawn revolt
give province
create treaty
cause famine
spawn army
force battle
advance month
advance year
```

Gate 21-B:

```text
- Debug controls are separated from normal player UI.
- Controls make testing faster.
- Debug actions create validation-safe state.
```

## Phase 21-C — Balance dashboard

Track:

```text
strongest factions
richest factions
unstable factions
war counts
revolt counts
average war length
faction collapse rate
economy collapse frequency
food crisis frequency
empire snowball rate
dead-world/no-war periods
```

Gate 21-C:

```text
- Balance dashboard helps detect broken simulation behaviour.
- It is clearly dev-facing or advanced-facing.
```

## Phase 21-D — Timeline replay

Track:

```text
province ownership changes
war starts/ends
ruler changes
major battles
revolts
faction collapses/restorations
city growth/decline
major disasters
```

Gate 21-D:

```text
- Timeline replay data exists.
- Replay/export can explain history over time.
- It connects to chronicles.
```

## Phase 21-E — Modding pipeline

Organise:

```text
scenario files
faction files
province files
character files
dynasty files
culture files
religion files
institution files
event template files
name lists
validation rules
```

Gate 21-E:

```text
- New content can be added without editing core code where possible.
- Validation runs against mod/scenario data.
- Data docs explain required fields.
```

## Phase 21 Closing Gate

Closed when:

```text
- The game can load scenarios.
- Dev can force events for testing.
- Balance dashboard can identify broken runs.
- Timeline replay exists.
- Modding/data folders are structured.
```

---

# PHASE 22 — Final Presentation, Map Art, UI Polish, Audio and Onboarding

## Goal

Make the finished systems beautiful, readable and satisfying to watch.

## Phase 22-A — Final map art pass

Polish:

```text
terrain
rivers
forests
trees
mountains
coasts
roads
ports
settlements
fortresses
battle markers
province borders
realm tint readability
```

Gate 22-A:

```text
- Map is readable at normal zoom.
- Rivers and trees are final-player quality.
- Province borders and realm colours are clear.
```

## Phase 22-B — Icon and marker system

Icons for:

```text
armies
sieges
battles
capitals
ports
trade hubs
holy sites
mana sites
revolts
famine
blockades
plague
disaster zones
```

Gate 22-B:

```text
- Map markers communicate important state without clutter.
- Icons have tooltips.
- Icons use consistent visual language.
```

## Phase 22-C — Final UI polish

Polish:

```text
province panel
realm panel
war panel
character panel
dynasty panel
institution panel
chronicle panel
timeline replay
scenario selector
tooltips
event cards
```

Gate 22-C:

```text
- UI is consistent.
- Copy/SPAG quality remains high.
- Debug language does not leak into normal UI.
```

## Phase 22-D — Audio and atmosphere

Audio cues:

```text
war declared
battle fought
siege started
ruler died
revolt started
peace signed
month/year passed
chronicle page turn
plague/disaster event
```

Gate 22-D:

```text
- Audio supports events without becoming annoying.
- Audio can be muted/configured.
```

## Phase 22-E — Tutorial and onboarding

Explain:

```text
what am I watching?
what do colours mean?
how do wars work?
why did this faction collapse?
how do characters matter?
how do dynasties matter?
how do I read the chronicle?
how do I use timeline replay?
how do I load scenarios?
```

Gate 22-E:

```text
- A new player can understand the observer loop.
- Onboarding does not require reading dev docs.
```

## Phase 22 Closing Gate

Closed when:

```text
- The game looks and reads like a serious grand-strategy observer sim.
- The UI explains the simulation.
- Presentation no longer feels like a prototype.
```

---

# PHASE 23 — Release, Long-Run Stability, Community and Support

## Goal

Turn the finished prototype into something people can use, test, share and build on.

## Phase 23-A — Long-run stability

Test:

```text
100-year simulation
250-year simulation
500-year simulation
multiple scenarios
many wars
many revolts
many faction collapses
timeline replay
save/load after major events
```

Gate 23-A:

```text
- No major memory leaks.
- No repeated broken references.
- Save/load survives long-run history.
- Dead-world and endless-chaos cases are measured.
```

## Phase 23-B — Performance profiling

Profile:

```text
map rendering
simulation ticks
event logs
chronicle generation
timeline replay
save/load
large faction counts
large character counts
```

Gate 23-B:

```text
- Performance is acceptable on target machines.
- Worst bottlenecks are known.
- Debug tools can measure sim speed.
```

## Phase 23-C — Release scenarios

Package scenarios:

```text
The War of Halem Bridge
The Red Bog Uprising
The Greyhook Succession Crisis
The First Lanter Trade War
The Qeresh Salt Crisis
The Fall of the Sevrin Canal
```

Gate 23-C:

```text
- Each scenario has intro text, major factions, tensions and expected chaos.
- Each scenario passes validation.
- Each scenario runs at least 50 years without catastrophic errors.
```

## Phase 23-D — Public build and docs

Prepare:

```text
GitHub Pages build
itch.io build
offline build
dev/debug build
observer guide
map guide
war guide
character guide
diplomacy guide
modding guide
validation error guide
```

Gate 23-D:

```text
- Public build is separated from dev/debug build.
- Docs explain how to play/watch and how to mod.
- Feedback path exists.
```

## Phase 23-E — Community support

Later features:

```text
custom scenarios
mod uploads
community-made factions
community timelines
exported chronicles
screenshots/gifs
shared world histories
```

Gate 23-E:

```text
- Community features do not compromise data safety.
- Modded content still validates.
```

## Phase 23 Closing Gate

Closed when:

```text
- Public build is stable.
- Docs exist.
- Testers can report issues.
- The project can support long-term expansion.
```

---

# Cross-System Integration Matrix

Every major system should connect to other systems.

```text
Characters -> families, courts, wars, schemes, memories, succession
Dynasties -> claims, marriage, succession, memory, diplomacy
Factions -> war, diplomacy, economy, institutions, culture, faith
Provinces -> resources, population, culture, faith, history, trade, revolt
Wars -> battles, sieges, claims, treaties, memory, exhaustion, economy
Institutions -> law, succession, economy, faith, revolts, diplomacy
Trade -> resources, ports, roads, treaties, raids, famine, cities
Naval -> ports, sea routes, blockades, piracy, amphibious movement
Culture -> identity, revolt, marriage, law, names, hybridisation
Religion -> legitimacy, sects, holy sites, law, institutions, revolt
Magic -> dynasties, law, religion, institutions, disasters, resources
Disasters -> economy, migration, succession, memory, revolt, culture
Scenario tools -> validation, balance, replay, modding, release
```

# Content Scaling Rules

Use these rules to avoid overbuilding.

```text
1. Build one vertical slice first.
2. Validate it.
3. Add UI/readability.
4. Run a 25-50 year test.
5. Only then scale content.
```

For faction count:

```text
8-12 = prototype core
16-20 = serious political test
35-50 = regional world
100+ = CK-style scale
```

For character count:

```text
Core phase = ruler, heir, commander, rival per major faction
Dynasty phase = close family only
Court phase = council and key nobles
World scale = wider noble families and minor figures
Release scale = enough characters for history, not infinite noise
```

# Definition of Done for Any Feature

A feature is Done only when:

```text
1. It has data.
2. It has logic.
3. It has validation.
4. It has UI or reporting.
5. It has save/load support if persistent.
6. It has at least basic tests.
7. It creates readable events if important.
8. It connects to at least one other system.
9. It does not leak debug wording into normal UI.
10. It survives a multi-year simulation.
```

# Recommended Immediate Next Order

The next short-term production order should be:

```text
1. Phase 1 — Data Validation Gate
2. Phase 2 — UI Copy/SPAG and Presentation Pass
3. Phase 3 — War Simulation Hardening
4. Phase 4 — Faction AI Priorities
5. Phase 5 — Character Core
6. Phase 6 — Family/Dynasty Systems
7. Phase 14-A/B — Faction Tiers and first major-power expansion to 16-20 powers
```

Do not push to 100+ political entities until character, dynasty, validation, UI copy and first expansion gates are passing.

# What was added beyond the previous roadmap

This master roadmap adds the missing AAA production structure:

```text
product pillars
production tracks
sub-phases A/B/C/D per phase
closing gates for every phase
acceptance criteria
cross-system integration matrix
content scaling rules
definition of done
short-term recommended order
vertical-slice thinking
validation-first workflow
UI copy quality gates
debug/player UI separation
long-run stability gates
performance gates
scenario/modding gates
release gates
```

It also adds or expands missing systems:

```text
court offices
social classes and population groups
law and justice
crime and punishment
secrets and espionage
non-state violence
mercenaries and bandits
technology and doctrine
education systems
magic consequences
climate and disasters
settlement growth
disease and plague
rituals and festivals
language/culture drift
religious sects
scenario tooling
balance dashboard
timeline replay
modding pipeline
long-run release testing
```

# Master principle

Do not build this as a pile of features.

Build it as a chain of gates:

```text
safe data -> readable UI -> working systems -> connected systems -> tested systems -> scaled content -> polished presentation -> stable release
```

That is how this becomes a real grand-strategy history simulator instead of a huge fragile spreadsheet with a map.
