# Methodology Note: Topic Naming Reliability and Inter-Run Stability

**Project:** CyberneticsNLP  
**Date:** 14 April 2026  
**Status:** Agreed methodology — implementation pending  
**Agreed in:** Chat session (date TBC — confirm and add to session log)

---

## 1. The Problem

Topic names in the current pipeline are agreed by a single rater (Paul Wong) inspecting the top-loading books for each topic in a single canonical pipeline run (k=9, 3 April 2026). This creates two compounding reliability problems:

**Single-run instability.** LDA is a stochastic model. Even with fixed seeds, small changes to the corpus, preprocessing, or hyperparameters can shift which books load on which topics and change the composition of the top-word list. A name agreed in one run may not accurately describe the topic cluster in a subsequent run. The recurrent observation that agreed names do not match up with top words or top books when plots and visualisations are regenerated is a symptom of this instability — the visual output reflects a different run state than the one on which naming was based.

**Single-rater subjectivity.** Topic naming is an interpretive act. A single rater's judgement about what a cluster of books "is about" reflects their domain knowledge, conceptual priors, and attention at a particular moment. There is no mechanism to distinguish a name that reflects a stable, replicable intellectual cluster from one that reflects the rater's idiosyncratic reading of an ambiguous book list.

Together these mean the current names carry more epistemic weight in the paper and visualisations than they can legitimately bear.

---

## 2. Agreed Solution: Run-Records System

A run-records system will be implemented to track topic naming across pipeline runs and raters. The core principle is that topic names should only be used in the paper and presented as findings once they have demonstrated stability across runs and agreement across raters.

### 2.1 Run record structure

For each pipeline run, a record is appended to `json/topic_run_records.json`:

```json
{
  "run_id": "run_20260403_k9_s5",
  "date": "2026-04-03",
  "parameters": {
    "k": 9,
    "seeds": [42, 7, 123, 256, 999],
    "min_chars": 10000,
    "lemmatize": true
  },
  "stability": {
    "stable_topics": 7,
    "dead_topics": 0,
    "mean_stability": 0.382
  },
  "topics": [
    {
      "topic_id": "T1",
      "top_words": ["word1", "word2", "..."],
      "top_books": [
        {"id": 123, "title": "...", "loading": 0.87},
        "..."
      ],
      "naming_records": [
        {
          "rater": "Paul Wong",
          "name": "Management Cybernetics",
          "date": "2026-04-03",
          "confidence": "high",
          "notes": "VSM and Beer dominate top books; words less diagnostic"
        }
      ]
    }
  ]
}
```

### 2.2 n-run comparison report

```bash
python src/compare_topic_runs.py --runs N
```

The user specifies N — the number of pipeline runs to compare. The script either:
- Runs the pipeline N times fresh (each with fixed seeds, recording results to `topic_run_records.json`), or
- Reads the last N completed records from `topic_run_records.json` (default if records exist)

Output is an HTML report at `data/outputs/topic_run_comparison_N.html` showing, for each topic:

**Book presence matrix** — rows = books (union of top books across all N runs), columns = runs. A ✓ or loading score in each cell shows whether a given book appeared in that run's top N. Books present in all N runs form the "stable core". This scales naturally to any N.

**Word stability** — for each word in the union of top-10 lists, count in how many of the N runs it appeared. Words present in all N runs are highlighted as the stable vocabulary signal.

**Naming records table** — one row per (run × rater) combination. Shows proposed name, rater, date, confidence, notes. Agreement status computed across all N naming records.

**Inter-run book overlap** — pairwise overlap percentages between all run combinations (N×N matrix or summary).

The two-column side-by-side layout (appropriate for N=2) is replaced by the matrix/table layout for N>2, which scales to arbitrary N without becoming unreadably narrow.

### 2.3 Naming stability criterion

A topic name is considered **stable** when:
- The top 5 books by loading score overlap ≥60% across ≥3 pipeline runs
- ≥2 independent raters assign the same name (exact match or agreed synonym) to the same top-book list

Until these criteria are met, names are **provisional** and should be clearly labelled as such in all outputs, reports, and the paper.

---

## 3. Multi-Rater Protocol

### 3.1 Rater requirements

- At least 2 raters per naming exercise
- At least one rater must have cybernetics domain expertise independent of pipeline development
- Raters should not see each other's names before completing their own

### 3.2 Naming procedure

Each rater receives:
1. The top 10 words for the topic
2. The top 10 books by loading score (title, author, year only — no summaries)
3. A free-text field for a proposed name (1–5 words)
4. A confidence rating (high / medium / low)
5. A notes field for reasoning

Raters complete this independently before any discussion.

### 3.3 Agreement coding

After independent naming:
- **Exact agreement**: same name or clear synonym → stable, use the name
- **Partial agreement**: overlapping concept, different framing → discuss, reach consensus name, record both originals
- **Disagreement**: substantially different interpretations → flag topic as ambiguous; document in paper; do not present as a stable finding

Inter-rater reliability will be reported in the paper using percentage agreement on the core conceptual referent (not exact string match).

---

## 4. Relationship to Existing Methodology

### 4.1 Triangulation framework

The five-signal triangulation framework (LDA top words → high-loading titles → aggregated index terms → keyphrases → year distribution) was developed to validate topic *content*. The run-records system and multi-rater protocol extend this to validate topic *names* — the human interpretive layer on top of the statistical output.

The recurring mismatch between top words and top books (e.g. T8: words suggested popular writing; books revealed VSM/management cybernetics) is not a flaw in the triangulation framework — it is precisely what the framework is designed to detect. But it does mean that a name derived from a single title-sweep in a single session is based on one signal at one point in time. The run-records system ensures that the name reflects a pattern that persists across runs and is legible to more than one reader.

### 4.2 Implications for the paper

The current k=9 names should be presented in the paper as **provisional working names** derived from title-sweep inspection. The paper should report:

- That names were assigned by title-sweep (triangulation framework signal 2) rather than word-level inspection
- That naming reliability was assessed using the run-records system (describe methodology)
- The inter-rater agreement score for each topic name
- Which topics showed high naming stability across runs and raters, and which were ambiguous

Topics with low naming stability or rater disagreement should be discussed as methodological findings — they are likely the most intellectually interesting cases (boundary topics, topics where cybernetics' intellectual diffusion has created genuinely ambiguous clusters).

### 4.3 What "locked" means

The phrase "taxonomy agreed and locked" in earlier documentation was premature. The correct status is:

- **k=9** — locked (confirmed as canonical solution by coherence, stability, and interpretability criteria)
- **Topic compositions** (which books load on which topic) — stable within this run; may shift with corpus changes
- **Topic names** — provisional; subject to revision pending run-records and multi-rater validation

---

## 5. Immediate Implication for the 27 April Presentation

The presentation should not present topic names as settled findings. The recommended framing is:

> *"Working names assigned by title-sweep inspection — subject to validation across runs and independent raters."*

Visualisations should show the top books alongside the names, making the basis of naming transparent. This actually strengthens the methodological argument: it demonstrates that the names come from the data (the books), not from the model (the words), and that the epistemic work is being done by the title-sweep signal rather than by LDA word lists alone.

---

## 6. Implementation Priority

| Task | Priority | Estimated effort |
|---|---|---|
| `json/topic_run_records.json` schema + populate with k=9 canonical run | High — before presentation | 1–2 hours |
| `src/compare_topic_runs.py` comparison report | Medium — post-presentation | Half day |
| Multi-rater naming session (second rater) | High — before paper draft | Requires rater scheduling |
| Update paper draft to reflect provisional naming status | High — in paper draft | Minimal once protocol is designed |

---

*Methodology note compiled 14 April 2026 (Cowork session). Based on agreed decision in Chat session — confirm session date and add to session log.*
