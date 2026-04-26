# CLAUDE.md — CyberneticsNLP

## Protocol
See `04 Resources/Claude Working Protocol.md` in the vault — standard end-of-session
update rules apply. Trigger phrase: "Update CLAUDE.md".

File reference format:
- Code: `src/filename.py:LINE`
- Docs: `docs/filename.md §"Section heading"` or `docs/filename.md:LINE`
- Data: `json/filename.json`

Session history, changelog, and open work live in the canonical logs — not here.
- Change log: `docs/CHANGELOG.md`
- CRediT / session rows: `docs/contributions.md`
- Design decisions: `docs/decisions.md`
- Open backlog: `docs/ROADMAP.md`
- Master project doc (sprint list, session log, known issues): `02 Projects/CyberneticsNLP/CyberneticsNLP.md` in the vault

---

## Project snapshot

- **Repo:** `~/CyberneticsNLP/` on the NLP machine, accessed via the sshfs mount inside the vault
- **Vault path:** `02 Projects/CyberneticsNLP/cybersonic/CyberneticsNLP/`
- **Canonical corpus framing:** "541 monographs and collected works analysed" from a 695-book Calibre collection. [2133] *Cybernation and Social Change* excluded (OCR corruption — KI-08).
- **Canonical k:** 9 (validated on sampled runs 3–14 April 2026; confirmed on the first full-text canonical run by Paul Wong, 26 April 2026 — `run_20260426_k9_s5`, equivalence class `23b29233a67b2938`). `run_all.sh` enforces `--topics 9 --seeds 5 --full-text --max-features 15000 --max-iter 100 --gpu`. Topic names finalised 26 April 2026 (single rater, single run — sprint item 4 still requires ≥3 runs × ≥2 raters before names can be considered stable).
- **Current run record:** query `data/pipeline.db` (`pipeline_runs`, `runlog_entries`) or read the latest `data/outputs/runlogYYYYMMDD.csv`. Don't rely on hardcoded figures here — they rot.
- **Current version:** read `docs/CHANGELOG.md` (top entry).

---

## Commands

All commands run from the project root on the NLP machine. **Claude edits files via the
sshfs mount but cannot execute anything on the NLP machine** — the user runs these in a
terminal.

**Full pipeline:**
```
bash src/run_all.sh              # standard (<~300 books)
bash src/run_all.sh --stream     # streaming parse+clean for large corpora
bash src/run_all.sh --test       # test run; runlog suffixed _test; not survey-eligible
```
Runlog auto-written to `data/outputs/runlogYYYYMMDD.csv` (suffix `-2`, `-3`, … for repeat runs
on the same day).

**Rebuild from step 09** — after `09_extract_index.py` or `09b_build_index_analysis.py` changes:
`09 → 09b → 09c → 10 → 12 → 14 → 15`. Simplest: rerun `run_all.sh`.

**Restore canonical k=9 after a k-sweep comparison run:**
```
python3 src/03_nlp_pipeline.py --min-chars 10000 --lemmatize --topics 9 --seeds 5 --full-text --max-features 15000 --max-iter 100 --gpu
python3 src/patch_topic_names.py
python3 src/check_stale_vars.py --fix
python3 src/09c_validate_topics.py --top 10 --md
```
`topic_stability.json` always reflects the **last** k run — this restoration step is
mandatory before committing.

**Survey workflow (Google Forms):**
```
python src/log_pipeline_run.py --runlog data/outputs/runlogYYYYMMDD.csv  # gate: must log before form
python src/generate_google_form.py                                       # creates form for logged run
python src/ingest_google_responses.py                                    # idempotent response fetch
```
One-time setup: `python src/get_google_token.py` on a machine with browser access (writes
`token.json` via sshfs mount).

**Utilities:**
- `python src/check_stale_vars.py --fix` — sync `_LDA_BASE` literals across 8 scripts against `nlp_results.json['topic_names']`; also cross-verifies TAXONOMY and flags corpus-count literals.
- `python src/migrate_pipeline_db.py` — one-shot migration from `topic_naming.db` → `pipeline.db`.

**Optional second pass:** `03_nlp_pipeline.py --weighted` boosts discriminating index terms.
Requires `index_analysis.json` from a prior full run. See the commented block at the end of
`src/run_all.sh`.

---

## Architecture

Numbered scripts in `src/` form a linear pipeline orchestrated by `run_all.sh`.

**Pre-processing (NOT in `run_all.sh` — external APIs, run manually):**
- `00_classify_book_styles.py` — heuristic style classification (title/author/publisher signals)
- `00_fetch_worldcat_metadata.py`, `00_fetch_anu_primo.py` — Google Books / Open Library / ANU Primo enrichment
- Writes `json/book_styles.json` (covariate for downstream analysis)

**Main pipeline stages (in `run_all.sh`):**
1. `01_parse_books.py` → `json/books_parsed.json`
2. `02_clean_text.py` → `json/books_clean.json` (or `parse_and_clean_stream.py` in `--stream` mode)
3. `03_nlp_pipeline.py` → `json/nlp_results.json`, `json/topic_stability.json`
4. `patch_topic_names.py` — overlays canonical taxonomy onto raw LDA labels in `nlp_results.json`
5. `check_stale_vars.py --fix` — propagates topic names into `_LDA_BASE` literals across scripts
6. `09c_validate_topics.py` → `data/outputs/topic_validation.md` (post-naming, so names not raw labels)
7. Book-level reports: `04_summarize.py` → `05_visualize.py` → `06_build_report.py` → `07_build_excel.py`
8. Chapter-level reports: `03_nlp_pipeline_chapters.py` → `05_visualize_chapters.py` → `06_build_report_chapters.py` → `07_build_excel_chapters.py`
9. `09_extract_index.py` → `json/index_terms.json`, `json/index_vocab.json`
10. `09b_build_index_analysis.py` → `json/index_analysis.json`, `json/index_snippets.json`
11. `10_build_index_report.py`
12. `12_index_grounding.py` → `json/topic_index_grounding.json`, `json/concept_density.json`, `json/concept_velocity.json`
13. `08_build_timeseries.py` (Chart 7 requires `index_analysis.json` + `concept_velocity.json`)
14. `11_embedding_comparison.py` + `build_embed_report.py`
15. `15_entity_classify.py` → `json/entity_types_cache.json` **(must run before 14)**
16. `14_entity_network.py` → `json/entity_network.json`, `data/outputs/book_nlp_entity_network.html`

**Key invariants:**
- `--topics 9` is enforced in `run_all.sh`; canonical k=9.
- `nlp_results.json` is overwritten every run; k-sweep variants persist as `nlp_results_k{N}.json`.
- Step 14 runs **with** paragraph windows by default (no `--no-windows` flag). Omitting windows cuts ~239 concept nodes — see KI-10.
- Step 15 builds the NER cache; step 14 reads it. Running 14 without a cached 15 result produces an incomplete network.
- Two regex filters in `14_entity_network.py` (`_TRAILING_FUNC`, `_CTA_BACK_MATTER`, `_EOLSS_NOISE`, `_TRAILING_COLON`) run **before** cache lookup so stale cache entries cannot override them.

**Survey infrastructure (orthogonal to the NLP pipeline):**
- `data/pipeline.db` — SQLite, 8 tables. Replaces the older 3-table `data/topic_naming.db`. All survey scripts import from `src/pipeline_db.py`.
- **Equivalence class** = SHA-256(16) of `(k, n_books, max_features, pipeline_mode, seeds_used)`. Two runs in the same class are comparable up to topic permutation.
- **nlp_hash** = SHA-256(16) of `nlp_results.json` — identifies a specific run instance.
- `credentials.json` + `token.json` are gitignored (see `.gitignore`).

**Output directories:**
- `json/` — pipeline intermediates (see `README.md` for full inventory)
- `data/outputs/` — HTML reports, Excel workbooks, dated runlog CSVs
- `figures/` — PNGs for paper / presentation
- `data/pipeline.db` — survey workflow state

---

## Standing methodological principle — all outputs are provisional

All pipeline outputs should be treated as provisional results subject to validation, not
as findings. Because the distribution of residual input errors is unknown, and because each
algorithm makes different simplifying assumptions, the degree of corruption from residual
error cannot be determined in advance. Domain knowledge can flag individual artefacts but
cannot certify the absence of subtler, undetectable ones.

**Practical consequence for dissemination:**
- HTML reports shared publicly: viewers flagging errors is expected and welcome.
  Corrections should be checked against source data (→ ROADMAP #15).
- Peer reviewers: must be told explicitly that (a) known error classes are characterised
  and mitigated; (b) unknown residual errors remain with uncharacterised distribution;
  (c) results are robust in aggregate and indicative at the level of individual
  associations, not individually certified facts.

**Paper/report framing to use:**
> *Results are derived from automated analysis of the CyberneticsNLP corpus and should be
> treated as provisional. Known data quality issues have been characterised and mitigated;
> residual errors of uncharacterised distribution remain. Individual associations should be
> verified against source material before being treated as established findings.*

Note: hardcoded corpus counts (e.g. "542-book") have been removed from the provenance
statement — the count is fragile (KI-08) and a precise number in a data-quality warning
is itself a data-quality risk.

Full methodological argument: `docs/methodology.md` §"Implication for dissemination —
all outputs are provisional".

---

## Standing interpretive principle — principle of context (incomplete information)

Linguistic items stripped of their context lose determinate meaning. This applies
equally to human readers and to algorithms: without the surrounding text, both face
genuine ambiguity that cannot be resolved by surface form alone.

**Pipeline consequence:** index terms, entity labels, and vocabulary entries are
inherently decontextualised. A string like "University of California" can be a
publisher credit, an institutional affiliation, a subject of study, or a funding
body — the index entry carries none of that distinction. Filtering or classifying
such items on the basis of string form alone will always produce a mixture of correct
decisions and errors, because the signal needed to decide is absent at the point of
decision.

**Practical implications:**
- Upstream filters (regex blocklists, NER classifiers, entity type rules) operate on
  decontextualised strings and will therefore always have a residual error rate that
  cannot be driven to zero without access to full sentence context.
- When a filter would correctly block one sense of a term but incorrectly block
  another legitimate sense, the right response is usually to leave the term unfiltered
  and accept the noise, rather than introduce a systematic false-negative for the
  legitimate sense. Record the ambiguity in ROADMAP as a known artefact.
- Corpus-scale NLP results should be understood as reflecting the distribution of
  surface co-occurrences, not the distribution of intended meanings. Individual
  associations require verification against source text before being treated as
  semantically grounded.
- This is not a pipeline failure — it is an inherent property of working with
  decontextualised linguistic data at scale.

**Motivating instance:** "University of California" appears in the entity network as an
isolated organisation node, connected only to Tylor, E. B. It is present in the index
of *Living Systems*, *Gregory Bateson: The Legacy of a Scientist*, and *Cyburbia* —
where it may be a publisher credit, an institutional affiliation, or a genuine subject
reference. No upstream filter can resolve this without sentence context. Accepted as a
known artefact; not filtered.

---

## Standing engineering principle — fix upstream, not downstream

The corpus will grow over time. Any fix that patches a downstream script rather than
the script responsible for producing the relevant data will fail silently for every
new book added to the collection — the same malformed input will propagate the same
error through every downstream stage without warning.

**Rule:** when a data-quality problem is identified, the fix must go into the earliest
script in the pipeline that can intercept it. Downstream scripts must handle the
exception at source, not compensate for it.

**Practical consequence:**
- A regex filter in `09_extract_index.py` (e.g. `FOREIGN_HEADER_RE`, `_canonical_term()`)
  is the right place to fix an index-extraction artefact — not in `14_entity_network.py`
  by blacklisting the resulting bad term.
- A casing normalisation in `_canonical_term()` is the right place to fix lowercased
  proper names — not by patching individual entries in `index_vocab.json`.
- A stopword addition in `03_nlp_pipeline.py` is the right place to suppress a noise
  term — not by post-filtering topics in `06_build_report.py`.

**When a downstream patch is unavoidable** (e.g. the upstream fix is blocked by
missing data or pending API access), record it explicitly in ROADMAP.md with a note
that it is a temporary workaround and a pointer to the upstream script that should
eventually own the fix.

---

## Standing engineering principle — non-disjoint labels require inclusion semantics

Many of the label spaces used in this project are **non-disjoint** — a single
item can legitimately carry more than one label at once. Publication types
(a book can be both monograph and textbook), style labels (monograph and
anthology), entity kinds (Cold War functions as both event and concept
depending on context), and paragraph-level relationship types (synthesis and
contrast can co-occur in the same passage) all behave this way. The labels
describe aspects of identity, not partitions of it.

**Rule:** any filter, gate, or membership test keyed on a non-disjoint label
space must use **inclusion semantics** ("admit if any approved label is
present"), not **exclusion semantics** ("reject if any disapproved label is
present"). Exclusion rules on secondary labels systematically remove items
whose primary label is legitimate.

**Practical consequence:**
- The pub-type filter in `src/03_nlp_pipeline.py:295-333` tests
  `any(p in _INCLUDE_TYPES for p in parts)`. This admits Ashby's
  *An Introduction to Cybernetics* (labelled `monograph, textbook`) on the
  strength of `monograph`, regardless of the secondary `textbook` label. A
  rule like "drop if `textbook` in pub_type" would wrongly remove it.
- The signal-inventory-derived filter planned in ROADMAP #9 must be
  built the same way — inclusion on approved content signals, not
  exclusion on disapproved ones.
- Style-conditioned sampling (ROADMAP #10) faces the same question: a
  multi-label book must be assignable to every stratum it qualifies for,
  or explicitly apportioned — never dropped from strata by the presence
  of an additional label.
- Entity kind assignment and paragraph-level edge classification: if a
  term can legitimately function as event *and* concept (or a paragraph
  co-occurrence can legitimately reflect synthesis *and* contrast),
  treating the classes as mutually exclusive forces a false choice.
  Multi-membership or soft assignment is usually the right representation.

**Connection to the Principle of Context:** a label records one aspect of
an item's identity, observable from whatever signal the labeller had
access to. It does not exhaust the item's meaning, and filtering on the
assumption that it does produces systematic errors of the same form as
filtering on decontextualised strings.

**Motivating instance:** Ashby, *An Introduction to Cybernetics* (1956) —
a foundational monograph in the field that is also, unambiguously, a
textbook. Retained in the corpus by the inclusion-based pub-type filter.
An exclusion-based rule keyed on the `textbook` label would drop it.
Full rationale: `docs/decisions.md` §"Inclusion vs exclusion semantics
for non-disjoint labels".

---

## Standing security principle — no identifying infrastructure details in documentation

**Scope:** all version-controlled files — source code (including comments), docs/,
CLAUDE.md, README.md, CHANGELOG.md, and any other committed file.

**Rule:** the names of specific machines, users, hostnames, server URLs, account
identifiers, or credential values must not appear in any committed file. This includes
comments, docstrings, inline examples, and decision/methodology prose.

**In practice:**
- Machine names → "the NLP machine", "the workstation", or omit entirely
- Usernames / login handles → `<user>` as a placeholder in example commands
- Hostnames / SSH targets → `<nlp-host>` or `<hostname>` as placeholders
- Server URLs or domain names → describe the service type only (e.g. "a custom domain")
- OAuth project IDs, client IDs → omit; note only that credentials are gitignored
- Email addresses → omit from code and docs; the gitignored `credentials.json` holds these

**Credentials and tokens** (`credentials.json`, `token.json`, `*.db`) are gitignored
separately — see `.gitignore`. The documentation principle above applies to any
identifying detail that would appear in plain text in a committed file even without
being a credential itself.

The mapping from generic placeholders to actual infrastructure identifiers lives in
`csv/infrastructure.csv` (gitignored).

---

## Release goal — Book-level HTML for colleague sharing

**Target:** Release the book-level analysis HTML files to colleagues after presentation.
**Standard:** Defensible — genuine effort at error reduction; not certified error-free.
Consistent with the standing methodological principle and the provenance notice in all
reports.

**Files in scope for release (nav links to entity network, not summaries):**
- `data/outputs/index.html` — main report (Fig 1–6 + topic proportions)
- `data/outputs/clusters.html` — cluster composition
- `data/outputs/keyphrases.html` — keyphrase analysis
- `data/outputs/cosine.html` — cosine similarity
- `data/outputs/book_nlp_entity_network.html` — entity relational network

`books.html` (per-book summaries) is **not** in the current release scope — summary quality
is not yet at release standard (60k-token sampling limits). All four navigable pages link
to the entity network via the nav tab.

**"Defensible" means:** all known systematic errors (platform contamination, EOLSS noise,
trailing fragments, node misclassifications) are fixed or mitigated; provenance notice
visible at all scroll positions; topic names match current provisional LDA names; entity
network validated against domain knowledge; results framed as automated provisional
analysis with no individual certified findings.

---

## Current sprint — Topic naming reliability

**Item 1 complete:** full `pipeline.db` survey infrastructure built.

**Core database:** `data/pipeline.db` (8 tables). Shared by all survey scripts via
`src/pipeline_db.py`. Tables: `equivalence_classes`, `pipeline_runs`, `runlog_entries`,
`naming_sessions`, `topic_ratings`, `google_form_configs`, `google_form_responses`.

**Canonical workflow:**
1. `bash src/run_all.sh` — pipeline run; runlog auto-saved.
2. Review runlog. If satisfied: `python src/log_pipeline_run.py --runlog …`.
3. `python src/generate_google_form.py` — creates a form for the logged run (blocks test runs).
4. Share form URL with raters.
5. `python src/ingest_google_responses.py` — idempotent.

**Survey scripts:**
- `src/pipeline_db.py` — DB module; schema; `open_db()`, `compute_file_hash()`, `compute_run_hash()`, `find_run_by_nlp_hash()`
- `src/log_pipeline_run.py` — manual run logging; shows equivalence class; `--test` marks run survey-ineligible
- `src/migrate_pipeline_db.py` — one-shot migration from `topic_naming.db`
- `src/get_google_token.py` — one-time OAuth (run on a machine with browser)
- `src/generate_google_form.py` — creates Google Form from `nlp_results.json`; enforces run-logging pre-condition
- `src/ingest_google_responses.py` — fetches responses into `naming_sessions` + `topic_ratings`
- `src/record_topic_run.py` — local HTTP server (interim); uses `pipeline_db`

**Items 2–4 open** (tracked in `docs/ROADMAP.md` and the master project doc):
2. **n-run comparison report** — `src/compare_topic_runs.py --runs N`. Draft: `02 Projects/CyberneticsNLP/docs/src_draft/compare_topic_runs.py`.
3. **Multi-rater naming protocol** — ≥2 independent raters per topic per run; inter-rater agreement.
4. **Revise naming status** — current k=9 names are provisional (single run, single rater). Names stable only after ≥3 runs and ≥2 raters agree.

---

## Backlog item — User correction mechanism (ROADMAP #15)

Entity network HTML is shared publicly. Viewers will spot misclassifications.
**Future task:** add in-report UI for users to flag corrections (wrong kind, duplicate,
fragment). Corrections feed back into `MANUAL_CORRECTIONS` after review.
Open design questions: capture channel, correction schema, review workflow.

---

## HTML report bugs

Canonical list in `docs/ROADMAP.md`. KI numbers in this file refer to pipeline/data issues;
ROADMAP # refers to code/UI bugs. The ROADMAP's older KI-01–KI-09 list is stale (v0.4.2)
and should not be confused with the active KI tracking below.

| ROADMAP # | Report file | Description | Status |
|-----------|-------------|-------------|--------|
| #16 | `index.html` Fig 3 + `keyphrases.html` | Topic filter dropdowns used stale names. Root cause: `patch_topic_names.py` TAXONOMY overwrote `nlp_results.json` on every run. Fixed: TAXONOMY updated; `_LDA_BASE` fallback updated; `lda_names` added to `kp_data`; keyphrases JS fixed. | ✅ Done |
| #17 | `book_nlp_entity_network.html` | Provenance notice (`position:fixed;top:0`) covered the app header. Fixed in `src/14_entity_network.py`: notice is now `flex-shrink:0` static, injected before `<div class="header">`. | ✅ Done |

---

## Infrastructure notes

Specific machine names, usernames, hostnames, email addresses, and resource IDs are
replaced with generic descriptions here (security principle). Actual values live in
`csv/infrastructure.csv` (gitignored).

- **sshfs mount:** the NLP machine is mounted inside the vault at `02 Projects/CyberneticsNLP/cybersonic/` via alias `mcyber` on the NLP machine. Claude can read and write files through this mount. Mount goes stale after ~30 min — run `mcyber` on the NLP machine to remount if directories appear empty.
- **Execution boundary:** Claude cannot run commands on the NLP machine. Git, Python scripts, pip installs — all NLP machine only. Claude edits files via the mount; the user runs the scripts.
- **Git push:** commit and push from the NLP machine to `github.com:cyberneticbookshelf-stack/cyberneticsNLP.git`. SSH key must be configured on the NLP machine.
- **Cowork second workspace:** known bug (GitHub #19318) — `+` button fails with "Session VM process not available" on FUSE/sshfs mounts. Use the vault-internal mount as workaround.
- **Python environment:** NLP machine, `~/CyberneticsNLP/`. Use `pip install --break-system-packages`.
- **ngrok (optional, for interim naming server):** `conda install trenta3::ngrok`, then `ngrok http 7474` in a second terminal. Free tier requires an ngrok account. Superseded by Google Forms for public surveys.
- **Google Forms survey:** `get_google_token.py` (run once on the workstation via sshfs mount) → `log_pipeline_run.py` → `generate_google_form.py` → share URL → `ingest_google_responses.py`. App is in Google OAuth Testing mode; the project Google account is whitelisted as a test user.
- **Naming server — local (interim):** `ssh -L 7474:localhost:7474 <user>@<nlp-host> -N` from the workstation; open `http://localhost:7474`. Fragile; manual server start; held SSH session.
- **Naming server — self-hosted (abandoned):** Docker/Caddy infrastructure fully built but permanently blocked by ISP inbound port restrictions on residential connection.
- **Patch scripts:** when sshfs mount goes read-only mid-session, write patch scripts to the vault (not the project directory) and run them on the NLP machine. Use `str.replace()` or line scanners, not `re.sub()` — `re.sub` processes backslash sequences in replacement strings and corrupts Python string literals.

---

## Known issues (active)

Resolution detail (commit hashes, file-level changes) is in `docs/CHANGELOG.md` and
`docs/contributions.md`. This table is the orientation index only.

| ID | Issue | Status |
|----|-------|--------|
| KI-04 | Amazon/Google as high-degree nodes — ebook metadata noise | **Resolved.** `KNOWN_TECH_PLATFORMS` in `src/14_entity_network.py`; noise filters in `src/09b_build_index_analysis.py`; Internet Archive strings in `src/02_clean_text.py`. |
| KI-05 | T9: book [249] loading=1.000 dominates | **Resolved (by interpretation).** Topic T9 labelled **"Residual / Outlier Cluster"** — the dominant single-book loading is accepted as a feature of the topic's role as a catch-all for material that doesn't cohere with the other eight topics, not a defect to be filtered. Label applied in `src/patch_topic_names.py:108-109` TAXONOMY and visible in `data/outputs/index.html`. Rationale recorded in `docs/decisions.md`. |
| KI-06 | Proceedings/handbook books not yet filtered from pipeline | **Resolved.** Pub-type filter in `src/03_nlp_pipeline.py:295-333` includes only books whose Calibre `pub_type` contains `monograph` or `collected works`. Consistent with canonical framing ("541 monographs and collected works analysed"). Two lenient-default caveats (unlabelled books default to include; missing metadata CSV skips the filter silently) tracked as ROADMAP #25. |
| KI-07 | ~130 misclassified nodes + EOLSS contamination + plural/comma fragments | **Resolved.** Regex pre-filters (`_TRAILING_FUNC`, `_CTA_BACK_MATTER`, `_EOLSS_NOISE`, `_TRAILING_COLON`) in `src/14_entity_network.py` run before cache lookup; `MANUAL_CORRECTIONS` in `src/15_entity_classify.py` extended across five batches. |
| KI-08 | 541 vs 542 book count — one book dropped at runtime | **Resolved.** [2133] *Cybernation and Social Change* added to `ocr-excluded` list. Parsed and cleaned normally but excluded before LDA/TF-IDF fitting and entity network construction. Canonical corpus: 542 parsed, 541 analysed. |
| KI-09 | ~150 singular/plural node pairs split PMI signal | **Resolved.** `_singular_form()` + `concept_plural_map` in `src/14_entity_network.py`; plurals merged into singulars with book-set union. `_CONCEPT_PLURAL_EXCEPTIONS` protects 35 `-ics` field names (cybernetics, thermodynamics, …). |
| KI-10 | Entity network concepts dropped 746→500 on fresh rebuild | **Resolved.** Root cause: `run_all.sh` was running step 14 with `--no-windows`, excluding ~239 concept nodes that only have paragraph-level edges. Fix: `--no-windows` removed from `run_all.sh`. |
| KI-11 | Stability band thresholds inconsistent: `log_pipeline_run.py` vs `09c_validate_topics.py` | **Open (post-presentation).** `09c` uses stable ≥0.30 / moderate 0.15–0.30 / unstable <0.15; `log_pipeline_run.py` uses different implicit thresholds (~≥0.45 stable). Same `topic_stability.json`, conflicting counts. Fix: centralise thresholds. See ROADMAP KI-10. |
| KI-12 | Release HTMLs reflect rebuild nlp_hash, not logged canonical run | **Open (post-presentation).** Rebuild run (`c8e3c71bf8a3d910`) differs from canonical logged run (`901e5ec924248fe2`); same equivalence class. Survey workflow unaffected. See ROADMAP KI-11. |

---

## Session startup protocol

Before each session, the user runs a fresh `run_all.sh` on the NLP machine. At session
start, read the latest `data/outputs/runlogYYYYMMDD.csv` and review:
- Book count and any exclusions
- Topic stability figures (mean stability, n stable / 9)
- Entity network summary (node counts by kind, edge counts by level, LCC %)
- Any warnings or errors in the log

Standalone script reruns (e.g. `python3 src/14_entity_network.py` outside `run_all.sh`) are
**not** captured in the runlog — if a mid-session standalone rerun is done, note the stats
manually in `docs/ROADMAP.md` or the master project doc.
