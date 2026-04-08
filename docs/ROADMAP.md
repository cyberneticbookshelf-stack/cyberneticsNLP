# Roadmap

Tracks planned work, open questions, and longer-term directions.
Issues are tracked at: https://github.com/cyberneticbookshelf-stack/cyberneticsNLP/issues

Last updated: 8 April 2026 (v0.4.2)

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
| 12 | Complete paragraph-window edges in entity network | ⏳ Pending |
| 13 | Regenerate 17 outstanding book summaries | ⏳ Pending |
| 14 | Weighted second pass (run after full pipeline) | ⏳ Pending |

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
