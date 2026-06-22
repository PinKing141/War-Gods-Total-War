# Observer Simulation Rules Framework

This document redefines the project as a spreadsheet-first and dashboard-assisted observer simulation. The world runs by itself. The user does not issue faction orders, command armies, or adjudicate outcomes by hand. The engine advances a live in-world calendar, state actors make decisions, deterministic systems update the economy and logistics, and logged stochastic systems introduce uncertainty where appropriate.

The core principle is simple: the runtime state is the world, and every visible historical outcome must be explainable from recorded state transitions.

## 1. Source of Truth

1. The official simulation state is the combination of the SQLite runtime database, generated workbook exports, desktop dashboard views, checkpoints, and machine-readable logs.
2. The SQLite runtime database is authoritative for active world state.
3. Workbook exports and desktop dashboard panels are observer views generated from the authoritative runtime state.
4. If an actor, claim, army, resource stockpile, treaty, rebellion, event, or casualty is not recorded in official state, it does not exist.
5. Permanent changes must be produced by deterministic formulas, validated autonomous decisions, or logged random resolution.
6. Narrative text, summaries, and observer commentary may explain outcomes, but they must not create outcomes.

## 2. Simulation Identity

The default product direction is a pure observer simulation.

1. No human faction receives direct command authority.
2. All polities are simulated actors with goals, pressures, capabilities, and memory.
3. The user may pause, resume, inspect, filter, export, save, load, and change simulation speed.
4. The user may not directly move armies, spend treasury, recruit units, sign treaties, or trigger battles during a live run.
5. Scenario configuration, seed changes, and world-parameter changes are allowed before a run begins or through explicit curator tools that are themselves logged.

## 3. Time Model

The simulation uses a live in-world calendar displayed as `DD/MM/YYYY`.

1. World time is simulated time, not wall-clock time.
2. The engine advances the calendar automatically while unpaused.
3. The UI must support at minimum `Pause`, `1x`, `2x`, `5x`, and `Fast` simulation speeds.
4. The current canonical time object should track day, month, and year rather than only turn counters.
5. Turn numbers may remain as internal aggregation markers, but the calendar date is the primary observer-facing time reference.

Recommended baseline:

| Area | Default scale |
| --- | --- |
| Primary observer clock | Day / Month / Year |
| Daily pulse | Local drift, movement progress, report aging, minor incidents |
| Weekly pulse | Route checks, short-term markets, AI threat review |
| Monthly pulse | Taxes, upkeep, production, strategic review |
| Seasonal pulse | Harvests, weather regime, disease pressure |
| Yearly pulse | Demographic change, institutional drift, succession risk |

## 4. Observer Visibility

The simulation has no player fog-of-war requirement by default, but it still needs layered visibility for clarity and future extensibility.

### Master State

The master state may include hidden probabilities, AI goals, internal decision weights, route efficiencies, threat maps, and raw stochastic inputs.

### Observer State

The observer state should expose:

1. Current date and speed.
2. Realm summaries.
3. Province summaries.
4. Resource and logistics pressures.
5. Diplomatic states.
6. Wars, battles, rebellions, collapses, and major events.
7. Historical logs and cause chains.

### Debug / Analysis State

For development and balancing, debug views may expose:

1. AI goals and decision scores.
2. Event trigger reasons.
3. Raw economic calculations.
4. Threat evaluations.
5. Hidden random rolls.

Debug data should be clearly separated from observer-facing history so the public chronology remains readable.

## 5. Simulation Pulse Order

Each simulated day should resolve in this order unless a scenario-specific rule overrides it:

1. Start-of-day snapshot markers and time advance.
2. Weather and seasonal effect checks.
3. Movement progress and route-state updates.
4. Local supply consumption and shortage progression.
5. Daily morale, loyalty, unrest, recovery, and attrition drift.
6. Intelligence aging and confirmation checks.
7. Incident trigger checks.
8. Event and audit log append.

Each simulated week should additionally resolve:

1. Market and route recalculations.
2. AI short-horizon reassessment.
3. Risk-map refresh for borders, shortages, and instability.

Each simulated month should additionally resolve in this order:

1. Production, spoilage, and trade-price updates.
2. Income collection.
3. Mandatory expenses, upkeep, debt, and corruption losses.
4. Recruitment progress, construction progress, and repair progress.
5. Autonomous faction strategic decisions.
6. Diplomatic changes, threat responses, war declarations, treaty changes, and internal political shifts.
7. Battles, sieges, rebellions, and strategic consequences triggered by the month’s state transitions.
8. Monthly summary generation.
9. Checkpoint save eligibility.

Each simulated year should additionally resolve:

1. Population growth or decline.
2. Succession, aging, or leadership change checks.
3. Cultural, religious, and institutional drift.
4. Long-horizon AI goal reevaluation.

## 6. Autonomous Decision Rules

Every major polity must act through a validated decision layer rather than arbitrary script text.

Each actor should evaluate at minimum:

1. Strategic goals.
2. Treasury and food constraints.
3. Military readiness.
4. Internal stability.
5. Threat perception.
6. Opportunity perception.
7. Existing diplomatic commitments.
8. Historical memory.

Decision validation questions:

1. Does the actor exist and remain viable?
2. Does the actor have the treasury, manpower, supply, or political capital required?
3. Is the target valid and reachable?
4. Does the action contradict locked state, treaty state, or simultaneous commitments?
5. Is the action physically or politically possible under current conditions?

Invalid autonomous decisions should be logged as rejected intent rather than silently discarded.

## 7. Deterministic Systems

Predictable systems should use formulas rather than narrative judgment.

### Economy

Net Income = Taxes + Trade + Production + Tribute - Upkeep - Construction - Administration - Corruption - Interest

### Food

Food Change = Farms + Imports + Foraging - Civilian Consumption - Military Consumption - Spoilage - Exports - Raid Losses

### Stability

Stability Change = Prosperity Modifier + Food Modifier + Security Modifier + Legitimacy Modifier + War Pressure Modifier + Corruption Modifier

### Province Unrest

Unrest Change = Tax Pressure + Shortage Pressure + Occupation Pressure + Cultural/Religious Tension - Garrison Pressure - Prosperity Relief - Reform Relief

### Construction

Progress = Base Labor x Worker Efficiency x Material Availability x Engineering Modifier x Weather Modifier x Security Modifier

### Movement

Operational Progress = Base Terrain Speed x Road Modifier x Weather Modifier x Supply Modifier x Logistics Modifier

## 8. Random Resolution

Uncertain actions require logged random resolution. A d100 or normalized 0.0-1.0 model is recommended because most state pressures map cleanly to probabilities.

Resolution procedure:

1. Identify the triggering action, actor, and target.
2. Calculate base chance.
3. Apply deterministic modifiers.
4. Clamp the final chance within allowed minimum and maximum values.
5. Roll.
6. Compare roll to threshold.
7. Apply result.
8. Log formula, modifiers, roll, and outcome.

Randomness should be narrow for routine systemic drift and wider for espionage, disease, commander survival, rebellion timing, and diplomatic brinkmanship.

## 9. Battles and Conflict

Conflict remains generated from state rather than prose, but it no longer waits for player orders.

Battles, sieges, raids, and rebellions should emerge from:

1. AI strategic decisions.
2. Movement overlap.
3. Border tension.
4. Supply collapse.
5. Provincial unrest.
6. Opportunistic aggression.

Baseline battle procedure:

1. Confirm participants, location, weather, morale, fatigue, supply, and retreat routes.
2. Establish terrain and fortification context.
3. Calculate combat power per side.
4. Apply morale, fatigue, terrain, equipment, experience, and commander modifiers.
5. Resolve engagement phases.
6. Apply casualties, wounded, prisoners, desertion, and supply loss.
7. Apply post-battle diplomatic, internal, and strategic effects.
8. Record the conflict as a historical event with cause data.

## 10. Logistics and Endurance

Supply is a hard constraint. Long-lived observer simulations become unconvincing if armies or provinces ignore material exhaustion.

Each army or major force should eventually track:

1. Food endurance.
2. Route access.
3. Route security.
4. Local forage quality.
5. Seasonal penalties.
6. Attrition state.

Suggested shortage ladder:

1. Fully Supplied: no penalty.
2. Strained: reduced movement, mild morale pressure.
3. Short: rising fatigue, reduced recovery, falling morale.
4. Critical: attrition, desertion, disease, reduced combat power.
5. Starving: collapse risk, surrender, or dispersal.

## 11. Construction, Recruitment, and State Capacity

Infrastructure and military capacity must grow through time and cost.

1. Recruitment consumes population, money, food, equipment, officer capacity, and training capacity.
2. Construction consumes money, materials, labor, security, and engineering capacity.
3. Large polities should face administrative drag and slower coherent execution.
4. Administrative overreach should appear as corruption, delays, unrest, and brittle logistics.

## 12. Diplomacy and Internal Politics

The observer simulation should treat politics as a first-class engine, not a flavor layer.

Diplomatic state may include:

1. Opinion.
2. Trust.
3. Fear.
4. Threat perception.
5. Claims.
6. Trade dependence.
7. Treaty commitments.
8. War support.

Internal political state may include:

1. Stability.
2. Legitimacy.
3. Noble loyalty.
4. Public support.
5. Cultural tension.
6. Religious tension.
7. Corruption.
8. War exhaustion.

## 13. Historical Memory and Causality

The world must remember its own history.

Every major actor should eventually preserve memory of:

1. Past wars.
2. Betrayals.
3. Alliances.
4. Famines.
5. Rebellions.
6. Claims and lost territory.
7. Dynastic or leadership crises.

Every major event should record:

1. What happened.
2. When it happened.
3. Which entities were affected.
4. Which systems contributed.
5. What changed because of it.

If an observer cannot answer why a kingdom rose, declined, or fractured, the simulation is not yet sufficiently legible.

## 14. Logs, Replays, and Auditability

Every important state change should be auditable and replayable.

Minimum logs:

1. Event log.
2. Random-resolution log.
3. Diplomacy log.
4. Conflict log.
5. Casualty log.
6. Construction log.
7. Recruitment log.
8. Economic summary log.
9. Checkpoint/save log.
10. Observer-summary log.

Logs should include date, actor, target, previous value where useful, new value, cause, and source system.

## 15. Observer Summary Format

Each summary should explain the world rather than request player action.

Recommended summary sections:

1. Executive summary.
2. Current date and speed.
3. Major power shifts.
4. Treasury, food, and logistics pressures.
5. Wars, battles, and rebellions.
6. Recruitment and construction.
7. Diplomacy and treaty changes.
8. Province instability hotspots.
9. Notable events and cause chains.
10. Emerging risks for the next interval.

The summary is not the source of truth. It is the observer-readable interpretation of the source of truth.

## 16. Anti-Retcon and Save Integrity Rules

1. Past simulated dates cannot be edited except through documented data correction or explicit dev tools.
2. Corrections must log original value, corrected value, reason, and operator.
3. Live runs may not silently rewrite earlier history.
4. Replays and exports must reflect the same official underlying state.
5. Checkpoints should be retained so long runs can be audited and resumed.

## 17. Implementation Roadmap Constraints

The roadmap that follows elsewhere in the repo should obey these rules:

1. Replace the current month-only turn mental model with a live simulated calendar.
2. Introduce daily, weekly, monthly, seasonal, and yearly pulses incrementally.
3. Keep exports and dashboard views as observer outputs, not primary mutation surfaces.
4. Build autonomous faction behavior before adding curator powers.
5. Prioritize causality, logs, and explainability before content breadth.
6. Add battles and rich politics only after the calendar, pulses, economy, and event logging are stable.

## 18. Current Implementation Status

The codebase already supports the modular foundation required for this pivot: separate domain packages, JSON configuration, SQLite persistence, workbook export, a PySide6 dashboard shell, an application entry point, and deterministic monthly advancement for the kingdom economy and resources.

The major remaining gap is not architecture. The major remaining gap is behavioral depth: a real calendar model, autonomous faction loops, pulse-based progression, historical memory, richer logs, and observer-grade summaries that explain world motion over time.
