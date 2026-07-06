# Phase 20 Naval detail example

This file exists to show the subphase gate style requested for complex systems.

## 20A. Port system

Ports are first because fleets need ports to exist.

Closing gate:

```text
Ports validate.
Ports affect economy and trade.
Province UI shows Harbour/Port data in polished player language.
```

## 20B. Fleet objects

Fleets come after ports because they need home ports and valid locations.

Closing gate:

```text
Fleets exist, move between valid ports/sea zones, validate ownership/location, and survive save/load.
```

## 20C. Fleet missions

Missions come after fleet objects because a fleet needs valid state before it can act.

Closing gate:

```text
Patrol, escort, blockade, raid, transport and intercept missions all have visible effects and readable event logs.
```

## 20D. Sea routes and blockades

Sea routes come after ports and fleets because routes need port endpoints and blockades need fleet missions.

Closing gate:

```text
Blockades affect trade, food imports, war exhaustion, merchant loyalty, city unrest and coastal siege progress.
```

## 20E. Army transport and amphibious movement

Transport comes last because it depends on ports, fleets, routes and blockade/interception logic.

Closing gate:

```text
Armies cannot teleport across water. Embark/disembark rules work. A 25-year coastal war test passes.
```
