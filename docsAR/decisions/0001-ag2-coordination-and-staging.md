# Decision 0001 – AG2 Coordination and Staged AR Development

## Date
2026-03-22

## Status
Accepted

## Context
CyberneticsNLP is the canonical project in this repository.
CyberneticsAR is a related but distinct effort being developed in parallel.

Multiple AI agents may perform independent work.
Uncoordinated parallel activity risks semantic drift, pipeline breakage,
or accidental authority inversion.

## Decision
CyberneticsAR will be developed as a **staged extension** using explicit
`*AR` directories (e.g. `docsAR/`, `srcAR/`) with the following constraints:

- `docs/` and `src/` remain canonical for CyberneticsNLP.
- `docsAR/` and `srcAR/` are provisional and non‑canonical.
- No reverse dependencies from canonical paths into `*AR` paths.
- Migration of AR assets is expected and should be mechanically achievable.

AG2 sessions are used for alignment, while durable decisions are documented
explicitly.

## Rationale
Explicit staging avoids scope creep while permitting serious exploration.
Naming and directory structure encode intent directly, reducing reliance
on human memory or informal convention.

## Coordination Impact
- AI agents must treat `*AR` content as staged.
- Outputs affecting shared assumptions require explicit documentation.
- Migration should involve path replacement, not conceptual refactoring.

## Consequences
- Parallel AR work may proceed without redefining the NLP project.
- Governance artifacts become first‑class during staging.

## Related
- AG2 Session 01 agenda
