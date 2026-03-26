# Book Corpus NLP Analysis Pipeline — Pilot Snapshot

A reproducible NLP pipeline for topic modelling, clustering, keyphrase
extraction, summarisation, controlled vocabulary analysis, and visualisation
applied to a cybernetics book corpus extracted from a Calibre library.

**Corpus:** 675 books · 7,349 chapters · 1954–2025

---

## Folder Structure

```
project-root/
├── books_lang.csv              ← Calibre metadata (tab-separated)
├── books_text_01.csv           ← OCR text files (25 total)
│   …
├── books_text_25.csv
│
├── src/                        ← Pipeline scripts
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
│   ├── 08_build_timeseries.py      Step 8:  time series HTML report
│   ├── 09_extract_index.py         Step 9:  index term extraction
│   ├── 09b_build_index_analysis.py Step 9b: build index_analysis.json + snippets
│   ├── 10_build_index_report.py    Step 10: controlled vocabulary report
│   ├── 11_embedding_comparison.py  Step 11: embedding method comparison (optional)
│   ├── build_embed_report.py       Step 11b: rebuild comparison report from results JSON
│   ├── 13_weighted_comparison.py   Step 13: compare unweighted vs weighted pipeline runs
│   ├── 14_entity_network.py        Step 14: person–concept–location relational network
│   ├── 12_index_grounding.py       Step 12: index-term topic labelling, density, velocity
│   ├── embeddings.py               Embedding provider abstraction module
│   └── run_all.sh                  End-to-end runner
│
├── data/
│   ├── summaries.json          ← Abstractive summaries (shipped with package)
│   └── outputs/                ← Generated reports and Excel files
│
├── docs/
│   ├── methodology.md
│   ├── decisions.md
│   └── chat_history.md
│
├── requirements.txt
└── README.md

# Intermediate files (generated in project root during pipeline run)
books_parsed.json               written by 01, read by 02
books_clean.json                written by 02/stream, read by 03, 04, 09
nlp_results.json                written by 03, read by 04–08, 11, 12
summaries.json                  written by generate_api/04, read by 03c–07c
nlp_results_chapters.json       written by 03c, read by 05c–08
index_terms.json                written by 09, read by 10, 12
index_vocab.json                written by 09, read by 10
index_analysis.json             written by 09b, read by 10, 08 (Chart 7), 11, 12
index_snippets.json             written by 09b, read by 10
topic_index_grounding.json      written by 12, read by reports
concept_density.json            written by 12, read by reports
concept_velocity.json           written by 12, read by 08 (Chart 7)
nlp_results.json topic_names    written by 03 --name-topics, read by all report scripts
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

### 2. Place input files in project root

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
# Place Calibre CSVs in csv/ before running:
#   cp /path/to/books_lang.csv      csv/
#   cp /path/to/books_text_*.csv    csv/

# Book-level pipeline
python3 src/03_nlp_pipeline.py              # standard (always run this first)
python3 src/03_nlp_pipeline.py --name-topics  # + auto-name topics via API (~$0.01)
python3 src/04_summarize.py
python3 src/05_visualize.py
python3 src/06_build_report.py
python3 src/07_build_excel.py

# Chapter-level pipeline (uses summaries.json from 04)
python3 src/03_nlp_pipeline_chapters.py
python3 src/05_visualize_chapters.py
python3 src/06_build_report_chapters.py
python3 src/07_build_excel_chapters.py

# Index extraction — must run before 10, 12, and 08
python3 src/09_extract_index.py
python3 src/09b_build_index_analysis.py   # builds index_analysis.json + snippets
python3 src/10_build_index_report.py

# Index grounding — must run after 09+10, before 08
# Produces: index_analysis.json, concept_velocity.json, concept_density.json
python3 src/12_index_grounding.py

# Time series — must run after 12 (Chart 7 needs concept_velocity.json)
python3 src/08_build_timeseries.py

# Optional: abstractive summaries (rerun 03c onwards if you regenerate)
# python3 src/generate_summaries_api.py --workers 4

# Optional: embedding comparison
# python3 src/11_embedding_comparison.py --no-voyage  # A+B+C

# Entity relational network (run after 09b and 12)
# python3 src/14_entity_network.py --no-windows   # fast
# python3 src/14_entity_network.py                # + paragraph windows (~5 min)
#
# Outputs: data/outputs/book_nlp_entity_network.html
# Node kinds: Person (blue) · Concept (green) · Organisation (purple) · Location (amber)
# Layouts: Force-directed · Radial · Bipartite · Circular (selector in report UI)
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
for 675 books. When done, rerun from step 03_nlp_pipeline_chapters.py onwards
to use the new summaries.

---

## Pipeline Overview

```
books_lang.csv  +  books_text_*.csv
        │
        ├── STREAMING (recommended) ──── parse_and_clean_stream.py × 25
        └── STANDARD                ──── 01_parse_books.py → 02_clean_text.py
        │
        ▼
  03_nlp_pipeline.py          LDA (book-level, 7 topics)
  generate_summaries_api.py   Abstractive summaries via Anthropic API
  04_summarize.py             Extractive fallback summaries
  03_nlp_pipeline_chapters.py NMF (chapter-level, 6 topics)
  05_visualize.py / _chapters  Matplotlib figures
  06_build_report.py / _chapters  Interactive HTML reports
  07_build_excel.py / _chapters   Excel workbooks
  09_extract_index.py         Step 9:  index term extraction
  10_build_index_report.py    Step 10: controlled vocabulary report
  12_index_grounding.py       Step 12: topic labelling, density, velocity  ← needs 09+10
  08_build_timeseries.py      Step 8:  time series report                  ← needs 12
```

---

## Output Files

| File | Description |
|------|-------------|
| `book_nlp_analysis.html` | Book-level interactive report — LDA topics, clusters, cosine similarity, keyphrases, summaries |
| `book_nlp_analysis_chapters.html` | Chapter-level report — NMF topics, clusters, keyphrases, chapter summaries |
| `book_nlp_timeseries.html` | Publication year analysis — 7 charts: publications/yr, LDA topics, NMF topics, clusters, scatter, cumulative, band prevalence + concept velocity (Chart 7 requires steps 09→12 first) |
| `book_nlp_index_analysis.html` | Controlled vocabulary — index term frequency, time series, co-occurrence, topic distribution, term explorer |
| `book_nlp_index_grounding.html` | Index grounding — topic labelling, concept density scatter, concept velocity across decades |
| `book_nlp_embedding_comparison.html` | Embedding method comparison — LSA vs Sentence Transformers vs Voyage AI |
| `book_nlp_results.xlsx` | Book-level Excel (5 sheets) |
| `book_nlp_chapters.xlsx` | Chapter-level Excel (4 sheets) |

---

## Topic Solutions

### Book-level (LDA, 7 topics)

| # | Name | Characteristic terms |
|---|------|---------------------|
| T1 | Human & Social Experience | human, media, technology, social, cybernetic |
| T2 | Mathematical & Formal Systems | wiener, machine, mathematical, computer, language |
| T3 | General Systems Theory | systems, cybernetics, social, management, design |
| T4 | History & Philosophy of Cybernetics | science, human, theory, life, knowledge, philosophy |
| T5 | 2nd-Order Cybernetics & Bateson | bateson, communication, living, order, self, reality |
| T6 | Control Theory & Engineering | control, systems, behavior, feedback, model, function |
| T7 | Popular & Applied Cybernetics | people, world, human, life, make, years, think |

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
| `nlp_results.json` | `03_nlp_pipeline.py` (first pass) |
| `index_analysis.json` | `09b_build_index_analysis.py` |

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

- **Step 14 — Entity Network** (`14_entity_network.py`): force-directed person–concept–location relational network using PMI × reliability (book-level) and paragraph-window co-occurrence (local textual proximity)
- **`--weighted` flag** (`03_nlp_pipeline.py`): index-term lift-weighted TF-IDF — boosts Signal terms (schismogenesis, autopoiesis) and dampens pervasive Anchor terms (feedback, system)
- **Chart 7** (`08_build_timeseries.py`): band prevalence by decade + concept velocity — tracks how Anchor/Signal/Frontier term density evolves and how key terms migrate between topics over time
- **Step 12 — Index Grounding** (`12_index_grounding.py`): topic labelling via lift scores, concept density scatter, concept velocity
- **Recursive summarisation**: `--recursive` flag in `generate_summaries_api.py` for map-reduce book summaries
- **Embedding abstraction**: `embeddings.py` — swap LSA / Sentence Transformers / Voyage AI with one line
- **Embedding comparison**: `11_embedding_comparison.py` with `--no-voyage` and `--no-st` flags

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
with open('books_clean.jsonl') as f:
    for line in f:
        if line.strip():
            r = json.loads(line); books[r['id']] = {k:v for k,v in r.items() if k!='id'}
with open('books_clean.json','w') as f:
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

---

## Reproducibility

Random seed: `random_state=99`. Sensitivity analysis confirmed stable topic
and cluster solutions across seeds 42, 99, 123, and 2024.
