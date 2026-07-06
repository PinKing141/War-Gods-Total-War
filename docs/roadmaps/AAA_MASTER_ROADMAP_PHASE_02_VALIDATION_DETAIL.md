# Phase 2 validation detail

This is the immediate next implementation gate from the master roadmap.

## 2A. Core ID validation

Validate unique IDs for:

```text
province
faction
character
army
war
claim
institution
culture
religion
scenario
```

Closing gate:

```text
Duplicate IDs fail validation with file, row, field and value.
```

## 2B. Relationship validation

Validate references for:

```text
province controller
province owner
character faction
army owner
army location
adjacency links
war attackers
war defenders
war goal province
claim claimant
claim target
mage patron
institution home province
treaty parties
```

Closing gate:

```text
Dangling references fail validation before scenario start.
```

## 2C. Numeric bounds validation

Validate values for:

```text
population
garrison
army size
treasury
manpower
fort level
road level
devastation
supply
relations/opinion
```

Closing gate:

```text
Invalid numbers fail before the sim starts.
Suspicious but legal values produce warnings.
```

## 2D. Save/load and smoke tests

Add checks for:

```text
war state
siege state
ruler death
revolt state
treaty state
25-year simulation smoke test
```

Closing gate:

```text
Validation runs before scenario start and 25-year smoke test passes.
```
