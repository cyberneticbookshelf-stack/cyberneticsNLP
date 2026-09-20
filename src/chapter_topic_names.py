#!/usr/bin/env python3
"""
chapter_topic_names.py
──────────────────────
Single source of truth for **chapter-level NMF** topic names, and the resolver
that attaches them to a run.

WHY THIS MODULE EXISTS (ROADMAP #33, 21 September 2026)
───────────────────────────────────────────────────────
`06_build_report_chapters.py` and `07_build_excel_chapters.py` each did:

    R['topic_names'] = _RB.get('topic_names')   # carry book-level names

which crossed labels between two unrelated models. The book model is **LDA
k=9**; the chapter model is a separate **NMF** fit with its own vocabulary and
no names of its own (k=8 when the bug was found, k=9 since the #35 front-matter
fix — the k is chosen by elbow and moves). So chapter topics were labelled with
book topic names by position —
chapter T2 (*function, state, input, output*) was presented as "Social Systems
and Second-Order Constructivism", and so on. Both scripts also kept their own
divergent `_BASE_NAMES` fallback list, so the two artefacts could disagree.

This is the same class of error as ROADMAP #32, one step worse: #32 mapped a
name to the wrong topic *within* one model; this mapped names *across models*.
It was made visible on 20 September when the book-level residual label landed
on 125 chapters of the people/life/human topic.

Two rules follow, and this module enforces both:

  1. Chapter topics get **chapter names**. Nothing is carried from the book
     model, ever.
  2. Names are matched **by content, not position** — each name carries the top
     words of the topic it was written for, and `resolve()` aligns them against
     the run's actual topics by word overlap.

Failure behaviour differs from `patch_topic_names.py` deliberately. That script
is a gate and refuses to write. This one runs inside report builders, where a
hard failure would abort `run_all.sh` over a labelling problem. So a weak or
ambiguous alignment **degrades to unnamed generic labels with a loud warning**
rather than printing a confident wrong name. An unnamed topic is honest; a
misnamed one is not.
"""

PROVENANCE = {
    'model':      'NMF, chapter-level',
    'k':          9,
    'n_chapters': 6307,
    'run':        'run_20260920_k9_s5 corpus, chapters rebuilt 21 September 2026 '
                  'after the ROADMAP #35 front-matter fix',
    'rater':      'proposed from top words + top-loading books; provisional, '
                  'single-source — not yet reviewed',
}

# Re-derived 21 September 2026. Removing publisher front matter (#35) did not
# just delete a junk topic — it changed the model's shape. The elbow moved from
# k=8 to k=9, and the freed capacity resolved structure that the boilerplate had
# been masking: a distinct **brain / neural** topic and a distinct **information
# theory** topic now exist, neither of which had a counterpart in the k=8 fit.
# Chapter count fell 6,449 → 6,307. The #33 guard caught the k change and fell
# back to unnamed labels until these names were re-derived, which is exactly
# what it is for.

# Ordered as validated. `signature` is the topic's top words at validation time
# and is what resolve() matches on; list order is NOT relied upon.
CHAPTER_TAXONOMY = [
    {
        'name': 'Self, Mind and Everyday Experience',
        'signature': ['people', 'just', 'like', 'time', 'even', 'make', 'might',
                      'many', 'think', 'something', 'much', 'know'],
        'notes': '615 chapters / 201 books. Psycho-Cybernetics and the self-help '
                 'lineage; anecdotal, second-person register.',
    },
    {
        'name': 'Mathematical and Formal Systems',
        'signature': ['function', 'state', 'input', 'system', 'output', 'time',
                      'value', 'equation', 'number', 'values', 'case', 'form'],
        'notes': '834 chapters / 204 books. State equations, formal models, '
                 'quantitative method.',
    },
    {
        'name': 'General Systems Theory',
        'signature': ['systems', 'system', 'theory', 'organization', 'complexity',
                      'self', 'complex', 'social', 'environment', 'systems theory',
                      'processes', 'general'],
        'notes': '783 chapters / 223 books. Luhmann, autopoiesis, complexity.',
    },
    {
        'name': 'Management and Political Economy',
        'signature': ['management', 'economic', 'production', 'development',
                      'decision', 'national', 'growth', 'economy', 'project',
                      'market', 'resources', 'political'],
        'notes': '785 chapters / 204 books. Economic cybernetics, Cybersyn/Allende, '
                 'state planning and development. In the k=8 fit management and '
                 'political economy were a single mixed topic; this is its clearer '
                 'successor.',
    },
    {
        'name': 'Machines, Computing and the Cybernetic Tradition',
        'signature': ['machine', 'computer', 'cybernetics', 'wiener', 'machines',
                      'computers', 'intelligence', 'electronic', 'norbert',
                      'cybernetic', 'norbert wiener', 'artificial'],
        'notes': '605 chapters / 224 books. Machines and computing told through '
                 'the field\'s own lineage — Wiener anchors it.',
    },
    {
        'name': 'Control Theory and Engineering',
        'signature': ['control', 'feedback', 'control system', 'loop', 'system',
                      'controlled', 'control systems', 'behavior', 'error',
                      'reference', 'signal', 'variable'],
        'notes': '477 chapters / 165 books. PCT and control-engineering registers.',
    },
    {
        'name': 'Science, Philosophy and Culture',
        'signature': ['human', 'world', 'science', 'social', 'knowledge', 'nature',
                      'scientific', 'philosophy', 'life', 'cultural', 'history',
                      'reality'],
        'notes': '1,139 chapters / 327 books — the largest, and the widest book '
                 'spread. Epistemology, philosophy of science, cultural theory.',
    },
    {
        'name': 'Brain, Nerve and Neural Systems',
        'signature': ['brain', 'nervous', 'neural', 'nervous system', 'neurons',
                      'activity', 'cells', 'body', 'sensory', 'learning',
                      'network', 'behavior'],
        'notes': '591 chapters / 192 books. NEW at k=9 — no counterpart in the '
                 'k=8 fit, where this material was dispersed. Neurophysiology, '
                 'neural modelling, sensory systems.',
    },
    {
        'name': 'Information Theory and Communication',
        'signature': ['information', 'communication', 'theory', 'information theory',
                      'language', 'entropy', 'message', 'shannon', 'semantic',
                      'meaning', 'channel', 'symbols'],
        'notes': '478 chapters / 204 books. NEW at k=9 — Shannon, entropy, '
                 'semantic communication. Previously folded into the formal and '
                 'theory topics.',
    },
]

MIN_OVERLAP = 0.50
MIN_MARGIN = 0.10


def _jaccard(a, b):
    sa, sb = set(a), set(b)
    return len(sa & sb) / len(sa | sb) if (sa or sb) else 0.0


def resolve(top_words, n_topics, verbose=True):
    """Return a list of `n_topics` names aligned to `top_words` by content.

    Degrades to generic 'T<n> (unnamed)' labels, with a warning, when the
    alignment is weak or ambiguous — never guesses a confident wrong name.
    """
    generic = [f'T{i + 1} (unnamed)' for i in range(n_topics)]

    if n_topics != PROVENANCE['k']:
        if verbose:
            print(f"  [chapter-names] k mismatch: taxonomy is for "
                  f"k={PROVENANCE['k']}, this run is k={n_topics} — "
                  f"falling back to unnamed labels")
        return generic

    matrix = [[_jaccard(entry['signature'], tw) for tw in top_words]
              for entry in CHAPTER_TAXONOMY]

    try:
        from scipy.optimize import linear_sum_assignment
        import numpy as np
        rows, cols = linear_sum_assignment(-np.array(matrix))
        pairs = list(zip(rows, cols))
    except ImportError:                                # pragma: no cover
        pairs, taken = [], set()
        for r in sorted(range(len(matrix)), key=lambda r: -max(matrix[r])):
            best = max((c for c in range(n_topics) if c not in taken),
                       key=lambda c: matrix[r][c], default=None)
            if best is not None:
                taken.add(best)
                pairs.append((r, best))

    names = list(generic)
    problems = []
    for r, c in pairs:
        score = matrix[r][c]
        runner = max([matrix[r][j] for j in range(n_topics) if j != c] or [0.0])
        entry = CHAPTER_TAXONOMY[r]
        if score < MIN_OVERLAP:
            problems.append(f"{entry['name'][:44]!r} best match T{c + 1} "
                            f"only {score:.2f}")
        elif score - runner < MIN_MARGIN:
            problems.append(f"{entry['name'][:44]!r} ambiguous: T{c + 1} "
                            f"{score:.2f} vs runner-up {runner:.2f}")
        else:
            names[c] = entry['name']

    if problems:
        if verbose:
            print("  [chapter-names] ⚠ alignment failed — the chapter topics have "
                  "moved since these names were written.")
            for p in problems:
                print(f"      {p}")
            print("      Affected topics fall back to unnamed labels. Re-validate "
                  "against the current chapter model and update "
                  "src/chapter_topic_names.py (ROADMAP #33).")
    elif verbose:
        print(f"  [chapter-names] {len(pairs)}/{n_topics} chapter topics matched "
              f"by content ✓")
    return names


def is_artefact(name):
    """True if `name` is a labelled artefact rather than an interpretable topic."""
    return any(e.get('artefact') and e['name'] == name for e in CHAPTER_TAXONOMY)


if __name__ == '__main__':
    import json
    import pathlib
    R = json.load(open(pathlib.Path('json/nlp_results_chapters.json')))
    for i, nm in enumerate(resolve(R['top_words'], R['n_topics'])):
        print(f"  T{i + 1}  {nm}")
        print(f"       {', '.join(R['top_words'][i][:10])}")
