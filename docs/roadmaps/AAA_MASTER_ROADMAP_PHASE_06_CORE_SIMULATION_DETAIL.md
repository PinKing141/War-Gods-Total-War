# Phase 6 Core simulation depth Phase 2 detail

This phase makes factions feel like political bodies with motives, stress,
survival problems and internal weakness.

## 6A. Faction AI priorities — DONE

Build:

```text
Give each faction weighted priorities:
- expand territory
- protect homeland
- recover old claims
- raid for wealth
- avoid war
- secure trade routes
- hold mountain passes
- control ports
- defend faith
- destroy rival
- survive economic stress
```

Closing gate:

```text
Faction decisions are scored by profile and context.
Event logs explain major decisions in player language.
Different faction archetypes behave differently.
```

Completed with:

```text
- live AI priority scoring added to the browser simulation
- priority scoring considers faction profile, ruler traits, claims, relations, army strength, treasury, manpower, active wars, exhaustion, strategic holdings, ports and passes
- war declaration chance now uses the attacking faction's current priorities
- war cause text explains the court priority behind the decision
- realm inspector shows top faction priorities and reasons
- regression tests prove raider, trade, pass and faith archetypes score differently
- runtime stress changes priorities toward survival and war avoidance
- 50-year multi-seed balance gate still passes
- 25-year observer validation passes
- full test suite passing
```

## 6B. Internal politics first pass — DONE

Build:

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

Closing gate:

```text
Strong factions can suffer internal instability.
Internal state affects war willingness, taxes, revolt risk and succession.
```

Completed with:

```text
- internal politics state added to every runtime faction
- tracked court tension, succession tension, army influence, tax burden, faith tension, culture tension, regional autonomy, noble loyalty, merchant loyalty, revolt risk and succession pressure
- monthly internal politics updates respond to wars, deficits, exhaustion, occupations, sieges, manpower pressure, weak succession and realm structure
- internal state affects monthly income through tax burden and merchant loyalty
- internal instability affects war willingness without freezing regional tension
- realm inspector shows internal stability, revolt risk, succession pressure and top internal stress causes
- validation now reports missing, invalid or out-of-range internal politics state
- tests prove strong/stressed factions can suffer internal instability and that stress affects economy and war appetite
- 50-year multi-seed balance gate still passes
- 25-year observer validation passes
- full test suite passing
```

## 6C. Revolts and instability — DONE

Build:

```text
Province instability comes from:
- devastation
- occupation
- recent conquest
- low garrison
- culture mismatch
- faith mismatch
- high taxes
- famine
- weak ruler
- foreign support

Revolt types:
- peasant revolt
- noble revolt
- separatist revolt
- religious uprising
- pretender revolt
- military coup
- frontier independence
```

Closing gate:

```text
Revolts can start, fight, win, lose and be recorded.
Revolt causes are visible in UI and event logs.
Revolt risk is validated and save/load safe.
```

Completed with:

```text
- province instability scoring added from devastation, occupation, recent conquest, low garrison, internal culture/faith tension, high taxes, autonomy, weak loyalty, famine, weak ruler and foreign support
- revolt type selection added for peasant revolt, noble revolt, separatist revolt, religious uprising, pretender revolt, military coup and frontier independence
- revolts now start as runtime conflicts with type, causes, strength, progress, status and outcome
- monthly revolt pulse lets revolts spread, be suppressed or win
- winning revolts can transfer province control to a strong claimant, devastate the province and increase recent conquest pressure
- suppressed revolts are recorded and reduce local instability without magically healing the province
- province inspector shows instability score, causes and active revolt progress
- realm inspector shows active revolt count
- validation checks revolt province, target, status, strength, progress and province revolt links
- tests cover revolt start, win, suppression and broken revolt validation
- 50-year balance validation passing
- 25-year observer validation passing
- full test suite passing
```

## 6D. Succession and ruler death expansion — DONE

Build:

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

Closing gate:

```text
Ruler death can cause stable succession, regency or crisis.
Succession results update ruler, heir, claims, faction state and chronicle.
```

Completed with:

```text
- succession state added to every runtime faction
- inheritance law, heir legitimacy, regency, crisis state, pretenders and last transition are tracked
- heir legitimacy considers bloodline, age, prestige, internal politics and succession law
- ruler death can now produce stable succession, regency or succession crisis
- succession crisis records pretenders, backing factions, pretender claims and chronicle events
- severe succession pressure can trigger a pretender revolt in the capital
- succession results update ruler, faction succession state, claims, internal politics and event logs
- realm inspector shows succession law, heir legitimacy, crisis risk, regency, crisis and pretenders
- validation checks succession law, heir legitimacy and pretender references
- tests cover stable succession, regency, succession crisis, pretender claims and broken succession validation
- 50-year balance validation passing
- 25-year observer validation passing
- full test suite passing
```

## 6E. Simple survival economy — DONE

Build:

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

Closing gate:

```text
Economy affects war decisions, unrest, peace desire and faction survival.
UI labels stay polished: Economy, Treasury, Taxation, Food.
```

Completed with:

```text
- explicit runtime economy state added to every faction
- tracked war debt, food stress, trade value, devastation loss, tribute due and last survival decision
- economy snapshots expose treasury, income, upkeep, court costs, debt service, tax burden, food stress, trade, devastation loss and tribute
- monthly survival decisions can raise taxes, lower taxes, borrow money, sell privileges, dismiss armies and squeeze conquered land
- survival decisions affect tax burden, loyalty, debt, treasury, devastation, unrest and revolt risk
- war debt and unaffordable war economy can push factions toward peace
- realm inspector uses polished Economy, Treasury, Taxation, Food, Trade, War Debt and Tribute labels
- validation checks missing, invalid and negative economy state
- tests cover economy tracking, survival decisions, debt pressure, peace pressure and broken economy validation
- 50-year balance validation passing
- 25-year observer validation passing
- full test suite passing
```

## Phase 6 closing gate — DONE

```text
Core simulation depth Phase 2 is complete: faction priorities, internal politics,
revolts, succession and survival economy now interact and remain validated.
```
