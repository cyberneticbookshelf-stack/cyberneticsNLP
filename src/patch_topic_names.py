"""
patch_topic_names.py
────────────────────
Writes agreed topic names and notes into topic_validation.json and
nlp_results.json — matching each name to a topic **by content**, never by
position.

Run from project root:
    python3 src/patch_topic_names.py                # apply (gated)
    python3 src/patch_topic_names.py --report       # show alignment, write nothing
    python3 src/patch_topic_names.py --emit-signatures
    python3 src/patch_topic_names.py --force        # apply despite a failed gate

WHY THE GATE EXISTS (ROADMAP #32, 20 September 2026)
────────────────────────────────────────────────────
This script used to apply TAXONOMY['T1'] to topic index 0, TAXONOMY['T2'] to
index 1, and so on. That is only valid while topic positions are stable, and
they are not. When the corpus grew 566 -> 575 books, the clusters **recombined**:
two July topics merged into one, one split across two, one dispersed, and one
new topic emerged with no predecessor. **0 of 9 names landed on the right
topic**, every downstream report shipped mislabelled, and nothing failed —
`check_stale_vars.py` reported "9/9 match" throughout, because it compares
scripts against nlp_results.json, which by then already held the wrong names.
The error was caught only by hand-comparing top words against an old runlog.

So the rule this script now enforces: **a name belongs to a run, not to a topic
index.** Each TAXONOMY entry carries a SIGNATURE — the top words of the topic it
was validated against. On every invocation the stored signatures are aligned
against the current run's topics by word overlap (optimal assignment, not
greedy), and names are applied along that alignment. If the alignment is weak or
ambiguous, the script **refuses to write** rather than guessing.

It also refuses outright when the equivalence class has changed, because a
changed corpus is precisely the situation where names stop transferring — and a
confident-looking alignment is then more dangerous than no alignment at all.
Re-validate the names against the new run, then refresh this file's provenance
and signatures with --emit-signatures.
"""
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# Alignment gate thresholds.
# MIN_OVERLAP: a stored signature must share at least this Jaccard overlap with
#   the topic it is matched to. Calibrated against the 20 Sep evidence: a topic
#   that genuinely carried across runs scored 0.50-0.71 on top-8 words, while
#   merged/dispersed topics scored 0.20-0.33. 0.50 sits at that boundary — but
#   note the gate below refuses on a changed equivalence class regardless, so
#   this threshold mainly guards same-class re-fits.
# MIN_MARGIN: the best match must beat the runner-up by this much, otherwise the
#   assignment is ambiguous (two names contending for one topic — the signature
#   of a merge).
MIN_OVERLAP = 0.50
MIN_MARGIN = 0.10

# ── Full-text canonical taxonomy (541-book corpus, 25 April 2026) ─────────────
# First genuine full-text canonical run (--full-text --max-features 15000).
# Names derived from seed-42 top-loading books in the 25 April run after
# diagnostic established that doc_topic argmax assignments are unreliable
# across the seed-42 / seed-99 split (see docs/methodology.md §"LDA topics
# as discursive registers, not subject domains" and ROADMAP #26).
#
# Per session startup protocol (CLAUDE.md): names are provisional pending
# Paul Wong's validation of the full-text canonical run. Stability scores
# below should be refreshed from json/topic_stability.json after each run;
# the literals here are intentionally omitted to avoid stale figures.
#
# All names should be read as discursive registers ("how cybernetics gets
# written about"), not as subject domains ("what cybernetics is about").
# See docs/methodology.md for the full reframe and the PCT-dispersion
# worked example.
# ─────────────────────────────────────────────────────────────────────────────
# CURRENT: names finalised 20 September 2026 (single rater) against the 575-book
# run `runlog20260920-2` — 742 full-text rows from the enlarged Calibre collection
# (755 books in metadata.db), 26 books newly gaining full text since 19 July.
#
# This is a NEW equivalence class (575 books, not the 566 of 19 July). Topic
# positions did NOT merely permute this time — the clusters recombined. Provenance,
# measured as where each July topic's top-10 books are now dominant:
#
#     July T3  → T4  (10/10)   clean transfer
#     July T5  → T2  ( 9/10)   clean transfer
#     July T7  → T3  (10/10)   clean transfer
#     July T6  → T6  (10/10) ┐ MERGE: formal/mathematical + control engineering
#     July T8  → T6  ( 8/10) ┘        (T6 now has 5 books at loading 1.000)
#     July T4  → T7  (10/10) ┐ MERGE: self/therapy + popular history & biography
#     July T1  → T7  ( 6/10) ┘
#     July T9  → T8  ( 6/10) ┐ SPLIT: architecture strand → T8, arts/media → T5
#     July T9  → T5  ( 4/10) ┘
#     July T2  → dispersed   (3/10 → T1, 4/10 → T5, remainder scattered)
#
# T9 has NO July parent: no July top-10 book is dominant there, yet it is the
# largest topic in the run (110 books, 68 at loading ≥0.50). It cohered out of
# material that sat mid-loading across the July solution.
#
# T1 is retained as an UNNAMED RESIDUAL — excluded from interpretation and from
# reader-facing topic lists, but kept in the k=9 solution. It is NOT a dead topic:
# 09c's dead_topic() returns False for it (top-10 loadings 1.00, 0.99, 0.76, 0.63,
# 0.61, …), so the zero-dead-topics basis for canonical k=9 in docs/decisions.md
# §"Dead-topic count" is unaffected. It was dropped on incoherence between its word
# list (Sinophone: qian, chinese, xuesen) and its book list (3 of its 7 books have
# no China content; the top loading at 1.000 is about speaking and singing), at
# 0.159 stability over 7 books.
#
# Reporting framing (decided): "nine topics, one residual" — the k=9 model is stated
# as fitted, with T1 named as residual rather than silently omitted. Reader-facing
# counts are 9 topics / 8 interpreted.
#
# Because positions recombine when the corpus grows, the positional mapping below is
# only valid for THIS equivalence class. Re-derive it against the landing matrix
# before reusing these names on any future run — see ROADMAP: patch_topic_names.py
# should align by word overlap rather than by position.
#
# Provisional, single-rater, single-run; the multi-rater protocol (sprint item 4,
# ≥3 runs × ≥2 raters) remains outstanding.
#
# PRIOR: names finalised by Paul Wong, 19 July 2026, against the 566-book
# re-canonicalisation run (post-Calibre-reconstruction, KI-13); superseded above.
# ─────────────────────────────────────────────────────────────────────────────
TAXONOMY = {
    'T1': {
        'proposed_name': 'Residual — uninterpreted',
        'notes': (
            'UNNAMED RESIDUAL — retained in the k=9 solution, excluded from '
            'interpretation and from reader-facing topic lists. Not a dead '
            'topic: dead_topic() returns False (top-10 loadings 1.00, 0.99, '
            '0.76, 0.63, 0.61), so the zero-dead-topics basis for canonical '
            'k=9 is unaffected. Dropped on incoherence between word list '
            '(Sinophone: qian, chinese, xuesen, china) and book list — 3 of '
            'its 7 books have no China content and the 1.000 top loading is '
            'A Cybernetic Study of Speaking and Singing. Residue of July T2, '
            'which dispersed. Stability 0.159 over 7 books; lowest in the run.'
        ),
    },
    'T2': {
        'proposed_name': 'Social Systems and Second-Order Constructivism',
        'notes': (
            'Discursive register: Luhmannian social systems theory and '
            'second-order/constructivist epistemology. Luhmann anchors '
            'strongly (Theory of Society 0.930, Social Systems 0.927, '
            'Theories of Distinction 0.914, Law as a Social System 0.876); '
            'The Making of Meaning, actor-network and constructivist '
            'currents. Most stable topic this run (0.586), 100 books. '
            'Clean transfer from July T5 (9/10 of its top-10 land here).'
        ),
    },
    'T3': {
        'proposed_name': 'Management and Organisational Cybernetics',
        'notes': (
            'Discursive register: organisational and managerial cybernetics, '
            'VSM lineage and system dynamics. The Cybernetics of Workplace '
            'Conflict (1.000), Democracy at Work (0.998), Structural '
            'Cybernetics (0.983), The Fractal Organization (0.980), '
            'project/construction management. Stable (0.430), 69 books. '
            'Clean transfer from July T7 (10/10).'
        ),
    },
    'T4': {
        'proposed_name': 'Biological and Ecological Regulation: Homeostasis & Allostasis',
        'notes': (
            'Discursive register: biological and ecological regulation. '
            'Rethinking Homeostasis (0.994), What Is Health? Allostasis '
            '(0.990), The Communication Systems of the Body (0.936), Social '
            'Allostasis, Principles of Neural Design. Stable (0.368), 37 '
            'books — the smallest interpreted topic. Clean transfer from '
            'July T3 (10/10).'
        ),
    },
    'T5': {
        'proposed_name': 'Cybernetics and Digital Culture',
        'notes': (
            'Discursive register: digital media arts, music, performance and '
            'posthuman culture. The Composer\'s Black Box (0.884), Digital '
            'Performance (0.866), History of Computer Art (0.858), '
            'Cybernethisms (0.852), Experimenting the Human. Stable (0.320), '
            '45 books. Recombination with no majority parent: July T2 (4/10), '
            'July T9 (4/10), July T1 (2/10). NOTE the architecture strand of '
            'July T9 did NOT come here — 6 of 7 architecture-titled books are '
            'now in T8, so this topic is the arts/media half only.'
        ),
    },
    'T6': {
        'proposed_name': 'Formal Foundation and Control Engineering',
        'notes': (
            'Discursive register: mathematical formalism and control '
            'engineering, merged. MERGE of July T6 (formal/mathematical, '
            '10/10) and July T8 (control/feedback, 8/10) — the merged topic '
            'is tighter than either parent, with five books at loading 1.000 '
            '(Marine Control Systems, Engineering Cybernetics, Cybernetical '
            'Physics, Random Wavelets, Mathematical Structure of Finite '
            'Random Cybernetic Systems) spanning 1954-2007. Stable (0.413), '
            '59 books, median loading 0.70 — the most concentrated topic. '
            'PCT engineering vocabulary anchors here: the methodology.md '
            'PCT-dispersion worked example needs re-checking against this '
            'equivalence class.'
        ),
    },
    'T7': {
        'proposed_name': 'Cybernetics of Self and Reimagination of Self',
        'notes': (
            'Discursive register: the personal and narrative voice — self-'
            'help, memoir, fiction and popular history sharing an anecdotal, '
            'second-person address. MERGE of July T4 (self/therapy, 10/10) '
            'and July T1 (popular history and biography, 6/10). R.U.R. '
            '(0.995), Psycho-Cybernetics franchise (0.989, 0.975, 0.912), '
            '@Heaven (0.979), The Cyberiad (0.965, 0.956), With a Daughter\'s '
            'Eye (0.929). Stable (0.334), 81 books. Word list still reads '
            'Bateson/family-therapy, but that material is now a minority of '
            'the top loadings — the register, not the subject, is what unites '
            'it.'
        ),
    },
    'T8': {
        'proposed_name': 'Political Economy of Cybernetics',
        'notes': (
            'Discursive register: Cold War and postcolonial political '
            'history, political economy, and the architectural imaginary of '
            'cybernetics. The Cybernetic Border (0.918), The Internet '
            'Revolution (0.904), Imaginary Futures (0.904), Constructing '
            'Soviet Cultural Policy (0.902), Balkan Cyberia (0.853), How Not '
            'to Network a Nation, Cybernetic Circulation Complex. Inherits '
            'the majority of July T9 (6/10) including its architecture '
            'strand — Architectural Principles in the Age of Cybernetics, '
            'Architecture in Digital Culture, Last Futures. Stable (0.455), '
            '67 books, median year 2017 — the most contemporary topic, '
            'grown by recent critical scholarship.'
        ),
    },
    'T9': {
        'proposed_name': 'Cognition and Cybernetics',
        'notes': (
            'Discursive register: philosophy of mind, behaviour and machine — '
            'purposive explanation, perception, language and the cybernetic '
            'account of cognition. Philosophical Foundations of Cybernetics '
            '(0.988), The Discovery of the Artificial (0.953), Purposive '
            'Explanation in Psychology (0.923), Cybernetics and Biology '
            '(0.919), The Foundations of Cybernetics (0.907). LARGEST topic '
            'in the run (110 books, 68 at loading >=0.50) yet it has NO July '
            'parent — no July top-10 book is dominant here; it cohered out of '
            'material that sat mid-loading across the July solution. '
            'Moderate stability (0.237), the lowest of the interpreted eight, '
            'and it holds no vocabulary exclusive to itself — both worth '
            'watching on the next run.'
        ),
    },
}

# ── Provenance of the taxonomy above ─────────────────────────────────────────
# The run these names were validated against. If the current run's equivalence
# class differs from this, the names are not entitled to transfer — see the
# module docstring.
TAXONOMY_PROVENANCE = {
    'run_id':            'run_20260920_k9_s5',
    'equivalence_class': '3273ea3e577fdc99',
    'nlp_hash':          '92b9f2d2151f0ee7',
    'k':                 9,
    'n_books':           575,
    'validated':         '2026-09-20',
    'rater':             'single (provisional — sprint item 4 requires >=3 runs x >=2 raters)',
}

# ── Topic signatures ─────────────────────────────────────────────────────────
# Top words of each topic **as validated**, used to match names to topics by
# content. Regenerate with --emit-signatures after any re-validation, and update
# TAXONOMY_PROVENANCE in the same edit — the two must always describe the same
# run, or the gate is checking one run's names against another run's fingerprint.
SIGNATURES = {
    'T1': ['city', 'qian', 'chinese', 'water', 'xuesen', 'ancient', 'culture', 'china', 'century', 'invention', 'tion', 'technology'],
    'T2': ['social', 'communication', 'society', 'environment', 'meaning', 'object', 'distinction', 'reality', 'philosophy', 'organization', 'language', 'complexity'],
    'T3': ['decision', 'management', 'organization', 'variety', 'environment', 'organisation', 'manager', 'company', 'goal', 'feedback', 'market', 'cybernetic'],
    'T4': ['cell', 'brain', 'animal', 'neuron', 'energy', 'organism', 'body', 'evolution', 'behavior', 'mechanism', 'biological', 'specie'],
    'T5': ['computer', 'machine', 'technology', 'medium', 'cybernetic', 'body', 'artist', 'image', 'digital', 'object', 'robot', 'program'],
    'T6': ['input', 'variable', 'equation', 'output', 'rate', 'define', 'feedback', 'network', 'energy', 'signal', 'property', 'probability'],
    'T7': ['bateson', 'person', 'feel', 'family', 'child', 'tell', 'story', 'therapy', 'woman', 'talk', 'image', 'therapist'],
    'T8': ['cybernetic', 'social', 'wiener', 'technology', 'political', 'economic', 'society', 'machine', 'culture', 'computer', 'architecture', 'network'],
    'T9': ['machine', 'behavior', 'language', 'brain', 'computer', 'cybernetic', 'organism', 'perception', 'object', 'pattern', 'message', 'signal'],
}


# ── Alignment machinery ──────────────────────────────────────────────────────

def jaccard(a, b):
    sa, sb = set(a), set(b)
    return len(sa & sb) / len(sa | sb) if (sa or sb) else 0.0


def current_equivalence_class(nlp):
    """Equivalence class of the loaded run, or None if it cannot be computed."""
    try:
        from pipeline_db import compute_run_hash
        stab = nlp.get('stability') or {}
        seeds = stab.get('seeds_used')
        if not seeds:
            return None
        return compute_run_hash(
            nlp['n_topics'], len(nlp['book_ids']), nlp.get('max_features'),
            nlp.get('pipeline_mode'), seeds,
        )
    except Exception as exc:                      # pragma: no cover - diagnostic
        print(f"  [class] could not compute equivalence class: {exc}")
        return None


def align(stored, current_words):
    """Match stored signatures to current topics by optimal assignment.

    stored        : {label: signature_words}
    current_words : list of top-word lists, indexed by current topic index

    Returns (mapping, scores, matrix) where mapping is {current_index: label},
    scores is {label: (best_score, runner_up_score)}, and matrix is the full
    label x index overlap grid for reporting.
    """
    labels = sorted(stored, key=lambda s: int(s[1:]))
    matrix = {lab: [jaccard(stored[lab], cw) for cw in current_words]
              for lab in labels}

    # Optimal assignment — greedy would happily hand two names the same topic.
    try:
        from scipy.optimize import linear_sum_assignment
        import numpy as np
        cost = np.array([[-matrix[lab][i] for i in range(len(current_words))]
                         for lab in labels])
        rows, cols = linear_sum_assignment(cost)
        pairs = list(zip(rows, cols))
    except ImportError:                            # pragma: no cover - fallback
        print("  [align] scipy unavailable — falling back to greedy assignment")
        pairs, taken = [], set()
        order = sorted(range(len(labels)),
                       key=lambda r: -max(matrix[labels[r]]))
        for r in order:
            best = max((c for c in range(len(current_words)) if c not in taken),
                       key=lambda c: matrix[labels[r]][c], default=None)
            if best is not None:
                taken.add(best)
                pairs.append((r, best))

    mapping, scores = {}, {}
    for r, c in pairs:
        lab = labels[r]
        mapping[c] = lab
        row = sorted(matrix[lab], reverse=True)
        scores[lab] = (matrix[lab][c], row[1] if len(row) > 1 else 0.0)
    return mapping, scores, matrix


def print_alignment(mapping, scores, current_words, taxonomy):
    print("\n  Alignment — stored name → current topic (by word overlap)")
    print("  " + "─" * 74)
    for idx in sorted(mapping):
        lab = mapping[idx]
        best, runner = scores[lab]
        name = taxonomy.get(lab, {}).get('proposed_name', lab)
        moved = '' if lab == f'T{idx + 1}' else f'  ⇠ was {lab}'
        flag = ''
        if best < MIN_OVERLAP:
            flag = f'  ✗ WEAK (<{MIN_OVERLAP})'
        elif best - runner < MIN_MARGIN:
            flag = f'  ✗ AMBIGUOUS (runner-up {runner:.2f})'
        print(f"  T{idx + 1:<2} {name[:46]:<48} {best:.2f}{moved}{flag}")
        print(f"       now: {', '.join(current_words[idx][:8])}")


def emit_signatures(nlp, cls):
    """Print a paste-ready provenance + signature block for the current run."""
    print("\n# ── paste into src/patch_topic_names.py, replacing both blocks ──")
    print("TAXONOMY_PROVENANCE = {")
    print(f"    'run_id':            '<run id from log_pipeline_run.py --list>',")
    print(f"    'equivalence_class': '{cls}',")
    print(f"    'nlp_hash':          '<nlp_hash from log_pipeline_run.py --list>',")
    print(f"    'k':                 {nlp['n_topics']},")
    print(f"    'n_books':           {len(nlp['book_ids'])},")
    print(f"    'validated':         '<YYYY-MM-DD>',")
    print(f"    'rater':             '<who>',")
    print("}")
    print("\nSIGNATURES = {")
    for i in range(nlp['n_topics']):
        print(f"    'T{i + 1}': {nlp['top_words'][i][:12]!r},")
    print("}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[3])
    ap.add_argument('--report', action='store_true',
                    help='show the alignment and exit without writing')
    ap.add_argument('--emit-signatures', action='store_true',
                    help='print a paste-ready provenance + signature block')
    ap.add_argument('--force', action='store_true',
                    help='apply the alignment even if the gate fails (records a warning)')
    ap.add_argument('--min-overlap', type=float, default=MIN_OVERLAP)
    args = ap.parse_args()

    nlp_path = pathlib.Path('json/nlp_results.json')
    if not nlp_path.exists():
        sys.exit(f"ERROR: {nlp_path} not found — run from project root")
    nlp = json.load(open(nlp_path))

    cls = current_equivalence_class(nlp)

    if args.emit_signatures:
        emit_signatures(nlp, cls or '<unavailable>')
        return 0

    n_topics = nlp['n_topics']
    current_words = nlp['top_words']

    print(f"Taxonomy validated against : {TAXONOMY_PROVENANCE['run_id']}  "
          f"(class {TAXONOMY_PROVENANCE['equivalence_class']}, "
          f"{TAXONOMY_PROVENANCE['n_books']} books)")
    print(f"Current run                : class {cls}, "
          f"{len(nlp['book_ids'])} books, k={n_topics}")

    failures = []

    # Gate 1 — k must match, or the taxonomy simply does not describe this run.
    if n_topics != TAXONOMY_PROVENANCE['k']:
        failures.append(
            f"k mismatch: taxonomy is for k={TAXONOMY_PROVENANCE['k']}, "
            f"this run is k={n_topics}")

    # Gate 2 — a changed equivalence class means the corpus or configuration
    # moved, which is exactly when names stop transferring.
    class_changed = cls is not None and cls != TAXONOMY_PROVENANCE['equivalence_class']
    if class_changed:
        failures.append(
            f"equivalence class changed ({TAXONOMY_PROVENANCE['equivalence_class']} "
            f"→ {cls}) — names must be re-validated against this run, not carried over")

    # Gate 3 — content alignment.
    mapping, scores, _matrix = align(SIGNATURES, current_words)
    for idx in sorted(mapping):
        lab = mapping[idx]
        best, runner = scores[lab]
        if best < args.min_overlap:
            failures.append(
                f"{lab} ({TAXONOMY[lab]['proposed_name'][:40]}) matches T{idx + 1} "
                f"at only {best:.2f} — below {args.min_overlap}")
        elif best - runner < MIN_MARGIN:
            failures.append(
                f"{lab} ({TAXONOMY[lab]['proposed_name'][:40]}) is ambiguous: "
                f"best {best:.2f} vs runner-up {runner:.2f}")

    print_alignment(mapping, scores, current_words, TAXONOMY)

    moved = [f"{mapping[i]}→T{i + 1}" for i in sorted(mapping)
             if mapping[i] != f'T{i + 1}']
    if moved:
        print(f"\n  NOTE: {len(moved)} name(s) move position this run: "
              f"{', '.join(moved)}")
        print("  They will be applied along the alignment above, not by position.")

    if failures:
        print("\n" + "═" * 78)
        print("  REFUSING TO APPLY NAMES — the taxonomy does not fit this run")
        print("═" * 78)
        for f in failures:
            print(f"   ✗ {f}")
        print("""
  What to do:
    1. Read the alignment above alongside data/outputs/topic_validation.md and
       the top-loading books per topic. Expect merges and splits, not a tidy
       permutation — that is what happened on 20 September.
    2. Re-validate the names against THIS run. A name is a claim about a
       cluster; if the cluster recombined, the claim needs re-making.
    3. Edit TAXONOMY above, then run --emit-signatures and paste the new
       provenance + signature blocks.
    4. Re-run this script; the gate should pass.

  --force applies the alignment anyway. Only do that if you have just
  confirmed by eye that every name above is on the right topic.""")
        if not args.force:
            return 1
        print("\n  --force given: applying anyway.")

    if args.report:
        print("\n  --report: no files written.")
        return 0

    # ── Apply, following the alignment ───────────────────────────────────────
    ordered_names, ordered_notes = [], []
    for i in range(n_topics):
        lab = mapping.get(i)
        ordered_names.append(TAXONOMY.get(lab, {}).get('proposed_name', f'T{i + 1}'))
        ordered_notes.append(TAXONOMY.get(lab, {}).get('notes', ''))

    target = pathlib.Path('json/topic_validation.json')
    if target.exists():
        data = json.load(open(target))
        topics = data.get('topics', data.get('validation', []))
        if not topics:
            print("WARNING: no topics list in topic_validation.json — skipping it")
        else:
            updated = 0
            for topic in topics:
                label = topic.get('topic_label', '')
                if not label.startswith('T'):
                    continue
                idx = int(label[1:]) - 1
                if 0 <= idx < n_topics:
                    topic['proposed_name'] = ordered_names[idx]
                    topic['notes'] = ordered_notes[idx]
                    updated += 1
                    print(f"  {label} → {ordered_names[idx]}")
            json.dump(data, open(target, 'w'), ensure_ascii=False, indent=2)
            print(f"\nUpdated {updated}/{n_topics} topics in {target}")
    else:
        print(f"WARNING: {target} not found — skipping (run 09c first)")

    # Write into nlp_results.json so the report builders pick up agreed names
    # rather than defaulting to 'Topic 1', 'Topic 2', … . topic_notes is written
    # alongside so 09c_validate_topics.py can overlay both (ROADMAP #27).
    nlp['topic_names'] = ordered_names
    nlp['topic_notes'] = ordered_notes
    json.dump(nlp, open(nlp_path, 'w'), ensure_ascii=False)
    print(f"Updated nlp_results.json topic_names: {ordered_names}")
    print(f"Updated nlp_results.json topic_notes ({len(ordered_notes)} entries)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
