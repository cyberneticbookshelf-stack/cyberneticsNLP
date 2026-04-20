"""
check_stale_vars.py
───────────────────
Checks that hardcoded fallback variables across pipeline scripts are
consistent with the most recent completed run.

Ground truth (read-only):
    json/nlp_results.json  — topic_names, n_topics, book_ids

Usage (from project root):
    python3 src/check_stale_vars.py           # report only
    python3 src/check_stale_vars.py --fix     # report + auto-update stale _LDA_BASE lists

Checks performed:
    1. _LDA_BASE fallback list in each pipeline script — compared to topic_names
    2. TAXONOMY proposed_name entries in patch_topic_names.py — cross-consistency check
    3. Hardcoded corpus-count literals in 06_build_report.py — flagged for manual fix

Variables intentionally skipped:
    _BASE_CH  (08_build_timeseries.py)  — chapter-level NMF model, different source
    _NMF_BASE (12_index_grounding.py)   — chapter-level NMF model, different source

Notes:
    - patch_topic_names.py TAXONOMY is the authoritative source; the checker will
      cross-verify it against nlp_results.json but will NOT auto-fix it.
    - _LDA_BASE in all scripts is a fallback only (used when nlp_results.json lacks
      topic_names). Keeping it current ensures safe fallback after a fresh pipeline run
      before patch_topic_names.py is applied.
    - Use str-level line-scanning (not re.sub) to avoid backslash-mangling of string
      literals in source files.
"""

import json, pathlib, sys, argparse, re, os

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT     = pathlib.Path('.')
JSON_DIR = ROOT / 'json'
SRC_DIR  = ROOT / 'src'

# Scripts carrying _LDA_BASE — in run order
LDA_BASE_SCRIPTS = [
    '06_build_report.py',
    '08_build_timeseries.py',
    '09b_build_index_analysis.py',
    '10_build_index_report.py',
    '11_embedding_comparison.py',
    '12_index_grounding.py',
    '13_weighted_comparison.py',
    '14_entity_network.py',
]

# Hardcoded corpus-count patterns to flag (script, search_string, note)
COUNT_PATTERNS = [
    ('06_build_report.py',
     '542 \u00d7 542, no labels',
     'option value in cosine mode selector — make dynamic with {len(book_ids)}'),
    ('06_build_report.py',
     'all 542 \u00d7 542 book pairs',
     'fig-caption text — make dynamic with {len(book_ids)}'),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_canonical():
    """Load ground truth from nlp_results.json. Returns dict with keys:
       topic_names (list[str]), n_topics (int), n_books (int)."""
    p = JSON_DIR / 'nlp_results.json'
    if not p.exists():
        sys.exit(f'ERROR: {p} not found — run from project root')
    R = json.loads(p.read_text(encoding='utf-8'))
    names = R.get('topic_names')
    if not names:
        sys.exit('ERROR: nlp_results.json has no topic_names key — run patch_topic_names.py first')
    return {
        'topic_names': names,
        'n_topics':    R['n_topics'],
        'n_books':     len(R['book_ids']),
    }


def extract_lda_base(path):
    """Parse _LDA_BASE list from a source file.
    Returns (names: list[str], start_line: int, end_line: int) or None if not found.
    Line numbers are 0-indexed."""
    lines = path.read_text(encoding='utf-8').splitlines()
    for i, line in enumerate(lines):
        if line.rstrip() == '_LDA_BASE = [':
            names = []
            j = i + 1
            while j < len(lines):
                stripped = lines[j].strip()
                if stripped == ']':
                    return names, i, j
                # Extract string value from lines like:  '  ''Some Name'',\n'
                m = re.match(r"^\s*'([^']+)',?\s*$", lines[j])
                if m:
                    names.append(m.group(1))
                j += 1
    return None


def replace_lda_base(text, new_names):
    """Replace the _LDA_BASE = [...] block in source text using line-scanning.
    Returns (new_text: str, changed: bool)."""
    lines = text.splitlines(keepends=True)
    out = []
    i = 0
    replaced = False
    while i < len(lines):
        line = lines[i]
        if line.rstrip() == '_LDA_BASE = [':
            # Write new block
            out.append('_LDA_BASE = [\n')
            for name in new_names:
                out.append(f"    '{name}',\n")
            out.append(']\n')
            # Skip old block (find closing ])
            i += 1
            while i < len(lines):
                if lines[i].rstrip() == ']':
                    i += 1
                    break
                i += 1
            replaced = True
        else:
            out.append(line)
            i += 1
    return ''.join(out), replaced


def write_script(path, new_text):
    """Write updated source file. Uses direct write (src files are small)."""
    path.write_text(new_text, encoding='utf-8')


def extract_taxonomy_names(path):
    """Parse proposed_name values from TAXONOMY dict in patch_topic_names.py.
    Returns list[str] in T1..T9 order."""
    text = path.read_text(encoding='utf-8')
    return re.findall(r"'proposed_name':\s*'([^']+)'", text)


# ── Check functions ───────────────────────────────────────────────────────────

def check_lda_base(canonical, fix=False):
    """Check (and optionally fix) _LDA_BASE in all pipeline scripts."""
    canon_names = canonical['topic_names']
    n_canon = len(canon_names)
    results = []

    print(f"\n[1/3] Checking _LDA_BASE in pipeline scripts")
    print(f"      Canonical: {n_canon} topics from nlp_results.json")
    print('      ' + '─' * 60)

    n_ok = n_stale = n_missing = 0

    for fname in LDA_BASE_SCRIPTS:
        path = SRC_DIR / fname
        if not path.exists():
            print(f'  {fname:<40s}  –  file not found (skipped)')
            n_missing += 1
            continue

        result = extract_lda_base(path)
        if result is None:
            print(f'  {fname:<40s}  –  no _LDA_BASE found (skipped)')
            n_missing += 1
            continue

        found_names, start, end = result
        match_count = sum(1 for a, b in zip(found_names, canon_names) if a == b)
        is_current = (found_names == canon_names)

        if is_current:
            print(f'  {fname:<40s}  ✓  current ({n_canon}/{n_canon} match)')
            n_ok += 1
        else:
            print(f'  {fname:<40s}  ✗  STALE  ({match_count}/{n_canon} match, '
                  f'{len(found_names)} entries found)')
            # Show first mismatch
            for idx, (got, want) in enumerate(zip(found_names, canon_names)):
                if got != want:
                    print(f'      T{idx+1}: found    "{got}"')
                    print(f'           expected "{want}"')
                    break
            if len(found_names) != n_canon:
                print(f'      ⚠  list length mismatch: found {len(found_names)}, '
                      f'expected {n_canon}')
            n_stale += 1

            if fix:
                text = path.read_text(encoding='utf-8')
                new_text, changed = replace_lda_base(text, canon_names)
                if changed:
                    write_script(path, new_text)
                    print(f'      → FIXED ✓')
                else:
                    print(f'      → fix attempted but no change made (check manually)')

        results.append({'file': fname, 'status': 'ok' if is_current else 'stale',
                        'found': found_names, 'expected': canon_names})

    print()
    print(f'      Result: {n_ok} current, {n_stale} stale, {n_missing} skipped')
    return results


def check_taxonomy(canonical):
    """Cross-verify TAXONOMY in patch_topic_names.py against nlp_results.json."""
    print(f"\n[2/3] Cross-checking TAXONOMY in patch_topic_names.py")
    print('      ' + '─' * 60)

    path = SRC_DIR / 'patch_topic_names.py'
    if not path.exists():
        print('      patch_topic_names.py not found — skipped')
        return

    taxonomy_names = extract_taxonomy_names(path)
    canon_names    = canonical['topic_names']

    if taxonomy_names == canon_names:
        print(f'  patch_topic_names.py TAXONOMY        ✓  consistent '
              f'({len(canon_names)}/{len(canon_names)} match nlp_results.json)')
    else:
        print(f'  patch_topic_names.py TAXONOMY        ⚠  MISMATCH '
              f'({len(taxonomy_names)} entries vs {len(canon_names)} in nlp_results.json)')
        print()
        print('      TAXONOMY proposed_names:')
        for i, name in enumerate(taxonomy_names):
            flag = '' if i < len(canon_names) and name == canon_names[i] else '  ← differs'
            print(f'        T{i+1}: "{name}"{flag}')
        print('      nlp_results.json topic_names:')
        for i, name in enumerate(canon_names):
            print(f'        [{i}]: "{name}"')
        print()
        print('      NOTE: TAXONOMY is the authoritative source. If nlp_results.json')
        print('      disagrees, re-run patch_topic_names.py to re-apply the taxonomy.')
    print()


def check_corpus_counts(canonical):
    """Flag hardcoded corpus-count literals in HTML template scripts."""
    print(f"\n[3/3] Checking hardcoded corpus-count literals")
    print(f"      Actual n_books analysed: {canonical['n_books']}")
    print('      ' + '─' * 60)

    n_warned = 0
    for fname, pattern, note in COUNT_PATTERNS:
        path = SRC_DIR / fname
        if not path.exists():
            continue
        text = path.read_text(encoding='utf-8')
        lines = text.splitlines()
        for lineno, line in enumerate(lines, 1):
            if pattern in line:
                print(f'  {fname}:{lineno:<6}  ⚠  found "{pattern}"')
                print(f'             actual n_books={canonical["n_books"]} '
                      f'→ {note}')
                n_warned += 1

    if n_warned == 0:
        print('  No hardcoded corpus-count literals found  ✓')
    else:
        print()
        print('  NOTE: these are in f-string HTML templates and require a manual fix.')
        print('  Replace the literal "542" with a dynamic {len(book_ids)} expression.')
    print()


# ── Summary ───────────────────────────────────────────────────────────────────

def print_summary(lda_results, fix):
    n_stale  = sum(1 for r in lda_results if r['status'] == 'stale')
    n_ok     = sum(1 for r in lda_results if r['status'] == 'ok')
    n_skip   = len(LDA_BASE_SCRIPTS) - len(lda_results)

    print('═' * 62)
    if fix and n_stale > 0:
        print(f'  Fixed:   {n_stale} script(s) updated')
        print(f'  Already current: {n_ok}  |  Skipped: {n_skip}')
    elif n_stale > 0:
        print(f'  {n_stale} stale script(s) found — re-run with --fix to update')
        print(f'  Current: {n_ok}  |  Skipped: {n_skip}')
    else:
        print(f'  All _LDA_BASE lists are current  ✓  ({n_ok} scripts)')
    print('═' * 62)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Check (and optionally fix) stale hardcoded variables across pipeline scripts.')
    parser.add_argument('--fix', action='store_true',
                        help='Update stale _LDA_BASE lists in-place (dry-run without this flag)')
    args = parser.parse_args()

    print()
    print('═' * 62)
    print('  check_stale_vars.py  —  CyberneticsNLP pipeline')
    print(f'  Mode: {"FIX" if args.fix else "report only (pass --fix to update)"}')
    print('═' * 62)

    canonical = load_canonical()
    print(f'\n  Ground truth: json/nlp_results.json')
    print(f'  Canonical topic names : {canonical["n_topics"]}')
    print(f'  Books analysed        : {canonical["n_books"]}')
    print(f'  Topic names           : {canonical["topic_names"]}')

    lda_results = check_lda_base(canonical, fix=args.fix)
    check_taxonomy(canonical)
    check_corpus_counts(canonical)
    print_summary(lda_results, fix=args.fix)
    print()


if __name__ == '__main__':
    main()
