# CyberneticsNLP

**Version:** 0.5.5 in progress (last released 0.5.4) · last updated 2026-07-19
**Valid for:** 2026 work program (publication target 2026; may carry into 2027)
**Repository:** https://github.com/cybersonic/CyberneticsNLP
**Local path:** Cybersonic → `~/CyberneticsNLP/`
**Status:** Phase 1 in progress — pipeline consolidation
**Archive after:** Publication → `05 Archive/`

---

## Overview

A reproducible NLP pipeline for topic modelling, clustering, keyphrase extraction, summarisation, controlled vocabulary analysis, and visualisation applied to a cybernetics book corpus extracted from a Calibre library.

**Corpus:** reconstructed Calibre collection ~739 books (July 2026 rebuild) · 1954–2025 · **canonical corpus (19 Jul 2026): 566 monographs and collected works analysed** (`run_20260719_k9_s5`, equivalence class `88c44bece9a5a875`, nlp_hash `e3a85b79ca484636`; `--full-text --topics 9 --seeds 5 --lemmatize --max-features 15000 --max-iter 100`, CPU). Supersedes the 26 April 541-book canonical (`run_20260426_k9_s5` / `23b29233a67b2938`); this re-canonicalisation followed the July Calibre reconstruction + KI-13 recovery. Pre-reconstruction figures (726 collection / 695 pipeline) are historical.

The pipeline maps the intellectual landscape of cybernetics — tracing topic evolution, canonical figures, concept velocity, and entity relationships across 70 years of literature.

The paper's core contribution is not merely that the pipeline is reproducible, but that its design decisions are **epistemically justified** for a book corpus specifically. Back-of-book indexes, bibliography depth, chapter structure, and long-form argument arc are affordances of books that are absent or structurally different in journal articles and conference papers. Feature selection is calibrated to these affordances. See `docs/memo_media_aware_nlp_epistemic_affordances.md` for the theoretical framework.

---

## Authorship

| Author | Role |
|--------|------|
| Paul Wong (ANU School of Cybernetics · ORCID 0000-0001-6515-1860) | Lead — conceptualisation, domain expertise, corpus assembly, validation, supervision |
| Claude Sonnet 4.6 (Anthropic) | Lead — software, formal analysis, visualisation, documentation (sessions v0.1.0–v0.5.4; platforms Chat, Cowork) |
| Claude Opus 4.8 (Anthropic) | Lead — software, documentation (sessions v0.5.5+; platform Claude Code CLI) |

Full CRediT taxonomy and the model-author/platform note: see `docs/contributions.md`.

Where journals do not permit AI authorship, the Claude model-authors (Sonnet 4.6 and Opus 4.8) will be listed in Acknowledgements.

---

## Current Sprint

**Re-canonicalisation after the July 2026 Calibre reconstruction (KI-13) — *complete 19 Jul 2026***

The Calibre DB was corrupted and rebuilt (July 2026): ids reassigned, corpus grown, clean cache went stale. The re-canonicalisation is now done — new canonical `run_20260719_k9_s5` (**566 books**, class `88c44bece9a5a875`, nlp_hash `e3a85b79ca484636`). Full staging record: `docs/recanonicalisation_checklist.md`.

- [x] **§0 — regenerated `csv/books_metadata_full.csv`** from the reconstructed `metadata.db`. Exposed + fixed a corpus-dropping bug: the reconstruction swapped custom_column_4↔5 (Publication Type↔Theme); `00_export_calibre.py` now binds them **by name** (KI-13, commit `37e2138`).
- [x] **Closed the ingestion gap (KI-13)** — §0 metadata regen fixed the No-meta skips; the 8 image-only monographs (Bateson/Mead, Beer, Wiener, …) were **OCR'd + Calibre FTS re-indexed** (Paul, user-side); all 12 gap monographs now admit.
- [x] **Re-ran** `run_all.sh --stream --rebuild-clean` — **566 analysed** (was 544); 12/12 gap ids present in `nlp_results.json['book_ids']`. Ran on CPU (GPU/cuML unavailable).
- [x] **Re-established the canonical run** — logged as `run_20260719_k9_s5`; count/framing propagated across `CLAUDE.md`, `README.md`, this doc, `patch_topic_names.py`.
- [x] **Re-validated topic names** against the new fit (finalised by Paul Wong, 19 Jul; provisional, single-rater). Positions permuted — see Topic Solutions.
- [x] **Reader's-guide content rewrite + deck migration** — 4 reader's guides refreshed in-place (`data/outputs/`, gitignored) and deck migrated to 566/new-name facts (`patch_deck_566.py` → `CyberneticsNLP_Talk_v4_566.pptx`, commit `941ae73`).
- [x] **GPU-backend parity — resolved as "CPU is canonical" (20 Jul 2026).** No GPU re-run: `--gpu` was deliberately removed from `run_all.sh` on 25 Apr 2026 (broken cuML/RAPIDS conda env, `run_all.sh:197-201`), so the 566-book run correctly executed on CPU **by design** (`gpu_used=False`), not via silent fallback. cuML and sklearn are different LDA implementations, so a GPU run would not reproduce the CPU `nlp_hash` — GPU is a repaired-env *speed* option, not a route to "parity" and not part of canonical provenance. Stale "enforces `--gpu`" claims corrected in `CLAUDE.md` + the restore-canonical snippets (`CLAUDE.md`, `run_all.sh:185`).
- [ ] **Remaining:** multi-rater naming (sprint item 4).

*Superseded:* the April "Tuesday 28 release" sprint (release HTMLs + deck v3) completed 26 April 2026; those reports will be regenerated by the re-canonicalisation run, so the remaining spot-check/final-review items from that sprint are moot. Detail in `docs/CHANGELOG.md` (v0.5.4).

**Topic naming reliability (still open — survives the re-canonicalisation)**
- [x] ~~Run-records system~~ — **superseded by `data/pipeline.db`** (survey infrastructure, v0.5.0): `log_pipeline_run.py` + `pipeline_db.py` record run params, per-topic words, top books, name, rater, date.
- [ ] **Implement n-run comparison report** — `python src/compare_topic_runs.py --runs N` (draft in vault `docs/src_draft/`) reads the last N logged runs from `data/pipeline.db` and generates a comparison across all N. Report shows: per-topic book presence matrix, stable word core, naming records table, inter-run book overlap %, and agreement status. Layout must scale to arbitrary N (not fixed two-column).
- [ ] **Multi-rater naming protocol** — at least two independent raters name each topic per run; record disagreements; compute inter-rater agreement (e.g. Cohen's kappa or % agreement on names)
- [ ] **Revise naming status** — current k=9 names are **provisional** (single run, single rater); names should only be considered stable once agreement is established across ≥3 runs and ≥2 raters

**Infrastructure**
- [ ] Install RAPIDS cuML for GPU-accelerated LDA (optional — CPU run already viable)
- [x] ~~KI-04 entity-network platform noise~~ — **resolved** (see Known Issues)

**Moratorium — do not start until signal inventory and document unit decision complete**
- [ ] **Signal inventory audit** — for each book, record observable structural signals: index present/absent, reference location (end-of-book/chapter-level/none), distinct author count, chapter count, publication era
- [ ] **Document unit decision** — formally decide proceedings/anthology treatment policy before implementing exclusions in pipeline
- [ ] **Implement exclusion filter** — add `book_styles.json` lookup to `03_nlp_pipeline.py` to exclude 22 proceedings/handbook/reader books from LDA analysis
- [ ] **Sampling strategy review** — review `sample_book()` in `03_nlp_pipeline.py` with book style as conditioning variable
- [ ] **Validation framework extension** — add style-stratified validation to `09c_validate_topics.py`
- [ ] **Weighted second pass** — `python src/03_nlp_pipeline.py --weighted` after exclusion filter implemented
- [ ] **Regenerate 17 missing/bad summaries** — via `generate_summaries_api.py`

**Classifier (post-presentation)**
- [ ] Second active learning round — review new `monograph_sample_*.csv`
- [ ] Add reviewed labels to Calibre `custom_column_5`
- [ ] Retrain classifier — target recall improvement on 71 false negatives
- [ ] More negative examples needed — especially anthologies and textbooks
- [ ] Consider `h_toc_contributor_names` heuristic once TOC extraction verified

**Classification redesign (post-moratorium)**
- [ ] **Hand-label ~150 books** — functional ground truth (which pipeline assumptions does each book violate?) — NOT categorical labels
- [ ] **Multi-label scorer redesign** — after signal inventory complete

**Recently completed (July 2026)**
- [x] KI-13 clean-cache staleness guard — `src/check_clean_cache.py` + `run_all.sh --rebuild-clean` (commit `be560c2`)
- [x] KI-13 post-rebuild 28-book ingestion-gap audit + verified dispositions; ROADMAP / checklist / master-doc updated (commits `d8eedc5`, `a8bead3`, `42c3112`)

**Earlier completed sprints (v0.4.0 → v0.5.4)** — full detail in `docs/CHANGELOG.md` and `docs/contributions.md`: release-HTML suite + reader's guides, full-text LDA refactor, pub-type filter (canonical 542 → 541 analysed), k-selection sweeps, survey / `pipeline.db` infrastructure, 26 April topic-name finalisation, entity-network noise fixes (KI-04/07/09/10), monograph classifier + active-learning cycle. (Not re-listed here to avoid drift with the canonical logs.)

---

## Phase 1 — Pipeline Consolidation (in progress)

Core pipeline is functional. Focus is on data quality and reproducibility.

- [x] Streaming corpus ingestion
- [x] LDA topic model (k=9, book-level — canonical solution locked 3 April 2026)
- [x] NMF topic model (8 topics, chapter-level — names written to `nlp_results_chapters.json` 8 April 2026)
- [x] Abstractive summaries via API (695 books; 17 requiring regeneration)
- [x] Index extraction and canonical vocabulary (262 person name merging rules)
- [x] Index grounding (lift scores, concept density, concept velocity)
- [x] Time series report with concept velocity (Chart 7)
- [x] Entity relational network (4 node kinds, 4 layout algorithms)
- [x] Entity classification (heuristics + spaCy + Wikidata)
- [x] Regression test suite (15 tests)
- [ ] Complete spaCy + Wikidata classification pass
- [ ] Complete paragraph-window edge computation
- [ ] Regenerate 17 outstanding summaries
- [ ] Weighted second pass (run after full pipeline complete)

---

## Phase 2 — Analysis and Interpretation

- [ ] **Index quality stratification** — compute 5-year moving average of `status` outcomes (`ok`/`truncated`/`garbled`/`no_index`) by `pubdate` from `books_clean.json`; characterise the temporal diffusion curve of indexing practice across the corpus; assess whether NLP results differ between books with rich vs. absent/algorithmic indexes
- [ ] **Topic validation (triangulation)** — apply five-signal framework to all 9 LDA topics: LDA top words → high-loading titles → aggregated index terms → keyphrases → year distribution; flag noisy topics for merging or splitting; document divergence cases
- [ ] Events analysis — extract and classify historical events from index terms
- [ ] Co-citation network — who cites whom? Build from bibliography sections
- [ ] Temporal entity analysis — how do person/concept networks change across decades?
- [ ] Cross-corpus comparison — cybernetics vs systems theory, complexity science, AI/ML
- [ ] Topic evolution — track how LDA topic distributions shift 1954→2025
- [ ] Canonical figures — rank persons by centrality, temporal span, cross-topic reach

---

## Phase 3 — Publication

- [ ] Paper draft — *Mapping the Cybernetics Intellectual Landscape: A Computational Analysis of 695 Books* — includes extended methodological discussion on epistemic justification of pipeline design for book corpora (media-aware NLP, index-as-primary-signal, index quality stratification, triangulation validation framework)
- [x] Confirm paper scope: epistemic justification of design decisions folds into main paper as extended methods, not a separate methodological paper — **confirmed 1 April 2026**
- [ ] Search bibliometrics / scientometrics / STS literature for prior use of "epistemic affordances" or equivalent concept before finalising terminology
- [ ] Merge `contributions.md` authorship statement into manuscript
- [ ] Zenodo deposit — archive pipeline with DOI
- [ ] Journal target — TBD (candidates: *Kybernetes*, *Systems Research and Behavioral Science*, *Digital Humanities Quarterly*)
- [ ] GitHub release — tag v1.0 when pipeline fully validated

---

## Release goal — Book-level HTML for colleague sharing

**Target:** release the book-level analysis HTML files to colleagues after presentation.
**Standard:** *defensible* — genuine effort at error reduction, not certified error-free;
consistent with the standing methodological principle (all outputs provisional) and the
provenance notice carried in every report.

**Files in scope** (nav links to the entity network, not per-book summaries):
- `data/outputs/index.html` — main report (Fig 1–6 + topic proportions)
- `data/outputs/clusters.html` — cluster composition
- `data/outputs/keyphrases.html` — keyphrase analysis
- `data/outputs/cosine.html` — cosine similarity
- `data/outputs/book_nlp_entity_network.html` — entity relational network

`books.html` (per-book summaries) is **not** in current release scope — summary quality is
not yet at release standard (60k-token sampling limits). All four navigable pages link to the
entity network via the nav tab.

**"Defensible" means:** all known systematic errors (platform contamination, EOLSS noise,
trailing fragments, node misclassifications) fixed or mitigated; provenance notice visible at
all scroll positions; topic names match current provisional LDA names; entity network
validated against domain knowledge; results framed as automated provisional analysis with no
individual certified findings.

> **Status (19 Jul 2026):** regenerated on the 566-book re-canonicalisation run — all five
> release pages carry the new topic names and the 566 corpus. **Still to do before re-sharing:**
> the two reader's guides (`book_nlp_index_guide.html`, `book_nlp_keyphrases_guide.html`) are
> hand-written and still show the April names/stability — content rewrite pending; and the
> "defensible" checks should be re-confirmed against the new fit.

---

## Topic Solutions

> Five book-level LDA runs are documented here (newest first). They used different corpora and/or
> text representations, so topic **positions and names are not comparable across runs**. All names are
> provisional, single-rater. **The 19 July 2026 post-reconstruction run is the current canonical.**
>
> ✅ **KI-13 re-canonicalisation complete (19 July 2026):** the July Calibre reconstruction was
> re-ingested — the 28-book gap closed via OCR of image-only scans plus a custom-column metadata fix
> (`00_export_calibre.py` now binds Publication Type/Theme by name). The new canonical analyses
> **566 books** under a **new equivalence class** (`88c44bece9a5a875`). The 26 April "541" run is now
> historical. Names were re-validated against the new fit — positions permuted, so this is not a
> relabelling.

---

**Book-level LDA — 19 July 2026 post-reconstruction full-text canonical ← CURRENT CANONICAL**
566 books (monographs + collected works) · `--full-text --topics 9 --seeds 5 --lemmatize --max-features 15000 --max-iter 100` (executed on **CPU** — GPU/cuML unavailable)
Run `run_20260719_k9_s5` · equivalence class `88c44bece9a5a875` · nlp_hash `e3a85b79ca484636`
**6/9 stable · 2 moderate (T2/T6) · T1 unstable · mean stability=0.365** (09c bands, stable ≥0.30)

⚠️ Names **provisional**: finalised by a single rater (Paul Wong), 19 July 2026, single run. Stable only after ≥3 runs × ≥2 raters (sprint item 4). Positions **permuted** vs 26 April — the clusters moved (April's single "Social and Organisational" split into Social Systems T5 vs Management T7; control engineering merged with neural networks into T8), so this is **not** a relabelling.

| # | Name | Stability | Notes |
|---|------|-----------|-------|
| T1 | History of Information Age and Cybernetics | 0.145 unstable | Brand, Gleick, *Dark Hero* (Wiener bio), Markoff — popular computing/info-age histories |
| T2 | Extensions and Exploration of Cybernetics | 0.173 moderate | Heterogeneous: voice/sound/singing + Sinophone (Yuk Hui, Qian Xuesen) |
| T3 | Biological and Ecological Regulation: Homeostasis & Allostasis | 0.325 stable | Schulkin, Sterling, Corning, Lovelock (*Gaia*) |
| T4 | Cybernetics of Self | 0.322 stable | Maltz *Psycho-Cybernetics* franchise, self-help, counselling |
| T5 | Social Systems and Second-Order Constructivism | 0.514 stable | Luhmann ×4, Varela (autopoiesis), constructivism |
| T6 | Foundations of Cybernetics | 0.225 moderate | Information theory, probability/entropy, formal + relational-biology models |
| T7 | Management and Organisational Cybernetics | 0.566 stable | Espinosa, Lassl (VSM), Emery/Thorsrud, Forrester — most stable |
| T8 | Control and Feedback Systems | 0.523 stable | Neural networks, marine/plant control, Qian (*Engineering Cybernetics*), Powers (PCT) |
| T9 | Digital Arts, Architecture, Design and Posthumanism | 0.495 stable | Ascott, Dixon, digital-culture architecture, posthumanism |

*Stability-band note (KI-11): `log_pipeline_run.py` uses a higher "stable" cutoff (~≥0.45) and reports **4** stable for these same scores; `09c_validate_topics.py` (≥0.30, used above) reports **6**. Same `topic_stability.json` — an open threshold inconsistency, not a data difference.*

---

**Book-level LDA — 26 April 2026 full-text canonical ← historical (superseded by 19 July re-canonicalisation)**
541 books (monographs + collected works only) · `--full-text --topics 9 --seeds 5 --lemmatize --max-features 15000 --max-iter 100 --gpu`
Run `run_20260426_k9_s5` · equivalence class `23b29233a67b2938` · nlp_hash `901e5ec924248fe2`
**5/9 stable · 3 moderate (T1/T5/T8) · T7 unstable · mean stability=0.348** · perplexity 3650.7 · coherence 0.0780

⚠️ Names **provisional**: finalised by a single rater (Paul Wong) in a single session (26 April 2026). Names are stable only after ≥3 runs × ≥2 raters (sprint item 4). Positions/names do **not** carry over from earlier runs — e.g. "Extensions of Cybernetics" named T3 in the pre-25-April sampled taxonomy occupies T9 here.

| # | Name | Stability | Notes |
|---|------|-----------|-------|
| T1 | History and Historiography of Cybernetics | 0.261 moderate | Wiener/Bateson biographies, Macy Conferences, field history |
| T2 | Techno-political Complexes | 0.441 stable | Cold War computing, surveillance, big tech, internet capitalism |
| T3 | Engineering Control | 0.512 stable | State-space, transfer functions, controller design; PCT engineering vocab anchors here |
| T4 | Social and Organisational Cybernetics | 0.529 stable | Beer/VSM recursive org model + Luhmann social-institutions scope |
| T5 | Formal Foundations of Cybernetics | 0.178 moderate | Mathematical + computational foundations |
| T6 | Reinventing Selves and Others, Past and Future | 0.458 stable | |
| T7 | Psychological and Behavioural Regulation and Control | 0.045 unstable | ⚠️ PCT does *not* anchor here despite the name — a methodological feature, not a defect |
| T8 | Biological and Neural Cybernetics | 0.287 moderate | |
| T9 | Extensions of Cybernetics | 0.421 stable | Broad framing: ecology, posthumanism, second-order cybernetics, digital ontology |

---

**Book-level LDA — Run C: Full-text, pub-type filtered (14 April 2026) ← historical (superseded by 26 April canonical)**
542 books (monographs + collected works only) · `--full-text --topics 9 --seeds 5 --lemmatize --max-features 15000 --run-id k9`
File: `json/nlp_results_k9.json` · **5/9 stable · mean stability=0.327 · T9 highest (0.622)**

⚠️ Names below are **provisional**: agreed by a single rater (Paul Wong) in a single session (14 April 2026, Session 2). Subject to the naming reliability protocol in `docs/memo_topic_naming_reliability.md`.

| # | Name | Stability | Notes |
|---|------|-----------|-------|
| T1 | History and Biography of Cybernetics | 0.131 low | Low stability due to Lem/Čapek fiction outliers; cluster coherent |
| T2 | Cybernetics of Psychology | 0.559 stable | |
| T3 | Extensions of Cybernetics | 0.153 low | Brier, Yuk Hui, actor-network theory |
| T4 | Cybernetic Management Theory | 0.349 stable | Beer's VSM tradition |
| T5 | Biological Systems Cybernetics | 0.224 moderate | Sterling, Schulkin, Laughlin |
| T6 | Formal Foundations of Cybernetics | 0.289 moderate | Mathematical + computational |
| T7 | Cross-Domain Applications of Cybernetics | 0.306 stable | Urban systems, church, border security |
| T8 | Cybernetics of Posthumanism | 0.306 stable | |
| T9 | Cultural Applications of Cybernetics | 0.622 **most stable** | Highest stability across all k values in sweep |

---

**Book-level LDA — Run B: Full-text (14 April 2026, Session 1) ← historical reference**
~690 books (min-chars 10000, no pub-type filter) · `--full-text --topics 9 --max-features 15000`
File: `json/nlp_results.json` · **6/9 stable · 1 unstable · mean stability=0.352**
Predates pub-type filter; superseded (by Run C, in turn by the 26 April canonical).

| # | Name | Stability |
|---|------|-----------|
| T1 | Second-Order Systems Theory & Constructivism | 0.484 stable |
| T2 | Digital Media Arts, Posthumanism & Cultural Studies | 0.453 stable |
| T3 | *(unstable — do not name)* | 0.132 unstable |
| T4 | System Dynamics (Forrester School) | 0.349 stable |
| T5 | Political & Governance Cybernetics | 0.336 stable |
| T6 | Biological Cybernetics: Homeostasis & Allostasis | 0.189 moderate |
| T7 | Systemic Psychotherapy & Family Therapy | 0.357 stable |
| T8 | Popular, Literary & Metaphorical "Cybernetics" | 0.598 most stable |
| T9 | History of Cybernetics | 0.271 moderate |

---

**Book-level LDA — Run A: Sampled (3 April 2026) ← historical reference**
695 books · `--min-chars 10000 --lemmatize --topics 9 --seeds 5`
Text input: 3 × 20k-char slices (10%/50%/85%) = **60k chars (~12k words) per book** · 7/9 stable · 0 dead · mean stability=0.382

⚠️ Names below are **provisional**: agreed by a single rater (Paul Wong) in a single session. Superseded (by Run C, in turn by the 26 April canonical); retained here for comparison. File was overwritten by Run B on Cybersonic (confirmed 14 April 2026).

| # | Name | Stability |
|---|------|-----------|
| T1 | Management Cybernetics | stable |
| T2 | Second-Order Cybernetics Applied to Social Systems | stable |
| T3 | Dynamical Systems, Homeostasis & Biological Regulation | stable |
| T4 | Psychological Cybernetics | stable |
| T5 | Non-Anglophone Engineering Cybernetics | unstable |
| T6 | Mathematical Foundations of Cybernetics | stable |
| T7 | Cultural Cybernetics, Posthumanism & Digital Media | stable |
| T8 | Applied Cybernetics & Computers in Society | stable |
| T9 | Residual / Outlier Cluster | unstable |

**Chapter-level (NMF, 8 topics — names written to `nlp_results_chapters.json` 8 April 2026)**

| # | Name | Key Terms |
|---|------|-----------|
| T1 | Human & Social Experience | argues, human, author, understanding, explores |
| T2 | Mathematical & Formal Systems | mathematical, system, functions, models, demonstrates |
| T3 | General Systems Theory | theory, cybernetics, systems, opening, sections |
| T4 | Management & Organisational Cybernetics | organizational, management, decision making, model |
| T5 | Control Theory & Engineering | control, feedback, control systems, mechanisms, loops |
| T6 | Popular & Applied Cybernetics | examines, technological, analysis, human, technology |
| T7 | Applied Cybernetics & Technology | — |
| T8 | Biological & Cognitive Systems | — |

---

## Key Design Decisions (summary)

- **LDA for books, NMF for chapters** — LDA fails on short chapter texts (~2,000 words); NMF on clean abstractive summaries is more appropriate for diverse, short documents
- **Abstractive summaries as NMF input** — removes OCR noise, boilerplate, and multilingual artefacts that pollute raw chapter text
- **Multi-point text sampling (10%/50%/85%, 60k chars total)** — three 20,000-character slices concatenated (positions confirmed from `03_nlp_pipeline.py`): 10% (past front matter), 50% (argumentative core), 85% (conclusions); minimum 4,000-char offset avoids publisher/copyright pages. Total input to LDA ≈ 60,000 characters (~12,000 words) per book.
- **35% verbatim similarity threshold** — empirically chosen to catch genuinely extractive summaries while allowing natural phrasing overlap
- **NPMI coherence for topic selection** — avoids gensim dependency; implemented directly with numpy/sklearn
- **Back-of-book index as primary signal** — for book corpora, the index is a hand-curated concept ontology unavailable in any other scholarly medium; treated as a primary analytical feature, not a supplementary one
- **Index quality as covariate, not uniform feature** — indexing practice is temporally stratified: manual/variable (~pre-1985), concordance-tool/shallow (~1985–2010), algorithmic-or-absent (~post-2010); modelled using `status` field in `index_terms.json` enriched with publication decade
- **Topic validation by triangulation** — five independent signals: LDA top words, high-loading book titles, aggregated index terms from those titles, per-book keyphrases, publication year distribution; divergence between LDA words and index terms flags a noisy topic

Full rationale: `docs/decisions.md` (1,600+ lines) · Full methodology: `docs/methodology.md` (2,000+ lines) · Epistemic justification: `docs/memo_media_aware_nlp_epistemic_affordances.md`

---

## Open Questions

**Text representation and topic stability**
- The two runs (60k-char sample vs full body text) produced substantially different topic solutions — not just shifted names but different cluster membership. This raises a prior question: **which text representation is epistemically appropriate for this corpus?** The sampled run captured concentrated terminology from three positions; the full-text run captures the full argument, including discursive/narrative register. For a study whose claims rest on epistemic affordances of book-length texts, the full-text approach is more defensible — but the tradeoff (T3 instability, T8 popular-register cluster) needs to be documented.
- **T8 (Popular/Literary "Cybernetics")** is a new finding from the full-text run: a highly stable cluster of fiction, self-help, and sports books using "cybernetics" metaphorically. Should these be excluded from the analytical corpus, or documented as a distinct stratum (non-academic cybernetics discourse)?
- **T3 instability** may be addressable by implementing the exclusion filter (moratorium-blocked): several T3 books (Fossen, Jumarie, Grössing) are the technical proceedings/engineering handbooks the filter targets. Run 3 after exclusion filter to test.

**Topic naming reliability**
- How many pipeline runs are needed before names can be considered stable? Suggested threshold: ≥3 runs with consistent top-book composition.
- Who should serve as independent raters? At least one rater with domain expertise in cybernetics independent of the pipeline development.
- What constitutes "agreement" on a topic name — exact match, synonym, or shared conceptual referent? A coding rubric is needed.
- Should the run-records system capture names per-run (re-named fresh each time), or anchor to a reference name and score drift?
- Is the recurrent mismatch between top words and top books a naming problem, a model stability problem, or a feature of LDA on book corpora that should be documented as a methodological finding rather than fixed?

**Pipeline / infrastructure**
- ~~What is the right LDA k?~~ **Resolved**: k=9 canonical (3 April 2026)
- What is the right document unit for proceedings and anthologies? Are chapters the right unit, or should these books be excluded entirely? — moratorium pending decision
- Should `sample_book()` be conditioned on book style (e.g. sample differently for anthologies vs monographs)? Slice positions are currently fixed at 10%/50%/85% (20,000 chars each); anthologies may benefit from chapter-boundary-aligned sampling. — pending signal inventory
- Should entity network include a "works" node kind for cited books?
- Is Wikidata rate limit (2 req/sec) acceptable for future full re-runs?
- Should `test_pipeline.py` run as a GitHub Action on each push?
- What is the right `n_books` threshold for canonical vocab? (Currently 3)

**Epistemic justification / methodology**
- Is "epistemic affordances" the right term, or does existing literature in bibliometrics, scientometrics, or STS already name this concept? Search before finalising.
- Should index quality stratification be modelled formally (regression of `status` on `pubdate` and publisher) or treated as a stated limitation?
- Is publisher or disciplinary metadata available from Calibre to model the disciplinary gradient in index quality alongside the temporal one?
- How to handle born-digital books with no index — exclude from index-term analysis, or treat absence as a meaningful signal in itself?
- Is the triangulation validation framework generalisable to other book corpora, or is it specific to cybernetics?
- Should the signal inventory replace or supplement the current book style classifier? What is the relationship between the two approaches?

---

## Known Issues

| ID | Issue | Status |
|----|-------|--------|
| KI-01 | 6 books (IDs: 1416, 240, 1772, 1718, 1727, 1262) — OCR failures | **Resolved 3 April** — Calibre reindex + re-stream; all pass alpha ≥ 0.60 |
| KI-02 | NLP run on 675 books with legacy k=7 | **Resolved 3 April** — canonical k=9 run on 695 books complete |
| KI-03 | Dictionary inconsistency between AshbyX and NorbertX (SCOWL en_US-large) | **Superseded** — project moved to Cybersonic; monitor Cybersonic environment for reproducibility |
| KI-04 | Amazon/Google/Facebook as high-degree nodes in entity network — ebook metadata noise | **Resolved** — `KNOWN_TECH_PLATFORMS` in `src/14_entity_network.py`; noise filters in `09b`; Internet Archive strings in `02`. |
| KI-05 | T9 (Residual/Outlier): single-book loading=1.000 dominates | **Resolved (by interpretation)** — T9 labelled "Residual / Outlier Cluster"; the dominant single-book loading is accepted as the topic's catch-all role, not a defect. (`docs/decisions.md`) |
| KI-06 | Monograph assumption violations (proceedings/handbook/reader) not yet filtered from pipeline | **Resolved** — pub-type filter in `src/03_nlp_pipeline.py` includes only `monograph`/`collected works`. |
| KI-07 | ~130 misclassified entity nodes + EOLSS contamination + plural/comma fragments | **Resolved** — regex pre-filters (`_TRAILING_FUNC`, `_CTA_BACK_MATTER`, `_EOLSS_NOISE`, `_TRAILING_COLON`) in `src/14_entity_network.py` run before cache lookup; `MANUAL_CORRECTIONS` in `src/15_entity_classify.py` extended across five batches. |
| KI-08 | 541 vs 542 book count — one book dropped at runtime | **Resolved** — [2133] *Cybernation and Social Change* added to `ocr-excluded`; parsed and cleaned normally but excluded before LDA/TF-IDF + entity network. Canonical: 542 parsed, 541 analysed. |
| KI-09 | ~150 singular/plural node pairs split PMI signal | **Resolved** — `_singular_form()` + `concept_plural_map` in `src/14_entity_network.py` merge plurals into singulars (book-set union); `_CONCEPT_PLURAL_EXCEPTIONS` protects 35 `-ics` field names. |
| KI-10 | Entity network concepts dropped 746→500 on fresh rebuild | **Resolved** — `run_all.sh` was running step 14 with `--no-windows`, excluding ~239 paragraph-only concept nodes; `--no-windows` removed. |
| KI-11 | Stability band thresholds inconsistent: `log_pipeline_run.py` vs `09c_validate_topics.py` | **Open (post-presentation)** — `09c` uses stable ≥0.30 / moderate 0.15–0.30 / unstable <0.15; `log_pipeline_run.py` uses ~≥0.45; same `topic_stability.json`, conflicting counts. Centralise thresholds. (ROADMAP KI-10) |
| KI-12 | Release HTMLs reflect rebuild nlp_hash, not logged canonical run | **Open (post-presentation)** — rebuild `c8e3c71bf8a3d910` differs from canonical logged `901e5ec924248fe2`; same equivalence class; survey workflow unaffected. (ROADMAP KI-11) |
| KI-13 | Streaming clean cache stale after July 2026 Calibre DB reconstruction. Post-`--rebuild-clean` audit (17 Jul, `runlog20260717.csv`) found a **28-book ingestion gap**: 12 confirmed analysable-monograph recoveries (207, 2087, 2186, 2257, 2271, 2283, 2511, 2517, 2716, 2797, 2799, 2801), 5 correctly excluded (2193/2239/2306 non-monograph; 2138 fr / 2359 ca), 11 brand-new unverifiable (2174, 2701, 2707, 2776, 2778, 2790, 2806–2810). Corrected analysed count **~556–567, not 544**. Mechanisms: (a) id 207 has no `format='PDF'` `books_text` row → dropped by `split_books_text.sh`; (b) ~27 No-meta skips in streaming clean. Second arm: reconstruction never regenerated `books_metadata_full.csv` (Apr 11, old ids), so the pub-type filter ran on stale metadata. | **Resolved (19 Jul 2026).** Guard landed (`check_clean_cache.py` + `--rebuild-clean`); `00_export_calibre.py` now binds custom columns by **name** (the reconstruction had swapped Publication Type↔Theme — a positional export would have dropped the whole corpus); the 8 image-only monographs were **OCR'd + Calibre FTS re-indexed**, and the §0 metadata regen closed the No-meta gap. New canonical `run_20260719_k9_s5` — **566 books**, class `88c44bece9a5a875`. Detail: `docs/ROADMAP.md`; steps: `docs/recanonicalisation_checklist.md`. |

> **Ownership (decided 19 Jul 2026):** this table is the **canonical orientation index** for
> known issues. **`docs/ROADMAP.md`** holds the canonical per-issue resolution detail (commit
> hashes, file-level changes), with `docs/CHANGELOG.md` / `docs/contributions.md`. `CLAUDE.md`
> now points here and no longer carries its own KI table. KI-01–03 are retained as historical
> (resolved/superseded under an older numbering that predates the active KI-04+ scheme).

---

## Session Log

| Date | Focus | Platform | Version |
|------|-------|----------|---------|
| 2026-03-20 | Initial pipeline (steps 01–10), corpus ingestion, LDA/NMF | Cowork | v0.1.0 |
| 2026-03-21 | Index grounding, time series Chart 7, weighted pass, embedding comparison | Cowork | v0.2.0 |
| 2026-03-24 | Entity network (step 14), entity classifier (step 15), integrity checker, regression tests | Cowork | v0.3.0 |
| 2026-03-27 | Entity classifier audit (121 corrections), 4 layouts, index canonicalisation, README rewrite, GitHub/OneDrive setup | Cowork | v0.4.0 |
| 2026-03-31 | Data quality pipeline overhaul: `preprocess_raw_text()` in 01; ASCII gate fix + case normalisation in 02; stopword expansion + compound hyphen-joining + `--min-chars` flag in 03; `alpha_ratio` raised + `FOREIGN_HEADER_RE` + `_canonical_term()` in 09; SCOWL en_US-large dictionary installed on AshbyX/NorbertX; full corpus re-clean (675 books) | Chat | post-v0.4.0 |
| 2026-04-01 | Theoretical framework: media-aware NLP and epistemic affordances; index-as-primary-signal rationale; index quality stratification by era (pre-digital / early digital / born-digital); topic validation triangulation framework (5 signals); paper scope confirmed — extended methods folds into main paper; ran remaining pipeline scripts (all without error); LDA coherence sweep k=2–12: best k=11 (coherence=0.0887, perplexity=1487.1), 5-seed run at k=11 (⚠️ script defaulted to sweep — agreed fixed k=20 run still pending); discussed auto-naming LDA topics via Claude API; memo filed → `docs/memo_media_aware_nlp_epistemic_affordances.md` | Chat | post-v0.4.0 |
| 2026-04-02 | Documentation update (Cowork): synced `CyberneticsNLP.md` session log and sprint; updated `contributions.md` and `CHANGELOG.md`; created `Handoff to Chat - 2 April 2026.md` | Cowork | post-v0.4.0 |
| 2026-04-02 | Book style classifier: `00_classify_book_styles.py`, `00_fetch_worldcat_metadata.py`, `00_fetch_anu_primo.py`; `books_metadata_full.csv` (20 cols, replaces `books_lang.csv`; 726 books); OCLC removed (403-blocked), Open Library used; Primo edited_book → anthology; platform contributors suppressed; classifier identified as needing multi-label redesign (over-tuning recognised); ground truth ~150 books agreed as prerequisite. Theoretical §13–15: affordance as mixture, historical cybernetics narrative, NLP-as-affordance-at-scale (Paul's framing). New docs: `memo_attribution_annotations.md`, `draft_methods_corpus_construction.md` | Chat | post-v0.4.0 |
| 2026-04-03 | Documentation update: processed Chat handoff; updated `CyberneticsNLP.md`, `contributions.md`, `CHANGELOG.md`; created next handoff | Cowork | post-v0.4.0 |
| 2026-04-03 | Data quality: OCR reindex confirmed for 6 books (IDs 240, 1262, 1416, 1718, 1727, 1772); `books_clean.jsonl` fully re-streamed (695 books, all 25 CSVs); `books_clean.json` regenerated from scratch (169MB, `clean_text` key); k=9 pipeline run blocked by front-matter alpha-ratio bias — handed to Chat for fix | Cowork | post-v0.4.0 |
| 2026-04-03 | Alpha-ratio front-matter fix; k=9 canonical run (695 books, 7/9 stable, 0 dead, mean stability=0.382); k=10 comparison (rejected); 9-topic taxonomy agreed and locked; full pipeline run (steps 03–15); enrichment pipeline rebuilt (Primo full fetch: 285/726); publication type exclusion policy (22 excluded, 704 retained); 4 manual reclassifications; §16 (document unit problem) and §17 (temporal dimension) added to memo; GitHub push | Chat | v0.4.1 |
| 2026-04-03 | v0.4.1 bump: updated `CyberneticsNLP.md`, `contributions.md`, `CHANGELOG.md` with full session record | Cowork | v0.4.1 |
| 2026-04-08 | Report quality fixes: all 8 HTML reports cleaned (675→695, topic label fixes, NMF/LDA name separation); monograph binary classifier (`heuristic_features.py`, `train_monograph_classifier.py`); active learning cycle established (197 expert labels, first review round complete); terminological decisions: "expert labels" not "ground truth"; classifier training data integrity rule; book-level LDA reports reviewed and confirmed presentation-ready | Chat | post-v0.4.1 |
| 2026-04-14 | Vault update: vault docs updated to reflect 8 April session; contributions draft processed; v0.4.2 bump (documentation sprint) | Cowork | v0.4.2 |
| 2026-04-14 | Full-text pipeline refactor (Session 1): confirmed `books_clean.json` stores full text (mean 346k chars); confirmed `sample_book()` uses 60k **chars** not words; refactored `03_nlp_pipeline.py` with `--full-text`, `--max-features`, `--run-id`, `--name-topics` flags + `strip_front_matter()` / `strip_back_matter()` functions; project confirmed moved from OneDrive/NorbertX to Cybersonic; Run B launched (`--full-text --topics 9 --seeds 5 --max-features 15000 --min-chars 10000` on ~690 books), 6/9 stable, mean stability=0.352; Run B topic names agreed by Paul Wong; k=9/10/12 concurrent sweeps on 542-book corpus initiated | Chat | v0.4.3 |
| 2026-04-14 | k-sweep confirmation, canonical run decision, consolidation (Session 2): k-sweep (k=8/9/10/12) on 542-book pub-type filtered corpus completed; k=9 recommended; Run C k=9 (`nlp_results_k9.json`) names agreed by Paul Wong; Run C confirmed canonical for v0.4.3 (pipeline_mode check on Cybersonic; Run A overwrite confirmed); `docs/consolidation_14apr2026.md` compiled | Cowork | v0.4.3 |
| 2026-04-15 | Slide deck update + documentation completion (Session 3): `CyberneticsNLP_Talk_v2.pptx` — all v0.4.3 facts, preliminary findings framing, index-as-controlled-vocabulary (+ compilation caveat), epistemic affordance at corpus scale (slides 5 and 23), NMF "not presented in this talk"; `docs/decisions.md`, `docs/methodology.md`, `docs/CHANGELOG.md`, `docs/contributions.md` all updated on Cybersonic; vault docs updated (this file, `Cybernetics Bookshelf.md`) | Cowork | v0.4.3 |
| 2026-04-26 | Topic naming finalisation for 25 April full-text canonical run: 9 names revised by Paul Wong — substantive changes to T4 (now "Social and Organisational Cybernetics"; Beer/VSM + Luhmann scope), T6 ("Reinventing Selves and Others, Past and Future"), T7 ("Psychological and Behavioural Regulation and Control"), T9 ("Extensions of Cybernetics" — broader than the interim "Ecology, Posthumanism and Digital Ontology"); T1/T2/T3/T5/T8 capitalisation normalised. Propagation chain: `patch_topic_names.py` → `check_stale_vars.py --fix` → `09c_validate_topics.py --top 10 --md`. `README.md` topic-name table replaced with pointer to `nlp_results.json` / TAXONOMY / `topic_validation.md` (stops the table rotting on every re-naming). k=9 confirmed appropriate for full-text corpus. Run logged as `run_20260426_k9_s5`, equivalence class `23b29233a67b2938`, 2368 runlog lines ingested (recovery via `sqlite3 DELETE` + rerun after `nlp_hash` short-circuit gap — routed to ROADMAP #28). v0.5.3 ⚑ flag cleared; CLAUDE.md post-run validation block removed; canonical-k line updated. Survey workflow now unblocked. **Note:** session-log gap — entries for 18, 20, 21, 23, 25 April are in `docs/contributions.md` but not yet in this master doc. | Cowork | v0.5.3 |
| 2026-04-26 | Tuesday release prep (v0.5.4): `run_all.sh` rebuild (12:02–13:09 AEST; rebuild nlp_hash `c8e3c71bf8a3d910`); reader's guide suite completed — `book_nlp_cosine_guide.html`, `book_nlp_clusters_guide.html`, `book_nlp_keyphrases_guide.html` written; `book_nlp_index_guide.html` corrected for full-text canonical facts (stability scores, max_iter, perplexity table, T7 instability caveat); `06_build_report.py` rerun to inject guide nav links into all five release-scope pages; `presentation/patch_deck.py` updated with 26 April TAXONOMY, stability corrections, LDA input fix, era heading renames ("Cybernetics at Social Scale" / "Diffusion and Injection"), "Phase 2 → Possible Extensions"; deck manual layout formatting applied; `CyberneticsNLP_Talk_v3.pptx` committed. ROADMAP KI-10 (stability band threshold inconsistency) and KI-11 (release HTML nlp_hash drift from rebuild run) recorded. v0.5.4 committed and pushed (`f667f03..f956039`). | Cowork | v0.5.4 |
| 2026-07-17 | KI-13 follow-up — post-`--rebuild-clean` ingestion-gap audit of `data/outputs/runlog20260717.csv`: the 17 Jul rebuild cleaned 694 / analysed 544 but the gap persisted — 28 `eng`-tagged books in the reconstructed DB (`csv/books_lang.csv`, 722) never reached `json/books_clean.jsonl`. Verified vs April `books_metadata_full.csv`: 12 confirmed analysable-monograph gaps, 5 correctly excluded, 11 brand-new unverifiable; corrected count ~556–567 not 544. Mechanisms: (a) id 207 (was 2075, retitled) has no `format='PDF'` `books_text` row → dropped by `split_books_text.sh`; (b) ~27 No-meta skips in streaming clean; second arm — `csv/books_metadata_full.csv` never regenerated post-reconstruction, so the pub-type filter ran on stale April metadata. Docs updated: `docs/ROADMAP.md` KI-13 (verified 28-book table + 4-step fix), `docs/recanonicalisation_checklist.md` §0 (regenerate metadata via `00_export_calibre.py` before re-run), this file's Known Issues table. Committed `d8eedc5` + pushed; no code changes. | CLI | v0.5.5 |

---

## Related

- [[CyberneticsAR]] — staged parallel project consuming NLP outputs as a product/service
- [[Performance Agreement 2026]] — NLP paper and CyberneticsNLP cited as research outputs
- [[02 Areas/Research]]
