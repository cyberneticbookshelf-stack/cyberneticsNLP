# Decision 0003 – Roles and Decision Authority

## Date
2025-07-10

## Status
Accepted

## Context
The CyberneticsAR project involves multiple specialized agents with distinct capabilities operating across different domains. Establishing clear role assignments and a decision authority matrix is necessary to enable parallel work, prevent coordination failures, resolve potential conflicts, and ensure the distinct lifecycles and integrity requirements of CyberneticsNLP and CyberneticsAR are respected.

## Decision

### Agent Roles

*   **Claude** — Lead Developer and Technical Authority
    *   Primary authority over codebase architecture, development standards, and implementation integrity across the entire project.
    *   Holds **review and veto authority** over architectural decisions within `srcAR/` that impact the broader codebase's integrity, performance, or adherence to project-wide standards.
    *   Maintains and enforces development standards and code quality.

*   **Gemini** — AR Lead and Research Domain Authority
    *   **Primary implementation authority** for AR feature design, AR visualization, and AR-specific technical approaches within `srcAR/`.
    *   Holds **Research Integrity Veto:** Can unilaterally block any decision that threatens NLP research reproducibility or integrity, triggering automatic escalation to the human integrator.
    *   Primary authority within the NLP Research domain.

*   **DeepSeek** — Integration Specialist
    *   Primary responsibility for driving cross-domain integration efforts.
    *   Brings multi-perspective analysis to decisions spanning NLP, AR, and infrastructure.
    *   Leads the Data Interface domain decisions with required input from both domain leads.

*   **Human Integrator** — Voice of Human and Final Authority
    *   Final decision authority on all cross-domain disputes and escalations.
    *   Sole authority on ontology, project scope, and migration decisions.
    *   Authority to override the Research Integrity Veto with written rationale, providing explicit justification.

### Decision Authority Matrix

| Domain | Primary Authority | AG2 Review Required | Special Provisions |
|---|---|---|---|
| NLP Research | Gemini | When decision affects AR requirements or data interfaces | **Research Integrity Veto** applies (held by Research Domain Authority) |
| AR Product | Gemini | When decision requires NLP changes or affects research integrity | Must design for eventual operation against archived NLP outputs |
| Codebase Architecture | Claude | When decision affects AR implementation approach or core architectural patterns | Claude has review/veto authority over architectural aspects within `srcAR/` |
| Data Interface | DeepSeek (led) | **Always** | Both domain leads must confirm compatibility |
| Infrastructure | Shared — Claude leads | **Always** | Decisions must consider eventual project separation |
| Cross-Domain UX | Shared — AG2 reviews | **Always** | Must balance research accuracy with user experience |
| Future: Extended Processing | TBD (post-migration) | N/A | Placeholder — not in current scope, will be defined if/when CyberneticsAR takes on this responsibility |

### Escalation and Decision Process

1.  **Identification:** Agent identifies decision scope using this matrix.
2.  **Single-Domain Internal:** If single-domain and no AG2 review explicitly required:
    *   Primary authority agent makes decision.
    *   Documents in appropriate domain-specific location (NLP or AR docs).
    *   Notifies other agents if decision might have downstream effects.
3.  **Cross-Domain or AG2 Required:**
    *   Agent creates decision proposal using the agreed-upon template.
    *   Submits to AG2 for review.
    *   AG2 reviews with both domain experts.
    *   If consensus: Decision documented in `docsAR/decisions/`.
    *   If disagreement: Human integrator makes final binding decision.
4.  **Research Integrity Veto:**
    *   The Research Domain Authority (Gemini) can invoke this at any point in the process.
    *   Veto triggers automatic, immediate escalation to the human integrator.
    *   Human integrator must either uphold the veto or provide written rationale for overriding it.

### Additional Migration Trigger — Protective Condition

In addition to the positive AR maturity criteria defined in Decision Record 002, migration may also be triggered as a **protective measure due to fundamental incompatibility between AR operational demands and NLP research integrity requirements**. If AR requirements—such as prioritizing processing speed over data accuracy at a level irreconcilable with research standards—cannot be harmonized with the NLP project's mandate, this constitutes grounds for accelerated separation, protecting research integrity regardless of AR maturity level.

## Rationale
*   Clearly assigns roles and responsibilities based on demonstrated capabilities and project needs.
*   Establishes unambiguous primary authorities for specific domains while instituting robust cross-domain review and escalation paths.
*   Provides essential protection for NLP research integrity through the explicit veto mechanism.
*   Names and resolves the potential overlap between codebase architectural authority and AR implementation authority within `srcAR/`.
*   Formally recognizes DeepSeek's crucial role as an integration specialist for complex cross-domain decisions.
*   Includes a critical protective migration trigger, safeguarding NLP research from incompatible product demands.

## Coordination Impact
*   All agents will operate within defined domains, with clear protocols for engaging AG2 when boundaries are crossed.
*   Decisions on `srcAR/` will benefit from both AR-specific expertise and overarching architectural integrity oversight.
*   DeepSeek's integration role will ensure comprehensive consideration of cross-domain impacts.
*   Formal documentation standards will provide an audit trail for all significant decisions.

## Consequences
*   The human integrator explicitly carries responsibility for active inter-agent communication relay and decision index integrity.
*   Session preparation includes briefing agents on relevant decisions at session start.
*   DeepSeek's role includes preparing the decision index for the human integrator.
*   All agents must adhere to the defined documentation and notification standards.

## Related
*   Decision 0001 (AG2 as coordination body)
*   Decision 0002 (Project framing and domain hierarchy)

## Revision History
*   [Session Date]: Drafted in AG2 Session 01
*   [Session Date]: Accepted with resolution of open questions and inclusion of protective migration trigger.
