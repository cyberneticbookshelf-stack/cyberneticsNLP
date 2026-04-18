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

**Version:** 0.4.6 (committed `526e964`, pushed to origin/main — 18 April 2026)
**Repo:** `~/CyberneticsNLP/` on Cybersonic (accessed via sshfs mount inside vault)
**Vault path:** `02 Projects/CyberneticsNLP/cybersonic/CyberneticsNLP/`
**Canonical run:** Run C — `json/nlp_results_k9.json` — 542 books parsed, 541 analysed
(1 excluded: [2133] Cybernation and Social Change — OCR), k=9, **6/9 stable**,
**mean stability=0.357**. Run C updated to reflect sixth-batch rerun (18 April 2026);
decision pending on whether to formally supersede the 14 April lock.
**Canonical `run_all.sh`:** Step 14 runs **without** `--no-windows` (18 April 2026).
Paragraph-window edges are included in all canonical builds. Network: 1,620 nodes
(concepts=739), 11,501 edges (book=10,362 + para=1,139). Runs with `--no-windows`
produce a materially different, smaller network (concepts=500) and are not canonical.
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

**Files in scope for release:**
- `data/outputs/index.html` — main report (Fig 1–6 + topic proportions)
- `data/outputs/books.html` — per-book summaries and topic assignments
- `data/outputs/clusters.html` — cluster composition
- `data/outputs/keyphrases.html` — keyphrase analysis
- `data/outputs/cosine.html` — cosine similarity
- `data/outputs/book_nlp_entity_network.html` — entity relational network

**Known issues affecting these files (prioritised):**

| Priority | Issue | File | Status |
|----------|-------|------|--------|
| High | ROADMAP #16: Fig 3 topic filter uses stale NMF names | index.html | Open |
| High | KI-10: concept node count 746→500 on fresh rebuild — resolved (`--no-windows` removed from `run_all.sh`) | entity_network.html | ✅ Resolved |
| Medium | KI-09: ~150 singular/plural node pairs split PMI signal | entity_network.html | Deferred |
| Low | Chapter NMF T4 contains metadata noise words | (chapter reports, not in scope) | Note only |

**What "defensible" means here:**
- All known systematic errors (platform contamination, EOLSS noise, trailing fragments,
  node misclassifications) are fixed or mitigated — done.
- Provenance notice visible at all scroll positions — done.
- Topic names in all reports match the current provisional LDA names — needs ROADMAP #16 fix.
- Entity network validated against domain knowledge — done (KI-07 resolved).
- KI-10 understood well enough to decide whether 500 or 746 concepts is correct — pending.
- No individual certified finding; results framed as automated provisional analysis — done.

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

## Files modified this session (17 April 2026)

- `docs/methodology.md` — new section ~line 2074:
  §"Residual error propagation and the limits of upstream cleaning"
- `src/09b_build_index_analysis.py` — `is_noise_term` extended; `_AUTHAFFIL` fixed;
  book-level exclusion from `book_styles.json` added (~line 94–220)
- `src/14_entity_network.py` — `KNOWN_TECH_PLATFORMS` + structural terms added to
  `NOISE_TERMS`; wired into classification loop (~line 141–162)
- `src/02_clean_text.py` — Internet Archive / platform strings added to
  `INLINE_PATTERNS` (~line 387)
- `CLAUDE.md` — created this session
- `json/book_styles.json` — EOLSS vols 1–3 (IDs 2232/2233/2711) reclassified
  `reference`, `verified=True` (not committed — json/ is gitignored)

## Files modified this session (18 April 2026 — third batch)

- `src/14_entity_network.py` — `_TRAILING_FUNC` and `_CTA_BACK_MATTER` regexes added
  after `KNOWN_TECH_PLATFORMS` (~line 167–185); both wired into classification loop
  before cache lookup (~line 200). Suppresses ~50 trailing-function-word fragment nodes
  and CTA/back-matter strings regardless of cache content.
- `src/15_entity_classify.py` — two changes:
  (a) Stage 2 spaCy loop: guard added (`if cache.get(tl,{}).get('source')=='manual': continue`)
      so spaCy never overwrites MANUAL_CORRECTIONS entries, even on `--refresh` runs.
  (b) `MANUAL_CORRECTIONS` dict: 98 new entries + 1 existing entry corrected
      (`macy conferences on cybernetics` concept→suppress). Full KI-07 correction set
      now hardcoded in source — survives cache wipes and `--refresh`. (183 total entries.)
- `json/entity_types_cache.json` — 101 entries corrected (all pre-existing wrong entries;
  see KI-07 above for full list). Not committed — json/ is gitignored.
- `docs/CHANGELOG.md` — [0.4.4] entry added.
- `CLAUDE.md` — KI-07 added; files-modified and next-session sections updated.
- All 9 HTML-generating scripts — `_PROV_NOTICE` constant added; `html.replace('</body>',
  _PROV_NOTICE + '\n</body>', 1)` inserted before each `f.write(html)`. Committed `e2273e7`.

## Files modified this session (18 April 2026 — fourth batch)

**Context:** run_all.sh rerun (KI-07) completed. runlog20260418.csv reviewed.
Confirmed: pipeline ran 01:53–02:12 AEST, completed cleanly, node count 1,860 → 1,459.
Manual spot-check found residual issues, leading to full entity cache audit.

- `src/14_entity_network.py` — `_CTA_BACK_MATTER`: `author` → `authors?`; new
  `_EOLSS_NOISE` and `_TRAILING_COLON` regexes added and wired in.
- `src/15_entity_classify.py` — MANUAL_CORRECTIONS fourth batch: 7 singular/plural
  misclassifications, `brain, human` concept→suppress, `about the author/authors`,
  `not`, `requisite variety, law of`, `perceptrons` → suppress (18 new entries).
- `data/outputs/concept_node_review.csv` (vault) — 294-row review spreadsheet of all
  degree 1–2 concept nodes; columns: term, degree, n_books, ner_source, recommendation,
  reason, paul_decision. 89 Suppress / 205 Keep recommended.

**Output file note:** `book_nlp_results.html` split into `index.html`, `books.html`,
`clusters.html`, `keyphrases.html`, `cosine.html` in `data/outputs/`.

**Open discrepancy:** pipeline logged 541 books for LDA; canonical corpus is 542.
One book dropped at runtime — not yet investigated (KI-08).

## Files modified this session (18 April 2026 — sixth batch)

**Context:** Full pipeline rerun (`runlog20260418-2.csv`) after fifth batch commit `526e964`.
OCR exclusion of [2133] Cybernation and Social Change confirmed in pipeline output.

**No source files modified this session.** Pipeline run only. Outputs regenerated:
- `data/outputs/runlog20260418-2.csv` — full run log, 05:37–05:56 AEST
- `json/nlp_results.json` — 541-book corpus, k=9, mean stability=0.357, 6/9 stable
- `json/entity_network.json` — 1,380 nodes; density=0.0109; APL=3.24; diameter=7
- `data/outputs/book_nlp_entity_network.html` — regenerated (1651 KB)
- All other HTML/Excel outputs in `data/outputs/` — regenerated

**Findings from runlog review:**
- KI-08 resolved: [2133] excluded via `ocr-excluded` list (542→541 confirmed)
- Topic stability improved: mean 0.357 (was 0.327), 6/9 stable (was 5/9)
- Entity network concept nodes dropped 746→500; KI-10 opened to investigate
- Chapter NMF topic T4 contains metadata noise: "minor sections", "sections", "rights"
  — suggests publication boilerplate leaking into chapter summaries (minor issue)
- One benign numpy warning in `src/05_visualize_chapters.py` (`where` without `out`)
- sklearn stop-word warning (contractions) is pre-existing and benign

---

## Files modified this session (18 April 2026 — fifth batch)

**Context:** Degree 1–2 concept node review. Paul confirmed all recommendations from
`concept_node_review.csv`. 89 suppressions implemented. Provenance notice redesigned.

- `src/15_entity_classify.py` — MANUAL_CORRECTIONS fifth batch: 89 suppressions
  (17 bare adjectives, 28 noise/irrelevant, 36 too-generic, 6 near-duplicates).
  Applied via `patch_apply.py` run on Cybersonic.
- All 9 HTML-generating scripts — `_PROV_NOTICE` updated:
  (a) Hardcoded corpus count removed ("542-book corpus" → "the CyberneticsNLP corpus").
      Rationale: KI-08 unresolved; fragile count in a data-quality notice is itself
      a data-quality risk.
  (b) `position:fixed;top:0` replaces static bottom placement — banner now visible
      at all scroll positions. `body{padding-top:54px}` added to prevent content overlap.
  Applied via `fix_prov_notice.py` (corrected version of `patch_apply.py`, which had
  a `re.sub` backslash-processing bug causing unterminated string literals).
- `json/entity_network.json` — rebuilt: 1,627 nodes (persons=656, orgs=154,
  locations=71, concepts=746); 11,558 edges; density=0.0087; APL=3.248; diameter=5.
- `data/outputs/book_nlp_entity_network.html` — regenerated (1,849 KB).
- Patch scripts (vault, moved to bin after use — not in repo).
- **Committed `526e964`, pushed to origin/main 18 April 2026.**

---

## Next session agenda

*Items 1–3 are release-blocking for colleague HTML sharing. Items 4+ are lower priority.*

1. **Fix ROADMAP #16** *(release-blocking for index.html)* — Fig 3 topic filter dropdown
   uses stale NMF names. Fix in `src/06_build_report.py` to read `topic_names` from
   `json/nlp_results.json` at build time. Requires Cybersonic script run after fix.

3. **Canonical run decision** — formally update canonical run from 14 April lock
   (mean stability=0.327, 5/9) to sixth-batch figures (mean stability=0.357, 6/9).
   Depends on KI-10 resolution. Once locked, update snapshot in this file.

4. **Document KI-08 in methodology** — add a data quality entry for [2133] Cybernation
   and Social Change to `docs/methodology.md`: nature of OCR corruption, why excluded,
   what "infects the collection" means operationally.

5. **Entity network interface review** — review `book_nlp_entity_network.html` for any
   remaining presentation-quality issues before colleague release.

6. **Topic name validation method** — review and develop the validation approach;
   connect to topic naming reliability sprint items (run-records, multi-rater protocol).

7. **Conceptual writing** — draft or develop sections on:
   - Epistemic affordances of the pipeline
   - Human–AI collaboration framing for the methodology
   - Data quality issues and the algorithm infection principle
   Target: `docs/methodology.md` or standalone memo(s).

8. **Review draft scripts** in vault `02 Projects/CyberneticsNLP/docs/src_draft/`:
   - `compare_topic_runs.py` — assess readiness to graduate to `src/`
   - `record_topic_run.py` — assess readiness to graduate to `src/`

9. **Future structural item:** plural-dedup normalisation step in `src/14_entity_network.py`
   (~150 same-kind singular/plural pairs; defer until entity network otherwise stable).

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
| KI-09 | ~150 singular/plural node pairs (e.g. algorithm/algorithms) — split PMI signal | **Open** — structural fix (lemmatisation in `src/14`) deferred as future sprint item |
| KI-10 | Entity network concepts dropped 746→500 on fresh rebuild (sixth batch) | **Resolved 18 April 2026** — `run_all.sh` was running step 14 with `--no-windows`, excluding ~239 concept nodes that only have paragraph-level edges (no qualifying book-level co-occurrence). Not a data bug; two internally consistent networks. Fix: removed `--no-windows` from `run_all.sh` so paragraph windows always run. Canonical network: 1,620 nodes, 739 concepts. |

*Updated 18 April 2026 — Cowork session (sixth batch)*
