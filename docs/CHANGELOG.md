# Changelog

All notable changes to the CyberneticsNLP pipeline are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Dates are AEST (UTC+11).

---

## [0.4.3] — 2026-04-17

> Session: 17 April 2026

### Added
- `src/02_clean_text.py` — 4-signal OCR likelihood scorer producing Low / Medium / High bands. Signals: scanning metadata (+0.55), low alphabetic ratio (+0.25), OCR error patterns (+0.20), page artifacts (+0.10). Scores embedded in `books_clean.json` and propagated to all outputs
- `src/06_build_report.py` — monolithic 15 MB HTML split into 5 focused pages with shared CSS and active-link navigation: `index.html` (topics), `clusters.html`, `cosine.html`, `similarity`), `keyphrases.html`, `books.html`
- `src/09b_build_index_analysis.py` — `is_person_term()` function using `entity_types_cache.json` (NER cache from `15_entity_classify.py`) with `_is_clean_name()` and `_ANCIENT_PERSONS` fallbacks. Propagates `is_person` flag to all vocab and top-200 entries
- `src/10_build_index_report.py` — concepts/persons split throughout index report: frequency, time series, and topic distribution charts each have 📚 Concepts / 👤 Persons toggle; co-occurrence network is concepts-only
- `docs/memo_data_quality_algorithm_infection.md` — methodology memo documenting OCR propagation pathways, digitisation metadata contamination, PMI inflation for small-n entities, and phrase-fragment nodes. Includes worked example (Google–Wiener association) and planned mitigations table

### Fixed
- `src/06_build_report.py` — added `_esc()` (`html.escape()`) to all user-generated text in book cards (titles, authors, summaries, keyphrases, chapter content) — prevents OCR garbage from being parsed as unclosed HTML tags (e.g., book 2109 OCR `<s f Miscellaneous…` was causing strikethrough across entire page)
- `src/06_build_report.py` — fig7 keyphrases PNG now embedded in Section 5; previously replaced with interactive table but PNG was never removed from build and never placed in output
- `src/05_visualize.py` — fig7 replaced broken 542-panel per-book keyphrase grid with 9-panel per-topic summary bar chart
- Cosine similarity heatmap: fixed blank chart (`texttemplate` → `layout.annotations`); added cluster-averaged default view
- Google Books text-layer artefacts (`"Digitized by Google / Original from / UNIVERSITY OF CALIFORNIA"`) now stripped from clean text in OCR pre-processing
- Keyphrase blocklist expanded; verb filtering improved; timeseries explanatory text updated

### Analysis
- Entity network data quality investigation: Google (#4 hub, weighted degree 178.7) and Amazon (#3, 180+) rank above Bateson, Shannon, and von Neumann despite appearing in <12 books. Root cause: PMI inflation — for rare entities with 100% overlap with a common entity, `sqrt(overlap/20)` reliability dampener is insufficient. Not primarily a metadata contamination issue (only 1 confirmed contamination case: book 2761). Amazon, Google, Facebook, National Security Agency, Bell Laboratories, Santa Fe Institute all identified as inflated hubs
- Phrase fragment nodes identified in entity network: "free will and" (degree 47), "ai and" (degree 39), "cybernetics and" (degree 15) — structural mis-parsing of hierarchical index entries in `09_extract_index.py`
- OCR distribution (Run C, 542 books): 148 Low / 322 Medium / 72 High
- Person/concept split (top 200 index terms): 144 concepts, 56 persons

### Design decisions (17 April 2026)
- **Algorithm infection principle** — without a characterised distribution of input errors, every downstream algorithm is subject to infection from those errors. Pipeline outputs must be interpreted against known error distributions (OCR band, entity n_books, phrase-fragment provenance), not as measurements. See `docs/memo_data_quality_algorithm_infection.md`
- **Person/concept separation** — index analysis charts separate person names from concept terms to avoid mixing citation prominence (persons) with conceptual density (concepts) in the same frequency distributions
- **Multi-page HTML** — the monolithic report was split for usability; each page is self-contained with shared CSS and cross-links. All 5 pages written via `json/` staging + `os.replace()` to work around fuse-t file-size limits

### Known issues / planned mitigations (not yet implemented)
- PMI inflation: change reliability term `sqrt(overlap/20)` → `overlap/20`; raise `MIN_BOOKS` from 3 to 5 in `14_entity_network.py`
- Phrase fragment suppression: add filter for terms ending with ` and`, ` or`, ` of` in `09b_build_index_analysis.py`
- Digitisation metadata strip: extend OCR scorer to flag and strip provenance-string injections in `02_clean_text.py`
- Index structure parsing: improve hierarchical sub-entry parsing in `09_extract_index.py`

### GitHub
- Commits: `c814b52` through `90a0d84` (16 commits) + this documentation commit

---

## [0.4.2] — 2026-04-08

> Sessions: 8 April 2026 (Chat)

### Added
- `src/heuristic_features.py` — 10 structural text heuristics extracted from `books_clean.json` clean text for monograph classification. Features: `h_multi_affiliations`, `h_chapter_summaries`, `h_per_chapter_refs`, `h_contributors_section`, `h_edited_by`, `h_essays_front`, `h_cross_chapter_refs`, `h_single_author_bio`, `h_has_exercises`, `h_has_objectives`. Majority-vote agreement: 100% on 14 known books. Run audit: `python3 src/heuristic_features.py`
- `src/train_monograph_classifier.py` — binary logistic regression classifier: monograph vs. not-monograph. Features: 23 metadata + 10 heuristic = 33 total. Training data: 197 expert-labelled books (159 Calibre + 40 from first review round). `class_weight='balanced'`. Decision threshold: 0.4. 5-fold CV: precision=0.89, recall=0.68 (monograph). Outputs: `csv/monograph_predictions.csv`, `csv/monograph_sample_*.csv`

### Fixed
- `src/10_build_index_report.py` — 675 → 695 (stale corpus count)
- `src/11_embedding_comparison.py` — 675 → 695; `_LDA_BASE` updated to 9 agreed k=9 topic names
- `src/06_build_report_chapters.py` — line 27: was overwriting NMF chapter topic names with LDA book-level names; fixed to use NMF names where present, LDA only as fallback. Critical distinction: chapter NMF and book LDA use different methodologies and must not share labels
- `src/08_build_timeseries.py` — `_BASE_CH` updated to 8 named NMF topics; removed stale `'Topic 7'`, `'Topic 8'`, `'Topic 9'` placeholders
- `src/12_index_grounding.py` — `_NMF_BASE` expanded from 6 to 8 names
- `src/14_entity_network.py` — `_LDA_BASE` updated to 9 agreed k=9 topic names
- `json/nlp_results_chapters.json` — `topic_names` written (8 agreed NMF chapter topic names; was None)
- `json/entity_network.json` — rebuilt after `_LDA_BASE` fix; nodes now tagged with correct LDA names
- `json/embedding_results.json` — stale cache deleted and rebuilt with correct topic names
- All remaining `_LDA_BASE` fallback lists updated across the 8 scripts that use them (was 7 old names)

### Analysis
- Monograph binary classifier first run on 529 unlabelled books (threshold=0.4): 433 predicted monograph, 96 predicted not-monograph (of which 71 auto-style monographs — known recall ceiling; 10 anthology, 4 handbook, 2 proceedings, 3 textbook correctly identified)
- Active learning cycle established: first review round complete (Paul reviewed random samples from each class); 40 new expert labels added; classifier retrained with heuristic features; significant recall improvement

### Design decisions (8 April 2026)
- **"Expert labels" not "ground truth"** — publication type labels are expert judgements (Paul Wong). Use "agreement with expert labels" not "accuracy". See `docs/decisions.md`
- **Classifier training data integrity rule** — machine-inferred labels from `00_classify_book_styles.py` must never be used as training data for the supervised classifier. Calibre `custom_column_5` labels are the only legitimate training source
- **Active learning cycle** — random sampling from predicted classes → Paul reviews → new expert labels → retrain. Each iteration uses genuinely new expert labels, not machine output

### Quality review (8 April 2026 — Paul)
- All HTML reports verified clean: no generic Topic 7/8/9 labels, no 675 references, entity network uses correct LDA names
- Book-level LDA analysis confirmed presentation-ready
- Chapter-level analysis: MVP infrastructure — not validated to same standard; presentation will focus on book-level LDA only

### Known issues (post-presentation)
- [126] Narrative Gravity — verbatim descriptive summary (extractive fallback)
- Chapter cluster scatter: 17 clusters unexplained
- Book × Topic heatmap: numeric values unlabelled
- Keyphrases: single words not phrases (TF-IDF `min_ngrams` issue)
- Entity network: "information and", "cybernetics and" as spurious concepts
- Concept density: Frontier band all zero
- Cluster composition: shows only 3
- 71 false negative monographs in classifier (recall ceiling with current features)
- AshbyX/NorbertX `json/` divergence — NorbertX is canonical

### GitHub
- Commits: `post-v0.4.1: report quality fixes, monograph classifier, heuristic features`

---

## [0.4.1] — 2026-04-03

> Sessions: 31 March 2026 (Chat) + 1 April 2026 (Chat) + 2 April 2026 (Chat) + 3 April 2026 (Cowork × 2 + Chat)

### Added (2 April 2026 — Chat)
- `src/00_classify_book_styles.py` — book style classifier (monograph, anthology, textbook, popular, history_bio, handbook, proceedings, reader, report); reads `books_metadata_full.csv`
- `src/00_fetch_worldcat_metadata.py` — WorldCat Open Library metadata fetcher (`--reclassify` flag for pipeline rebuild)
- `src/00_fetch_anu_primo.py` — ANU Primo catalogue fetcher; full run: 726 books, 285 found (39%), 0 errors
- `csv/books_metadata_full.csv` — 726 books, 20 columns including `inclusion_stratum`, `archive_id`, `in_title`, `in_description`, `in_tags`, per-field keyword flags; replaces `books_lang.csv`

### Changed (31 March + 1 April 2026 — Chat)
- `01_parse_books.py` — added `preprocess_raw_text()`: strips control chars, symbol runs (3+ non-alphanumeric), page-number lines, repeated punctuation, all-caps headers
- `02_clean_text.py` — fixed ASCII gate to whitelist accented terms; fixed case normalisation (`CYBERNETics` → `cybernetics`); tightened proper-noun shortcut in `build_english_checker`
- `03_nlp_pipeline.py` — expanded stopword list (+20 academic boilerplate terms); hyphen-joining for compounds (`self-organising` → `selforganising`); added `--min-chars` filter flag
- `09_extract_index.py` — raised `alpha_ratio` threshold 0.45 → 0.60; added `FOREIGN_HEADER_RE`; added `_canonical_term()`

### Changed (2 April 2026 — Chat)
- Book style classifier: OCLC Classify removed (403-blocked); Open Library used instead; Primo `edited_book` mapped to anthology detection; platform contributors (ProQuest, EBSCO etc.) suppressed before contributor-based anthology inference; Wiley removed from publisher rules; `principles_of` confidence lowered

### Changed (3 April 2026 — Chat)
- `src/03_nlp_pipeline.py` — `_alpha_ratio()` patched to skip first 10% of text (front-matter bias fix) and sample 3 evenly-spaced windows from body; canonical k=9 locked with warning comment
- `src/09c_validate_topics.py` — f-string syntax fix (Mean stability line)
- `src/run_all.sh` — steps 14+15 now active; canonical k=9 warning added; enrichment pipeline sequence documented
- `src/00_classify_book_styles.py` — Primo override; final classifier stats: monograph 560, anthology 38, textbook 39, popular 38, history_bio 29, handbook 12, proceedings 6, reader 3, report 1
- `json/book_styles.json` — 4 manual reclassifications (verified=True): [267] proceedings→history_bio, [1195] reader→monograph, [1774] reader→monograph, [1271] handbook→popular
- `json/topic_validation.json` — k=9 restored; 9 topic names written
- `json/topic_stability.json` — k=9 canonical (seeds: 42, 7, 123, 256, 999); 7/9 stable, 0 dead, mean stability=0.382
- `json/nlp_results.json` — k=9 run on 695 books
- `json/entity_network.json` — rebuilt on 695 books: 1,846 nodes, 13,444 edges, 99.8% connected
- `README.md` — updated: 695 books, 3 April 2026, `00_*` scripts documented

### Fixed (3 April 2026 — Cowork)
- **KI-01 resolved**: all 6 known OCR-failure books (IDs: 240, 1262, 1416, 1718, 1727, 1772) reindexed via Calibre; all pass alpha_ratio ≥ 0.60 (0.73–0.80)
- ID 1840 (Cybernation and Social Change) also found stale — fixed in same pass
- 4 previously-unprocessed books cleaned (IDs: 1791, 1794, 1799, 1800)
- All 25 CSV files fully streamed; `books_clean.jsonl` complete at 695 books
- `books_clean.json` **regenerated from scratch**: 695 books, `clean_text` key (was `text`), 169MB (was 758MB). Backup: `books_clean.json.bak3`
- Alpha-ratio front-matter bias fix (3 April Chat) resolved secondary exclusions for IDs 205, 265, 413, 597, 1261, 1918

### Infrastructure
- Full SCOWL en_US-large Hunspell dictionary (76,959 words) installed on AshbyX and NorbertX (⚠️ dictionary inconsistency between machines — monitor for reproducibility)
- Full corpus re-clean: 675 books via `02_clean_text.py`; expanded to 695 books via `parse_and_clean_stream.py` (all CSVs)
- Corpus: 726 books in Calibre; 695 in NLP pipeline (22 excluded by publication type policy; remainder below `--min-chars` threshold)

### Analysis
- LDA coherence sweep (k=2–12) post-data quality overhaul: best k=11 (coherence=0.0887, perplexity=1487.1)
- **k=9 canonical run**: 695 books, `--min-chars 10000 --lemmatize --topics 9 --seeds 5`; 7/9 stable, 0 dead, mean stability=0.382
- k=10 comparison: 6/10 stable — worse than k=9; k=9 confirmed as final solution
- Topic validation (`09c_validate_topics.py --top 10 --md`) completed; 9-topic taxonomy agreed and locked

### Design decisions (3 April 2026)
- **k=9 is canonical** — k=10 tested and rejected; locked in `run_all.sh`
- **Publication type exclusion policy**: proceedings, handbooks, readers excluded from NLP pipeline (monograph assumption violations); 22 books excluded, 704 retained (97%) — not yet implemented in pipeline
- **Ground truth reframed**: not "what type is this book?" but "which pipeline assumptions does this book violate?" Observable binary signals replace categorical labels
- **Moratorium on further NLP code** until signal inventory audit and document unit decision are complete
- **Publication era as structural variable**: type × era interaction determines whether pipeline assumptions hold; born-digital transition is the most consequential boundary for index-term features
- Classifier to be redesigned as **multi-label scorer** — types are not disjoint (Ashby paradigm case); signal inventory is the prerequisite

### Documentation
- `docs/memo_media_aware_nlp_epistemic_affordances.md` — §13–15 added (2 April Chat); §16 (document unit problem, monograph assumption, signal inventory) and §17 (temporal dimension, type × era interaction) added (3 April Chat); now 17 sections
- `docs/memo_attribution_annotations.md` — updated
- `docs/draft_methods_corpus_construction.md` — filed
- `docs/contributions.md` — all sessions through 3 April logged; v0.4.1 sign-off

### Known issues
- KI-04: Amazon/Google/Facebook appear as high-degree nodes in entity network — platform/publisher noise from ebook metadata; fix in `15_entity_classify.py` exclusion list
- KI-05: T9 (Residual/Outlier Cluster) — [249] Reflexion and Control dominates at loading=1.000; document in paper; may resolve at higher k or after exclusion filter implemented
- KI-06: Monograph assumption violations not yet filtered from pipeline — pending signal inventory + document unit decision

### GitHub
- Commit: `post-v0.4.0: epistemic affordances memos, exclusion policy, canonical k=9, steps 14+15 in run_all`
- Repo: https://github.com/cyberneticbookshelf-stack/cyberneticsNLP

---

## [0.4.0] — 2026-03-27

### Added
- `15_entity_classify.py` — three-stage NER pipeline (heuristics → spaCy `en_core_web_sm` → Wikidata REST API). Produces `json/entity_types_cache.json`, cached permanently. Run once before step 14. Flags: `--no-wikidata` (offline), `--refresh` (discard cache)
- `MANUAL_CORRECTIONS` dict in `15_entity_classify.py` — 121 post-audit overrides (e.g. `stelarc` → person, `digital` → concept, `whole earth catalog` → suppress)
- Four graph layout algorithms in `14_entity_network.py` — Force-directed (Fruchterman-Reingold), Radial (d3.forceRadial), Bipartite (fixed columns), Circular (arc segments). Selectable from dropdown in report UI
- Node-kind checkboxes in entity network report (toggle persons/concepts/orgs/locations)
- Network statistics panel in entity network report (degree distribution, APL, diameter, hub nodes)
- Degree percentile filter in entity network report (p75/p90/p95/p99)

### Changed
- `09_extract_index.py` — six new noise filters: extended alpha-header pattern, ebook preamble text, author affiliation strings, function-word sub-entry fragments, roman numeral page numbers, line length threshold 120→100
- `09b_build_index_analysis.py` — three canonicalisation passes: noise suppression, person name merging (262 rules, e.g. `Wiener, N.` → `Wiener, Norbert`), accent normalisation (René/Rene, Schrödinger/Schrodinger)
- Entity classification now reads `entity_types_cache.json` in `14_entity_network.py`; heuristics used as fallback only
- `README.md` — full rewrite: accurate folder structure, correct script order, missing scripts added, all json/ paths updated, authorship block added
- Regression test suite extended to 15 tests (added step 15 with spot-checks)

### Fixed
- Duplicate `data/` block and stray trailing lines in README folder tree
- `summaries.json` incorrectly listed under `data/` (now correctly under `json/`)
- `12_index_grounding.py` listed after `14_entity_network.py` in README (step 12 must precede 14)
- `reports/` stale directory removed from package

### Project
- Added `docs/CHANGELOG.md` (this file)
- Added `docs/ROADMAP.md`
- Added `docs/contributions.md`
- Added `.gitignore` (excludes `csv/`, `json/`, `data/outputs/`, `figures/`)
- Repository: https://github.com/cyberneticbookshelf-stack/cyberneticsNLP
- OneDrive sync established for `csv/`, `json/`, `data/outputs/`, `figures/`

---

## [0.3.0] — 2026-03-24

### Added
- `14_entity_network.py` — person–concept–organisation–location relational network using book-level PMI × reliability edges. Four node kinds with colour coding (person=blue, concept=green, organisation=purple, location=amber)
- `15_entity_classify.py` (initial version) — heuristics-only entity classification
- Entity classification: `KNOWN_TECH_ORGS` curated set (Google, Facebook, IBM, NASA, etc.)
- Entity classification: `BARE_BOOK_TITLES`, `_FUNC_START`, `_ARTICLE_TITLE` suppression patterns
- `check_integrity.py` — session-start integrity checker for 17 scripts
- `test_pipeline.py` — regression test suite (initial: 13 tests)

### Changed
- Node kinds expanded from 2 (person, concept) to 4 (person, concept, organisation, location)
- `09_extract_index.py` — improved noise filters: PREAMBLE_RE, AUTHOR_AFFIL_RE, FUNC_FRAGMENT_RE, extended ALPHA_HEADER, PAGENUM_ONLY with roman numerals

---

## [0.2.0] — 2026-03-21

### Added
- `12_index_grounding.py` — topic labelling via lift scores, concept density scatter, concept velocity across decades
- `08_build_timeseries.py` Chart 7 — band prevalence by decade + concept velocity (requires step 12)
- `09b_build_index_analysis.py` — person name merging (initial 262-rule set), accent normalisation
- `13_weighted_comparison.py` — side-by-side comparison of unweighted vs weighted pipeline runs
- `11_embedding_comparison.py` — LSA vs Sentence Transformers vs Voyage AI comparison
- `build_embed_report.py` — rebuild embedding comparison report from cached results JSON
- `embeddings.py` — embedding provider abstraction module
- `--weighted` flag in `03_nlp_pipeline.py` — index-term lift-weighted TF-IDF
- `--recursive` flag in `generate_summaries_api.py` — map-reduce summarisation

### Changed
- `generate_summaries_api.py` — PLACEHOLDER_RE and REPORT_RE filters to catch low-quality API responses
- Summaries: 675 books processed; 17 requiring regeneration identified and cleaned

---

## [0.1.0] — 2026-03-20

### Added
- Initial pipeline: steps 01–10
- `parse_and_clean_stream.py` — streaming corpus ingestion (no full-corpus load)
- `01_parse_books.py`, `02_clean_text.py` — standard parse/clean path
- `03_nlp_pipeline.py` — LDA topic modelling (7 topics, book-level)
- `03_nlp_pipeline_chapters.py` — NMF topic modelling (6 topics, chapter-level)
- `04_summarize.py` — extractive fallback summaries
- `generate_summaries_api.py` — abstractive summaries via Anthropic API
- `05_visualize.py`, `05_visualize_chapters.py` — matplotlib figures
- `06_build_report.py`, `06_build_report_chapters.py` — interactive HTML reports
- `07_build_excel.py`, `07_build_excel_chapters.py` — Excel workbooks
- `08_build_timeseries.py` — time series report (Charts 1–6)
- `09_extract_index.py` — index term extraction
- `09b_build_index_analysis.py` — index vocabulary builder
- `10_build_index_report.py` — controlled vocabulary report
- `run_all.sh` — end-to-end runner
- Corpus: 675 books, 7,349 chapters, 1954–2025, random seed 99


### Note on canonical topic solution (2026-04-03)
`topic_stability.json` reflects the most recently run k. Canonical solution: **k=9** (validated 3 April 2026). After comparison runs, restore with `python3 src/03_nlp_pipeline.py --min-chars 10000 --lemmatize --topics 9 --seeds 5`
[126] Narrative Gravity — descriptive summary is verbatim extract, needs API regeneration

## [0.4.2] — 2026-04-08

### Fixed
- `src/10_build_index_report.py` — corpus count 675 → 695
- `src/11_embedding_comparison.py` — corpus count 675 → 695
- `src/06_build_report_chapters.py` — line 27 bug fixed (was overwriting NMF chapter names with LDA book names)
- `_LDA_BASE` fallback lists updated in all 8 report scripts (7 old topic names → 9 agreed k=9 names from 3 April)
- `_BASE_CH` in `src/08_build_timeseries.py` — 8 named NMF topics; removed placeholder Topic 7/8/9 labels
- `_NMF_BASE` in `src/12_index_grounding.py` — expanded 6 → 8 topic names
- `json/nlp_results_chapters.json` — `topic_names` field populated (was None)
- `json/embedding_results.json` — stale cache deleted and rebuilt
- All 8 HTML reports verified clean: no generic "Topic N" labels, no 675 references

### Added
- `src/heuristic_features.py` — 10 structural text heuristics for monograph classification; 100% majority-vote agreement on 14 known books
- `src/train_monograph_classifier.py` — logistic regression monograph classifier; 33 features (23 metadata + 10 heuristic); 197 expert labels; threshold=0.4; 5-fold CV: precision=0.89, recall=0.68
- Active learning cycle established: first round of 40 new labels from Paul via `Monograph_Review.xlsx`

### Design decisions (8 April 2026)
- **"Expert labels" not "ground truth"**: labels record which pipeline assumptions a book violates, not objective type
- **"Agreement with expert labels" not "accuracy"**: classifier performance stated relative to expert judgement
- **Classifier training data integrity rule**: machine-inferred labels from `00_classify_book_styles.py` must never be used as training data for `train_monograph_classifier.py` — circuits in active learning cycle

### Documentation
- `docs/decisions.md` — training data integrity rule, terminology substitutions
- `docs/methodology.md` — Phase 1 binary classifier design, active learning protocol
- `docs/contributions.md` — 8 April session logged

---

## [0.4.3] — 2026-04-14

### Added
- `src/03_nlp_pipeline.py` — `--full-text` flag: strips front/back matter, feeds full body text to LDA; `--run-id` flag: appends suffix to all output filenames enabling concurrent runs without collision; `--max-features` default raised to 15,000 for full-text server runs; `--name-topics` flag: Anthropic API integration (claude-sonnet-4-20250514) for automated topic name proposals
- `src/record_topic_run.py` (drafted in `docs/src_draft/`) — snapshots each pipeline run to `json/topic_run_records.json`; supports multi-run topic naming reliability tracking
- `src/compare_topic_runs.py` (drafted in `docs/src_draft/`) — generates HTML comparison report across N runs; book presence matrices, word stability, naming records
- `json/nlp_results_k8.json`, `json/nlp_results_k9.json`, `json/nlp_results_k10.json`, `json/nlp_results_k12.json` — k-sweep comparison runs (pub-type filtered corpus, 542 books)
- `docs/memo_lda_k_selection.md` — k-selection analysis; stability tables for k=8/9/10/12; final topic names and rationale
- `docs/consolidation_14apr2026.md` — master reference: canonical facts, all four topic runs, slide deck and PDF discrepancy tables, pending tasks

### Changed
- **Canonical corpus for LDA: 542 books** (pub-type filter: monographs + collected works only; confirmed 14 April 2026)
- **Canonical k=9 run: `json/nlp_results_k9.json`** (Run C: 542 books, `--seeds 5 --lemmatize --full-text --max-features 15000 --run-id k9`) — supersedes 3 April sampled run
- `json/nlp_results.json` — now holds Run B (Session 1 full-text, ~690 books, no pub-type filter); Run A (3 April sampled) overwritten
- `docs/draft_methods_corpus_construction.md` — §3.8 added: LDA preprocessing, k-selection methodology, fiction outlier note, final topic structure table
- `README.md` — updated to v0.4.3: 695/542 corpus counts, new scripts, Run C topic names

### Design decisions (14 April 2026)
- **Run C is canonical for v0.4.3** (not Run B): v0.4.3 is defined by the pub-type filter (542 books); Run C was run with this filter, `--seeds 5`, and `--lemmatize`, making it reproducible. Confirmed by Paul Wong.
- **k=9 recommended** over k=8/10/12: best balance of perplexity (3413.6), stability (mean=0.327, 5/9 stable), and interpretability; T9 highest-stability topic (0.622) across all k
- **Topic names provisional**: agreed by title-sweep (top-loading books inspection), not word-level inspection alone; subject to multi-run validation via run-records system and independent rater review before use in paper
- **T1 (History and Biography of Cybernetics) low stability (0.131)**: attributed to Lem/Čapek science fiction outliers at top of loading list; cluster intellectually coherent beneath them; name retained with caveat

### New canonical 9-topic taxonomy (Run C, 542 books)
| # | Name | Stability |
|---|------|-----------|
| T1 | History and Biography of Cybernetics | 0.131 |
| T2 | Cybernetics of Psychology | 0.559 |
| T3 | Extensions of Cybernetics | 0.153 |
| T4 | Cybernetic Management Theory | 0.349 |
| T5 | Biological Systems Cybernetics | 0.224 |
| T6 | Formal Foundations of Cybernetics | 0.289 |
| T7 | Cross-Domain Applications of Cybernetics | 0.306 |
| T8 | Cybernetics of Posthumanism | 0.306 |
| T9 | Cultural Applications of Cybernetics | 0.622 |

### Documentation
- `docs/decisions.md` — corpus-scale epistemic access framing; run-id rationale; canonical run decision
- `docs/methodology.md` — corpus-scale epistemic access; index compilation caveat; compression trade-offs
- `docs/memo_lda_k_selection.md` — filed
- `docs/consolidation_14apr2026.md` — filed
- `docs/contributions.md` — 14 April sessions to be logged (see below)

### Known issues
- KI-04: Amazon/Google/Facebook entity noise — unresolved (post-presentation)
- KI-05: T9 residual cluster (3 April run) — superseded by Run C taxonomy
- T1 Lem/Čapek fiction outliers — documented; cluster coherent below top 3 books

---
