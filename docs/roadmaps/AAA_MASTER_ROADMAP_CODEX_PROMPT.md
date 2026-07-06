# Codex prompt for AAA master roadmap sequencing

Use this after reading `docs/roadmaps/AAA_MASTER_ROADMAP_V1.md`.

```text
You are working on War Gods: Total War.

Use docs/roadmaps/AAA_MASTER_ROADMAP_V1.md as the master sequencing document.

Rules:
1. Do not add features out of order unless the roadmap says they are allowed as an early dependency.
2. Every phase must pass through Design -> Data -> Simulation -> UI -> Validation -> Save/Load -> Balance -> Presentation -> Closing Gate.
3. Keep debug text out of normal player-facing UI.
4. Keep raw IDs, AI scores, map RGB, CSV row references and validation details inside debug/validation views only.
5. Do not add 100+ factions before World Scale Gate 1 and World Scale Gate 2 pass.
6. Do not return to final map art, rivers or trees before the presentation phase unless fixing a bug.
7. Every new system must connect to at least one existing system and must be validated.
8. Every major event must be explainable in clean player-facing language.
9. Preserve save/load compatibility where possible.
10. Add tests or smoke checks for every major system.

Current immediate order:
1. Complete the data validation and technical quality gate.
2. Complete the UI copy, SPAG and presentation language gate.
3. Prepare data architecture and scenario foundation.
4. Expand to World Scale Gate 1: 16-20 serious powers.
5. Continue into core simulation depth, character systems, dynasties, courts, memory, culture, institutions, diplomacy, economy, non-state actors, espionage, knowledge, disasters, magic, naval systems, tools, scale gates, presentation and release.

When implementing a phase:
- Break it into A/B/C/D subphases.
- Implement one subphase at a time.
- Add a closing gate check before moving to the next subphase.
- Do not mix unrelated roadmap phases in the same change.
```
