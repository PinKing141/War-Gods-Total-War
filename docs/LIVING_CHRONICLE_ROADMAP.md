# Living Chronicle Simulator Roadmap

**Document Version**: 1.0  
**Last Updated**: 2026-06-22  
**Strategic Direction**: Autonomous Historical Chronicle Simulator  
**Current Codebase Status**: Modular campaign foundation, calendar engine, and pulse scheduler complete

---

## 1. Product Vision

**Living Chronicle Simulator** is a no-player-agency medieval history simulator. The user does not command a faction, win battles, or optimize a build. The world runs by itself. Kingdoms tax, starve, march, negotiate, betray, revolt, collapse, recover, and remember. The primary experience is watching the hidden simulation state become public chronicles, reports, annals, ledgers, and disputed histories.

The game is not a conventional real-time strategy game, role-playing game, tactical combat game, or quest-driven adventure. It is an autonomous history engine.

### One-sentence pitch

> A fantasy history generator where autonomous kingdoms, rulers, armies, nobles, spies, logistics, famine, war, and politics create history without player control.

### What the project is

- A persistent simulation of medieval campaign state.
- A chronicle generator that reports what happened after the simulation resolves it.
- A no-player-agency observer experience.
- A systems-first project where hidden truth, public records, rumors, and later histories can disagree.
- A data-driven engine where state, pressure, decisions, constraints, consequences, logs, and chronicles form the main loop.

### What the project is not

- Not a player-controlled strategy game.
- Not a tactical battle game where the user commands units.
- Not a character RPG.
- Not a quest game.
- Not an online/multiplayer game unless added much later as a separate observer/sharing layer.
- Not a graphics-first AAA production. The project should use AAA-style planning discipline, but only the sections that apply to a simulation/chronicle engine.

---

## 2. Design Pillars

1. **The world acts without the player.**  
   Factions, rulers, armies, provinces, nobles, spies, markets, and crises generate their own pressures and actions.

2. **State is truth; chronicle is camera.**  
   SQLite/runtime state and logs are the truth. Workbooks, summaries, reports, and historical accounts are generated views of that truth.

3. **Every major outcome must have a cause.**  
   A revolt, famine, betrayal, battle loss, or alliance shift should trace back to pressures, formulas, decisions, random checks, and logged consequences.

4. **Logistics limits ambition.**  
   Armies and kingdoms should fail because of food, roads, weather, debt, morale, manpower, corruption, and time, not only because an enemy army is larger.

5. **History should be readable, but not always reliable.**  
   The master state may know the truth, but public reports, faction knowledge, rumors, propaganda, and later historians can present partial or biased versions.

6. **Build the smallest complete world first.**  
   Every major layer should exist in simple form before any one layer becomes deep: decision-making, logistics, war, politics, logging, and chronicle output.

---

## 3. Current Codebase Baseline

The repository already has a strong modular foundation:

- Domain-driven package structure with `kingdom`, `geography`, `military`, `diplomacy`, `logistics`, and `events` domains.
- JSON campaign definitions validated by Pydantic schemas.
- SQLite runtime persistence and repository hydration.
- Workbook export with dashboard, provinces, resources, army, commanders, diplomacy, logistics, and event sheets.
- A thin application layer that loads config, seeds SQLite, hydrates repositories, and exports the campaign workbook.
- Calendar-backed daily advancement with deterministic daily, weekly, monthly, seasonal, and yearly pulse boundaries.
- Monthly kingdom economy, resource advancement, persisted turn state, audits, and summaries are executed through registered pulse hooks during day-by-day progression.
- Tests covering domain behavior, config/persistence, export parity, application startup/export, checkpointing, persisted turn advancement, and pulse scheduling.

### Existing systems to preserve

| Existing area | Keep because |
| --- | --- |
| JSON config files | They are useful seed data and designer-editable definitions. |
| SQLite runtime state | It is the correct source of mutable truth for a persistent sim. |
| Repository pattern | It isolates domain persistence and supports future state expansion. |
| Workbook export | It is already a useful chronicle/reporting surface. |
| Event domain | It should grow into audit, dice, battle, intelligence, diplomacy, and chronicle logs. |
| Modular domains | They are the right boundaries for autonomous simulation layers. |

### Existing gaps to plan around

- The world has state but not autonomous will.
- Autonomous decisions still need to move onto the pulse scheduler.
- Event scheduling exists as pulse boundaries, but no action queue or delayed event queue exists yet.
- There is no full audit/dice log schema.
- Battle resolution is documented but not implemented.
- Movement is mostly a stored location, not a route/time/supply process.
- Logistics production exists, but supply consequences are not yet systemic.
- Diplomacy stores relations, but factions do not yet make decisions.
- Internal politics is represented lightly through morale/loyalty/stability but not as a collapse system.
- Workbook reports exist, but chronicle generation is not yet driven by event/audit logs.

---

## 4. Core Experience Loop

Because there is no player agency, the loop is not “player acts, world responds.” The loop is “world acts, observer reads.”

### Minute-to-minute user experience

- Start/pause/resume simulation.
- Advance by day, month, year, or until major event.
- Read generated chronicles and reports.
- Inspect factions, provinces, armies, commanders, resources, and logs.
- Compare master-state truth with public/faction/historian accounts when available.

### Simulation loop

```text
State
→ pressure evaluation
→ autonomous intent generation
→ validation/constraint checks
→ scheduled action resolution
→ consequences
→ audit/dice/event logs
→ chronicle/report generation
→ checkpoint
```

### Strategic time model

Use a hybrid tick model:

```text
1 day tick
30 day ticks = 1 campaign month
12 campaign months = 1 campaign year
```

Monthly resolution remains the strategic anchor. Daily ticks are for movement progress, weather, scouting, supply checks, encounters, event triggers, and scheduled actions.

### Observer speed controls

- Pause.
- Step one day.
- Step one month.
- Step one year.
- Run until next major event.
- Run until next battle.
- Run until a selected faction collapses.
- Run until year end.
- Run until war ends.

---

## 5. Unified Simulation Layers

The project should combine five layers into one living engine.

| Layer | Purpose | Current support | Roadmap focus |
| --- | --- | --- | --- |
| Chronicle output | Make history readable | Workbook sheets and event sheet | Monthly chronicles, yearly annals, battle reports, faction histories |
| Faction/ruler AI | Give the world will | Factions, relations, commanders, kingdoms | Personalities, pressures, intents, memories |
| Logistics survival | Constrain actions | Resources, projects, supply routes | Food, depots, route security, shortage penalties, overextension |
| War sandbox | Resolve violence | Units, commanders, morale, fatigue, garrisons | Movement, contact, battle, siege, casualties, retreat, occupation |
| Political collapse | Make realms fragile | Morale, loyalty, faction stability | Legitimacy, unrest, noble factions, coups, civil wars, rebellions |

---

## 6. Applicable AAA-Style Planning Sections

This roadmap adopts AAA discipline where it helps, but removes sections that do not fit this project.

### Applies strongly

- Vision and design pillars.
- Core loop.
- State architecture.
- Data architecture.
- AI architecture.
- Tools/debugging architecture.
- Save/load/versioning.
- Performance budgets for long simulation runs.
- Automated QA and soak tests.
- Documentation structure.
- Build/version-control hygiene.
- Risk/cut plan.
- Production phases.

### Applies lightly or later

- Visual art pipeline: only needed for future maps/UI presentation.
- Audio/music: optional polish, not core engine work.
- Localization: later if the chronicle text becomes product-facing.
- Platform certification: later if packaged for stores.
- Accessibility: important for UI/reporting later, but not a blocker for engine prototypes.

### Does not apply now

- Combat animation pipeline.
- Character animation and VFX pipeline.
- Cutscene tools.
- Level streaming.
- Controller combat feel.
- Multiplayer/network architecture.
- Player quest systems.
- Player inventory/progression systems.
- Moment-to-moment camera/combat design.

---

## 7. Target Platforms and Delivery

### Near-term target

- Python package and CLI/workbook-export workflow.
- SQLite persistence.
- Excel workbook and Markdown/text chronicle outputs.
- Automated pytest suite.

### Medium-term target

- Local desktop observer tool or lightweight web dashboard.
- Timeline/log viewer.
- Faction/province/army inspectors.
- Simulation run controls.

### Long-term optional targets

- Standalone desktop app.
- Web viewer for chronicles and maps.
- Moddable scenario packs.
- Steam-style packaged release if the observer UI becomes polished enough.

---

## 8. Technical Architecture Roadmap

### 8.1 State architecture

The rule remains:

> Runtime state is the source of truth. Views only display or interpret it.

Current state lives across SQLite tables and hydrated repositories. The next architecture step is to explicitly separate:

| State type | Purpose |
| --- | --- |
| Master state | Full hidden truth of the world. |
| Faction knowledge | What each faction believes or knows. |
| Public record | What common reports say happened. |
| Chronicle account | Generated readable history, possibly biased. |
| Audit log | Exact machine-readable state changes. |
| Dice log | Random checks with formulas, modifiers, rolls, and outcomes. |
| Checkpoint | Restorable simulation snapshot. |

### 8.2 System architecture

Systems should communicate through events and typed records, not direct uncontrolled mutation.

Example:

```text
Battle resolver emits:
- BattleResolved
- UnitCasualtiesApplied
- CommanderKilled
- ProvinceLooted
- MoraleChanged

Economy, politics, diplomacy, and chronicle systems react to those events.
```

Required system boundaries:

| System | Role |
| --- | --- |
| Time/scheduler | Runs daily/monthly/yearly events in deterministic order. |
| Pressure evaluator | Computes faction and province pressures. |
| Intent generator | Converts pressures/personality into desired actions. |
| Validation/constraint engine | Checks resources, authority, location, timing, and physical possibility. |
| Logistics resolver | Applies food, supply, route, weather, and shortage effects. |
| Movement resolver | Moves armies over routes and triggers contacts. |
| Battle/siege resolver | Resolves combat and consequences. |
| Diplomacy resolver | Updates relations, treaties, fear, trust, and coalitions. |
| Internal politics resolver | Handles unrest, legitimacy, coups, rebellions, and collapse. |
| Event/audit logger | Records all important changes. |
| Chronicle generator | Turns logs into readable reports. |
| Export/view layer | Produces workbook, Markdown, dashboards, or UI views. |

### 8.3 Data architecture

Keep JSON as seed/config data and SQLite as mutable runtime state.

Needed future data assets:

- Faction personality templates.
- Ruler and noble traits.
- Commander trait/effect tables.
- Pressure formula definitions.
- Intent/action definitions.
- Event trigger tables.
- Random/dice table definitions.
- Weather and seasonal tables.
- Terrain and route tables.
- Battle modifier tables.
- Chronicle phrase/report templates.
- Historian bias/source templates.

Needed future SQLite tables:

- `simulation_clock` or expanded checkpoint metadata.
- `scheduled_event` for day-level event queue.
- `audit_log` for state changes.
- `dice_log` for random resolution.
- `intent` for generated actor intentions.
- `action_resolution` for validated/failed/resolved actions.
- `army` or `force` for multi-unit operational groups.
- `movement_order` or `movement_plan` for route progress.
- `battle` and `battle_participant`.
- `casualty_log`.
- `intelligence_report`.
- `chronicle_entry`.
- `faction_memory`.
- `political_pressure` or expanded faction/province stability tables.

---

## 9. Main Feature Roadmap

### 9.1 Time and scheduler

**Goal**: Move from one monthly jump to a deterministic daily/monthly event queue.

Minimum viable version:

- Store current year/month/day.
- Support daily ticks.
- Support end-of-month resolution.
- Support scheduled events with due date, actor, target, type, payload, and status.
- Support deterministic ordering for same-day events.
- Support running until a condition: next event, next month, next year, battle, collapse.

Acceptance criteria:

- A 12-month simulation can run without manual intervention.
- Same seed and same initial state produce the same event order.
- Checkpoints restore the same next scheduled events.

### 9.2 Audit and dice logs

**Goal**: Make every important outcome explainable.

Minimum viable version:

- `audit_log` records turn/month/day, actor, target, system, action, previous value, new value, reason, source event.
- `dice_log` records action, base chance, modifiers, final chance, roll, outcome, random seed/context.
- Event log references audit/dice entries.
- Chronicle generator reads event/audit logs instead of inventing facts.

Acceptance criteria:

- A treasury change, food shortage, battle casualty, failed action, and diplomacy shift can each be traced to a log entry.
- Tests can assert that a state mutation creates a corresponding audit entry.

### 9.3 Faction AI and intent generation

**Goal**: Give the world autonomous will.

Minimum viable version:

- Factions/rulers have 3-5 traits such as aggression, caution, greed, paranoia, stability focus.
- Each month, pressure scores are calculated: hunger, debt, threat, opportunity, unrest, war exhaustion, ambition.
- Pressure plus personality creates intents such as raid, fortify, raise taxes, seek alliance, suppress unrest, recruit, build supply depot.
- Intents can fail validation and be logged.

Acceptance criteria:

- Different rulers facing the same pressures choose different likely intents.
- A starving aggressive faction prefers raids; a cautious wealthy faction prefers fortification or diplomacy.
- Generated intents are persisted and auditable.

### 9.4 Logistics survival layer

**Goal**: Make supply a hard constraint.

Minimum viable version:

- Armies consume food/supplies each day or month.
- Provinces and supply routes determine available supply.
- Shortage ladder applies penalties: strained, short, critical, starving.
- Shortage impacts movement speed, morale, fatigue, attrition, desertion, and combat readiness.
- Routes can be active, blocked, raided, or insecure.

Acceptance criteria:

- An overextended army loses effectiveness before it is destroyed.
- A large army can fail due to supply even without a battle.
- Supply failures create logs and chronicle entries.

### 9.5 Movement and contact

**Goal**: Make armies travel over time instead of teleporting by location id.

Minimum viable version:

- Create operational army/force grouping over units.
- Movement has origin, destination, route, distance/progress, speed, supply endurance, fatigue, and status.
- Terrain, roads, weather, commander logistics, and supply modify speed.
- Contact detection can trigger scouting, encounter, ambush, siege, or battle events.

Acceptance criteria:

- Armies take multiple days to move between provinces.
- Movement can be delayed by weather/supply.
- Opposing armies in compatible locations can trigger encounters.

### 9.6 Battle and siege resolver

**Goal**: Resolve combat from state, not prose.

Minimum viable battle formula:

```text
Combat Power = soldiers
             × training/equipment modifier
             × morale modifier
             × fatigue modifier
             × terrain modifier
             × commander modifier
             × supply modifier
             × random factor
```

Minimum outputs:

- Winner/loser or inconclusive result.
- Casualties by unit.
- Morale shifts.
- Fatigue shifts.
- Retreat/pursuit outcome.
- Commander injury/capture/death checks.
- Province/public-order consequences.
- Battle log and chronicle-ready battle report.

Acceptance criteria:

- Battle results update units and commanders.
- Battle logs include formulas, modifiers, random rolls, and outcomes.
- Public chronicle can summarize the battle without inventing facts.

### 9.7 Recruitment and construction lifecycle

**Goal**: Make growth compete with survival.

Minimum viable version:

- Recruitment consumes silver, manpower, equipment, food, training capacity, and time.
- Units progress through states: mustered, training, green, trained, veteran, elite.
- Construction consumes silver, materials, labor, engineering capacity, and time.
- Projects can be delayed by shortage, weather, raids, corruption, unrest, or siege.
- Completed infrastructure adds benefits and possibly maintenance costs.

Acceptance criteria:

- A faction cannot recruit forever without manpower/equipment/food.
- Building a fort competes with feeding armies or paying soldiers.
- Recruitment/construction progress and delays are logged.

### 9.8 Diplomacy and memory

**Goal**: Make factions react to history.

Minimum viable version:

- Relations track opinion, trust, fear, threat perception, trade dependency, claims, treaties, war support, and memory.
- Major events create faction memories: betrayal, aid, raid, battle, marriage, famine relief, occupation.
- Diplomacy intents include alliance, peace, tribute, coalition, embargo, spy support, rebel support.

Acceptance criteria:

- A faction reacts differently to a recent betrayal than to an old neutral relation.
- Rising empires generate fear and coalitions.
- Diplomacy shifts are logged and included in summaries.

### 9.9 Internal politics and collapse

**Goal**: Let factions rot from within.

Minimum viable version:

- Track legitimacy, noble loyalty, public support, corruption, war exhaustion, tax burden, food security, religious/cultural tension, succession clarity.
- Crises include tax riot, peasant revolt, noble conspiracy, mutiny, civil war, succession crisis, coup, separatist uprising.
- Suppression, concessions, reform, bribery, purges, and abdication become possible autonomous intents.

Acceptance criteria:

- A militarily strong faction can collapse through internal pressure.
- Food shortage and war exhaustion can trigger rebellion.
- Collapse events have clear logged causes.

### 9.10 Chronicle and historian mode

**Goal**: Make simulation results enjoyable to read.

Minimum viable version:

- Monthly chronicle generated from event/audit logs.
- Yearly annal generated from monthly summaries.
- Battle report generated from battle logs.
- Faction situation report generated from state and logs.
- Collapse/famine/rebellion reports generated when major events occur.

Advanced version:

- Separate master truth, faction reports, public rumors, royal propaganda, rebel accounts, and later historian interpretation.
- Record confidence, source, age, and bias for each account.
- Allow contradictory accounts based on knowledge and incentives.

Acceptance criteria:

- The same hidden event can produce different public accounts.
- Chronicle entries cite underlying event IDs/log IDs.
- User can inspect why a chronicle entry was generated.

---

## 10. Tools and Debugging Roadmap

Tools are more important than visuals for this project.

### Required early tools

- Simulation runner CLI: run N days/months/years.
- Seeded deterministic run mode.
- Save/checkpoint inspector.
- Event/audit/dice log viewer.
- Faction pressure debug report.
- Intent generation debug report.
- State invariant checker.
- Export validator.

### Useful medium-term tools

- Scenario editor for factions/provinces/resources.
- Balance table editor.
- Chronicle template previewer.
- Battle resolver sandbox.
- Logistics route visualizer.
- Long-run simulation dashboard.
- Regression diff tool comparing two simulation runs.

### Later tools

- Map viewer.
- Timeline browser.
- Faction history browser.
- Mod/scenario packaging tools.

---

## 11. Testing and QA Roadmap

### Existing testing baseline

The current suite already covers:

- Domain model/service basics.
- Config loading.
- Database schema creation.
- JSON-to-SQLite seeding and repository hydration.
- Export parity with the legacy monolith.
- Application-level export flow.
- Turn advancement, checkpointing, persistence, and rehydration.

### Required next tests

| Test category | Examples |
| --- | --- |
| Scheduler tests | Same seed creates same event order; events resolve on due day. |
| Audit tests | Every mutation creates audit record. |
| Dice tests | Rolls are logged with modifiers and deterministic seed behavior. |
| Intent tests | Faction traits/pressures produce expected weighted choices. |
| Constraint tests | Invalid intents fail with reason instead of mutating state. |
| Logistics tests | Shortage ladder affects morale/fatigue/attrition. |
| Movement tests | Route progress, delay, arrival, and contact events. |
| Battle tests | Casualties, morale changes, commander risk, battle logs. |
| Politics tests | War exhaustion/famine can trigger unrest/collapse. |
| Chronicle tests | Generated text references real log/event data. |
| Soak tests | Run 10, 100, and 1,000 simulated years without impossible state. |

### Simulation invariants

Long-run tests should check:

- No negative population, soldiers, treasury, food, or resources unless explicitly allowed as debt.
- No unit exists without a faction/kingdom.
- No active army has impossible location or route.
- No battle references missing units/commanders/provinces.
- No chronicle entry references missing event/log IDs.
- No faction relation references deleted factions.
- No project completes above 100% or remains active after completion.
- Save/load round trips preserve scheduled events and deterministic future outcomes.

---

## 12. Performance Budget

This is not a graphics-heavy game, so the main performance risk is simulation cost over long timelines.

### Prototype targets

- Run 1 simulated year in under 5 seconds for the starter scenario.
- Run 100 simulated years overnight in CI/local soak mode.
- Keep SQLite writes batched where possible.
- Keep chronicle generation incremental, not full-history regenerated every tick.

### Medium scenario targets

- 10 factions.
- 50 provinces.
- 100 units/armies.
- 1,000+ yearly events.
- 100-year run completes without manual intervention.

### Scaling strategy

- Daily detailed simulation only for active scheduled events.
- Monthly abstract resolution for stable/off-screen systems.
- Batch audit/event writes per tick or phase.
- Use deterministic seeds per event/action for reproducibility.
- Archive old logs into summary tables if needed.

---

## 13. Save/Load and Versioning Plan

Save/load is core infrastructure, not polish.

### Requirements

- SQLite runtime database remains primary save file.
- Checkpoints include clock, scheduler queue, random seed state/context, and schema version.
- Save version table tracks migrations.
- Every schema expansion gets a migration or documented reset path.
- Corrupt or failed writes should not destroy the last good checkpoint.
- Long-run simulations should support rolling checkpoints.

### Checkpoint policy

- Start-of-month checkpoint.
- End-of-month checkpoint.
- Optional pre-major-event checkpoint.
- Manual checkpoint through CLI/tooling.
- Keep configurable number of historical checkpoints.

---

## 14. Documentation Roadmap

### Existing docs to keep

- `README.md`: quick start and project overview.
- `MODULARIZATION_ROADMAP.md`: historical modularization/technical refactor plan.
- `docs/RULES_FRAMEWORK.md`: enforceable campaign operating rules.
- `docs/ARCHITECTURE.md`: architecture overview.
- `docs/API.md`: public API reference.
- `docs/EXTENDING.md`: how to add systems.

### New docs to add over time

- `docs/LIVING_CHRONICLE_ROADMAP.md`: this product/simulation roadmap.
- `docs/SIMULATION_LOOP.md`: exact daily/monthly/yearly phase order.
- `docs/EVENT_SCHEMA.md`: audit, dice, scheduled event, chronicle schemas.
- `docs/FACTION_AI.md`: pressure/intent/personality rules.
- `docs/LOGISTICS.md`: supply, routes, shortage ladder.
- `docs/BATTLE_RESOLUTION.md`: formulas, modifiers, outputs.
- `docs/CHRONICLE_GENERATION.md`: report templates, bias, historian mode.
- `docs/SOAK_TESTING.md`: long-run test strategy.

---

## 15. Feature Priority Tiers

### Tier 1: Required for the Living Chronicle MVP

- Explicit daily/monthly simulation loop.
- Event scheduler.
- Audit log.
- Dice/random log.
- Faction pressure evaluation.
- Basic autonomous intent generation.
- Intent validation and failure reasons.
- Basic logistics shortage consequences.
- Basic movement over time.
- Basic battle resolver.
- Monthly chronicle generated from logs.
- Save/load/checkpoint compatibility.
- Long-run smoke/soak test.

### Tier 2: Important after MVP

- Ruler/noble/commander traits.
- Faction memory.
- Political collapse system.
- Siege system.
- Recruitment/training lifecycle.
- Construction delay/maintenance system.
- Diplomacy reactions and coalitions.
- Intelligence reports and fog of war.
- Yearly annals.
- Debug dashboards.

### Tier 3: Nice-to-have

- Rich historian disagreement mode.
- Map viewer.
- Timeline UI.
- Procedural faction names/dynasties.
- Chronicle prose style variants.
- Scenario editor.
- Modding support.
- Advanced weather/seasonal regional modeling.

### Tier 4: Explicitly out of scope for now

- Player faction control.
- Tactical battle control.
- Real-time 3D map.
- Multiplayer.
- Character inventory.
- Quest systems.
- Cutscenes.
- Combat animation/VFX pipelines.

---

## 16. Production Phases

### Phase 0 — Direction lock and roadmap alignment

**Goal**: Align the project around Living Chronicle Simulator instead of a player-controlled strategy game.

Tasks:

- Add this roadmap.
- Update README references.
- Decide naming: Living Chronicle Simulator vs current Warfare Simulation Campaign Engine branding.
- Reconcile `MODULARIZATION_ROADMAP.md` with this product roadmap.
- Mark player-order language as future `actor intent` language where applicable.

Exit criteria:

- Docs clearly state no-player-agency direction.
- Roadmap separates current foundation from future autonomous simulation.

### Phase 1 — Chronicle skeleton MVP

**Goal**: Build the smallest complete world loop.

Scope:

- 3 factions.
- 5 provinces.
- 3 resources: food, silver, manpower.
- 2 army stats: soldiers and morale.
- 3 ruler traits.
- 3 crisis types: famine, revolt, war.
- Monthly chronicle output.
- Yearly summary.

Systems:

- Explicit monthly phase pipeline.
- Audit/event log expansion.
- Basic pressure evaluator.
- Basic intent generation.
- Basic chronicle generation from logs.

Exit criteria:

- A 12-month unattended run produces plausible state changes and monthly chronicle entries.
- Every chronicle entry references underlying events/logs.

### Phase 2 — Scheduler and daily ticks

**Goal**: Make the world feel fluid without abandoning monthly strategic clarity.

Scope:

- Day-level clock.
- Scheduled events.
- Run controls.
- End-of-month resolution.
- Checkpoint scheduler state.

Exit criteria:

- Army arrival, spy mission, harvest event, and monthly report can occur on different days within the same month.

### Phase 3 — Faction AI v1

**Goal**: Make factions behave differently.

Scope:

- Personality traits.
- Pressure scoring.
- Weighted intent selection.
- Intent validation.
- Failure logging.

Exit criteria:

- Same state with different ruler personalities produces different intent distributions.
- Invalid intents are logged and do not mutate state.

### Phase 4 — Logistics and movement v1

**Goal**: Make physical constraints matter.

Scope:

- Army grouping.
- Route/progress movement.
- Supply endurance.
- Shortage ladder.
- Weather/road modifiers.
- Contact detection.

Exit criteria:

- An army can fail, turn back, suffer attrition, or arrive weakened due to supply/weather.

### Phase 5 — Battle and siege v1

**Goal**: Resolve violence from state.

Scope:

- Simple combat power formula.
- Casualties.
- Morale/fatigue shifts.
- Commander risk.
- Retreat/pursuit.
- Battle logs.
- Battle chronicle entries.

Exit criteria:

- Two armies can meet, fight, update state, and produce an auditable report.

### Phase 6 — Internal politics and collapse v1

**Goal**: Make factions vulnerable from within.

Scope:

- Legitimacy/public support/corruption/war exhaustion/tax burden.
- Revolt and coup checks.
- Noble loyalty consequences.
- Civil war/collapse events.

Exit criteria:

- A strong military faction can still collapse from famine, debt, legitimacy loss, or noble betrayal.

### Phase 7 — Historian mode v1

**Goal**: Make records interesting and unreliable.

Scope:

- Master truth vs public account.
- Faction knowledge reports.
- Rumor/confidence/age fields.
- Later historian summaries.
- Contradictory accounts for selected major events.

Exit criteria:

- One battle, famine, or revolt can produce multiple differing accounts tied to the same hidden truth.

### Phase 8 — Observer tool / dashboard

**Goal**: Make the project easier and more enjoyable to watch.

Scope:

- Timeline viewer.
- Event log browser.
- Faction/province/army inspectors.
- Simulation controls.
- Chronicle reader.
- Export buttons.

Exit criteria:

- User can run, pause, inspect, and read history without opening raw SQLite/workbook files.

### Phase 9 — Content expansion and balance

**Goal**: Increase scenario richness after the full loop works.

Scope:

- More factions.
- More provinces.
- More ruler/commander traits.
- More event types.
- More chronicle templates.
- More diplomacy/politics outcomes.
- Soak testing and balancing.

Exit criteria:

- 100-year simulations produce varied but plausible histories without impossible state.

### Phase 10 — Release hardening

**Goal**: Stabilize the tool/game for external users.

Scope:

- Packaging.
- Documentation polish.
- Save migration guarantees.
- Crash/bug reporting.
- Performance budget enforcement.
- Example scenarios.
- Tutorial/readme walkthrough.

Exit criteria:

- A user can install, run a scenario, inspect reports, and replay from checkpoints without developer help.

---

## 17. Risk and Cut Plan

| Risk | Impact | Mitigation | Cut if needed |
| --- | --- | --- | --- |
| Scope becomes too large | Project stalls | Build thin full loop first | Delay historian mode, advanced politics, UI |
| AI becomes opaque | Outcomes feel random | Log pressures, intents, and reasons | Keep intent rules simple and visible |
| Simulation becomes slow | Long runs unusable | Batch writes, deterministic seeds, abstract off-event systems | Reduce daily detail, run monthly abstraction |
| Chronicle invents facts | Project loses simulation integrity | Generate only from logs/state | Use plain reports before prose |
| Save/load breaks | Long histories become disposable | Version schema early, checkpoint often | Reset only in prototypes, not post-MVP |
| Inter-system bugs multiply | Debugging becomes impossible | Event-driven boundaries and audit logs | Limit direct cross-domain mutation |
| Export parity blocks new sim work | Roadmap stalls on legacy workbook shape | Keep legacy export as compatibility surface | Add separate chronicle output before changing workbook |
| Too much AAA process | Solo/indie velocity drops | Use only applicable AAA planning sections | Skip art/cutscene/animation pipelines |

---

## 18. Definition of Done for the Core Vision

The Living Chronicle Simulator direction is proven when the system can:

1. Run for at least 10 simulated years without player orders.
2. Produce autonomous faction decisions from pressure and personality.
3. Enforce logistics constraints on war and politics.
4. Resolve movement, battles, casualties, diplomacy, and internal crises.
5. Persist all state and checkpoints.
6. Log all major causes, rolls, and consequences.
7. Generate monthly and yearly chronicles from logs.
8. Let the user inspect why major events happened.
9. Produce at least one disputed history where public/faction/historian accounts differ from master truth.
10. Pass long-run invariant tests without impossible state.

---

## 19. Immediate Next Steps

1. Keep `MODULARIZATION_ROADMAP.md` as the technical history/refactor roadmap.
2. Use this document as the product/simulation roadmap.
3. Update README to point to both roadmaps.
4. Implement Phase 1 in thin slices:
   - explicit turn pipeline,
   - event/audit log schema,
   - basic pressure evaluator,
   - basic intent generator,
   - chronicle skeleton.
5. Add tests before expanding depth.
6. Avoid UI/art/polish until the autonomous loop is proven.

---

## 20. North Star

The strongest version of this project is not a war game with the player removed.

It is a living historical engine where:

- rulers make decisions,
- armies march,
- supply lines break,
- cities starve,
- nobles betray,
- peasants revolt,
- dynasties collapse,
- commanders become legends,
- records lie,
- historians argue,
- and the world keeps going whether anyone is watching or not.
