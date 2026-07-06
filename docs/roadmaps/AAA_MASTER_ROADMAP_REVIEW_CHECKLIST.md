# Master roadmap review checklist

Use this when reviewing Codex work against the roadmap.

## For every PR/change

```text
Does this belong to the current phase?
Does it complete one subphase gate?
Does it avoid mixing unrelated work?
Does it add or update validation?
Does save/load still work?
Does normal UI avoid debug wording?
Does event text read naturally?
Does the chronicle have enough information later?
Does the change avoid unnecessary map polish?
Does it pass smoke tests?
```

## Red flags

```text
new content without validation
new UI labels using debug language
new systems with no save/load path
new mechanics with no event explanation
new factions before validation
new naval transport before ports/fleets
new visuals before presentation phase
one huge Codex prompt changing many unrelated systems
```
