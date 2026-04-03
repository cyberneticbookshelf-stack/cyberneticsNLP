# Changelog

All notable changes to the CyberneticsNLP pipeline are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Dates are AEST (UTC+11).

---

## [Unreleased] — post-v0.4.0 (targeting v0.4.1)

> Sessions: 31 March 2026 (Chat) + 1 April 2026 (Chat) + 2 April 2026 (Chat) + 3 April 2026 (Cowork)
> Status: awaiting k=9 pipeline run, topic validation, and contributions.md sign-off before version bump

### Added (2 April 2026 — Chat)
- `src/00_classify_book_styles.py` — book style classifier (monograph, anthology, textbook, popular, history_bio, handbook, proceedings, reader, report); reads `books_metadata_full.csv`
- `src/00_fetch_worldcat_metadata.py` — WorldCat Open Library metadata fetcher (`--reclassify` flag for pipeline rebuild)
- `src/00_fetch_anu_primo.py` — ANU Primo catalogue fetcher (726 books, ~12 min full run; 10-book test only so far)
- `csv/books_metadata_full.csv` — 726 books, 20 columns including `inclusion_stratum`, `archive_id`, `in_title`, `in_description`, `in_tags`, per-field keyword flags; replaces `books_lang.csv`

### Changed (2 April 2026 — Chat)
- `03_nlp_pipeline.py` — target topic count updated: k=9 selected for next run (from coherence-sweep best k=11 vs legacy k=7)
- Book style classifier: OCLC Classify removed (403-blocked); Open Library used instead; Primo `edited_book` mapped to anthology detection; platform contributors (ProQuest, EBSCO etc.) suppressed before contributor-based anthology inference; Wiley removed from publisher rules; `principles_of` confidence lowered — textbook count still pending confirmation after full rebuild

### Changed (31 March + 1 April 2026 — Chat)
- `01_parse_books.py` — added `preprocess_raw_text()`: strips control chars, symbol runs (3+ non-alphanumeric), page-number lines, repeated punctuation, all-caps headers
- `02_clean_text.py` — fixed ASCII gate to whitelist accented terms; fixed case normalisation (`CYBERNETics` → `cybernetics`); tightened proper-noun shortcut in `build_english_checker`
- `03_nlp_pipeline.py` — expanded stopword list (+20 academic boilerplate terms); hyphen-joining for compounds (`self-organising` → `selforganising`); added `--min-chars` filter flag
- `09_extract_index.py` — raised `alpha_ratio` threshold 0.45 → 0.60; added `FOREIGN_HEADER_RE`; added `_canonical_term()`

### Infrastructure
- Full SCOWL en_US-large Hunspell dictionary (76,959 words) installed on AshbyX and NorbertX (⚠️ dictionary inconsistency between machines noted — monitor for reproducibility)
- Full corpus re-clean completed: 675 books via `02_clean_text.py`
- Corpus expanded: 675 → 726 books in Calibre; inclusion strata documented in `books_metadata_full.csv`

### Analysis
- LDA coherence sweep (k=2–12) post-data quality overhaul: best k=11 (coherence=0.0887, perplexity=1487.1); 5-seed run at k=11 completed (seeds: 42, 7, 123, 256, 999)
- ⚠️ **k=9 pipeline run pending**: `python src/03_nlp_pipeline.py --min-chars 10000 --lemmatize --topics 9 --seeds 5`
- ⚠️ **Topic validation pending**: `python src/09c_validate_topics.py --top 10 --md`
- Current classifier state (partial rebuild, before full Primo fetch): monograph 475 (65.4%), anthology 88 (12.1%), textbook 59 (8.1%), popular 47 (6.5%), history_bio 27 (3.7%), handbook 13, proceedings 11, reader 5, report 2

### Design decisions (2 April 2026)
- Classifier to be redesigned as **multi-label scorer** — book types are not disjoint (Ashby's *Introduction to Cybernetics* is simultaneously monograph and textbook)
- **Ground truth labelling (~150 books) is the prerequisite** for any further rule tuning — over-tuning risk identified (adding rules without held-out test set is methodologically equivalent to supervised learning without validation)
- Corpus inclusion strata formalised: title-corroborated (183), title-only (55), curated-keyword (144), curated-pure (330), metadata-search (14)

### Planned (agreed in Chat, not yet implemented)
- Auto-populate LDA topic names via Claude API from top words + high-loading titles
- Full Primo fetch (`python src/00_fetch_anu_primo.py`, ~12 min) → full classifier rebuild sequence

### Documentation
- `docs/memo_media_aware_nlp_epistemic_affordances.md` — updated: §13 (affordance as mixture), §14 (historical cybernetics narrative), §15 (NLP-as-affordance-at-scale); now 15 sections
- `docs/memo_attribution_annotations.md` — new: attribution of ideas by section (PW/CS/Joint); AI-human collaboration pattern documented
- `docs/draft_methods_corpus_construction.md` — new: draft methods §3.1–3.7 covering corpus overview, precision-recall trade-off, inclusion strata, cybernetics' recall problem, stratum as analytical covariate

### Fixed (3 April 2026 — Cowork)
- **KI-01 partially resolved**: 6 known OCR-failure books (IDs: 240, 1262, 1416, 1718, 1727, 1772) successfully reindexed via Calibre and re-cleaned via `parse_and_clean_stream.py`. All 6 pass alpha_ratio ≥ 0.60 in jsonl:
  - 240 Sociocybernetics: alpha=0.748, 278,587 chars
  - 1262 Ecological Communication (Luhmann): alpha=0.799, 252,666 chars ← previously below threshold
  - 1416 Information, Mechanism and Meaning: alpha=0.788, 235,675 chars
  - 1718 Cybernetic Engineering: alpha=0.747, 123,402 chars
  - 1727 The Foundations of Cybernetics: alpha=0.769, 294,871 chars
  - 1772 Progress in Biocybernetics Vol.1: alpha=0.736, 227,008 chars
- ID 1840 (Cybernation and Social Change) also found to be stale — fixed in same pass
- 4 additional previously-unprocessed books also cleaned (IDs: 1791, 1794, 1799, 1800) — from books_text_21.csv
- All remaining CSV files streamed; `books_clean.jsonl` now complete at 695 books
- `books_clean.json` **regenerated from scratch** from `books_clean.jsonl`: 695 books, `clean_text` key (was `text`), 169MB (was 758MB). Old file backed up as `books_clean.json.bak3`
- ⚠️ **KI-01 not fully resolved**: step 03 run revealed 6 further alpha-ratio failures (IDs: 205, 265, 413, 597, 1261, 1918) — all show good alpha in jsonl (0.71–0.80) suggesting either additional OCR issues in source or OneDrive sync lag. Under investigation in Chat.

### Known issues (carried forward)
- ⚠️ IDs 205, 265, 413, 597, 1261, 1918: pipeline reports alpha < 0.40 despite good values in jsonl — sync/OCR investigation pending (Chat)
- Current NLP run uses `--min-chars 10000`; full k=9 run on updated corpus pending

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
