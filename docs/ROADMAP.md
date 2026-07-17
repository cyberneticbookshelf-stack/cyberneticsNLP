# Roadmap

Tracks planned work, open questions, and longer-term directions.
Issues are tracked at: https://github.com/cyberneticbookshelf-stack/cyberneticsNLP/issues

Last updated: 20 April 2026 (v0.4.7)

---

## Current sprint — post-v0.4.2

**Status:** Moratorium on NLP pipeline code in effect. Presentation complete (book-level LDA). Classifier active learning underway.

### Classifier track

| # | Task | Status |
|---|------|--------|
| 1 | Second review round — review `csv/monograph_sample_*.csv` | ⏳ Pending — awaiting Paul |
| 2 | Add reviewed labels to Calibre `custom_column_5` | ⏳ Pending — follows #1 |
| 3 | Retrain classifier with expanded label set | ⏳ Pending — follows #2 |
| 4 | Target: improve recall on 71 known false negatives | ⏳ Pending |
| 5 | Acquire more negative examples (anthologies, textbooks) | ⏳ Pending |
| 6 | Consider `h_toc_contributor_names` heuristic once TOC extraction is verified | 🔵 Deferred — TOC often stripped/garbled |

### Pipeline (blocked by moratorium)

| # | Task | Status |
|---|------|--------|
| 7 | Signal inventory audit | ⏳ Pending — prerequisite for all pipeline work |
| 8 | Document unit decision (formally record) | ⏳ Pending — prerequisite for #9–10 |
| 9 | Implement signal-inventory-derived **inclusion filter** in `03_nlp_pipeline.py` (distinct from the pub-type inclusion filter at `:295-333` that resolves KI-06). Must use inclusion semantics, not exclusion: publication types and style labels are non-disjoint (a book can be both monograph and textbook — e.g. Ashby's *An Introduction to Cybernetics*), and exclusion rules on any secondary label would wrongly drop legitimate monographs. See `docs/decisions.md` §"Inclusion vs exclusion semantics for non-disjoint labels". | 🔒 Blocked by #7, #8 |
| 10 | Implement style-conditioned sampling in `sample_book()`. Style labels are non-disjoint (a book may carry `monograph` and `anthology` simultaneously), so a multi-label book must be assignable to every stratum it qualifies for, or explicitly apportioned — never dropped from strata by the presence of an additional label. See CLAUDE.md §"non-disjoint labels require inclusion semantics". | 🔒 Blocked by #7, #8 |

### Known issues (post-presentation fixes)

| # | Issue | Notes |
|---|-------|-------|
| KI-01 | [126] Narrative Gravity — verbatim extractive summary | Needs API regeneration |
| KI-02 | Chapter cluster scatter: 17 clusters unexplained | Post-presentation |
| KI-03 | Book × Topic heatmap: numeric values unlabelled | Post-presentation |
| KI-04 | Keyphrases: single words not phrases (TF-IDF `min_ngrams` issue) | Post-presentation |
| KI-05 | Entity network: "information and", "cybernetics and" as spurious concepts | Post-presentation |
| KI-06 | Concept density: Frontier band all zero | Post-presentation |
| KI-07 | Cluster composition: shows only 3 | Post-presentation |
| KI-08 | 71 false negative monographs in classifier (recall ceiling) | Classifier track #3 |
| KI-09 | AshbyX/NorbertX `json/` divergence — NorbertX is canonical | Monitor |
| KI-10 | **Stability band thresholds inconsistent across scripts.** `09c_validate_topics.py` and the reader's guides use: stable ≥0.30, moderate 0.15–0.30, unstable <0.15. `log_pipeline_run.py` uses different implicit thresholds (observed on 26 April run: T2 at 0.441 → ~; T8 at 0.287 → ✗; T6 at 0.458 → ✓), consistent with approximately stable ≥0.45, moderate 0.30–0.45, unstable <0.30. Produces conflicting counts: `09c` reports 5/3/1; `log_pipeline_run.py` shows 3/2/4. Both scripts read from the same `topic_stability.json`. Fix: define canonical thresholds in one place (e.g. `src/pipeline_db.py` or a new `src/stability_bands.py`) and import in both. Decision needed on which set is correct — the ≥0.30 thresholds (used in `09c`, guides, sprint notes) are more permissive and consistent with what has been reported externally. | Post-presentation |
| KI-11 | **Release HTMLs reflect rebuild run, not logged canonical run.** The `run_all.sh` rebuild on 26 April (for HTML report refresh after name propagation) produced `nlp_hash c8e3c71bf8a3d910`, which differs from the logged canonical run `run_20260426_k9_s5` (`nlp_hash 901e5ec924248fe2`). Both runs share equivalence class `23b29233a67b2938` (same k, n_books, max_features, pipeline_mode, seeds_used), so the topic structure is comparable, but the shipped HTML reports do not exactly correspond to the logged run. Not a problem for the Tuesday presentation but is a gap in the audit trail. The survey workflow is unaffected (it operates on the logged canonical run). Longer-term: `log_pipeline_run.py` should optionally accept a `--mark-as-release` flag that records the nlp_hash of the most recent run as the release build, distinct from the analytical canonical run. | Post-presentation |
| KI-13 | **Streaming clean cache silently stale after Calibre DB reconstruction.** (Number follows the CLAUDE.md active-KI list, which reached KI-12; this ROADMAP table's local sequence skips KI-12.) The Calibre DB was corrupted and reconstructed (July 2026); book ids were reassigned and some authors normalised (e.g. `Emery, Fred E.` → `Emery, Frederick Edmund`, old ids 2188/2382/2383 → new 2799/2801/2797). `parse_and_clean_stream.py:294` skips books whose id already appears in `books_clean.jsonl` (id-only skip check), so the reconstructed corpus was never re-ingested: `run_20260716-5` analysed **544 books from a pre-reconstruction cache** while the shards and `metadata.db` (739 books) already held the reconstructed set. Diagnosis (`check_clean_cache` + sweep): **27 books have PDF text in the reconstructed `metadata.db` but are absent from the cache** — 12 English (genuine recoveries: 3 re-IDed Emery works + 9 brand-new incl. Luhmann *Ecological Communication*, Kevin Kelly *Out of Control*, Jackson *Systems Approaches to Management*, Iberall *Toward a General Science of Viable Systems*) and 15 non-English correctly excluded by the language filter. A timestamp guard is insufficient — the cache was rewritten (15:02) *after* the shards (14:51) yet still missing shard-25's book 2797. **Fix (implemented):** `src/check_clean_cache.py` SHA-256-fingerprints each shard against `json/books_clean.manifest.json` (written at the last full rebuild); `run_all.sh --stream` aborts on mismatch, and `--rebuild-clean` moves the cache aside, re-cleans from shards, then rewrites the manifest. **Follow-up (open):** run `run_all.sh --stream --rebuild-clean`, then **re-establish the canonical run** — `n_books` changes (~544 → ~556 English), so it is a **new equivalence class**; the "541 monographs analysed" framing and the canonical k=9 fit/topic names must be re-validated, not carried over. **Post-rebuild audit (17 Jul 2026, `runlog20260717.csv`):** `--rebuild-clean` ran (694 cleaned, 544 analysed) but **the ingestion gap persists — 28 books tagged `eng` in the reconstructed DB (`csv/books_lang.csv`, 722 total) never reached `books_clean.jsonl`.** Full list and mechanisms in the subsection below. | **Rebuild ran; ingestion gap persists — re-canonicalisation open** |

#### KI-13 post-rebuild ingestion gap — 28-book audit (17 Jul 2026)

Cross-check of the reconstructed Calibre DB (`csv/books_lang.csv`, 722 books all tagged `eng`)
against the cleaned output (`json/books_clean.jsonl`, 694 books) after
`run_all.sh --stream --rebuild-clean`. **28 `eng`-tagged books in the DB never reached the
clean output**, so they were absent from the 544-book analysed set. Two mechanisms:

- **(a) No PDF-format text row — 1 book.** id **207** (April id 2075, title reworded by the
  reconstruction to *"An Appraisal of The Next Step in Management Cybernetics"*) has no row in
  any `csv/books_text_*.csv`. `split_books_text.sh` selects `WHERE format='PDF'` from the
  `books_text` table (no id bound), so a book with no PDF-extracted text row — EPUB-only, or PDF
  text-extraction never produced a `books_text` row — is silently absent from the corpus. (The
  emergent min source id of 271 is a *consequence* of this, not an id floor.)
- **(b) Flagged "No-meta" and skipped during streaming clean despite having metadata in
  `books_lang.csv` — ~27 books.** The cleaner's metadata source is out of sync with the
  reconstructed DB, so books with valid reconstructed metadata were treated as metadata-less
  and skipped.

All four books earlier believed "dropped between April and July" resurface here under new
ids and none were analysed: **2075→207, 2188→2799, 2382→2801, 2383→2797**.

Full 28-book gap list, with **verified dispositions** (17 Jul, title/id-matched against
April `csv/books_metadata_full.csv` `pub_type` + runtime language detector; the reconstruction
did **not** regenerate `books_metadata_full.csv`, so this is the most current pub_type source
available and is authoritative for books that existed pre-reconstruction):

| id | title | verified disposition |
|----|-------|----------------------|
| 207 | An Appraisal of The Next Step in Management Cybernetics (was 2075) | **monograph, eng — REAL GAP** (recovered via old id 2075) |
| 2087 | Psycho-Cybernetics 365: Thrive and Grow Every Day of the Year | **monograph — REAL GAP** |
| 2138 | Cybernetic and Sculpture Environnement | pub_type=monograph but **fr** → correctly lang-excluded |
| 2174 | Autopoietic Organization Theory (Luhmann) | **unverified — no April metadata** (new; title → likely monograph) |
| 2186 | Balinese Character: A Photographic Analysis (Bateson/Mead) | **monograph — REAL GAP** |
| 2193 | Progress in Biocybernetics: Volume 2 | anthology → correctly pub-type-excluded |
| 2239 | Cybernetics: Circular, Causal and Feedback Mechanisms (Macy) | proceedings → correctly pub-type-excluded |
| 2257 | How Brains Make Up Their Minds | **monograph — REAL GAP** |
| 2271 | Cybernetic Principles of Learning and Educational Design | **monograph — REAL GAP** |
| 2283 | From Cells to Societies: Models of Complex Coherent Action | **monograph — REAL GAP** |
| 2306 | Whole Earth Catalog Access to Tools | catalog → correctly pub-type-excluded |
| 2359 | Ecological Communication | pub_type=monograph but **ca** → correctly lang-excluded |
| 2511 | Beyond Dispute: The Invention of Team Syntegrity | **monograph — REAL GAP** |
| 2517 | Invention: The Care and Feeding of Ideas | **monograph — REAL GAP** |
| 2701 | Self-Steering and Cognition in Complex Systems | **unverified — no April metadata** (new) |
| 2707 | Subjectivity, Information, Systems | **unverified — no April metadata** (new) |
| 2716 | The Cybernetic Foundation Mathematics | **monograph — REAL GAP** |
| 2776 | Helmsmen and Heroes: Control Theory as a Key to Past and Future | **unverified — no April metadata** (new) |
| 2778 | Out of Control: The Rise of Neo-Biological Civilization (Kevin Kelly) | **unverified — no April metadata** (new; title → likely monograph) |
| 2790 | Systems Approaches to Management | **unverified — no April metadata** (new; title → likely monograph) |
| 2797 | Futures We Are In (was 2383) | **monograph — REAL GAP** |
| 2799 | Democracy at Work: The Norwegian Industrial Democracy Program (was 2188) | **monograph — REAL GAP** |
| 2801 | A Choice of Futures (was 2382) | **monograph — REAL GAP** |
| 2806 | The Technoscientific Turn of Philosophy | **unverified — no April metadata** (new) |
| 2807 | Cybernetic System Design for a Complex World: The Variety Calculus | **unverified — no April metadata** (new) |
| 2808 | Systems Theory and Scientific Philosophy (Ashby application) | **unverified — no April metadata** (new) |
| 2809 | Toward a General Science of Viable Systems | **unverified — no April metadata** (new) |
| 2810 | Cyberspace for Beginners | **unverified — no April metadata** (new) |

**Verified tally (28):** **12 confirmed analysable-monograph gaps** (207, 2087, 2186, 2257,
2271, 2283, 2511, 2517, 2716, 2797, 2799, 2801) that should have been in the 544 but weren't;
**5 correctly excluded** (3 non-monograph pub-type: 2193 anthology, 2239 proceedings, 2306
catalog; 2 non-English: 2138 fr, 2359 ca); **11 unverifiable** because they are brand-new
books absent from April `books_metadata_full.csv` (2174, 2701, 2707, 2776, 2778, 2790,
2806–2810) — titles suggest most are monographs, but pub_type cannot be confirmed without a
fresh export. **So the true analysable shortfall is ≥12 and up to ~23**, putting the corrected
analysed count at ~556–567, not 544.

**Caveats confirmed:** (i) `books_lang.csv` labels 2138/2359 `eng` even though they are fr/ca —
its uniform `eng` labelling must not be trusted; only the runtime auto-detector is reliable.
(ii) The reconstruction did **not** regenerate `csv/books_metadata_full.csv` (still Apr 11), so
the July pipeline's own pub-type filter (`03_nlp_pipeline.py:319`, reads that file) ran against
**stale, old-id April metadata** — a second arm of the same reconstruction-sync problem, and a
reason the 11 new books can't be dispositioned here.

**Next:** (1) regenerate `csv/books_metadata_full.csv` from the reconstructed `metadata.db`
(via `00_export_calibre.py`) so pub_type is current and the 11 new books can be dispositioned;
(2) for id 207 (and any EPUB-only book), ensure a `format='PDF'` `books_text` row exists
(re-run PDF text extraction in Calibre) or extend ingestion to EPUB text — the current
`WHERE format='PDF'` in `split_books_text.sh` silently drops PDF-less books; (3) make streaming
clean key on `(id, metadata-fingerprint)` or otherwise resolve the No-meta mismatch so books
with reconstructed metadata are not skipped; (4) re-run, confirm the ≥12 monographs land in the
analysed set, then re-establish the canonical run.

### Longer-running backlog

| # | Task | Status |
|---|------|--------|
| 11 | Complete spaCy + Wikidata classification pass (full corpus) | ⏳ Pending |
| 12 | **Paragraph-window edges in entity network.** ~~Currently `para=0`~~ — **paragraph-window edges are now computed and included in the current build** (18 April 2026 rerun: 1,139 para edges alongside 10,362 book-level). Paragraph-window co-occurrence (±5 sentences, weighted by log(1+count)) is a distinct and richer signal from book-level co-occurrence: where book-level tells you two entities inhabit the same intellectual territory, paragraph-level with frequency tells you an author actively brought them into the same argumentative moment. High-frequency paragraph co-occurrence across multiple authors constitutes evidence of an epistemic affordance — a conceptual pairing that the field has found productive. This is also a diagnostic for the event/concept ambiguity: terms like "Cold War" that paragraph-co-occur primarily with institutional entities are functioning as historical context; those that co-occur with technical concepts are functioning as explanatory categories. Level filter already implemented; guide documentation updated with para edge explanation. **Remaining:** analysis of theoretically interesting pairs (see #22). | ✅ Edges computed — analysis pending |
| 13 | Regenerate 17 outstanding book summaries | ⏳ Pending |
| 14 | Weighted second pass (run after full pipeline) | ⏳ Pending |
| 15 | **User correction mechanism for entity network HTML** — entity network is shared publicly; viewers will spot misclassifications. Add in-report UI for users to flag/suggest corrections (e.g. wrong node kind, duplicate node, fragment node). Corrections should be capturable and feedable back into `MANUAL_CORRECTIONS`. **Design must precede implementation.** Key design questions: (a) capture channel — form→email, pre-filled GitHub issue, embedded JSON download, or other? (b) correction schema — node id, current kind, suggested kind, free-text note; (c) review/moderation workflow before corrections are committed to source. Implementation blocked until design is agreed. | ⏳ Design first |
| 16 | **Fig 3 (index.html) — topic filter dropdown uses stale topic names.** Root cause (18 April 2026): `src/patch_topic_names.py` TAXONOMY had 3 April topic names, overwriting `nlp_results.json` on every `run_all.sh`. Additionally `kp_data` in `src/06_build_report.py` omitted `lda_names`, so keyphrases topic filter used `Topic N` placeholders. Fixed 18 April 2026: (a) TAXONOMY in `patch_topic_names.py` updated to 18 April taxonomy; (b) `_LDA_BASE` fallback in `06_build_report.py` updated; (c) `'lda_names': LDA_NAMES` added to `kp_data`; (d) keyphrases filter JS updated to use `KD.lda_names`. HTML regenerated via `patch_topic_names.py` + `06_build_report.py`. Verified. | ✅ Done |
| 17 | **Entity network HTML — provenance notice covers app header.** `position:fixed;top:0` approach does not work with the network viewer's full-viewport flex layout; `body{padding-top:54px}` does not push flex children down. Fixed 18 April 2026: notice changed to `flex-shrink:0` static element injected before `<div class="header">` rather than before `</body>`. Verified. | ✅ Done |
| 18 | **Entity network — min-degree percentile filter broken for p99.** `p99` was a dropdown option but absent from `_deg_percentiles` dict passed to `STATS`. JavaScript `STATS.deg_percentiles?.['p99']` returned `undefined`, fell through to `\|\| 0`, so threshold was 0 (show all). Fixed 18 April 2026: added `'p99': float(_np.percentile(_degs, 99))` to `_deg_percentiles` in `src/14_entity_network.py`. p99 threshold = 114.6 (degree ≥ 115). Verified. | ✅ Done |
| 19 | **Entity network — degree filter not applied to node set; orphans shown at high thresholds.** Two bugs: (a) `filterGraph()` else-branch set `activeNodes = new Set(NODES.map(n=>n.id))` — all nodes — discarding `allowedNodes` entirely, so degree-filtered nodes were never removed from the canvas; (b) even with (a) fixed, nodes whose neighbours all fall below the threshold become orphans with no visible edges, degrading ink-to-signal ratio. Fixed 18 April 2026: (a) else-branch now uses `activeNodes = allowedNodes`; (b) when `degThresh > 0`, orphan nodes (no edges in `activeEdges`) are additionally removed. Reflects genuine hub-and-spoke topology: hubs connect primarily to peripheral nodes. Verified post-rerun 18 April 2026. | ✅ Done |
| 20 | **Entity network — needs explanatory document for colleagues.** Created `data/outputs/book_nlp_entity_network_guide.html` (18 April 2026): plain-language overview + technical appendix covering corpus, entity extraction, PMI×reliability weighting, filter mechanics, hub-and-spoke topology. Linked from network viewer header ("📖 Reader's guide"). Guide updated post-rerun with live network stats (1,620 nodes, 11,501 edges including 1,139 paragraph-window). | ✅ Done |
| 22 | **Research hypothesis: paragraph-level co-occurrence frequency as evidence of epistemic affordance.** *Theoretical proposition:* When an author repeatedly brings two entities into the same paragraph, this reflects an epistemic judgment — a decision that these two things belong together in the same argumentative or explanatory moment. When this pairing recurs at high frequency across multiple authors, it constitutes evidence of a field-level epistemic affordance: a conceptual pairing that the cybernetics tradition has found productive and generative. This is distinct from book-level co-occurrence, which records only that two entities inhabit the same intellectual territory; paragraph-level frequency records that authors actively reasoned with them together. *Assumption:* Paragraph proximity is a proxy for argumentative co-deployment. This assumption holds more strongly in discursive monographs than in technical texts or handbooks — consistent with the corpus construction decision to restrict to monographs and collected works. *Connection to existing theory:* This extends the "structural compression" argument in `docs/memo_media_aware_nlp_epistemic_affordances.md` §15.2, which proposes that the entity network compresses co-occurrence relationships that no individual reader could track. Paragraph-level frequency adds a further compression: not just *that* two things appear together but *how insistently* authors chose to reason with them together. The book medium's argumentative paragraph structure is itself an epistemic affordance that enables this signal — it would not be recoverable from an encyclopedia, database, or journal abstract corpus. *Proposed investigation:* Compare book-level and paragraph-level co-occurrence for a set of theoretically interesting pairs (e.g. feedback/control, Cold War/cybernetics, Wiener/Shannon). Cases where paragraph frequency is disproportionately high relative to book-level co-occurrence are candidates for field-constituting epistemic pairings. Paragraph-window edges are now available in the current build (1,139 edges; see #12). When operationalising the relationship-type dimension of "epistemic affordance" (see #24), treat the types as non-disjoint — CLAUDE.md §"non-disjoint labels require inclusion semantics". | ⏳ Ready for analysis |
| 21 | **Entity network — add "event" as a new node kind.** Cybernetics conferences, landmark publications, institutional milestones, and other historically significant events appear as index terms and should be classified and visualised as a distinct node kind alongside person, concept, organisation, and location. Design questions: (a) what constitutes an event vs. a concept — "Macy Conferences" is clearly an event; "feedback" is clearly not; but "Cold War" sits ambiguously between event and concept depending on how it is used in a given index (historical context, shaping force, analytical category). The same term may function differently across books, raising the question of whether classification should be per-term or per-occurrence; (b) event extraction — heuristic patterns, NER, manual seeding, or combination; (c) colour in the network palette; (d) whether events participate in PMI co-occurrence edges or require different edge semantics (e.g. temporal proximity). Connects to Phase 2 "Events analysis" item. **Design must precede implementation.** See CLAUDE.md §"non-disjoint labels require inclusion semantics" — event/concept is a non-disjoint space (Cold War legitimately functions as both), so per-occurrence classification or multi-label assignment is likely more faithful than a forced binary. | ⏳ Design first |

| 23 | **Entity misclassification audit tool** *(deferred)* — a periodic diagnostic (not a continuous pipeline step) to flag classification disagreements for human review. Motivation: entity classification (person/concept/org/location) uses four layers (regex, KNOWN_SINGLE_PERSONS, spaCy, Wikidata) plus MANUAL_CORRECTIONS, but residual misclassifications persist. A dedicated checker was considered and deferred 20 April 2026 for the following reasons: (a) **Principle of Context** — any automated checker operating on decontextualised node label strings faces the same fundamental ambiguity the classifier faced; it will flag genuinely ambiguous cases (e.g. "University of California" as publisher vs. institution) that require human judgement regardless; (b) **analytical impact is limited** — node kind affects colour and category counts in the visualisation but does not affect PMI edge weights, concept velocity, topic grounding, or main analytical outputs; (c) **cost-benefit** — the existing four-layer pipeline already handles the most impactful cases; the residual is a long tail of marginal and genuinely ambiguous terms; (d) **better mechanism exists** — ROADMAP #15 (viewer-flagging) surfaces real errors more efficiently because viewers bring the sentence context the algorithm lacks. **When to revisit:** when the corpus exceeds ~2,000 books, a batch Wikidata lookup on new nodes (flagging classification disagreements above a confidence threshold) would be a reasonable periodic maintenance tool. | ⏳ Deferred — revisit at 2k+ books |
| 25 | **Pub-type filter hardening in `03_nlp_pipeline.py`** (follow-up to KI-06 resolution). The monograph/collected-works filter at `src/03_nlp_pipeline.py:295-333` is lenient by design and has two silent-degradation modes: (a) **unlabelled books default to include** (line 317-318: `if not pt: return True`) — any new Calibre entry added without a `pub_type` in custom column 5 will silently pass the filter, shifting the curation discipline from CSV-level to Calibre-column-level; (b) **missing metadata CSV = filter skipped entirely** (line 332-333) — prints a warning but continues, so a broken `00_export_calibre.py` path degrades silently to a no-filter run. Easy to harden: either fail-loud on missing label / missing CSV, or add a `--strict-pubtype` flag that requires an explicit label for every book. Documenting here so leniency is an explicit choice rather than an unexamined default. Connects to the standing "fix upstream" engineering principle — the filter is upstream in the pipeline, but its input (the Calibre label) can itself be the source of drift. | ⏳ Pending |
| 24 | **Methodological open question: paragraph co-occurrence and the Principle of Context** — The entity network includes paragraph-level edges (±5 sentences, log-weighted by frequency) as a richer signal than book-level co-occurrence (ROADMAP #12, #22). Paragraph proximity is treated as a proxy for argumentative co-deployment. However, the **Principle of Context (incomplete information)** applies at the occurrence level as well as the classification level: the meaning of a specific co-occurrence of two entities within a paragraph may vary substantially depending on argumentative context — the same pairing may indicate synthesis, critique, contrast, or incidental proximity. Aggregating frequency counts across books without distinguishing these relationship types treats all associations as epistemically equivalent, which they are not. PMI and paragraph-frequency counts measure *association*, not *semantic relationship type*. A high paragraph co-occurrence score between (e.g.) Wiener and Shannon could reflect systematic intellectual synthesis, or systematic contrast, or both across different books and authors. **Why this matters for the paper:** results should be framed as patterns of association rather than patterns of intellectual relationship. Claims about epistemic pairings (ROADMAP #22) require this caveat explicitly — high paragraph co-occurrence frequency is evidence that authors brought two entities into the same argumentative moment, but the nature of that moment requires verification against source text. **Proposed investigation:** select a small set of high-frequency paragraph edges and manually examine the source paragraphs to characterise the distribution of relationship types (synthesis, contrast, citation, incidental). This would ground the methodological claim and provide language for the paper's limitations section. Connects to ROADMAP #22 and the Principle of Context in CLAUDE.md. Relationship types (synthesis / contrast / citation / incidental) are themselves non-disjoint — a single paragraph edge may legitimately carry more than one — so any coding scheme must allow multi-membership rather than forcing a primary type. See CLAUDE.md §"non-disjoint labels require inclusion semantics". | ⏳ Open — investigate before paper submission |
| 27 | **`09c_validate_topics.py` clobbered topic names written by `patch_topic_names.py`.** *Diagnosed and fixed 26 April 2026.* Symptom: after `run_all.sh` completed, `data/outputs/topic_validation.md` showed `*(to be named)*` for every topic, even though `patch_topic_names.py` reported "Updated 9/9 topics" earlier in the same run. Root cause: `09c_validate_topics.py` regenerated `topic_validation.json` from scratch with hardcoded `'proposed_name': ''` and `'notes': ''`, and runs **after** `patch_topic_names.py` in `run_all.sh` ordering. Whatever `patch_topic_names.py` had written into `topic_validation.json` was silently overwritten on every full-pipeline run. Cosmetic-only — `nlp_results.json[topic_names]` was correctly updated and is the source of truth for HTML/Excel report builders, so no shipped report was wrong. Only the human-facing validation markdown showed empty names. **Fix applied:** (a) `09c_validate_topics.py` now reads `topic_names` and `topic_notes` from `nlp_results.json` after loading results and uses them as defaults for `proposed_name`/`notes` when building the validation list (graceful degradation to empty strings when the keys are absent — preserves the original "manual edit topic_validation.json" workflow); (b) `patch_topic_names.py` extended to write `topic_notes` parallel to `topic_names` into `nlp_results.json` (previously wrote only the former); (c) trailing instruction text in 09c updated from the deprecated manual-edit workflow to the canonical "edit TAXONOMY → rerun" path. **Verification:** rerun 09c (or `run_all.sh`) and confirm `data/outputs/topic_validation.md` shows the 9 finalised names rather than `*(to be named)*`. | ✅ Done |
| 28 | **`log_pipeline_run.py` recovery gap — `nlp_hash` short-circuit prevents runlog re-ingestion on existing rows.** *Diagnosed 26 April 2026.* Symptom: when a `pipeline_runs` row already exists for the current `nlp_hash` but its `runlog_entries` count is zero (e.g. because the initial logging defaulted to today's filename and missed an end-of-day-completed runlog), passing `--runlog PATH` on a rerun has no effect. The script returns "Nothing to do" at `src/log_pipeline_run.py:287` and never reaches the `ingest_runlog()` call at line 419. Recovery requires `sqlite3 DELETE FROM pipeline_runs WHERE run_id='...'` + rerun, which is destructive (the original row's `logged_at` and any user-supplied `notes` are lost). **Concrete instance (26 April 2026):** canonical run completed 26 Apr 00:47 AEST, runlog landed at `data/outputs/runlog20260425-5.csv` (5th run started 25 April per the daily-suffix convention). `log_pipeline_run.py` invoked without `--runlog` defaulted to constructing today's filename, didn't find it, logged the run row with zero runlog entries, then refused to ingest on rerun even with explicit `--runlog`. Recovery via DELETE + rerun succeeded; 2368 runlog lines ingested second time. **Proposed fix:** when a row exists for the current `nlp_hash` AND `--runlog` is supplied AND the existing row has zero `runlog_entries`, offer to ingest the runlog into the existing row instead of treating "already logged" as terminal. Alternative robustness improvement: `latest_runlog()` could resolve by mtime across all `runlog*.csv` rather than constructing today's filename and exiting on miss — would prevent the silent miss in the first place. Either fix is small. The current behaviour penalises the recovery path for exactly the kind of date-boundary edge case it should handle gracefully. Connects to standing engineering principle "fix upstream, not downstream" — the `latest_runlog()` resolver is the upstream root cause; the short-circuit is the downstream consequence. | ⏳ Pending |
| 26 | **Drop the dual-fit pattern in `src/03_nlp_pipeline.py` — use a single seed for both `top_words` and `doc_topic`.** *Diagnosed 25 April 2026; surgical fix applied 25 April 2026.* **Surgical fix applied** — canonical LDA seed unified at `_CANONICAL_LDA_SEED = 42` across (a) k-selection scoring loop (line 695), (b) GPU canonical fit (`_fit_lda_gpu` default, line 734), (c) sklearn fallback paths (lines 782, 787). This matches `SEEDS[0]=42` in `run_stability_analysis`, which is the Hungarian-alignment reference. Result: `nlp_results.top_words` ≡ `topic_stability.canonical_words` (identical by construction at the same seed and backend), and `nlp_results.doc_topic` is in the same topic-index frame as `canonical_words`. The two LDA fits still happen separately (one redundant fit's worth of cost) but live in the same coordinate system. **Follow-up still open**: capture seed-42 components and doc_topic from the sweep workers (`_fit_one_seed`) and skip the separate canonical fit entirely. This requires modifying `_fit_one_seed` to optionally return components and doc_topic, and reordering `run_stability_analysis` to before the canonical-fit block. Estimated saving: one full LDA fit per `run_all.sh` invocation. *Diagnosed 25 April 2026.* The pipeline currently fits LDA twice with different `random_state` values: a 5-seed stability sweep (`SEEDS = [42, 7, 123, 256, 999]`) writes seed-42's top-word lists into `topic_stability.json` as `canonical_words` after Hungarian alignment to seed-42 as reference (`src/03_nlp_pipeline.py:937`, `ref = all_top_words[0]`); a separate single fit at `random_state=99` writes `top_words` and `doc_topic` into `nlp_results.json` (`src/03_nlp_pipeline.py:780-787`, sklearn fallback path). The two outputs live in unrelated topic-index coordinate systems. `09c_validate_topics.py` then pairs them by index `t` (lines 110-114, 122-125, against `doc_topic` at line 77) — across two unrelated frames — producing the topic-word vs top-book mismatch in `data/outputs/topic_validation.md`. **Diagnostic outcome (`src/diagnose_topic_alignment.py`, 25 April 2026):** Test C(i) PASSED — seed-42's `top_words` equals `topic_stability.canonical_words` exactly (set and order). Test C(ii)+D FAILED — even after Hungarian-permuting seed-99 to seed-42 (mean Jaccard 0.374), top-10-book overlap per canonical topic is 0–7/10 (criterion ≥8/10); 6 of 9 topics fail the threshold. **Diagnosis:** the validation mismatch is *not* solely a permutation bug. Cross-fit `doc_topic` is fundamentally unstable across seeds — two LDA fits at different seeds find genuinely different local optima that share top words at register level (β converges enough for word-level Jaccard) but diverge substantially on document loadings (θ diverges). The within-sweep stability metric measures word-level agreement only and says nothing about doc_topic stability. **No permutation patch in `09c` can recover cross-fit consistency for θ.** The fix must be upstream per the standing engineering principle. **Structural fix:** change `03_nlp_pipeline.py` so the same fit produces both `top_words` and `doc_topic`. Two viable approaches: (a) **drop the seed-99 fit entirely** — use the seed-42 fit from the stability sweep as the canonical fit and write its β and θ into `nlp_results.json`; (b) **drop the stability sweep's reference-aligning** — use seed-99 as the reference fit and align the other 4 seeds to it. (a) is simpler and consistent with the convention that seed 42 is the canonical reference. After the fix, `topic_stability.canonical_words` and `nlp_results.top_words` would be identical by construction; `09c_validate_topics.py` would pair top words and top books from the same coordinate system; the within-pipeline alignment bug would be eliminated by elimination of the dual-fit. **Risk:** any downstream artefact that implicitly depends on the seed-99 fit's specific topic structure (e.g. cached entity-network outputs keyed on seed-99 topic ids) would need to be regenerated. Audit before applying. **Connects to:** docs/methodology.md §"LDA topics as discursive registers" (the dispersion finding presupposes coherent θ); docs/decisions.md (record the fix when applied); standing engineering principle "fix upstream, not downstream". Diagnostic outputs at `json/topic_alignment_diagnostic.json` and `data/outputs/topic_alignment_diagnostic.md`. | ⏳ Pending — apply after current canonical run is validated |

---

## Phase 1 — Pipeline consolidation (largely complete)

Core pipeline is functional and presentation-ready (book-level LDA). Remaining items are data quality and classifier work.

- [x] Streaming corpus ingestion
- [x] LDA topic model (k=9 canonical, book-level)
- [x] NMF topic model (8 topics, chapter-level)
- [x] Abstractive summaries via API
- [x] Index extraction and canonical vocabulary
- [x] Index grounding (lift scores, density, velocity)
- [x] Time series report with concept velocity (Chart 7)
- [x] Entity relational network (4 node kinds, 4 layouts)
- [x] Entity classification (heuristics + spaCy + Wikidata cache)
- [x] Index canonicalisation (person name merging, accent normalisation)
- [x] Regression test suite (15 tests)
- [x] Book style classification pipeline (`00_*` scripts)
- [x] Monograph binary classifier Phase 1 (logistic regression, 33 features, active learning)
- [ ] Complete spaCy + Wikidata classification pass (full corpus run)
- [ ] Complete paragraph-window edge computation
- [ ] Regenerate 17 outstanding summaries
- [ ] Weighted second pass
- [ ] Signal inventory audit + document unit decision → exclusion filter

---

## Phase 2 — Analysis and interpretation

Moving from pipeline outputs to scholarly analysis. Blocked until moratorium is lifted.

- [ ] **Events analysis** — extract and classify historical events from index terms and text (cybernetics conferences, publications, institutional milestones)
- [ ] **Co-citation network** — who cites whom? Build from bibliography sections rather than indexes
- [ ] **Temporal entity analysis** — how do person and concept networks change across decades?
- [ ] **Cross-corpus comparison** — compare cybernetics corpus with adjacent fields (systems theory, complexity science, AI/ML)
- [ ] **Topic evolution** — track how LDA topic distributions shift 1954→2025
- [ ] **Canonical figures** — rank persons by centrality, temporal span, and cross-topic reach

---

## Phase 3 — Publication

- [ ] **Paper draft** — working title: *Mapping the Cybernetics Intellectual Landscape: A Computational Analysis of 695 Books*
- [ ] **Contributions.md → paper section** — merge evolving authorship statement into manuscript
- [ ] **Zenodo deposit** — archive pipeline with DOI; link from paper
- [ ] **Journal target** — TBD (candidates: *Kybernetes*, *Systems Research and Behavioral Science*, *Digital Humanities Quarterly*)
- [ ] **GitHub release** — tag v1.0 when pipeline is fully validated

---

## Open questions

- Should `book_nlp_entity_network.html` include a "works" node kind for cited books? Currently suppressed.
- Is the Wikidata rate limit (2 req/sec) acceptable for future full re-runs, or should we cache more aggressively?
- Should `test_pipeline.py` be run as a GitHub Action on each push?
- What is the right `n_books` threshold for the canonical vocab? Currently 3. Lower = more terms, more noise.
- Multi-label classifier Phase 2: when will anthology and textbook classes have sufficient expert labels (~20 each)?

---

## Deferred / won't do (for now)

- **Full-text search index** — Calibre already provides this
- **Browser-based Jupyter interface** — out of scope for a pipeline tool
- **GPU-accelerated embeddings** — sentence-transformers works fine on CPU for 695 books
