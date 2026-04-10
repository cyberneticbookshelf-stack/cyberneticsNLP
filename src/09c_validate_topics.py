"""
09c_validate_topics.py
─────────────────────────────────────────────────────────────────────────────
Topic validation via triangulation: stability scores, LDA top words, and
high-loading book titles. Run after 03_nlp_pipeline.py (with --seeds).

Produces a structured console report and saves topic_validation.json.

Usage:
    python3 src/09c_validate_topics.py                    # default top 10 books
    python3 src/09c_validate_topics.py --top 15           # top 15 books per topic
    python3 src/09c_validate_topics.py --md               # also write markdown report

Methodology note (for paper):
    LDA top words reflect vocabulary frequency, not intellectual coherence.
    Books with specialised or non-standard vocabulary (self-help, critical
    theory, engineering) produce misleading word signals. Title verification
    corrects this. The triangulation loop (words → stability → titles) is
    the primary validation method for this corpus.

Output:
    json/topic_validation.json   — structured validation data
    docs/topic_validation.md     — human-readable report (--md flag)
"""

# ── Directory layout ──────────────────────────────────────────────────────────
import pathlib as _pl
JSON_DIR = _pl.Path('json')
DOCS_DIR = _pl.Path('docs')
JSON_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)

import json, sys, re
from datetime import date

# ── CLI flags ─────────────────────────────────────────────────────────────────
TOP_N   = 10
WRITE_MD = '--md' in sys.argv
if '--top' in sys.argv:
    try:
        TOP_N = int(sys.argv[sys.argv.index('--top') + 1])
    except (IndexError, ValueError):
        print('  [--top] usage: --top N  (integer)')

# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading data...")

try:
    results = json.load(open(str(JSON_DIR / 'nlp_results.json')))
except FileNotFoundError:
    print("ERROR: json/nlp_results.json not found. Run 03_nlp_pipeline.py first.")
    sys.exit(1)

try:
    books = json.load(open(str(JSON_DIR / 'books_clean.json')))
except FileNotFoundError:
    print("ERROR: json/books_clean.json not found.")
    sys.exit(1)

# Stability data (optional — graceful degradation if --seeds wasn't used)
stability_scores  = None
canonical_words   = None
mean_stability    = None
try:
    stab = json.load(open(str(JSON_DIR / 'topic_stability.json')))
    stability_scores = stab['stability_scores']
    canonical_words  = stab['canonical_words']
    mean_stability   = stab['mean_stability']
    n_seeds          = stab['n_seeds']
    print(f"  Stability data: {n_seeds}-seed run loaded")
except FileNotFoundError:
    print("  WARNING: topic_stability.json not found — stability scores unavailable")
    print("  Re-run 03_nlp_pipeline.py with --seeds 5 to enable stability analysis")

n_topics  = results['n_topics']
book_ids  = results['book_ids']
doc_topic = results['doc_topic']
top_words = results['top_words']   # from LDA, n_top=12

print(f"  n_topics={n_topics}, corpus={len(book_ids)} books")

# ── Helpers ───────────────────────────────────────────────────────────────────

def stability_label(score):
    if score is None:    return 'n/a'
    if score >= 0.3:     return 'stable'
    if score >= 0.15:    return 'moderate'
    return 'unstable'

def stability_bar(score, width=20):
    if score is None: return '?' * 3
    return '█' * int(score * width)

def dead_topic(loading):
    """True if topic loading is degenerate — all top books near zero."""
    top_scores = [s for _, s in loading[:10]]
    return max(top_scores) < 0.05 or (
        sum(1 for s in top_scores if s < 0.01) >= 8
    )

# ── Per-topic analysis ────────────────────────────────────────────────────────

print(f"\nValidating {n_topics} topics (top {TOP_N} books each)...\n")

SEP  = "─" * 80
SEP2 = "═" * 80

validation = []

for t in range(n_topics):
    # Book loadings
    loading = [(book_ids[i], doc_topic[i][t]) for i in range(len(book_ids))]
    loading.sort(key=lambda x: x[1], reverse=True)
    top_books = [(bid, score) for bid, score in loading[:TOP_N]]

    # Stability
    score = stability_scores[t] if stability_scores else None
    label = stability_label(score)
    bar   = stability_bar(score)

    # Words — prefer canonical (from stability run) over LDA top_words
    if canonical_words:
        words = canonical_words[t][:8]
    else:
        words = top_words[t][:8] if t < len(top_words) else []

    # Dead topic detection
    is_dead = dead_topic(loading)

    # Console output
    score_str = f"{score:.3f}" if score is not None else "  n/a"
    flag = ' ⚠ DEAD — degenerate loadings' if is_dead else ''
    print(SEP)
    print(f"T{t+1:<3}  stability={score_str}  {bar:<22}  [{label}]{flag}")
    print(f"     words: {', '.join(words)}")
    print(f"     top {TOP_N} books:")
    for bid, s in top_books:
        b = books.get(bid, {})
        title  = b.get('title', '?')[:55]
        author = b.get('author', '?')[:25]
        year   = b.get('pubdate', '')
        print(f"       {s:.3f}  [{bid}] {title:55s} {year}")

    validation.append({
        'topic_index':     t,
        'topic_label':     f'T{t+1}',
        'stability_score': score,
        'stability_label': label,
        'is_dead':         is_dead,
        'top_words':       words,
        'top_books':       [
            {
                'book_id': bid,
                'score':   round(s, 4),
                'title':   books.get(bid, {}).get('title', '?'),
                'author':  books.get(bid, {}).get('author', '?'),
                'year':    books.get(bid, {}).get('pubdate', ''),
            }
            for bid, s in top_books
        ],
        'proposed_name':   '',   # to be filled in manually or via --name-topics
        'notes':           '',
        'status':          'dead' if is_dead else label,
    })

# ── Summary ───────────────────────────────────────────────────────────────────
print(SEP2)
print(f"\nSUMMARY  k={n_topics}  corpus={len(book_ids)} books  date={date.today()}")
if mean_stability is not None:
    print(f"Mean stability: {mean_stability:.3f}")
n_dead     = sum(1 for v in validation if v['is_dead'])
n_stable   = sum(1 for v in validation if v['stability_label'] == 'stable' and not v['is_dead'])
n_moderate = sum(1 for v in validation if v['stability_label'] == 'moderate' and not v['is_dead'])
n_unstable = sum(1 for v in validation if v['stability_label'] == 'unstable' and not v['is_dead'])
print(f"Dead topics:     {n_dead}/{n_topics}")
print(f"Stable   (≥0.3): {n_stable}/{n_topics}")
print(f"Moderate (0.15–0.3): {n_moderate}/{n_topics}")
print(f"Unstable (<0.15):    {n_unstable}/{n_topics}")

if n_dead > 0:
    print(f"\n⚠  {n_dead} dead topic(s) detected — k={n_topics} may be too high.")
    print(f"   Consider re-running with --topics {n_topics - n_dead}")

# ── Save JSON ─────────────────────────────────────────────────────────────────
out = {
    'date':           str(date.today()),
    'n_topics':       n_topics,
    'n_books':        len(book_ids),
    'top_n_books':    TOP_N,
    'mean_stability': mean_stability,
    'n_dead':         n_dead,
    'n_stable':       n_stable,
    'n_moderate':     n_moderate,
    'n_unstable':     n_unstable,
    'topics':         validation,
}
out_path = str(JSON_DIR / 'topic_validation.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\nSaved {out_path}")

# ── Markdown report (--md) ────────────────────────────────────────────────────
if WRITE_MD:
    md_path = str(DOCS_DIR / 'topic_validation.md')
    lines = [
        f"# Topic Validation Report",
        f"",
        f"**Date:** {date.today()}  ",
        f"**k:** {n_topics}  ",
        f"**Corpus:** {len(book_ids)} books  ",
        f"**Method:** LDA top words + 5-seed stability (Hungarian alignment) + title verification  ",
        f"",
        f"## Summary",
        f"",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Mean stability | {str(round(mean_stability, 3)) if mean_stability is not None else 'n/a'} |",
        f"| Dead topics | {n_dead}/{n_topics} |",
        f"| Stable (≥0.3) | {n_stable}/{n_topics} |",
        f"| Moderate (0.15–0.3) | {n_moderate}/{n_topics} |",
        f"| Unstable (<0.15) | {n_unstable}/{n_topics} |",
        f"",
        f"## Topics",
        f"",
    ]
    for v in validation:
        score_str = f"{v['stability_score']:.3f}" if v['stability_score'] is not None else "n/a"
        flag = " — ⚠ DEAD" if v['is_dead'] else ""
        lines += [
            f"### {v['topic_label']}  stability={score_str}  [{v['stability_label']}]{flag}",
            f"",
            f"**Top words:** {', '.join(v['top_words'])}  ",
            f"**Proposed name:** {v['proposed_name'] or '*(to be named)*'}  ",
            f"**Notes:** {v['notes'] or '—'}  ",
            f"",
            f"| Score | ID | Title | Year |",
            f"|---|---|---|---|",
        ]
        for b in v['top_books']:
            lines.append(
                f"| {b['score']:.3f} | {b['book_id']} | {b['title'][:55]} | {b['year']} |"
            )
        lines.append("")

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"Saved {md_path}")

print("\nDone. Edit 'proposed_name' and 'notes' fields in topic_validation.json")
print("to record your taxonomy decisions before running --name-topics.")
