"""


04_summarize.py
─────────────────────────────────────────────────────────────────────────────
Step 4 — Summarisation (chapter-by-chapter + whole-book, 3 styles).

For each book produces:
  A) Chapter summaries  — 2-3 extractive sentences per substantive chapter
                          (chapters < MIN_CHAPTER_WORDS words are merged into
                           an "Other / Minor Sections" group)
  B) Whole-book summaries (3 styles, ~5-6 sentences each):
       • Descriptive   — what the book is about (scope, key concepts)
       • Argumentative — central thesis + supporting evidence
       • Critical       — strengths, limitations, contribution

Method: Extractive summarisation via TF-IDF sentence scoring.

Input:  books_clean.json, nlp_results.json
Output: summaries.json
"""

# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_metadata_full.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


import re, json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# ── Config ────────────────────────────────────────────────────────────────────
MIN_CHAPTER_WORDS  = 400   # Chapters with fewer words are merged/skipped
MAX_CHAPTERS_SHOWN = 20    # Cap per book to keep report manageable
CHAPTER_SENTS      = 3     # Sentences per chapter summary
BOOK_SENTS         = 6     # Sentences per whole-book summary

STOPWORDS = set("""
a about above after again against all also am an and any are as at be because
been before being below between both but by can cannot could did do does doing
down during each few for from further get had has have having he her here hers
herself him himself his how if in into is it its itself let me more most my
myself no nor not of off on once only or other our ours ourselves out over own
same she should so some such than that the their theirs them themselves then
there these they this those through to too under until up very was we were what
when where which while who whom why will with would you your yours yourself
yourselves may thus hence therefore however moreover furthermore indeed
whereas whether although though since upon within without toward towards
""".split())


# ── Chapter splitting ─────────────────────────────────────────────────────────

CHAPTER_PATTERNS = [
    # CHAPTER ONE … FIFTEEN  (with optional title)
    r'CHAPTER\s+(?:ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|'
    r'ELEVEN|TWELVE|THIRTEEN|FOURTEEN|FIFTEEN)(?:\s+[A-Z][A-Za-z\s,:\-]{0,80})?',
    # CHAPTER 1-15  (with optional title)
    r'CHAPTER\s+(?:1[0-5]|\d)(?:\s+[A-Z][A-Za-z\s,:\-]{0,80})?',
    # Chapter 1-15  (title-case, with optional subtitle)
    r'Chapter\s+(?:1[0-5]|\d)(?:\s+[A-Z][A-Za-z\s,:\-]{0,60})?',
    # Part I-VIII or Part 1-8
    r'Part\s+(?:[IVX]{1,4}|\d)(?:\s+[A-Z][A-Za-z\s,:\-]{0,60})?',
    # "1. Long Title Of At Least Four Words" — require >= 4 words in title
    r'\b(?:1[0-5]|\d)\.\s+[A-Z][a-zA-Z]{3,}(?:\s+[A-Za-z]{2,}){3,}',
]

# Combined pattern anchored so it must appear after whitespace / start
SPLIT_RE = re.compile(
    r'(?<!\w)(?:' + '|'.join(CHAPTER_PATTERNS) + r')(?!\w)',
    re.UNICODE
)

def split_into_chapters(text):
    """
    Split flat text into (title, body) pairs. Returns list of dicts.
    Small fragments (< MIN_CHAPTER_WORDS words) are merged into an
    "Other / Minor Sections" aggregate.
    """
    # Find all split points
    splits = [(m.start(), m.group()) for m in SPLIT_RE.finditer(text)]

    if not splits:
        # Fallback: divide into ~5 equal chunks
        chunk = max(len(text) // 5, 10000)
        return [
            {'index': i+1, 'title': f'Section {i+1}',
             'text': text[i*chunk:(i+1)*chunk]}
            for i in range(5)
            if len(text[i*chunk:(i+1)*chunk].split()) >= MIN_CHAPTER_WORDS
        ]

    # Build raw chapter list
    raw = []
    # Text before first split = opening
    if splits[0][0] > 200:
        raw.append({'title': 'Opening', 'text': text[:splits[0][0]]})

    for i, (pos, title) in enumerate(splits):
        end = splits[i+1][0] if i+1 < len(splits) else len(text)
        body = text[pos + len(title): end].strip()
        raw.append({'title': re.sub(r'\s+', ' ', title).strip(), 'text': body})

    # Merge small chapters
    chapters, minor_texts = [], []
    for ch in raw:
        wc = len(ch['text'].split())
        if wc >= MIN_CHAPTER_WORDS:
            chapters.append(ch)
        else:
            minor_texts.append(ch['text'])

    # Append merged minor sections as one entry (if substantial)
    if minor_texts:
        merged = ' '.join(minor_texts)
        if len(merged.split()) >= MIN_CHAPTER_WORDS:
            chapters.append({'title': 'Other / Minor Sections', 'text': merged})

    # Cap at MAX_CHAPTERS_SHOWN (keep largest chapters)
    if len(chapters) > MAX_CHAPTERS_SHOWN:
        chapters.sort(key=lambda c: len(c['text'].split()), reverse=True)
        chapters = chapters[:MAX_CHAPTERS_SHOWN]
        chapters.sort(key=lambda c: c.get('orig_index', 0))

    # Add index
    for i, ch in enumerate(chapters):
        ch['index'] = i + 1
    return chapters


# ── Sentence tokenisation ─────────────────────────────────────────────────────

def sent_tokenize(text, min_words=8, max_words=80):
    text = re.sub(r'\s+', ' ', text)
    sents = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in sents
            if min_words <= len(s.split()) <= max_words]


# ── TF-IDF sentence scoring ───────────────────────────────────────────────────

def score_sentences(sentences, context=None):
    if len(sentences) < 2:
        return np.ones(len(sentences))
    corpus = list(sentences) + ([context] if context else [])
    try:
        vec = TfidfVectorizer(max_features=800, stop_words=list(STOPWORDS),
                              token_pattern=r'(?u)\b[a-zA-Z]{4,}\b')
        mat = vec.fit_transform(corpus)
        return np.array(mat[:len(sentences)].sum(axis=1)).flatten()
    except Exception:
        return np.ones(len(sentences))

def top_sents(sentences, scores, n):
    if not sentences: return ''
    n = min(n, len(sentences))
    idx = sorted(np.argsort(scores)[::-1][:n])
    return ' '.join(sentences[i] for i in idx)


# ── Chapter summariser ────────────────────────────────────────────────────────

def summarise_chapter(ch_text, book_context):
    sents = sent_tokenize(ch_text)
    if not sents:
        return 'No extractable summary for this section.'
    scores = score_sentences(sents, context=book_context)
    return top_sents(sents, scores, CHAPTER_SENTS)


# ── Whole-book summarisers ────────────────────────────────────────────────────

ARG_RE = re.compile(
    r'\b(argues?|argued|contends?|claims?|asserts?|proposes?|suggests?|'
    r'demonstrates?|shows?\s+that|this\s+(?:book|work|study)|'
    r'author\s+(?:argues?|demonstrates?|shows?|claims?)|'
    r'central\s+(?:claim|argument|thesis)|main\s+(?:argument|claim|thesis)|'
    r'purpose\s+of\s+this|thesis\s+is)\b', re.IGNORECASE)

CRIT_RE = re.compile(
    r'\b(however|although|despite|limitation|critique|weakness|strength|'
    r'failure|success|problem|challenge|importantly|significantly|'
    r'nevertheless|shortcoming|advantage|disadvantage|contributes?|'
    r'contribution|valuable|problematic|overlook|neglect|ignores?|misses?|'
    r'insight|innovative|groundbreaking|seminal|influential|'
    r'underestimates?|overestimates?|reductive|nuanced)\b', re.IGNORECASE)

def summarise_descriptive(text):
    sents = sent_tokenize(text[3000:30000])
    if not sents: return ''
    return top_sents(sents, score_sentences(sents), BOOK_SENTS)

def summarise_argumentative(text):
    sents = sent_tokenize(text[2000:45000])
    pool  = [s for s in sents if ARG_RE.search(s)] or sents
    return top_sents(pool, score_sentences(pool), BOOK_SENTS)

def summarise_critical(text):
    sents = sent_tokenize(text[3000:50000])
    pool  = [s for s in sents if CRIT_RE.search(s)] or sents
    return top_sents(pool, score_sentences(pool), BOOK_SENTS)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    with open(str(JSON_DIR / 'books_clean.json'), encoding='utf-8') as f:
        books = json.load(f)
    with open(str(JSON_DIR / 'nlp_results.json')) as f:
        R = json.load(f)

    summaries = {}
    for bid in R['book_ids']:
        title  = books[bid]['title']
        author = books[bid]['author']
        text   = books[bid]['clean_text']

        # Chapter summaries
        chapters = split_into_chapters(text)
        context  = text[:60000]
        ch_sums  = []
        for ch in chapters:
            s = summarise_chapter(ch['text'], context)
            ch_sums.append({
                'index':      ch['index'],
                'title':      ch['title'],
                'summary':    s,
                'word_count': len(ch['text'].split())
            })

        # Whole-book summaries
        summaries[bid] = {
            'title':         title,
            'author':        author,
            'n_chapters':    len(ch_sums),
            'chapters':      ch_sums,
            'descriptive':   summarise_descriptive(text),
            'argumentative': summarise_argumentative(text),
            'critical':      summarise_critical(text),
        }

        print(f"✓ [{bid}] {title[:55]:55s}  ({len(ch_sums)} chapters)")

    with open(str(JSON_DIR / 'summaries.json'), 'w', encoding='utf-8') as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)
    print(f"\nDone. Summaries saved for {len(summaries)} books.")

if __name__ == '__main__':
    main()