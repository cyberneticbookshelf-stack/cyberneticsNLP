# CyberneticsNLP — Persistent Project Context
**Last updated: 10 April 2026 | Maintained in: Cowork**

Paste this at the start of any Chat session working on CyberneticsNLP.
Chat cannot access the filesystem directly — this note is its substitute.

---

## Infrastructure

| Machine | Role | Notes |
|---------|------|-------|
| **Cybersonic** | Dedicated GPU server (remote) | Canonical home of the repo; full pipeline runs via SSH |
| **NorbertX** | Local workstation | Has Calibre; mounts Cybersonic/CyberneticsNLP as local drive; light runs and testing |
| **AshbyX** | Local workstation | Also mounts Cybersonic/CyberneticsNLP as local drive; light runs and testing |

**Canonical repo path (on Cybersonic):** `~/cybersonic/CyberneticsNLP`

Both NorbertX and AshbyX mount this path directly — there is no OneDrive sync.
Cowork accesses it at `/sessions/.../mnt/cybersonic--CyberneticsNLP` (same files).

**Calibre** lives on local machines (NorbertX / AshbyX).
`00_export_calibre.py` must be run locally (not on Cybersonic) to access `metadata.db`.
The exported `data/csv/books_metadata_full.csv` is written into the mounted repo
and is immediately available to Cybersonic for the next pipeline run.

**Workflow by task:**
- File editing / inspection → Cowork (via mount) or local text editor
- `00_export_calibre.py` (Calibre export) → NorbertX or AshbyX
- Single-script tests → NorbertX or AshbyX
- Full `run_all.sh` pipeline → SSH into Cybersonic

---

## Corpus

- **690 books** in current corpus (as of v0.4.2 pipeline run, April 2026)
- Source: Calibre library, cybernetics collection, exported via `00_export_calibre.py`
- Canonical metadata CSV: `data/csv/books_metadata_full.csv` (21 columns, tab-separated)
  - 21st column `lang_code` added April 2026 (ISO 639-2, from Calibre `languages` table)
- Pipeline entry point: `src/run_all.sh`
- Parse chain: 695 text CSVs → 692 after metadata join → 691 after min-chars → 690 after alpha-ratio

## Key pipeline parameters (canonical, do not change without a decisions.md entry)

- **LDA topics:** k=9, 5 seeds (`--topics 9 --seeds 5` in `run_all.sh`)
- **Alpha-ratio filter:** ≥ 40% alphabetic content (books below excluded at parse)
- **Language filter:** books with explicit non-`eng` `lang_code` excluded at parse
  (books with no lang_code set pass through — metadata gap ≠ exclusion)
- **Monograph classifier threshold:** 0.4 (logistic regression, 33 features, 197 expert labels)

---

## Active moratorium

**No further NLP pipeline code changes** until signal inventory audit and
document unit decision are complete. Classifier work (`train_monograph_classifier.py`,
active learning) is outside this moratorium.

---

## Terminology (use consistently)

- **Expert labels** — Paul's judgements in Calibre `custom_column_5`; NOT "ground truth"
- **Agreement rate** — not "accuracy" — when evaluating classifier on Paul's random samples
- **Expert-labelled set** — the 197 (and growing) labels; source of training data
- **Heuristic classifier** — `00_classify_book_styles.py`; outputs to `book_styles.json`
- **Supervised classifier** — `train_monograph_classifier.py`; learns from expert labels

**Critical rule:** Machine-inferred labels from `00_classify_book_styles.py` must NEVER
be used as training data for the supervised classifier. (See `docs/decisions.md`.)

---

## Current version

- **v0.4.2** (committed 8 April 2026)
- Latest commit: `lang-filter` (10 April 2026) — adds `lang_code` to metadata export
  and filters non-English books at parse time in `01_parse_books.py` and
  `parse_and_clean_stream.py`

## Key files Chat should ask the user to paste if needed

- `docs/decisions.md` — all design decisions with rationale
- `docs/methodology.md` — full methodology documentation
- `docs/CHANGELOG.md` — version history
- `data/outputs/runlog.csv` — last pipeline run log (1876 lines)
- `json/monograph_classifier.json` — classifier metadata
