# Unified Master Roadmap — War-Gods / Living Chronicle Simulator

**Document Version**: 1.0
**Last Updated**: 2026-07-01
**Status**: Canonical. This document supersedes and merges the previously separate roadmaps.
**Supersedes**:
- `MODULARIZATION_ROADMAP.md` (technical foundation & phases) — now historical/technical reference
- `LIVING_CHRONICLE_ROADMAP.md` (product direction & phases) — now folded in below
- `CONTENT_ROADMAP.md` (content backlog) — now the final stage of this plan
**Governed by**: `../RULES_FRAMEWORK.md` (the binding observer-simulation contract)

---

## 0. Why this document exists

The project previously carried three roadmaps with **two different, contradicting
phase-numbering schemes**. The product roadmap marked systems such as Faction AI,
Battle, Collapse, and Historian mode as "✓ initial implementation", while the
technical roadmap — designated as the honest record of what the code actually
does — still listed the same autonomous-decision work as *unstarted* (its Phase 11),
with province pressure, conflict, and memory as untouched future work. On top of
that, none of the deterministic formulas in `RULES_FRAMEWORK.md §7` and none of the
material dependency chains this project is really about have been implemented.

For a project whose whole thesis is *"state is truth and every outcome must be
auditable,"* the roadmap state itself was neither single nor auditable. This
document fixes that: **one roadmap, one ordered build plan, one honest status, one
prime design law.**

---

## 1. The Prime Law — Conservation ("nothing from nothing")

> **Nothing exists in the world without the inputs that produce it, and every input
> is itself produced by something else, all the way down to people and land.**

This is the top-level design law from which every system derives. It is not flavor;
it is an enforceable invariant.

- You cannot have **troops** without **people + silver + food + equipment**.
- You cannot have **food** without **farmers + tools + farmland**.
- You cannot have **tools** without **artisans + iron + a workshop**.
- You cannot have **iron** without **miners + tools + a mine**.
- You cannot have **silver** without **taxable people + a functioning economy**.
- You cannot have a **new kingdom** without a **founder + followers + wealth +
  legitimacy + unclaimed land**.

Every capability in the game is expressed as a **dependency graph**. When an input is
missing, the dependent output is *reduced or blocked*, and the **limiting input is
named in the logs**. An observer must always be able to ask "why couldn't they
produce/build/recruit/found more?" and get a concrete answer ("short on tools",
"no free farmland", "insufficient legitimacy").

### Supporting laws (from `RULES_FRAMEWORK.md`, retained verbatim in spirit)

1. **The world acts without the player.** All polities are autonomous actors; the
   user observes, pauses, inspects, and exports — never commands.
2. **State is truth; chronicle is camera.** SQLite runtime state and logs are the
   world. Workbooks, summaries, dashboards, and histories are generated views.
3. **Every major outcome must have a cause.** Rises, collapses, wars, famines,
   betrayals, and foundings must trace back through pressures, formulas, validated
   decisions, logged random rolls, and recorded consequences.
4. **Conservation over convenience.** No system may "spawn" a resource, unit, or
   realm to make numbers work. If it appears, it was produced from inputs.
5. **History should be readable but not always reliable.** Master truth may differ
   from public reports, faction knowledge, rumor, and later historians.
6. **Build the smallest complete world first.** Every layer exists in simple form
   before any one layer becomes deep.

---

## 2. Product Vision

**A fantasy history generator where autonomous kingdoms, rulers, characters, armies,
nobles, spies, logistics, famine, war, diplomacy, and politics create history without
player control — and where nothing in that history appears without the material
prerequisites that produced it.**

Two headline experiences define the target:

- **A living material economy.** Kingdoms tax, farm, mine, craft, build, recruit,
  starve, and go bankrupt because of concrete inputs and shortages — not abstract
  stat drift.
- **Characters who make history.** Named characters accumulate followers, wealth,
  and legitimacy; ambitious ones **found new kingdoms** from unclaimed land, others
  rebel, negotiate, betray, inherit, and die. Realms themselves are produced,
  founded, and destroyed under the same conservation law as grain and iron.

### What the project is / is not

| Is | Is not |
| --- | --- |
| An autonomous observer simulation of medieval history | A player-controlled strategy game |
| A conservation-driven material economy | A game where resources/units spawn on command |
| A character- and dynasty-driven political world | A single-hero RPG or quest game |
| A chronicle generator that reports resolved truth | A prose engine that invents facts |
| Deterministic + logged-stochastic and fully auditable | A black-box random event generator |

---

## 3. Design Pillars (merged)

1. **Conservation first.** Every system is a dependency graph; shortages propagate;
   limiting inputs are always named.
2. **Autonomy before content.** Build faction/character decision loops and their
   material constraints before adding more factions, provinces, or event packs.
3. **Explainability is non-negotiable.** Audit, dice, and observer logs make every
   change traceable; chronicles cite underlying log/event ids.
4. **Logistics limits ambition.** Armies and realms fail from food, roads, weather,
   debt, manpower, corruption, and time — not only from a bigger enemy.
5. **State/view separation stays strict.** SQLite is truth; exports, dashboards, and
   chronicles are generated observers.
6. **Ship in pulses, not fantasies.** Daily/weekly/monthly/seasonal/yearly systems
   grow incrementally, each with tests and conservation invariants.

---

## 4. The Canonical Dependency Model

This is the heart of the unified design. Every producible thing is defined by what it
consumes. Numbers below are illustrative starting recipes to be tuned in the balance
stage; the *shape* of the dependencies is the binding part.

### 4.1 Root inputs (the only things not produced by a recipe)

- **People** — allocated to roles: farmer, miner, artisan, laborer, soldier, idle.
- **Land / capacity** — farmland, mines, workshops, and the provinces themselves.
- **Time** — recipes and projects resolve over pulses, not instantly.

Everything else is derived from these.

### 4.2 Production chains

```text
people (miner)  + tools + mine        → iron
people (artisan)+ iron  + workshop    → tools
people (artisan)+ iron  + tools + workshop → equipment
people (farmer) + tools + farmland    → food
people (laborer)                      → food   (foraging: low yield, still needs people)
people (laborer)+ food                → silver (taxation/administration)
```

Because tools are both an input (farming, mining) and an output (smithing), and
smithing needs iron, and iron needs tools — the economy must **bootstrap from
stockpiles and can collapse in a cascade**: lose iron → lose tools → lose food and
silver. That cascade is the intended realism.

### 4.3 Capability prerequisites (actions gated by conservation)

| Capability | Requires (consumed unless noted) | On shortage |
| --- | --- | --- |
| Raise troops | idle people + silver + food + equipment | Rejected; missing input named |
| Build/upgrade | silver + timber/stone + labor + engineering capacity + time | Progress stalls; delay logged |
| Feed an army | food + secure supply route each pulse | Shortage ladder (see §7) |
| Collect taxes | taxable population + stability + administrative capacity | Reduced yield; cause logged |
| Sustain a realm | positive net food & silver over time | Debt, unrest, collapse pressure |
| **Found a kingdom** | a **founder** + **followers** + **silver** + **legitimacy** + **unclaimed land** | Ambition logged as *blocked* with the missing prerequisite |
| Wage war | armies + supply endurance + treasury + political capital | Overextension, attrition, mutiny |

### 4.4 The founding chain (characters → kingdoms)

```text
character (ambition ≥ threshold)
  + followers  (become the new realm's population)
  + silver     (become its founding treasury)
  + legitimacy (recognized right to rule)
  + unclaimed province (the land it sits on)
        → new autonomous realm/faction
```

If any prerequisite is missing, **no kingdom appears** and the attempt is recorded as
a blocked ambition with the exact deficit. This is the Prime Law applied to polities
themselves.

---

## 5. Simulation Architecture & Source of Truth

(From `RULES_FRAMEWORK.md §1, §4, §8.1` — retained as binding.)

| State type | Purpose |
| --- | --- |
| Master state (SQLite) | Full hidden truth: stockpiles, labor, capacities, AI goals, rolls |
| Faction knowledge | What each realm believes/knows |
| Public record | What common reports claim happened |
| Chronicle account | Generated readable history, possibly biased |
| Audit log | Exact machine-readable state transitions |
| Dice log | Random checks: base chance, modifiers, roll, outcome, seed |
| Checkpoint | Restorable snapshot (clock, queues, seeds, schema version) |

Systems communicate through **events and typed records**, not uncontrolled cross-domain
mutation. Conservation makes this natural: every mutation is "consume inputs → produce
outputs → log both".

---

## 6. Time Model & Pulse Order

Live in-world calendar shown as `DD/MM/YYYY`. Speeds: `Pause`, `1x`, `2x`, `5x`, `Fast`.

```text
1 day tick · 30 days = 1 month · 12 months = 1 year
```

**Pulse order (per `RULES_FRAMEWORK.md §5`, extended for conservation):**

- **Daily**: time advance; weather/season checks; movement & route state; local supply
  consumption & shortage progression; morale/unrest/attrition drift; intelligence
  aging; incident checks; event/audit append.
- **Weekly**: market & route recalculation; AI short-horizon reassessment; risk maps.
- **Monthly** (strategic anchor, strict order):
  1. **Production resolution** — run all recipes against stockpiles/labor/capacity
     (the conservation core).
  2. Spoilage & trade-price updates.
  3. Income collection (silver produced by taxation chain).
  4. Mandatory expenses, upkeep, debt, corruption.
  5. Recruitment / construction / repair progress (prerequisite-gated).
  6. Autonomous faction & character strategic decisions (validated; rejected intents
     logged).
  7. Diplomacy, threat response, war/treaty changes, internal political shifts.
  8. Battles, sieges, rebellions, foundings triggered by the month's state.
  9. Monthly summary generation.
  10. Checkpoint eligibility.
- **Seasonal**: harvest regimes, weather regime shifts, disease pressure.
- **Yearly**: demographics, succession/aging/death, cultural & institutional drift,
  long-horizon AI goal re-evaluation.

---

## 7. Deterministic Formulas, Shortage Ladder & Random Resolution

(From `RULES_FRAMEWORK.md §7–§10` — these replace the current `100 − stat` placeholders.)

**Deterministic formulas** (illustrative; tuned in balance stage):

```text
Net Income   = Taxes + Trade + Production + Tribute − Upkeep − Construction
               − Administration − Corruption − Interest
Food Change  = Farms + Imports + Foraging − Civilian Consumption
               − Military Consumption − Spoilage − Exports − Raid Losses
Stability Δ  = Prosperity + Food + Security + Legitimacy + WarPressure + Corruption
Unrest Δ     = TaxPressure + ShortagePressure + OccupationPressure + Cultural/Religious
               − Garrison − Prosperity − Reform
Construction = BaseLabor × WorkerEfficiency × MaterialAvailability × Engineering
               × Weather × Security
Movement     = TerrainSpeed × Road × Weather × Supply × Logistics
```

**Shortage ladder** (armies and provinces): Fully Supplied → Strained → Short →
Critical → Starving, with rising penalties to movement, morale, fatigue, attrition,
desertion, and combat power.

**Random resolution** (logged): identify actor/action/target → base chance → apply
modifiers → clamp → roll (d100 or 0.0–1.0) → compare → apply → **log formula,
modifiers, roll, and outcome** to the dice log. Narrow randomness for routine drift;
wider for espionage, disease, commander survival, rebellion timing, and diplomatic
brinkmanship.

---

## 8. Honest Current Status

**Solid foundation (real and preserved):**

- Domain-driven package structure; JSON seed config; SQLite runtime state; repository
  pattern; workbook export; PySide6 dashboard shell.
- Canonical `SimDate` calendar; pause/speed controls; checkpoint round-trip.
- Deterministic pulse scheduler (daily/weekly/monthly/seasonal/yearly) with
  duplicate-run prevention and a persisted scheduled-event queue.
- Observer-log/causality backbone: structured event metadata (date, actor, target,
  source system, cause chain, effect summary), audit logs, observer-log streams, and
  monthly/yearly summaries — all surviving restart.
- Deterministic monthly **flat** economy (treasury += income − expenses) and
  **flat** resource production (stored += production − consumption).

**Thin or placeholder (marked "done" in the old product roadmap, but shallow):**

- Faction "intent" chooses a posture but **mutates nothing** — an open loop.
- Internal politics is a **one-way stability decay** (`100 − stat`), with no recovery
  and monthly re-triggering once collapsed.
- Faction `power_level/wealth/stability` are abstract 0–100 stats with **no material
  backing**.
- Battle, logistics/movement, historian mode exist as isolated slices, not wired into
  the persisted monthly loop.

**Not started (the core of this project):**

- The **Prime Law / conservation model** — stockpiles, labor pools, capacities,
  recipes, prerequisite-gated actions.
- The `§7` deterministic formulas and the `§8` **dice/random log**.
- **Characters and kingdom founding.**
- Province pressure, emergent conflict, historical memory, chronicle-from-logs.

---

## 9. Unified Build Order (Stages)

One linear plan. Each stage states its **goal**, **dependency focus**, **scope**, and
**conservation acceptance criteria**. Old phase numbers are mapped in §12.

### Stage 0 — Direction lock ✅ (this document)
Merge roadmaps; adopt the Prime Law; reconcile status. **Exit:** one canonical roadmap
(this file) referenced by the roadmaps README.

### Stage 1 — Material foundation (source of truth for stuff)
**Goal:** give every realm countable backing. **Dependency focus:** people + land.
**Scope:** `MaterialState` per realm — stockpiles (silver, food, iron, timber, stone,
tools, equipment), labor pools (farmer/miner/artisan/laborer/soldier/idle), capacities
(farmland/mine/workshop); seed from existing kingdoms/provinces; persist to SQLite;
checkpoint round-trip.
**Conservation acceptance:** no stockpile or labor pool can be created except by
seeding or by a logged recipe/action; save/load preserves exact material state.

### Stage 2 — Production chains & prerequisite engine (the Prime Law, live)
**Goal:** replace flat production with recipe-driven production. **Dependency focus:**
the §4.2 chains. **Scope:** data-driven recipes (`config/data/world.json`); a
deterministic resolver that produces outputs only from available inputs/labor/capacity,
partial on shortage, naming the limiting input; prerequisite-gated recruitment and
construction; wire into the monthly production pulse; audit/observer logs per recipe.
**Conservation acceptance:**
- Food only increases when farmers + tools + farmland are present; remove tools and food
  output falls, with `input:tools` logged as the limiting factor.
- Recruiting with insufficient silver/food/equipment is **rejected** and names the deficit;
  no partial spawn.
- Every produced/consumed unit appears in an audit entry; totals conserve across a month.

### Stage 3 — Deterministic formulas & the dice log
**Goal:** honor the contract's math and make randomness auditable. **Scope:** implement
`§7` formulas for income/food/stability/unrest/construction/movement; add the `dice_log`
(base, modifiers, clamp, roll, outcome, seed); replace `100 − stat` placeholders.
**Conservation/audit acceptance:** a treasury change, food shortage, and a random check
each trace to a formula and/or a dice-log row; same seed + same state ⇒ same outcome.

### Stage 4 — Autonomous faction decision loop (closed)
**Goal:** decisions consume prerequisites and change state. **Scope:** pressures from real
material state (hunger, debt, threat, unrest, ambition) + personality → intents; intents
resolve into prerequisite-gated actions (tax, recruit, build, fortify, seek alliance);
invalid intents logged as rejected with reason.
**Conservation acceptance:** a starving realm that "decides to recruit" is blocked for lack
of food and the block is logged; different personalities under identical material state
produce different, auditable action distributions.

### Stage 5 — Characters, dynasties & kingdom founding
**Goal:** characters make history; realms are produced under the Prime Law. **Scope:**
`Character` (ambition, followers, silver, legitimacy, traits, home province, lifecycle);
`KingdomFoundingEngine` (founder + followers + silver + legitimacy + unclaimed land →
new realm); succession/aging/death; blocked ambitions logged.
**Conservation acceptance:** no realm is ever created without a founder consuming
followers + silver on an unclaimed province; a would-be founder short on any prerequisite
produces a logged blocked-founding, not a kingdom.

### Stage 6 — Province pressure & internal politics/collapse
**Goal:** realms rot from within; provinces diverge. **Scope:** province unrest/prosperity/
loyalty from `§7` formulas; legitimacy, noble loyalty, corruption, war exhaustion, tax
burden; crises (tax riot, revolt, coup, civil war, separatism) **with recovery paths and
post-crisis cooldown** (fixing the current one-way decay).
**Conservation acceptance:** a militarily strong realm can collapse from famine/debt/
legitimacy loss; stability can also recover when food/security/legitimacy improve; no
faction re-emits an identical crisis every month.

### Stage 7 — Logistics, movement & supply endurance
**Goal:** physical constraints on armies. **Scope:** operational army/force grouping;
route/progress movement over days; supply endurance + the `§10` shortage ladder;
weather/road modifiers; contact detection — all consuming real food/supply from stockpiles.
**Conservation acceptance:** an army consumes food each pulse from a real stockpile/route;
cut the supply and it strains → starves → attrites → turns back, all logged.

### Stage 8 — Emergent conflict: war, battle, siege, rebellion
**Goal:** violence emerges from state, not scripts. **Scope:** war/hostility escalation;
rebellion triggers from province/realm pressure; battle/siege resolver
(power × training × morale × fatigue × terrain × commander × supply × random-from-dice-log);
casualties, morale/fatigue shifts, commander risk, retreat/pursuit; post-conflict effects on
economy, politics, diplomacy, logistics.
**Conservation acceptance:** casualties remove real soldiers (labor) and equipment; a battle
cannot occur without armies that were themselves recruited under Stage 2; every battle
produces an auditable report citing its inputs and rolls.

### Stage 9 — Diplomacy, memory & historian mode
**Goal:** realms react to history; records become unreliable. **Scope:** relations
(opinion/trust/fear/threat/claims/treaties/war support); faction memory of wars, betrayals,
famines, foundings; historian accounts (master truth vs public vs faction vs later historian)
with confidence/rumor/age/contradictions.
**Acceptance:** a recent betrayal changes behavior differently than an old neutral relation;
one hidden event yields multiple differing accounts tied to the same event id.

### Stage 10 — Chronicle generation & observatory UX
**Goal:** make the world enjoyable to watch and read. **Scope:** monthly chronicles and
yearly annals generated **from logs** (never inventing facts); battle/famine/rebellion/
founding reports; observatory dashboard — timeline, event browser, faction/province/army/
character inspectors, material-flow & shortage panels, run controls, chronicle reader, export.
**Acceptance:** every chronicle entry cites underlying event/log ids; a user can run, pause,
inspect, and read history without opening raw SQLite/workbook files.

### Stage 11 — Content expansion (the old CONTENT roadmap)
**Goal:** richness after the loop works. **Scope:** more kingdoms/starts; named dynasties &
succession trees; regional event packs; culture/religion/legitimacy variants; weather/seasonal
packs; chronicle voice/historian-bias packs; more army variety.
**Gate:** only after Stages 1–10 produce readable, conserving history on their own.

### Stage 12 — Scale, balance, soak & release hardening
**Goal:** robust long runs and external usability. **Scope:** profiling; statistical run
analysis & balance tooling; scenario presets & seeds; save-migration guarantees; packaging;
docs polish; example scenarios; tutorial.
**Acceptance:** 100-year runs produce varied but plausible histories with **no impossible
state and no conservation violations**; a user can install, run, inspect, and replay without
developer help.

---

## 10. Feature Priority Tiers

**Tier 1 — MVP of the conserving world:** material foundation; production chains &
prerequisite engine; deterministic formulas + dice log; closed faction decision loop;
character founding; basic collapse with recovery; monthly chronicle from logs;
save/load/checkpoint; long-run soak smoke test.

**Tier 2 — after MVP:** logistics/movement/supply; battle & siege; province pressure depth;
diplomacy reactions & coalitions; faction & character memory; historian disagreement; yearly
annals; observatory dashboards.

**Tier 3 — nice-to-have:** rich historian bias modes; map viewer; timeline UI; procedural
dynasties & names; chronicle prose variants; scenario editor; modding; advanced weather/
seasonal regional modeling.

**Tier 4 — explicitly out of scope now:** player faction control; tactical battle control;
real-time 3D map; multiplayer; character inventory/quests; cutscene/animation/VFX pipelines.

---

## 11. Testing, Invariants & QA

**Conservation invariants (new, enforced in long-run soak tests):**

- No stockpile, unit, building, or realm exists without a seeding record or a logged
  production/action/founding that created it.
- Monthly production conserves: every consumed input and produced output is accounted for in
  audit rows; no untracked creation or destruction.
- No negative population, soldiers, treasury, food, or resources unless explicitly modeled as
  debt.
- Every recruited soldier traces to consumed silver/food/equipment; every battle casualty
  removes real labor/equipment.
- No realm exists without a founder record and a claimed province; no founding occurs with an
  unmet prerequisite.

**Contract invariants (retained from `RULES_FRAMEWORK.md §14, §16`):** every mutation is
auditable; random checks are logged and seed-deterministic; past dates are not silently
rewritten; checkpoints round-trip queues, seeds, and schema version.

**Standard invariants:** no unit without a faction; no army with impossible location/route; no
battle referencing missing entities; no chronicle entry citing missing event/log ids; no
project above 100% or active after completion.

**Test categories:** scheduler order/determinism; audit-on-mutation; dice determinism;
recipe/prerequisite conservation; intent validation & rejection; shortage ladder effects;
movement/contact; battle outcomes; politics collapse **and recovery**; founding
success/blocked; chronicle-cites-logs; soak runs at 10 / 100 / 1,000 simulated years.

---

## 12. Old → Unified Stage Mapping

| Old reference | Unified stage |
| --- | --- |
| Modularization Phases 1–10 (foundation, calendar, pulses, observer logs) | Pre-Stage-1 foundation (done) |
| Living Chronicle Phase 1–2 (chronicle skeleton, scheduler) | Foundation (done) + Stage 10 (chronicle depth) |
| *New — the project's actual core* | **Stage 1 (material), Stage 2 (conservation), Stage 3 (formulas + dice)** |
| Living Chronicle Phase 3 / Modularization Phase 11 (Faction AI) | Stage 4 (now with real material inputs) |
| *New — headline vision* | **Stage 5 (characters & kingdom founding)** |
| Modularization Phase 12 (province pressure) / Living Chronicle Phase 6 (collapse) | Stage 6 |
| Living Chronicle Phase 4 (logistics/movement), Rules §10 | Stage 7 |
| Modularization Phase 13 / Living Chronicle Phase 5 (battle/siege), Rules §9 | Stage 8 |
| Modularization Phase 14 / Living Chronicle Phase 7 (memory, historian), Rules §12–13 | Stage 9 |
| Modularization Phase 15 / Living Chronicle Phase 8 (observatory) | Stage 10 |
| `CONTENT_ROADMAP.md` (all buckets) | Stage 11 |
| Modularization Phase 16 / Living Chronicle Phase 9–10 (scale, balance, release) | Stage 12 |

---

## 13. Risk & Cut Plan

| Risk | Mitigation | Cut if needed |
| --- | --- | --- |
| Scope too large | Build the smallest conserving loop first (Stages 1–2) | Delay historian/politics depth, UI |
| Conservation math becomes unbalanced | Illustrative recipes now, tune in Stage 12 | Keep chains shallow before deepening |
| AI/decisions feel random | Log pressures, intents, rejected reasons, rolls | Keep intent rules simple and visible |
| Simulation too slow at scale | Batch writes; daily detail only for active events; monthly abstraction off-screen | Reduce daily granularity |
| Chronicle invents facts | Generate only from logs/state; cite ids | Plain reports before prose |
| Save/load breaks long runs | Version schema early, checkpoint often, round-trip tests | Reset only in prototypes, never post-MVP |
| Roadmaps drift apart again | This is the single canonical roadmap; others are archived references | — |

---

## 14. Definition of Done for the Core Vision

The unified direction is proven when the simulation can:

1. Run 10+ simulated years with no player orders.
2. Produce **all** resources, units, buildings, and realms strictly from inputs, with every
   creation traceable to a recipe/action/founding (**conservation holds**).
3. Let autonomous factions and characters make validated, prerequisite-gated decisions.
4. Let ambitious characters **found new kingdoms** from followers, wealth, legitimacy, and land.
5. Enforce logistics/supply constraints on war and politics.
6. Resolve movement, battles, casualties, diplomacy, and internal crises from state.
7. Persist all state, seeds, and checkpoints; replay deterministically.
8. Log all major causes, rolls, and consequences.
9. Generate monthly/yearly chronicles from logs, each citing its sources.
10. Produce at least one disputed history where public/faction/historian accounts differ from
    master truth.
11. Pass long-run invariant tests — including the conservation invariants — with no impossible
    state.

---

## 15. Immediate Next Steps

1. Adopt this document as the single roadmap; treat `MODULARIZATION_ROADMAP.md`,
   `LIVING_CHRONICLE_ROADMAP.md`, and `CONTENT_ROADMAP.md` as archived references.
2. Begin **Stage 1 (material foundation)** in thin, tested slices, then **Stage 2
   (production chains & prerequisite engine)** — the point at which the world stops being an
   instrumented ledger and starts obeying the Prime Law.
3. Add the **dice log** alongside the first §7 formula so randomness is auditable from the start.
4. Keep the roadmaps README pointed here; do not reopen parallel roadmaps.

---

## 16. North Star

The strongest version of this project is not a war game with the player removed. It is a
**living historical engine** where rulers and characters make decisions, farmers and miners
feed the realm, supply lines break, cities starve, ambitious lords **found new kingdoms**,
nobles betray, dynasties collapse, commanders become legends, records lie, historians argue —
and where **nothing in that history ever appears without the people, land, wealth, and work
that produced it.**
