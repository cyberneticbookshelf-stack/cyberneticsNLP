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

**To apply on Cybersonic:**
```bash
cd ~/CyberneticsNLP
python3 src/09b_build_index_analysis.py   # rebuilds json/index_analysis.json
python3 src/14_entity_network.py          # rebuilds json/entity_network.json
```

**Methodological note:** `docs/methodology.md:2074` §"Residual error propagation and
the limits of upstream cleaning" — revised 17 April 2026 to accurately distinguish
the two sources and clarify when output exclusion is vs. is not sufficient.

---

## Files modified this session (17 April 2026)

- `docs/methodology.md` — new section added then revised:
  §"Residual error propagation and the limits of upstream cleaning" (~line 2074)
- `src/09b_build_index_analysis.py` — `is_noise_term` extended (~line 94–144)
- `src/14_entity_network.py` — `KNOWN_TECH_PLATFORMS` added, wired into
  classification loop (~line 141–162)
- `src/02_clean_text.py` — platform strings added to `INLINE_PATTERNS` (~line 387)
- `CLAUDE.md` — created this session; seeded with full project context

---

## Next session agenda

1. **Run fixes on Cybersonic** — `python3 src/09b_build_index_analysis.py` then
   `python3 src/14_entity_network.py`; inspect entity network to confirm Wiener–Google
   edge is gone and structural terms no longer appear as nodes
2. **Review draft scripts** in vault `02 Projects/CyberneticsNLP/docs/src_draft/`:
   - `compare_topic_runs.py` — assess readiness to graduate to `src/`
   - `record_topic_run.py` — assess readiness to graduate to `src/`
3. **Continue topic naming reliability sprint** — all four items still open (see above)
4. **Commit** — stage and commit all four modified files plus CLAUDE.md

---

## Infrastructure notes

- **sshfs mount:** runs on Cybersonic via alias `mcyber`. Mount point inside vault:
  `02 Projects/CyberneticsNLP/cybersonic/`. Mount goes stale after ~30 min — run
  `mcyber` to remount if directories appear empty.
- **Cowork "+" button for second workspace:** known bug (GitHub #19318) — fails with
  "Session VM process not available" on FUSE/sshfs mounts. Use vault-internal mount
  as workaround.
- **Python environment:** Cybersonic, `~/CyberneticsNLP/`. Use `pip install --break-system-packages`.

---

## Known issues (active)

| ID | Issue | Status |
|----|-------|--------|
| KI-04 | Amazon/Google as high-degree nodes — ebook metadata noise | Fix pending: strip in `src/02_clean_text.py` upstream of PMI |
| KI-05 | T9: book [249] loading=1.000 dominates | Document in paper; may resolve after exclusion filter |
| KI-06 | Proceedings/handbook books not yet filtered from pipeline | Pending signal inventory + document unit decision (moratorium) |

*Updated 17 April 2026 — Cowork session*
