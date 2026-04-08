"""


generate_summaries_api.py  —  v3 (concurrent)
─────────────────────────────────────────────────────────────────────────────
Generates high-quality abstractive summaries via the Anthropic Messages API.

v3 changes over v2:
  - ThreadPoolExecutor for concurrent book processing (default: 4 workers)
  - Thread-safe file writes via a Lock — no data loss under concurrency
  - Token-bucket rate limiter shared across all threads — respects API limits
  - JSONL intermediate file (summaries.jsonl) for crash-safe incremental saves
  - Final conversion to summaries.json on completion for downstream compat
  - --workers N flag to control concurrency (use 1 to revert to sequential)

Usage:
    python3 generate_summaries_api.py              # 4 concurrent workers
    python3 generate_summaries_api.py --workers 8  # faster (watch rate limits)
    python3 generate_summaries_api.py --workers 1  # sequential (original behaviour)

Requires: ANTHROPIC_API_KEY environment variable

Quality controls (unchanged from v2):
  1. Strict length — max_tokens=250 (book), 130 (chapter)
  2. Multi-point text sampling — 15%/50%/80% through text
  3. Document type detection — edited volumes get a different prompt
  4. Anti-extraction instruction — explicit no-copy directive
  5. Verbatim similarity check — retries if >35% 8-gram overlap
  6. Chapter title cleaning — OCR fragments replaced with "Chapter N"
"""

# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_metadata_full.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


import json, re, time, os, sys, urllib.request, urllib.error
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Config ────────────────────────────────────────────────────────────────────
MODEL            = "claude-sonnet-4-20250514"
MAX_TOK_BOOK     = 250
MAX_TOK_CHAPTER  = 130
OVERLAP_RETRY_TH = 0.35
RETRY_LIMIT      = 3
RETRY_DELAY      = 5
MIN_CH_WORDS     = 400
MAX_CHAPTERS     = 20
SAMPLE_LEN       = 2000

import os
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not API_KEY:
    raise SystemExit(
        "ERROR: ANTHROPIC_API_KEY environment variable is not set.\n"
        "Set it before running:\n"
        "  export ANTHROPIC_API_KEY=sk-ant-..."
    )

# ── Rate limiter (token bucket, thread-safe) ──────────────────────────────────
class RateLimiter:
    """
    Thread-safe token bucket rate limiter.
    max_rate: maximum requests per second across all threads.
    Anthropic's default tier allows ~50 req/min ≈ 0.83 req/s.
    We use a conservative 0.6 req/s (one request per 1.67s across all threads)
    to stay well within limits and leave headroom for retries.
    """
    def __init__(self, max_rate=0.6):
        self._lock      = threading.Lock()
        self._min_gap   = 1.0 / max_rate   # minimum seconds between requests
        self._last_time = 0.0

    def acquire(self):
        with self._lock:
            now  = time.monotonic()
            wait = self._last_time + self._min_gap - now
            if wait > 0:
                time.sleep(wait)
            self._last_time = time.monotonic()

# ── Thread-safe file writer ───────────────────────────────────────────────────
class SafeWriter:
    """
    Appends completed book records to summaries.jsonl atomically.
    Each line is one JSON object — crash-safe, no read-back needed.
    """
    def __init__(self, path):
        self._path = path
        self._lock = threading.Lock()

    def write(self, record: dict):
        line = json.dumps(record, ensure_ascii=False) + '\n'
        with self._lock:
            with open(self._path, 'a', encoding='utf-8') as f:
                f.write(line)
                f.flush()

# ── Document type detection ───────────────────────────────────────────────────
EDITED_KEYWORDS = [
    'journal','festschrift','handbook','encyclopedia','proceedings',
    'anthology','reader','companion','collection','essays on',
    'selected papers','symposium','yearbook','annual','edited by',
    'routledge library','kybernetes','in memoriam','tribute',
]
def is_edited_volume(title):
    t = title.lower()
    return any(k in t for k in EDITED_KEYWORDS)

# ── Text utilities ─────────────────────────────────────────────────────────────
def sanitise(text):
    return ''.join(
        c for c in text
        if (32 <= ord(c) <= 65535 or c in '\n\t\r')
        and ord(c) not in range(0x80, 0xA0)
    )

def clean_sample(text):
    """Strip OCR scanning artefacts before sending to the API."""
    for _s in ('Digitized by Google', 'Digitized by\nGoogle',
               'Original from UNIVERSITYOF CALIFORNIA',
               'Original from UNIVERSITY OF CALIFORNIA',
               'UNIVERSITYOF CALIFORNIA', 'Google\nOriginal from',
               'Scanned by Internet Archive'):
        text = text.replace(_s, ' ')
    return re.sub(r'[ \t]+', ' ', text).strip()

def get_samples(text):
    n = len(text)
    offsets = [max(int(n * p), 4000) for p in (0.15, 0.50, 0.80)]
    slices = [clean_sample(sanitise(text[o: o + SAMPLE_LEN].strip())) for o in offsets]
    return '\n\n---\n\n'.join(f'[Excerpt {i+1}]\n{s}' for i, s in enumerate(slices))

def get_ch_sample(text):
    return sanitise(text[500: 3500].strip())

# ── Chapter splitting ─────────────────────────────────────────────────────────
CHAPTER_PATTERNS = [
    r'CHAPTER\s+(?:ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|'
    r'ELEVEN|TWELVE|THIRTEEN|FOURTEEN|FIFTEEN)(?:\s+[A-Z][A-Za-z\s,:\-]{0,80})?',
    r'CHAPTER\s+(?:1[0-5]|\d)(?:\s+[A-Z][A-Za-z\s,:\-]{0,80})?',
    r'Chapter\s+(?:1[0-5]|\d)(?:\s+[A-Z][A-Za-z\s,:\-]{0,60})?',
    r'Part\s+(?:[IVX]{1,4}|\d)(?:\s+[A-Z][A-Za-z\s,:\-]{0,60})?',
    r'\b(?:1[0-5]|\d)\.\s+[A-Z][a-zA-Z]{3,}(?:\s+[A-Za-z]{2,}){3,}',
]
SPLIT_RE = re.compile(
    r'(?<!\w)(?:' + '|'.join(CHAPTER_PATTERNS) + r')(?!\w)', re.UNICODE)

def is_good_title(title):
    t = title.strip()
    if t in ('Opening', 'Other / Minor Sections') or t.startswith('Section '):
        return True
    if not t or not t[0].isupper(): return False
    if len(t.split()) < 2: return False
    if len(t) > 80 and not re.search(r'[.!?:]$', t): return False
    return True

def split_into_chapters(text):
    splits = [(m.start(), m.group()) for m in SPLIT_RE.finditer(text)]
    if not splits:
        chunk = max(len(text) // 5, 10000)
        return [{'index': i+1, 'title': f'Section {i+1}',
                 'text': text[i*chunk:(i+1)*chunk]}
                for i in range(5)
                if len(text[i*chunk:(i+1)*chunk].split()) >= MIN_CH_WORDS]
    raw = []
    if splits[0][0] > 200:
        raw.append({'title': 'Opening', 'text': text[:splits[0][0]]})
    for i, (pos, title) in enumerate(splits):
        end = splits[i+1][0] if i+1 < len(splits) else len(text)
        raw.append({'title': re.sub(r'\s+', ' ', title).strip(),
                    'text': text[pos + len(title): end].strip()})
    chapters, minor = [], []
    for ch in raw:
        (chapters if len(ch['text'].split()) >= MIN_CH_WORDS else minor).append(ch)
    merged = ' '.join(c['text'] for c in minor)
    if len(merged.split()) >= MIN_CH_WORDS:
        chapters.append({'title': 'Other / Minor Sections', 'text': merged})
    if len(chapters) > MAX_CHAPTERS:
        chapters.sort(key=lambda c: len(c['text'].split()), reverse=True)
        chapters = chapters[:MAX_CHAPTERS]
    for i, ch in enumerate(chapters):
        ch['index'] = i + 1
    return chapters

# ── Quality checks ─────────────────────────────────────────────────────────────
NOISE_RE = re.compile(
    r'(?i)(isbn|©|\be-book\b|\bebook\b|\bepub\b|publisher|copyright|'
    r'all\s+rights\s+reserved|published\s+by|\d{10,}|catalogu|'
    r'digitized by|original from university|universityof)')

# Openers that signal description rather than analysis — trigger a retry
REPORT_RE = re.compile(
    r'^(this (book|work|chapter|collection|volume|text|study) (examines|explores|discusses|presents|covers|offers|provides|investigates|analyzes|analyses)|in this (book|chapter|work)|the author (examines|explores|discusses|presents))',
    re.IGNORECASE)

# Prompt format placeholder leaked into output — always retry
PLACEHOLDER_RE = re.compile(
    r'^\s*\[2 sentences|^\s*\[DESCRIPTIVE\]|^\s*\[2-sentence|^\s*\[Describe|^\s*\[A 2|^\s*\[its subject',
    re.IGNORECASE)

def ngram_overlap(text, source, n=8):
    tw = text.lower().split()
    sw = source.lower()
    if len(tw) < n: return 0.0
    grams = [' '.join(tw[i:i+n]) for i in range(len(tw) - n + 1)]
    hits  = sum(1 for g in grams if g in sw)
    return hits / len(grams)

def is_clean(text, source='', overlap_threshold=OVERLAP_RETRY_TH):
    if not text or len(text.split()) < 10: return False
    if NOISE_RE.search(text): return False
    if REPORT_RE.match(text.strip()): return False  # description not analysis
    if PLACEHOLDER_RE.match(text): return False      # prompt template leaked into output
    if source and ngram_overlap(text, source) > overlap_threshold: return False
    return True

def clean_noise(text):
    sents = re.split(r'(?<=[.!?])\s+', text.strip())
    return ' '.join(s for s in sents
                    if not NOISE_RE.search(s) and len(s.split()) >= 4).strip()

# ── API call ──────────────────────────────────────────────────────────────────
def call_claude(prompt, max_tokens, rate_limiter):
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload, headers=headers, method="POST")

    for attempt in range(RETRY_LIMIT):
        rate_limiter.acquire()
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())['content'][0]['text'].strip()
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='replace')[:300]
            if e.code in (429, 529):
                wait = RETRY_DELAY * (2 ** attempt)   # exponential backoff
                print(f"    [rate limit — waiting {wait}s]", flush=True)
                time.sleep(wait)
            elif e.code in (400, 500, 502, 503, 504):
                wait = RETRY_DELAY * (attempt + 2)
                print(f"    [HTTP {e.code} — waiting {wait}s, attempt {attempt+1}/{RETRY_LIMIT}]",
                      flush=True)
                if attempt == RETRY_LIMIT - 1:
                    print(f"    [giving up: {body}]", flush=True)
                    return ""
                time.sleep(wait)
            else:
                print(f"    [HTTP {e.code} — {body}]", flush=True)
                raise
        except Exception as exc:
            if attempt < RETRY_LIMIT - 1:
                time.sleep(RETRY_DELAY)
            else:
                print(f"    [error after {RETRY_LIMIT} attempts: {exc}]", flush=True)
                return ""
    return ""

# ── Prompts ───────────────────────────────────────────────────────────────────
BOOK_PROMPT = """\
You are an expert reader in cybernetics, systems theory, and the history of ideas.

Write THREE analytical summaries of "{title}" by {author}.

Before writing, consider what kind of intellectual work this book is doing.
Authors do not always argue towards a conclusion — they may instead:
  - trace what follows if a concept is taken seriously
  - propose a vocabulary and test what it illuminates
  - unsettle a received distinction or category
  - connect phenomena that were previously thought unrelated
  - work through a problem whose solution is uncertain
  - explore a possibility space without settling it
Your summaries should reflect whichever orientation fits this particular work.

REQUIREMENTS:
1. Each summary is EXACTLY 2 sentences.
2. Name the intellectual move — do not merely name the topic.
   WEAK:  "This book examines feedback loops and their applications in biology."
   STRONGER: "Ashby works out what conditions are necessary for a system to \
adapt, arriving at the principle that a regulator must match the variety of \
its environment — a conclusion with implications well beyond biology."
   Note: even the stronger example makes an assumption about intent. \
If uncertain, use hedged language: "The work can be read as...", \
"One way to understand its contribution is...", "What emerges from the \
analysis is..."
3. Avoid presupposing a thesis-first structure. Verbs like "argues", \
"demonstrates", "proves", "contends" imply the author had a conclusion and \
marshalled evidence for it. If the work is exploratory, tracing, or \
proposing, choose verbs that reflect that: "develops", "traces", "proposes", \
"works through", "questions", "opens up", "reframes", "connects".
4. Do NOT begin with "This book", "This work", "The author", or any phrase \
that signals content-listing rather than intellectual engagement.
5. Use the excerpts below only to orient yourself to the book's vocabulary \
and domain — not as the source of your summary.
6. Ignore OCR artefacts, page numbers, publisher details, and scanning noise.

Format EXACTLY as (no other text):
DESCRIPTIVE: [2 sentences: what intellectual problem or question does this \
work engage, and what kind of answer, framework, or reorientation does it \
propose or arrive at?]
ARGUMENTATIVE: [2 sentences: what is the work's core intellectual move — \
is it proving, exploring, proposing, questioning, or tracing? What gives \
the move its force — what evidence, logic, or conceptual manoeuvre does \
it turn on?]
CRITICAL: [2 sentences: what has this work made possible or changed in \
its field — what can now be thought or done that could not be before? \
What remains open, contested, or limited in what it achieves?]

Excerpts from "{title}" by {author} (for orientation only):
---
{samples}
---"""

EDITED_PROMPT = """\
You are an expert reader in cybernetics, systems theory, and the history of ideas.

Write THREE analytical summaries of "{title}", an edited collection associated \
with {author}.

Before writing, consider what intellectual work this collection is doing. \
Edited volumes may: consolidate an emerging field, stage a debate between \
positions, apply a framework across different domains, mark a historical moment, \
or open a space whose boundaries are still being negotiated.
Your summaries should reflect which of these orientations fits this collection.

REQUIREMENTS:
1. Each summary is EXACTLY 2 sentences.
2. Name the intellectual work, not the content inventory.
   WEAK:  "This collection presents papers on cybernetics from various authors."
   STRONGER: "The volume marks the moment when cybernetics turned reflexively \
on itself — contributors share the conviction that any account of a system \
must include an account of the observer constructing that account."
3. Avoid presupposing consensus where there may be tension. If the collection \
stages a debate or holds unresolved differences, say so. If uncertain, \
use hedged language: "The collection can be read as...", \
"What unites the contributions is, at minimum...", "One effect of grouping \
these pieces is..."
4. Do NOT begin with "This collection", "This volume", "This anthology", or \
any phrase that signals content-listing.
5. Use the excerpts only for orientation to domain and vocabulary.
6. Ignore OCR artefacts, scanning noise, and editorial metadata.

Format EXACTLY as (no other text):
DESCRIPTIVE: [2 sentences: what intellectual territory or moment does this \
collection stake out, and what unifying question, problem, or orientation \
holds it together — even loosely?]
ARGUMENTATIVE: [2 sentences: what intellectual move does the collection make \
as a whole — consolidating, staging debate, applying, opening? What gives \
that move its significance?]
CRITICAL: [2 sentences: what has this collection made visible or possible \
that was not before? What perspectives, voices, or problems remain at its \
edges or outside it?]

Excerpts (for orientation only):
---
{samples}
---"""

CHAPTER_PROMPT = """\
You are an expert reader in cybernetics, systems theory, and the history of ideas.

Write a 2-sentence analytical summary of the chapter "{ch_title}" \
from "{title}" by {author}.

Before writing, consider what kind of move this chapter is making. \
It may be: establishing a foundation, applying a concept, complicating \
an assumption, working through a difficult case, connecting two domains, \
or opening a question without settling it.

REQUIREMENTS:
1. Write EXACTLY 2 sentences.
2. Sentence 1: name the intellectual move — what does this chapter do, \
not merely what it is about.
   WEAK:  "This chapter examines feedback in biological systems."
   STRONGER: "Working from the problem of how organisms maintain stability \
despite perturbation, the chapter develops the concept of negative feedback \
as a correction mechanism that operates before deviations become irreversible."
3. Sentence 2: locate the move — what does it rest on (evidence, a thought \
experiment, a formal model, a case study), and how does it relate to the \
book's larger project?
4. Choose verbs that match the chapter's actual orientation: "develops", \
"works through", "questions", "connects", "reframes", "traces", "proposes", \
"tests", "complicates" — not "argues" or "demonstrates" unless those \
verbs genuinely fit.
5. Do NOT begin with "This chapter", "The chapter", or "In this chapter".
6. Ignore all OCR artefacts, page numbers, headers, and scanning noise.

Write only the 2-sentence summary with no preamble:

Excerpt (for orientation to vocabulary and domain — do not paraphrase it):
---
{text}
---"""

CHAPTER_RETRY_PROMPT = """\
You are an expert reader in cybernetics, systems theory, and the history of ideas.

Based on the chapter title "{ch_title}" from "{title}" by {author}, write a \
2-sentence analytical summary. You have no usable excerpt, so reason from what \
you know about this work and its intellectual context.

Sentence 1: what intellectual move does this chapter most plausibly make, \
given its title and its place in this book?
Sentence 2: what might ground that move — a concept, a case, a formal \
result, a historical example — and why would it matter?

If you are genuinely uncertain, use hedged language: "One reading of this \
chapter is...", "Given the book's larger project, this chapter likely..."

Write EXACTLY 2 sentences. No preamble or label."""

# ── Parse whole-book response ─────────────────────────────────────────────────
def parse_book_response(text):
    out = {}
    for key in ['DESCRIPTIVE', 'ARGUMENTATIVE', 'CRITICAL']:
        m = re.search(
            rf'{key}:\s*(.*?)(?=(?:DESCRIPTIVE|ARGUMENTATIVE|CRITICAL):|$)',
            text, re.DOTALL | re.IGNORECASE)
        out[key.lower()] = m.group(1).strip() if m else ''
    return out

# ── Summarise one book (called from worker thread) ────────────────────────────
def process_book(bid, books, rate_limiter, _recursive=False):
    """
    Summarises one book (whole-book + all chapters).
    Returns a complete summary record dict.
    Called concurrently from worker threads.
    """
    title  = books[bid]['title']
    author = books[bid]['author']
    text   = books[bid]['clean_text']
    edited = is_edited_volume(title)
    src_ref = text[:60000]

    # Split chapters early — needed for recursive mode and chapter summaries
    chapters_pre = split_into_chapters(text)

    # Recursive mode: use chapter excerpts as input for book-level summary
    if _recursive and chapters_pre:
        ch_excerpts = ' '.join(
            f"Ch{ch['index']} ({ch.get('title','')[:35]}): "
            f"{get_ch_sample(ch['text'])[:400]}"
            for ch in chapters_pre[:12]
        )
        samples = f"[Chapter excerpts — '{title}']\n\n{ch_excerpts[:5000]}"
    else:
        samples = get_samples(text)

    prompt = (EDITED_PROMPT if edited else BOOK_PROMPT).format(
        title=title, author=author, samples=samples)

    # ── Whole-book summary ────────────────────────────────────────────────────
    book_summs = None
    for attempt in range(2):
        try:
            raw    = call_claude(prompt, MAX_TOK_BOOK, rate_limiter)
            parsed = parse_book_response(raw)
            ok = all(
                is_clean(v, src_ref,
                         overlap_threshold=0.50 if attempt == 1 else OVERLAP_RETRY_TH)
                for v in parsed.values() if v
            )
            if ok:
                book_summs = parsed; break
            else:
                ovlaps = {k: ngram_overlap(v, src_ref) for k, v in parsed.items() if v}
                print(f"  [{bid}] book attempt {attempt+1} overlap "
                      f"{max(ovlaps.values()):.0%} — retrying", flush=True)
                prompt = prompt.replace(
                    'write entirely in your own words',
                    'write entirely in your own words — DO NOT quote or '
                    'paraphrase the excerpts at all, use only your prior knowledge')
        except Exception as e:
            print(f"  [{bid}] book error: {e}", flush=True)

    if book_summs is None:
        book_summs = {'descriptive': '', 'argumentative': '', 'critical': ''}
    for k in book_summs:
        book_summs[k] = clean_noise(book_summs[k])

    # ── Chapter summaries ─────────────────────────────────────────────────────
    chapters = chapters_pre   # already split above
    ch_sums  = []

    for ch in chapters:
        display_title = ch['title'] if is_good_title(ch['title']) \
                        else f"Chapter {ch['index']}"
        sample  = get_ch_sample(ch['text'])
        ch_prompt = CHAPTER_PROMPT.format(
            title=title, author=author, ch_title=display_title, text=sample)

        summ = ''
        for attempt in range(2):
            try:
                s = call_claude(ch_prompt, MAX_TOK_CHAPTER, rate_limiter).strip().strip('"')
                if is_clean(s, src_ref,
                            overlap_threshold=0.50 if attempt == 1 else OVERLAP_RETRY_TH):
                    summ = clean_noise(s); break
                print(f"  [{bid}] ch{ch['index']} overlap "
                      f"{ngram_overlap(s, src_ref):.0%} — retrying", flush=True)
                ch_prompt = CHAPTER_RETRY_PROMPT.format(
                    title=title, author=author, ch_title=display_title)
            except Exception as e:
                print(f"  [{bid}] ch{ch['index']} error: {e}", flush=True)

        ch_sums.append({
            'index':      ch['index'],
            'title':      display_title,
            'summary':    summ,
            'word_count': len(ch['text'].split()),
        })

    return {
        'id':            bid,
        'title':         title,
        'author':        author,
        'n_chapters':    len(ch_sums),
        'chapters':      ch_sums,
        'descriptive':   book_summs.get('descriptive', ''),
        'argumentative': book_summs.get('argumentative', ''),
        'critical':      book_summs.get('critical', ''),
    }

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    # Verify working directory has required data files
    if not os.path.exists(str(JSON_DIR / 'books_clean.json')):
        print('ERROR: books_clean.json not found in current directory.')
        print(f'Run from your project root, not from {os.getcwd()}')
        print('Example: cd /path/to/project && python3 src/generate_summaries_api.py')
        sys.exit(1)

    # Parse --workers and --recursive flags
    workers   = 4
    recursive = '--recursive' in sys.argv
    if '--workers' in sys.argv:
        try:
            workers = int(sys.argv[sys.argv.index('--workers') + 1])
        except (IndexError, ValueError):
            print("Usage: python3 generate_summaries_api.py [--workers N] [--recursive]")
            sys.exit(1)

    print(f"Workers: {workers}  |  Model: {MODEL}  |  Recursive: {recursive}")

    # Load books
    with open(str(JSON_DIR / 'books_clean.json'), encoding='utf-8') as f:
        books = json.load(f)
    with open(str(JSON_DIR / 'nlp_results.json')) as f:
        results = json.load(f)
    book_ids = results['book_ids']
    print(f"Books loaded: {len(book_ids)}")

    # Load already-done IDs from JSONL (fast — reads only id fields)
    jsonl_path = str(JSON_DIR / 'summaries.jsonl')
    done_ids   = set()
    if os.path.exists(jsonl_path):
        with open(jsonl_path, encoding='utf-8') as f:
            for line in f:
                m = re.search(r'"id"\s*:\s*"([^"]+)"', line)
                if m: done_ids.add(m.group(1))
        print(f"Resuming: {len(done_ids)}/{len(book_ids)} already done")
    else:
        print(f"Starting fresh: {len(book_ids)} books")

    pending = [bid for bid in book_ids if bid not in done_ids]
    print(f"To process: {len(pending)} books\n")
    if not pending:
        print("Nothing to do.")
        # Still convert any existing jsonl to json, then exit
    else:
        rate_limiter = RateLimiter(max_rate=workers * 0.5)
        writer       = SafeWriter(jsonl_path)
        completed    = 0

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(process_book, bid, books, rate_limiter,
                                          recursive): bid
                       for bid in pending}

            for future in as_completed(futures):
                bid = futures[future]
                try:
                    record = future.result()
                    writer.write(record)
                    completed += 1
                    desc_wc = len(record.get('descriptive','').split())
                    n_ch    = record['n_chapters']
                    print(f"[{completed}/{len(pending)}] [{bid}] "
                          f"{record['title'][:50]:50s} "
                          f"desc={desc_wc}w  ch={n_ch}", flush=True)
                except Exception as e:
                    print(f"[FAILED] [{bid}] {e}", flush=True)

    # ── Convert JSONL → JSON for downstream compatibility ─────────────────────
    print(f"\nConverting summaries.jsonl → summaries.json ...")
    summaries = {}
    if not os.path.exists(jsonl_path):
        print("  Nothing to convert — summaries.jsonl is empty or missing.")
    else:
     with open(jsonl_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                r = json.loads(line)
                bid = r.pop('id')
                summaries[bid] = r
            except Exception:
                pass

    with open(str(JSON_DIR / 'summaries.json'), 'w', encoding='utf-8') as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)

    print(f"Done. {len(summaries)} books in summaries.json")


if __name__ == '__main__':
    main()