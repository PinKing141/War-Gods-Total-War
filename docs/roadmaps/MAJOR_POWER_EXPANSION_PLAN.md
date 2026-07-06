# Major power expansion plan

## Purpose

The current seed frontier has enough factions for testing, but not enough for a CK-style political world. The goal is to add more major powers without breaking the simulation or turning every faction into an over-detailed content burden.

## Current state

The seed frontier currently has the core test powers:

```text
Crown of Rov Halem
Red Bog Hearth League
Open Gate Freehold
West Gear Compact
Third Charter House
Blue Chain Counting House
White Mare Ring
Hallow of the Ninth Banner
```

These should remain the first test core. New major powers should expand around them instead of replacing them.

## Rule

Do not jump straight to 100 fully simulated countries.

Use staged political expansion:

```text
Stage 1: 8-12 core test powers
Stage 2: 16-20 major and regional powers
Stage 3: 35-50 total powers
Stage 4: 100+ powers with tiers and lighter simulation for minor states
```

## Faction tiers

Every political entity should have a tier.

```text
Tier 1 = great power / major realm
Tier 2 = regional power
Tier 3 = minor state / city-state / march / hold
Tier 4 = background or non-state actor
```

Tier 1 and Tier 2 powers get deeper AI, rulers, dynasties, institutions and historical memory first.

Tier 3 and Tier 4 can use lighter simulation until they become important.

## How to add more major powers safely

### Step 1: choose regions first

Before naming countries, divide the world into political regions.

Suggested region slots:

```text
Rov Basin
Cairn March
Greyhook Spine
Taluun Steppe
Maren Coast
Qeresh Wells
Fenward
Bannerfields
Lanter Sea coast
northern highlands
southern drylands
eastern riverlands
western passes
island/coastal chains
```

Each region should have:

```text
1 dominant major power
1 rival regional power
2-5 minor neighbours
1 pressure actor such as a temple, guild, warband or free city
```

### Step 2: add only 8-12 new major/regional powers first

The next expansion should add about 8-12 factions, not 100.

Recommended new major-power slots:

```text
1. Lanter Sea thalassocracy or naval league
2. Northern highland kingdom
3. Southern dryland/salt-road kingdom
4. Eastern river empire or river confederation
5. Western pass marcher kingdom
6. Great religious state or holy protectorate
7. Large elven forest court/enclave federation
8. Large dwarf mountain hold/stone league
9. Orc war confederation beyond Open Gate
10. Mage-law state or mana-site protectorate
11. Wealthy free-city league
12. Nomad/steppe successor confederation
```

Do not make all of these identical kingdoms.

## Minimum data for each new major power

Every new major power needs:

```text
faction_id
name
short_name
identity
tier
dominant_culture
dominant_species
religion_id
government
capital_province
starting_provinces
ruler_id
dynasty_or_house_id
primary_goal
secondary_goal
conflict_pressure
rivals
allies
institution_pressure
starting_claims
starting_treaties
strategic_role
```

## Minimum character data

Every new major power needs at least:

```text
ruler
heir
chief general
court rival
religious/institutional pressure figure
merchant/noble/mage pressure figure if relevant
```

Minor powers do not need this full set at first.

## Minimum province data

A new major power should normally control:

```text
capital province
2-6 core provinces
1-3 contested border provinces or claims
1 strategic feature such as port, pass, river crossing, mine, holy site or market
```

Avoid huge blobs unless the faction is supposed to be a major empire.

## Major power archetypes

Use archetypes so each major faction has a different gameplay role.

```text
canal monarchy = road/river legitimacy and bureaucracy
hearth league = iron, oath-council and defensive power
freehold republic = anti-yoke independence and military citizenship
pass compact = mountain tolls, engineering and defensive warfare
charter court = ancient contracts, law and elven diplomacy
merchant house = debt, trade and diplomacy
horse ring = raiding, mobility and tribute
temple order = legitimacy, holy war and mage-law disputes
sea league = naval power, ports and merchant convoys
salt kingdom = desert logistics, oasis control and food pressure
forest court = long memory, border secrecy and sacred groves
imperial remnant = restoration claims and legitimacy drama
mage protectorate = mana law, magical risk and elite influence
frontier march = military defense and border colonisation
city league = money, autonomy and mercenary contracts
nomad confederation = seasonal movement, raiding and succession splits
```

## Expansion workflow

```text
1. Pick 8-12 new faction slots.
2. Assign each to a region.
3. Assign each a unique government/archetype.
4. Give each a capital and province cluster.
5. Give each one immediate enemy and one possible ally.
6. Give each one strategic reason to exist.
7. Add ruler/heir/general/rival characters only for Tier 1 and Tier 2.
8. Add claims and relations.
9. Run validation.
10. Simulate 25-50 years and check collapse/snowball behaviour.
```

## What not to do

```text
Do not add 100 factions at once.
Do not make every faction a kingdom.
Do not give every minor power full dynasty/institution data immediately.
Do not add visual map polish during this phase.
Do not expand names/content without connecting them to simulation systems.
```

## Codex task

```text
Begin staged major power expansion.

Tasks:
1. Keep the existing seed frontier powers as the test core.
2. Add faction tier support if it does not already exist.
3. Add 8-12 new Tier 1 or Tier 2 powers first, not 100.
4. Assign each new power a region, capital province, starting provinces, government, culture, religion, species, goal, pressure, rival and ally.
5. Add at least ruler, heir, commander and court rival characters for each Tier 1 or Tier 2 faction.
6. Add claims and relation entries connecting new powers to existing powers.
7. Make validation cover all new faction, province, ruler, culture, religion, relationship and claim references.
8. Keep Tier 3 and Tier 4 factions lighter until the simulation proves stable.
9. Run a 25-50 year simulation balance check after expansion.
10. Do not add map cosmetics, rivers, trees or huge unused content packs during this phase.
```
