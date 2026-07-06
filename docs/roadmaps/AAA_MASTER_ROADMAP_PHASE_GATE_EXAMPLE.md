# Phase gate example

Example: Naval power.

```text
20A Port system closes before fleets.
20B Fleet objects close before missions.
20C Fleet missions close before sea routes and blockades.
20D Sea routes and blockades close before transport.
20E Army transport closes only after ports, fleets, routes and blockade logic work.
```

This is the pattern every large phase should follow.

```text
Foundation first.
Actors second.
Actions third.
Interlinks fourth.
Advanced movement/consequences last.
```
