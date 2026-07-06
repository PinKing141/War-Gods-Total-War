# Phase 6 Core simulation depth detail

This phase starts after validation, UI copy, data architecture and World Scale Gate 1.

## 6A. Faction AI priorities

Build weighted goals:

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

Closing gate:

```text
Faction decisions are shaped by profile, context, ruler traits, claims, relations, army strength, economy and neighbour weakness.
```

## 6B. Internal politics

Build realm internal state:

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
Internal politics can affect war willingness, taxes, revolt risk and succession.
```

## 6C. Revolts and instability

Build revolt causes:

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

Closing gate:

```text
Revolts can start, fight, win, lose and be recorded with readable causes.
```

## 6D. Succession and ruler death

Build:

```text
inheritance law
heir legitimacy
regency
pretender claims
succession crisis
powerful generals backing claimants
court factions backing heirs
```

Closing gate:

```text
Ruler death can cause stable succession, regency or crisis and update faction state safely.
```

## 6E. Simple survival economy

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

Closing gate:

```text
Economy affects war decisions, unrest, peace desire and faction survival.
```
