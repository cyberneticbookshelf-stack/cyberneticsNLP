# CyberneticsNLP — Documentation Consolidation
**Date:** 14 April 2026 · **Prepared by:** Claude (Cowork, Session 2)
**Purpose:** Master reference of current project state before updating slide deck and PDF

---

## 1. Canonical Facts as of 14 April 2026

### Corpus
| Item | Value | Source |
|------|-------|--------|
| Total books in Calibre | 726 | books_metadata_full.csv |
| Books in NLP corpus | 695 | After export/cleaning (v0.4.1) |
| Books after pub-type filter | 542 | Monographs + collected works only (v0.4.3) |
| Chapters | 7,349 | Unchanged |
| Date range | 1954–2025 | Unchanged |

### Pipeline version
- **Current:** v0.4.3 (14 April 2026) — full-text LDA refactor, k-selection sweep, run-id flag
- **Previous:** v0.4.2 (8 April 2026) — monograph classifier, report quality fixes
- **Previous:** v0.4.1 (3 April 2026) — k=9 canonical, book style pipeline

### Pipeline scripts
~34 scripts in `src/` (up from 26 at time of slide deck, March 2026). See `README.md` for full listing.

### Canonical machine
**Cybersonic** (`~/CyberneticsNLP/`) — confirmed 14 April 2026. NorbertX/OneDrive retired.

### Documentation
- `docs/methodology.md` — 2,000+ lines
- `docs/decisions.md` — 1,600+ lines (likely longer now)
- `docs/CHANGELOG.md` — versioned history to v0.4.2 (v0.4.3 entry pending)
- `docs/contributions.md` — CRediT taxonomy + session log (pending 8 April + 14 April entries)

---

## 2. Topic Solutions — All Runs

Four runs now exist. All run from Cybersonic on 14 April 2026 except the 3 April canonical.

### Run A — 3 April 2026 canonical (sampled, k=9)
**File:** `json/nlp_results.json` (MAY BE OVERWRITTEN — see note below)
**Corpus:** 695 books · **Mode:** sample (3×20k chars) · **Flags:** `--min-chars 10000 --lemmatize --topics 9 --seeds 5`
**Stability:** mean=0.382 · 7/9 stable · 0 dead

| # | Name |
|---|------|
| T1 | Management Cybernetics |
| T2 | Second-Order Cybernetics Applied to Social Systems |
| T3 | Dynamical Systems, Homeostasis & Biological Regulation |
| T4 | Psychological Cybernetics |
| T5 | Non-Anglophone Engineering Cybernetics |
| T6 | Mathematical Foundations of Cybernetics |
| T7 | Cultural Cybernetics, Posthumanism & Digital Media |
| T8 | Applied Cybernetics & Computers in Society |
| T9 | Residual / Outlier Cluster |

> ⚠️ **Note:** The Session 1 full-text run (below) had no `--run-id` and wrote to `nlp_results.json`, potentially overwriting this. Verify on Cybersonic.

---

### Run B — 14 April 2026 Session 1 (full-text, k=9, no run-id)
**File:** `json/nlp_results.json` (overwrote Run A if pipeline completed)
**Corpus:** ~690 books (min-chars 10000 filter, no pub-type filter) · **Mode:** full-text
**Flags:** `--full-text --max-features 15000 --min-chars 10000`
**Stability:** mean=0.352 · 6/9 stable · 1 unstable
**Names agreed:** Paul Wong, 14 April 2026 (Session 1)

| # | Name | Stability |
|---|------|-----------|
| T1 | Second-Order Systems Theory & Constructivism | 0.484 |
| T2 | Digital Media Arts, Posthumanism & Cultural Studies | 0.453 |
| T3 | *(UNSTABLE — do not name)* | 0.132 |
| T4 | System Dynamics (Forrester School) | 0.349 |
| T5 | Political & Governance Cybernetics | 0.336 |
| T6 | Biological Cybernetics: Homeostasis & Allostasis | 0.189 |
| T7 | Systemic Psychotherapy & Family Therapy | 0.357 |
| T8 | Popular, Literary & Metaphorical Cybernetics | 0.598 |
| T9 | History of Cybernetics | 0.271 |

---

### Run C — 14 April 2026 Session 2 k-sweep comparison (full-text, k=8/9/10/12, with run-id)
**Files:** `json/nlp_results_k8.json`, `json/nlp_results_k9.json`, `json/nlp_results_k10.json`, `json/nlp_results_k12.json`
**Corpus:** 542 books (pub-type filter: monographs + collected works only)
**Flags:** `--full-text --seeds 5 --max-features 15000 --lemmatize --run-id k{N}`

**k-selection result: k=9 recommended** (mean stability 0.327, highest-stability topic T9=0.622)

| k | Perplexity | Mean stability | Stable ≥0.3 | Unstable <0.15 |
|---|-----------|----------------|-------------|----------------|
| 8 | 3436.7 | 0.333 | 5/8 | 1/8 |
| 9 | 3413.6 | 0.327 | 5/9 | 1/9 |
| 10 | 3382.4 | 0.300 | 5/10 | 3/10 |
| 12 | 3360.6 | 0.271 | 6/12 | 3/12 |

**k=9 names agreed:** Paul Wong, 14 April 2026 (Session 2) — API-generated then manually corrected
**File:** `json/nlp_results_k9.json`

| # | Name | Stability | Notes |
|---|------|-----------|-------|
| T1 | History and Biography of Cybernetics | 0.131 | Low stability due to Lem/Čapek fiction; cluster coherent |
| T2 | Cybernetics of Psychology | 0.559 | |
| T3 | Extensions of Cybernetics | 0.153 | Brier, Yuk Hui, actor-network theory |
| T4 | Cybernetic Management Theory | 0.349 | Beer's VSM tradition |
| T5 | Biological Systems Cybernetics | 0.224 | Sterling, Schulkin, Laughlin |
| T6 | Formal Foundations of Cybernetics | 0.289 | Mathematical + computational |
| T7 | Cross-Domain Applications of Cybernetics | 0.306 | Urban systems, church, border security |
| T8 | Cybernetics of Posthumanism | 0.306 | |
| T9 | Cultural Applications of Cybernetics | 0.622 | Highest stability across all k |

> ⚠️ **Reconciliation needed:** Run B (Session 1) and Run C k=9 (Session 2) give different topic structures because they use different corpus sizes (~690 vs 542 books) and Run B has no `--seeds` flag. These are not directly comparable. A decision is needed on which is the working canonical for v0.4.3.

---

### Run D — Chapter-level (NMF, 8 topics)
**File:** `json/nlp_results_chapters.json`
**Status:** MVP infrastructure — not validated to same standard as book-level LDA

| # | Name |
|---|------|
| T1 | Human & Social Experience |
| T2 | Mathematical & Formal Systems |
| T3 | General Systems Theory |
| T4 | History & Philosophy of Cybernetics |
| T5 | Management & Organisational Cybernetics |
| T6 | Control Theory & Engineering |
| T7 | Applied Cybernetics & Technology |
| T8 | Biological & Cognitive Systems |

---

## 3. Discrepancies in Slide Deck (CyberneticsNLP_Talk.pptx — March 2026)

| Slide | Item | Current (stale) | Correct |
|-------|------|-----------------|---------|
| 1, 4, PDF cover | Date | March 2026 | April 2026 |
| 4 | Corpus size | "675+" books | 695 books |
| 8 | Sessions timeline | Mar 20–30 only | Continues through April (8 Apr v0.4.2, 14 Apr v0.4.3) |
| 8 | Script count | 26 scripts | ~34 scripts |
| 8 | Documentation | "1,600+ line methodology doc · 900+ line decision log" | 2,000+ methodology · 1,600+ decisions |
| 10 | Pipeline step 3 | "LDA (7 topics, book-level, TF-IDF 3,000 features)" | k=9 canonical, 3,000 features (sampled) / 15,000 features (full-text) |
| 10 | NMF | "(6 topics, chapter-level)" | 8 topics |
| 11 | LDA stats | "7 topics selected via coherence + interpretability" | k=9 (9 topics), selected via NPMI coherence + stability |
| 11 | NMF stats | "6 topics vs 7" | 8 topics |
| 13 | Topic map | 7-topic solution (T1–T7) | Entirely superseded — now 9-topic solution |
| 14 | Historical narrative | References 7-topic naming (T2 Mathematical, T6 Control etc.) | Update to 9-topic naming |
| 22 | What's next | "Seed validation: rerun LDA/NMF across more seeds" | Done — 5-seed stability analysis completed |

---

## 4. Discrepancies in PDF (CyberneticsNLP_Analysis_Extracts.pdf — March 2026)

| Section | Item | Current (stale) | Correct |
|---------|------|-----------------|---------|
| Cover | Book count | 675 Books | 695 books |
| Cover | Date | March 2026 | April 2026 |
| Chart 2 | LDA solution | "4-Topic Solution" | Now 9-topic (book-level LDA) |
| Chart 2 | Topic names | Human & Social Experience, Mathematical & Formal Systems, General Systems Theory, History & Philosophy | Entirely superseded |
| Entity table | Dominant topic labels | "General Systems Theory", "History & Philosophy of Cybe", "Mathematical & Formal System" | Old 7-topic (or 4-topic) labels — superseded |
| Entity table | Amazon, Facebook, Google as organisations | Present | Known noise issue (KI-04) — flagged, not yet fixed |
| Section 2 | NMF topics | 10 topics shown | Now 8 topics |

---

## 5. Documentation Tasks Pending

### Immediate (before slide deck and PDF update)
- [x] ~~**Reconcile Runs B and C**~~ — **Run C (`nlp_results_k9.json`) confirmed canonical**, 14 April 2026
- [x] ~~Verify `nlp_results.json`~~ — confirmed holds Run B (full_text, 9 topics); Run A overwritten
- [ ] Update `docs/CHANGELOG.md` with v0.4.3 entry
- [ ] Append contributions entries from `contributions_entries_ready_to_merge.md` to `docs/contributions.md` on Cybersonic
- [x] ~~Append `new_decisions_methodology_apr7.md`~~ — **done**: Apr 7 content already in `decisions.md` and `methodology.md`; temp file gone
- [ ] Push v0.4.2 tag to GitHub (pending from Session 1 handoff)

### For slide deck update
- [ ] Update corpus count: 675 → 695 (slides 4, 8)
- [ ] Update date: March 2026 → April 2026 (slide 1)
- [ ] Update pipeline stats: 26 scripts → ~34; 1,600+ doc → 2,000+; NMF 6 → 8 topics (slides 8, 10, 11)
- [ ] Replace slide 13 (7-topic map) with 9-topic solution — **content decision needed**: which run's names?
- [ ] Update slide 14 (historical narrative) to match 9-topic naming
- [ ] Add sessions from April to timeline (slide 8)
- [ ] Update "What's Next" — seed validation is done; update open items (slide 22)

### For PDF update
- [ ] Regenerate charts with current pipeline outputs (requires HTML reports rebuilt on Cybersonic)
- [ ] Update cover: 675 → 695 books, March → April 2026
- [ ] Replace Chart 2 (4-topic LDA) with current 9-topic solution chart
- [ ] Update entity table topic labels to current naming
- [ ] Note entity noise (Amazon/Facebook/Google) as known issue

### Vault documents still stale (from audit)
- [ ] `CyberneticsNLP.md` — session log missing 8 April, 14 April sessions; version stale
- [ ] `Cybernetics Bookshelf.md` — v0.4.0, 675 books
- [ ] `Research.md` — 675 books

---

## 6. Canonical Run — Confirmed 14 April 2026

**Canonical for v0.4.3: Run C (`nlp_results_k9.json`) — confirmed by Paul Wong, 14 April 2026.**

Rationale: v0.4.3 is defined by the pub-type filter (monographs + collected works, 542 books). Run C was run with this filter, `--seeds 5`, and `--lemmatize`, making it reproducible. Run B (`nlp_results.json`) predates the pub-type filter and belongs to an intermediate state. Note: `nlp_results.json` currently holds Run B (confirmed via `pipeline_mode` check on Cybersonic) — the original 3 April sampled run (Run A) was overwritten.

| | Run B (Session 1) | **Run C k=9 (Session 2) ← CANONICAL** |
|-|-------------------|-----------------------|
| Corpus | ~690 books (min-chars filter) | **542 books (pub-type filter)** |
| Seeds | Not specified | **5 seeds** |
| Lemmatize | Not specified | **Yes** |
| Stability | mean=0.352, 6/9 stable | mean=0.327, 5/9 stable |
| Output file | `nlp_results.json` | **`nlp_results_k9.json`** |
| Names agreed | Session 1 (superseded) | **Session 2 (this session) ← USE THESE** |

---

*Consolidation compiled 14 April 2026 · Claude (Cowork Session 2) · Based on: slide deck, PDF, all vault docs, both session handoffs, README, CHANGELOG, and Cybersonic pipeline outputs.*
