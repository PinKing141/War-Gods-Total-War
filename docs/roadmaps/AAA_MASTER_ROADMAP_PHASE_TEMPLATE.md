# AAA roadmap phase template

Use this template for any future phase added to the roadmap.

```text
# Phase X. Phase Name

## Purpose

What this phase adds to the game and why it belongs here.

## Dependencies

What must already be complete before this starts.

## XA. First subphase

### Build

The first concrete system to implement.

### Interlinks

What existing systems this must connect to.

### Validation

What references, values, states or save/load behaviour must be validated.

### UI

What the player should see and what must remain debug-only.

### Closing gate XA

The exact condition that proves this subphase is complete.

## XB. Second subphase

Repeat the same format.

## Phase closing gate

The full phase is complete only when:

1. All subphase gates are complete.
2. Validation passes.
3. Save/load works.
4. Normal UI is clean.
5. Event text is readable.
6. A short simulation test proves it works.
7. Existing systems still pass.
```
