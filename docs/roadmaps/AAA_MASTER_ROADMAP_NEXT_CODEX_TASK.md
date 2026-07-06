# Next Codex task from the AAA master roadmap

The immediate next task is not a new feature. It is the first required gate.

## Next task

```text
Begin Phase 2: Data Validation and Technical Quality Gate.
```

## Codex prompt

```text
Begin Phase 2 of docs/roadmaps/AAA_MASTER_ROADMAP_V1.md: Data Validation and Technical Quality Gate.

Tasks:
1. Create a validation module/test suite.
2. Validate unique IDs for provinces, factions, characters, armies, wars, claims, institutions, cultures, religions and scenarios.
3. Validate all object references:
   - province controller exists
   - province owner exists
   - character faction exists
   - army owner exists
   - army location exists
   - adjacency links are valid
   - war attackers and defenders exist
   - war goal provinces exist
   - claims have valid claimant and target
   - mage patron exists
   - institution home province exists
   - treaty parties exist if treaties already exist
4. Validate numeric bounds:
   - population >= 0
   - garrison >= 0
   - army size >= 0
   - treasury is valid
   - manpower is valid
   - fort level is valid
   - road level is valid
   - devastation is within range
   - supply is within range
   - relations/opinion values are within range
5. Output clear failure messages naming the exact file, row, field and broken value.
6. Add save/load tests or smoke checks for war, siege, ruler death, revolt and treaty state where those systems exist.
7. Add a 25-year smoke simulation test.
8. Do not add map cosmetics.
9. Do not add new world content.
10. Do not change player-facing UI copy except where validation errors need readable wording.
```

## Closing gate

Phase 2 is closed only when:

```text
broken IDs fail loudly
broken references fail loudly
invalid numbers fail loudly
validation runs before scenario start
25-year smoke test passes
existing tests still pass
```
