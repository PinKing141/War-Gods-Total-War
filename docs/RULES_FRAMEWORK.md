# Campaign Rules Framework

This document turns the spreadsheet-first campaign concept into enforceable operating rules. The core principle is simple: the workbook and runtime state are the campaign engine. Narration explains outcomes after the data, formulas, and logged rolls resolve them.

## 1. Source of Truth

1. The official campaign state is the combination of the SQLite runtime database, the generated workbook, and the turn-resolution logs produced from them.
2. If an asset is not recorded in official state, it does not exist for orders or narration.
3. Players may only issue orders with assets available at the start of the current turn, unless a rule explicitly allows mid-turn availability.
4. No player may invent troops, gold, supplies, construction progress, diplomatic agreements, intelligence, casualties, weather, or victories by narration.
5. All permanent changes must be produced by formulas, validated orders, deterministic service logic, or a logged dice/random resolution.

## 2. Campaign Scale

The default campaign scale is one monthly turn. A month is long enough for taxation, supply consumption, construction progress, recruitment progress, local movement, intelligence activity, and political reactions to occur. Tactical battles may be resolved inside a turn, but their consequences are applied before the turn summary is finalized.

Recommended scale conventions:

| Area | Default scale |
| --- | --- |
| Turn length | 1 month |
| Population | Individual people |
| Manpower | Recruitable people, tracked separately from total population when implemented |
| Money | Campaign currency units |
| Food | Abstract stores convertible to months of civilian and military consumption |
| Resources | Stockpiled units with monthly production and consumption |
| Unit strength | Individual soldiers grouped into units |
| Movement | Kilometers per day converted into monthly operational movement |
| Morale, loyalty, support, fatigue | 0-100 unless a sheet explicitly states otherwise |

## 3. Workbook Visibility

The master state contains the truth. Player-facing views contain only what that player could know.

### Master State

The master state may include hidden armies, true troop counts, spy identities, secret diplomacy, inactive event triggers, exact resource stockpiles, and real order queues for every faction.

### Player State

The player state should include owned assets, public information, confirmed reports, estimates, rumors, and aged intelligence. Enemy information should use ranges and confidence values unless the player has current confirmed intelligence.

### Intelligence Records

Every intelligence item should record source, target, reported claim, confidence, information age, mission risk, and whether the report is confirmed or rumored. Old reports should not silently update themselves; a report gathered on Turn 12 remains a Turn 12 report until refreshed.

## 4. Turn Sequence

Each turn should be resolved in this order unless a scenario-specific rule overrides it:

1. Start-of-turn snapshot and backup.
2. Weather, season, and global event checks.
3. Harvest, production, spoilage, and trade-price updates.
4. Income collection.
5. Mandatory expenses, upkeep, interest, and shortage checks.
6. Recruitment progress and training updates.
7. Construction progress and repair updates.
8. Player orders validated against official state.
9. Movement, route, fatigue, and supply-line resolution.
10. Scouting, espionage, counterintelligence, and report aging.
11. Encounters, ambushes, sieges, and battles triggered by movement or orders.
12. Battle and siege resolution.
13. Casualties, prisoners, wounded recovery, desertion, and attrition.
14. Diplomacy, treaties, opinion changes, and war-support updates.
15. Public order, noble loyalty, rebellion, corruption, and stability checks.
16. Event log, dice log, and audit log updates.
17. Turn summary generated for the player.
18. End-of-turn save/checkpoint.

This order prevents disputes such as whether income arrives before expenses, whether a unit can fight before recruitment completes, or whether a bridge destroyed this turn blocks movement this turn.

## 5. Order Validation

Every order must be validated before resolution. An order is valid only when all required assets, permissions, locations, costs, and timing exist in official state.

Validation questions:

- Does the acting asset exist?
- Is the asset alive, active, supplied, and available?
- Is the order physically possible this turn?
- Is the origin, destination, target, or province valid?
- Is there enough treasury, manpower, equipment, food, and specialist capacity?
- Does the order conflict with another active order?
- Does a commander, governor, agent, or ruler have authority to execute it?
- Is the route blocked by terrain, weather, enemy control, destroyed bridges, or siege conditions?

Invalid orders should be logged with a failure reason instead of silently ignored.

## 6. Deterministic Formulas

Predictable systems should use formulas rather than narrative judgment.

### Economy

Net Income = Taxes + Trade + Production + Tribute - Army Upkeep - Construction Costs - Administration - Corruption - Debt Interest

### Food

Food Change = Farms + Imports + Foraging - Civilian Consumption - Army Consumption - Spoilage - Exports - Raid Losses

### Construction

Monthly Progress = Base Labor x Worker Efficiency x Material Availability x Engineer Modifier x Weather Modifier x Security Modifier

### Recruitment

Training Progress = Base Training Capacity x Facility Modifier x Officer Modifier x Equipment Availability x Stability Modifier

### Morale

Morale Change = Pay Modifier + Food Modifier + Victory/Defeat Modifier + Fatigue Modifier + Commander Modifier + Weather Modifier + Religious/Political Modifier

### Movement

Operational Movement = Base Terrain Speed x Road Modifier x Weather Modifier x Supply Modifier x Commander Logistics Modifier

Forced march may increase movement, but it must also increase fatigue, attrition risk, and combat-readiness penalties.

## 7. Random Resolution

Uncertain actions require logged dice or random numbers. A d100 model is recommended because most campaign values are percentages.

Resolution procedure:

1. Identify the action and actor.
2. Calculate base chance.
3. Apply modifiers.
4. Clamp the final chance within allowed minimum and maximum values.
5. Roll d100.
6. Compare roll to final chance.
7. Apply success, partial success, failure, or critical result.
8. Log the formula, modifiers, roll, and outcome.

Randomness should be small for routine deterministic systems and larger for risky human events such as espionage, ambushes, disease, diplomacy, and commander injury.

## 8. Battle Resolution

Battles are generated from the campaign state. They are not decided by prose.

Battle procedure:

1. Confirm participating units, commanders, locations, supplies, fatigue, morale, and orders.
2. Determine terrain, weather, visibility, fortifications, and surprise.
3. Establish objectives and retreat routes.
4. Calculate combat power per unit.
5. Apply terrain, weather, morale, fatigue, equipment, experience, formation, and commander modifiers.
6. Resolve phases: skirmish, main engagement, flank actions, reserves, morale checks, retreat, and pursuit.
7. Calculate dead, wounded, missing, captured, desertion, equipment loss, and supply loss.
8. Roll commander injury, capture, or death where appropriate.
9. Apply post-battle morale, experience, public-order, diplomatic, and strategic effects.
10. Record a battle report and update all affected sheets.

Baseline combat formula:

Combat Power = Unit Strength x Training x Equipment x Morale Modifier x Fatigue Modifier x Terrain Modifier x Commander Modifier x Random Factor

The random factor should usually be narrow, such as 0.95 to 1.05, so planning matters more than luck.

## 9. Logistics and Supply

Supply is a hard constraint. An army cannot campaign indefinitely just because it exists.

Each army should track food, water, ammunition where relevant, animal feed, supply wagons, road access, supply route, route security, and days or turns of endurance. Supply shortages should reduce morale and combat readiness before they destroy the army outright.

Suggested shortage ladder:

1. Fully supplied: no penalty.
2. Strained: slower movement and minor morale pressure.
3. Short: fatigue rises, training/recovery slows, morale drops.
4. Critical: attrition, desertion, disease, and combat penalties.
5. Starving: severe attrition, collapse risk, possible surrender or dispersal.

## 10. Recruitment and Manpower

Recruitment takes time and consumes population, manpower, money, equipment, food, officers, and training capacity. Units are not ready until they reach their required training threshold and receive required equipment.

Recommended readiness states:

| State | Meaning |
| --- | --- |
| Mustered | People have been gathered but are not trained |
| Training | Unit is forming and consumes resources |
| Green | Can fight poorly with morale and tactics penalties |
| Trained | Standard combat readiness |
| Veteran | Requires battle experience or special training |
| Elite | Requires rare facilities, officers, equipment, and time |

## 11. Construction and Infrastructure

Construction consumes money, materials, labor, engineering capacity, and time. Projects can be delayed or damaged by weather, raids, shortages, corruption, unrest, and siege conditions.

A project is complete only when official progress reaches 100% and all required final costs or checks are satisfied. Completed infrastructure should add maintenance costs where appropriate.

## 12. Diplomacy and Internal Politics

Diplomacy should track more than opinion. Relationship state may include trust, fear, threat perception, trade dependency, claims, treaties, war support, marriage ties, military access, and willingness to negotiate.

Internal politics should distinguish public support, noble loyalty, stability, corruption, legitimacy, war exhaustion, religious tension, and cultural tension. A kingdom can be militarily strong while politically fragile.

## 13. Event and Audit Logs

Every important state change should be auditable. Logs should preserve the campaign history and make disputes resolvable.

Minimum logs:

- Orders log.
- Dice/resolution log.
- Event log.
- Battle log.
- Casualty log.
- Intelligence log.
- Construction log.
- Diplomacy log.
- Save/checkpoint log.

Logs should include turn number, actor, target, previous value where useful, new value, reason, and source system.

## 14. Turn Summary Format

Each turn summary should be concise but complete:

1. Executive summary.
2. Treasury and economy.
3. Food, resources, and logistics.
4. Military movement and readiness.
5. Battles, sieges, and casualties.
6. Recruitment and construction.
7. Diplomacy.
8. Intelligence reports.
9. Provinces and public order.
10. Random events.
11. Invalid or partially completed orders.
12. Required player decisions for next turn.

The turn summary is not the source of truth; it is the readable report generated from the source of truth.

## 15. Anti-Retcon Rules

1. Past turns cannot be edited except to correct documented data-entry errors.
2. Corrections must be logged with the original value, corrected value, reason, and approver.
3. A player cannot retroactively issue an order after seeing a result.
4. Hidden information revealed later does not change what the player legally knew earlier.
5. Backups/checkpoints should be retained so the campaign can be audited or restored.

## 16. Implementation Status

The current codebase already supports a modular campaign foundation: separate domain packages, JSON configuration, SQLite persistence, workbook export generators, an application entry point, and early turn advancement for economy/logistics. The modularization work is substantially complete through the documented verification and documentation phase.

The remaining modularization gap is not basic package structure. The remaining gap is deeper simulation completeness: persisting advanced turn state back to SQLite, implementing richer order validation, combat resolution, fog-of-war views, dice logs, and full turn-summary generation.
