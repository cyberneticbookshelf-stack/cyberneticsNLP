# Re-canonicalisation checklist — post-reconstruction canonical run

**Status:** Staged, not yet applied. Blocked on the `--rebuild-clean` run.
**Trigger:** Calibre DB reconstruction (July 2026) → stale clean cache (KI-13) →
the 26 April canonical run (`run_20260426_k9_s5`, 541 books, equivalence class
`23b29233a67b2938`) no longer describes the analysed corpus.

This note lists (1) the numbers to capture from the rebuild run and (2) every
committed location that hardcodes the old canonical facts, with the exact edit to
make once the numbers are in. **Do not apply Section 2 until Section 1 is done and
the run is reviewed** — placeholders below (`«…»`) must be replaced with real
values, not guessed.

---

## 0. Run the rebuild (on the NLP machine)

```
bash src/run_all.sh --stream --rebuild-clean
```

This discards `json/books_clean.jsonl`, re-cleans every shard from the
reconstructed corpus, writes `json/books_clean.manifest.json`, and runs the full
pipeline. Expect the analysed count to rise from 544 toward ~556 (12 English
recoveries — see KI-13), pending content-language detection and the min-chars gate.

---

## 1. Capture the new canonical facts

Run these after the pipeline completes, then fill the table:

```bash
# n_books analysed (post all filters)
python3 -c "import json;print(len(json.load(open('json/nlp_results.json'))['book_ids']))"

# equivalence class + nlp_hash + run_id  (review the runlog FIRST, then log it)
python src/log_pipeline_run.py --runlog data/outputs/runlog$(date +%Y%m%d).csv

# topic stability (mean + bands) — read from the runlog 09c block or:
python3 -c "import json;s=json.load(open('json/topic_stability.json'));print(s)"

# topic names as fitted+patched (NB: may differ from 26 Apr — see §3)
python3 -c "import json;print(json.load(open('json/nlp_results.json'))['topic_names'])"
```

| Fact | Old (26 Apr) | New (fill in) |
|------|--------------|----------------|
| n_books analysed | 541 | «N_ANALYSED» |
| n_books parsed | 542 | «N_PARSED» |
| equivalence class | `23b29233a67b2938` | «EQUIV_CLASS» |
| run_id | `run_20260426_k9_s5` | «RUN_ID» |
| nlp_hash | `901e5ec924248fe2` | «NLP_HASH» |
| mean stability | 0.348 | «MEAN_STAB» |
| stable / moderate / unstable | 5 / 3 / 1 | «S» / «M» / «U» |
| OCR-excluded | [2133] (still id 2133 ✓) | verify still 1 |

**ID-stability check (should stay clean after reconstruction):**
```bash
# OCR_EXCLUDED={'2133'} must still resolve to Cybernation and Social Change
python3 -c "import sqlite3;print(sqlite3.connect('file:data/inputs/calibre/metadata.db?mode=ro',uri=True).execute(\"SELECT id,title FROM books WHERE id=2133\").fetchone())"
```
`lang_override.csv` is header-only and `MANUAL_CORRECTIONS` is keyed by entity
string, so neither carries id risk. If either gains id-keyed rows later, re-audit.

---

## 2. Files to update (apply after §1)

### Group A — canonical framing (MUST change)

- **`CLAUDE.md:25`** — corpus framing. Replace `"541 monographs and collected
  works analysed" from a 695-book Calibre collection` with
  `"«N_ANALYSED» monographs and collected works analysed" from a «739»-book
  reconstructed Calibre collection (rebuilt July 2026)`. Keep the [2133] OCR
  exclusion clause.
- **`CLAUDE.md:26`** — canonical-k line. Replace `run_20260426_k9_s5`,
  `23b29233a67b2938` with «RUN_ID» / «EQUIV_CLASS»; update the "confirmed on the
  first full-text canonical run … 26 April 2026" clause to note the July 2026
  re-canonicalisation after the DB reconstruction. **Keep** the sprint-item-4
  caveat (names still single-rater/single-run — now doubly so, since the corpus
  changed).
- **`CLAUDE.md:407` (KI-06 note)** — "consistent with canonical framing (541 …)"
  → «N_ANALYSED».
- **`CLAUDE.md:409` (KI-08)** — "542 parsed, 541 analysed" → «N_PARSED» parsed,
  «N_ANALYSED» analysed. Confirm [2133] is still the only OCR exclusion.
- **`README.md:24`** — `695 books in collection … · 541 … analysed` →
  `«739» … · «N_ANALYSED» … analysed`.
- **`README.md:252`** — "for 541 books from scratch" → «N_ANALYSED».
- **`src/patch_topic_names.py:16`** — taxonomy header `(541-book corpus, 25 April
  2026)` → `(«N_ANALYSED»-book corpus, July 2026 re-canonicalised)`. See §3 re
  the TAXONOMY body.
- **`docs/refactor_plan.md:15,18`** — the plan's baseline references
  `run_20260426_k9_s5` / `23b29233a67b2938` / "541-monograph framing". Add a note
  that the baseline moved to «RUN_ID» after the July reconstruction (the refactor's
  "same equivalence class" acceptance test must target «EQUIV_CLASS», not the old
  one).

### Group B — hardcoded counts in generated-report provenance (dynamicise, don't re-hardcode)

These are `# … N-book corpus` comments that get surfaced in report provenance. Per
the standing "counts rot" principle (CLAUDE.md; already applied in
`06_build_report.py` via `{len(book_ids)}`), prefer **removing the number** or
deriving it, rather than swapping to «N_ANALYSED»:

- `src/14_entity_network.py:31` — "541-book corpus"
- `src/11_embedding_comparison.py:51` — "542-book corpus"
- `src/06_build_report_chapters.py:15` — "542-book corpus"
- `src/12_index_grounding.py:18` — "542-book corpus"
- `src/08_build_timeseries.py:22` — "542-book corpus"
- `docs/methodology.md:2208` — provenance line still says "542-book corpus";
  CLAUDE.md §methodology claims counts were removed from the provenance statement.
  Reconcile: strip the count here to match the canonical provenance wording.

(These already disagree — 541 vs 542 — so this group is worth doing regardless.)

### Group C — presentation deck (`presentation/patch_deck.py`)

- `:48` and `:277` — comments referencing `run_20260426_k9_s5` and
  `mean=0.348, 5/9 stable, T7 unstable` → «RUN_ID» / «MEAN_STAB» / «S»/«M»/«U».
- `edit_slide_11()` — stability figures 0.348 / 5 of 9 → new values.
- `CANONICAL_NAMES` block and `edit_slide_14()` era→topic attributions — **do NOT
  blindly renumber.** A new corpus can permute topic positions and shift names.
  Re-derive from the new `nlp_results.json['topic_names']` and
  `data/outputs/topic_validation.md`. See §3.

### Group D — DO NOT edit (historical record)

`docs/CHANGELOG.md`, `docs/contributions.md`, `docs/archive/*`,
`docs/memos/*`, `docs/full_text_canonical_switch.md` — these are dated logs of what
was true then. Leave the old counts in place. Instead add a **new** CHANGELOG entry
and a new `contributions.md` row for the re-canonicalisation session.

---

## 3. Topic names & positions are NOT carried over

The 9 topic names were finalised on the 541-book fit (single rater, single run).
A ~556-book fit is a **new equivalence class**: topic composition, ordering, and
stability all change. Consequences:

- `patch_topic_names.py` TAXONOMY overlays names by position — if positions
  shifted, the overlay will mislabel. **Re-validate** names against the new
  `topic_validation.md` (`09c_validate_topics.py --top 10 --md`) before trusting
  the deck or reports.
- The `T3 ↔ T9 "Extensions of Cybernetics"` name-collision caveat (see 26 Apr
  contributions row) must be re-checked under the new fit.
- Sprint item 4 (names stable only after ≥3 runs × ≥2 raters) is **still open** —
  the reconstruction reset any progress toward it. Keep the "provisional" framing.

---

## 4. Provenance / dissemination

The standing "all outputs are provisional" notice already avoids a hardcoded count
(CLAUDE.md removed it deliberately — a precise number in a data-quality warning is
itself a risk). Keep it count-free. If any shipped HTML still embeds a count via
Group B, that's the place to remove it.

---

## Done-when

- [ ] `--rebuild-clean` run completed; §1 table filled.
- [ ] Group A applied; Group B counts removed/dynamicised; Group C deck re-derived.
- [ ] Topic names re-validated (§3); "provisional" caveat retained.
- [ ] New CHANGELOG + contributions rows added (Group D).
- [ ] Run logged (`log_pipeline_run.py`) under «RUN_ID» / «EQUIV_CLASS».
- [ ] KI-13 in ROADMAP + CLAUDE.md flipped from "re-canonicalisation open" to done.
- [ ] This checklist deleted or archived.

---

## Appendix — ready-to-paste log entries (Group D)

Two parts. **Part 1 is concrete** (this session's guard/diagnosis work — paste as-is
when you cut the release). **Part 2 has `«…»` placeholders** for the rebuild run —
fill from §1 before pasting. Version numbers are tentative: `0.5.5` for the guard,
`0.5.6` for the re-canonicalised run. Adjust if you ship them together as one bump.

> **Attribution note:** `contributions.md` currently credits *Claude Sonnet 4.6*
> (`claude-sonnet-4-6`). This session ran on **Claude Opus 4.8** (`claude-opus-4-8`)
> via the **Claude Code CLI** — a model and platform not yet listed in the Authors /
> platform sections. Before adding the rows below, either (a) add an Opus 4.8 author
> entry + a "CLI" platform bullet, or (b) decide these contributions fold into the
> existing single-author convention. Flagging rather than guessing — your call.

### Part 1 — CHANGELOG.md (paste above the `[0.5.4]` heading)

```markdown
## [0.5.5] — 2026-07-17

> Session: 17 July 2026 (Claude Code CLI) — KI-13 diagnosed and guarded; stale
> clean cache after the July Calibre reconstruction identified; re-canonicalisation
> staged.

### Fixed

- **`src/run_all.sh` + `src/check_clean_cache.py` (new)** — clean-cache staleness
  guard (KI-13). `parse_and_clean_stream.py` skips books by id, so the July 2026
  Calibre DB reconstruction (ids reassigned, books re-added) was never re-ingested:
  `run_20260716-5` analysed 544 books from a pre-reconstruction cache. New
  `check_clean_cache.py` SHA-256-fingerprints each `csv/books_text_*.csv` shard
  against `json/books_clean.manifest.json` (written at the last full rebuild);
  `run_all.sh --stream` aborts on mismatch. New `--rebuild-clean` flag moves the
  stale `books_clean.jsonl` aside, re-cleans every shard, and rewrites the manifest.
  A timestamp guard was rejected as insufficient — the cache was rewritten (15:02)
  after the shards (14:51) yet still missing shard-25's book 2797.
- **`src/split_books_text.sh`** — `TOTAL_ROWS` derived dynamically from the PDF row
  count (was hardcoded, silently truncating the tail as the corpus grew);
  `WHERE format='PDF'` + `ORDER BY book` added. With 169 books now dual-format
  (EPUB+PDF) after the reconstruction, the format filter prevents same-id row
  collisions in `01_parse_books.py`.

### Documentation

- **`docs/ROADMAP.md`, `CLAUDE.md`** — KI-13 added (stale clean cache after DB
  reconstruction; fix landed, re-canonicalisation open).
- **`docs/recanonicalisation_checklist.md` (new)** — staging note: numbers to
  capture from the rebuild run and every committed location hardcoding the old
  541-book / `run_20260426_k9_s5` canonical facts.

### Diagnosis (no code impact)

- Sweep of reconstruction casualties: 27 books have PDF text in the reconstructed
  `metadata.db` but were absent from the analysed cache — 12 English (3 re-IDed
  Emery works: old 2188/2382/2383 → new 2799/2801/2797; + 9 brand-new incl. Luhmann
  *Ecological Communication*, Kevin Kelly *Out of Control*, Jackson *Systems
  Approaches to Management*) and 15 non-English correctly excluded by the language
  filter. 0 stale ghosts (no orphaned old-id books in the cache).
```

### Part 1 — contributions.md (new Session Log row, insert after the `2026-04-26` row)

```markdown
| 2026-07-17 | CLI | KI-13 — stale clean cache after Calibre DB reconstruction: diagnosed that `parse_and_clean_stream.py`'s id-keyed skip silently ignored the July 2026 reconstructed corpus (`run_20260716-5` analysed 544 books from a pre-reconstruction cache). Title-based cross-match (ids unstable across the rebuild) + `books_text`/`metadata.db` queries established 0 deletions: the 4 apparently-removed books were the 3 Emery works re-IDed (author normalised `Fred E.` → `Frederick Edmund`) plus new acquisitions. Full sweep: 27 books with PDF text missing from cache (12 English recoveries, 15 non-English lang-excluded). **Fix:** new `src/check_clean_cache.py` (SHA-256 shard fingerprints vs `json/books_clean.manifest.json`); `src/run_all.sh` `--rebuild-clean` flag + abort-on-stale guard (timestamp guard rejected — cache rewritten after shards yet incomplete); guard lifecycle unit-tested (6 cases). `src/split_books_text.sh` dynamic `TOTAL_ROWS` + `WHERE format='PDF'`/`ORDER BY book` (169 dual-format books post-reconstruction). KI-13 added to ROADMAP + CLAUDE.md; `docs/recanonicalisation_checklist.md` drafted. Re-canonicalisation (new equivalence class) staged, pending the rebuild run. | v0.5.5 |
```

### Part 2 — CHANGELOG.md, after the rebuild run (fill placeholders)

```markdown
## [0.5.6] — «YYYY-MM-DD»

> Session: «date» — re-canonicalised run on the reconstructed corpus (KI-13 follow-up).

### Changed

- **Canonical run re-established on the reconstructed corpus.** `run_all.sh --stream
  --rebuild-clean` produced «N_ANALYSED» analysed books («N_PARSED» parsed), a new
  equivalence class «EQUIV_CLASS» (was `23b29233a67b2938`, 541 books). Logged as
  «RUN_ID», nlp_hash «NLP_HASH». Mean stability «MEAN_STAB»; «S» stable / «M»
  moderate / «U» unstable.
- **Topic names re-validated** against the new fit (positions can permute across
  equivalence classes — not carried over from the 541-book taxonomy). «summarise any
  name/position changes, or "positions stable; names unchanged"». Still provisional
  (single rater — sprint item 4 open).
- **Corpus framing updated** `541 → «N_ANALYSED»` analysed / `695 → 739` collection
  across `CLAUDE.md`, `README.md`, `patch_topic_names.py`; hardcoded provenance
  counts in report scripts removed/dynamicised (see checklist Group B).

### Documentation

- **`docs/recanonicalisation_checklist.md`** — completed and archived.
```

### Part 2 — contributions.md row, after the rebuild run (fill placeholders)

```markdown
| «YYYY-MM-DD» | «platform» | Re-canonicalisation on reconstructed corpus (KI-13 follow-up): `run_all.sh --stream --rebuild-clean` recovered the reconstruction casualties; «N_ANALYSED» analysed books, new equivalence class «EQUIV_CLASS», logged «RUN_ID» (nlp_hash «NLP_HASH»), mean stability «MEAN_STAB» («S»/«M»/«U»). Topic names re-validated against the new fit: «changes or "stable"». Corpus framing 541→«N_ANALYSED» propagated across CLAUDE.md/README/patch_topic_names.py; provenance counts dynamicised. KI-13 closed. | v0.5.6 |
```
