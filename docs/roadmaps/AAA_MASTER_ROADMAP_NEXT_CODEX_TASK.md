# Next Codex task from the AAA master roadmap

The validation, UI language, scenario foundation, world scale and faction AI priority gates are complete. The immediate next task is the internal politics slice.

## Next task

```text
Begin Phase 6-B: internal politics first pass.
```

## Codex prompt

```text
Begin Phase 6-B from docs/roadmaps/AAA_MASTER_ROADMAP_PHASE_06_CORE_SIMULATION_DETAIL.md: add internal politics first pass.

Tasks:
1. Add internal state values for court tension, succession tension, army influence, tax burden, faith tension, culture tension, regional autonomy, noble loyalty and merchant loyalty.
2. Make internal state respond to ruler traits, wars, exhaustion, treasury pressure, occupied land, culture/faith mismatch and realm size.
3. Make internal state affect war willingness, taxes, revolt risk and succession pressure.
4. Show internal politics clearly in the realm inspector.
5. Keep map cosmetics unchanged.
6. Do not add new factions or provinces in this slice.
```

## Closing gate

Phase 6-B is closed only when:

```text
Strong factions can suffer internal instability.
Internal state affects war willingness, taxes, revolt risk and succession.
Realm inspector explains internal stress in player language.
Existing balance and validation gates still pass.
Existing tests still pass.
```

Phase 5 is closed only when:

```text
the world has 16-20 serious powers
each power has a distinct role and valid data
a 50-year balance smoke run avoids total chaos and total silence
existing tests still pass
```

## Completed

```text
Phase 2: Data Validation and Technical Quality Gate — DONE
Phase 3: UI copy, SPAG and presentation language gate — DONE
Phase 4: Data architecture and scenario foundation — DONE
Phase 5-A: Faction tier support — DONE
Phase 5-B: Add 8 new major or regional powers — DONE
Phase 5-C: Regional balance pass — DONE
Phase 6-A: Faction AI priorities — DONE
```
