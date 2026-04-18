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

**Version:** 0.4.3 (tagged, pushed to origin/main — confirmed 16 April 2026)
**Repo:** `~/CyberneticsNLP/` on Cybersonic (accessed via sshfs mount inside vault)
**Vault path:** `02 Projects/CyberneticsNLP/cybersonic/CyberneticsNLP/`
**Canonical run:** Run C — `json/nlp_results_k9.json` — 542 books, k=9, 5/9 stable,
mean stability=0.327. Run C locked as canonical 14 April 2026.
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
- Final node count: **1,627** (persons=656, orgs=154, locations=71, concepts=746)
- Previous baseline: 1,708 (concepts=827 after fourth batch rerun)
- Concept reduction: 827 → 746 (81 fewer; 8 of 89 suppressed terms not present in network)
- Network: density=0.0087, LCC=1625/1627 (100%), APL=3.248, diameter=5, max degree=283

**Status: RESOLVED — entity network ready for colleague sharing.**

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
- Patch scripts (vault, not in repo):
  - `02 Projects/CyberneticsNLP/patch_apply.py` — applied 15_entity_classify.py
    changes and initial (broken) _PROV_NOTICE update.
  - `02 Projects/CyberneticsNLP/fix_prov_notice.py` — fixed the broken _PROV_NOTICE
    using line-scanner instead of re.sub.
  - `02 Projects/CyberneticsNLP/patch_15_entity_classify.py` — intermediate draft,
    superseded by patch_apply.py.

---

## Next session agenda

1. **Commit fifth batch changes on Cybersonic:**
   `git add src/14_entity_network.py src/15_entity_classify.py src/06_build_report.py`
   `src/06_build_report_chapters.py src/08_build_timeseries.py src/10_build_index_report.py`
   `src/11_embedding_comparison.py src/12_index_grounding.py src/13_weighted_comparison.py`
   `src/build_embed_report.py && git commit -m "fix: degree 1-2 concept node suppressions and sticky provenance banner (v0.4.6)"`
2. **Investigate KI-08** — 541 vs 542 book count: which book is dropped at LDA runtime
   and whether this is intentional or a bug.
3. **Review draft scripts** in vault `02 Projects/CyberneticsNLP/docs/src_draft/`:
   - `compare_topic_runs.py` — assess readiness to graduate to `src/`
   - `record_topic_run.py` — assess readiness to graduate to `src/`
4. **Continue topic naming reliability sprint** — all four items still open (see above).
5. **Future structural item:** plural-dedup normalisation step in `src/14_entity_network.py`
   (~150 same-kind singular/plural pairs; defer until entity network otherwise stable).
6. **Share entity network HTML** with colleagues — network now clean enough for external
   viewing. Provenance banner visible at top of page on all scroll positions.

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
| KI-08 | 541 vs 542 book count in LDA — one book dropped at runtime | **Open** — not yet investigated |
| KI-09 | ~150 singular/plural node pairs (e.g. algorithm/algorithms) — split PMI signal | **Open** — structural fix (lemmatisation in `src/14`) deferred as future sprint item |

*Updated 18 April 2026 — Cowork session (fifth batch)*
