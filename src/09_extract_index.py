"""


Extract index terms from all books, save to index_terms.json.
Structure: {book_id: {"terms": [...], "status": "ok"|"no_index"|"truncated"|"garbled"}}

Data-quality fixes (v0.4.1):
  - alpha_ratio threshold raised 0.45 → 0.60; hyphens and parentheses
    explicitly permitted so terms like 'feedback (negative)' are not rejected.
  - Foreign-language section headers (Bibliographie, Sachregister, Índice, etc.)
    now filtered before the main entry path.
  - All stored terms pass through _canonical_term(): single-word terms are
    title-cased, multi-word phrases lowercased, preserving genuine title-case
    proper nouns. Deduplication now operates on canonical forms so
    'Cybernetics', 'cybernetics', 'CYBERNETICS' all resolve to 'Cybernetics'.
"""
# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_lang.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


import csv, re, glob, json
csv.field_size_limit(10_000_000)

INDEX_START = re.compile(
    r'(?im)^[\s]*(?:general\s+)?index[\s]*$'
    r'|^[\s]*(?:subject|name|author|analytical|selective|combined)\s+index[\s]*$'
    r'|^[\s]*index\s+of\s+(?:names?|subjects?|terms?)[\s]*$'
)
# Single-letter or multi-letter alphabetical section headers: A, B, A B C D...
ALPHA_HEADER = re.compile(r'^[A-Z](\s+[A-Z])*\s*$')
PAGENUM_ONLY = re.compile(r'^[\d\s,;\-–—.]+$')
SUBENTRY     = re.compile(r'^[\x97\x96\u2014\u2013\u2012–—]\s*')
SEE_RE       = re.compile(r'(?i)^see\s+(?:also\s+)?(.+)')
# Strip trailing page references: "term, 12, 34–56, 78n, 90ff, xxi"
STRIP_PAGES  = re.compile(r'[,\s]+[\dxivlc][\d,\s;n\.–\-ffix]*$', re.IGNORECASE)

# Ebook preamble patterns to skip
PREAMBLE_RE = re.compile(
    r'page numbers|printed version|e-reader|scroll forward|'
    r'beginning of the|corresponding print|italics indicate|'
    r'bold refer|link will take|print edition',
    re.IGNORECASE)

# Author affiliation noise: 'Editor: Name, University, Country'
AUTHOR_AFFIL_RE = re.compile(
    r'\b(Editor|Editors|Author|Authors|Professor|Dr\.)\s*:?\s+[A-Z]',
    re.IGNORECASE)

# Sub-entry function-word fragments: 'and cybernetics', 'of machines'
FUNC_FRAGMENT_RE = re.compile(
    r'^(of|and|in|on|at|to|for|with|by|from|the|a|an)\b',
    re.IGNORECASE)

# FIX: Foreign-language header filter.
# Catches OCR'd section dividers from non-English indexes that survive as main
# entries: French (Bibliographie, Références), German (Sachregister, Literatur),
# Spanish (Índice), Italian, Dutch, and common all-caps variants.
FOREIGN_HEADER_RE = re.compile(
    r'^(?:'
    r'bibliograph(?:ie|y|ies|ia)|r[eé]f[eé]rences?|literatur(?:verzeichnis)?|'
    r'sachregister|namenregister|abk[uü]rzung(?:en)?|abbildung(?:en)?|'
    r'[ií]ndice|registro|bijlage|literatuur|'
    r'inhoudsopgave|afkortingen|'
    r'table\s+des\s+mati[eè]res?|liste\s+des|verzeichnis|anhang|'
    r'annexe?|ap[eé]ndice'
    r')$',
    re.IGNORECASE
)

# FIX: Index structural artifacts — the section header itself ('Index',
# 'General Index', etc.) leaking through as a harvested term.
# These are caught by INDEX_START at section-detection time but can still
# appear as the first line of the extracted block in some book formats.
INDEX_ARTIFACTS_RE = re.compile(
    r'^(?:general\s+)?index(?:\s+of\s+(?:names?|subjects?|terms?))?$'
    r'|^(?:subject|name|author|analytical|selective|combined)\s+index$',
    re.IGNORECASE
)

# Accent normalisation map for canonical person names
import unicodedata as _ud
def _norm_term(t):
    """Normalise for deduplication: lowercase, strip accents."""
    return _ud.normalize('NFC', t.lower().strip())

def _canonical_term(t: str) -> str:
    """
    Normalise an index term to a stable canonical form for storage.

    Rules:
    - Single-word terms: title-case  ('cybernetics' → 'Cybernetics',
                                       'CYBERNETICS' → 'Cybernetics')
    - Multi-word terms:  preserve if already well-formed title-case or proper
      name (including lowercase particles: von, de, van, di, etc.);
      otherwise lowercase ('GENERAL SYSTEMS THEORY' → 'general systems theory').

    This gives consistent deduplication without losing genuine proper nouns
    (e.g. 'Wiener', 'Shannon', 'von Neumann', 'General Systems Theory').
    """
    # Particles permitted lowercase inside a proper name
    PARTICLES = {'von', 'van', 'de', 'di', 'du', 'der', 'den',
                 'la', 'le', 'el', 'al', 'bin', 'bint'}

    words = t.split()
    if not words:
        return t
    if len(words) == 1:
        w = words[0]
        if w.isupper() and len(w) <= 5:   # keep short acronyms: DNA, AI
            return w
        return w.capitalize()

    # A word is "well-formed" if it is title-case, a known particle, or
    # a short all-caps acronym.
    def _ok(w):
        if w in PARTICLES: return True
        if w.isupper() and len(w) <= 5: return True
        return len(w) >= 1 and w[0].isupper() and w[1:].islower()

    if all(_ok(w) for w in words):
        return t   # already canonical — preserve as-is
    return t.lower()


def quality_score(lines):
    """Return fraction of lines that look like real index entries."""
    if not lines: return 0
    good = sum(1 for l in lines if l and l[0].isalpha() and
               sum(c.isalpha() or c.isspace() for c in l)/len(l) > 0.6)
    return good / len(lines)

def extract_index_terms(text, max_chars=60000):
    matches = list(INDEX_START.finditer(text))
    if not matches:
        return [], 'no_index'
    m = matches[-1]
    # Check quality of this index section
    idx_raw = text[m.start(): m.start() + max_chars]
    sample_lines = [l.strip() for l in idx_raw.split('\n')[2:52] if l.strip()]
    qs = quality_score(sample_lines)
    if qs < 0.15:
        return [], 'garbled'
    
    truncated = (m.start() > len(text) * 0.97 and len(idx_raw) < 3000)

    lines  = idx_raw.split('\n')
    terms  = []
    parent = None

    for line in lines[1:]:
        ls = line.strip()
        if not ls: continue
        if ALPHA_HEADER.match(ls): continue
        if PAGENUM_ONLY.match(ls): continue
        if PREAMBLE_RE.search(ls): continue
        if AUTHOR_AFFIL_RE.match(ls): continue
        # FIX: Reject foreign-language section headers (Bibliographie, Sachregister, etc.)
        if FOREIGN_HEADER_RE.match(ls): continue
        # FIX: Reject index section header leaking as a term ('Index', 'General Index', etc.)
        if INDEX_ARTIFACTS_RE.match(ls): continue

        # Garbage check: require mostly alphabetic content.
        # FIX: threshold raised from 0.45 → 0.60; hyphens and parentheses are
        # explicitly permitted (legitimate in terms like 'feedback (negative)').
        alpha_ratio = sum(
            c.isalpha() or c.isspace() or c in ",-'()–-" for c in ls
        ) / len(ls)
        if alpha_ratio < 0.60 and len(ls) > 8: continue
        # Skip very long lines (probably running prose that leaked in)
        if len(ls) > 100: continue

        # See / See also
        see = SEE_RE.match(ls)
        if see:
            ref = STRIP_PAGES.sub('', see.group(1)).strip()
            ref = re.sub(r'\s+', ' ', ref)
            if ref and 3 <= len(ref) <= 80 and ref[0].isalpha():
                terms.append(_canonical_term(ref))
            continue

        # Sub-entry
        if SUBENTRY.match(ls):
            sub = SUBENTRY.sub('', ls)
            sub = STRIP_PAGES.sub('', sub).strip()
            sub = re.sub(r'\s+', ' ', sub)
            # Skip function-word fragments ('and cybernetics', 'of machines')
            if FUNC_FRAGMENT_RE.match(sub): continue
            if parent and sub and 2 <= len(sub) <= 70 and sub[0].isalpha():
                terms.append(f"{parent} — {_canonical_term(sub)}")
            continue

        # Main entry
        term = STRIP_PAGES.sub('', ls).strip()
        term = re.sub(r'\s+', ' ', term)
        # Remove trailing comma
        term = term.rstrip(',').strip()
        # Skip function-word fragment main entries
        if FUNC_FRAGMENT_RE.match(term) and len(term.split()) <= 4: continue
        if (term and len(term) >= 3 and len(term) <= 80
                and term[0].isalpha()
                and not PAGENUM_ONLY.match(term)):
            term = _canonical_term(term)
            parent = term
            terms.append(term)

    # Deduplicate preserving order
    seen = set()
    unique = []
    for t in terms:
        tl = t.lower().strip()
        if tl not in seen:
            seen.add(tl)
            unique.append(t)

    status = 'truncated' if truncated else 'ok'
    return unique, status

# Run across all books

# ── Verify working directory has required data files ────────────────────────
import os as _os
if not _os.path.exists(str(JSON_DIR / 'books_clean.json')):
    print('ERROR: books_clean.json not found in current directory.')
    print(f'Run this script from your project root, not from {_os.getcwd()}')
    print('Example: cd /path/to/project && python3 src/generate_summaries_api.py')
    import sys as _sys; _sys.exit(1)

files = sorted(glob.glob(str(CSV_DIR / 'books_text_*.csv')))
index_data = {}
stats = {'ok':0,'truncated':0,'no_index':0,'garbled':0}

for fp in files:
    with open(fp, encoding='utf-8', errors='replace') as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        bid = row['id']
        if bid in index_data: continue  # skip dupes
        terms, status = extract_index_terms(row['searchable_text'])
        index_data[bid] = {'terms': terms, 'status': status, 'n_terms': len(terms)}
        stats[status] = stats.get(status,0) + 1

print(f"Processed {len(index_data)} books")
for k,v in stats.items():
    print(f"  {k:12s}: {v}")

# Overall vocabulary stats
all_terms = {}
for bid, d in index_data.items():
    for t in d['terms']:
        tl = t.lower()
        if tl not in all_terms: all_terms[tl] = {'term': t, 'books': [], 'count': 0}
        all_terms[tl]['books'].append(bid)
        all_terms[tl]['count'] += 1

print(f"\nTotal unique terms (case-insensitive): {len(all_terms):,}")
print(f"Terms appearing in 2+ books: {sum(1 for v in all_terms.values() if v['count']>=2):,}")
print(f"Terms appearing in 5+ books: {sum(1 for v in all_terms.values() if v['count']>=5):,}")
print(f"Terms appearing in 10+ books: {sum(1 for v in all_terms.values() if v['count']>=10):,}")

# Save
with open(str(JSON_DIR / 'index_terms.json'),'w') as f:
    json.dump(index_data, f, ensure_ascii=False)
with open(str(JSON_DIR / 'index_vocab.json'),'w') as f:
    json.dump(all_terms, f, ensure_ascii=False)
print("\nSaved index_terms.json and index_vocab.json")