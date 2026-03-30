# Decision 0005 – Staging, Coordination, and Migration Rules

## Date
2025-07-10

## Status
Accepted

## Context
Multiple agents working in parallel across CyberneticsNLP and CyberneticsAR
create specific coordination risks:

- **Semantic drift:** Agents independently evolving concepts or terminology
  in ways that diverge from the canonical NLP project.
- **Hidden assumptions:** An agent making implementation choices that
  presuppose decisions not yet made or not yet communicated.
- **Pipeline breakage:** Changes in one domain silently breaking downstream
  dependencies in another — particularly where AR consumes NLP outputs.

Additionally, the meaning of `*AR` directories, output classification rules,
and migration expectations need to be explicit and enforceable, not informal.

The project operates under unique constraints: the human integrator is the
sole session initiator, agents lack persistent memory between sessions,
and the self-funded experimental nature means "urgency" is relative to
human availability rather than external deadlines.

## Decision

### 1. Output Classification

All agent outputs must be labelled at the point of production:

- **[EXPLORATORY]** — investigation or proposal without commitment;
  no production implementation permitted.
- **[PROVISIONAL]** — AG2-approved but reversible implementation;
  requires explicit reversibility mechanisms.
- **[PROPOSED BINDING]** — recommended for acceptance; requires AG2 review
  before implementation.
- **[IMPLEMENTATION]** — work within already-accepted constraints;
  no new decisions being made.

Unlabelled outputs must be treated as **[EXPLORATORY]** by default and
cannot proceed to implementation until explicitly classified.

### 2. Scope and Assumption Declaration

Before undertaking independent work, an agent must declare:

- The scope of the task (which domain, which files, which decisions it relies on).
- Any assumptions being made that are not covered by an accepted decision record.
  These must be formally documented in the relevant domain documentation
  (e.g., `docsAR/` for AR, `cyberneticsNLP/docs/` for NLP) with a clear
  timestamp, agent identifier, and brief rationale.
- Any cross-domain dependencies the work creates or modifies.

Undeclared assumptions discovered after the fact must be raised at the next
AG2 session and resolved before the work is accepted.

### 3. AI-to-AI Coordination Safeguards

To prevent semantic drift and hidden assumption accumulation:

- Agents must not redefine terms already established in the NLP project
  ontology without explicit human integrator approval.
- Agents must not make cross-domain assumptions based on informal chat
  or prior session memory — only accepted decision records are authoritative.
- Where an agent identifies a gap (a decision needed but not yet made),
  it must flag it explicitly rather than filling it silently.

### 4. Session-Driven Communication Model

Given the human integrator as sole session initiator:

- **AG2 sessions are the primary forum** for all cross-domain coordination.
- **Human integrator controls cadence** — sessions scheduled based on
  availability and need to unblock agents or review progress.
- **Gemini provides session summaries** — reads and summarizes new entries
  in `docsAR/decisions/` and session agenda at start of each AG2 session.
- **Consolidated briefing** — human integrator provides single comprehensive
  briefing at session start rather than separate individual briefings.

### 5. Handling Blocking Decisions

Given lack of persistent agent memory and human-mediated sessions:

1. **Identification:** Agent identifies decision blocking further progress.
2. **Provisional documentation:** Documents as **[BLOCKING - PROVISIONAL]**
   in domain-specific docs with rationale and timestamp.
3. **Notification:** Notifies human integrator during current session or via
   persistent note (e.g., `docsAR/sessions/next-agenda.md`).
4. **Prioritization:** Human integrator prioritizes discussion in next
   available AG2 session.
5. **AG2 ratification:** Formal review in AG2 session; may ratify, modify,
   or overturn with full rationale documented.
6. **Research Integrity Veto:** Still applies to any blocking decision.

### 6. `*AR` Directory Rules

- `docsAR/` and `srcAR/` are provisional and non-canonical.
- `docs/` and `src/` remain canonical for CyberneticsNLP.
- **No reverse dependencies:** canonical paths must not import from,
  reference, or depend on `*AR` paths.
- **Mechanical migration expectation:** Migration should primarily involve
  automated refactoring (e.g., changing import paths from `srcAR/` to `src/`).
  Excludes redesigning fundamental data structures or ontological interpretations
  because AR deviated from NLP's canonical model — such conceptual refactoring
  at migration time signals governance failure.

### 7. Decision Documentation Model

- **Decision register:** Single index file (`docsAR/decisions/register.md`)
  lists all decision records with status and one-line summary.
  DeepSeek maintains this, updating within 24 hours of any decision status change.
  Human integrator holds final responsibility. Includes cross-references to
  session summaries.
- **Atomic decision records:** One decision per file, following the agreed
  template. Records are never edited to change meaning — supersession
  creates a new record.
- **Session summaries:** Each AG2 session produces a summary noting which
  decisions were made, proposed, or deferred. Stored in `docsAR/sessions/`.

### 8. Promotion Criteria (Provisional → Binding)

Provisional decisions can become binding when:
1. Implementation validated in `srcAR/`
2. No negative cross-domain impacts emerged
3. Positive user/research validation
4. Reversibility mechanisms proven unnecessary
5. AG2 recommends promotion
6. Human integrator approves

## Rationale
Explicit rules prevent the coordination failure modes identified in the
session. Labelling and declaration requirements create accountability without
requiring synchronous communication. Directory rules encode intent structurally
so it is visible to all agents regardless of session history. The model
respects actual constraints: human as bottleneck, no persistent agent memory,
self-funded experimental nature.

## Coordination Impact
- All agents must label outputs and declare scope before independent work.
- Gaps in decision coverage must be flagged, not silently resolved.
- The decision register becomes the authoritative navigation tool across
  all records.
- Pace of cross-domain decision-making depends on human integrator capacity
  to convene sessions.

## Consequences
- Agents cannot proceed with unlabelled or assumption-heavy work without
  explicit flagging.
- Migration complexity becomes a diagnostic signal — high complexity
  indicates drift.
- Session summaries become a required artefact, not optional.
- Human integrator carries responsibility for scheduling sessions and
  ensuring agents are briefed on relevant decisions.

## Related
- Decision 0001 – AG2 Coordination and Staged AR Development
- Decision 0002 – Project Framing and Domain Hierarchy
- Decision 0003 – Roles and Decision Authority
- Decision 0004 – Communication Protocols (supersedes sections 2, 3, 5)
- AG2 Session 01

## Revision History
- [Session Date]: Drafted in AG2 Session 01
- [Session Date]: Revised to incorporate feedback and align with human-driven,
  session-based coordination model
