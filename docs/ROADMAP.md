# Roadmap

Tracks planned work, open questions, and longer-term directions.
Issues are tracked at: https://github.com/cyberneticbookshelf-stack/cyberneticsNLP/issues

Last updated: 20 April 2026 (v0.4.7)

---

## Current sprint — post-v0.4.2

**Status:** Moratorium on NLP pipeline code in effect. Presentation complete (book-level LDA). Classifier active learning underway.

### Classifier track

| # | Task | Status |
|---|------|--------|
| 1 | Second review round — review `csv/monograph_sample_*.csv` | ⏳ Pending — awaiting Paul |
| 2 | Add reviewed labels to Calibre `custom_column_5` | ⏳ Pending — follows #1 |
| 3 | Retrain classifier with expanded label set | ⏳ Pending — follows #2 |
| 4 | Target: improve recall on 71 known false negatives | ⏳ Pending |
| 5 | Acquire more negative examples (anthologies, textbooks) | ⏳ Pending |
| 6 | Consider `h_toc_contributor_names` heuristic once TOC extraction is verified | 🔵 Deferred — TOC often stripped/garbled |

### Pipeline (blocked by moratorium)

| # | Task | Status |
|---|------|--------|
| 7 | Signal inventory audit | ⏳ Pending — prerequisite for all pipeline work |
| 8 | Document unit decision (formally record) | ⏳ Pending — prerequisite for #9–10 |
| 9 | Implement exclusion filter in `03_nlp_pipeline.py` | 🔒 Blocked by #7, #8 |
| 10 | Implement style-conditioned sampling in `sample_book()` | 🔒 Blocked by #7, #8 |

### Known issues (post-presentation fixes)

| # | Issue | Notes |
|---|-------|-------|
| KI-01 | [126] Narrative Gravity — verbatim extractive summary | Needs API regeneration |
| KI-02 | Chapter cluster scatter: 17 clusters unexplained | Post-presentation |
| KI-03 | Book × Topic heatmap: numeric values unlabelled | Post-presentation |
| KI-04 | Keyphrases: single words not phrases (TF-IDF `min_ngrams` issue) | Post-presentation |
| KI-05 | Entity network: "information and", "cybernetics and" as spurious concepts | Post-presentation |
| KI-06 | Concept density: Frontier band all zero | Post-presentation |
| KI-07 | Cluster composition: shows only 3 | Post-presentation |
| KI-08 | 71 false negative monographs in classifier (recall ceiling) | Classifier track #3 |
| KI-09 | AshbyX/NorbertX `json/` divergence — NorbertX is canonical | Monitor |

### Longer-running backlog

| # | Task | Status |
|---|------|--------|
| 11 | Complete spaCy + Wikidata classification pass (full corpus) | ⏳ Pending |
| 12 | **Paragraph-window edges in entity network.** ~~Currently `para=0`~~ — **paragraph-window edges are now computed and included in the current build** (18 April 2026 rerun: 1,139 para edges alongside 10,362 book-level). Paragraph-window co-occurrence (±5 sentences, weighted by log(1+count)) is a distinct and richer signal from book-level co-occurrence: where book-level tells you two entities inhabit the same intellectual territory, paragraph-level with frequency tells you an author actively brought them into the same argumentative moment. High-frequency paragraph co-occurrence across multiple authors constitutes evidence of an epistemic affordance — a conceptual pairing that the field has found productive. This is also a diagnostic for the event/concept ambiguity: terms like "Cold War" that paragraph-co-occur primarily with institutional entities are functioning as historical context; those that co-occur with technical concepts are functioning as explanatory categories. Level filter already implemented; guide documentation updated with para edge explanation. **Remaining:** analysis of theoretically interesting pairs (see #22). | ✅ Edges computed — analysis pending |
| 13 | Regenerate 17 outstanding book summaries | ⏳ Pending |
| 14 | Weighted second pass (run after full pipeline) | ⏳ Pending |
| 15 | **User correction mechanism for entity network HTML** — entity network is shared publicly; viewers will spot misclassifications. Add in-report UI for users to flag/suggest corrections (e.g. wrong node kind, duplicate node, fragment node). Corrections should be capturable and feedable back into `MANUAL_CORRECTIONS`. **Design must precede implementation.** Key design questions: (a) capture channel — form→email, pre-filled GitHub issue, embedded JSON download, or other? (b) correction schema — node id, current kind, suggested kind, free-text note; (c) review/moderation workflow before corrections are committed to source. Implementation blocked until design is agreed. | ⏳ Design first |
| 16 | **Fig 3 (index.html) — topic filter dropdown uses stale topic names.** Root cause (18 April 2026): `src/patch_topic_names.py` TAXONOMY had 3 April topic names, overwriting `nlp_results.json` on every `run_all.sh`. Additionally `kp_data` in `src/06_build_report.py` omitted `lda_names`, so keyphrases topic filter used `Topic N` placeholders. Fixed 18 April 2026: (a) TAXONOMY in `patch_topic_names.py` updated to 18 April taxonomy; (b) `_LDA_BASE` fallback in `06_build_report.py` updated; (c) `'lda_names': LDA_NAMES` added to `kp_data`; (d) keyphrases filter JS updated to use `KD.lda_names`. HTML regenerated via `patch_topic_names.py` + `06_build_report.py`. Verified. | ✅ Done |
| 17 | **Entity network HTML — provenance notice covers app header.** `position:fixed;top:0` approach does not work with the network viewer's full-viewport flex layout; `body{padding-top:54px}` does not push flex children down. Fixed 18 April 2026: notice changed to `flex-shrink:0` static element injected before `<div class="header">` rather than before `</body>`. Verified. | ✅ Done |
| 18 | **Entity network — min-degree percentile filter broken for p99.** `p99` was a dropdown option but absent from `_deg_percentiles` dict passed to `STATS`. JavaScript `STATS.deg_percentiles?.['p99']` returned `undefined`, fell through to `\|\| 0`, so threshold was 0 (show all). Fixed 18 April 2026: added `'p99': float(_np.percentile(_degs, 99))` to `_deg_percentiles` in `src/14_entity_network.py`. p99 threshold = 114.6 (degree ≥ 115). Verified. | ✅ Done |
| 19 | **Entity network — degree filter not applied to node set; orphans shown at high thresholds.** Two bugs: (a) `filterGraph()` else-branch set `activeNodes = new Set(NODES.map(n=>n.id))` — all nodes — discarding `allowedNodes` entirely, so degree-filtered nodes were never removed from the canvas; (b) even with (a) fixed, nodes whose neighbours all fall below the threshold become orphans with no visible edges, degrading ink-to-signal ratio. Fixed 18 April 2026: (a) else-branch now uses `activeNodes = allowedNodes`; (b) when `degThresh > 0`, orphan nodes (no edges in `activeEdges`) are additionally removed. Reflects genuine hub-and-spoke topology: hubs connect primarily to peripheral nodes. Verified post-rerun 18 April 2026. | ✅ Done |
| 20 | **Entity network — needs explanatory document for colleagues.** Created `data/outputs/book_nlp_entity_network_guide.html` (18 April 2026): plain-language overview + technical appendix covering corpus, entity extraction, PMI×reliability weighting, filter mechanics, hub-and-spoke topology. Linked from network viewer header ("📖 Reader's guide"). Guide updated post-rerun with live network stats (1,620 nodes, 11,501 edges including 1,139 paragraph-window). | ✅ Done |
| 22 | **Research hypothesis: paragraph-level co-occurrence frequency as evidence of epistemic affordance.** *Theoretical proposition:* When an author repeatedly brings two entities into the same paragraph, this reflects an epistemic judgment — a decision that these two things belong together in the same argumentative or explanatory moment. When this pairing recurs at high frequency across multiple authors, it constitutes evidence of a field-level epistemic affordance: a conceptual pairing that the cybernetics tradition has found productive and generative. This is distinct from book-level co-occurrence, which records only that two entities inhabit the same intellectual territory; paragraph-level frequency records that authors actively reasoned with them together. *Assumption:* Paragraph proximity is a proxy for argumentative co-deployment. This assumption holds more strongly in discursive monographs than in technical texts or handbooks — consistent with the corpus construction decision to restrict to monographs and collected works. *Connection to existing theory:* This extends the "structural compression" argument in `docs/memo_media_aware_nlp_epistemic_affordances.md` §15.2, which proposes that the entity network compresses co-occurrence relationships that no individual reader could track. Paragraph-level frequency adds a further compression: not just *that* two things appear together but *how insistently* authors chose to reason with them together. The book medium's argumentative paragraph structure is itself an epistemic affordance that enables this signal — it would not be recoverable from an encyclopedia, database, or journal abstract corpus. *Proposed investigation:* Compare book-level and paragraph-level co-occurrence for a set of theoretically interesting pairs (e.g. feedback/control, Cold War/cybernetics, Wiener/Shannon). Cases where paragraph frequency is disproportionately high relative to book-level co-occurrence are candidates for field-constituting epistemic pairings. Paragraph-window edges are now available in the current build (1,139 edges; see #12). | ⏳ Ready for analysis |
| 21 | **Entity network — add "event" as a new node kind.** Cybernetics conferences, landmark publications, institutional milestones, and other historically significant events appear as index terms and should be classified and visualised as a distinct node kind alongside person, concept, organisation, and location. Design questions: (a) what constitutes an event vs. a concept — "Macy Conferences" is clearly an event; "feedback" is clearly not; but "Cold War" sits ambiguously between event and concept depending on how it is used in a given index (historical context, shaping force, analytical category). The same term may function differently across books, raising the question of whether classification should be per-term or per-occurrence; (b) event extraction — heuristic patterns, NER, manual seeding, or combination; (c) colour in the network palette; (d) whether events participate in PMI co-occurrence edges or require different edge semantics (e.g. temporal proximity). Connects to Phase 2 "Events analysis" item. **Design must precede implementation.** | ⏳ Design first |

| 23 | **Entity misclassification audit tool** *(deferred)* — a periodic diagnostic (not a continuous pipeline step) to flag classification disagreements for human review. Motivation: entity classification (person/concept/org/location) uses four layers (regex, KNOWN_SINGLE_PERSONS, spaCy, Wikidata) plus MANUAL_CORRECTIONS, but residual misclassifications persist. A dedicated checker was considered and deferred 20 April 2026 for the following reasons: (a) **Principle of Context** — any automated checker operating on decontextualised node label strings faces the same fundamental ambiguity the classifier faced; it will flag genuinely ambiguous cases (e.g. "University of California" as publisher vs. institution) that require human judgement regardless; (b) **analytical impact is limited** — node kind affects colour and category counts in the visualisation but does not affect PMI edge weights, concept velocity, topic grounding, or main analytical outputs; (c) **cost-benefit** — the existing four-layer pipeline already handles the most impactful cases; the residual is a long tail of marginal and genuinely ambiguous terms; (d) **better mechanism exists** — ROADMAP #15 (viewer-flagging) surfaces real errors more efficiently because viewers bring the sentence context the algorithm lacks. **When to revisit:** when the corpus exceeds ~2,000 books, a batch Wikidata lookup on new nodes (flagging classification disagreements above a confidence threshold) would be a reasonable periodic maintenance tool. | ⏳ Deferred — revisit at 2k+ books |
| 24 | **Methodological open question: paragraph co-occurrence and the Principle of Context** — The entity network includes paragraph-level edges (±5 sentences, log-weighted by frequency) as a richer signal than book-level co-occurrence (ROADMAP #12, #22). Paragraph proximity is treated as a proxy for argumentative co-deployment. However, the **Principle of Context (incomplete information)** applies at the occurrence level as well as the classification level: the meaning of a specific co-occurrence of two entities within a paragraph may vary substantially depending on argumentative context — the same pairing may indicate synthesis, critique, contrast, or incidental proximity. Aggregating frequency counts across books without distinguishing these relationship types treats all associations as epistemically equivalent, which they are not. PMI and paragraph-frequency counts measure *association*, not *semantic relationship type*. A high paragraph co-occurrence score between (e.g.) Wiener and Shannon could reflect systematic intellectual synthesis, or systematic contrast, or both across different books and authors. **Why this matters for the paper:** results should be framed as patterns of association rather than patterns of intellectual relationship. Claims about epistemic pairings (ROADMAP #22) require this caveat explicitly — high paragraph co-occurrence frequency is evidence that authors brought two entities into the same argumentative moment, but the nature of that moment requires verification against source text. **Proposed investigation:** select a small set of high-frequency paragraph edges and manually examine the source paragraphs to characterise the distribution of relationship types (synthesis, contrast, citation, incidental). This would ground the methodological claim and provide language for the paper's limitations section. Connects to ROADMAP #22 and the Principle of Context in CLAUDE.md. | ⏳ Open — investigate before paper submission |

---

## Phase 1 — Pipeline consolidation (largely complete)

Core pipeline is functional and presentation-ready (book-level LDA). Remaining items are data quality and classifier work.

- [x] Streaming corpus ingestion
- [x] LDA topic model (k=9 canonical, book-level)
- [x] NMF topic model (8 topics, chapter-level)
- [x] Abstractive summaries via API
- [x] Index extraction and canonical vocabulary
- [x] Index grounding (lift scores, density, velocity)
- [x] Time series report with concept velocity (Chart 7)
- [x] Entity relational network (4 node kinds, 4 layouts)
- [x] Entity classification (heuristics + spaCy + Wikidata cache)
- [x] Index canonicalisation (person name merging, accent normalisation)
- [x] Regression test suite (15 tests)
- [x] Book style classification pipeline (`00_*` scripts)
- [x] Monograph binary classifier Phase 1 (logistic regression, 33 features, active learning)
- [ ] Complete spaCy + Wikidata classification pass (full corpus run)
- [ ] Complete paragraph-window edge computation
- [ ] Regenerate 17 outstanding summaries
- [ ] Weighted second pass
- [ ] Signal inventory audit + document unit decision → exclusion filter

---

## Phase 2 — Analysis and interpretation

Moving from pipeline outputs to scholarly analysis. Blocked until moratorium is lifted.

- [ ] **Events analysis** — extract and classify historical events from index terms and text (cybernetics conferences, publications, institutional milestones)
- [ ] **Co-citation network** — who cites whom? Build from bibliography sections rather than indexes
- [ ] **Temporal entity analysis** — how do person and concept networks change across decades?
- [ ] **Cross-corpus comparison** — compare cybernetics corpus with adjacent fields (systems theory, complexity science, AI/ML)
- [ ] **Topic evolution** — track how LDA topic distributions shift 1954→2025
- [ ] **Canonical figures** — rank persons by centrality, temporal span, and cross-topic reach

---

## Phase 3 — Publication

- [ ] **Paper draft** — working title: *Mapping the Cybernetics Intellectual Landscape: A Computational Analysis of 695 Books*
- [ ] **Contributions.md → paper section** — merge evolving authorship statement into manuscript
- [ ] **Zenodo deposit** — archive pipeline with DOI; link from paper
- [ ] **Journal target** — TBD (candidates: *Kybernetes*, *Systems Research and Behavioral Science*, *Digital Humanities Quarterly*)
- [ ] **GitHub release** — tag v1.0 when pipeline is fully validated

---

## Open questions

- Should `book_nlp_entity_network.html` include a "works" node kind for cited books? Currently suppressed.
- Is the Wikidata rate limit (2 req/sec) acceptable for future full re-runs, or should we cache more aggressively?
- Should `test_pipeline.py` be run as a GitHub Action on each push?
- What is the right `n_books` threshold for the canonical vocab? Currently 3. Lower = more terms, more noise.
- Multi-label classifier Phase 2: when will anthology and textbook classes have sufficient expert labels (~20 each)?

---

## Deferred / won't do (for now)

- **Full-text search index** — Calibre already provides this
- **Browser-based Jupyter interface** — out of scope for a pipeline tool
- **GPU-accelerated embeddings** — sentence-transformers works fine on CPU for 695 books
