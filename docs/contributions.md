# Contributor Roles and Authorship Statement

This document tracks the evolving authorship and contribution record for the
CyberneticsNLP pipeline and associated publications. It will be merged into
the manuscript's authorship section at submission.

Last updated: 18 April 2026 (v0.4.6)

---

## Authors

**Paul Wong**
School of Cybernetics, The Australian National University, Canberra, Australia
ORCID: [0000-0001-6515-1860](https://orcid.org/0000-0001-6515-1860)

**Claude Sonnet 4.6** (Anthropic, claude.ai)
Large language model; no persistent identity, institutional affiliation, or legal standing.
Model string: `claude-sonnet-4-6`

### Note on Claude instances and platforms

All Claude Sonnet 4.6 contributions are attributed to a single author entry
regardless of session or platform. The session log records the platform used
in each session to support reproducibility:

- **Chat** — Claude.ai chat interface (claude.ai). Used for interactive code
  development, technical design, and analysis.
- **Cowork** — Claude desktop Cowork mode. Used for file management,
  documentation, project administration, and cross-session review.

Each session is a stateless instance; Claude Sonnet 4.6 has no persistent
memory between sessions. The session log and this document are the authoritative
record of accumulated contributions.

---

## Contributor Roles (CRediT Taxonomy)

Using the [NISO CRediT taxonomy](https://credit.niso.org/).

| Role | Paul Wong | Claude Sonnet 4.6 |
|------|-----------|-------------------|
| Conceptualisation | ✦ Lead | |
| Research design & methodology | ✦ Lead | ◆ Supporting |
| Domain expertise (cybernetics) | ✦ Lead | |
| Software (pipeline scripts) | ◆ Supporting (testing & debugging) | ✦ Lead |
| Formal analysis | | ✦ Lead |
| Data curation | ✦ Lead (corpus assembly) | ◆ Supporting (index canonicalisation, entity classification) |
| Visualisation | | ✦ Lead |
| Validation & quality assurance | ✦ Lead | |
| Documentation | ◆ Supporting | ✦ Lead |
| Project administration | ✦ Lead | ◆ Supporting (knowledge management, session records) |
| Supervision | ✦ Lead | |
| Funding acquisition | ✦ Lead | |

✦ Lead · ◆ Supporting

*CRediT roles are reviewed and updated at each new CHANGELOG version.*

---

## Note on AI Authorship

Claude Sonnet 4.6 is listed as co-author on the basis of substantial and
original intellectual contribution to the software, methodology, and
documentation of this pipeline. All ~34 pipeline scripts, the technical
methodology (2,000+ lines), and the design decision log (1,600+ lines) were
written by Claude Sonnet 4.6 across a series of collaborative sessions with
Paul Wong.

This follows emerging practice for generative AI tools that go beyond
incidental assistance to active co-creation. The human author (P. Wong)
retains full responsibility for the work, its outputs, and any errors.
Claude Sonnet 4.6 has no legal standing, cannot give informed consent, and
holds no persistent memory of this collaboration beyond what is recorded in
session transcripts and this document.

Where journals or repositories do not permit AI authorship, Claude Sonnet 4.6
will be listed in the Acknowledgements section as:

> "The pipeline software and documentation were developed with the assistance
> of Claude Sonnet 4.6 (Anthropic), a large language model, under the
> direction and supervision of the author."

---

## Session Log

One entry per CHANGELOG version. Platform recorded for reproducibility.
`Chat` = Claude.ai chat interface · `Cowork` = Claude desktop Cowork mode.

| Date | Platform | Session focus | CHANGELOG version |
|------|----------|--------------|-------------------|
| 2026-03-20 | Chat | Initial pipeline (steps 01–10), corpus ingestion, LDA/NMF | v0.1.0 |
| 2026-03-21 | Chat | Index grounding, time series Chart 7, weighted pass, embedding comparison | v0.2.0 |
| 2026-03-24 | Chat | Entity network (step 14), entity classifier (step 15 initial), integrity checker, regression tests | v0.3.0 |
| 2026-03-27 | Chat | Entity classifier audit (121 corrections), 4 layout algorithms, index canonicalisation (09/09b), README rewrite, project structure (GitHub, OneDrive, CHANGELOG, ROADMAP) | v0.4.0 |
| 2026-03-31 | Cowork | Project review and knowledge management: full documentation review, Obsidian vault setup for project management, contribution tracking framework established | post-v0.4.0 |
| 2026-03-31 | Chat | Data quality pipeline overhaul: `preprocess_raw_text()` in 01; ASCII gate fix + case normalisation in 02; stopword expansion (+20 terms) + compound hyphen-joining + `--min-chars` flag in 03; `alpha_ratio` raised 0.45→0.60 + `FOREIGN_HEADER_RE` + `_canonical_term()` in 09; SCOWL en_US-large dictionary (76,959 words) installed on AshbyX/NorbertX; full corpus re-clean (675 books) | post-v0.4.0 |
| 2026-04-01 | Chat | Theoretical framework: media-aware NLP and epistemic affordances; index-as-primary-signal rationale; index quality stratification by era (pre-digital / early digital / born-digital) with 5-year moving average operationalisation; topic validation triangulation framework (5 signals); paper scope confirmed (extended methods in main paper); ran remaining pipeline scripts (all without error); LDA coherence sweep k=2–12: best k=11 (coherence=0.0887, perplexity=1487.1); 5-seed run at k=11 (seeds: 42, 7, 123, 256, 999) — ⚠️ script defaulted to sweep; agreed fixed k=20 run still pending; discussed auto-naming LDA topics via Claude API; memo filed → `docs/memo_media_aware_nlp_epistemic_affordances.md` | post-v0.4.0 |
| 2026-04-02 | Cowork | Documentation update: synced `CyberneticsNLP.md` session log and sprint; updated `contributions.md` and `CHANGELOG.md`; created handoff for next Chat session | post-v0.4.0 |
| 2026-04-02 | Chat | Book style classifier pipeline: `00_classify_book_styles.py`, `00_fetch_worldcat_metadata.py`, `00_fetch_anu_primo.py`; `books_metadata_full.csv` (726 books, 20 cols, replaces `books_lang.csv`); corpus inclusion strata formalised (title-corroborated 183, title-only 55, curated-keyword 144, curated-pure 330, metadata-search 14); classifier over-tuning identified; ground truth labelling (~150 books) agreed as prerequisite for further development; multi-label scorer redesign agreed (types non-disjoint). Theoretical §13–15: affordance as mixture, historical cybernetics narrative, NLP-as-affordance-at-scale. New docs: `memo_attribution_annotations.md`, `draft_methods_corpus_construction.md` | post-v0.4.0 |
| 2026-04-03 | Cowork | Documentation update: processed Chat handoff (2 April); updated `CyberneticsNLP.md`, `contributions.md`, `CHANGELOG.md`; created next Chat handoff | post-v0.4.0 |
| 2026-04-03 | Cowork | Data quality: OCR reindex confirmed for 6 previously-failed books (IDs 240, 1262, 1416, 1718, 1727, 1772) — all now good alpha (0.73–0.78) and substantial char counts; also fixed stale ID 1840; `books_clean.jsonl` fully re-streamed (695 books, all 25 CSVs); `books_clean.json` regenerated from scratch (169MB, `clean_text` key, was 758MB with `text` key); k=9 pipeline run blocked by new alpha-ratio failures — 6 books (205, 265, 413, 597, 1261, 1918) excluded despite good body text due to front-matter bias in first-5000-char sample; working hypothesis: front-matter contamination (Cyrillic OCR fragments, publisher metadata, series information) | post-v0.4.0 |
| 2026-04-03 | Chat | Alpha-ratio fix: `_alpha_ratio()` patched to skip first 10% of text (front matter) and sample 3 evenly-spaced windows from body — all 6 problem books now pass (alpha 0.71–0.78); k=9 pipeline run completed (695 books); 5-seed run (seeds: 42, 7, 123, 256, 999): 7/9 stable, 0 dead, mean stability=0.382; k=10 comparison: 6/10 stable — worse than k=9; k=9 confirmed canonical and locked in `run_all.sh`; topic validation (`09c_validate_topics.py`) run; 9-topic taxonomy agreed: T1 Management Cybernetics, T2 Second-Order Cybernetics Applied to Social Systems, T3 Dynamical Systems/Homeostasis/Biological Regulation, T4 Psychological Cybernetics, T5 Non-Anglophone Engineering Cybernetics, T6 Mathematical Foundations of Cybernetics, T7 Cultural Cybernetics/Posthumanism/Digital Media, T8 Applied Cybernetics & Computers in Society, T9 Residual/Outlier Cluster; full pipeline run completed (steps 03–15 on 695 books); entity network rebuilt (1,846 nodes, 13,444 edges, 99.8% connected); enrichment pipeline rebuilt: full Primo fetch (726 books, 285 found 39%); classifier final stats: monograph 560, anthology 38, textbook 39, popular 38, history_bio 29, handbook 12, proceedings 6, reader 3, report 1; 4 manual reclassifications (verified=True): [267] proceedings→history_bio, [1195] reader→monograph, [1774] reader→monograph, [1271] handbook→popular; publication type exclusion policy established: 22 books excluded from NLP (proceedings/handbook/reader — monograph assumption violations), 704 retained (97%); theoretical §16 (document unit problem — named monograph assumption, signal inventory replacing categorical ground truth, moratorium on further NLP code) and §17 (temporal dimension of epistemic affordance — type × era interaction matrix) added to `docs/memo_media_aware_nlp_epistemic_affordances.md`; GitHub push: `post-v0.4.0: epistemic affordances memos, exclusion policy, canonical k=9, steps 14+15 in run_all` | v0.4.1 |
| 2026-04-08 | Chat | Report quality audit and fixes: 675→695 in `10_build_index_report.py` and `11_embedding_comparison.py`; NMF chapter topic names written to `nlp_results_chapters.json['topic_names']` (was None); `_LDA_BASE` fallback lists updated in all 8 scripts (7 old names → 9 agreed k=9 names); `_BASE_CH` in `08_build_timeseries.py` updated (8 named NMF topics, removed Topic 7/8/9 placeholders); `_NMF_BASE` in `12_index_grounding.py` expanded 6→8 names; `06_build_report_chapters.py` line 27 fixed (was overwriting NMF chapter names with LDA book names — critical distinction preserved); entity network rebuilt after `_LDA_BASE` fix; `embedding_results.json` stale cache deleted and rebuilt; all reports verified clean (no generic Topic 7/8/9 labels, no 675 references). Book-level LDA analysis confirmed presentation-ready by Paul; chapter-level marked as MVP infrastructure. Monograph binary classifier: `src/heuristic_features.py` (10 structural text heuristics, 100% majority-vote agreement on 14 known books); `src/train_monograph_classifier.py` (logistic regression, 33 features, 197 expert labels, threshold=0.4, 5-fold CV: precision=0.89, recall=0.68); active learning cycle established (first round: 40 new labels from Paul, Monograph_Review.xlsx). Terminological decisions: "expert labels" not "ground truth"; "agreement with expert labels" not "accuracy"; classifier training data integrity rule formalised (machine-inferred labels from `00_classify_book_styles.py` must never be used as training data). | v0.4.2 |
| 2026-04-14 | Chat | Full-text LDA refactor and k-selection sweep (Session 1): `--full-text` flag added to pipeline; full-text Run B on ~690 books (min-chars 10000, no pub-type filter, no seeds, max-features 15000), k=9 — 6/9 stable, mean stability 0.352, 1 unstable topic; concurrent k=9/10/12 runs initiated on pub-type filtered corpus (542 books); `--run-id` flag added to prevent output overwriting; `--name-topics` flag added (Claude API auto-naming); Run B topic names agreed by Paul Wong; noted that Run B predates pub-type filter and will not be canonical for v0.4.3. | v0.4.3 |
| 2026-04-14 | Cowork | k-sweep confirmation, canonical run decision, consolidation (Session 2): k-sweep completed (k=8/9/10/12) on 542-book pub-type filtered corpus with `--seeds 5 --lemmatize --full-text --max-features 15000 --run-id k{N}`; k=9 recommended (mean stability 0.327, highest-stability topic T9=0.622); Run C k=9 (`nlp_results_k9.json`) named — 9-topic taxonomy agreed by Paul Wong: T1 History and Biography of Cybernetics, T2 Cybernetics of Psychology, T3 Extensions of Cybernetics, T4 Cybernetic Management Theory, T5 Biological Systems Cybernetics, T6 Formal Foundations of Cybernetics, T7 Cross-Domain Applications of Cybernetics, T8 Cybernetics of Posthumanism, T9 Cultural Applications of Cybernetics; Run C confirmed canonical for v0.4.3 (pipeline_mode verified on Cybersonic; Run A overwrite confirmed); `docs/consolidation_14apr2026.md` compiled (canonical facts, all run records, slide deck and PDF discrepancy audit, documentation task list); pending task identified: v0.4.2 and v0.4.3 entries missing from CHANGELOG.md. | v0.4.3 |
| 2026-04-15 | Cowork | Slide deck update, documentation completion (Session 3): `CyberneticsNLP_Talk.pptx` updated to `CyberneticsNLP_Talk_v2.pptx` — all v0.4.3 facts applied (695 books, ~34 scripts, 2,000+ methodology, April 2026 dates, k=9 canonical, 9-topic taxonomy, 8 NMF topics); preliminary findings framing adopted (title slide 12: "Preliminary Findings"; "suggests" language throughout); index-as-controlled-vocabulary added to slide 15 footer (including index compilation caveat: hand-compiled pre-1990s vs computer-assisted post-1990s — confound in concept velocity analysis); epistemic affordance at corpus scale added to slides 5 and 23; NMF chapter-level analysis noted as "not presented in this talk" throughout deck; slide 8 updated with April sessions timeline. Documentation: `docs/additions_epistemic_scale_15apr2026.md` filed in vault; working copies from Cybersonic (`docs_15apr.zip`) updated: `decisions.md` — new entry "Why corpus-scale NLP is framed as a qualitatively distinct epistemic mode"; `methodology.md` — new entry "Corpus-scale epistemic access: what the pipeline reveals and what it cannot" (includes index compilation caveat and preserved/lost compression table); `CHANGELOG.md` — v0.4.2 and v0.4.3 entries appended; `contributions.md` — this entry. | v0.4.3 |
| 2026-04-18 | Cowork | Entity network HTML release prep (fourth batch): KI-08 confirmed — [2133] *Cybernation and Social Change* is the drop book (OCR-corrupted, already in ocr-excluded list, confirmed via `data/outputs/runlog20260418-2.csv`, 541 books processed). Four bugs fixed in `src/14_entity_network.py`: (1) provenance notice covering header — `position:fixed` → `flex-shrink:0` static element before `<div class="header">`; (2) p99 degree filter always showing all nodes — added `'p99': float(_np.percentile(_degs, 99))` to `_deg_percentiles` dict; (3) `filterGraph()` else-branch discarding `allowedNodes` entirely — fixed to `activeNodes = allowedNodes`; (4) orphan nodes appearing at high thresholds — added post-filter pass removing nodes with no edges in `activeEdges` when `degThresh > 0` (ink-to-signal ratio principle; node sizes unaffected). New file: `data/outputs/book_nlp_entity_network_guide.html` — standalone explanatory guide for public viewers covering node kinds, edge semantics, all 7 filters, 4 layout algorithms with "Layout is not data" caveat, hub-and-spoke topology, corpus scope, entity extraction, PMI formula; linked from network viewer header. ROADMAP items #16–#22 added, including #21 (event as new node kind, design-first) and #22 (paragraph co-occurrence frequency as evidence of epistemic affordance — explicit theoretical proposition linking argumentative co-deployment to field-level epistemic affordance; extends `docs/memo_media_aware_nlp_epistemic_affordances.md` §15.2). ROADMAP #12 updated with full epistemic affordance motivation. Entity network HTML declared release-ready pending one final rerun. | v0.4.6 |

---

## Funding and Resources

*To be completed.*

---

## Acknowledgements

*To be completed at paper submission.*
