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

## Active issue — Node misclassification sweep (KI-07 — RESOLVED in data, awaiting rerun)

**Symptom:** Comprehensive review of all 1860 nodes (18 April 2026) found ~130 misclassified
nodes. Examples: Perceptron [81] as location; Manhattan Project [86] as location; New York
Times [138] as location; Brain/Neurotransmitters/Retina/Slavery/Synthesis as organisations;
Voltaire/Homer/Sophocles as concepts; Lorente de Nó as organisation; Weiner Norbert as
duplicate person; ~50 trailing-function-word fragments ("evolution of", "wiener and",
"free will and", "ai and", "definition of", etc.) surviving as concept/location/org nodes.

**Two-part fix — applied 18 April 2026:**

1. **`src/14_entity_network.py`** — two new module-level regexes, applied *before* cache
   lookup (so they cannot be overridden by stale cache entries):
   - `_TRAILING_FUNC` — suppresses any term whose surface form ends in a function word
     ("of", "and", "on", "the", "to", "for", …). Catches ~50 fragment nodes.
   - `_CTA_BACK_MATTER` — suppresses "sign up now", "about the author", "all rights
     reserved", "first edition", "published by", etc.

2. **`json/entity_types_cache.json`** — 101 entries corrected (all pre-existing, wrong):
   - location → organisation: New York Times, San Francisco Chronicle, Vienna Circle
   - location → concept: Manhattan Project, Perceptron, Big Bang, Hippocampus, Algorithm, Truth
   - location → suppress: Systém (Czech OCR), Tortoise, ai and
   - org → person: Lorente de Nó Rafael, Cicero, St. Augustine, Epictetus, Rutherford
   - org → concept: Principia Mathematica, design for a brain, quantum computing,
     social sciences, Synergy, Brain, Neurotransmitters, Retina, Slavery, Synthesis,
     quantum entanglement, Speech, Healthcare, Recognition, actor-network theory, + 13 more
   - org → suppress: Laboratory, Bishop, University), Self-, and 15 more generic nouns
   - concept → person: Voltaire, Homer, Sophocles, Bernard (Claude Bernard)
   - concept → org: Life Magazine, CoEvolution Quarterly, Ramparts
   - concept → suppress: Galileo Galilei (dup), Stengers (dup), wiener (standalone fragment)
   - person → suppress: Weiner Norbert (misspelling), Drop, Norbert (fragment),
     One Park Avenue NY (address), Foerster Heinz von (dup), Neumann John von (dup),
     Clark (ambiguous), Humphreys (ambiguous)
   - person → location: New York NY, Cambridge Massachusetts
   - person → concept: brain human, Grammar
   - person → org: Gordon and Breach Science Publishers, Whole Earth Catalog The
   - org → suppress (duplicates): kluckhohn, von bertalanffy, vinge, waddington, free will and

**Next action:** Rerun `python3 src/14_entity_network.py` on Cybersonic to apply fixes.
`entity_types_cache.json` is gitignored — not committed; but `src/14_entity_network.py` change
(the `_TRAILING_FUNC`/`_CTA_BACK_MATTER` additions) should be committed.

**Two minor issues noted 17 April — still open:**
- "evolution of" node — now caught by `_TRAILING_FUNC` ✓ (was previously unfixed)
- "New York Times" → organisation — now fixed in cache ✓ (was previously unfixed)

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

**Fixes implemented 17 April 2026 — awaiting rerun on Cybersonic:**

- `src/09b_build_index_analysis.py` — `is_noise_term` extended with `_STRUCT_NAV`
  (structural document navigation terms) and `_PLATFORM` (digitisation attribution
  strings). Also added structural terms to `NOISE_TERMS` in `14` as belt-and-suspenders.

- `src/14_entity_network.py` — `KNOWN_TECH_PLATFORMS` set added (Google, Amazon,
  Facebook, Meta, Twitter, Apple, Microsoft, OpenAI, etc.), checked before entity
  classification loop. Platforms never enter book sets or PMI computation. `src/14_entity_network.py:155` (classification loop) and new constant above it.

- `src/02_clean_text.py` — Internet Archive / Kahle–Austin / Kindle / Google Play
  patterns added to `INLINE_PATTERNS`. Affects future regeneration of
  `json/books_clean.json` only (existing file not invalidated for current work).

**Applied and verified on Cybersonic 17 April 2026:**
- Reran `09b` and `14` twice (once after initial fixes, once after second-pass fixes)
- Final network: 1860 nodes, 12799 edges (was 1888/13061)
- Wiener top edges: cybernetics (108), communication (60), control (32) — all correct
- All EOLSS, platform, and structural noise terms confirmed absent
- Committed: `9daf49c` — "fix: clean entity network noise and document data quality methodology"

**Two minor issues noted for future attention (low priority):**
- "New York Times" classified as `location` — should be `organisation`
- "evolution of" appears as a node — fragment starting with "evolution" slips
  `_FUNC_FRAG` because filter only catches terms that *start* with a function word

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

## Files modified this session (18 April 2026)

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

---

## Next session agenda

1. **Rerun `src/14_entity_network.py` on Cybersonic** — applies KI-07 fixes;
   verify new node counts and spot-check previously bad nodes
   (Perceptron should be concept, Brain should be concept, no fragment nodes).
2. **Commit `src/14_entity_network.py`** — the `_TRAILING_FUNC`/`_CTA_BACK_MATTER`
   additions (KI-07 code fix). `entity_types_cache.json` stays gitignored.
3. **Review draft scripts** in vault `02 Projects/CyberneticsNLP/docs/src_draft/`:
   - `compare_topic_runs.py` — assess readiness to graduate to `src/`
   - `record_topic_run.py` — assess readiness to graduate to `src/`
4. **Continue topic naming reliability sprint** — all four items still open (see above)

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

---

## Known issues (active)

| ID | Issue | Status |
|----|-------|--------|
| KI-04 | Amazon/Google as high-degree nodes — ebook metadata noise | **Resolved 17 April 2026** — `KNOWN_TECH_PLATFORMS` in `src/14_entity_network.py`; noise filters in `src/09b`; committed `9daf49c` |
| KI-05 | T9: book [249] loading=1.000 dominates | Document in paper; may resolve after exclusion filter |
| KI-06 | Proceedings/handbook books not yet filtered from pipeline | Pending signal inventory + document unit decision (moratorium) |
| KI-07 | ~130 misclassified nodes in entity network | **Resolved in data 18 April 2026** — `_TRAILING_FUNC`/`_CTA_BACK_MATTER` in `src/14`; 101 cache entries corrected. **Awaiting rerun + commit.** |

*Updated 18 April 2026 — Cowork session*
