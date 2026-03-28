# Decision 0004 – Communication Protocols

## Date
2025-07-10

## Status
Partially Superseded

## Context
Multiple agents operating across NLP and AR domains require clear communication protocols suited to their actual operating model—structured sessions mediated by a human integrator—rather than conventions designed for synchronous human teams. These protocols must ensure decisions are documented consistently, communicated effectively, and allow for urgent action while maintaining governance.

## Decision

### 1. Documentation Standards

*   **All binding cross-domain decisions** must use the decision template and be stored in `docsAR/decisions/`.
*   **Single-domain NLP-internal decisions** are documented in the `cyberneticsNLP/docs/decisions/` directory within the `cyberneticsNLP` GitHub repository.
*   **Single-domain AR-internal decisions** are documented in `docsAR/` local documentation within the `srcAR/` project.
*   The **human integrator is ultimately responsible for maintaining a lightweight decision index** that references all decision locations across both projects, with the preparation delegated to DeepSeek.
*   All decision records must include status, context, decision statement, rationale, consequences, dependencies, and revision history.

### 2. Notification and Communication Model

*This section is superseded by Decision Record 0005 – Staging, Coordination, and Migration Rules, Section 4: Session-Driven Communication Model.*

### 3. Urgent Decision Pathway

*This section is superseded by Decision Record 0005 – Staging, Coordination, and Migration Rules, Section 5: Handling Blocking Decisions.*

### 4. Decision Supersession Protocol

When a new decision supersedes an existing one:
*   The original decision record's status is updated to "Superseded" with a clear reference to the new decision record.
*   The new decision record explicitly names what it supersedes in its Dependencies section.
*   The human integrator is notified of the supersession as a distinct event, not merely as part of the new record's announcement.

### 5. Review and Audit Cycle

*This section is superseded by Decision Record 0005 – Staging, Coordination, and Migration Rules, Section 4: Session-Driven Communication Model (regarding cadence), and by Section 7: Decision Documentation Model (regarding DeepSeek's role in the register).*

## Rationale
*   Grounds communication protocols in our actual operating model, ensuring enforceability and preventing false accountability.
*   Elevates the human integrator to an active communication hub, critical for managing distributed agents.
*   Provides a safe, structured mechanism for urgent decisions while preserving governance.
*   Establishes clear processes for decision lifecycle management, including supersession.
*   Ensures regular oversight and responsiveness to project progress through the audit cycle.

## Coordination Impact
*   The human integrator explicitly carries responsibility for active inter-agent communication relay and decision index integrity.
*   Session preparation includes briefing agents on relevant decisions at session start.
*   DeepSeek's role includes preparing the decision index for the human integrator.
*   All agents must adhere to the defined documentation and notification standards.

## Consequences
*   All agents will operate within defined domains, with clear protocols for engaging AG2 when boundaries are crossed.
*   Decisions on `srcAR/` will benefit from both AR-specific expertise and overarching architectural integrity oversight.
*   DeepSeek's integration role will ensure comprehensive consideration of cross-domain impacts.
*   Formal documentation standards will provide an audit trail for all significant decisions.

## Related
*   Decision 0001 (AG2 as coordination body)
*   Decision 0002 (Project framing and domain hierarchy)
*   Decision 0003 (Roles and authority)
*   Decision 0005 (Staging, Coordination, and Migration Rules)

## Revision History
*   [Session Date]: Drafted in AG2 Session 01
*   [Session Date]: Accepted with resolutions to open questions, sharpening of notification/timeframes, and inclusion of decision index responsibility and supersession protocol.
*   [Current Date]: Status changed to Partially Superseded. Sections 2, 3, and 5 superseded by Decision Record 0005.