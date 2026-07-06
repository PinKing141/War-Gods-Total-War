# War Gods: Total War — AAA-Style Master Development Roadmap

## Purpose

This is the master roadmap for turning War Gods: Total War from a working observer-sim prototype into a deep historical fantasy grand-strategy simulation.

The goal is not just to add features. The goal is to build the game in the right order, with clean dependency gates, test gates, content gates, quality gates, and player-facing presentation gates.

The end target is:

```text
A living world where factions, rulers, families, institutions, cultures, economies, wars, disasters, and memories generate believable history over centuries.
```

---

# 0. Roadmap rules

## 0.1 Core production rule

Every major feature must pass through:

```text
Design -> Data -> Simulation -> UI -> Validation -> Save/Load -> Balance -> Presentation -> Closing Gate
```

No phase is complete just because the data exists or the code runs once.

## 0.2 Definition of Done

A phase is only done when:

```text
1. Data exists.
2. Simulation logic uses it.
3. Player-facing UI displays it cleanly.
4. Debug UI can inspect it.
5. Validation catches broken references.
6. Save/load preserves it.
7. Event logs explain it.
8. The chronicle can mention it when relevant.
9. A short simulation test proves it works.
10. It does not break previous systems.
```

## 0.3 Debug vs player-facing rule

Normal UI must never show debug language.

```text
Normal UI = polished grand-strategy language
Debug UI = raw IDs, scores, references, validation details
```

Examples:

```text
Normal UI: Goal, Economy, Status, Strategic Value
Debug UI: faction_id, province_id, AI score, source CSV row
```

## 0.4 Content scale rule

Do not jump to 100+ factions too early.

Use world scaling gates:

```text
World Scale Gate 1: 16-20 serious powers
World Scale Gate 2: 35-50 total powers
World Scale Gate 3: 100+ political entities with tiers
```

## 0.5 Phase gate types

Each phase has smaller gates:

```text
A Gate = base data and schema complete
B Gate = simulation logic complete
C Gate = UI and player readability complete
D Gate = validation/save/load complete
E Gate = balance and long-run test complete
```

A phase should not move forward until its closing gate passes.

---

# 1. Current baseline and freeze gate

## Purpose

Lock down what already works before more systems are added.

## Current done areas

```text
old map decommission
layered map foundation
army supply
movement depth
basic attrition
first-pass siege depth
AI intent strings
peace summaries
observer readability first pass
```

## 1A. Baseline audit

### Build

Document current systems:

```text
map loading
province picking
realm tinting
army movement
war declaration
siege progress
peace resolution
monthly recap
province inspector
realm inspector
war inspector
```

### Interlinks

This phase links to every later phase because it defines the current stable foundation.

### Closing gate 1A

```text
Game launches without old map dependency.
Layered map loads normally.
Old procedural map only loads through explicit debug fallback.
Province picking still works.
Current sim can run at least 10 years without a crash.
```

## 1B. Baseline risk register

### Build

Create a living risk list:

```text
simulation crash risk
UI wording risk
data inconsistency risk
save/load break risk
performance risk
content bloat risk
map polish distraction risk
```

### Closing gate 1B

```text
Known risks are written down.
Each risk has an owner area, trigger, and mitigation.
No new major system starts without checking the risk register.
```

---

# 2. Data validation and technical quality gate

## Purpose

Stop the world from silently breaking as more factions, characters, provinces and systems are added.

This phase comes before deeper content.

## 2A. Core ID validation

### Build

Validate:

```text
province IDs
faction IDs
character IDs
army IDs
war IDs
claim IDs
institution IDs
religion IDs
culture IDs
scenario IDs
```

### Interlinks

Everything later depends on these references being valid.

### Closing gate 2A

```text
Duplicate IDs fail validation.
Missing IDs fail validation.
Error messages name the exact file, row, field and broken value.
```

## 2B. Relationship validation

### Build

Validate references:

```text
province controller exists
province owner exists
character faction exists
army owner exists
army location exists
adjacency links are valid
war attackers and defenders exist
war goals point to valid provinces
claims point to valid claimant and target
mage patron exists
institution home province exists
treaty parties exist
```

### Closing gate 2B

```text
No dangling references can enter the sim.
Every failed relation names the source object and target object.
```

## 2C. Numeric and gameplay bounds validation

### Build

Validate values:

```text
population >= 0
garrison >= 0
army size >= 0
treasury is valid
manpower is valid
fort level is valid
road level is valid
devastation is within range
supply is within range
opinion/relations are within range
```

### Closing gate 2C

```text
Invalid numbers fail before the sim starts.
Warnings exist for suspicious but legal values.
```

## 2D. Save/load and test harness

### Build

Add tests for:

```text
save after war
load after war
save after siege
load after siege
save after ruler death
load after ruler death
save after revolt
load after revolt
save after treaty
load after treaty
```

### Closing gate 2D

```text
All core systems survive save/load.
A 25-year smoke test passes.
Validation runs before scenario start.
```

---

# 3. UI copy, SPAG and presentation language gate

## Purpose

The normal UI must read like a finished grand-strategy game, not debug notes.

This must happen early, before UI bad habits spread across 20+ factions and hundreds of events.

## 3A. Player-facing copy audit

### Build

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

### Replace awkward labels

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

### Closing gate 3A

```text
No normal UI labels are written as questions.
No normal UI labels sound like debug/design notes.
All panel labels use consistent title case.
```

## 3B. Debug separation

### Build

Split UI into:

```text
normal UI
advanced tooltip
map debug mode
simulation debug mode
validation output
```

### Debug-only terms

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

### Closing gate 3B

```text
Raw IDs and internal scores appear only in debug views.
Normal UI shows readable names and clean labels.
```

## 3C. Event text polish

### Build

Rewrite event text so it explains causes naturally.

Good style:

```text
The Crown of Rov Halem goes to war to press its claim on Halem Bridge.
```

Bad style:

```text
Faction declares due to seeded risk and current chance.
```

### Closing gate 3C

```text
No player event text exposes raw simulation scoring.
All major events explain the visible reason in readable language.
```

---

# 4. Data architecture and scenario foundation

## Purpose

Prepare the data layout before the world grows.

## 4A. Data file structure

### Build

Separate files for:

```text
factions
provinces
characters
cultures
religions
houses
dynasties
institutions
wars
claims
treaties
resources
scenarios
event templates
name lists
```

### Closing gate 4A

```text
Each content type has a clear home.
No giant mixed data file becomes the only source of truth.
Validation can load every file type.
```

## 4B. Scenario loader foundation

### Build

A scenario should define:

```text
start date
active factions
province ownership
starting rulers
starting wars
starting claims
starting relations
starting resources
special crisis flags
```

### Closing gate 4B

```text
At least one scenario loads from scenario data.
Validation runs before loading.
Broken scenario data fails cleanly.
```

---

# 5. World Scale Gate 1: 16-20 serious powers

## Purpose

Expand beyond the small test core without jumping straight to 100+ countries.

## 5A. Faction tier support

### Build

Add political tiers:

```text
Tier 1 = great power / major realm
Tier 2 = regional power
Tier 3 = minor state / city-state / march / hold
Tier 4 = background or non-state actor
```

### Interlinks

Faction tiers affect:

```text
AI depth
character depth
chronicle priority
simulation cost
UI importance
balance reports
```

### Closing gate 5A

```text
Every faction has a valid tier.
Tier affects sim depth without breaking old factions.
UI displays tier using player-friendly wording.
```

## 5B. Add 8-12 new major or regional powers

### Build

Add new powers in different regions/archetypes:

```text
Lanter Sea naval league
northern highland realm
southern salt-road realm
eastern river confederation
western marcher realm
great religious protectorate
large forest court
large stone hold
orc war confederation
mage-law state
wealthy free-city league
nomad successor confederation
```

### Minimum data

Each new Tier 1 or Tier 2 power needs:

```text
id
name
identity
tier
government
culture
species
faith
capital
starting provinces
ruler
heir
commander
court rival
goal
rival
possible ally
starting claim
strategic role
```

### Closing gate 5B

```text
World has 16-20 serious political entities.
Each has a different role.
No new power is just a duplicate kingdom.
Validation passes.
```

## 5C. Regional balance pass

### Build

Run 25-50 year tests and check:

```text
one faction snowballs too fast
no faction ever fights
all factions collapse too quickly
new powers never interact
new powers lack border tension
```

### Closing gate 5C

```text
A 50-year run produces wars, peace, survival, collapse risk and border changes without total chaos.
```

---

# 6. Core simulation depth Phase 2

## Purpose

Make factions feel like political bodies with motives, stress, survival problems and internal weakness.

## 6A. Faction AI priorities

### Build

Give each faction weighted priorities:

```text
expand territory
protect homeland
recover old claims
raid for wealth
avoid war
secure trade routes
hold mountain passes
control ports
defend faith
destroy rival
survive economic stress
```

### Interlinks

AI priority considers:

```text
ruler traits
claims
relations
army strength
treasury
manpower
active wars
war exhaustion
strategic province value
neighbour weakness
institution demands
```

### Closing gate 6A

```text
Faction decisions are scored by profile and context.
Event logs explain major decisions in player language.
Different faction archetypes behave differently.
```

## 6B. Internal politics first pass

### Build

Add internal state values:

```text
court tension
succession tension
army influence
tax burden
faith tension
culture tension
regional autonomy
noble loyalty
merchant loyalty
```

### Closing gate 6B

```text
Strong factions can suffer internal instability.
Internal state affects war willingness, taxes, revolt risk and succession.
```

## 6C. Revolts and instability

### Build

Province instability comes from:

```text
devastation
occupation
recent conquest
low garrison
culture mismatch
faith mismatch
high taxes
famine
weak ruler
foreign support
```

Revolt types:

```text
peasant revolt
noble revolt
separatist revolt
religious uprising
pretender revolt
military coup
frontier independence
```

### Closing gate 6C

```text
Revolts can start, fight, win, lose and be recorded.
Revolt causes are visible in UI and event logs.
Revolt risk is validated and save/load safe.
```

## 6D. Succession and ruler death expansion

### Build

Add:

```text
inheritance law
heir legitimacy
regency
pretender claims
succession crisis
powerful generals backing claimants
court factions backing heirs
ruler death consequences
```

### Closing gate 6D

```text
Ruler death can cause stable succession, regency or crisis.
Succession results update ruler, heir, claims, faction state and chronicle.
```

## 6E. Simple survival economy

### Build

Track:

```text
treasury
income
army upkeep
war debt
tax burden
food stress
trade value
devastation loss
tribute payments
```

Decisions:

```text
raise taxes
lower taxes
seek peace
dismiss armies
borrow money
sell privileges
squeeze conquered land
risk unrest
```

### Closing gate 6E

```text
Economy affects war decisions, unrest, peace desire and faction survival.
UI labels stay polished: Economy, Treasury, Taxation, Food.
```

---

# 7. Character life, traits, relationships and personal ambition

## Purpose

Make history personal. Factions should not be the only actors.

## 7A. Character schema expansion

### Build

Characters need:

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

### Closing gate 7A

```text
Characters validate correctly.
Character inspector can show core identity cleanly.
Save/load preserves character state.
```

## 7B. Ambitions and fears

### Build

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
escape court
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

### Interlinks

Ambitions and fears affect:

```text
war support
marriage choices
schemes
succession behaviour
battle risk
loyalty
betrayal chance
```

### Closing gate 7B

```text
At least rulers and commanders use ambition/fear in decisions.
Event logs explain character-driven choices naturally.
```

## 7C. Relationship system

### Build

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

### Closing gate 7C

```text
Relationships validate both ends.
Relationships affect loyalty, schemes, succession and diplomacy.
Character panel displays important relationships.
```

## 7D. Personal memories and military record

### Build

Track:

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
```

Military record:

```text
battles fought
battles won
battles lost
sieges led
wounds
notable victories
notable defeats
```

### Closing gate 7D

```text
Characters remember major events.
Memories can create grudges, loyalty and reputation.
Character biographies become possible later.
```

---

# 8. Family trees, houses, dynasties and inheritance

## Purpose

Make long-term history generational.

## 8A. Family tree data

### Build

Each character can store:

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

### Closing gate 8A

```text
Family links validate.
No impossible parent/child loops.
Character panel shows close family.
```

## 8B. Dynasty and house system

### Build

Dynasty fields:

```text
id
name
founder
culture
faith
home province
prestige
renown
famous ancestors
rivals
alliances
bloodline traits
cadet branches
```

House fields:

```text
id
dynasty
name
founder
head
home province
legitimacy
prestige
living members
```

### Closing gate 8B

```text
Dynasties and houses validate.
House heads update correctly.
Dynasty panel can show founder, head, members, claims and rivals.
```

## 8C. Cadet branches, bastards and legitimacy

### Build

Cadet branches can form when:

```text
younger child receives land
exiled prince survives
bastard is legitimised
succession splits
ruler loses capital but keeps land
marriage creates merged claim
```

### Closing gate 8C

```text
Cadet branches can form without breaking dynasty trees.
Legitimacy affects inheritance, claims and faction support.
```

## 8D. Inheritance and claims

### Build

Claim sources:

```text
parents
marriage
dynasty history
lost titles
faith blessing
adoption
legitimisation
old treaty
fabricated claim
popular support
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

### Closing gate 8D

```text
Succession uses family tree data.
Claims can pass through bloodline and marriage.
Claim wars become character/dynasty-driven.
```

---

# 9. Courts, social groups, law and justice

## Purpose

Make realms more than rulers and armies.

## 9A. Court and office system

### Build

Court roles:

```text
ruler
heir
chancellor
marshal
steward
spymaster
court mage
high priest
captain of guard
governor
regent
```

### Closing gate 9A

```text
Important characters can hold offices.
Offices affect faction decisions and internal tension.
```

## 9B. Social groups inside provinces

### Build

Population groups:

```text
nobles
clergy
merchants
peasants
craftsmen
soldiers
mages
scholars
minorities
tribes
foreign settlers
refugees
urban poor
```

Each group tracks:

```text
size
loyalty
unrest
needs
wealth
influence
```

### Closing gate 9B

```text
Province society affects tax, unrest, recruitment, culture and faith tension.
UI shows readable summaries, not raw spreadsheets.
```

## 9C. Law, crime and justice

### Build

Law areas:

```text
inheritance law
tax law
military obligation
religious law
merchant law
noble privilege
trial system
hostage law
exile
execution
imprisonment
pardon
```

Crime and disorder:

```text
banditry
corruption
treason
smuggling
heresy
noble violence
urban unrest
```

### Closing gate 9C

```text
Law affects succession, taxation, unrest, imprisonment, executions and legitimacy.
Character and province events can reference law outcomes.
```

---

# 10. Historical memory and living chronicle

## Purpose

Make the world remember, then make memory shape the future.

## 10A. Memory object system

### Build

Memories can belong to:

```text
character
family
house
dynasty
faction
province
war
institution
culture
faith
```

Memory fields:

```text
id
type
date
actors
victims
location
importance
decay
description
future effect
```

### Closing gate 10A

```text
Major events create memories.
Memories validate and survive save/load.
```

## 10B. Grievances and loyalties

### Build

Factions and characters remember:

```text
lost land
slain ruler
betrayal
broken treaty
humiliation
liberation
saved life
marriage alliance
shared victory
religious persecution
```

### Closing gate 10B

```text
Memories affect AI decisions.
War and diplomacy reasons can reference old events naturally.
```

## 10C. Chronicle generation

### Build

Generate:

```text
monthly chronicle
yearly annals
war history
ruler biography
faction rise/fall summary
battle summary
province history
dynasty record
```

### Closing gate 10C

```text
The chronicle can explain what changed and why it mattered.
Yearly annals read like history, not raw logs.
```

## 10D. Province/faction/character history panels

### Build

Panels show:

```text
previous rulers/owners
major battles
sieges
revolts
famous characters
dynasty changes
faith/culture changes
notable disasters
```

### Closing gate 10D

```text
Clicking a province, faction or character shows meaningful history.
History data is not just hidden in logs.
```

---

# 11. Culture, faith, identity and sects

## Purpose

Make identity evolve and matter over time.

## 11A. Culture system

### Build

Culture fields:

```text
language group
naming style
martial customs
burial customs
food customs
honour code
festival traditions
elite/common divide
frontier variant
```

Culture changes:

```text
assimilation
hybridisation
diaspora
elite adoption
frontier culture birth
cultural revolt
```

### Closing gate 11A

```text
Culture affects unrest, marriage, diplomacy, recruitment and province identity.
Culture can change slowly over time.
```

## 11B. Faith and sect system

### Build

Faith features:

```text
holy sites
pilgrimage
religious law
priesthood
saints
martyrs
heresies
schisms
miracle claims
persecution
conversion
religious wars
```

### Closing gate 11B

```text
Faith affects legitimacy, unrest, institutions, laws, diplomacy and war goals.
Religious changes are recorded in the chronicle.
```

## 11C. Identity conflict and integration

### Build

Systems for:

```text
minority rights
elite culture mismatch
religious tolerance
forced conversion
cultural autonomy
frontier settlement
refugee communities
```

### Closing gate 11C

```text
Identity conflict can cause unrest, compromise, revolt or integration.
UI uses clean labels: Culture, Faith, Autonomy, Unrest.
```

---

# 12. Institutions and power structures

## Purpose

Make power exist outside rulers.

## 12A. Institution schema

### Build

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

Fields:

```text
id
name
type
home province
influence
wealth
loyalty
goal
supported ruler/faction
rivals
key characters
```

### Closing gate 12A

```text
Institutions validate.
Realm and province panels can show important institutions.
```

## 12B. Institution actions

### Build

Institutions can:

```text
support ruler
oppose ruler
back pretender
fund revolt
push war
oppose tax
protect holy site
support trade
sponsor mage law
raise military order troops
```

### Closing gate 12B

```text
Institutions affect succession, war support, economy, law and unrest.
Events explain when an institution influenced a decision.
```

## 12C. Institution memory and rivalries

### Build

Institutions remember:

```text
privileges granted
privileges revoked
persecution
land grants
betrayal
sacked temple
declared heresy
merchant debt
mage disaster
```

### Closing gate 12C

```text
Institution history affects future loyalty and demands.
Chronicle can mention institutions as actors.
```

---

# 13. Diplomacy, treaties and international politics

## Purpose

Make factions interact through negotiation, threats, dependency and manipulation, not only war.

## 13A. Treaty system

### Build

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

Treaty fields:

```text
id
type
parties
start date
end date
terms
obligations
penalties
hostages
marriage link
memory entry
```

### Closing gate 13A

```text
Treaties validate, save/load and expire correctly.
Active treaties appear in faction UI.
```

## 13B. Diplomacy AI

### Build

AI evaluates:

```text
need for allies
fear of neighbours
old grievances
family ties
treaty obligations
economy
institutions
ruler traits
military strength
war exhaustion
```

### Closing gate 13B

```text
Factions can choose alliance, tribute, peace, threat or meddling when war is not ideal.
Event reasons are readable.
```

## 13C. Coalitions and containment

### Build

Coalition triggers:

```text
rapid expansion
broken treaties
sacked major city
religious threat
holding sacred land
murdered ruler
oppressed institution
high infamy
```

### Closing gate 13C

```text
Large powers can be contained.
Coalitions form and dissolve with clear causes.
```

## 13D. Foreign meddling

### Build

Actions:

```text
fund rebels
back pretender
shelter exile
send weapons
bribe noble
support religious unrest
hire raiders
sabotage trade
```

### Closing gate 13D

```text
Factions can harm enemies without direct war.
Meddling creates memories and diplomatic consequences.
```

---

# 14. Trade, economy and resource networks

## Purpose

Make land valuable for reasons beyond map colour.

## 14A. Province resources

### Build

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
```

Each province starts with:

```text
primary resource
optional secondary resource
resource output
local demand
strategic value
```

### Closing gate 14A

```text
Province resources validate.
Resources appear in province UI.
Faction AI can recognise resource value.
```

## 14B. Food and survival economy

### Build

Track:

```text
food production
food demand
food storage
famine risk
army food use
siege starvation
devastation crop loss
food imports
```

### Closing gate 14B

```text
Food affects unrest, army supply, siege endurance and faction survival.
Famine events can occur and be recorded.
```

## 14C. Trade routes

### Build

Routes connect:

```text
capital to port
mine to city
farm region to market
oasis to desert town
pass to trade hub
river to merchant city
```

Disruption from:

```text
war
siege
occupation
raids
rebellion
devastation
bad relations
blockades later
```

### Closing gate 14C

```text
Trade routes create value.
Disruption affects economy and diplomacy.
UI shows routes clearly without debug labels.
```

## 14D. Strategic resource dependency

### Build

Effects:

```text
grain = stability and army food
iron = army quality
horses = mobility and cavalry
timber = siege/naval preparation
salt = food preservation and wealth
mana = mage institutions
silver = treasury strength
```

### Closing gate 14D

```text
Factions value provinces for resources.
Resource shortages can change war, trade and treaty choices.
```

---

# 15. Non-state actors: mercenaries, bandits, orders, pirates and rebels

## Purpose

Make the world contain dangerous actors that are not normal countries.

## 15A. Non-state actor schema

### Build

Types:

```text
mercenary company
bandit realm
raider band
pirate haven
rebel army
religious militia
frontier warband
disgraced knight company
exiled claimant band
mage circle
```

Fields:

```text
id
name
type
leader
home region
strength
wealth
loyalty
employer
rivals
ambition
```

### Closing gate 15A

```text
Non-state actors validate and can appear on the map or in events.
They do not require full country simulation at first.
```

## 15B. Mercenary and hiring system

### Build

Mercenaries can:

```text
accept contracts
switch sides if unpaid
loot after war
become famous
found a state if powerful
```

### Closing gate 15B

```text
Factions can hire mercenaries.
Unpaid mercenaries create risk.
Mercenary records appear in chronicle when important.
```

## 15C. Bandit, raider and rebel escalation

### Build

Non-state violence can escalate:

```text
banditry -> rebel band -> local warlord -> minor state
piracy -> pirate haven -> sea league threat
religious militia -> holy order -> theocratic state
```

### Closing gate 15C

```text
Small threats can become historical actors.
Validation and balance prevent endless chaos.
```

---

# 16. Espionage, secrets and schemes

## Purpose

Make politics less clean and more personal.

## 16A. Secret system

### Build

Secrets:

```text
illegitimate child
hidden claimant
forged document
secret lover
heresy
murder plot
treason
bribery
mage corruption
debt
cowardice
betrayal
```

### Closing gate 16A

```text
Secrets validate, are discoverable, and can affect relationships or legitimacy.
```

## 16B. Scheme system

### Build

Schemes:

```text
support claimant
undermine rival
seek marriage
forge claim
bribe commander
spread rumour
sabotage peace
defect
hide claimant
arrange escape
```

### Closing gate 16B

```text
Characters and institutions can run simple schemes.
Schemes have progress, success, failure and consequences.
```

## 16C. Spy networks and counterplay

### Build

Add:

```text
spymaster office
spy network strength
counter-intelligence
informants
blackmail
exposure events
```

### Closing gate 16C

```text
Espionage affects diplomacy, succession, revolt and war without becoming random noise.
```

---

# 17. Technology, doctrine and knowledge

## Purpose

Create era progression without turning the game into a rigid 4X tech tree.

## 17A. Knowledge schools

### Build

Knowledge areas:

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
law scholarship
```

### Closing gate 17A

```text
Factions and institutions can hold knowledge strengths.
Knowledge affects economy, war, law and disaster response.
```

## 17B. Doctrine and army evolution

### Build

Doctrine changes:

```text
infantry discipline
cavalry tradition
raiding doctrine
siege craft
mountain warfare
river crossing skill
naval doctrine later
mage battlefield doctrine
```

### Closing gate 17B

```text
Army quality can improve through culture, institutions, resources and experience.
```

## 17C. Lost knowledge and breakthroughs

### Build

Events:

```text
rediscovered archive
captured engineer
mage theory scandal
plague medicine breakthrough
fortification reform
shipwright school founded
```

### Closing gate 17C

```text
Knowledge events create memories and long-term realm identity.
```

---

# 18. Disasters, disease, climate and world shocks

## Purpose

History should not only be caused by rulers.

## 18A. Disaster framework

### Build

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
coastal storm
river drying
volcanic winter
```

### Closing gate 18A

```text
Disasters can target provinces or regions.
Effects are bounded and validated.
```

## 18B. Disease and plague

### Build

Disease affects:

```text
population
rulers
heirs
armies
trade routes
court stability
succession
faith events
```

### Closing gate 18B

```text
Plague can kill characters, weaken armies and trigger succession without destroying every run.
```

## 18C. Climate and long-term stress

### Build

Climate affects:

```text
food
migration
trade
war season
nomad movement
river value
famine
frontier settlement
```

### Closing gate 18C

```text
Climate creates strategic change over years, not random punishment every month.
```

---

# 19. Magic consequences and rare mana politics

## Purpose

Make fantasy matter mechanically without turning the world into generic spell spam.

## 19A. Mana site system

### Build

Mana sites track:

```text
location
purity
output
risk
controlling faction
mage institution
faith opinion
local unrest
```

### Closing gate 19A

```text
Mana sites affect institutions, politics, economy and conflict.
UI treats them as rare strategic features.
```

## 19B. Mage law and social fear

### Build

Add:

```text
mage registration
court mage office
illegal sorcerers
anti-mage laws
mage sanctuary
mage persecution
mage rebellion
```

### Closing gate 19B

```text
Factions can differ in mage policy.
Mage policy affects institutions, faith tension, events and diplomacy.
```

## 19C. Magical disaster and bloodlines

### Build

Add:

```text
mana sickness
cursed bloodline
mana-touched lineage
battlefield magic trauma
forbidden school scandal
mana site corruption
```

### Closing gate 19C

```text
Magic creates long-term memories, risks and dynasty consequences.
```

---

# 20. Naval power, sea trade and coastal warfare

## Purpose

Make seas, ports and coastal cities strategically valuable.

## 20A. Port system

### Build

Port province fields:

```text
port level
dock capacity
naval supply
shipbuilding value
coastal defence
trade value
merchant presence
```

### Interlinks

Ports connect to:

```text
trade routes
food imports
naval fleets
blockades
merchant institutions
coastal sieges
piracy
```

### Closing gate 20A

```text
Ports validate.
Ports affect economy and trade.
Province UI shows Harbour/Port data in player-friendly wording.
```

## 20B. Fleet objects

### Build

Fleet fields:

```text
id
owner
home port
location
ships
quality
commander
mission
supply
transport capacity
```

### Closing gate 20B

```text
Fleets can exist, move between sea zones/ports and survive save/load.
Fleet ownership and location validate.
```

## 20C. Fleet missions

### Build

Missions:

```text
patrol
escort trade
blockade port
raid coast
transport army
intercept enemy fleet
protect strait
hunt pirates
```

### Interlinks

Fleet missions affect:

```text
trade
food imports
war exhaustion
merchant loyalty
coastal siege speed
pirate risk
```

### Closing gate 20C

```text
Each mission has a visible effect.
Event logs explain naval actions cleanly.
```

## 20D. Sea routes and blockades

### Build

Sea routes can be:

```text
safe
contested
raided
blockaded
closed by war
controlled by treaty
```

Blockades affect:

```text
trade income
food imports
war exhaustion
merchant loyalty
city unrest
coastal siege progress
```

### Closing gate 20D

```text
Blockades work with trade, war and siege systems.
Port UI and war UI show blockade state.
```

## 20E. Army transport and amphibious movement

### Build

Rules:

```text
army size must fit transport capacity
embark from port first
disembark at valid coastal province first
landing causes supply penalty
enemy fleets can intercept later
```

### Closing gate 20E

```text
Armies cannot teleport across water.
Naval transport works and validates.
A 25-year coastal war test passes.
```

---

# 21. World Scale Gate 2: 35-50 political entities

## Purpose

Expand the world after the major systems can support more actors.

## 21A. Regional minor states

### Build

Add:

```text
duchies
marches
city-states
merchant republics
tribal confederations
clan holds
religious states
mage domains
free cities
nomad rings
frontier forts
island powers
```

### Closing gate 21A

```text
World reaches 35-50 entities.
Tier 3 entities use lighter simulation.
Validation and performance remain stable.
```

## 21B. Regional conflict web

### Build

Every region should have:

```text
1 dominant power
1 rival regional power
2-5 minor neighbours
1 non-state actor
1 institution conflict
1 resource/trade reason for conflict
```

### Closing gate 21B

```text
Every region has tension, not just names on a map.
```

## 21C. 100-year balance test

### Build

Run checks for:

```text
faction survival
war frequency
revolt frequency
succession crises
trade disruption
non-state actor growth
performance
chronicle readability
```

### Closing gate 21C

```text
100-year sim runs without crash.
No region is permanently dead unless designed that way.
```

---

# 22. Scenario tools, debug controls and modding pipeline

## Purpose

Make the project controllable, testable and expandable.

## 22A. Scenario tools

### Build

Scenario files support:

```text
start date
active factions
province ownership
rulers
wars
treaties
institutions
resources
culture/faith setup
special crisis setup
```

### Closing gate 22A

```text
Multiple scenarios can load.
Broken scenarios fail validation cleanly.
```

## 22B. Developer debug controls

### Build

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

### Closing gate 22B

```text
Debug controls are separate from normal UI.
Each control updates sim state correctly.
```

## 22C. Balance dashboard

### Build

Track:

```text
strongest factions
richest factions
unstable factions
war counts
revolt counts
average war length
faction collapse rate
food stress
economy collapse frequency
empire snowball rate
dead-world periods
```

### Closing gate 22C

```text
Balance dashboard exposes problems before content expansion.
Reports can be exported or copied.
```

## 22D. Timeline replay

### Build

Replay tracks:

```text
province ownership changes
war starts and ends
ruler changes
major battles
revolts
faction collapses
restorations
treaty changes
disaster events
```

### Closing gate 22D

```text
The user can inspect history by year or major event.
Timeline data survives save/load.
```

## 22E. Modding/data pipeline

### Build

Support safe editing of:

```text
scenarios
factions
characters
provinces
cultures
faiths
institutions
event templates
name lists
```

### Closing gate 22E

```text
New content goes through validation.
Modded scenarios do not require code edits for simple additions.
```

---

# 23. World Scale Gate 3: 100+ political entities

## Purpose

Reach CK-style political scale after systems, tools and validation can carry it.

## 23A. 100+ entity data expansion

### Build

World composition target:

```text
9-12 great powers
20-30 regional powers
40-60 minor states
20-40 tribes, city-states, holds, marches and leagues
10-20 non-state military/religious/economic actors
```

### Closing gate 23A

```text
World has 100+ entities with tiers.
Only important entities get full depth immediately.
Performance remains acceptable.
```

## 23B. Content density pass

### Build

Every region gets:

```text
political tension
dynasty tension
resource tension
faith/culture tension
trade route tension
institution tension
non-state threat
possible crisis
```

### Closing gate 23B

```text
The world is dense enough to produce history without scripted events.
```

## 23C. Long-run world stability

### Build

Run:

```text
100-year test
250-year test
500-year test
multiple seeds
multiple scenarios
```

### Closing gate 23C

```text
The world can survive centuries.
History remains readable.
The sim does not become permanent chaos or permanent peace.
```

---

# 24. Presentation, art polish and player-facing feel

## Purpose

Return to visuals only after the systems underneath are worth presenting.

## 24A. Map art pass

### Build

Polish:

```text
terrain look
coasts
province borders
realm tint readability
roads
ports
settlements
fortresses
mountains
forests
```

### Closing gate 24A

```text
Map is readable at normal zoom.
Borders and realm tint do not hide terrain or icons.
```

## 24B. Rivers and trees final pass

### Build

Add final:

```text
cartographic rivers
major river hierarchy
forest/tree visuals
terrain mask blending
```

### Closing gate 24B

```text
Rivers and trees look intentional, not debug-generated.
They improve readability instead of cluttering the map.
```

## 24C. Icon and marker system

### Build

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
```

### Closing gate 24C

```text
Map icons communicate state quickly.
Icons do not overlap badly at normal zoom.
```

## 24D. UI polish

### Build

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

### Closing gate 24D

```text
UI feels consistent.
No debug language leaks into normal UI.
Panels are readable and not overlong.
```

## 24E. Sound, ambience and onboarding

### Build

Add subtle feedback for:

```text
war declared
battle fought
siege started
ruler died
revolt started
peace signed
month/year passed
chronicle page turn
```

Onboarding explains:

```text
what am I watching
what colours mean
how wars work
how to read the chronicle
why realms collapse
how timeline replay works
```

### Closing gate 24E

```text
A new user can understand observer mode without reading source docs.
Sound supports events without becoming annoying.
```

---

# 25. Release, community and long-term support

## Purpose

Turn the finished prototype into something people can use, test, share and build on.

## 25A. Stability and performance

### Build

Test:

```text
100 years
250 years
500 years
many wars
many revolts
many faction collapses
timeline replay
save/load after major events
multiple browsers
```

### Closing gate 25A

```text
No major memory leak.
No common crash.
Performance budget is documented.
Long-run simulation remains usable.
```

## 25B. Balance and tuning

### Build

Reports for:

```text
faction survival rate
average war length
revolt frequency
succession crisis frequency
economy collapse frequency
empire snowball rate
no-war periods
naval blockade frequency
non-state actor growth
```

### Closing gate 25B

```text
The world produces interesting outcomes without constant manual fixing.
```

## 25C. Scenario packaging

### Build

Official scenarios:

```text
The War of Halem Bridge
The Red Bog Uprising
The Greyhook Succession Crisis
The First Lanter Trade War
The Qeresh Salt Crisis
The Fall of the Sevrin Canal
```

Each scenario needs:

```text
intro text
major factions
starting tensions
special rules
expected chaos
recommended watch points
```

### Closing gate 25C

```text
Scenarios feel intentional, not random start states.
Each can run 50 years without breaking.
```

## 25D. Documentation

### Build

Docs:

```text
observer guide
map guide
war guide
character/dynasty guide
diplomacy guide
economy guide
scenario guide
modding guide
validation error guide
```

### Closing gate 25D

```text
A new player can understand the game.
A modder can add simple content without asking the developer.
```

## 25E. Public build

### Build

Prepare:

```text
GitHub Pages build
itch.io build
offline web build
dev/debug build kept separate
feedback/reporting path
known issues list
```

### Closing gate 25E

```text
Public build works without debug tools exposed by default.
Feedback path is clear.
Version is tagged.
```

---

# 26. Backlog for future expansions

These should not block first release.

```text
multiplayer
persistent online worlds
cloud saves
community scenario browser
mod uploads
advanced naval combat
advanced economy/prices
full public editor
animated battle viewer
AI-generated chronicle voiceover
large-scale procedural world generation
```

---

# 27. Master order summary

```text
1. Current baseline and freeze gate
2. Data validation and technical quality gate
3. UI copy, SPAG and presentation language gate
4. Data architecture and scenario foundation
5. World Scale Gate 1: 16-20 serious powers
6. Core simulation depth Phase 2
7. Character life, traits, relationships and personal ambition
8. Family trees, houses, dynasties and inheritance
9. Courts, social groups, law and justice
10. Historical memory and living chronicle
11. Culture, faith, identity and sects
12. Institutions and power structures
13. Diplomacy, treaties and international politics
14. Trade, economy and resource networks
15. Non-state actors
16. Espionage, secrets and schemes
17. Technology, doctrine and knowledge
18. Disasters, disease, climate and world shocks
19. Magic consequences and rare mana politics
20. Naval power, sea trade and coastal warfare
21. World Scale Gate 2: 35-50 political entities
22. Scenario tools, debug controls and modding pipeline
23. World Scale Gate 3: 100+ political entities
24. Presentation, art polish and player-facing feel
25. Release, community and long-term support
```

---

# 28. Master closing gate before release

The game is ready for a serious public build only when:

```text
validation passes
normal UI has no debug wording
100-year sim works
250-year sim works
500-year sim works at least once
save/load survives major events
world has meaningful actors beyond factions
characters and dynasties affect history
diplomacy and economy affect war choices
naval systems matter on coasts
chronicle produces readable history
scenario tools work
public build hides debug by default
documentation exists
```

The final target is not just a big map. The final target is a world that can produce believable history without the player forcing it.
