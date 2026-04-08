"""
heuristic_features.py  v2
──────────────────────────
Structural heuristics from books_clean.json clean text.
Each heuristic is binary (0/1). Treat as weak signals — no single
one is definitive. Calibrated from audit of actual clean text (April 2026).

Changes from v1:
- h_edited_by: tightened — requires person name after "Edited by"
- h_has_contributors: split into anthology-specific section headings only
- h_single_author_bio: now uses "About the Author" (singular) as monograph signal
- h_chapter_summaries: loosened to match "Publisher Summary" not on own line
- h_essays_front: verified working
"""
import re

# ── Anthology signals ──────────────────────────────────────────────────────────

# Multiple institutional affiliations in front matter
AFFILIATION_RE = re.compile(
    r'(?:Department|Faculty|School|Institute|Centre|Center|Division)\s+of\s+'
    r'[A-Z][^,\n]{3,50},\s*'
    r'(?:University|Universit[äáéy]|Institute|College|Academy)\s+of\s+[A-Z]',
    re.IGNORECASE
)

# Recurring chapter abstracts — "Publisher Summary" or standalone "SUMMARY"
# Loosened: Publisher Summary need not be on its own line
CHAPTER_SUMMARY_RE = re.compile(
    r'Publisher\s+Summary|^\s*SUMMARY\s*$',
    re.MULTILINE | re.IGNORECASE
)

# Per-chapter reference lists
REFERENCES_RE = re.compile(r'^\s*References\s*$', re.MULTILINE | re.IGNORECASE)

# Section headings specific to anthologies
# "About the Authors" (plural) or "About the Editors" → anthology
# "Contributors", "Notes on Contributors", "List of Contributors" → anthology
# Does NOT match "About the Author" (singular) — that's a monograph signal
CONTRIBUTORS_SECTION_RE = re.compile(
    r'(?:^|\n)\s*(?:'
    r'Contributors|List\s+of\s+Contributors|Notes\s+on\s+Contributors|'
    r'About\s+the\s+(?:Authors|Editors)'  # plural Authors or Editors
    r')\s*(?:\n|$)',
    re.IGNORECASE
)

# "Edited by" or "Eds."/"Ed." suffix after editor names
EDITED_BY_RE = re.compile(
    r'\bEdited\s+by\s+[A-Z][a-z]+(?:\.?\s+[A-Z][a-z]+)+'  # "Edited by Name"
    r'|(?:[A-Z][a-z]+\s+){1,}Eds?\.',                          # "Name(s) Eds."
)

# "essays" framing in front matter → collected works / anthology
ESSAYS_RE = re.compile(
    r'\b(?:contains?|comprising|collection\s+of|brings?\s+together|'
    r'gathers?|assembles?)\s+(?:\w+\s+){0,4}essays?\b',
    re.IGNORECASE
)

# ── Monograph signals ──────────────────────────────────────────────────────────

# Cross-chapter references — sustained argument across chapters
CROSS_CHAPTER_RE = re.compile(
    r'\b(?:in|see|as\s+(?:shown|argued|discussed|demonstrated|established)\s+in|'
    r'return(?:s|ing)?\s+to|introduced\s+in|developed\s+in|'
    r'as\s+we\s+(?:showed|argued|saw|noted)\s+in|'
    r'discussed\s+(?:further\s+)?in)\s+[Cc]hapter\s+\d+',
    re.IGNORECASE
)

# "About the Author" (singular) — monograph signal
SINGLE_AUTHOR_BIO_RE = re.compile(
    r'(?:^|\n)\s*About\s+the\s+Author\s*(?:\n|$)',
    re.IGNORECASE
)

# ── Textbook signals ───────────────────────────────────────────────────────────

EXERCISE_RE = re.compile(
    r'^\s*(?:Exercises?|Problems?|Review\s+Questions?|'
    r'Discussion\s+Questions?|Problem\s+Set|Self[- ]Test)\s*$',
    re.MULTILINE | re.IGNORECASE
)

OBJECTIVES_RE = re.compile(
    r'\b(?:Learning\s+Objectives?|By\s+the\s+end\s+of\s+this\s+chapter|'
    r'After\s+(?:reading|completing|studying)\s+this\s+chapter|'
    r'Chapter\s+Objectives?)\b',
    re.IGNORECASE
)


def extract_heuristics(text):
    """
    Extract structural heuristics from clean book text.
    Returns dict of binary float features (0.0 or 1.0).
    """
    if not text:
        return {k: 0.0 for k in [
            'h_multi_affiliations', 'h_chapter_summaries',
            'h_cross_chapter_refs', 'h_has_exercises',
            'h_has_objectives', 'h_essays_front',
            'h_per_chapter_refs', 'h_contributors_section',
            'h_edited_by', 'h_single_author_bio',
        ]}

    n = len(text)
    front = text[:max(1, int(n * 0.20))]   # first 20% — TOC, preface, author info
    body  = text[max(0, int(n * 0.10)):]   # skip first 10% front matter noise

    return {
        # Anthology signals (→ not-monograph)
        'h_multi_affiliations':   float(len(AFFILIATION_RE.findall(front)) >= 2),
        'h_chapter_summaries':    float(len(CHAPTER_SUMMARY_RE.findall(body)) >= 3),
        'h_per_chapter_refs':     float(len(REFERENCES_RE.findall(body)) >= 3),
        'h_contributors_section': float(bool(CONTRIBUTORS_SECTION_RE.search(front))),
        'h_edited_by':            float(bool(EDITED_BY_RE.search(front))),
        # "essays" only signals anthology when combined with multiple authors or editor
        # "essays" alone often means single-author collected works (still a monograph)
        'h_essays_front':         float(
            bool(ESSAYS_RE.search(front)) and (
                bool(EDITED_BY_RE.search(front)) or
                len(AFFILIATION_RE.findall(front)) >= 2 or
                bool(CONTRIBUTORS_SECTION_RE.search(front))
            )
        ),
        # Monograph signals (→ monograph)
        'h_cross_chapter_refs':   float(len(CROSS_CHAPTER_RE.findall(body)) >= 3),
        'h_single_author_bio':    float(bool(SINGLE_AUTHOR_BIO_RE.search(front))),
        # Textbook signals (→ not-monograph for binary classifier)
        'h_has_exercises':        float(bool(EXERCISE_RE.search(body))),
        'h_has_objectives':       float(bool(OBJECTIVES_RE.search(body))),
    }


if __name__ == '__main__':
    """Audit heuristics on known books."""
    import json, pathlib, sys

    path = pathlib.Path('json/books_clean.json')
    if not path.exists():
        sys.exit("Run from project root")

    KNOWN = {
        '1435': 'anthology',
        '1204': 'anthology',
        '765':  'anthology',
        '389':  'monograph',
        '743':  'monograph',
        '1661': 'monograph',
        '368':  'monograph',
        '762':  'monograph',
        '257':  'monograph',
        '1260': 'monograph',
    }

    # Also add the review sample disagreements
    KNOWN.update({
        '1231': 'anthology',  # predicted mono, expert says anthology
        '1725': 'monograph',  # predicted not-mono, expert says mono
        '445':  'monograph',  # predicted not-mono, expert says mono
        '259':  'monograph',  # predicted not-mono, expert says mono
        '1204': 'anthology',  # confirmed anthology
    })

    books = json.load(open(path))

    print(f"\n{'ID':>5}  {'Expert':>10}  "
          f"{'maff':>4} {'chsum':>5} {'xchap':>5} "
          f"{'exer':>4} {'edit':>4} {'contrib':>7} "
          f"{'bio1':>4} {'essay':>5}  title")
    print("-" * 95)

    correct = 0
    total = 0
    for bid, label in sorted(KNOWN.items()):
        b = books.get(bid, {})
        text = b.get('clean_text', '')
        h = extract_heuristics(text)
        title = b.get('title', '')[:28]

        # Simple majority vote: anthology signals > monograph signals → not-mono
        anthology_score = (h['h_multi_affiliations'] + h['h_chapter_summaries'] +
                          h['h_per_chapter_refs'] + h['h_contributors_section'] +
                          h['h_edited_by'] + h['h_essays_front'])
        monograph_score = h['h_cross_chapter_refs'] + h['h_single_author_bio']
        predicted = 'monograph' if monograph_score >= anthology_score else 'not-mono'
        expert_mono = 'monograph' if label == 'monograph' else 'not-mono'
        agrees = predicted == expert_mono
        if agrees: correct += 1
        total += 1
        flag = '✓' if agrees else '✗'

        print(f"{flag} {bid:>4}  {label:>10}  "
              f"{'Y' if h['h_multi_affiliations'] else '.':>4} "
              f"{'Y' if h['h_chapter_summaries'] else '.':>5} "
              f"{'Y' if h['h_cross_chapter_refs'] else '.':>5} "
              f"{'Y' if h['h_has_exercises'] else '.':>4} "
              f"{'Y' if h['h_edited_by'] else '.':>4} "
              f"{'Y' if h['h_contributors_section'] else '.':>7} "
              f"{'Y' if h['h_single_author_bio'] else '.':>4} "
              f"{'Y' if h['h_essays_front'] else '.':>5}  "
              f"{title}")

    print(f"\nSimple majority vote agreement: {correct}/{total} = {100*correct/total:.0f}%")
    print("(These are heuristics only — classifier uses logistic regression weighting)")
