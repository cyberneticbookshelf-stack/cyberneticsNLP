# Changelog

All notable changes to the CyberneticsNLP pipeline are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Dates are AEST (UTC+11).

---

## [Unreleased]

See `docs/ROADMAP.md` for planned work.

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
