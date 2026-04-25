# Book Corpus NLP Analysis Pipeline

**Authors**

Paul Wong¹ · ORCID [0000-0001-6515-1860](https://orcid.org/0000-0001-6515-1860)
Claude Sonnet 4.6 (Anthropic, claude.ai)²

¹ School of Cybernetics, The Australian National University, Canberra, Australia
² Large language model; no persistent identity, affiliation, or legal standing

---

## Contributor Roles

Full CRediT taxonomy statement, session log, and note on AI authorship:
→ [`docs/contributions.md`](docs/contributions.md)

---

A reproducible NLP pipeline for topic modelling, clustering, keyphrase
extraction, summarisation, controlled vocabulary analysis, and visualisation
applied to a cybernetics book corpus extracted from a Calibre library.

**Corpus:** 695 books in collection (1954–2025) · 541 monographs and collected works analysed

---

## Folder Structure

```
CyberneticsNLP/
├── csv/                        ← Place Calibre CSV exports here (NLP machine local)
│   ├── books_metadata_full.csv ← Calibre metadata, 20 cols incl. inclusion_stratum (tab-separated)
│   └── books_text_*.csv        ← OCR text (25 files)
│
├── json/                       ← All JSON/JSONL outputs (auto-created, NLP machine local)
│   ├── books_clean.json        ← cleaned text corpus (written by 02/stream)
│   ├── nlp_results.json        ← current canonical run (written by 03; overwritten on each run)
│   ├── nlp_results_k{N}.json  ← k-sweep runs (k=9 canonical; others retained for comparison)
│   ├── summaries.json          ← abstractive summaries (written by generate_summaries_api)
│   ├── index_terms.json        ← raw per-book index terms (written by 09)
│   ├── index_vocab.json        ← raw vocabulary (written by 09)
│   ├── index_analysis.json     ← canonical index vocab (written by 09b)
│   ├── index_snippets.json     ← term context sentences (written by 09b)
│   ├── topic_index_grounding.json  ← lift scores by topic (written by 12)
│   ├── concept_density.json    ← concept density scatter data (written by 12)
│   ├── concept_velocity.json   ← term migration across decades (written by 12)
│   ├── entity_types_cache.json ← NER classification cache (written by 15)
│   ├── entity_network.json     ← entity relational network (written by 14)
│   └── ...                     ← other pipeline intermediates
│
├── data/
│   ├── pipeline.db             ← Pipeline SQLite database (8 tables: runs, equivalence classes,
│   │                              runlog ingestion, survey generation, response collection)
│   │                              Replaces data/topic_naming.db (3 tables); shared via pipeline_db.py
│   └── outputs/                ← Generated HTML reports and Excel files (NLP machine local)
│       │
│       │   ── Book-level (main analysis — split) ──
│       ├── index.html                      ← main report (Fig 1–6, topic proportions)
│       ├── clusters.html                   ← cluster composition
│       ├── keyphrases.html                 ← keyphrase analysis
│       ├── cosine.html                     ← cosine similarity
│       ├── book_nlp_entity_network.html    ← entity relational network
│       ├── books.html                      ← per-book summaries (excluded from release —
│       │                                      60k token sampling; see notes)
│       │
│       │   ── Book-level (other reports) ──
│       ├── book_nlp_timeseries.html
│       ├── book_nlp_index_analysis.html
│       ├── book_nlp_index_grounding.html
│       ├── book_nlp_embedding_comparison.html
│       ├── book_nlp_weighted_comparison.html
│       │
│       │   ── Chapter-level (not yet refactored) ──
│       ├── book_nlp_analysis_chapters.html
│       │
│       │   ── Excel ──
│       ├── book_nlp_results.xlsx
│       └── book_nlp_chapters.xlsx
│
├── figures/                    ← matplotlib figures (auto-created, NLP machine local)
│
├── src/                        ← Pipeline scripts (tracked in git)
│   ├── parse_and_clean_stream.py   Step 0s: streaming clean (large corpora)
│   ├── 01_parse_books.py           Step 1:  parse CSV → json/books_parsed.json
│   ├── 02_clean_text.py            Step 2:  Hunspell clean → json/books_clean.json
│   ├── 03_nlp_pipeline.py          Step 3:  LDA topics (book-level)
│   ├── generate_summaries_api.py   Step 3b: abstractive summaries via API
│   ├── 04_summarize.py             Step 4:  extractive fallback summaries
│   ├── 03_nlp_pipeline_chapters.py Step 3c: NMF topics (chapter-level)
│   ├── 05_visualize.py             Step 5:  book-level matplotlib figures
│   ├── 05_visualize_chapters.py    Step 5c: chapter-level figures
│   ├── 06_build_report.py          Step 6:  book-level HTML report
│   ├── 06_build_report_chapters.py Step 6c: chapter-level HTML report
│   ├── 07_build_excel.py           Step 7:  book-level Excel workbook
│   ├── 07_build_excel_chapters.py  Step 7c: chapter-level Excel workbook
│   ├── 09_extract_index.py         Step 9:  index term extraction
│   ├── 09b_build_index_analysis.py Step 9b: canonical vocab + person name merging
│   ├── 10_build_index_report.py    Step 10: controlled vocabulary report
│   ├── 12_index_grounding.py       Step 12: index-term topic labelling, density, velocity
│   ├── 08_build_timeseries.py      Step 8:  time series HTML report (needs step 12)
│   ├── 15_entity_classify.py       Step 15: NER classification cache (spaCy + Wikidata)
│   ├── 14_entity_network.py        Step 14: entity relational network (needs step 15)
│   ├── 11_embedding_comparison.py  Step 11: embedding method comparison (optional)
│   ├── build_embed_report.py       Step 11b: rebuild comparison report from results JSON
│   ├── 13_weighted_comparison.py   Step 13: compare unweighted vs weighted pipeline runs
│   ├── embeddings.py               Embedding provider abstraction module
│   ├── 00_export_calibre.py        Step 0:  export csv/books_metadata_full.csv from Calibre DB
│   ├── 00_classify_book_styles.py  Step 0a: heuristic book style classification
│   ├── 00_fetch_worldcat_metadata.py Step 0b: Google Books + Open Library enrichment
│   ├── 00_fetch_anu_primo.py        Step 0c: ANU Primo catalogue enrichment
│   ├── 09c_validate_topics.py      Topic validation report (coherence, stability, top terms)
│   ├── patch_topic_names.py        One-off: write agreed topic names to JSON files
│   ├── heuristic_features.py       Monograph classifier: 10 structural text heuristics
│   ├── train_monograph_classifier.py  Monograph binary classifier (logistic regression)
│   ├── check_integrity.py          Session-start integrity checker
│   ├── test_pipeline.py            Regression test suite (15 tests)
│   ├── check_stale_vars.py         Detect and auto-fix stale hardcoded fallback vars (--fix)
│   ├── record_topic_run.py         Topic naming server — direct DB submission (server/offline/ingest modes)
│   ├── pipeline_db.py              Shared DB module — 8-table schema, DB path, hash functions
│   ├── log_pipeline_run.py         Manual run logging — equivalence class tracking; pre-survey gate
│   ├── migrate_pipeline_db.py      One-shot migration from topic_naming.db → pipeline.db
│   ├── get_google_token.py         OAuth token generator for Google Forms API (run once on the workstation)
│   ├── generate_google_form.py     Google Forms survey creation — 39-item form per pipeline run
│   ├── ingest_google_responses.py  Google Form response ingester → pipeline.db
│   └── run_all.sh                  End-to-end runner (--test flag for survey-ineligible test runs)
│
├── docs/
│   ├── methodology.md          ← full technical methodology (canonical)
│   ├── decisions.md            ← design decision log (canonical)
│   ├── contributions.md        ← authorship, CRediT statement, session log
│   ├── CHANGELOG.md            ← versioned change history
│   ├── ROADMAP.md              ← planned work, open questions, phases
│   │
│   ├── memos/                  ← research memos, paper feeds
│   │   ├── memo_media_aware_nlp_epistemic_affordances.md   ← theoretical framework
│   │   ├── memo_attribution_annotations.md                 ← FLAGGED for paper integration
│   │   ├── memo_data_quality_algorithm_infection.md
│   │   ├── memo_lda_k_selection.md
│   │   ├── memo_topic_naming_reliability.md
│   │   └── corpus_construction.md                          ← draft paper methods §3
│   │
│   ├── reference/              ← project-specific reference data
│   │   ├── book_styles.md
│   │   ├── project_context.md
│   │   └── survey_hosting_options.md
│   │
│   └── archive/                ← frozen; do not edit
│       └── consolidation_14apr2026.md
│
├── README.md
├── requirements.txt
└── .gitignore                  ← excludes csv/, json/, data/outputs/, figures/
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

System-level spell-checker (for `02_clean_text.py` only — skip for streaming):

```bash
# Linux
sudo apt-get install hunspell-en-us

# macOS
brew install hunspell

# Windows or any OS (pure-Python fallback)
pip install pyspellchecker>=0.7

# Or: place en_US.dic in project data/ directory
# Download from: https://github.com/LibreOffice/dictionaries
```

### 2. Export Calibre metadata and place text CSVs in csv/

Export `books_metadata_full.csv` directly from the Calibre database:

```bash
python3 src/00_export_calibre.py
# or if metadata.db is elsewhere:
python3 src/00_export_calibre.py --db /path/to/metadata.db
```

Re-run whenever books are added to or removed from Calibre, or when custom
column values (Publication Type, Theme, Available at) are updated.

Also place the OCR text exports in csv/:

```
csv/books_text_*.csv
```

### 3. Book style enrichment (run once, before main pipeline)

Not part of `run_all.sh` — external APIs, caching logic, reads
`csv/books_metadata_full.csv` (from step 2):

```bash
python3 src/00_classify_book_styles.py                    # heuristic baseline
python3 src/00_fetch_worldcat_metadata.py                 # Google Books + OL (~10 min)
python3 src/00_fetch_anu_primo.py                         # ANU Primo (~12 min)
python3 src/00_fetch_worldcat_metadata.py --reclassify    # apply enrichment
python3 src/00_fetch_anu_primo.py --reclassify            # apply Primo signals
python3 src/00_classify_book_styles.py --stats            # final distribution
```

Writes `json/book_styles.json` (covariate for downstream analysis).

### 4. Run the pipeline

```bash
bash src/run_all.sh              # standard (<~300 books)
bash src/run_all.sh --stream     # streaming parse+clean for large corpora
bash src/run_all.sh --test       # test run; runlog suffixed _test; not survey-eligible
```

See `src/run_all.sh` for the full ordered step list (01 → 02 → 03 → 04 → 05 → 06 → 07 →
09 → 09b → 09c → 10 → 12 → 08 → 11 → 15 → 14, with chapter-level variants after book-level).
Runlog auto-written to `data/outputs/runlogYYYYMMDD.csv`.

**Entity classification requires spaCy** (step 15, cached in `json/entity_types_cache.json`):

```bash
pip install spacy && python3 -m spacy download en_core_web_sm
# or offline: step 15 falls back to heuristics if --no-wikidata / spaCy unavailable
```

### 5. Generate abstractive summaries (optional — see note)

> **Note:** Each book is summarised from a ~60k token sample. Summary reliability
> has not been established and `books.html` is excluded from the current release
> scope for this reason. Generate summaries if you need them for the chapter-level
> pipeline, but treat outputs as provisional.

```bash
export ANTHROPIC_API_KEY=sk-ant-...

python3 src/generate_summaries_api.py              # 4 workers, ~28 min
python3 src/generate_summaries_api.py --workers 8  # faster, ~14 min
python3 src/generate_summaries_api.py --workers 1  # sequential, ~112 min
```

Fully resumable — safe to interrupt and restart. Estimated cost: ~$25–35
for 541 books from scratch (only missing books are processed on reruns —
if most summaries already exist, the incremental cost is a few cents).

---

## Pipeline Overview

```
Calibre metadata.db  +  csv/books_text_*.csv
        │
  00_export_calibre.py         Export books_metadata_full.csv from Calibre DB
        │
        ▼
csv/books_metadata_full.csv  +  csv/books_text_*.csv
        │
        ├── STREAMING (recommended) ──── parse_and_clean_stream.py × 25
        └── STANDARD                ──── 01_parse_books.py → 02_clean_text.py
        │
        ▼                              writes to json/
  03_nlp_pipeline.py          LDA (book-level, k=9 canonical)
  generate_summaries_api.py   Abstractive summaries via Anthropic API (~60k token sample; provisional)
  04_summarize.py             Extractive fallback summaries
  05_visualize.py             Matplotlib figures (book-level)
  06_build_report.py          Book-level HTML reports → data/outputs/
                                  index.html · clusters.html · keyphrases.html
                                  cosine.html · book_nlp_entity_network.html
                                  books.html (excluded from release — 60k token sampling)
  07_build_excel.py           Excel workbook → data/outputs/book_nlp_results.xlsx

  ── Chapter-level (not yet refactored) ──
  03_nlp_pipeline_chapters.py NMF (chapter-level, 8 topics)
  05_visualize_chapters.py    Matplotlib figures (chapter-level)
  06_build_report_chapters.py Chapter-level HTML → data/outputs/book_nlp_analysis_chapters.html
  07_build_excel_chapters.py  Excel workbook → data/outputs/book_nlp_chapters.xlsx
  09_extract_index.py         Index term extraction
  09b_build_index_analysis.py Canonical vocab + person name merging
  10_build_index_report.py    Controlled vocabulary report  → data/outputs/
  12_index_grounding.py       Topic labelling, density, velocity  ← needs 09b
  08_build_timeseries.py      Time series report            → data/outputs/  ← needs 12
  15_entity_classify.py       NER classification cache (run once)
  14_entity_network.py        Entity relational network     → data/outputs/  ← needs 15
```

---

## Output Files

All reports are written to `data/outputs/`.

**Book-level — main analysis (split)**

| File | Description |
|------|-------------|
| `index.html` | Main report — LDA topics, Fig 1–6, topic proportions |
| `clusters.html` | Cluster composition |
| `keyphrases.html` | Keyphrase analysis |
| `cosine.html` | Cosine similarity |
| `book_nlp_entity_network.html` | Entity relational network — persons, concepts, organisations, locations; 4 layout algorithms; degree filter |
| `books.html` | Per-book summaries — excluded from release; summaries are generated from a ~60k token sample per book and reliability has not been established |

**Book-level — other reports**

| File | Description |
|------|-------------|
| `book_nlp_timeseries.html` | Publication year analysis — 7 charts: publications/yr, LDA topics, NMF topics, clusters, scatter, cumulative, band prevalence + concept velocity (Chart 7 requires steps 09b→12 first) |
| `book_nlp_index_analysis.html` | Controlled vocabulary — index term frequency, time series, co-occurrence, topic distribution, term explorer |
| `book_nlp_index_grounding.html` | Index grounding — topic labelling, concept density scatter, concept velocity across decades |
| `book_nlp_embedding_comparison.html` | Embedding method comparison — LSA vs Sentence Transformers vs Voyage AI |
| `book_nlp_weighted_comparison.html` | Side-by-side comparison of unweighted vs weighted pipeline runs |

**Chapter-level (not yet refactored)**

| File | Description |
|------|-------------|
| `book_nlp_analysis_chapters.html` | Chapter-level report — NMF topics, clusters, keyphrases, chapter summaries |

**Excel**

| File | Description |
|------|-------------|
| `book_nlp_results.xlsx` | Book-level Excel (5 sheets) |
| `book_nlp_chapters.xlsx` | Chapter-level Excel (4 sheets) |

---

## Topic Solutions

### Book-level (LDA, k=9)

Canonical run: monographs and collected works only ([2133] excluded — OCR corruption),
full-text with front/back matter stripped, 15,000-feature vocabulary, spaCy lemmatisation,
`--topics 9 --seeds 5`. Current per-topic stability and run parameters live in
`json/topic_stability.json` and `json/nlp_results.json`; aggregate figures and runlog are
in the latest `data/outputs/runlogYYYYMMDD.csv`.

Topic names generated via `--name-topics` (Anthropic API) then manually reviewed.
Individual names are provisional pending multi-rater validation (sprint items 3–5).

Live topic names are not duplicated here — they rotate per run and the previous
static table went stale. Authoritative sources:

- **Current names:** `json/nlp_results.json['topic_names']`
- **Canonical taxonomy overlay:** `src/patch_topic_names.py` (TAXONOMY dict)
- **Latest validation report (top words, stability, exemplar books):**
  `data/outputs/topic_validation.md` — regenerate with
  `src/09c_validate_topics.py --top 10 --md`

### Chapter-level (NMF, 8 topics)

| # | Name |
|---|------|
| T1 | Human & Social Experience |
| T2 | Mathematical & Formal Systems |
| T3 | General Systems Theory |
| T4 | History & Philosophy of Cybernetics |
| T5 | Management & Organisational Cybernetics |
| T6 | Control Theory & Engineering |
| T7 | Applied Cybernetics & Technology |
| T8 | Biological & Cognitive Systems |

*Note: chapter-level analysis is MVP infrastructure — not validated to the same standard as book-level LDA.*

---

## Input Data Format

### `csv/books_metadata_full.csv` (tab-separated)
Full Calibre metadata export: 695 books, 20 columns including `id`, `title`, `pubdate`, `author_sort`, `lang_code`, `inclusion_stratum`, `archive_id`, `in_title`, `in_description`, `in_tags`, and per-field keyword flags.

### `csv/books_text_*.csv` (CSV, two columns)
Columns: `id`, `searchable_text`
Files: `csv/books_text_*.csv` (auto-detected by glob from `csv/` directory)

---

## Weighted Second Pass (optional)

The `--weighted` flag boosts topic-discriminating index terms and dampens
pervasive ones, improving cluster quality by ~1–2%. It has a hard dependency
on two files written by earlier pipeline steps:

| Required file | Written by |
|--------------|------------|
| `json/nlp_results.json` | `03_nlp_pipeline.py` (first pass) |
| `json/index_analysis.json` | `09b_build_index_analysis.py` |

**It cannot run on a clean start.** Run the full pipeline once first, then:

```bash
python3 src/03_nlp_pipeline.py --weighted             # re-weights features
python3 src/03_nlp_pipeline.py --weighted --name-topics  # + regenerate names
python3 src/04_summarize.py
python3 src/05_visualize.py
python3 src/06_build_report.py
python3 src/07_build_excel.py
python3 src/12_index_grounding.py
python3 src/08_build_timeseries.py

# Chapter-level weighted rerun (not yet refactored — run separately if needed)
# python3 src/03_nlp_pipeline_chapters.py
# python3 src/05_visualize_chapters.py
# python3 src/06_build_report_chapters.py
# python3 src/07_build_excel_chapters.py
```

Or uncomment the pre-written block at the bottom of `src/run_all.sh`.

---

## Change history

Versioned change log: [`docs/CHANGELOG.md`](docs/CHANGELOG.md).

---

## Requirements

Python 3.9+. Install Python dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Spell-checking (`02_clean_text.py` only)

The script uses portable, OS-agnostic dictionary discovery — no hardcoded
paths. It searches through five methods in order, then falls back gracefully:

| Priority | Method | Notes |
|----------|--------|-------|
| 1 | **`DICPATH` env var** | hunspell's own standard — set this to override everything else |
| 2 | **`hunspell -D`** | asks hunspell where its dictionaries live |
| 3 | **`CONDA_PREFIX` glob** | scans the active conda environment recursively |
| 4 | **`find` command** | searches `/usr`, `/opt`, `/usr/local` (Unix/macOS) |
| 5 | **`pkg-config`** | queries the hunspell package for its data directory (Linux) |
| 6 | **pyspellchecker** | pure Python fallback, any OS: `pip install pyspellchecker>=0.7` |
| 7 | **No filtering** | automatic last resort — `min_df=2` still handles most OCR noise |

**Installing hunspell:**
```bash
# conda (any OS) — recommended if using Anaconda/Miniconda
conda install -c conda-forge hunspell hunspell-en

# macOS Homebrew
brew install hunspell

# Linux (Debian/Ubuntu)
sudo apt-get install hunspell-en-us

# Linux (Fedora/RHEL)
sudo dnf install hunspell-en
```

**Manual override** — if the script can't find your dictionary, set `DICPATH`
to the directory containing `en_US.dic` before running:
```bash
export DICPATH=/opt/anaconda3/share/hunspell_dictionaries
python3 src/02_clean_text.py
```

**Tip**: `parse_and_clean_stream.py` uses regex-only cleaning with
**no spell-checking dependency**. For large corpora, use the streaming path.

---

## Troubleshooting

### Hunspell dictionary not found
The script searches for `en_US.dic` via five portable methods (see
Spell-checking section above). If all fail, set `DICPATH` explicitly:
```bash
# Find where conda installed it:
find $CONDA_PREFIX -name "en_US.dic" 2>/dev/null

# Then set DICPATH to that directory:
export DICPATH=/opt/anaconda3/share/hunspell_dictionaries
```
Or install the pure-Python fallback (no system dependency):
```bash
pip install pyspellchecker>=0.7
```
The script warns and continues without filtering if neither is found.

### API rate limit errors (`HTTP 429`)
The `generate_summaries_api.py` script uses exponential backoff automatically,
but if you see frequent 429s reduce concurrency:
```bash
python3 src/generate_summaries_api.py --workers 2
```
Check your rate tier at [console.anthropic.com](https://console.anthropic.com).

### `credit balance is too low` (HTTP 400)
Top up credits at **console.anthropic.com → Plans & Billing**. The script
will resume from where it left off — completed books are saved to
`summaries.jsonl` and skipped on the next run.

### Out of memory during streaming
If `parse_and_clean_stream.py` runs out of memory, the CSV file may contain
unusually large records. Try reducing `CLEAN_CAP` from 300,000 to 150,000
characters at the top of the script, or split the CSV file into smaller chunks.

### `books_clean.json not found`
Run the parse/clean step first:
```bash
# Streaming (recommended)
for f in csv/books_text_*.csv; do python3 src/parse_and_clean_stream.py "$f"; done
# Then convert JSONL → JSON:
python3 -c "
import json
books = {}
with open('json/books_clean.jsonl') as f:
    for line in f:
        if line.strip():
            r = json.loads(line); books[r['id']] = {k:v for k,v in r.items() if k!='id'}
with open('json/books_clean.json','w') as f:
    json.dump(books, f, ensure_ascii=False)
print(f'Converted {len(books)} books')
"
```

### Reports open but charts are blank
The interactive reports require an internet connection to load Plotly.js from
CDN (`cdnjs.cloudflare.com`). Open the HTML file in a browser with internet
access, or host Plotly.js locally and update the `<script src="...">` tag.

### Summaries look extractive (copying source text)
Re-run `generate_summaries_api.py` — it includes verbatim similarity checking
and will retry books whose summaries exceed the 35% overlap threshold. If the
problem persists, delete the affected entries from `summaries.jsonl` and rerun.

### `entity_types_cache.json not found`
Run step 15 first:
```bash
pip install spacy && python3 -m spacy download en_core_web_sm
python3 src/15_entity_classify.py
```
Or run in offline mode (heuristics only, no spaCy or Wikidata required):
```bash
python3 src/15_entity_classify.py --no-wikidata
```

---

## Reproducibility

Random seed: `random_state=99`. Sensitivity analysis confirmed stable topic
and cluster solutions across seeds 42, 99, 123, and 2024.
