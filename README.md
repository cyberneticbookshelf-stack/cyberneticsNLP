# Book Corpus NLP Analysis Pipeline — Pilot Snapshot

**Authors**

Paul Wong¹ · ORCID [0000-0001-6515-1860](https://orcid.org/0000-0001-6515-1860)
Claude Sonnet 4.6 (Anthropic, claude.ai)²

¹ School of Cybernetics, The Australian National University, Canberra, Australia
² Large language model; no persistent identity, affiliation, or legal standing

**Date:** 3 April 2026

---

## Contributor Roles

Full CRediT taxonomy statement, session log, and note on AI authorship:
→ [`docs/contributions.md`](docs/contributions.md)

---

A reproducible NLP pipeline for topic modelling, clustering, keyphrase
extraction, summarisation, controlled vocabulary analysis, and visualisation
applied to a cybernetics book corpus extracted from a Calibre library.

**Corpus:** 695 books · 1954–2025

---

## Folder Structure

```
CyberneticsNLP/
├── csv/                        ← Place Calibre CSV exports here (OneDrive synced)
│   ├── books_metadata_full.csv ← Calibre metadata, 20 cols incl. inclusion_stratum (tab-separated)
│   └── books_text_*.csv        ← OCR text (25 files)
│
├── json/                       ← All JSON/JSONL outputs (auto-created, OneDrive synced)
│   ├── books_clean.json        ← cleaned text corpus (written by 02/stream)
│   ├── nlp_results.json        ← LDA/cluster results (written by 03)
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
│   └── outputs/                ← Generated HTML reports and Excel files (OneDrive synced)
│       ├── book_nlp_analysis.html
│       ├── book_nlp_analysis_chapters.html
│       ├── book_nlp_timeseries.html
│       ├── book_nlp_index_analysis.html
│       ├── book_nlp_index_grounding.html
│       ├── book_nlp_entity_network.html
│       ├── book_nlp_embedding_comparison.html
│       ├── book_nlp_weighted_comparison.html
│       ├── book_nlp_results.xlsx
│       └── book_nlp_chapters.xlsx
│
├── figures/                    ← matplotlib figures (auto-created, OneDrive synced)
│
├── src/                        ← Pipeline scripts (tracked in git)
│   ├── parse_and_clean_stream.py   Step 0s: streaming clean (large corpora)
│   ├── 01_parse_books.py           Step 1:  parse CSV → books_parsed.json
│   ├── 02_clean_text.py            Step 2:  Hunspell clean → books_clean.json
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
│   ├── 00_classify_book_styles.py  Step 0a: heuristic book style classification
│   ├── 00_fetch_worldcat_metadata.py Step 0b: Google Books + Open Library enrichment
│   ├── 00_fetch_anu_primo.py        Step 0c: ANU Primo catalogue enrichment
│   ├── check_integrity.py          Session-start integrity checker
│   ├── test_pipeline.py            Regression test suite (15 tests)
│   └── run_all.sh                  End-to-end runner
│
├── docs/
│   ├── methodology.md          ← full technical methodology (1,600+ lines)
│   ├── decisions.md            ← design decision log (900+ lines)
│   ├── contributions.md        ← authorship, CRediT statement, session log
│   ├── CHANGELOG.md            ← versioned change history
│   ├── ROADMAP.md              ← planned work, open questions, phases
│   └── chat_history.md         ← session notes
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

### 2. Place input files in csv/

```
csv/books_lang.csv
csv/books_text_*.csv
```

### 3a. Run — streaming path (recommended for large corpora)

Processes one CSV at a time, never loads the full corpus into memory.
Run once per CSV file in any order:

```bash
for f in csv/books_text_*.csv; do
    python3 src/parse_and_clean_stream.py "$f"
done
```

Then run downstream steps:

```bash
# Book-level pipeline
python3 src/03_nlp_pipeline.py              # standard (always run this first)
python3 src/03_nlp_pipeline.py --name-topics  # + auto-name topics via API (~$0.01)
python3 src/04_summarize.py
python3 src/05_visualize.py
python3 src/06_build_report.py
python3 src/07_build_excel.py

# Chapter-level pipeline (uses summaries.json from generate_summaries_api / 04)
python3 src/03_nlp_pipeline_chapters.py
python3 src/05_visualize_chapters.py
python3 src/06_build_report_chapters.py
python3 src/07_build_excel_chapters.py

# Index extraction and canonical vocabulary
python3 src/09_extract_index.py
python3 src/09b_build_index_analysis.py   # canonical vocab + person name merging
python3 src/10_build_index_report.py

# Index grounding — must run after 09b, before 08
python3 src/12_index_grounding.py

# Time series — must run after 12 (Chart 7 needs concept_velocity.json)
python3 src/08_build_timeseries.py

# Book style enrichment — run once before main pipeline
# Requires csv/books_metadata_full.csv (exported from Calibre via metadata.db)
python3 src/00_classify_book_styles.py                    # heuristic baseline
python3 src/00_fetch_worldcat_metadata.py                 # Google Books + OL (~10 min)
python3 src/00_fetch_anu_primo.py                         # ANU Primo (~12 min)
python3 src/00_fetch_worldcat_metadata.py --reclassify    # apply enrichment
python3 src/00_fetch_anu_primo.py --reclassify            # apply Primo signals
python3 src/00_classify_book_styles.py --stats            # final distribution

# Entity classification — run once, results cached in json/entity_types_cache.json
# Requires: pip install spacy && python3 -m spacy download en_core_web_sm
python3 src/15_entity_classify.py          # heuristics + spaCy + Wikidata
python3 src/15_entity_classify.py --no-wikidata  # offline mode

# Entity relational network — run after 09b, 12, and 15
python3 src/14_entity_network.py --no-windows  # fast (book-level edges only)
python3 src/14_entity_network.py               # + paragraph-window edges (~5 min)

# Optional: abstractive summaries (rerun 03c onwards if you regenerate)
# python3 src/generate_summaries_api.py --workers 4

# Optional: embedding comparison
# python3 src/11_embedding_comparison.py --no-voyage  # A+B+C
```

### 3b. Run — standard path (small corpora, <~300 books)

```bash
bash src/run_all.sh
```

### 4. Generate abstractive summaries (optional but recommended)

```bash
export ANTHROPIC_API_KEY=sk-ant-...

python3 src/generate_summaries_api.py              # 4 workers, ~28 min
python3 src/generate_summaries_api.py --workers 8  # faster, ~14 min
python3 src/generate_summaries_api.py --workers 1  # sequential, ~112 min
```

Fully resumable — safe to interrupt and restart. Estimated cost: ~$25–35
for 675 books from scratch (only missing books are processed on reruns —
if most summaries already exist, the incremental cost is a few cents).
When done, rerun from step 03_nlp_pipeline_chapters.py onwards
to use the new summaries.

---

## Pipeline Overview

```
csv/books_lang.csv  +  csv/books_text_*.csv
        │
        ├── STREAMING (recommended) ──── parse_and_clean_stream.py × 25
        └── STANDARD                ──── 01_parse_books.py → 02_clean_text.py
        │
        ▼                              writes to json/
  03_nlp_pipeline.py          LDA (book-level, k=9 canonical)
  generate_summaries_api.py   Abstractive summaries via Anthropic API
  04_summarize.py             Extractive fallback summaries
  03_nlp_pipeline_chapters.py NMF (chapter-level, 6 topics)
  05_visualize.py / _chapters  Matplotlib figures
  06_build_report.py / _chapters  Interactive HTML reports  → data/outputs/
  07_build_excel.py / _chapters   Excel workbooks           → data/outputs/
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

| File | Description |
|------|-------------|
| `book_nlp_analysis.html` | Book-level interactive report — LDA topics, clusters, cosine similarity, keyphrases, summaries |
| `book_nlp_analysis_chapters.html` | Chapter-level report — NMF topics, clusters, keyphrases, chapter summaries |
| `book_nlp_timeseries.html` | Publication year analysis — 7 charts: publications/yr, LDA topics, NMF topics, clusters, scatter, cumulative, band prevalence + concept velocity (Chart 7 requires steps 09b→12 first) |
| `book_nlp_index_analysis.html` | Controlled vocabulary — index term frequency, time series, co-occurrence, topic distribution, term explorer |
| `book_nlp_index_grounding.html` | Index grounding — topic labelling, concept density scatter, concept velocity across decades |
| `book_nlp_entity_network.html` | Entity relational network — persons, concepts, organisations, locations; 4 layout algorithms; degree filter |
| `book_nlp_embedding_comparison.html` | Embedding method comparison — LSA vs Sentence Transformers vs Voyage AI |
| `book_nlp_weighted_comparison.html` | Side-by-side comparison of unweighted vs weighted pipeline runs |
| `book_nlp_results.xlsx` | Book-level Excel (5 sheets) |
| `book_nlp_chapters.xlsx` | Chapter-level Excel (4 sheets) |

---

## Topic Solutions

### Book-level (LDA, k=9 — canonical, 3 April 2026)

695 books · `--min-chars 10000 --lemmatize --topics 9 --seeds 5` · 7/9 stable · 0 dead · mean stability=0.382

| # | Name |
|---|------|
| T1 | Management Cybernetics |
| T2 | Second-Order Cybernetics Applied to Social Systems |
| T3 | Dynamical Systems, Homeostasis & Biological Regulation |
| T4 | Psychological Cybernetics |
| T5 | Non-Anglophone Engineering Cybernetics |
| T6 | Mathematical Foundations of Cybernetics |
| T7 | Cultural Cybernetics, Posthumanism & Digital Media |
| T8 | Applied Cybernetics & Computers in Society |
| T9 | Residual / Outlier Cluster |

Full topic validation: `json/topic_validation.json` · run `src/09c_validate_topics.py --top 10 --md` to regenerate.

### Chapter-level (NMF, 6 topics)

| # | Name | Characteristic terms |
|---|------|---------------------|
| T1 | Human & Social Experience | argues, human, author, understanding, explores |
| T2 | Mathematical & Formal Systems | mathematical, system, functions, models, demonstrates |
| T3 | General Systems Theory | theory, cybernetics, systems, opening, sections |
| T4 | Management & Organisational Cybernetics | organizational, management, decision making, model |
| T5 | Control Theory & Engineering | control, feedback, control systems, mechanisms, loops |
| T6 | Popular & Applied Cybernetics | examines, technological, analysis, human, technology |

---

## Input Data Format

### `csv/books_lang.csv` (tab-separated)
Columns: `id`, `title`, `pubdate`, `author_sort`, `lang_code`

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
python3 src/03_nlp_pipeline_chapters.py
python3 src/05_visualize_chapters.py
python3 src/06_build_report_chapters.py
python3 src/07_build_excel_chapters.py
python3 src/12_index_grounding.py
python3 src/08_build_timeseries.py
```

Or uncomment the pre-written block at the bottom of `src/run_all.sh`.

---

## New in This Snapshot

- **Step 15 — Entity Classification** (`15_entity_classify.py`): three-stage NER pipeline — heuristics → spaCy `en_core_web_sm` → Wikidata REST API. Produces `json/entity_types_cache.json`, cached permanently. Run once before step 14. Offline mode: `--no-wikidata`
- **Step 14 — Entity Network** (`14_entity_network.py`): interactive entity relational network (persons, concepts, organisations, locations) using PMI × reliability (book-level edges). Four layout algorithms selectable in the report UI: Force-directed (Fruchterman-Reingold), Radial, Bipartite, Circular
- **Index canonicalisation** (`09b_build_index_analysis.py`): person name merging (262 rules: `Wiener, N.` → `Wiener, Norbert`), accent normalisation, noise suppression (function-word fragments, ebook preambles, author affiliations)
- **`--weighted` flag** (`03_nlp_pipeline.py`): index-term lift-weighted TF-IDF — boosts Signal terms (schismogenesis, autopoiesis) and dampens pervasive Anchor terms (feedback, system)
- **Chart 7** (`08_build_timeseries.py`): band prevalence by decade + concept velocity — tracks how Anchor/Signal/Frontier term density evolves and how key terms migrate between topics over time
- **Step 12 — Index Grounding** (`12_index_grounding.py`): topic labelling via lift scores, concept density scatter, concept velocity
- **Recursive summarisation**: `--recursive` flag in `generate_summaries_api.py` for map-reduce book summaries
- **Embedding abstraction**: `embeddings.py` — swap LSA / Sentence Transformers / Voyage AI with one line
- **Embedding comparison**: `11_embedding_comparison.py` with `--no-voyage` and `--no-st` flags
- **`check_integrity.py`**: session-start integrity checker — verifies all 20 required scripts and their key definitions
- **`test_pipeline.py`**: regression test suite — 15 tests covering the full pipeline end-to-end

---

## Requirements

Python 3.9+.

```bash
pip install scikit-learn==1.8.0 numpy==2.4.2 matplotlib==3.10.8 \
            seaborn==0.13.2 openpyxl==3.1.5 pandas==3.0.1
```

See `requirements.txt` for full details including system-level dependencies.

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
