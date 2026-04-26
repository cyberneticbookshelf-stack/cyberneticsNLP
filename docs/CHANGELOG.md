# Changelog

All notable changes to the CyberneticsNLP pipeline are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Dates are AEST (UTC+11).

---

## [0.5.4] — 2026-04-26

> Session: 26 April 2026 (Cowork) — reader's guide suite completed; HTML reports rebuilt; presentation patched to 26 April taxonomy.

### Added

- **`data/outputs/book_nlp_cosine_guide.html`** — new reader's guide for the Cosine Similarity page (`cosine.html`). Covers plain-language overview of the three views (cluster averages, full matrix, top pairs), interpretation guidance (vocabulary similarity ≠ intellectual proximity), TF-IDF cosine formula, and per-view construction details. Guide link auto-injected into `cosine.html` nav by `06_build_report.py` (rerun required, completed this session).
- **`data/outputs/book_nlp_clusters_guide.html`** — new reader's guide for the Clusters page (`clusters.html`). Covers the LSA 2D scatter and K-Means cluster table; the LDA topics vs K-Means clusters distinction (soft mixture vs hard partition, different input matrices — CountVectorizer for LDA, TF-IDF for K-Means); and the low silhouette scores (0.004–0.022) confirming no statistically valid hard cluster structure. Includes full K-Means inertia/silhouette table (k=2–9, current run).
- **`data/outputs/book_nlp_keyphrases_guide.html`** — new reader's guide for the Key Phrases page (`keyphrases.html`). Covers per-book TF-IDF keyphrase extraction (distinct from corpus-wide topic words), Fig 7 construction (pooling keyphrases by dominant topic), search/filter usage, and interpretive traps (proper nouns, register phrases, OCR-inflated n-grams, keyphrases ≠ argument summaries). Technical appendix: `extract_keyphrases()` parameters (`max_features=500`, `ngram_range=(1,3)`, 4-char minimum tokens).

### Fixed

- **`data/outputs/book_nlp_index_guide.html`** — updated throughout for the 26 April 2026 full-text canonical run (`run_20260426_k9_s5`). Changes: (1) topic stability table updated — 9 new names + current scores (T1 0.261 moderate, T2 0.441 stable, T3 0.512 stable, T4 0.529 stable, T5 0.178 moderate, T6 0.458 stable, T7 0.045 unstable, T8 0.287 moderate, T9 0.421 stable; mean 0.348); (2) `max_iter` corrected 20 → 100; (3) perplexity/coherence table replaced with live full-text sweep values (k=9: perplexity 3650.7, coherence 0.0780 — values are higher than the prior sampled-run table because full-body text contributes substantially more words per document); (4) stability counts corrected: "Six of nine stable, T1/T2/T9 moderate" → "Five stable, three moderate (T1/T5/T8), T7 unstable"; (5) T9 "Residual / Outlier Cluster" caveat paragraph removed and replaced with T7 instability caveat; (6) footer date updated.
- **`presentation/patch_deck.py`** — updated to apply 26 April 2026 canonical facts. Changes: (1) `CANONICAL_NAMES` block updated to finalised 26 April taxonomy with position-indexed comments and safety note re "Extensions of Cybernetics" T3↔T9 name collision; (2) `edit_slide_11()` — stability figures corrected from stale 0.357/9/9 (prior patch run) to 0.348/5/9 with T7 unstable; LDA input description fixed from "abstractive summaries (not raw text)" → "full body text, front/back matter stripped (--full-text)" (abstractive summaries are NMF input only); (3) `edit_slide_14()` — era heading renames: "Fragmentation & Specialisation" → "Cybernetics at Social Scale" (Beer/VSM + Luhmann scope); "Expansion & Revival" → "Diffusion and Injection"; dominant-topic attributions remapped to 26 April topic positions; (4) `edit_slide_23()` — "Phase 2 — Analysis" column header renamed to "Possible Extensions".

### Documentation

- **`docs/ROADMAP.md`** — two new known-issue entries: KI-10 (stability band thresholds inconsistent between `log_pipeline_run.py` and `09c_validate_topics.py` — same `topic_stability.json`, conflicting stable/moderate/unstable counts; centralise thresholds post-presentation); KI-11 (release HTMLs reflect rebuild run nlp_hash `c8e3c71bf8a3d910`, not logged canonical run `901e5ec924248fe2`; same equivalence class; survey workflow unaffected; proposes `--mark-as-release` flag for `log_pipeline_run.py`).
- **`CyberneticsNLP.md`** (vault) — sprint checklist updated (run_all ✓, deck patch ✓, provenance refresh ✓; spot-check and final review pass deferred to next session); session log row added for 26 April v0.5.4 session.

---

## [0.5.3] — 2026-04-25

> Sessions: 25 April 2026 (Cowork) — canonical run definition corrected; first genuine full-text run executed.
> 26 April 2026 (Cowork) — topic naming finalised by Paul Wong; canonical run logged; ⚑ flag cleared.

### Fixed

- **`src/run_all.sh`** — canonical `03_nlp_pipeline.py` invocation corrected to include `--full-text --max-features 15000 --gpu`. Prior canonical runs (including the April 18 run, `pipeline_mode: sampled, max_features: 3000`) are rejected as non-genuine canonical runs — they used default sampling mode rather than the full-body text mode that validated k=9 (Run C, 14 April). The April 25 run is the first genuine canonical run under this definition.
- **`src/run_all.sh`** — restore-canonical comment updated to match.
- **`CLAUDE.md`** — canonical k line and restore command updated to include `--full-text --max-features 15000`.
- **`src/03_nlp_pipeline.py`** — canonical LDA seed unified at `_CANONICAL_LDA_SEED = 42` (ROADMAP #26 surgical fix). Previously the canonical fit producing `top_words` and `doc_topic` for `nlp_results.json` ran at `random_state=99`, while `topic_stability.canonical_words` came from `SEEDS[0]=42` in the stability sweep — two unrelated topic-index frames. `09c_validate_topics.py` paired them by index `t` and silently mis-aligned topics with top books across frames. Diagnosis (`src/diagnose_topic_alignment.py`, 25 April 2026): test C(i) PASS, test C(ii)+D FAIL — even after Hungarian permutation (mean Jaccard 0.374), per-topic top-10-book overlap was 0–7/10 across 9 topics. Cause: cross-fit `doc_topic` is fundamentally unstable across seeds; β converges enough to share top words but θ diverges. Fix: change `random_state=99` → `42` in three places: (a) k-selection scoring loop (line 695), (b) `_fit_lda_gpu` default (line 734), (c) sklearn fallback paths (lines 782, 787). At the same seed and backend, the canonical fit and seed-42 sweep worker produce equivalent components by construction. Result: `top_words ≡ canonical_words`; `doc_topic` is in the same frame; `09c_validate_topics.py` outputs become coherent without modification. The redundant LDA fit is preserved for now (one wasted fit's worth of cost); a future refactor (ROADMAP #26 follow-up) will capture seed-42 state from the sweep workers and skip the canonical fit entirely. Diagnostic outputs preserved at `json/topic_alignment_diagnostic.json` and `data/outputs/topic_alignment_diagnostic.md`.
- **`docs/methodology.md`** — added section "LDA topics as discursive registers, not subject domains" (between "Residual error propagation" and Section 24). States the reframe (LDA finds vocabulary co-occurrence patterns, not themes), uses the 21-book PCT scatter as worked example (T5 ×8, T6 ×5, T8 ×4, T3 ×3, T4 ×1, T7 ×0), three implications for interpretation (read names as registers; prefer doc-topic distributions over argmax; cross-cutting programmes invisible to LDA), and frames PCT as second worked instance of the standing principle of context (parallel to "University of California" — strings → vocabulary, same structural property).
- **`src/09c_validate_topics.py` + `src/patch_topic_names.py`** — fixed 09c clobber bug (ROADMAP #27). Symptom: after a full pipeline run, `data/outputs/topic_validation.md` showed `*(to be named)*` for every topic despite `patch_topic_names.py` reporting "Updated 9/9 topics". Cause: 09c regenerates `topic_validation.json` from scratch with hardcoded `'proposed_name': ''` and `'notes': ''`, and runs **after** patch_topic_names in `run_all.sh`, silently overwriting what patch_topic_names wrote. Cosmetic-only — names were correctly carried in `nlp_results.json` so HTML/Excel reports were unaffected. Fix: 09c now reads `topic_names` and `topic_notes` from `nlp_results.json` and overlays them as defaults for `proposed_name`/`notes` (graceful degradation to empty strings if absent — preserves the original manual-edit workflow). `patch_topic_names.py` extended to write `topic_notes` alongside `topic_names`. Trailing instructions in 09c updated to reflect the canonical naming workflow (edit TAXONOMY → rerun) rather than the deprecated manual-edit-JSON path.
- **`src/patch_topic_names.py`** — TAXONOMY block replaced with 9 finalised topic names from the 25 April full-text canonical run: T1 Classical cybernetics history/historiography; T2 Techno-political complexes; T3 Engineering control; T4 Systems theory & Viable Systems Model; T5 Formal foundations of cybernetics; T6 Reinvention of self and others; T7 Psychological regulation and control; T8 Biological & neural cybernetics; T9 Ecology and posthuman technologies. Notes scoped to discursive-register reframe; per-topic stability scores intentionally omitted (fetched from `topic_stability.json` per session). T9 is no longer "Residual / Outlier Cluster" — under full-text mode the position carries coherent ecological/posthuman content. T7 explicitly notes that PCT does NOT anchor here despite the topic name suggesting it should — a methodological feature, not a defect.
- **`src/patch_topic_names.py`** — TAXONOMY names revised by Paul Wong (26 April 2026) following review of the 25 April full-text canonical run. Final names: T1 History and Historiography of Cybernetics; T2 Techno-political Complexes; T3 Engineering Control; T4 Social and Organisational Cybernetics (Beer/VSM as recursive organisational model + Luhmann's broader social-institutions scope); T5 Formal Foundations of Cybernetics; T6 Reinventing Selves and Others, Past and Future; T7 Psychological and Behavioural Regulation and Control; T8 Biological and Neural Cybernetics; T9 Extensions of Cybernetics (replaces interim "Ecology, Posthumanism and Digital Ontology" — broader framing accommodates ecology, posthumanism, second-order cybernetics, digital ontology, and other extension paths rather than naming three specific extensions). T9 notes rewritten to reflect the broader framing. Capitalisation normalised across all 9. **Note:** "Extensions of Cybernetics" was the T3 name in the pre-25-April sampled-run taxonomy; same name now occupies a different topic position under the full-text canonical fit. Downstream consumers holding old runlogs/cached HTML/prior drafts should not treat the name as identifying the same cluster across runs.
- **`README.md`** — stale topic-name table (lines 350–363, pre-25-April taxonomy) replaced with a pointer block referencing `json/nlp_results.json['topic_names']`, `src/patch_topic_names.py` TAXONOMY, and `data/outputs/topic_validation.md` as authoritative sources. Stops the README rotting on every re-naming; consistent with "don't rely on hardcoded figures here — they rot" (CLAUDE.md project snapshot). Chapter-level NMF table retained (those names have not shifted).

### Added

- **`src/03_nlp_pipeline.py`** — multi-GPU parallel seeds in `run_stability_analysis()`. New `_fit_one_seed()` worker function pins each seed run to a specific GPU via `CUDA_VISIBLE_DEVICES` and runs in a subprocess. `_detect_gpu_count()` queries `nvidia-smi` at runtime. When `--gpu` is active and ≥2 GPUs are available, seeds are dispatched across GPUs in parallel using `ProcessPoolExecutor` (up to `min(n_seeds, n_gpus)` workers) — collapsing a 5-seed run on the 5× RTX 3090 server from 5× to ~1× single-model time. Falls back gracefully to sequential single-GPU or CPU if cuML is unavailable. The `--gpu` flag also added to the canonical `run_all.sh` invocation.

- **`data/outputs/book_nlp_index_guide.html`** — new reader's guide for the Topic Modelling page (`index.html`), parallel to the entity network guide. Covers plain-language overview, how to read each figure, caveats and limitations, and a technical appendix (corpus, preprocessing, vectorisation, LDA fitting, stability, k-selection, topic naming). Guide link auto-injected into `index.html` nav by `src/06_build_report.py` (mechanism already present; link appears on next pipeline run).
- **`presentation/patch_deck.py`** — idempotent script applying v0.5.1 canonical facts to `CyberneticsNLP_Talk_v2.pptx` → `CyberneticsNLP_Talk_v3.pptx`. Committed as provenance record.

### Documentation

- **`docs/decisions.md`** — two new entries prepended: (1) canonical run requires `--full-text --max-features 15000` (with rejection of April 18 run); (2) T9 "Residual / Outlier Cluster" rationale; (3) inclusion vs exclusion semantics for non-disjoint labels.
- **`docs/` reorganisation** — research memos moved to `docs/memos/`; project-specific reference docs to `docs/reference/`; one historical snapshot to `docs/archive/`. Transcript dumps and superseded files retired.

### Pending (complete before removing ⚑ flag)

- [x] `run_all.sh` rerun complete on NLP machine (started 25 April 2026; canonical runlog `data/outputs/runlog20260425-5.csv` finalised 26 April 00:47 AEST)
- [x] Topic structure reviewed by Paul Wong against full-text solution
- [x] k=9 confirmed as still appropriate for full-text corpus (26 April 2026)
- [x] Topic names re-validated by Paul Wong, 26 April 2026 — still provisional pending ≥3 runs × ≥2 raters for stable names; this satisfies the post-run validation block in CLAUDE.md but not the multi-rater stability criterion in sprint item 4
- [x] Run logged via `log_pipeline_run.py` as `run_20260426_k9_s5`, equivalence class `23b29233a67b2938`, nlp_hash `901e5ec924248fe2`, 2368 runlog lines ingested. **Recovery note:** initial logging defaulted to today's filename and missed the runlog at `runlog20260425-5.csv` (canonical run started 25 April, 5th of the day, completed 26 April 00:47 AEST). The `nlp_hash` short-circuit at `src/log_pipeline_run.py:287` returned "Nothing to do" on rerun, so recovery required `sqlite3 ... DELETE FROM pipeline_runs WHERE run_id='run_20260426_k9_s5'` followed by re-run with explicit `--runlog`. Logged as ROADMAP entry: `log_pipeline_run.py` should ingest the runlog into an existing row when `runlog_entries` count is zero, rather than terminating on `nlp_hash` match.
- [x] `contributions.md` updated with 26 April session row; `CLAUDE.md` post-run validation block removed (no longer applicable). Master project doc (`02 Projects/CyberneticsNLP/CyberneticsNLP.md` in vault) needs separate update — outside the repo mount, handled by user.

---

## [0.5.2] — 2026-04-25

> Session: 25 April 2026 (Cowork/Chat) — docs reorganisation, retire stale outputs, presentation refresh

*(See v0.5.3 above for full context of this session's changes.)*

---

## [0.5.1] — 2026-04-23

> Session: 23 April 2026 (Cowork) — documentation maintenance; entity network noise suppression

### Fixed

- **`src/14_entity_network.py`** — four fixes applied:
  1. **`NOISE_TERMS` extended** with three new groups: (a) generic academic words (`work`, `project`, `study`, `result`, `analysis`, `research`, `approach`, `method`, `use`, `problem`, `process`, `example`, `case`, `form`, `type`, `term`, `role`, `way`, and plurals) — eliminates high-frequency but non-associative concept nodes appearing in Wiener's neighbourhood; (b) OCR line-break suffix fragments (`tion`, `sion`, `ence`, `ance`, `ment`, `ness`, `ism`, `ity`, `ing`, `tems`, `ther`, `ters`, `tions`) — these appear capitalised in the index as standalone entries because hyphenated words split across a line leave the suffix as a new "word"; (c) function words that survived upstream filters (`this`, `that`, `these`, `those`, `there`, `their`, `they`, `with`, `from`, `also`, `been`, `have`, `were`, `will`).
  2. **`_LDA_BASE` fallback** updated from Run A/B names to 18 April 2026 taxonomy (T1–T9 in correct topic order). Fallback only — live names always come from `R['topic_names']` in `nlp_results.json`.
  3. **Methodological note**: corpus count corrected 542 → 541.
  4. **Duplicate `<div id="stats_panel">`**: removed second dead copy of the stats panel HTML element.

### Network (standalone rerun of step 14 only — 23 April 2026)

| Metric | Previous canonical (18 Apr) | This rerun (23 Apr) |
|--------|----------------------------|----------------------|
| Nodes | 1,638 | 1,604 |
| Persons | 656 | 657 |
| Concepts | 758 | 722 |
| Orgs | 154 | 154 |
| Locations | 70 | 71 |
| Edges (total) | 11,563 | 11,644 |
| Book edges | 10,362 | 10,468 |
| Para edges | 1,201 | 1,176 |
| Density | 0.009 | 0.009057 |
| LCC | 1,636/1,638 | 1,602/1,604 |
| APL | 3.27 | 3.2 |
| Diameter | 6 | 6 |

LDA topic stats unchanged (from `runlog20260418-3.csv` canonical run). Full `run_all.sh` rerun required to make this the committed canonical state.

### Documentation

- **`CLAUDE.md`** — security principle applied throughout: machine names, SSH username/hostname, email address, and Google Form ID replaced with generic descriptions. Mapping from placeholder to actual value moved to `csv/infrastructure.csv` (gitignored). Pointer to lookup file added to infrastructure notes section. Numbering error in next session agenda fixed.
- **`README.md`** — multiple updates: corpus framing corrected (695 in collection / 541 analysed); canonical run header updated to v0.5.0 / 18 April / 9/9 stable / mean stability=0.357; output file table restructured into four groups (book-level split, book-level other, chapter-level not yet refactored, Excel); `books.html` excluded from release with 60k token sampling explanation; chapter-level pipeline flagged as not yet refactored throughout; step 4 summary generation caveat added; `nlp_results.json` description updated; `726 books` → `695` in input data format; security fixes matching CLAUDE.md principle.
- **`csv/infrastructure.csv`** — new gitignored file mapping all generic placeholders in `CLAUDE.md` and `README.md` to their actual values.

---

## [0.5.0] — 2026-04-21

> Session: 21 April 2026 (Cowork) — Google Forms survey infrastructure; pipeline.db refactor

### Added

- **`src/pipeline_db.py`** — central shared DB module. Defines `DB_PATH = data/pipeline.db` (replacing `topic_naming.db`). Full schema for 8 tables: `equivalence_classes`, `pipeline_runs`, `runlog_entries`, `naming_sessions`, `topic_ratings`, `google_form_configs`, `google_form_responses`. Key functions: `open_db()` (creates all tables on first call), `compute_file_hash(path, prefix_len=16)` (SHA-256 hex of file contents, first 16 chars), `compute_run_hash(k, n_books, max_features, pipeline_mode, seeds_used, prefix_len=16)` (SHA-256 of canonical JSON of input parameters — defines an equivalence class), `find_run_by_nlp_hash(nlp_hash, db_path)` (look up a run by its nlp_results.json hash).

  **Schema highlights:**
  - `equivalence_classes` — groups runs sharing identical input parameters; `run_hash` is the key
  - `pipeline_runs` — one row per logged run; includes `nlp_hash` (hash of `nlp_results.json` contents), `run_hash` (FK to equivalence_classes), `is_test` flag (test runs cannot be surveyed), and full LDA params blob
  - `runlog_entries` — structured log lines from `data/outputs/runlogYYYYMMDD.csv`, linked to `pipeline_runs`
  - `google_form_configs` — one row per created Google Form; stores `form_id`, `run_id`, `share_url`, `question_id_map` (JSON), `topic_meta` (JSON)
  - `google_form_responses` — response deduplication table; `response_id` (Google's ID) is unique

- **`src/log_pipeline_run.py`** — manual run logging tool. Reads `nlp_results.json`, computes `nlp_hash` and `run_hash`, finds or creates the equivalence class, and inserts the run into `pipeline_runs`. Interactive: shows equivalence class status and sibling runs; prompts for `run_id` (default: `run_YYYYMMDD_k{k}_s{seeds}`), notes, and confirmation. `--yes` flag bypasses confirmation. `--test` marks run as `is_test=1` (survey-ineligible). Auto-detects and ingests the most recent runlog CSV into `runlog_entries`. Commands: `--list` (all runs), `--list-classes` (equivalence classes), `--show RUN_ID`.

  **Design principle:** A run must be manually logged — and must not be a test run — before a Google Form can be generated. This ensures the survey is always tied to a specific, reviewed pipeline run with a known identity.

- **`src/migrate_pipeline_db.py`** — one-shot migration from `data/topic_naming.db` (old schema) to `data/pipeline.db` (new schema). Reads the old `runs`, `naming_sessions`, and `topic_ratings` tables and ports them. Each migrated run has `nlp_hash=""` (unknown — the original `nlp_results.json` may have changed since the run). Computes `run_hash` for each old run, creates `equivalence_classes` rows. `--dry-run` flag.

- **`src/get_google_token.py`** — one-time OAuth token generator. Reads `credentials.json`, calls `flow.run_local_server(port=0)`, saves `token.json` to the project root. Run on a machine with a browser (e.g. via sshfs mount). `--creds` and `--out` flags for custom paths. Scopes: `forms.body`, `forms.responses.readonly`, `drive.file`. This is the recommended one-time setup path.

- **`src/generate_google_form.py`** — **fully rewritten** (previously a stub). Creates a Google Form from the current `nlp_results.json`. Pre-flight: computes `nlp_hash`, calls `find_run_by_nlp_hash()`, errors if the run is not logged or is a test run. Checks for an existing form for the same run (warns unless `--force`). OAuth via `token.json` (written by `get_google_token.py`). Form structure: title, description, rater (required), session notes, then per-topic blocks (stability score, canonical top words, stable core words, top 8 books with loading/author/year) followed by name, confidence (radio: high/medium/low), and notes fields — 39 `batchUpdate` items. Writes form config to `google_form_configs`.

- **`src/ingest_google_responses.py`** — fetches all responses from a Google Form and inserts new submissions into `naming_sessions`, `topic_ratings`, and `google_form_responses`. Reads form config from `google_form_configs` table. `fetch_responses()` paginates the Google Forms API. `parse_response()` extracts rater, session notes, and per-topic name/confidence/notes using `question_id_map`. `ingest_response()` deduplicates by `response_id`. Fully idempotent. `--dry-run` flag. `--list-forms` command. `--form FORM_ID` and `--run RUN_ID` flags to target a specific form; defaults to the most recently created.

### Changed

- **`src/record_topic_run.py`** — refactored to use `pipeline_db`. Local imports of `DB_PATH`, `SCHEMA`, and `open_db` replaced with `from pipeline_db import DB_PATH, open_db, compute_file_hash`. `_save()` now computes `nlp_hash`, looks up the run in `pipeline_runs WHERE nlp_hash = ?`, and errors if the run is not logged or is `is_test=1`. Export query updated to join `pipeline_runs`. Local HTTP server mode unchanged.

- **`src/run_all.sh`** — `--test` flag added (alongside existing `--stream`). Test runs: runlog named `runlogYYYYMMDD_test.csv` (collision-safe suffixes). A `⚠ TEST RUN` banner is printed after the mode line. Completion message: canonical runs print the `python src/log_pipeline_run.py` reminder; test runs print a clear non-eligible warning.

### Infrastructure

- **`data/pipeline.db`** replaces `data/topic_naming.db`. Old three-table schema (`runs`, `naming_sessions`, `topic_ratings`) expanded to 8 tables. Migrate with `python src/migrate_pipeline_db.py`. All scripts updated to import from `pipeline_db.py`.

- **Google OAuth:** `credentials.json` (Desktop app OAuth) is in the project root (gitignored). `token.json` is generated once via `get_google_token.py` on a machine with a browser. Both scripts share identical scopes so the token works for `generate_google_form.py` and `ingest_google_responses.py` without re-authentication.

- **Equivalence classes:** Two runs are in the same equivalence class if they share `k`, `n_books`, `max_features`, `pipeline_mode`, and `seeds_used`. `run_hash = SHA-256(16)` of the canonical JSON of these five parameters. Within an equivalence class, topic ordering may differ between runs (LDA is non-deterministic); surveys are compared across runs in the same class using topic alignment (Hungarian algorithm). Forms are created per-run, not per equivalence class.

### Status

First live form: `CyberneticsNLP — Topic Naming (2026-04-21)` — Form ID recorded in `data/pipeline.db` (`google_form_configs` table). Run: `run_20260421_k9_s5`, equivalence class `0ab6e3f8ba95d0d0`. Form confirmed live. Responses disabled pending further testing.

---

## [0.4.7] — 2026-04-20

> Session: 18–20 April 2026 (Cowork) — fifth batch

### Added

- **`src/record_topic_run.py`** — topic naming server (graduated from `docs/src_draft/`). Three modes:
  - **Server mode** (default): `python src/record_topic_run.py` → http://localhost:7474. Exposes an HTML naming form; submissions stored in SQLite. Share with remote raters via SSH tunnel or tunnel service (e.g. ngrok).
  - **Offline mode** (`--generate`): produces a self-contained 108 KB HTML file; rater fills in locally, downloads a JSON, returns it.
  - **Ingest mode** (`--ingest rater_file.json`): inserts an offline JSON response into the DB; duplicate-safe.
  
  SQLite database: `data/topic_naming.db` (three tables: `runs`, `naming_sessions`, `topic_ratings`). Captures: rater, confidence (high/medium/low), per-topic notes, stability score, top words, top books, and a full LDA parameter blob. `--test` flag: form live but nothing written to DB. `--query` and `--export json/csv` modes for review.
  
  **First live test:** 20 April 2026 — server run on the NLP machine, SSH tunnel established, test naming session submitted by Paul W (run_20260420_k9_s5, 9 topic names saved).

- **`src/check_stale_vars.py`** — new utility to detect and auto-fix stale hardcoded fallback variables across all pipeline scripts. Three checks:
  1. `_LDA_BASE` lists in 8 scripts (`06_build_report.py`, `08_build_timeseries.py`, `09b_build_index_analysis.py`, `10_build_index_report.py`, `11_embedding_comparison.py`, `12_index_grounding.py`, `13_weighted_comparison.py`, `14_entity_network.py`) compared against `json/nlp_results.json['topic_names']` (canonical source); `--fix` mode auto-updates stale lists using a line-scanner (`replace_lda_base()`) rather than `re.sub()` — avoids backslash mangling of Python string literals.
  2. `patch_topic_names.py` TAXONOMY cross-consistency (report only, not auto-fixed — TAXONOMY is authoritative).
  3. Hardcoded corpus-count literals in HTML template scripts (flagged for manual fix).
  
  First run: 7 stale scripts fixed, 1 already current, TAXONOMY consistent. Integrated into `run_all.sh` directly after `patch_topic_names.py` so every pipeline run auto-fixes stale fallbacks.

- **`src/run_all.sh` — automatic runlog generation**: all pipeline stdout/stderr now captured to `data/outputs/runlogYYYYMMDD.csv` via `exec > >(tee "$RUNLOG") 2>&1`. Collision-safe: if a log for the current date exists, appends `-2`, `-3`, etc. Runlog path echoed in the pipeline completion summary.

### Fixed

- **`src/03_nlp_pipeline.py` — contraction stems missing from STOPWORDS**: 13 stems added — `aren, couldn, didn, doesn, hadn, hasn, haven, mustn, shan, shouldn, wasn, weren, wouldn`. Root cause: sklearn's built-in stop list includes full contracted forms (`"aren't"`, `"couldn't"`, etc.) but the pipeline's lemmatiser strips the `"'t"` suffix before CountVectorizer tokenises, producing bare stems that bypass the stop list and inflate TF-IDF scores.

- **`src/06_build_report.py` — cosine section hardcoded counts**: both `542 × 542` literals replaced with `{len(book_ids)} × {len(book_ids)}` — in the dropdown `<option>` label and in the figure caption. Count now updates automatically on each run without manual patching.

- **`src/06_build_report.py` — clusters caveat box**: yellow interpretive warning inserted before the cluster table in `_content_clusters`. States: (a) silhouette scores all 0.013–0.021 across k=2–9 — no statistically valid cluster structure in the high-dimensional space; (b) clusters are exploratory partitions only; (c) a rerun of `run_all.sh` may produce a different k or different cluster assignments. Uses `{best_k}` so the current run's k is always quoted accurately.

- **`src/06_build_report.py` — nav tab "Summaries" → "Network"**: `_PAGES` entry changed from `('books.html', '📝 Summaries')` to `('book_nlp_entity_network.html', '🕸 Network')`. All four release-scope pages (`index.html`, `cosine.html`, `clusters.html`, `keyphrases.html`) will link to the entity network report on next rerun. Summaries page remains in the source but is not in the current release scope; manually edited HTML nav tabs will be correctly regenerated by `run_all.sh`.

- **`figures/fig7_keyphrases.png` — stale topic names**: regenerated from `json/nlp_results.json` with 18 April 2026 canonical taxonomy. Previous chart displayed Run C / 14 April names (e.g. "History and Biography of Cybernetics" for T1, "Cybernetics of Psychology" for T2). `data/outputs/keyphrases.html` also repaired — was blank after a write error during an earlier direct-edit attempt; reconstructed by running `06_build_report.py` from sandbox.

### Changed

- **`src/run_all.sh` — `09c_validate_topics.py` sequencing**: moved from immediately after `03_nlp_pipeline.py` to after `patch_topic_names.py` and `check_stale_vars.py --fix`. Previously `09c` wrote `docs/topic_validation.md` using raw LDA ordering labels (T1…T9 integers); it now writes with agreed canonical names. Comment block updated to explain the dependency.

### Fixed — Entity network: singular/plural concept node deduplication (KI-09)

**`src/14_entity_network.py`**

Index vocabularies routinely contain both singular and plural forms of the same
concept (algorithm/algorithms, network/networks, feedback loop/feedback loops).
Treating them as separate nodes splits their PMI signal: books indexed under the
plural form do not contribute to the singular node's book-set, artificially
weakening edge weights for both nodes.

**New components:**

- `_CONCEPT_PLURAL_EXCEPTIONS` — set of 35 discipline/field names ending in
  `-ics` (`cybernetics`, `thermodynamics`, `semantics`, `dynamics`, `linguistics`,
  etc.) that are NOT grammatical plurals of their adjectival `-ic` forms. Genuine
  count-noun plurals ending in `-ics` (e.g. `topics → topic`) are absent from
  this list and merge normally.

- `_singular_form(tl)` — derives the candidate singular form of a term-lower key.
  Five morphological rules: `-ies → -y` (theories→theory), `-ses/-xes/-zes → drop
  -es` (processes→process), `-ches/-shes → drop -es` (approaches→approach),
  simple `-s → drop` (algorithms→algorithm), multi-word recursion on last word
  (feedback loops→feedback loop, Turing machines→Turing machine). Returns `None`
  for any term in `_CONCEPT_PLURAL_EXCEPTIONS`.

- `concept_plural_map` — built after concept classification: `{plural_tl:
  singular_tl}` for all pairs where both forms survive as concept nodes. Plurals
  removed from `concepts` dict before book-set construction.

- Book-set union — after `concept_booksets` is built, each plural's book-set is
  unioned into its canonical singular's set. `vocab[sing_tl]['n_books']` updated
  to the union size so HTML node labels show the correct merged book count.

- Paragraph-window normalisation — `target_tls` filter extended to include terms
  in `concept_plural_map`; each term mapped to its canonical form before passing
  to `para_cooccur`. `dict.fromkeys` deduplication prevents double-counting when
  a book indexes both singular and plural forms.

**Conservative by design:** the merge only fires when BOTH the plural and the
singular are independently present as concept nodes after all upstream filters
(NOISE_TERMS, KNOWN_TECH_PLATFORMS, `_TRAILING_FUNC`, cache suppression, etc.).
No merge is inferred — every pair is confirmed by presence in the data.

**Expected impact on rerun:** concept node count will decrease (duplicate plurals
removed); PMI edge weights for high-frequency concepts will increase (fuller
book-set unions); network topology otherwise unchanged.

### Fixed — `09_extract_index.py`: systematic lowercasing of multi-word proper names containing English function words

**`src/09_extract_index.py` — `_canonical_term()` bug** (v0.4.7, 20 April 2026)

`_canonical_term()` preserves a multi-word term as-is only when every word passes the
`_ok()` well-formedness check. Previously `_ok()` recognised: name particles (`von`,
`de`, `van`…), short all-caps acronyms (≤ 5 chars), and title-case words — but it did
not recognise English function words that are legitimately lowercase in title-case
proper nouns. Any multi-word proper name containing `in`, `and`, `of`, `the`, `from`,
`on`, `by`, `at`, etc. therefore failed the well-formedness check and was lowercased
wholesale.

**Affected terms (examples):** `Experiments in Art and Technology`, `Laws of Form`,
`Order from Noise`, `Macy Conferences on Cybernetics`, `Society for General Systems
Research`, `Towards a Systems Theory`, `Journal of Theoretical Biology`.

**Three changes applied:**

1. **`LOWER_IN_TITLE` set** added inside `_canonical_term()` — articles (`a`, `an`,
   `the`), coordinating conjunctions (`and`, `but`, `or`, `nor`, `for`, `yet`, `so`),
   and common prepositions (`in`, `on`, `at`, `to`, `of`, `by`, `from`, `with`, `as`,
   `into`, `about`, `over`, `under`, `between`, `among`, `through`, `its`, `their`).
   `_ok()` updated to return `True` for any word in this set, so well-formedness check
   now correctly passes title-case proper nouns containing these words.

2. **All-caps OCR pre-processing** — before the `_ok()` loop, if ALL alpha characters
   in the input are uppercase AND at least one word has more than 3 alpha characters
   (distinguishing real words from acronym sequences like `DNA RNA`), the string is
   lowercased before canonical processing. Fixes OCR artefacts such as `LAWS OF FORM`
   (previously preserved unchanged because every word passed the ≤ 5-char acronym
   guard) → `laws of form`.

3. **"Best casing wins" in vocab builder** — when accumulating `all_terms` from
   across all books, if a term is already stored in all-lowercase form and a later
   book supplies a mixed-case form, the stored entry is upgraded to the better-cased
   version. Handles the case where the first book to index a term happened to render
   it in lowercase or all-caps (which `_canonical_term()` lowercases), while a later
   book provides the properly title-cased form.

**Verification:** 22/22 tests pass including all pre-existing behaviours:
`Experiments in Art and Technology` preserved ✓, `Laws of Form` preserved ✓,
`LAWS OF FORM` → `laws of form` ✓, `DNA RNA` preserved as-is ✓,
`cybernetics` → `Cybernetics` ✓, `von Neumann` preserved ✓.

**Pipeline impact:** `index_terms.json` and `index_vocab.json` must be regenerated.
Rebuild required from step 09 onwards (`09_extract_index.py` → `09b` → `09c` → `10`
→ `12` → `14` → `15`, or full `run_all.sh`).

### Status

All source-level fixes applied for the five release-targeted HTML files (`index.html`, `cosine.html`, `clusters.html`, `keyphrases.html`, `book_nlp_entity_network.html`) and for `09_extract_index.py`. Full rerun of `run_all.sh` required to regenerate all outputs from updated sources.

**Naming server deployment — superseded.** Interim SSH-tunnel deployment tested successfully 20 April 2026 (Paul W, run_20260420_k9_s5, 9 topics). Self-hosted permanent deployment was blocked by ISP port restrictions; replaced by Google Forms in v0.5.0 (see decisions.md).

---

## [0.4.6] — 2026-04-18

> Session: 18 April 2026 (Cowork) — fourth batch

### Fixed — Entity network HTML: four bugs repaired, release-ready

**`src/14_entity_network.py`**

1. **Provenance notice covers header (ROADMAP #17)** — `position:fixed;top:0` overlay does not
   work with the network viewer's full-viewport flex layout; `body{padding-top:54px}` does not
   push flex children down. Fixed: `_PROV_NOTICE` changed to a `flex-shrink:0` static element
   injected before `<div class="header">` rather than before `</body>`. Amber banner now appears
   above the toolbar without obscuring it. Verified.

2. **p99 degree filter always showing all nodes (ROADMAP #18)** — `'p99'` was present in the
   dropdown but absent from the `_deg_percentiles` dict passed to `STATS`. JavaScript
   `STATS.deg_percentiles?.['p99']` returned `undefined`, fell through `|| 0`, setting threshold
   to 0 (show all). Fixed: added `'p99': float(_np.percentile(_degs, 99))` to `_deg_percentiles`.
   p99 threshold = 114.6 (degree ≥ 115). Verified.

3. **Degree filter not applied to node set; orphan nodes shown at high thresholds (ROADMAP #19)**
   — Two bugs: (a) `filterGraph()` else-branch set `activeNodes = new Set(NODES.map(n=>n.id))`
   (all nodes), completely discarding the correctly-built `allowedNodes`; (b) nodes whose
   neighbours all fall below the threshold appeared as isolated orphans, degrading ink-to-signal
   ratio. Fixed: (a) else-branch now uses `activeNodes = allowedNodes`; (b) when `degThresh > 0`,
   a second pass builds `connectedIds` from `activeEdges` and removes any node with no remaining
   edge. Reflects hub-and-spoke topology: hubs connect primarily to peripheral nodes, not to each
   other. Node sizes unchanged — orphan removal affects only render set, not the degree value that
   determines node radius. Requires rerun.

4. **Reader's guide link added to header** — `📖 Reader's guide` anchor linking to
   `book_nlp_entity_network_guide.html` injected into the header div alongside the title.
   Requires rerun.

### Added

- **`data/outputs/book_nlp_entity_network_guide.html`** — new standalone explanatory document
  for colleagues and public viewers. Plain-language overview and technical appendix covering:
  node kinds and colour coding, edge semantics (book-level PMI × reliability), all 7 interactive
  filters (Search, Show/hide, Min weight, Charge, Min degree, Level, Layout) with interpretive
  guidance, four layout algorithms with amber "Layout is not data" callout (algorithmic layout has
  no 1-to-1 correspondence with network features), hub-and-spoke topology explanation, corpus
  scope and exclusions (541 books), entity extraction pipeline summary, node counts table,
  PMI formula, network statistics table, and filter mechanics. Linked from network viewer header.
  Back-link to network viewer included. Provenance notice consistent with all report HTML.

### Documentation

- **`docs/ROADMAP.md`** — items #16–#22 added:
  - #16: Fig 3 `index.html` topic filter dropdown uses stale NMF names — fix needed in `src/06_build_report.py` (open)
  - #17: Provenance notice covers header — fixed (this release)
  - #18: p99 filter broken — fixed (this release)
  - #19: Degree filter not applied + orphan nodes — fixed in source, rerun needed
  - #20: Reader's guide created and linked — done, rerun needed
  - #21: "event" as new node kind — design-first, open
  - #22: Paragraph co-occurrence frequency as evidence of epistemic affordance — theoretical
    proposition with explicit assumptions; awaits ROADMAP #12 (paragraph-window edge computation)
  - #12: Updated with full epistemic affordance motivation (argumentative co-deployment proxy;
    extends §15.2 of `docs/memo_media_aware_nlp_epistemic_affordances.md`)

- **KI-08 documented** — [2133] *Cybernation and Social Change* confirmed as the drop book:
  OCR-corrupted short monograph, already excluded via `ocr-excluded` list in pipeline.
  Confirmed in `data/outputs/runlog20260418-2.csv` (541 books processed).

### Changed — Topic taxonomy revised after ordering shuffle detected (18 April 2026)

Full `run_all.sh` rerun (`runlog20260418-3.csv`) confirmed mean stability=0.357, 0/9
unstable — but title-sweep of top-loading books revealed the topic ordering had shuffled
from Run C (14 April). Only T6 (Formal Foundations) held its position. `patch_topic_names.py`
and `_LDA_BASE` in `06_build_report.py` updated to reflect revised names.

**Previous taxonomy (Run C, 14 April 2026) → New taxonomy (18 April 2026):**

| Index | Run C name (14 Apr) | 18 Apr name | Change |
|-------|---------------------|-------------|--------|
| T1 | History and Biography of Cybernetics | Cybernetics of Political Economy | Shuffled |
| T2 | Cybernetics of Psychology | Cybernetics and Circularity | Shuffled |
| T3 | Extensions of Cybernetics | Biological Systems Cybernetics | Shuffled |
| T4 | Cybernetic Management Theory | Applied Engineering Cybernetics | Shuffled |
| T5 | Biological Systems Cybernetics | Cultural Applications of Cybernetics | Shuffled |
| T6 | Formal Foundations of Cybernetics | Formal Foundations of Cybernetics | **Stable** |
| T7 | Cross-Domain Applications of Cybernetics | History and Biography of Cybernetics | Shuffled |
| T8 | Cybernetics of Posthumanism | Cybernetic Management Theory | Shuffled |
| T9 | Cultural Applications of Cybernetics | Residual / Outlier Cluster | Shuffled |

**Diagnosis:** LDA topic ordering is non-deterministic between runs. Mean stability and
individual cluster content are consistent, but index positions rotate. `patch_topic_names.py`
applies names by index, so a fresh `run_all.sh` without a title-sweep check silently
misassigns names. This confirms the need for the topic name validation sprint (run-records
system, multi-rater protocol — CLAUDE.md current sprint). All names remain provisional.

**Stability comparison (same mean, reshuffled per-topic):**

| Index | Run C stability | 18 Apr stability |
|-------|----------------|-----------------|
| T1 | 0.131 | 0.232 |
| T2 | 0.559 | 0.224 |
| T3 | 0.153 | 0.551 |
| T4 | 0.349 | 0.437 |
| T5 | 0.224 | 0.374 |
| T6 | 0.289 | 0.349 |
| T7 | 0.306 | 0.464 |
| T8 | 0.306 | 0.319 |
| T9 | 0.622 | 0.261 |
| **Mean** | **0.357** | **0.357** |

**18 April topic detail (top words and top 5 books, from `runlog20260418-3.csv`):**

T1 — Cybernetics of Political Economy (stability=0.232)
Words: decision, border, investment, security, price, market, stock, information
Top books: [2269] Cybernetic Circulation Complex (2025) · [2607] Constructing Soviet Cultural Policy (2008) · [2331] The Cybernetic Border: Drones (2024) · [2352] Balkan Cyberia: Cold War Computing (2023) · [2449] Imaginary Futures (2007)

T2 — Cybernetics and Circularity (stability=0.224)
Words: information, function, element, value, number, probability, define, entropy
Top books: [2733] The Question Concerning Technology in China (2016) · [2699] Recursivity and Contingency (2019) · [2447] Documentarity (2019) · [2187] Ontology of Complexity: Bateson (2014) · [2181] Philosophical Posthumanism (2019)

T3 — Biological Systems Cybernetics (stability=0.551)
Words: control, model, behavior, variable, input, cell, level, output
Top books: [2702] Rethinking Homeostasis (2003) · [2721] The Discovery of the Artificial (2010) · [2740] The Things We Do (2000) · [2577] Adaptation and Well-Being: Social Allostasis (2011) · [2502] Information Theory and Evolution (2012)

T4 — Applied Engineering Cybernetics (stability=0.437)
Words: wiener, bateson, science, cybernetic, theory, world, nature, year
Top books: [2737] Study of Living Control Systems (2021) · [2678] Neural Networks as Cybernetic Systems (1996) · [2356] Engineering Cybernetics (1954) · [2194] Biological Feedback (1990) · [2744] Cybernetic Modeling for Bioreaction Engineering (2018)

T5 — Cultural Applications of Cybernetics (stability=0.374)
Words: year, people, look, right, trurl, tell, every, hand
Top books: [2657] History of Computer Art (2020) · [2047] The Composer's Black Box (2025) · [2398] Cybernethisms: Aldo Giorgini's Computer Art Legacy (2015) · [2166] Computers, Automation, and Cybernetics at the Hagley Museum (1989) · [2448] Digital Performance (2007)

T6 — Formal Foundations of Cybernetics (stability=0.349) ← stable from Run C
Words: machine, human, computer, brain, problem, control, language, program
Top books: [2097] The Mathematical Theory of Semantic Communication (2025) · [2670] Mathematical Structure of Finite Random Cybernetic Systems (1972) · [2453] Intangible Life (2017) · [2435] Relative Information (2011) · [2665] Information and Reflection (2012)

T7 — History and Biography of Cybernetics (stability=0.464)
Words: human, theory, social, world, concept, self, science, communication
Top books: [2560] @Heaven: The Online Death of a Cybernetic Futurist (2015) · [2677] Norbert Wiener—A Life in Cybernetics (2018) · [2637] Dark Hero of the Information Age (2009) · [2298] Full Circles Overlapping Lives (2000) · [2709] Success Cybernetics (2022)

T8 — Cybernetic Management Theory (stability=0.319)
Words: cybernetic, social, information, organization, technology, design, control, management
Top books: [2244] Health as a Social System: Luhmann (2023) · [2727] The Management Process, Management Information and Control (1969) · [2683] Organizational Systems: VSM (2011) · [2682] Organization Structure: Cybernetic Systems Foundation (2012) · [2420] The Viability of Organizations Vol. 3 (2019)

T9 — Residual / Outlier Cluster (stability=0.261)
Words: people, family, person, life, experience, therapy, child, client
Top books: [2467] The Cyberiad (1974, loading=1.000) · [2764] The Cyberiad: Stories (2002, loading=1.000) · [2703] R.U.R. (2004) · [2333] Return to China One Day: Qian Xuesen (2023) · [2103] The Communication Systems of the Body (1964)

### Changed — `run_all.sh` canonical step 14 now includes paragraph windows

`src/run_all.sh` line 133 changed from:
```
python3 src/14_entity_network.py --no-windows
```
to:
```
python3 src/14_entity_network.py
```

**Rationale:** `--no-windows` excluded ~239 concept nodes that only have paragraph-level
edges (no qualifying book-level co-occurrence). This produced a materially different,
smaller network (1,380 nodes, concepts=500) than the paragraph-inclusive build
(1,620 nodes, concepts=739). The canonical release HTML is the paragraph-inclusive
network; running `run_all.sh` with `--no-windows` would produce a divergent result on
every future run. Paragraph windows add ~5 minutes to the pipeline run.

**Canonical `run_all.sh` network (from 18 April 2026):**
1,620 nodes (persons=656, concepts=739, orgs=154, locations=71), 11,501 edges
(book=10,362 + para=1,139), density=0.009, LCC=1,618/1,620, APL=3.26, diameter=6.

**Resolution of KI-10:** The 746→500 concept count drop seen in the sixth-batch runlog
was not a data bug but a direct consequence of `--no-windows`. KI-10 closed.

### Status

Entity network HTML release-ready. Rerun completed 18 April 2026.

---

## [0.4.5] — 2026-04-18

> Session: 18 April 2026 (Cowork) — second batch

### Added — Algorithm infection principle embedded in all HTML-generating scripts

All 9 HTML-generating scripts now carry the methodological provenance statement in two places:

1. **Python source (comment block):** A standardised `# ── METHODOLOGICAL NOTE —
   all outputs are provisional ──` block placed immediately after the module docstring
   (or at the top of scripts without a docstring). States the algorithm infection principle
   and links to `docs/methodology.md §"Implication for dissemination — all outputs are
   provisional"`. Serves as a standing reminder for anyone reading or modifying the code.

2. **Generated HTML (visible disclaimer):** `_PROV_NOTICE` constant defined in each script.
   `html.replace('</body>', _PROV_NOTICE + '\n</body>', 1)` inserted just before each
   `f.write(html)`. Renders as an amber-bordered notice panel at the bottom of every
   generated report, visible to anyone who opens the HTML.

Scripts updated: `src/06_build_report.py`, `src/06_build_report_chapters.py`,
`src/08_build_timeseries.py`, `src/10_build_index_report.py`,
`src/11_embedding_comparison.py`, `src/12_index_grounding.py`,
`src/13_weighted_comparison.py`, `src/14_entity_network.py`, `src/build_embed_report.py`.

Pattern is idempotent and survives `run_all.sh` reruns (disclaimer is injected at write
time from the constant, not stored in the output file).

---

## [0.4.4] — 2026-04-18

> Session: 18 April 2026 (Cowork)

### Fixed — Entity network node misclassification sweep (KI-07)

Comprehensive review of all 1860 nodes in `json/entity_network.json` identified ~130
misclassified nodes across all four kinds. Two-part fix:

**`src/14_entity_network.py` — new suppression filters (applied before cache lookup):**
- `_TRAILING_FUNC` regex — suppresses any term whose surface form ends with a function word
  ("of", "and", "on", "the", "to", "for", "in", "with", …). Catches ~50 fragment nodes
  that slipped through NER as apparent named entities ("evolution of" [degree 18],
  "definition of" [18], "history of" [15], "cybernetics and" [15], "wiener and" [3],
  "free will and" [47 — was org], "ai and" [39 — was location], etc.)
- `_CTA_BACK_MATTER` regex — suppresses "sign up now", "discover your next",
  "all rights reserved", "about the author", "first edition", "published by", etc.
  Both filters run before cache lookup so they cannot be overridden by stale cache entries.

**`json/entity_types_cache.json` — 101 entries corrected** (all pre-existing entries with
wrong classification; not committed — json/ is gitignored):

| Category | Count | Examples |
|----------|-------|---------|
| location → organisation | 3 | New York Times [138], San Francisco Chronicle [25], Vienna Circle [21] |
| location → concept | 7 | Manhattan Project [86], Perceptron [81], Big Bang [22], Hippocampus [18], Algorithm [10], Truth [10] |
| location → suppress | 3 | Systém [58] (Czech OCR artefact), Tortoise [1], ai and [39] |
| org → person | 5 | Lorente de Nó Rafael [33], Cicero [12], St. Augustine [9], Epictetus [8], Rutherford [1] |
| org → concept | 27 | Principia Mathematica [54], design for a brain [51], quantum computing [44], social sciences [37], Synergy [34], Brain [22], Neurotransmitters [21], Retina [21], Slavery [20], Synthesis [16], quantum entanglement [13], Speech [10], … |
| org → suppress | 18 | Laboratory [60], Bishop [12], University) [23], Self- [6], Linear [3], generic nouns |
| concept → person | 4 | Voltaire [7], Homer [3], Sophocles [1], Bernard [4] (Claude Bernard) |
| concept → organisation | 3 | Life Magazine [15], CoEvolution Quarterly [6], Ramparts [2] |
| concept → suppress | 3 | Galileo Galilei [2] (dup), Stengers [3] (dup), wiener [1] (standalone fragment) |
| person → suppress | 8 | Weiner Norbert [5] (misspelling), Drop [4], Norbert [2] (fragment), One Park Ave NY [3], Foerster Heinz von [22] (dup), Neumann John von [19] (dup), Clark [4], Humphreys [3] |
| person → location | 2 | New York NY [5], Cambridge Massachusetts [1] |
| person → concept | 2 | brain human [8], Grammar [1] |
| person → organisation | 2 | Gordon and Breach Science Publishers [3], Whole Earth Catalog The [4] |
| org → suppress (dups) | 4 | kluckhohn, von bertalanffy, vinge, waddington (all duplicated in person list) |
| misc cache corrections | 6 | free will and → suppress, ai and → suppress, oxford → location, etc. |

**Expected result after rerun:** ~130 fewer bad nodes; anatomy terms (Brain, Retina, etc.)
correctly as concepts; classical persons (Voltaire, Cicero, Homer) as persons; duplicates
eliminated; no trailing-function-word fragments in any category.

### Next action
Rerun `python3 src/15_entity_classify.py` then `python3 src/14_entity_network.py`.
Then commit both source files — the cache file stays gitignored but the
corrections are now permanent in source code.

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
- `json/` divergence between machines — NLP machine is canonical

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
- Full SCOWL en_US-large Hunspell dictionary (76,959 words) installed on all development machines (⚠️ dictionary inconsistency between machines — monitor for reproducibility)
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
