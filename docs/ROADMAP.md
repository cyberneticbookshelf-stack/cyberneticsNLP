# Roadmap

Tracks planned work, open questions, and longer-term directions.
Issues are tracked at: https://github.com/cyberneticbookshelf-stack/cyberneticsNLP/issues

---

## Current sprint

| # | Task | Status |
|---|------|--------|
| 1 | Regenerate 17 missing/bad summaries | ⏳ Pending — cleaned `summaries.json` ready |
| 2 | Run spaCy + Wikidata pass on entity cache | ⏳ Pending — needs `pip install spacy` on corpus machine |
| 3 | Run paragraph-window edges in entity network | ⏳ Pending — `python3 src/14_entity_network.py` (~5 min) |
| 4 | Push initial commit to GitHub | ⏳ Pending |
| 5 | Confirm OneDrive sync working across all machines | ⏳ Pending |

---

## Phase 1 — Pipeline consolidation (in progress)

Core pipeline is functional. Focus is on data quality and reproducibility.

- [x] Streaming corpus ingestion
- [x] LDA topic model (7 topics, book-level)
- [x] NMF topic model (6 topics, chapter-level)
- [x] Abstractive summaries via API
- [x] Index extraction and canonical vocabulary
- [x] Index grounding (lift scores, density, velocity)
- [x] Time series report with concept velocity (Chart 7)
- [x] Entity relational network (4 node kinds, 4 layouts)
- [x] Entity classification (heuristics + spaCy + Wikidata)
- [x] Index canonicalisation (person name merging, accent normalisation)
- [x] Regression test suite (15 tests)
- [ ] Complete spaCy + Wikidata classification pass
- [ ] Complete paragraph-window edge computation
- [ ] Regenerate 17 outstanding summaries
- [ ] Weighted second pass (run after full pipeline complete)

---

## Phase 2 — Analysis and interpretation

Moving from pipeline outputs to scholarly analysis.

- [ ] **Events analysis** — extract and classify historical events from index terms and text (cybernetics conferences, publications, institutional milestones)
- [ ] **Co-citation network** — who cites whom? Build from bibliography sections rather than indexes
- [ ] **Temporal entity analysis** — how do person and concept networks change across decades?
- [ ] **Cross-corpus comparison** — compare cybernetics corpus with adjacent fields (systems theory, complexity science, AI/ML)
- [ ] **Topic evolution** — track how LDA topic distributions shift 1954→2025
- [ ] **Canonical figures** — rank persons by centrality, temporal span, and cross-topic reach

---

## Phase 3 — Publication

- [ ] **Paper draft** — working title: *Mapping the Cybernetics Intellectual Landscape: A Computational Analysis of 675 Books*
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

---

## Deferred / won't do (for now)

- **Full-text search index** — Calibre already provides this
- **Browser-based Jupyter interface** — out of scope for a pipeline tool
- **GPU-accelerated embeddings** — sentence-transformers works fine on CPU for 675 books
