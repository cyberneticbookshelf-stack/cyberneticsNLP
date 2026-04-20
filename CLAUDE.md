# CLAUDE.md — CyberneticsNLP

## Protocol
See `04 Resources/Claude Working Protocol.md` in the vault — standard end-of-session
update rules apply. Trigger phrase: "Update CLAUDE.md".

File reference format:
- Code: `src/filename.py:LINE`
- Docs: `docs/filename.md §"Section heading"` or `docs/filename.md:LINE`
- Data: `json/filename.json`

---

## Project snapshot

**Version:** 0.4.7 (source edits applied 20 April 2026; commit pending rerun)
**Repo:** `~/CyberneticsNLP/` on Cybersonic (accessed via sshfs mount inside vault)
**Vault path:** `02 Projects/CyberneticsNLP/cybersonic/CyberneticsNLP/`
**Canonical run:** `runlog20260418-3.csv` — 542 books parsed, 541 analysed
(1 excluded: [2133] Cybernation and Social Change — OCR), k=9, **0/9 unstable**,
**mean stability=0.357**. Topic ordering shuffled from Run C (14 April); 18 April
title-sweep confirmed new names (see CHANGELOG [0.4.6]). Committed `491991e`.
**Canonical `run_all.sh`:** Step 14 runs **without** `--no-windows` (18 April 2026).
Paragraph-window edges included in all canonical builds. Network: 1,638 nodes
(persons=656, concepts=758, orgs=154, locations=70), 11,563 edges
(book=10,362 + para=1,201), density=0.009, LCC=1,636/1,638, APL=3.27, diameter=6.
**Master project doc:** `02 Projects/CyberneticsNLP/CyberneticsNLP.md` in vault
(full sprint list, topic solutions, session log, known issues)

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
statement — the count is fragile (KI-08 unresolved) and a precise number in a data-quality
warning is itself a data-quality risk.

Full methodological argument: `docs/methodology.md` §"Implication for dissemination —
all outputs are provisional" (added 18 April 2026).

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

**Motivating instance (20 April 2026):** "University of California" appears in the
entity network as an isolated organisation node, connected only to Tylor, E. B.
It is present in the index of *Living Systems*, *Gregory Bateson: The Legacy of a
Scientist*, and *Cyburbia* — where it may be a publisher credit, an institutional
affiliation, or a genuine subject reference. No upstream filter can resolve this
without sentence context. Accepted as a known artefact; not filtered.

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

This principle was made explicit 20 April 2026 after the `_canonical_term()` casing
bug: the fix in `09_extract_index.py` was the right intervention point; any entity
network node-level patch would have been a stopgap that new books would bypass.

---

## Backlog item — User correction mechanism (ROADMAP #15)

Entity network HTML is shared publicly. Viewers will spot misclassifications.
**Future task:** add in-report UI for users to flag corrections (wrong kind, duplicate,
fragment). Corrections feed back into `MANUAL_CORRECTIONS` after review.
Design open questions: capture channel, correction schema, review workflow.
See `docs/ROADMAP.md` item #15.

---

## Release goal — Book-level HTML for colleague sharing

**Target:** Release the book-level analysis HTML files to colleagues after presentation.
**Standard:** Defensible — genuine effort at error reduction; not certified error-free.
This is consistent with the standing methodological principle (all outputs are provisional)
and the provenance notice already in all reports.

**Files in scope for release (nav links to entity network, not summaries):**
- `data/outputs/index.html` — main report (Fig 1–6 + topic proportions)
- `data/outputs/clusters.html` — cluster composition
- `data/outputs/keyphrases.html` — keyphrase analysis
- `data/outputs/cosine.html` — cosine similarity
- `data/outputs/book_nlp_entity_network.html` — entity relational network

`books.html` (per-book summaries) is not in the current release scope — summary quality is not yet at release standard. All four navigable pages link to the entity network via the nav tab.

**Known issues affecting these files (prioritised):**

| Priority | Issue | File | Status |
|----------|-------|------|--------|
| High | ROADMAP #16: topic filter dropdowns stale | index.html, keyphrases.html | ✅ Resolved 18 April |
| High | KI-10: concept count 746→500 on fresh rebuild | entity_network.html | ✅ Resolved 18 April |
| Medium | KI-09: ~150 singular/plural node pairs split PMI signal | entity_network.html | ✅ Resolved 20 April |
| Low | Chapter NMF T4 contains metadata noise words | (chapter reports, not in scope) | Note only |

**What "defensible" means here:**
- All known systematic errors (platform contamination, EOLSS noise, trailing fragments,
  node misclassifications) are fixed or mitigated — done.
- Provenance notice visible at all scroll positions — done.
- Topic names in all reports match current provisional LDA names — done (18 April).
- Entity network validated against domain knowledge — done (KI-07 resolved).
- No individual certified finding; results framed as automated provisional analysis — done.

**Release status: All source-level fixes applied 20 April 2026. Full rerun of `run_all.sh` required (rebuild from step 09 due to `09_extract_index.py` casing fix).**

---

## Current sprint — Topic naming reliability

All four items remain open:

1. **Run-records system** — record pipeline run parameters, top 10 words, top N books,
   human-assigned name, rater ID, date. Store as `json/topic_run_records.json`.
   Draft script: `02 Projects/CyberneticsNLP/docs/src_draft/record_topic_run.py`

2. **n-run comparison report** — `src/compare_topic_runs.py --runs N`. Reads last N
   records from `topic_run_records.json`. Report: per-topic book presence matrix,
   stable word core, naming records table, inter-run book overlap %, agreement status.
   Must scale to arbitrary N. Draft: `02 Projects/CyberneticsNLP/docs/src_draft/compare_topic_runs.py`

3. **Multi-rater naming protocol** — ≥2 independent raters per topic per run;
   record disagreements; compute inter-rater agreement (Cohen's kappa or % agreement).

4. **Revise naming status** — current k=9 names are provisional (single run, single
   rater). Names stable only after ≥3 runs and ≥2 raters agree.

---

## Active issue — OCR exclusion: Cybernation and Social Change (KI-08 — RESOLVED)

**Book:** [2133] *Cybernation and Social Change* — short monograph with severe OCR
corruption. Identified as the source of the 541 vs 542 book count discrepancy.

**Root cause:** OCR errors in this monograph were infecting the cleaned corpus with noise
vocabulary and spurious co-occurrences. The book is too short and too corrupted to
contribute reliable signal; its presence degrades both topic and entity outputs.

**Fix:** Added [2133] to an explicit `ocr-excluded` list in the pipeline. The book is
parsed and cleaned normally but excluded before LDA/TF-IDF fitting and entity network
construction. Log confirms: `[ocr-excluded] excluded 1 book(s) from explicit exclusion
list (542 → 541)` — `data/outputs/runlog20260418-2.csv` line 204–205.

**Documentation required:** This exclusion should be recorded in `docs/methodology.md`
under data quality decisions. The canonical corpus is 542 books parsed, 541 analysed.
The corpus count framing for dissemination should use "541 monographs and collected works
analysed" rather than "542-book corpus" to reflect the exclusion accurately.

**Status: RESOLVED 18 April 2026.**

---

## Active issue — Node misclassification sweep (KI-07 — FULLY RESOLVED)

**Symptom:** Comprehensive review of all 1860 nodes (18 April 2026) found ~130 misclassified
nodes. Examples: Perceptron [81] as location; Manhattan Project [86] as location; New York
Times [138] as location; Brain/Neurotransmitters/Retina/Slavery/Synthesis as organisations;
Voltaire/Homer/Sophocles as concepts; Lorente de Nó as organisation; Weiner Norbert as
duplicate person; ~50 trailing-function-word fragments ("evolution of", "wiener and",
"free will and", "ai and", "definition of", etc.) surviving as concept/location/org nodes.

**Two-part fix — applied 18 April 2026 (third/fourth batch):**

1. **`src/14_entity_network.py`** — two new module-level regexes, applied *before* cache
   lookup (so they cannot be overridden by stale cache entries):
   - `_TRAILING_FUNC` — suppresses any term whose surface form ends in a function word
     ("of", "and", "on", "the", "to", "for", …). Catches ~50 fragment nodes.
   - `_CTA_BACK_MATTER` — suppresses "sign up now", "about the author", "all rights
     reserved", "first edition", "published by", etc.
   - `_EOLSS_NOISE` — suppresses EOLSS contamination terms at runtime.
   - `_TRAILING_COLON` — suppresses index sub-entry header fragments ending with `:`.

2. **`src/15_entity_classify.py`** — MANUAL_CORRECTIONS: 101 pre-existing cache errors
   corrected; 18 new entries (fourth batch); 89 further suppressions (fifth batch,
   18 April 2026 — degree 1–2 concept node review). Full correction set now hardcoded
   in source — survives cache wipes and `--refresh`.

**Rerun completed 18 April 2026 (fifth batch session):**
- Node count after fifth batch: **1,627** (persons=656, orgs=154, locations=71, concepts=746)
- Previous baseline: 1,708 (concepts=827 after fourth batch rerun)
- Concept reduction: 827 → 746 (81 fewer; 8 of 89 suppressed terms not present in network)
- Network: density=0.0087, LCC=1625/1627 (100%), APL=3.248, diameter=5, max degree=283

**Full pipeline rerun 18 April 2026 (sixth batch — `runlog20260418-2.csv`):**
- Node count after fresh rebuild: **1,380** (persons=656, orgs=154, locations=70, concepts=500)
- Concept reduction from fifth batch: 746 → 500 (246 fewer) — **requires investigation**
  Most likely cause: regex pre-filters (`_TRAILING_FUNC` etc.) applied before cache lookup
  on fresh build suppress terms that the fifth batch's patch-based approach left in the
  cache as classified. Could also reflect [2133]'s removal reducing some concepts below
  co-occurrence threshold. See KI-10 (new).
- Network: density=0.0109, LCC=1378/1380 (100%), APL=3.24, diameter=7, max degree=248
- Note: higher density and larger diameter than fifth batch; persons/orgs unchanged.

**Status: RESOLVED — but KI-10 opened for concept count investigation.**

---

## Active issue — Platform metadata contamination (KI-04 — RESOLVED in code)

**Symptom:** Norbert Wiener associated with Google (PMI 1.0, 9-book overlap) in entity
network — immediately wrong on domain grounds (Wiener died 1964, Google founded 1998).

**Root cause (two distinct sources, confirmed by corpus inspection 17 April 2026):**

1. **Temporal co-occurrence (structural):** Google appears in 95 books, Amazon in 60 —
   modern books on algorithms/AI that legitimately discuss both Wiener and contemporary
   platforms. Book-level PMI does not distinguish historical from contemporary entities.
   Fix: exclude from entity network before PMI computation.

2. **Index vocabulary noise (data quality):** Structural navigation terms ("Chapter"
   12 books, "Index" 15, "Introduction" 15, "Volume" 14, "Section" 7) leak into
   `json/index_analysis.json` from cross-references and front-matter fragments.
   Internet Archive attribution strings ("Digitized by the Internet Archive...
   Kahle/Austin Foundation") appear in 67 books. Fix: extend noise filters.

**Fixes implemented 17 April 2026 — applied and verified on Cybersonic:**
- `src/14_entity_network.py` — `KNOWN_TECH_PLATFORMS` set added.
- `src/09b_build_index_analysis.py` — `is_noise_term` extended.
- `src/02_clean_text.py` — Internet Archive / platform strings added to `INLINE_PATTERNS`.
- Committed: `9daf49c`

---

## Files modified this session (18–20 April 2026 — fifth batch, v0.4.7)

**Context:** Fifth-batch Cowork session spanning 18–20 April 2026. Two sub-sessions:
(a) 18 April — stale-var automation, runlog, keyphrases repair (see CHANGELOG [0.4.7]);
(b) 20 April — five source-level fixes for release-targeted HTML files + KI-09 resolution
+ `09_extract_index.py` systematic casing fix.
Commit pending; full rerun of `run_all.sh` required (rebuild from step 09 onwards).

**18 April sub-session:**

- `src/check_stale_vars.py` — new utility created: checks `_LDA_BASE` in 8 scripts
  against `json/nlp_results.json['topic_names']`; cross-verifies TAXONOMY; flags
  corpus-count literals. `--fix` mode uses line-scanner (not `re.sub()`). First run:
  7 scripts fixed, 1 already current. Integrated into `run_all.sh`.

- `src/run_all.sh` — (a) runlog generation via `exec > >(tee "$RUNLOG") 2>&1` added
  after `STREAM` setup; (b) `python3 "$SCRIPT_DIR/check_stale_vars.py" --fix` added
  after `patch_topic_names.py`.

- `figures/fig7_keyphrases.png` — regenerated with 18 April canonical topic names.

- `data/outputs/keyphrases.html` — repaired (was blank after sshfs write error);
  reconstructed by running `06_build_report.py` from sandbox.

**20 April sub-session:**

- `src/03_nlp_pipeline.py` — 13 contraction stems added to STOPWORDS (`aren, couldn,
  didn, doesn, hadn, hasn, haven, mustn, shan, shouldn, wasn, weren, wouldn`). These
  bypass the stop list because the lemmatiser strips `"'t"` before CountVectorizer runs.

- `src/06_build_report.py` — three changes:
  (a) `_PAGES` nav: `('books.html', '📝 Summaries')` → `('book_nlp_entity_network.html',
      '🕸 Network')` — all four release pages now link to entity network.
  (b) Cosine: both `542 × 542` literals → `{len(book_ids)} × {len(book_ids)}`.
  (c) Clusters: yellow interpretive caveat box added before cluster table (silhouette
      scores 0.013–0.021; no valid cluster structure; exploratory only; k may vary).

- `src/run_all.sh` — `09c_validate_topics.py --top 10 --md` moved to after
  `patch_topic_names.py` and `check_stale_vars.py --fix`. `topic_validation.md` now
  written with canonical names, not raw LDA labels.

- `src/14_entity_network.py` — KI-09 resolved: `_CONCEPT_PLURAL_EXCEPTIONS` set (35
  `-ics` field names); `_singular_form()` function (5 morphological rules + multi-word
  recursion); `concept_plural_map` built after concept classification; plural nodes
  removed from `concepts` dict; book-set union into singulars post `concept_booksets`;
  `vocab[sing_tl]['n_books']` updated; `target_tls` normalised via `concept_plural_map`.

- `src/09_extract_index.py` — systematic casing fix for `_canonical_term()`:
  (a) `LOWER_IN_TITLE` set added (articles, conjunctions, prepositions); `_ok()`
  updated — terms like `Experiments in Art and Technology`, `Laws of Form`,
  `Macy Conferences on Cybernetics` now preserved correctly;
  (b) all-caps pre-processing — multi-word ALL-CAPS strings lowercased before canonical
  check if any word > 3 chars (exempts genuine acronym sequences like `DNA RNA`);
  (c) "best casing wins" in `all_terms` vocab builder — stored all-lowercase entries
  upgraded when a later book supplies mixed-case form.
  **Rebuild from step 09 required** (`09_extract_index.py` → `09b` → `09c` → `10`
  → `12` → `14` → `15`).

- `docs/CHANGELOG.md` — [0.4.7] entry updated with `09_extract_index.py` casing fix.
- `docs/contributions.md` — 20 April session row updated with all changes.
- `CLAUDE.md` — release status and files-modified section updated.

---

## Next session agenda

*Session startup: run fresh `run_all.sh`, save runlog, review key stats before proceeding.*

1. **Topic name validation sprint** *(high priority)* — topic ordering shuffled this
   session without warning; the run-records system would have caught it. Start with
   `src/record_topic_run.py` (draft in vault `docs/src_draft/`): record run parameters,
   top words, top books, assigned names, rater, date → `json/topic_run_records.json`.
   Then `src/compare_topic_runs.py` — cross-run comparison report. Multi-rater protocol
   to follow.

2. **Document KI-08 in methodology** — add data quality entry for [2133] Cybernation
   and Social Change to `docs/methodology.md`: nature of OCR corruption, why excluded,
   what "infects the collection" means operationally. Canonical corpus framing:
   "541 monographs and collected works analysed".

3. **Classifier track** — second review round: `csv/monograph_sample_*.csv` awaiting
   Paul's review (ROADMAP #1). Feeds classifier retraining (#2, #3).

4. **Topic name ordering shuffle — note for paper** — the non-determinism of LDA topic
   ordering between runs is itself a methodological finding worth documenting: stability
   metrics are preserved but index positions rotate, making run-to-run name comparison
   unreliable without a tracking system. Relevant to methodology section.

5. **Conceptual writing** — draft or develop sections on:
   - Epistemic affordances of the pipeline
   - Human–AI collaboration framing
   - Data quality and the algorithm infection principle
   Target: `docs/methodology.md` or standalone memo(s).

6. **Review draft scripts** in vault `docs/src_draft/`:
   - `record_topic_run.py` — graduate to `src/`?
   - `compare_topic_runs.py` — graduate to `src/`?

7. **Future structural item** — plural-dedup normalisation in `src/14_entity_network.py`
   (~150 singular/plural pairs; defer until entity network otherwise stable).

---

## HTML report bugs

Bug tracking for the HTML outputs. Canonical list in `docs/ROADMAP.md` (backlog items).
KI numbers in this file refer to pipeline/data issues; ROADMAP # refers to code/UI bugs.
Note: the ROADMAP's old KI-01–KI-09 list is stale (v0.4.2) and should not be confused
with the active KI-04–KI-10 tracking in this file.

| ROADMAP # | Report file | Description | Status |
|-----------|-------------|-------------|--------|
| #16 | `data/outputs/index.html` Fig 3 + `keyphrases.html` | Topic filter dropdowns used stale names. Root cause: `patch_topic_names.py` TAXONOMY had 3 April names, overwriting `nlp_results.json` on every run. Fixed: TAXONOMY updated to 18 April taxonomy; `_LDA_BASE` fallback updated; `lda_names` added to `kp_data`; keyphrases JS fixed. HTML regenerated. | ✅ Done |
| #17 | `data/outputs/book_nlp_entity_network.html` | Provenance notice (`position:fixed;top:0`) covers app header in full-viewport flex layout. Fixed in source (`src/14_entity_network.py`): notice is now a `flex-shrink:0` static element injected before `<div class="header">`. | ✅ Verified 18 April 2026 |

---

## Session startup protocol

**Before each session:** Run a fresh `run_all.sh` on Cybersonic and save the log to
`data/outputs/runlog_YYYYMMDD.csv` (or similar). At session start, read the latest
runlog and do a quick review of:
- Book count and any exclusions
- Topic stability figures (mean stability, n stable / 9)
- Entity network summary (node counts by kind, edge counts by level, LCC %)
- Any warnings or errors in the log

This ensures the session begins from a known, current pipeline state and provides a
permanent machine-readable record of each day's run. Network stats from standalone
script reruns (e.g. `python3 src/14_entity_network.py` without `run_all.sh`) are not
captured in the runlog — if a standalone rerun is done mid-session, note the stats
manually (e.g. in CLAUDE.md or ROADMAP).

---

## Infrastructure notes

- **sshfs mount:** Cybersonic is always mounted inside the vault at
  `02 Projects/CyberneticsNLP/cybersonic/` via alias `mcyber` on Cybersonic.
  Claude can read and write files through this mount. Mount goes stale after
  ~30 min — run `mcyber` on Cybersonic to remount if directories appear empty.
- **IMPORTANT — Claude cannot run commands on Cybersonic.** Git, Python scripts,
  and anything requiring Cybersonic's environment must be run manually in a
  Cybersonic terminal. Claude edits files via the mount; Paul runs the scripts.
  Specifically: `git push`, `python3 src/*.py`, pip installs — all Cybersonic only.
- **Git push:** commit on Cybersonic (`git commit`), push from Cybersonic (`git push`)
  to `github.com:cyberneticbookshelf-stack/cyberneticsNLP.git`. SSH key must be
  configured on Cybersonic — was broken 17 April 2026, now fixed.
- **Cowork "+" button for second workspace:** known bug (GitHub #19318) — fails with
  "Session VM process not available" on FUSE/sshfs mounts. Use vault-internal mount
  as workaround.
- **Python environment:** Cybersonic, `~/CyberneticsNLP/`. Use `pip install --break-system-packages`.
- **Patch scripts:** when sshfs mount goes read-only mid-session, write patch scripts
  to vault (not cybersonic/) and run them on Cybersonic. Use str.replace() or line
  scanners rather than re.sub() for source-code patching — re.sub processes backslash
  sequences in replacement strings, which corrupts Python string literals.

---

## Known issues (active)

| ID | Issue | Status |
|----|-------|--------|
| KI-04 | Amazon/Google as high-degree nodes — ebook metadata noise | **Resolved 17 April 2026** — `KNOWN_TECH_PLATFORMS` in `src/14_entity_network.py`; noise filters in `src/09b`; committed `9daf49c` |
| KI-05 | T9: book [249] loading=1.000 dominates | Document in paper; may resolve after exclusion filter |
| KI-06 | Proceedings/handbook books not yet filtered from pipeline | Pending signal inventory + document unit decision (moratorium) |
| KI-07 | ~130 misclassified nodes + EOLSS contamination + plural/comma fragments | **Fully resolved 18 April 2026** — all fixes in `src/14` and `src/15`; rerun complete; final network 1,627 nodes |
| KI-08 | 541 vs 542 book count in LDA — one book dropped at runtime | **Resolved 18 April 2026** — [2133] Cybernation and Social Change excluded via `ocr-excluded` list; OCR corruption infects collection |
| KI-09 | ~150 singular/plural node pairs (e.g. algorithm/algorithms) — split PMI signal | **Resolved 20 April 2026** — `_singular_form()` + `concept_plural_map` in `src/14_entity_network.py`; plurals merged into singulars with book-set union; `_CONCEPT_PLURAL_EXCEPTIONS` blocks 35 `-ics` field names (cybernetics, thermodynamics, etc.) that are not genuine plurals; paragraph-window `target_tls` normalised; rerun required |
| KI-10 | Entity network concepts dropped 746→500 on fresh rebuild (sixth batch) | **Resolved 18 April 2026** — `run_all.sh` was running step 14 with `--no-windows`, excluding ~239 concept nodes that only have paragraph-level edges (no qualifying book-level co-occurrence). Not a data bug; two internally consistent networks. Fix: removed `--no-windows` from `run_all.sh` so paragraph windows always run. Canonical network: 1,620 nodes, 739 concepts. |

*Updated 20 April 2026 — Cowork session (fifth batch, v0.4.7; commit pending rerun)*
