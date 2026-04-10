# Decision 0002 – Project Framing and Domain Hierarchy

## Date
2025-07-10

## Status
Accepted

## Context
The CyberneticsAR project involves multiple agents working across two fundamentally
different types of work:

1. **CyberneticsNLP** is a research project with defined objectives and a
   planned end state. Upon publication, its outputs (knowledge graph, NLP
   models, corpus) will be archived and locked down for reproducibility.
   The corpus is fixed at 675 books.

2. **CyberneticsAR** is a product/service development effort with a
   potentially open-ended lifecycle, distinct scaling needs (100+ concurrent
   users, growing corpus), and production-grade infrastructure requirements.

Without explicit framing, AR development could impose constraints on NLP
research, or NLP changes could destabilise AR development.

## Decision
Three principles govern the relationship between the two projects:

1. **CyberneticsNLP is canonical with respect to research integrity and
   reproducibility.** AR requirements cannot constrain the NLP project unless
   compatible with the research on its own terms. Once archived, NLP outputs
   are immutable; AR must be designed to operate against static artefacts.

2. **CyberneticsAR is staged, provisional, and a separate concern.** The
   current shared infrastructure (single GitHub repo, OneDrive) is a pragmatic
   temporary arrangement, not a long-term commitment. AR must be designed for
   eventual independence. Future corpus growth beyond 675 books is an AR
   responsibility, not an NLP one.

3. **Migration is expected but conditional.** AR components may migrate to
   maintained status only when all of the following are met:
   - Technical stability across target devices
   - Semantic fidelity with NLP/KG outputs
   - Positive user validation
   - Stable, documented data contracts
   - AG2 recommendation and human integrator approval

   Migration may also be triggered protectively if AR operational demands
   (e.g. speed over accuracy) become incompatible with NLP research integrity.

## Rationale
Protects NLP research integrity from product development pressures.
Acknowledges divergent lifecycles. Prevents premature coupling.
Enables clean future separation by encoding intent from the outset.

## Coordination Impact
- AR agents must treat NLP outputs as read-only and research-governed.
- Change requests from AR that affect NLP outputs require upstream justification
  compatible with research standards.
- Shared infrastructure decisions must consider eventual separation.
- After NLP archival, no further changes to NLP outputs are possible;
  AR must build its own processing for new material.

## Consequences
- AR design must anticipate operating against frozen NLP artefacts.
- CyberneticsAR will need NLP-equivalent processing capability
  if corpus growth is pursued post-migration.
- Migration criteria must be actively tracked as NLP approaches its end state.

## Related
- Decision 0001 – AG2 Coordination and Staged AR Development
- AG2 Session 01
