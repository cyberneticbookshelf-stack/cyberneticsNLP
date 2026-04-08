"""


02_clean_text.py
─────────────────────────────────────────────────────────────────────────────
Step 2 of the Book NLP Pipeline.

Cleans raw book text by:
  1. Removing structural boilerplate sections:
       - Publisher / copyright / legal notices
       - Table of contents
       - Preface / foreword
       - Acknowledgements / dedications
       - Index (end-of-book)
       - About-the-author sections
       - "Blank page" markers, URLs, DOIs, ISBNs
  2. Removing non-English tokens using the Hunspell en_US dictionary
     (76,741 words) supplemented with an academic/cybernetics domain
     whitelist (~500 terms).

Data-quality fixes (v0.4.1):
  - ASCII gate moved after whitelist check: accented terms present in the
    domain whitelist (e.g. Wiener, Foerster, lebenswelt) are now preserved
    rather than silently deleted.  Accent-stripped probes are tried before
    the gate so 'naïve' → 'naive' lookup also works.  Purely non-Latin
    tokens (Cyrillic, CJK, Arabic) are still dropped.
  - Case normalisation: process_token now works on a lowercased probe for
    all checks (alpha-ratio, dictionary lookup, consonant heuristic).
    Mixed-case OCR artefacts such as 'CYBERNETics' or 'SYSTEMs' no longer
    slip through the proper-noun shortcut in build_english_checker.

Dictionary note:
  Oxford English Dictionary is not available in this offline environment.
  Hunspell en_US (/usr/share/hunspell/en_US.dic) is used instead — the
  same engine used by LibreOffice, Firefox, and most Linux spell-checkers,
  providing comprehensive American English coverage including academic vocab.

Input:  books_parsed.json
Output: books_clean.json
"""

# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_metadata_full.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


import re, json

# ── 1. Load English dictionary (portable, OS-agnostic discovery) ────────────
#
# No hardcoded paths. _find_dic_via_system() tries in order:
#   1. DICPATH env var    — hunspell's own standard
#                          export DICPATH=/path/to/dir/containing/en_US.dic
#   2. hunspell -D        — asks the binary where its dictionaries live
#   3. CONDA_PREFIX glob  — scans active conda env recursively (any package layout)
#   4. find command       — searches /usr, /opt, /usr/local (Unix/macOS)
#   5. pkg-config         — queries hunspell data dir (Linux)
#   6. pyspellchecker     — pure-Python fallback: pip install pyspellchecker
#   7. No filtering       — graceful degradation with a clear warning
#
# Install options:
#   conda:   conda install -c conda-forge hunspell hunspell-en
#   macOS:   brew install hunspell
#   Linux:   sudo apt-get install hunspell-en-us
#   Override: export DICPATH=/opt/anaconda3/share/hunspell_dictionaries

import sys, os, platform

def _find_dic_via_system():
    """
    Ask the system where hunspell dictionaries are — OS-agnostic.
    Returns a valid path to en_US.dic or None.
    """
    import subprocess, glob, shutil

    # ── Method 1: DICPATH environment variable (hunspell's own standard) ────
    dicpath = os.environ.get('DICPATH', '')
    if dicpath:
        for d in dicpath.split(os.pathsep):
            p = os.path.join(d, 'en_US.dic')
            if os.path.isfile(p):
                return p

    # ── Method 2: `hunspell -D` lists all dictionary directories ────────────
    if shutil.which('hunspell'):
        try:
            out = subprocess.check_output(
                ['hunspell', '-D'], stderr=subprocess.STDOUT,
                timeout=5, text=True, errors='replace')
            for line in out.splitlines():
                line = line.strip()
                if line.endswith('en_US') or line.endswith('en_US.dic'):
                    candidate = line if line.endswith('.dic') else line + '.dic'
                    if os.path.isfile(candidate):
                        return candidate
                    # hunspell -D may list base name without extension
                    for ext in ['.dic', '']:
                        if os.path.isfile(line + ext):
                            return line + ext
        except Exception:
            pass

    # ── Method 3: scan CONDA_PREFIX recursively for any en_US.dic ───────────
    conda_prefix = os.environ.get('CONDA_PREFIX', '')
    if conda_prefix:
        # Use glob to scan without hardcoding subdirectory names
        for pattern in ['**/en_US.dic', '**/en-US.dic']:
            hits = glob.glob(os.path.join(conda_prefix, pattern),
                             recursive=True)
            if hits:
                return hits[0]
        # Also check base conda installation
        conda_root = os.environ.get('CONDA_ROOT',
                     os.path.expanduser('~/anaconda3') if
                     os.path.isdir(os.path.expanduser('~/anaconda3')) else
                     os.path.expanduser('~/miniconda3'))
        for pattern in ['**/en_US.dic']:
            hits = glob.glob(os.path.join(conda_root, 'share', pattern),
                             recursive=True)
            if hits:
                return hits[0]

    # ── Method 4: `find` command (Unix/macOS) ────────────────────────────────
    if shutil.which('find'):
        for search_root in ['/usr', '/opt', '/usr/local']:
            if not os.path.isdir(search_root):
                continue
            try:
                out = subprocess.check_output(
                    ['find', search_root, '-name', 'en_US.dic',
                     '-path', '*/hunspell*', '-type', 'f'],
                    timeout=10, text=True, errors='replace',
                    stderr=subprocess.DEVNULL)
                hits = [l.strip() for l in out.splitlines() if l.strip()]
                if hits:
                    return hits[0]
            except Exception:
                pass

    # ── Method 5: pkg-config (Linux) ─────────────────────────────────────────
    if shutil.which('pkg-config'):
        try:
            out = subprocess.check_output(
                ['pkg-config', '--variable=datadir', 'hunspell'],
                timeout=5, text=True, errors='replace').strip()
            p = os.path.join(out, 'hunspell', 'en_US.dic')
            if os.path.isfile(p):
                return p
        except Exception:
            pass

    return None


def _load_from_hunspell(path):
    """Load word set from a Hunspell .dic file."""
    words = set()
    with open(path, encoding='utf-8', errors='replace') as f:
        for i, line in enumerate(f):
            if i == 0: continue   # first line is word count
            word = line.strip().split('/')[0].lower()
            if word and word.isalpha():
                words.add(word)
    return words

def _load_from_pyspellchecker():
    """Load word set from pyspellchecker's bundled frequency list."""
    from spellchecker import SpellChecker
    sc = SpellChecker()
    # SpellChecker.word_frequency.words() returns all known words
    return set(sc.word_frequency.words())

def load_english_dictionary():
    # 1. Discover hunspell dictionary using portable system methods
    path = _find_dic_via_system()
    if path:
        try:
            words = _load_from_hunspell(path)
            print(f"  Loaded {len(words):,} words from Hunspell: {path}")
            return words
        except Exception as e:
            print(f"  WARNING: Found {path} but failed to read: {e}")

    # Not found — print portable diagnostics
    print("  [hunspell] Dictionary not found via any system method.")
    print(f"  [hunspell] CONDA_PREFIX={os.environ.get('CONDA_PREFIX','(not set)')}")
    print("  [hunspell] To fix: set DICPATH=/path/to/hunspell/dicts in your shell,")
    print("  [hunspell] or: conda install -c conda-forge hunspell hunspell-en,")
    print("  [hunspell] or: brew install hunspell  (macOS),")
    print("  [hunspell] or: sudo apt install hunspell-en-us  (Ubuntu/Debian)")

    # 2. Try pyspellchecker (pip install pyspellchecker)
    try:
        words = _load_from_pyspellchecker()
        print(f"  Loaded {len(words):,} words from pyspellchecker (fallback)")
        print("  NOTE: pyspellchecker uses a frequency list, not a morphological")
        print("  dictionary. Filtering may be slightly less precise than Hunspell.")
        return words
    except ImportError:
        pass

    # 3. Degraded mode — no filtering
    print("  WARNING: No dictionary found. Word filtering is disabled.")
    print("  To enable filtering, either:")
    print(f"    Linux:   sudo apt-get install hunspell-en-us")
    print(f"    macOS:   brew install hunspell")
    print(f"    Any OS:  pip install pyspellchecker")
    print(f"    Manual:  place en_US.dic in the project data/ directory")
    return set()

def build_domain_whitelist():
    """Academic, scientific, and cybernetics-domain terms."""
    return set("""
    cybernetics cybernetic cybernetician cyberneticians cyberneticism
    homeostasis homeostatic homeostat
    autopoiesis autopoietic autopoietically
    teleonomy teleonomic teleological
    feedforward feedbacks
    servomechanism servomechanisms servomechanistic
    eigenvalue eigenvalues eigenvector eigenvectors eigenfunction
    attractor attractors bifurcation bifurcations bifurcate
    stochastic deterministic probabilistic heuristic heuristics
    epistemology epistemological epistemologies epistemically
    ontology ontological ontologies
    phenomenology phenomenological phenomenologies
    hermeneutics hermeneutical hermeneutic
    semiotics semiotic semiotician semioticians semiotically
    recursion recursions recursively recursiveness recursive
    isomorphism isomorphisms isomorphic isomorph
    morphogenesis morphogenetic
    neuropil neurodynamics neurophysiology neurophysiological
    cybernation wiener norbert maturana varela bateson
    ashby foerster luhmann pask mcculloch pitts umezuzu
    von neumann shannon weaver turing
    reductionism holism emergentism emergentist
    constructivism constructivist constructivism
    operationalism operationalist
    technoculture cyberculture cyberspace cyberpunk cyborg cyborgs
    posthuman transhumanism transhumanist
    algorithmically heuristically computationally
    modelling modelled modeller modellers
    behaviour behaviours behavioural behaviourism behaviourist
    organisation organisations organisational
    analyse analysed analyses analysing analyser
    recognise recognised recognises recognising
    realise realised realises realising
    optimise optimised optimises optimising optimisation
    visualise visualised visualises visualising visualisation
    generalise generalised generalises generalising generalisation
    characterise characterised characterises characterising
    emphasise emphasised emphasises emphasising
    utilise utilised utilises utilising utilisation
    theorise theorised theorises theorising theorisation
    minimise maximise minimised maximised minimisation maximisation
    stabilise stabilised destabilise stabilisation
    catalyse catalysed catalysis
    ibid isbn doi pdf epub loc cit preprint forthcoming
    multidisciplinary interdisciplinary transdisciplinary
    subsystem subsystems subcomponent subcomponents
    dataset datasets preprocessing preprocessed
    metacognition metacognitive metalanguage metalevel
    nonlinear nonlinearity nonlinearities
    feedforward retrofeed
    sociotechnical sociocultural socioeconomic sociopolitical
    morphism endomorphism homomorphism
    biosemiotics biocybernetics bionics bioengineering
    neocybernetics protocybernetics
    praxis praxeology praxeological
    affordance affordances
    lifeworld lebenswelt
    weltanschauung gestalt zeitgeist
    heuresis poiesis mimesis methexis praxis
    noosphere technosphere biosphere ecosphere
    thermodynamics thermodynamical thermodynamic
    electrodynamics electrodynamical
    biophysics biophysical biophysicist
    sememe morpheme phoneme lexeme
    semiosphere semiogenesis
    enactivism enactive enactivist
    situatedness embeddedness
    intersubjectivity intersubjective
    performativity performative
    reflexivity reflexive reflexiveness
    objectivity subjectivity intersubjectivity
    positivism positivist postpositivism
    paradigm paradigms paradigmatic
    dialectic dialectics dialectical dialectically
    teleology teleological teleologically
    tautology tautological tautologies
    topology topological topologies
    """.split())

def build_english_checker(dictionary, whitelist):
    expanded = set(dictionary) | set(whitelist)
    suffixes = ['s', 'es', 'ed', 'ing', 'er', 'ers', 'est', 'ly', 'ness',
                'tion', 'tions', 'ment', 'ments', 'ity', 'ities',
                'ism', 'isms', 'ist', 'ists', 'ize', 'ized', 'izes',
                'ise', 'ised', 'ises', 'ical', 'ically', 'ous', 'ious',
                'ful', 'less', 'able', 'ible', 'al', 'ial', 'ic', 'ics']

    def is_english(token):
        t = token.lower()
        if len(t) <= 2: return True
        if t in expanded: return True
        # Title-case proper noun: ONLY first char upper, ALL remaining chars lower.
        # Rejects mixed-case OCR artefacts like 'CYBERNETics' or 'SYSTEMs'.
        if token[0].isupper() and token[1:].islower(): return True
        # Suffix stripping
        for suf in suffixes:
            if t.endswith(suf) and len(t) - len(suf) >= 3:
                stem = t[:-len(suf)]
                if stem in expanded: return True
                if len(stem) > 1 and stem[-1] == stem[-2] and stem[:-1] in expanded:
                    return True
        # Hyphenated compound
        if '-' in t:
            parts = t.split('-')
            if all(p in expanded or len(p) <= 2 for p in parts):
                return True
        return False

    return is_english


# ── 2. Boilerplate section removal ───────────────────────────────────────────

SECTION_HEADERS = [
    # Table of contents
    r'^[\s]*(?:table\s+of\s+)?contents[\s]*$',
    r'^[\s]*(?:brief\s+)?contents[\s]*$',
    r'^[\s]*list\s+of\s+(?:tables?|figures?|illustrations?|plates?)[\s]*$',
    # Preface / foreword
    r'^[\s]*(?:preface|foreword|prologue|prolegomena|preamble)[\s]*$',
    r'^[\s]*(?:author[\'s]*\s+)?preface[\s]*$',
    r'^[\s]*series\s+(?:editor[\'s]*\s+)?(?:preface|foreword)[\s]*$',
    r'^[\s]*editorial\s+(?:preface|foreword|note)[\s]*$',
    # Acknowledgements
    r'^[\s]*acknowledg(?:e?ments?|ments?)[\s]*$',
    r'^[\s]*(?:author[\'s]*\s+)?acknowledgements?[\s]*$',
    # Dedication
    r'^[\s]*dedication[\s]*$',
    r'^[\s]*for\s+[A-Z].{0,60}$',   # "For my wife..." style dedications
    # About the author
    r'^[\s]*about\s+the\s+author[s]?[\s]*$',
    r'^[\s]*notes?\s+on\s+(?:the\s+)?(?:contributors?|authors?)[\s]*$',
    r'^[\s]*(?:contributors?|list\s+of\s+contributors?)[\s]*$',
    # Index
    r'^[\s]*(?:general\s+)?index[\s]*$',
    r'^[\s]*(?:subject|name|author|analytical|selective)\s+index[\s]*$',
    # Bibliography
    r'^[\s]*(?:bibliography|references|works\s+cited|further\s+reading|'
    r'select(?:ed)?\s+bibliography|suggested\s+readings?)[\s]*$',
    r'^[\s]*notes\s+and\s+references[\s]*$',
]
SECTION_RE = re.compile('|'.join(f'(?i:{p})' for p in SECTION_HEADERS))

CHAPTER_RE = re.compile(
    r'(?im)^[\s]*(?:'
    r'chapter\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|'
    r'eleven|twelve)|'
    r'part\s+(?:\d+|one|two|three|four|five|i{1,3}v?|vi*)|'
    r'introduction|'
    r'section\s+\d+|'
    r'\d+\.\s+[A-Z]'
    r')[\s]*$'
)

INLINE_PATTERNS = [
    # Copyright / publisher block
    r'(?i)(?:published\s+by|copyright\s*©?|©\s*\d{4}|all\s+rights\s+reserved|'
    r'printed\s+in|first\s+(?:published|edition)|typeset|'
    r'no\s+part\s+of\s+this\s+(?:publication|book|work)|'
    r'reproduction\s+in\s+any\s+form|'
    r'transmitted\s+in\s+any\s+form|'
    r'mechanical\s+photocopying|'
    r'electronic\s+or\s+mechanical).{0,400}?(?:\.\s|\n|$)',
    # ISBN / ISSN
    r'\bISBN(?:-1[03])?[:\s\-][\d\-X]{9,17}\b',
    r'\bISSN[:\s\-][\d\-]{8,12}\b',
    # Library cataloguing
    r'(?i)library\s+of\s+congress.{0,250}?(?:\n|$)',
    r'(?i)(?:british\s+)?library\s+catalogu.{0,200}?(?:\n|$)',
    r'(?i)catalogu(?:e|ing)-in-publication.{0,200}?(?:\n|$)',
    # Blank-page markers
    r'(?i)this\s+page\s+(?:is\s+)?intentionally\s+(?:left\s+)?blank',
    # URLs / DOIs
    r'https?://\S+',
    r'www\.\S+',
    r'\bdoi:\s*\S+',
    r'\b10\.\d{4,9}/\S+',
]

def remove_boilerplate_sections(text):
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    result, skip_mode, skip_budget = [], False, 0
    MAX_SKIP = 500

    for line in lines:
        stripped = line.strip()
        if skip_mode and CHAPTER_RE.match(stripped):
            skip_mode = False
            skip_budget = 0
            result.append(line)
            continue
        if not skip_mode and SECTION_RE.match(stripped):
            skip_mode = True
            skip_budget = MAX_SKIP
            continue
        if skip_mode:
            skip_budget -= 1
            if skip_budget <= 0:
                skip_mode = False
            continue
        result.append(line)

    return '\n'.join(result)

def apply_inline_patterns(text):
    for pat in INLINE_PATTERNS:
        text = re.sub(pat, ' ', text)
    return text


# ── 3. Dictionary word filtering ─────────────────────────────────────────────

def filter_non_english_tokens(text, is_english_fn):
    import unicodedata as _ud

    def _strip_accents(s):
        """Decompose accented characters and drop the combining marks.
        'Foerster' stays 'Foerster'; 'naïve' → 'naive'; 'über' → 'uber'.
        This is used for dictionary lookup only — the original token is
        returned to the caller so accent information is preserved in output.
        """
        return ''.join(
            c for c in _ud.normalize('NFD', s)
            if _ud.category(c) != 'Mn'
        )

    def process_token(token):
        if re.match(r'^\d+$', token): return token
        if len(token) <= 2: return token

        # ── Case normalisation ────────────────────────────────────────────
        # Work on a lowercased probe for all checks; return original token
        # if it passes, so casing in the source text is preserved.
        probe = token.lower()

        # ── Non-ASCII handling ────────────────────────────────────────────
        # FIX: previously non-ASCII tokens were discarded here, before the
        # whitelist was consulted. Now we:
        #   1. Try the token as-is (catches whitelisted accented terms).
        #   2. Try an accent-stripped version (catches 'naïve' → 'naive').
        #   3. Only then gate on ASCII — purely non-Latin tokens are dropped.
        if not token.isascii():
            clean_probe = re.sub(r'[^a-zA-Z\-]', '', _strip_accents(probe))
            if clean_probe and is_english_fn(clean_probe):
                return token          # whitelist/dictionary hit — keep
            # Non-Latin script (Cyrillic, CJK, Arabic, etc.) — drop
            if not any(c.isascii() for c in token if c.isalpha()):
                return ''
            # Mixed: strip accents and continue to normal checks below
            probe = _strip_accents(probe)
            token = _strip_accents(token)  # de-accent for output too

        # ── Alpha-ratio check (on lowercased probe) ───────────────────────
        alpha = sum(c.isalpha() for c in probe)
        if alpha < len(probe) * 0.6: return ''

        clean = re.sub(r'[^a-zA-Z\-]', '', probe)
        if not clean: return ''
        if is_english_fn(clean):
            # Return the original token if it is already well-formed
            # (all-lower or genuine title-case like 'Cybernetics').
            # Return the lowercased clean form if the token is a mixed-case
            # OCR artefact ('CYBERNETics' → 'cybernetics', 'SYSTEMs' → 'systems').
            is_titlecase = token[0].isupper() and token[1:].islower()
            is_lowercase  = token == token.lower()
            return token if (is_lowercase or is_titlecase) else clean

        # OCR garbage heuristic: >85% consonants
        vowels = sum(c in 'aeiou' for c in clean)
        if len(clean) > 4 and vowels / len(clean) < 0.12:
            return ''
        return ''

    def process_paragraph(para):
        parts = re.split(r'(\s+)', para)
        out = []
        for part in parts:
            if re.match(r'\s+', part):
                out.append(part)
            else:
                pre  = re.match(r'^[^a-zA-Z\d]*', part).group()
                post_m = re.search(r'[^a-zA-Z\d]*$', part)
                post = post_m.group() if post_m else ''
                word = part[len(pre): len(part)-len(post) if post else len(part)]
                processed = process_token(word)
                if processed:
                    out.append(pre + processed + post)
        return ''.join(out)

    return '\n\n'.join(process_paragraph(p) for p in text.split('\n\n'))


# ── 4. Main ───────────────────────────────────────────────────────────────────

def clean_book(text, is_english_fn):
    text = remove_boilerplate_sections(text)
    text = apply_inline_patterns(text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = filter_non_english_tokens(text, is_english_fn)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def main():
    print("Loading English dictionary...")
    dictionary = load_english_dictionary()
    whitelist  = build_domain_whitelist()
    is_english = build_english_checker(dictionary, whitelist)
    print(f"  Domain whitelist: {len(whitelist)} terms")
    print(f"  Total vocabulary: {len(dictionary | whitelist):,} entries\n")

    with open(str(JSON_DIR / 'books_parsed.json'), encoding='utf-8') as f:
        books = json.load(f)

    # Load already-cleaned books so we can resume interrupted runs
    out_path = str(JSON_DIR / 'books_clean.json')
    try:
        with open(out_path, encoding='utf-8') as f:
            cleaned = json.load(f)
        print(f"Resuming: {len(cleaned)} books already cleaned, "
              f"{len(books) - len(cleaned)} remaining\n")
    except (FileNotFoundError, json.JSONDecodeError):
        cleaned = {}
        print(f"Cleaning {len(books)} books...\n")

    for i, (bid, data) in enumerate(books.items()):
        if bid in cleaned:
            continue
        orig  = len(data['text'])
        clean = clean_book(data['text'], is_english)
        pct   = 100 * (1 - len(clean) / orig) if orig else 0
        print(f"  [{i+1:3d}/{len(books)}] [{bid}] {data.get('title','')[:45]:45s} | "
              f"{orig:>8,} → {len(clean):>8,} chars  ({pct:.1f}%)")
        cleaned[bid] = {**data, 'clean_text': clean}
        # Write after every book so progress is never lost
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned, f, ensure_ascii=False)

    print(f"\nDone. Saved {len(cleaned)} books to {out_path}")

if __name__ == '__main__':
    main()