# Closing gate definition

A closing gate is the checklist that proves a phase or subphase is actually done.

A system is not done when it merely exists in data or code.

## Standard closing gate

A phase closes only when:

```text
1. Data exists.
2. Simulation uses it.
3. Player-facing UI displays it cleanly.
4. Debug UI can inspect it.
5. Validation catches broken references.
6. Save/load preserves it.
7. Events explain it in readable language.
8. Chronicle can mention it where relevant.
9. A short simulation test proves it works.
10. Existing systems still work.
```

## Example

Naval power is not done when fleets exist.

It closes only when:

```text
ports exist and validate
fleets exist and validate
fleet missions affect trade/war/sieges
sea routes and blockades work
army transport obeys rules
save/load preserves naval state
UI shows clean naval info
25-year coastal war test passes
```
