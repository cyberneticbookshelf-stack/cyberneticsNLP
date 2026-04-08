# Changelog

All notable changes to the CyberneticsNLP pipeline are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Dates are AEST (UTC+11).

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
