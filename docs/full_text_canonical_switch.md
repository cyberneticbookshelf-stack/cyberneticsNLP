# Full-text canonical switch — pre-Tuesday-presentation checklist

**Created:** 25 April 2026 (Saturday)
**Target:** Tuesday 28 April 2026 presentation
**Status:** Planned. Not yet executed.
**Destination on remount:** `docs/full_text_canonical_switch.md`

---

## Plan

Switch the canonical LDA fit from `sampled` (3 × 20k slices per book) to `full_text`
(front/back-matter-stripped body). Re-establish provisional topic names against the
new decomposition. Refresh all downstream artefacts and documentation before Tuesday.

**Why now.** Verified 25 Apr: `nlp_results.json` carries `pipeline_mode = sampled`.
Sampled mode was a laptop-hardware compromise. Moving canonical to full-text gives
the model the whole intellectual body of each book and removes the "the LDA only
saw 60k chars per book" caveat in dissemination.

**Cost — equivalence-class break.** The hash in `pipeline.db` includes
`pipeline_mode`. A full-text run lives in a new equivalence class. Any existing
Google Forms responses against the sampled class cannot be aggregated with future
full-text ratings under the multi-rater protocol. Decide before switching whether
to preserve sampled responses as a snapshot or treat them as superseded. Record in
`docs/decisions.md`.

**Alternative considered.** Keep sampled as canonical and frame the index guide /
paper around the sampling choice. Cheaper, no rerun, no equivalence break. Rejected
— canonical full-text gives a stronger story for the presentation.

---

## Step 1 — Run

On the NLP machine:

    # Option A — modify run_all.sh:122 to add --full-text, then:
    bash src/run_all.sh

    # Option B — one-off, without committing run_all.sh change:
    python3 src/03_nlp_pipeline.py --min-chars 10000 --lemmatize --topics 9 --seeds 5 --full-text
    python3 src/patch_topic_names.py
    python3 src/check_stale_vars.py --fix
    python3 src/09c_validate_topics.py --top 10 --md
    # then continue run_all.sh from step 04 onward, or just rerun run_all.sh end-to-end

Verify `nlp_results.json` carries `pipeline_mode: 'full_text'`. Log the run with
`python src/log_pipeline_run.py --runlog data/outputs/runlogYYYYMMDD.csv`.

---

## Step 2 — Provisional topic names

Full-text fit will produce different topics with different T1–T9 numbering. Current
TAXONOMY in `src/patch_topic_names.py:108-109` is mapped to the *sampled* indices
and will be wrong against the new fit.

1. Read `data/outputs/topic_validation.md` (top words, stability, high-loading
   titles for each new topic).
2. Hand-assign provisional names to each new T*n* using the same triangulation as
   before.
3. Update TAXONOMY in `src/patch_topic_names.py`.
4. `python src/patch_topic_names.py && python src/check_stale_vars.py --fix`.
5. Rerun `09c_validate_topics.py` to confirm names propagated.

T9 is currently labelled "Residual / Outlier Cluster" by interpretation (KI-05).
Whether the full-text fit also yields a residual/outlier topic is empirical —
inspect, don't carry the label across by default.

Names remain provisional under the multi-rater protocol regardless of the mode
change.

---

## Step 3 — Auto-regenerated artefacts (rebuilt by run_all.sh, just sanity-check)

- `json/nlp_results.json`, `json/topic_stability.json`
- `data/outputs/index.html`, `clusters.html`, `cosine.html`, `keyphrases.html`, `books.html`
- `data/outputs/topic_validation.md`
- `data/outputs/book_nlp_entity_network.html` (independent of LDA but rebuilt by 14)
- All Excel workbooks under `data/outputs/`
- Chapter-level outputs: `nlp_results_chapters.json`, chapter HTMLs, chapter Excel
- All `figures/*.png`

Entity network nodes/edges are derived from index extraction + paragraph windows,
not from the topic model — counts should be unchanged unless the corpus changed.

---

## Step 4 — Hand-authored documentation needing manual revision

### Reader's guides (published HTML)

- `data/outputs/book_nlp_index_guide.html` — hardcoded numbers will all change:
  perplexity sweep table k=2..12, per-topic stability table at k=9, mean stability
  "0.357", topic names in the stability table, the §"Sampling and tokenisation"
  description (full-text becomes default), the analysis-input table.
- `data/outputs/book_nlp_entity_network_guide.html` — entity counts, LCC %, degree
  stats; edit only if numbers shifted.
- *To be created after the rerun:* `book_nlp_clusters_guide.html`,
  `book_nlp_cosine_guide.html`, `book_nlp_keyphrases_guide.html`.

### Project-level documentation

- `CLAUDE.md` — §"Project snapshot" canonical-run framing; "k=9 validated 3 April
  2026" date; sampling-mode references in §"Standing methodological principle";
  KI-05 row may need re-statement against new T-numbering.
- `docs/CHANGELOG.md` — add entry: canonical pipeline mode `sampled → full_text`;
  equivalence-class break recorded.
- `docs/decisions.md` — new ADR "Switch canonical LDA mode from sampled to
  full_text" with rationale, equivalence-class consequences, status of prior
  survey responses.
- `docs/methodology.md` — search for "sampled", "60k", "60,000", "sample_book";
  update narrative for full-text default.
- `docs/ROADMAP.md` — header currently reads "Moratorium on NLP pipeline code in
  effect. Presentation complete (book-level LDA)." Both clauses need updating —
  moratorium being lifted for this switch; presentation is Tuesday and being prepped
  against a refreshed canonical run.
- `02 Projects/CyberneticsNLP/CyberneticsNLP.md` (master vault doc) — sprint log +
  known issues.

### Code comments

- `src/03_nlp_pipeline.py:411-417` — sampling comment block describes sampled as
  default and full-text as the server alternative. Reverse the framing if Option A
  in Step 1 is taken.
- `src/run_all.sh` — header comment if it describes the canonical run.

---

## Step 5 — Tuesday presentation deck

`presentation/CyberneticsNLP_Talk_v3.pptx` — full content audit:

- Charts/figures referencing perplexity, stability, topic names, dominant-book
  lists must be regenerated against the new fit.
- Speaker notes / slide body text quoting sampled-run numbers ("mean stability
  0.357", "T1 = Cybernetics of Political Economy") must be rewritten against the
  new TAXONOMY.
- Methods slide: input description must say full-text, not "60k char sample".
- If the deck shows entity-network screenshots, regenerate after rerun for
  consistent timestamps.
- Sanity-check the deck's narrative arc against the new topic structure —
  provisional names may shift the story.
- Consider bumping to `_v4.pptx` to make the canonical-mode change explicit in
  the version trail.

---

## Risk register

1. **Time.** Saturday → Tuesday. Full-text run on 541 books with `--seeds 5` will
   take substantially longer than the sampled equivalent. Start the run early
   Monday at the latest; have a fallback plan in case of OOM or stale mount.
2. **Stability may drop.** Full-text gives more vocabulary per book, which can
   either improve or worsen stability — won't know until the run completes. If
   mean stability drops below the current 0.357, the deck should acknowledge this
   rather than hide it.
3. **Topic names will shift.** Anyone who has previewed the sampled topic names
   will see different names. Worth a one-line acknowledgement if relevant.
4. **Provisional status unchanged.** Even with a full-text canonical run, names
   remain provisional under the multi-rater protocol — frame topics as
   provisional, not validated.

---

## When done

Move salient parts of this file into `docs/CHANGELOG.md` and `docs/decisions.md`,
then archive this file to `docs/archive/` or delete. It is a transient working
note, not a canonical log.
