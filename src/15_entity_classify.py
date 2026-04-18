"""
15_entity_classify.py
────────────────────────────────────────────────────────────────────────────
Classifies all index vocabulary terms into entity kinds using a two-stage
NER pipeline:

  Stage 1 — Heuristics (instant, no dependencies)
    Suppresses noise, detects persons by name pattern, moves tech companies
    to organisations, removes book/work titles (Title (Author) pattern),
    removes ALL_CAPS encyclopedia headings.

  Stage 2 — spaCy en_core_web_sm (local, offline, ~500 terms/sec)
    Classifies remaining terms using spaCy's NER:
    PERSON → person | ORG → organisation | GPE/LOC → location
    WORK_OF_ART → suppress | NORP/EVENT → concept | no entity → concept

  Stage 3 — Wikidata REST API (for terms spaCy marks uncertain, ~3 req/sec)
    Queries wikidata.org for P31 (instance of) to disambiguate proper nouns
    that spaCy couldn't resolve confidently. Results are cached permanently.

Output: json/entity_types_cache.json
  {term_lower: {"kind": "person"|"organisation"|"location"|"concept"|"suppress",
                "source": "heuristic"|"spacy"|"wikidata"|"default",
                "label": original_term, "confidence": 0.0-1.0}}

Usage:
  python3 src/15_entity_classify.py               # full pipeline
  python3 src/15_entity_classify.py --no-wikidata # skip Wikidata (offline mode)
  python3 src/15_entity_classify.py --refresh     # discard cache, reclassify all

Run this once before 14_entity_network.py. Re-run when the index grows
significantly or when classification errors are found.
"""

import json, re, sys, os, time
from pathlib import Path
from collections import defaultdict

import pathlib as _pl
CSV_DIR  = _pl.Path('csv')
JSON_DIR = _pl.Path('json')
JSON_DIR.mkdir(exist_ok=True)

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here) if os.path.basename(_here) == 'src' else _here
os.chdir(_root)

NO_WIKIDATA = '--no-wikidata' in sys.argv
REFRESH     = '--refresh'     in sys.argv
MIN_BOOKS   = 3

CACHE_PATH = JSON_DIR / 'entity_types_cache.json'

# ── Load existing cache ───────────────────────────────────────────────────────
cache = {}
if CACHE_PATH.exists() and not REFRESH:
    try:
        cache = json.loads(CACHE_PATH.read_text())
        print(f"Loaded cache: {len(cache):,} entries")
    except Exception:
        cache = {}

# ── Load index vocabulary ─────────────────────────────────────────────────────
with open(str(JSON_DIR / 'index_analysis.json')) as f: IA = json.load(f)
vocab = {tl: v for tl, v in IA['vocab'].items() if v['n_books'] >= MIN_BOOKS}
print(f"Index terms to classify (n_books≥{MIN_BOOKS}): {len(vocab):,}")

# ── Stage 1: Heuristics ───────────────────────────────────────────────────────
print("\n── Stage 1: Heuristics ──────────────────────────────────────────────────────")

PERSON_PAT = re.compile(
    r'^[A-Z][\w\-]+(?:\s+[A-Z][\w\-]+)*,\s'
    r'|^(?:von|de|van|der|du|al)\s+[A-Z]',
    re.UNICODE)

KNOWN_SINGLE_PERSONS = {
    'aristotle','plato','socrates','pythagoras','heraclitus','democritus',
    'archimedes','epicurus','thales','anaximander','anaximenes','empedocles',
    'parmenides','zeno','hippocrates','euclid','ptolemy','diogenes','plotinus',
    'averroes','avicenna','aquinas','paracelsus','copernicus','galileo','kepler',
    'descartes','spinoza','leibniz','newton','locke','hume','kant','hegel',
    'schopenhauer','nietzsche','marx','engels','freud','jung','darwin',
    'lamarck','malthus','einstein','bohr','heisenberg','schrodinger',
    'wittgenstein','husserl','heidegger','sartre','lacan','derrida',
}

ORG_PAT = re.compile(
    r'\b(University|College|Institute|Laboratory|Labs?|Foundation|'
    r'Corporation|School|Academy|Center|Centre|Association|Press|'
    r'Media Lab|RAND|Caltech|MIT|NSF|NASA|DARPA|BBC|CIA|FBI)\b',
    re.IGNORECASE)

# Curated tech companies/platforms missed by ORG_PAT
KNOWN_TECH_ORGS = {
    'google','facebook','amazon','microsoft','apple inc','twitter','instagram',
    'netflix','tesla','uber','airbnb','openai','deepmind','general electric',
    'general motors','ford motor','boeing','lockheed','westinghouse','at&t',
    'att','bell telephone','pentagon','arpanet','darpa','architecture machine group',
    'deepsea challenge','parc','xerox parc','bell labs','ge',
    'ibm','nsa','cia','fbi','nasa','mit press','rand corporation','rand',
    'abc','nbc','cbs','cnn','youtube','whatsapp','snapchat','linkedin',
    'dropbox','salesforce','oracle','intel','amd','nvidia','qualcomm',
}

GEO_PAT = re.compile(
    r'\b(Soviet Union|Germany|France|Britain|England|Japan|China|India|'
    r'America|Europe|Russia|Australia|Canada|Italy|Spain|Brazil|Mexico|'
    r'Africa|Asia|London|New York|Cambridge|Chicago|Paris|Berlin|Vienna|'
    r'Tokyo|Moscow|Beijing|Amsterdam|Copenhagen|Brussels|California|'
    r'Massachusetts|Edinburgh|Toronto|Budapest|Silicon Valley|'
    r'Latin America|Middle East|South America|North America|Great Britain|'
    r'United States|United Kingdom|New Zealand|South Africa|Hong Kong)\b',
    re.IGNORECASE)

# Book/work titles: "Word Word (Author)" or "Word, The (Author)"
WORK_TITLE_PAT = re.compile(
    r'\(([A-Z][a-z]+(?:\s+and\s+[A-Z][a-z]+)?'
    r'|[A-Z][a-z]+,\s+[A-Z][a-z]+'
    r'|[A-Z][a-z]+\s+[A-Z][a-z]+)\)$')

# ALL_CAPS encyclopedia headings
ALL_CAPS_PAT = re.compile(r'^[A-Z][A-Z\s\-&/]{5,}$')

# Garbled/long author-affiliation strings
# Index sub-entry fragments (start with preposition / conjunction)
_FUNC_START = re.compile(
    r'^(of|with|in|on|at|to|for|by|from|and|or|but|as|if|it|is|'
    r'its|this|that)\b', re.IGNORECASE)

# Bare book/work titles: curated list without parenthetical author
BARE_BOOK_TITLES = {
    'steps to an ecology of mind', 'design for a brain',
    'an introduction to cybernetics', 'understanding media',
    'the medium is the massage', 'being digital', 'out of control',
    'silent spring', 'the selfish gene', 'the blind watchmaker',
    "the emperor's new mind", 'the society of mind',
    'the architecture of complexity', 'the age of spiritual machines',
    'godel escher bach', 'gödel escher bach', 'the systems bible',
    'the whole earth catalog', 'the structure of scientific revolutions',
    'the concept of mind', 'beyond freedom and dignity',
    'plans and the structure of behavior', 'mind and nature',
    'the cybernetic brain', 'brain of the firm',
    'platform for change', 'heart of enterprise', 'the living brain',
    'perceptrons', 'steps to ecology',
}

def is_noise(tl, term):
    if len(term) < 3: return True
    if ALL_CAPS_PAT.match(term): return True
    if len(term) > 60 and term.count(',') >= 2: return True
    if tl.lower() in {'index','and','or','the','a','an','of','for',
                      'see','also','but','nor','etc','vs','ie','eg'}: return True
    if re.match(r'^[^a-zA-Z]*$', term): return True
    # Index sub-entry fragments: start with preposition/conjunction
    if _FUNC_START.match(term) and len(term.split()) <= 6: return True
    return False

h_counts = defaultdict(int)
needs_ner = []

for tl, v in vocab.items():
    if tl in cache and not REFRESH:
        continue  # already classified

    term = v['term']

    if is_noise(tl, term):
        cache[tl] = {'kind':'suppress','source':'heuristic',
                     'label':term,'confidence':1.0}
        h_counts['suppress'] += 1
    elif WORK_TITLE_PAT.search(term) or tl.lower() in BARE_BOOK_TITLES:
        cache[tl] = {'kind':'suppress','source':'heuristic',
                     'label':term,'confidence':1.0,
                     'note':'work_title'}
        h_counts['suppress_work'] += 1
    # Article-led titles ≥4 words: 'The Mathematical Theory of...'
    elif (re.match(r'^(The|An|A)\s+[A-Z]', term, re.IGNORECASE)
          and len(term.split()) >= 4):
        cache[tl] = {'kind':'suppress','source':'heuristic',
                     'label':term,'confidence':0.85,
                     'note':'article_title'}
        h_counts['suppress_article'] += 1
    elif PERSON_PAT.match(term) or tl.lower() in KNOWN_SINGLE_PERSONS:
        cache[tl] = {'kind':'person','source':'heuristic',
                     'label':term,'confidence':1.0}
        h_counts['person'] += 1
    elif ORG_PAT.search(term) or tl.lower().strip() in KNOWN_TECH_ORGS:
        cache[tl] = {'kind':'organisation','source':'heuristic',
                     'label':term,'confidence':1.0}
        h_counts['organisation'] += 1
    elif GEO_PAT.search(term):
        cache[tl] = {'kind':'location','source':'heuristic',
                     'label':term,'confidence':1.0}
        h_counts['location'] += 1
    else:
        needs_ner.append((tl, term, v['n_books']))

for kind, count in sorted(h_counts.items()):
    print(f"  {kind:20s}: {count:4d}")
print(f"  {'needs_ner':20s}: {len(needs_ner):4d}")

# --- Manual corrections (post-audit overrides) ---
# Applied after all heuristics so they survive --refresh.
MANUAL_CORRECTIONS = {
    **{t: ("suppress","noise") for t in [
        "a. n.","arnold","lee","john","james","frank","michael","paul",
        "richard","simon","taylor","max","miller","david","edward",
        "williams","brown","xiii","guattari)","heinz","oes","der",
        "omt","templates","schizophrenia and",
    ]},
    "whole earth catalog":("suppress","work_title"),
    "understanding media (mcluhan)":("suppress","work_title"),
    "blade runner (film)":("suppress","work_title"),
    "tractatus logico-philosophicus":("suppress","work_title"),
    "m.s. swaminathan, first world food prize winner":("suppress","noise"),
    "environmental structure and function: climate system - volume":("suppress","noise"),
    "environmental structure and function: climate system – volume":("suppress","noise"),
    "digital":("concept",""),    "general systems theory":("concept",""),
    "renaissance":("concept",""),"transistors":("concept",""),
    "homeostat":("concept",""),  "automata":("concept",""),
    "radio":("concept",""),      "cyborg":("concept",""),
    "social systems":("concept",""), "chatgpt":("concept",""),
    "macy conferences":("concept",""),
    "macy conferences on cybernetics":("suppress","duplicate of macy conferences [96]"),
    "second-order":("concept",""),"theorem":("concept",""),
    "quantum mechanics":("concept",""),"quantum theory":("concept",""),
    "rna":("concept",""),       "syntax":("concept",""),
    "trace":("concept",""),     "universal turing machine":("concept",""),
    "quantum":("concept",""),   "chemical":("concept",""),
    "channel":("concept",""),   "neuron":("concept",""),
    "navigation":("concept",""),"punch cards":("concept",""),
    "telegraph":("concept",""), "android":("concept",""),
    "postmodern":("concept",""),"eskimos":("concept",""),
    "islam":("concept",""),
    "test for the controlled variable (tcv)":("concept",""),
    "schizophrenia":("concept",""), "problem solving":("concept",""),
    "symbolic":("concept",""),   "metadata":("concept",""),
    "oxygen":("concept",""),     "jacquard loom":("concept",""),
    "apple macintosh":("concept",""),"cloud computing":("concept",""),
    "deep blue":("concept",""),  "reader":("concept",""),
    "differential analyzer":("concept",""),
    "project cybersyn":("concept",""),"cybersyn project":("concept",""),
    "cybersyn":("concept",""),   "covid-19":("concept",""),
    "dasein":("concept",""),     "formula":("concept",""),
    "tetrahedron":("concept",""),"trolley problem":("concept",""),
    "markov chain":("concept",""),"monte carlo method":("concept",""),
    "wholes":("concept",""),     "mitochondria":("concept",""),
    "vasopressin":("concept",""),"superego":("concept",""),
    "reflex arc":("concept",""), "tacit knowledge":("concept",""),
    "techne":("concept",""),     "zeno's paradox":("concept",""),
    "electroencephalography (eeg)":("concept",""),"apps":("concept",""),
    "stelarc":("person",""),     "napoleon":("person",""),
    "le corbusier":("person",""),"maxwell":("person",""),
    "whitehead":("person",""),   "vitruvius":("person",""),
    "merry pranksters":("organisation",""),"ted":("organisation",""),
    "archigram":("organisation",""),
    "encyclopedia britannica":("organisation",""),
    "viet cong":("organisation",""),"wiley":("organisation",""),
    "pink floyd":("organisation",""),
    "kingsley hall":("location",""),

    # ── Comprehensive misclassification fixes — 18 April 2026 (KI-07) ─────────
    # Full-corpus node review: ~130 misclassified nodes corrected.
    # These entries also live in entity_types_cache.json but that file is
    # gitignored. Keeping them here guarantees they survive cache rebuilds
    # (including --refresh) and are applied before spaCy/Wikidata can
    # re-introduce the wrong classification.

    # location → organisation
    "new york times":          ("organisation","newspaper"),
    "san francisco chronicle": ("organisation","newspaper"),
    "vienna circle":           ("organisation","philosophical group/movement"),

    # location/organisation → concept (historical programmes/events misread by spaCy as ORG/LOC)
    "marshall plan":     ("concept","historical economic programme"),
    "manhattan project": ("concept","historical programme/event"),
    "perceptron":        ("concept","ML model/concept"),
    "big bang":          ("concept","cosmological event/concept"),
    "hippocampus":       ("concept","anatomical concept"),
    "algorithm":         ("concept","CS concept"),
    "truth":             ("concept","philosophical concept"),
    "weltanschauung":    ("concept","worldview concept"),

    # location → suppress
    "systém":   ("suppress","OCR artefact — Czech word for system"),
    "tortoise": ("suppress","too ambiguous at network level"),
    "ai and":   ("suppress","trailing-function-word fragment"),

    # organisation → person
    "lorente de nó, rafael": ("person","neuroanatomist"),
    "cicero":                ("person","Roman orator/philosopher"),
    "st. augustine":         ("person","theologian/philosopher"),
    "epictetus":             ("person","Stoic philosopher"),
    "rutherford":            ("person","Ernest Rutherford, physicist"),

    # organisation → concept
    "principia mathematica":      ("concept","foundational work in mathematical logic"),
    "design for a brain":         ("concept","Ashby book title used as concept in discourse"),
    "quantum computing":          ("concept",""),
    "social sciences":            ("concept",""),
    "synergy":                    ("concept",""),
    "actor-network theory (ant)": ("concept",""),
    "brain":                      ("concept","anatomical structure/concept"),
    "neurotransmitters":          ("concept",""),
    "retina":                     ("concept","anatomical concept"),
    "slavery":                    ("concept","social/historical concept"),
    "synthesis":                  ("concept",""),
    "quantum entanglement":       ("concept",""),
    "speech":                     ("concept",""),
    "healthcare":                 ("concept",""),
    "recognition":                ("concept",""),
    "neo-darwinism":              ("concept",""),
    "aesthetic":                  ("concept",""),
    "phenomenon":                 ("concept",""),
    "complex adaptive systems":   ("concept",""),
    "digital communication":      ("concept",""),
    "knowledge-based systems":    ("concept",""),
    "quantum physics":            ("concept",""),
    "habit":                      ("concept",""),
    "digital media":              ("concept",""),
    "venture capital":            ("concept",""),
    "linear programming":         ("concept",""),
    "digital computer":           ("concept",""),
    "signal":                     ("concept","information/communication concept"),
    "sequence":                   ("concept","mathematical/biological concept"),

    # organisation → suppress (generic nouns / fragments / ambiguous)
    "laboratory":    ("suppress","generic noun — many distinct labs in corpus"),
    "university)":   ("suppress","malformed fragment — stray closing paren"),
    "self-":         ("suppress","truncated fragment"),
    "linear":        ("suppress","bare adjective"),
    "epistemological":("suppress","bare adjective"),
    "trajectories":  ("suppress","generic noun"),
    "corporation":   ("suppress","generic noun"),
    "women":         ("suppress","generic noun — too broad for entity network"),
    "force":         ("suppress","generic noun"),
    "school":        ("suppress","generic noun"),
    "phenomena":     ("suppress","generic noun"),
    "frequency":     ("suppress","generic noun"),
    "wages":         ("suppress","generic noun"),
    "institute":     ("suppress","generic noun"),
    "decline":       ("suppress","generic noun"),
    "ace":           ("suppress","too short / ambiguous"),
    "stickleback":   ("suppress","animal species; too specific for network"),
    "health care":   ("suppress","duplicate of healthcare"),
    "bishop":        ("suppress","too ambiguous — multiple Bishops in corpus"),
    "press":         ("suppress","generic publisher abbreviation"),
    "oxford":        ("location","city/university location"),

    # concept → person
    "voltaire":  ("person",""),
    "homer":     ("person","ancient Greek poet"),
    "sophocles": ("person","ancient Greek playwright"),
    "bernard":   ("person","Claude Bernard, physiologist"),

    # concept → organisation
    "life magazine":         ("organisation","publication"),
    "coevolution quarterly": ("organisation","publication by Stewart Brand"),
    "ramparts":              ("organisation","political magazine"),

    # concept → suppress (duplicates / standalone name fragments)
    "galileo galilei": ("suppress","duplicate of galileo in person list"),
    "stengers":        ("suppress","duplicate of stengers, isabelle in person list"),
    "wiener":          ("suppress","first-name-absent fragment; canonical is wiener, norbert"),

    # person → suppress (noise / fragments / address strings / duplicates)
    "drop":    ("suppress","random word"),
    "norbert": ("suppress","first-name-only fragment (Norbert Wiener)"),
    "one park avenue, new york, ny":
               ("suppress","publisher address string"),
    "growing field with applications to many disciplines. frank george":
               ("suppress","sentence fragment with embedded person name"),
    "enlightenment, the":
               ("suppress","variant of Enlightenment concept — duplicate"),
    "weiner, norbert": ("suppress","misspelling — canonical is wiener, norbert"),
    "clark":           ("suppress","surname only; ambiguous"),
    "humphreys":       ("suppress","surname only; ambiguous"),

    # person → concept
    "grammar":      ("concept","linguistic concept"),

    # person → suppress (index sub-entry comma form — not a standalone entity)
    "brain, human": ("suppress","index sub-entry fragment"),

    # person → organisation
    "whole earth catalog, the":             ("organisation","publication by Stewart Brand"),
    "gordon and breach science publishers": ("organisation","publisher"),

    # person → location
    "new york, ny":          ("location",""),
    "cambridge, massachusetts": ("location",""),

    # suppress duplicates (name-order variants and surname-only forms)
    "foerster, heinz von": ("suppress","duplicate of von foerster, heinz"),
    "neumann, john von":   ("suppress","duplicate of von neumann, john"),
    "kluckhohn":           ("suppress","duplicate of kluckhohn, clyde in person list"),
    "von bertalanffy":     ("suppress","duplicate of bertalanffy, ludwig von in person list"),
    "vinge":               ("suppress","duplicate of vinge, vernor in person list"),
    "waddington":          ("suppress","duplicate of waddington, conrad hal in person list"),

    # trailing-function-word fragments (belt-and-suspenders: _TRAILING_FUNC in
    # 14_entity_network.py catches these at runtime; cache entries here ensure
    # they are suppressed even if 14 is run without the code fix)
    "free will and": ("suppress","trailing-function-word fragment"),

    # ── Misclassified singular/plural pairs — 18 April 2026 ──────────────────
    # spaCy NER misclassifies the singular or plural form; correct both.
    # Singular/plural variants that share the same kind are handled separately
    # by the plural-dedup note in CLAUDE.md (future structural fix in 14).

    # spaCy → org, correct: concept
    "node":       ("concept","spaCy misclassified as org; plural 'nodes' already concept"),
    "objectives": ("concept","spaCy misclassified as org; singular 'objective' already concept"),
    "subsystem":  ("concept","spaCy misclassified as org; plural 'subsystems' already concept"),
    "viewpoint":  ("concept","spaCy misclassified as org; plural 'viewpoints' already concept"),

    # spaCy → location, correct: concept
    "schemas":  ("concept","spaCy misclassified as location; singular 'schema' already concept"),
    "symbol":   ("concept","spaCy misclassified as location; plural 'symbols' already concept"),
    "theorems": ("concept","spaCy misclassified as location; singular 'theorem' already concept"),

    # ── Back-matter / function-word fragments — 18 April 2026 ────────────────
    # Belt-and-suspenders: _CTA_BACK_MATTER in 14 catches "about the authors?"
    # at runtime; this entry ensures suppression if 14 is run without the fix.
    "about the authors": ("suppress","back-matter string"),
    "about the author":  ("suppress","back-matter string"),
    "not":               ("suppress","function word — spaCy false positive"),

    # ── Duplicate concept forms — 18 April 2026 ───────────────────────────────
    # Suppress the less canonical surface form; keep the more standard one.
    "requisite variety, law of": ("suppress","variant — canonical is 'law of requisite variety'"),

    # ── Plural dedup (targeted) — 18 April 2026 ──────────────────────────────
    # perceptron/perceptrons flagged in network review. Suppress plural to
    # consolidate PMI signal on the canonical form. Broader plural-dedup
    # (normalisation step in 14) deferred as a structural sprint item.
    "perceptrons": ("suppress","plural variant — canonical is 'perceptron'"),
    # ── Degree 1–2 concept node review — 18 April 2026 (fifth batch) ─────────
    # 89 suppressions confirmed after full review of all 294 degree 1–2 concept
    # nodes. Categories: bare adjectives, too-generic nouns, noise/irrelevant
    # terms, near-duplicates of higher-degree canonical nodes.

    # Bare adjectives (spaCy false positives — no entity, just a modifier)
    "capitalist":   ("suppress","bare adjective"),
    "generative":   ("suppress","bare adjective"),
    "regulatory":   ("suppress","bare adjective"),
    "sexual":       ("suppress","bare adjective"),
    "concrete":     ("suppress","bare adjective"),
    "embodied":     ("suppress","bare adjective"),
    "passive":      ("suppress","bare adjective"),
    "conscious":    ("suppress","bare adjective"),
    "closed":       ("suppress","bare adjective"),
    "logical":      ("suppress","bare adjective"),
    "statistical":  ("suppress","bare adjective"),
    "industrial":   ("suppress","bare adjective"),
    "physical":     ("suppress","bare adjective"),
    "scientific":   ("suppress","bare adjective"),
    "natural":      ("suppress","bare adjective"),
    "cybernetic":   ("suppress","bare adjective"),
    "procedural":   ("suppress","bare adjective"),

    # Noise / irrelevant (appear in corpus but not meaningful network nodes)
    "scaffolding":     ("suppress","noise/irrelevant"),
    "branding":        ("suppress","noise/irrelevant"),
    "quoted":          ("suppress","noise/irrelevant"),
    "her (film)":      ("suppress","noise/irrelevant"),
    "containerization":("suppress","noise/irrelevant"),
    "methane":         ("suppress","noise/irrelevant"),
    "mediatization":   ("suppress","noise/irrelevant"),
    "abiogenesis":     ("suppress","noise/irrelevant"),
    "newspapers":      ("suppress","noise/irrelevant"),
    "monotheism":      ("suppress","noise/irrelevant"),
    "arts":            ("suppress","noise/irrelevant"),
    "facilitation":    ("suppress","noise/irrelevant"),
    "atheism":         ("suppress","noise/irrelevant"),
    "astronautics":    ("suppress","noise/irrelevant"),
    "teledildonics":   ("suppress","noise/irrelevant"),
    "rats":            ("suppress","noise/irrelevant"),
    "chimpanzees":     ("suppress","noise/irrelevant"),
    "success":         ("suppress","noise/irrelevant"),
    "happiness":       ("suppress","noise/irrelevant"),
    "street":          ("suppress","noise/irrelevant"),
    "content":         ("suppress","noise/irrelevant"),
    "hurricanes":      ("suppress","noise/irrelevant"),
    "maintenance":     ("suppress","noise/irrelevant"),
    "individual":      ("suppress","noise/irrelevant"),
    "quality":         ("suppress","noise/irrelevant"),
    "group":           ("suppress","noise/irrelevant"),
    "networking":      ("suppress","noise/irrelevant"),
    "compuserve":      ("suppress","noise/irrelevant — early internet service, not a concept"),

    # Too generic (valid English words but no discriminating power in this network)
    "organisation":  ("suppress","too generic — use specific org names"),
    "signals":       ("suppress","too generic — use 'signal'"),
    "image":         ("suppress","too generic"),
    "integration":   ("suppress","too generic"),
    "methods":       ("suppress","too generic"),
    "performance":   ("suppress","too generic"),
    "law":           ("suppress","too generic — use specific law names"),
    "values":        ("suppress","too generic"),
    "production":    ("suppress","too generic"),
    "writing":       ("suppress","too generic"),
    "observation":   ("suppress","too generic"),
    "revolution":    ("suppress","too generic — use specific revolutions"),
    "action":        ("suppress","too generic"),
    "world":         ("suppress","too generic"),
    "analysis":      ("suppress","too generic"),
    "machine":       ("suppress","too generic"),
    "processes":     ("suppress","too generic"),
    "thinking":      ("suppress","too generic"),
    "management":    ("suppress","too generic"),
    "model":         ("suppress","too generic"),
    "simulation":    ("suppress","too generic"),
    "definition":    ("suppress","too generic"),
    "mechanisms":    ("suppress","too generic"),
    "direction":     ("suppress","too generic"),
    "capital":       ("suppress","too generic"),
    "reconstruction":("suppress","too generic"),
    "connectivity":  ("suppress","too generic"),
    "images":        ("suppress","too generic"),
    "studies":       ("suppress","too generic"),
    "change":        ("suppress","too generic"),
    "pattern":       ("suppress","too generic"),
    "purpose":       ("suppress","too generic"),
    "regulation":    ("suppress","too generic"),
    "universal":     ("suppress","too generic — bare adjective / abstract noun"),
    "behavior":      ("suppress","too generic"),
    "development":   ("suppress","too generic"),

    # Near-duplicates (lower-degree variant; canonical higher-degree node retained)
    "cybernetic systems": ("suppress","near-duplicate — canonical is 'cybernetics'"),
    "complex systems":    ("suppress","near-duplicate — canonical is 'complexity'"),
    "decision making":    ("suppress","near-duplicate — canonical is 'decision-making'"),
    "thermostats":        ("suppress","near-duplicate — canonical is 'thermostat'"),
    "requisite variety":  ("suppress","near-duplicate — canonical is 'law of requisite variety'"),
    "computer":           ("suppress","near-duplicate — canonical is 'computers'"),
}

for _tl, (_kind, _note) in MANUAL_CORRECTIONS.items():
    if _tl in vocab:
        cache[_tl] = {"kind": _kind, "source": "manual",
                      "label": vocab[_tl]["term"], "confidence": 1.0,
                      **({"note": _note} if _note else {})}
        h_counts["manual_" + _kind] += 1

# ── Stage 2: spaCy NER ────────────────────────────────────────────────────────
print("\n── Stage 2: spaCy NER ───────────────────────────────────────────────────────")

spacy_uncertain = []   # → send to Wikidata

try:
    import spacy
    try:
        nlp = spacy.load('en_core_web_sm')
        print(f"  Model: en_core_web_sm  Terms to classify: {len(needs_ner):,}")

        # spaCy label → our kind
        SPACY_MAP = {
            'PERSON':      ('person',       1.0),
            'ORG':         ('organisation', 0.85),
            'GPE':         ('location',     0.9),
            'LOC':         ('location',     0.9),
            'FACILITY':    ('location',     0.8),
            'WORK_OF_ART': ('suppress',     0.85),
            'PRODUCT':     ('organisation', 0.7),
            'EVENT':       ('concept',      0.8),
            'NORP':        ('concept',      0.8),  # nationalities/movements
            'LAW':         ('concept',      0.8),
            'LANGUAGE':    ('concept',      0.8),
        }
        UNCERTAIN_THRESHOLD = 0.75  # below this → send to Wikidata

        for tl, term, nb in needs_ner:
            # Manual corrections take absolute precedence — never overwrite them,
            # even on --refresh runs (needs_ner is built before MANUAL_CORRECTIONS
            # runs, so manual entries can end up in both cache and needs_ner).
            if cache.get(tl, {}).get('source') == 'manual':
                continue
            doc = nlp(term)
            if doc.ents:
                ent = doc.ents[0]
                mapped = SPACY_MAP.get(ent.label_)
                if mapped:
                    kind, conf = mapped
                    if conf >= UNCERTAIN_THRESHOLD:
                        cache[tl] = {'kind': kind, 'source': 'spacy',
                                     'label': term, 'confidence': conf,
                                     'spacy_label': ent.label_}
                    else:
                        spacy_uncertain.append((tl, term, nb, ent.label_))
                else:
                    # Unknown label → uncertain
                    spacy_uncertain.append((tl, term, nb, ent.label_))
            else:
                # No entity detected → almost certainly a genuine concept
                cache[tl] = {'kind': 'concept', 'source': 'spacy',
                             'label': term, 'confidence': 0.9}

        spacy_counts = defaultdict(int)
        for entry in cache.values():
            if entry['source'] == 'spacy':
                spacy_counts[entry['kind']] += 1
        for kind, count in sorted(spacy_counts.items()):
            print(f"  {kind:20s}: {count:4d}")
        print(f"  {'uncertain→Wikidata':20s}: {len(spacy_uncertain):4d}")

    except OSError:
        print("  en_core_web_sm not installed.")
        print("  Run: python3 -m spacy download en_core_web_sm")
        print("  Skipping spaCy — all remaining terms go to Wikidata or default.")
        spacy_uncertain = needs_ner  # send all to Wikidata

except ImportError:
    print("  spaCy not installed.")
    print("  Run: pip install spacy && python3 -m spacy download en_core_web_sm")
    spacy_uncertain = needs_ner

# ── Stage 3: Wikidata API ─────────────────────────────────────────────────────
print("\n── Stage 3: Wikidata API ────────────────────────────────────────────────────")

# P31 (instance of) Q-code → our kind
# Covers the most common Wikidata entity types
WIKIDATA_KIND_MAP = {
    # Persons
    'Q5':        'person',       # human
    'Q215627':   'person',       # person (non-human fictional etc — keep as person)
    # Organisations
    'Q4830453':  'organisation', # business
    'Q783794':   'organisation', # company
    'Q43229':    'organisation', # organization
    'Q2659904':  'organisation', # government agency
    'Q327333':   'organisation', # government body
    'Q3918':     'organisation', # university
    'Q31855':    'organisation', # research institute
    'Q7075':     'organisation', # library
    'Q16917':    'organisation', # hospital
    'Q180958':   'organisation', # think tank
    'Q484652':   'organisation', # international organisation
    'Q1664720':  'organisation', # institute
    # Locations
    'Q6256':     'location',     # country
    'Q515':      'location',     # city
    'Q1549591':  'location',     # big city
    'Q3957':     'location',     # town
    'Q35657':    'location',     # US state
    'Q7275':     'location',     # republic
    'Q82794':    'location',     # geographic region
    'Q2221906':  'location',     # geographic region (alt)
    'Q23397':    'location',     # lake
    'Q4022':     'location',     # river
    # Works
    'Q571':      'suppress',     # book
    'Q7725634':  'suppress',     # literary work
    'Q47461344': 'suppress',     # written work
    'Q11424':    'suppress',     # film
    'Q134556':   'suppress',     # single (music)
    'Q482994':   'suppress',     # album
    # Concepts / movements (keep as concepts)
    'Q132241':   'concept',      # festival
    'Q49773':    'concept',      # social movement
    'Q12284':    'concept',      # political movement
    'Q2198779':  'concept',      # movement (general)
    'Q15709879': 'concept',      # artistic movement
    'Q20826013': 'concept',      # scientific theory
    'Q11862829': 'concept',      # academic discipline
}

def wikidata_lookup(term):
    """
    Query Wikidata for entity type. Returns (kind, confidence, qid) or None.
    Raises on network error so caller can handle gracefully.
    """
    import urllib.request, urllib.parse

    # Search
    search_url = (
        'https://www.wikidata.org/w/api.php?action=wbsearchentities'
        f'&search={urllib.parse.quote(term)}&language=en&limit=1&format=json'
    )
    with urllib.request.urlopen(search_url, timeout=8) as r:
        results = json.loads(r.read()).get('search', [])
    if not results:
        return None

    qid  = results[0]['id']
    desc = results[0].get('description', '')

    # Get P31
    entity_url = (
        f'https://www.wikidata.org/w/api.php?action=wbgetentities'
        f'&ids={qid}&props=claims&format=json'
    )
    with urllib.request.urlopen(entity_url, timeout=8) as r:
        edata = json.loads(r.read())

    p31_claims = (edata.get('entities', {})
                       .get(qid, {})
                       .get('claims', {})
                       .get('P31', []))
    type_qids = [
        c.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id')
        for c in p31_claims[:5]
    ]
    type_qids = [q for q in type_qids if q]

    for qid_type in type_qids:
        if qid_type in WIKIDATA_KIND_MAP:
            return WIKIDATA_KIND_MAP[qid_type], 0.9, qid

    return None  # couldn't resolve

if NO_WIKIDATA:
    print("  Skipped (--no-wikidata)")
    for tl, term, *_ in spacy_uncertain:
        if tl not in cache:
            cache[tl] = {'kind':'concept','source':'default',
                         'label':term,'confidence':0.5}
else:
    uncertain_new = [(tl, term, nb, *rest)
                     for tl, term, nb, *rest in spacy_uncertain
                     if tl not in cache]
    print(f"  Terms to query: {len(uncertain_new):,}  (rate: 2 req/sec)")

    wikidata_counts = defaultdict(int)
    errors = 0

    for idx, row in enumerate(uncertain_new):
        tl, term = row[0], row[1]
        # Strip parenthetical for lookup
        lookup_term = re.sub(r'\s*\([^)]+\)\s*$', '', term).strip()
        try:
            result = wikidata_lookup(lookup_term)
            if result:
                kind, conf, qid = result
                cache[tl] = {'kind': kind, 'source': 'wikidata',
                             'label': term, 'confidence': conf, 'qid': qid}
            else:
                cache[tl] = {'kind': 'concept', 'source': 'wikidata_notfound',
                             'label': term, 'confidence': 0.6}
            wikidata_counts[cache[tl]['kind']] += 1
        except Exception as e:
            errors += 1
            cache[tl] = {'kind': 'concept', 'source': 'default',
                         'label': term, 'confidence': 0.5}
            if errors <= 3:
                print(f"  ⚠ Wikidata error for '{term}': {e}")

        # Rate limiting — 2 req/sec (search + entity = 2 calls per term)
        time.sleep(0.5)

        # Progress
        if (idx + 1) % 50 == 0 or idx == len(uncertain_new) - 1:
            pct = (idx + 1) / max(len(uncertain_new), 1) * 100
            print(f"  {idx+1:4d}/{len(uncertain_new):4d} ({pct:.0f}%)  "
                  f"errors={errors}", end='\r')

    if uncertain_new:
        print()
    for kind, count in sorted(wikidata_counts.items()):
        print(f"  {kind:20s}: {count:4d}  (from Wikidata)")
    if errors:
        print(f"  {errors} terms fell back to 'concept' due to network errors")

# ── Remaining: default to concept ─────────────────────────────────────────────
for tl, v in vocab.items():
    if tl not in cache:
        cache[tl] = {'kind': 'concept', 'source': 'default',
                     'label': v['term'], 'confidence': 0.5}

# ── Save cache ────────────────────────────────────────────────────────────────
CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=1))
print(f"\nSaved: {CACHE_PATH}  ({len(cache):,} entries)")

# ── Summary ───────────────────────────────────────────────────────────────────
final = defaultdict(int)
by_source = defaultdict(int)
for entry in cache.values():
    final[entry['kind']] += 1
    by_source[entry['source']] += 1

print("\n── Classification summary ───────────────────────────────────────────────────")
for kind, count in sorted(final.items(), key=lambda x: -x[1]):
    print(f"  {kind:20s}: {count:5d}")
print("\nBy source:")
for src, count in sorted(by_source.items(), key=lambda x: -x[1]):
    print(f"  {src:20s}: {count:5d}")
