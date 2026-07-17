# Refactor plan — direct Calibre DB ingestion

**Status:** Draft. Not yet started.
**Goal:** Replace the CSV intermediate layer (`csv/books_metadata_full.csv` + `csv/books_text_*.csv` shards) with direct reads from `data/inputs/calibre/metadata.db` and `data/inputs/calibre/full-text-search.db`.

## Why

1. **Streamline.** The CSV layer is two jobs in one: (a) flatten/enrich `metadata.db` into a 22-column denormalised view, (b) shard `books_text.searchable_text` into 25 files. Neither needs a CSV intermediate. ~500 MB of on-disk artefacts can go.
2. **Fix a latent correctness bug.** `data/inputs/calibre/split_books_text.sh:34` does `SELECT book AS id, searchable_text FROM books_text LIMIT … OFFSET …` with no `WHERE format=...`, no `ORDER BY`, and `TOTAL_ROWS=695` hardcoded. Today this happens to work because all rows are PDF and total is 703 (8 books currently get silently dropped off the end). The day an EPUB lands alongside a PDF, the same script would emit two rows with the same `id` — `src/01_parse_books.py:195-196` would drop the second one nondeterministically.
3. **Consolidate duplicated rules.** Pub-type inclusion (`src/03_nlp_pipeline.py:317`) and inclusion-stratum logic (`src/00_export_calibre.py:299-311`) currently live in two places. Each refactor step that re-derives them risks drift.
4. **Make corpus boundaries explicit.** 14 books currently in `metadata.db` lack FTS coverage (text not yet extracted by Calibre). The current pipeline silently ignores them. Direct DB access makes this gap visible at load time.

## What stays the same

- Canonical k=9 fit and topic naming (`run_20260426_k9_s5`, equivalence class `23b29233a67b2938`)
- Format preference: **PDF first**, to preserve the validated canonical run
- All downstream JSON artefacts (`json/books_clean.json`, `json/nlp_results.json`, etc.)
- The 541-monograph analysed framing
- Survey infrastructure (`data/pipeline.db`)

## Non-goals (deferred)

- Switching to EPUB as the preferred text source. See "Post-refactor: EPUB vs PDF comparison" below.
- Re-validating canonical k=9. The refactor must produce results in the same equivalence class as the current canonical run.
- Touching enrichment scripts (`00_fetch_worldcat_metadata.py`, `00_fetch_anu_primo.py`) beyond making them read via the new module.

---

## Plan

Each step is a single-PR-sized change with one acceptance test. CSV paths stay in place until Step 12 — any step is revertible by flipping a flag.

### Step 0 — Baseline snapshot (no code changes)

**What:** Run `bash src/run_all.sh` on current `main`. Record `nlp_hash`, equivalence class, runlog row, `wc -l json/books_clean.json`, byte-size of `csv/books_metadata_full.csv`, SHA-256 of each `csv/books_text_*.csv`.

**Why:** Every subsequent step is judged against this. Without a frozen baseline you can't tell "equivalent" from "different but unnoticed".

**Pass:** Snapshot stored in a working note (not committed). Figures available for diff.

### Step 0.5 — Audit current multi-format state

**What:** One-shot SQL diagnostic: `SELECT book, COUNT(*), GROUP_CONCAT(format) FROM books_text GROUP BY book HAVING COUNT(*) > 1;` against `full-text-search.db`.

**Why:** Confirms the corpus assumption (zero multi-format books today) before any code change relies on it.

**Pass:** Query returns zero rows. If non-zero, halt and re-plan format-preference rule.

### Step 1 — Add `src/calibre_db.py` (pure addition, no callers)

**What:** New read-only access module. Exports:

```python
open_calibre(metadata_db, fts_db) -> sqlite3.Connection
iter_books_meta(conn) -> Iterator[BookMeta]
iter_books_text(conn, *, format_preference=('PDF','EPUB','MOBI','AZW3'),
                only_ids=None, on_duplicate='warn') -> Iterator[BookText]
get_book(conn, book_id) -> tuple[BookMeta, str]
pub_type_filter(pt: str, include={'monograph','collected works'}) -> bool
inclusion_stratum(in_title, in_description, in_tags, in_publisher, theme) -> str
```

Connection opens via `file:path?mode=ro&immutable=1` URI; falls back to `shutil.copy` to `/tmp/` if `immutable` fails or Calibre is running. `iter_books_text` resolves multi-format rows deterministically by preference order (`WITH ranked … WHERE rank = MIN(rank) PARTITION BY book`).

**Why:** Single canonical access point. No behaviour change yet — nothing imports it.

**Pass:** `python3 -c "from calibre_db import *; conn=open_calibre(); print(sum(1 for _ in iter_books_meta(conn)))"` prints `714`; `iter_books_text` prints `703`; `pub_type_filter('monograph, textbook')` returns `True`.

### Step 1b — Multi-format audit query (CLI tool)

**What:** `src/audit_multiformat.py` — reports any book in `books_text` with more than one format row. Output to `data/outputs/multiformat_audit.csv` (book id, formats, text-size delta, text-hash delta).

**Why:** Today a no-op (zero rows). Re-runnable in `run_all.sh` to catch the day a curator adds an EPUB. Makes the format-preference rule's existence visible.

**Pass:** Tool runs, produces empty CSV (only header).

### Step 2 — Parity harness `src/check_db_csv_parity.py`

**What:** For each book ID, fetch text via (a) current CSV path and (b) `calibre_db.iter_books_text`. Compare `len(text)`, first-1000-char hash, last-1000-char hash. Report mismatches. Explicitly verify the format chosen by the DB path matches what the CSV contains (today both are PDF).

**Why:** Establishes byte-equivalence between old and new paths *before* any consumer switches over. Catches CSV-escaping issues (embedded tabs, quoted newlines) up front.

**Pass:** 703 books all match. Any mismatch investigated and resolved before Step 3.

### Step 3 — Rewrite `src/00_export_calibre.py` on `calibre_db.py`

**What:** Replace the 10 ad-hoc SELECTs with one joined query through the module. Output CSV format and column order stay identical.

**Why:** Easiest migration — single-script, deterministic output. Validates the module against a known-good consumer before touching the pipeline.

**Pass:** `diff <(sort csv/books_metadata_full.csv.old) <(sort csv/books_metadata_full.csv.new)` → empty.

### Step 4 — Consolidate the pub-type rule

**What:** Move `_INCLUDE_TYPES` and `_is_included` from `src/03_nlp_pipeline.py:317-335` into `calibre_db.pub_type_filter()`. `03_nlp_pipeline.py` imports it. No change to where the data comes from yet (still CSV).

**Why:** Removes a duplicated rule before it diverges. Tiny, low-risk, easy to revert.

**Pass:** `bash src/run_all.sh` produces the same equivalence-class hash as Step 0 baseline.

### Step 5 — Add `--source {csv,db}` flag to `src/01_parse_books.py`, default `csv`

**What:** With `--source db`, read book IDs and text from `calibre_db.iter_books_text()` instead of `books_text_*.csv`. Metadata still pulled the same way for now.

**Why:** Behind-a-flag toggle means either mode runs cleanly. A/B comparison on one machine without uninstalling either path.

**Pass:** Run both modes; `jq -S 'to_entries | map(.key)' json/books_parsed.json` identical. Per-book `len(text)` within tolerance (small differences may surface if CSV escaping was lossy — investigate before continuing).

### Step 6 — Same flag for `src/parse_and_clean_stream.py`

**What:** `--source db` path streams directly from `iter_books_text()` instead of taking a CSV path argument.

**Why:** Streaming mode is what `run_all.sh --stream` uses for the full corpus — the path that matters for production.

**Pass:** `json/books_clean.json` from both modes have the same book set, same length per book within tolerance.

### Step 7 — Flip `src/run_all.sh` default to `--source db`

**What:** Change `run_all.sh` to call `parse_and_clean_stream.py --source db` (or `01_parse_books.py --source db`). CSV shards still on disk; nothing deletes them. Add `audit_multiformat.py` as a pre-check.

**Why:** First step that changes default behaviour. Easy to revert by flipping the flag back.

**Pass:** Full `run_all.sh` produces an `nlp_results.json` in the same equivalence class as Step 0 baseline. Canonical k=9 names still patch in. Runlog row identical except for `nlp_hash` (fresh run, expected to differ).

### Step 8 — Migrate `src/09_extract_index.py`

**What:** Same `--source {csv,db}` pattern as Step 5. Default to `db` once parity is confirmed.

**Why:** Index extraction is independent of parse/clean. Separating from Step 5/6 keeps each diff reviewable.

**Pass:** `json/index_terms.json` and `json/index_vocab.json` content-equivalent between modes (term lists identical; per-term book counts within tolerance for tokenisation differences).

### Step 9 — Migrate remaining CSV readers

**What:** Switch `src/00_classify_book_styles.py`, `src/00_fetch_anu_primo.py`, `src/00_fetch_worldcat_metadata.py`, `src/diagnose_topic_alignment.py`, and the `src/03_nlp_pipeline.py:319` pub-type read to `calibre_db.iter_books_meta()`.

**Why:** Removes the last live dependencies on the CSV as a source of truth. After this, the CSV is purely a snapshot.

**Pass:** Each script run end-to-end produces output equivalent to its Step 0 baseline. `json/book_styles.json` byte-identical (heuristics deterministic from same input).

### Step 10 — Stop generating `books_text_*.csv`

**What:** Remove `split_books_text.sh` from any orchestration. Move existing CSVs to `csv/_archive/` (or delete after a buffer period). Update `.gitignore` if needed.

**Why:** ~500 MB of redundant on-disk artefacts gone. `run_all.sh` no longer depends on the shard step.

**Pass:** Fresh `run_all.sh` on a machine with no `books_text_*.csv` present succeeds and produces baseline equivalence-class output.

### Step 11 — Demote `books_metadata_full.csv` to a derived snapshot

**What:** Add header comment `# DERIVED FROM metadata.db — do not edit; regenerate via 00_export_calibre.py`. The script becomes an optional dump for git-diff visibility, not a pipeline input.

**Why:** Removes "is the CSV stale?" failure mode. Curator edits to Calibre custom columns become the only source of truth.

**Pass:** Running `00_export_calibre.py` immediately after a Calibre metadata edit produces the expected diff in `csv/books_metadata_full.csv`. Running the pipeline *without* first regenerating the CSV still produces correct output (proving no live dependency remains).

### Step 12 — Cleanup

**What:** Delete `--source` flag branches (DB-only now). Remove `CSV_DIR = _pl.Path('csv')` and `csv.field_size_limit(10_000_000)` lines from scripts that no longer touch CSVs. Update `CLAUDE.md` §Architecture. Update `src/test_pipeline.py:217` to use an in-memory SQLite fixture instead of a synthetic CSV. Log decisions to `docs/decisions.md`.

**Why:** Locks in the new shape. Keeping dead `--source csv` branches indefinitely invites bit-rot.

**Pass:** `grep -r "books_text_.*\.csv" src/` returns nothing. `test_pipeline.py` passes. `run_all.sh` runs to completion. Final equivalence-class hash recorded as the new canonical state.

---

## Cross-cutting notes

- **Rollback:** Steps 5–11 keep the old code path available behind a flag or regeneration command. Any step revertible with a single config change. Step 12 is the point of no return — defer until at least one full pipeline run has shipped on the new path.
- **Commit per step.** Each is a single PR-sized change with one acceptance test. Don't bundle.
- **"Equivalent" means** same book set, same per-book length within ~0.1% tolerance (whitespace handling can differ trivially between CSV and DB paths), same `nlp_results.json` equivalence class, same canonical k=9 names. *Not* byte-identical `nlp_results.json` — LDA seed scheduling can shift hash without changing semantics.
- **Calibre running during pipeline:** `immutable=1` is unsafe if Calibre writes mid-run. Either close Calibre during pipeline execution, or fall back to the existing `shutil.copy` pattern (~30 s cost for the 1.9 GB FTS DB). Document which.
- **The 14-book gap.** Books in `metadata.db` but not in `full-text-search.db` (IDs: 2087, 2174, 2186, 2193, 2239, 2257, 2271, 2283, 2306, 2511, 2517, 2701, 2707, 2716). `iter_books_text` should warn at load time. Curator action: re-run Calibre text extraction.

---

## Post-refactor: EPUB vs PDF comparison

**Premise.** EPUB is structurally a cleaner text source than PDF (HTML in a zip — no layout reconstruction, no header/footer noise, no hyphenation artefacts, no column-order confusion, no OCR substitutions). PDF extraction relies on glyph positioning and inherits all the noise the cleaning pipeline currently exists to suppress.

**Caveats specific to this corpus:**
1. EPUBs converted from PDFs inherit all the PDF errors plus conversion damage. You can't always tell which Calibre has.
2. Many EPUBs lack page numbers entirely — breaks page-anchored citation, relevant to ROADMAP #15.
3. Pre-2000 cybernetics books mostly exist in scanned-PDF form only; EPUB versions when present are often retyped — different text source per book.
4. The cleaning code (`src/02_clean_text.py`, `preprocess_raw_text` in `src/01_parse_books.py`) is tuned to PDF noise. EPUB content passing through may have legitimate structure stripped.
5. **Equivalence-class break.** Mixing formats mid-corpus changes the noise profile per book — different word counts, different vocabulary, different topic loadings. Invalidates canonical k=9 fit.

**Proposed comparison step (separate from the refactor):**

1. Build `src/compare_epub_pdf.py` for the subset of books that have *both* formats available (curator adds EPUBs to ~10–20 sample books in Calibre).
2. Compare on metrics that matter:
   - Vocab size and OOV rate against `index_vocab.json`
   - Hyphenation-fragment count
   - Header/footer leakage rate
   - Per-topic loadings on a single-book LDA fit
3. If EPUB wins clearly and consistently, treat as a separate corpus refresh — a new canonical run with `format_preference=('EPUB','PDF',...)`, recorded as a new equivalence class, re-validated against the multi-rater protocol (current sprint items 3–4). Do not mix formats silently.
4. Books that *only* have EPUB (future additions) use EPUB by definition — the format-preference rule and audit query handle this case already.

---

## Open decisions to log in `docs/decisions.md`

- Format-preference rule: `('PDF', 'EPUB', 'MOBI', 'AZW3')` with rationale (scans dominate today; PDF is the validated source).
- Whether to copy DBs to `/tmp/` per run or rely on `immutable=1` with Calibre closed.
- Whether to keep `books_metadata_full.csv` as a committed git-diff snapshot or remove it entirely after Step 11.
- Disposition of the 14 books missing from `full-text-search.db` — re-extract via Calibre, or formally exclude.
