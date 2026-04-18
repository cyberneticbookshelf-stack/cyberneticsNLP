# Changelog

All notable changes to the CyberneticsNLP pipeline are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Dates are AEST (UTC+11).

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
Rerun `python3 src/15_entity_classify.py` then `python3 src/14_entity_network.py` on
Cybersonic. Then commit both source files — the cache file stays gitignored but the
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
- AshbyX/NorbertX `json/` divergence — NorbertX is canonical

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
- Full SCOWL en_US-large Hunspell dictionary (76,959 words) installed on AshbyX and NorbertX (⚠️ dictionary inconsistency between machines — monitor for reproducibility)
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
