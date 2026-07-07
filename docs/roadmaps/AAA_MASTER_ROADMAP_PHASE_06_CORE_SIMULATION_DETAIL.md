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

## 6B. Internal politics first pass

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

## 6C. Revolts and instability

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
