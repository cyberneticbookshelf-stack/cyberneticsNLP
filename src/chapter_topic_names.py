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
k=9**; the chapter model is **NMF k=8** with its own vocabulary and no names of
its own. So chapter topics were labelled with book topic names by position —
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
    'k':          8,
    'n_chapters': 6449,
    'run':        'run_20260920_k9_s5 (20 September 2026, 575-book corpus)',
    'rater':      'proposed from top words + top-loading books; provisional, '
                  'single-source — not yet reviewed',
}

# Ordered as validated. `signature` is the topic's top words at validation time
# and is what resolve() matches on; list order is NOT relied upon.
CHAPTER_TAXONOMY = [
    {
        'name': 'Self, Mind and Everyday Experience',
        'signature': ['people', 'life', 'human', 'even', 'like', 'world', 'just',
                      'something', 'mind', 'might', 'much', 'self'],
        'notes': '953 chapters / 281 books. Psycho-Cybernetics and the self-help '
                 'lineage, popular and anecdotal registers.',
    },
    {
        'name': 'Mathematical and Formal Systems',
        'signature': ['function', 'state', 'system', 'input', 'time', 'output',
                      'value', 'number', 'equation', 'values', 'rate', 'case'],
        'notes': '1,101 chapters / 245 books. Formal models, state equations, '
                 'quantitative method.',
    },
    {
        'name': 'General Systems Theory',
        'signature': ['systems', 'system', 'organization', 'environment',
                      'complexity', 'complex', 'model', 'processes', 'self',
                      'structure', 'social', 'different'],
        'notes': '927 chapters / 247 books. Luhmann, autopoiesis, viable-systems '
                 'and complexity registers.',
    },
    {
        'name': 'Machines, Computers and Artificial Intelligence',
        'signature': ['machine', 'computer', 'brain', 'machines', 'human',
                      'intelligence', 'artificial', 'computers', 'neural',
                      'digital', 'artificial intelligence', 'nervous'],
        'notes': '603 chapters / 212 books. Previously unnamed — the old '
                 '_BASE_NAMES list called this "History & Philosophy of '
                 'Cybernetics", which belongs to the theory topic instead.',
    },
    {
        'name': 'History and Philosophy of Cybernetics',
        'signature': ['theory', 'science', 'wiener', 'scientific', 'cybernetics',
                      'philosophy', 'sciences', 'knowledge', 'social',
                      'communication', 'general', 'theories'],
        'notes': '938 chapters / 314 books — the widest book spread. Soviet and '
                 'institutional histories, philosophy of the field.',
    },
    {
        'name': 'Control Theory and Engineering',
        'signature': ['control', 'feedback', 'loop', 'control system',
                      'control systems', 'behavior', 'system', 'controlled',
                      'systems', 'error', 'signal', 'controlling'],
        'notes': '581 chapters / 193 books. PCT and control-engineering registers.',
    },
    {
        'name': 'Political Economy, Technology and Development',
        'signature': ['economic', 'political', 'technology', 'social',
                      'management', 'production', 'work', 'research',
                      'development', 'national', 'technological', 'society'],
        'notes': '1,049 chapters / 274 books. Previously unnamed ("Topic 7"). '
                 'Economic cybernetics, Allende/Cybersyn, state and development.',
    },
    {
        'name': '⚠ Front-matter artefact — not a topic',
        'signature': ['part', 'electronic', 'minor', 'retrieval',
                      'minor sections', 'sections', 'permission', 'information',
                      'rights', 'storage', 'reproduced', 'recording'],
        'artefact': True,
        'notes': '297 chapters / 225 books. Publisher copyright boilerplate ("no '
                 'part of this publication may be reproduced … retrieval system '
                 '… without permission") that survived cleaning into the chapter '
                 'segmentation path. One of eight chapter topics is spent on it. '
                 'Labelled explicitly so readers are not invited to interpret it. '
                 'Upstream fix (cleaning/segmentation) is ROADMAP #35.',
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
