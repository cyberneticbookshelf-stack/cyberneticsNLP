"""
train_monograph_classifier.py
──────────────────────────────
Binary classifier: monograph vs. not-monograph.

Data sources:
  - data/inputs/calibre/metadata.db  → expert labels (custom_column_5)
  - csv/books_metadata_full.csv       → features (title, author, publisher,
                                        pubdate, inclusion_stratum)
  - json/anu_primo_cache.json         → Primo resource type signal
  - json/book_styles.json             → NOT used as training labels
                                        (machine-inferred; kept separate)

Output:
  - csv/monograph_predictions.csv     → all 726 books with prediction +
                                        confidence score
  - csv/monograph_sample_positive.csv → random sample of predicted monographs
  - csv/monograph_sample_negative.csv → random sample of predicted not-monograph
  - json/monograph_classifier.json    → model metadata and feature importances

Usage:
  python3 train_monograph_classifier.py
  python3 train_monograph_classifier.py --sample-size 25  # books per class to sample
  python3 train_monograph_classifier.py --no-sample        # skip sampling step

Validation:
  Agreement rate is estimated from the random samples after Paul reviews them.
  Reviewed samples can be added to Calibre custom_column_5 and the classifier
  retrained by re-running this script.
"""
import argparse, json, pathlib, re, sqlite3, sys
import numpy as np
import pandas as pd
from collections import Counter

# ── sklearn imports ────────────────────────────────────────────────────────────
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.pipeline import Pipeline, FeatureUnion
    from sklearn.base import BaseEstimator, TransformerMixin
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import classification_report, confusion_matrix
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    import scipy.sparse as sp
except ImportError:
    sys.exit("ERROR: pip install scikit-learn pandas numpy")

ROOT    = pathlib.Path('.')
SRC     = ROOT / 'src'
CSV_DIR = ROOT / 'csv'
JSON    = ROOT / 'json'
DB_PATH = ROOT / 'data' / 'inputs' / 'calibre' / 'metadata.db'

# ── Argument parsing ───────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument('--sample-size', type=int, default=20,
                    help='Books per predicted class to sample for expert review')
parser.add_argument('--no-sample', action='store_true',
                    help='Skip random sampling step')
parser.add_argument('--seed', type=int, default=42,
                    help='Random seed for reproducibility')
args = parser.parse_args()

rng = np.random.default_rng(args.seed)

print("=" * 65)
print("MONOGRAPH BINARY CLASSIFIER")
print("=" * 65)

# ── 1. Load expert labels from Calibre metadata.db ────────────────────────────
print("\n[1] Loading expert labels from Calibre...")
if not DB_PATH.exists():
    sys.exit(f"ERROR: {DB_PATH} not found")

conn = sqlite3.connect(DB_PATH)

# custom_column_5 is comments-type: value stored in comments table linked
# to custom_column via books_custom_column_5_link
# First find the actual column id
cur = conn.execute("""
    SELECT id, label, name, datatype
    FROM custom_columns
    WHERE label LIKE '%type%' OR label LIKE '%style%' OR label LIKE '%kind%'
       OR name LIKE '%type%' OR name LIKE '%style%' OR name LIKE '%kind%'
       OR name LIKE '%publication%' OR name LIKE '%genre%'
""")
cols = cur.fetchall()
print(f"  Candidate custom columns: {cols}")

# Try to find custom_column_5 specifically
cur = conn.execute("SELECT id, label, name, datatype FROM custom_columns")
all_cols = cur.fetchall()
print(f"  All custom columns: {all_cols}")

# Explicitly target Publication Type (custom_column_5) only.
# Do NOT load other comment columns (e.g. column 4 = Theme).
# Confirmed: custom_column_5 = Publication Type, 159 entries.
expert_labels = {}
PUBLICATION_TYPE_COL = 5

try:
    cur = conn.execute(f'SELECT book, value FROM custom_column_{PUBLICATION_TYPE_COL}')
    rows = cur.fetchall()
    print(f'  Publication Type (col {PUBLICATION_TYPE_COL}): {len(rows)} entries')
    print(f'    Sample: {rows[:5]}')
    for book_id, value in rows:
        if value and str(value).strip():
            expert_labels[str(book_id)] = str(value).strip()
except Exception as e:
    sys.exit(f'ERROR reading custom_column_{PUBLICATION_TYPE_COL}: {e}')

conn.close()

print(f"\n  Expert labels loaded: {len(expert_labels)} books")
if expert_labels:
    sample_items = list(expert_labels.items())[:5]
    for bid, label in sample_items:
        print(f"    [{bid}] {label}")

if not expert_labels:
    sys.exit("ERROR: No expert labels found. Check custom column structure.")

# ── 2. Parse labels → binary monograph flag ────────────────────────────────────
print("\n[2] Parsing expert labels...")

def normalise_label(raw):
    """Sort comma-separated labels alphabetically (canonical form)."""
    parts = [p.strip().lower() for p in raw.split(',') if p.strip()]
    return ', '.join(sorted(parts))

def is_monograph(label_str):
    """True if 'monograph' appears in the label set."""
    parts = [p.strip().lower() for p in label_str.split(',')]
    return 'monograph' in parts

label_counts = Counter()
monograph_ids = set()
not_monograph_ids = set()

for bid, raw in expert_labels.items():
    norm = normalise_label(raw)
    label_counts[norm] += 1
    if is_monograph(raw):
        monograph_ids.add(bid)
    else:
        not_monograph_ids.add(bid)

print(f"  Monograph (positive):     {len(monograph_ids)}")
print(f"  Not-monograph (negative): {len(not_monograph_ids)}")
print(f"  Total labelled:           {len(expert_labels)}")
print(f"\n  Label combinations:")
for combo, n in label_counts.most_common():
    flag = '✓' if is_monograph(combo) else '✗'
    print(f"    {flag} {n:4d}  {combo}")

# ── 3. Load metadata features ──────────────────────────────────────────────────
print("\n[3] Loading metadata features...")
meta_path = CSV_DIR / 'books_metadata_full.csv'
if not meta_path.exists():
    sys.exit(f"ERROR: {meta_path} not found")

meta = pd.read_csv(meta_path, sep='\t', dtype=str).fillna('')
meta['id'] = meta['id'].astype(str)
print(f"  Metadata: {len(meta)} books, {len(meta.columns)} columns")
print(f"  Columns: {list(meta.columns)}")

# ── 4. Load Primo cache for resource type signal ───────────────────────────────
print("\n[4] Loading Primo resource type signal...")
primo_cache = {}
primo_path = JSON / 'anu_primo_cache.json'
if primo_path.exists():
    raw_primo = json.load(open(primo_path))
    for bid, data in raw_primo.items():
        if isinstance(data, dict):
            primo_cache[str(bid)] = data.get('resource_type', '')
    print(f"  Primo cache: {len(primo_cache)} entries")
else:
    print("  Primo cache not found — skipping Primo features")

# ── 4b. Load books_clean.json for heuristic text features ──────────────────────
print("\n[4b] Loading clean text for heuristic features...")
sys.path.insert(0, str(SRC))
try:
    from heuristic_features import extract_heuristics
    books_clean = {}
    bc_path = ROOT / 'json' / 'books_clean.json'
    if bc_path.exists():
        books_clean = json.load(open(bc_path))
        print(f"  books_clean.json: {len(books_clean)} books")
    else:
        print("  WARNING: books_clean.json not found — heuristic features will be zero")
    USE_HEURISTICS = True
except ImportError:
    print("  WARNING: heuristic_features.py not found — skipping text heuristics")
    USE_HEURISTICS = False
    books_clean = {}

# ── 5. Build feature matrix ────────────────────────────────────────────────────
print("\n[5] Building features...")

EDITOR_RE = re.compile(
    r'\b(?:ed\.|eds\.|edited\s+by|editor|editors)\b', re.IGNORECASE)

PROCEEDINGS_TITLE_RE = re.compile(
    r'\b(?:proceedings|conference|symposium|workshop|annual\s+meeting)\b',
    re.IGNORECASE)

HANDBOOK_TITLE_RE = re.compile(
    r'\b(?:handbook|encyclopedia|encyclopaedia|companion|reference|reader)\b',
    re.IGNORECASE)

TEXTBOOK_TITLE_RE = re.compile(
    r'\b(?:introduction\s+to|fundamentals|textbook|primer|workbook|'
    r'lecture\s+notes|course\s+in)\b', re.IGNORECASE)

def build_features(row, primo_cache):
    bid = str(row.get('id', ''))
    title = str(row.get('title', ''))
    authors = str(row.get('authors', ''))
    publisher = str(row.get('publisher', ''))
    pubdate = str(row.get('pubdate', ''))
    stratum = str(row.get('inclusion_stratum', ''))

    feats = {}

    # Title signals
    feats['title_proceedings'] = float(bool(PROCEEDINGS_TITLE_RE.search(title)))
    feats['title_handbook']    = float(bool(HANDBOOK_TITLE_RE.search(title)))
    feats['title_textbook']    = float(bool(TEXTBOOK_TITLE_RE.search(title)))

    # Author/editor signals
    n_authors = len([a for a in authors.split('&') if a.strip()]) if authors else 0
    feats['n_authors']   = min(n_authors, 10)  # cap at 10
    feats['has_editor']  = float(bool(EDITOR_RE.search(authors)))
    feats['single_author'] = float(n_authors == 1)
    feats['many_authors']  = float(n_authors >= 4)

    # Publication era
    try:
        year = int(pubdate[:4])
        feats['era_pre1990']   = float(year < 1990)
        feats['era_1990_2010'] = float(1990 <= year < 2010)
        feats['era_post2010']  = float(year >= 2010)
        feats['pub_year_norm'] = (year - 1954) / (2025 - 1954)
    except:
        feats['era_pre1990']   = 0.0
        feats['era_1990_2010'] = 0.0
        feats['era_post2010']  = 0.0
        feats['pub_year_norm'] = 0.5

    # Inclusion stratum
    feats['stratum_title_corr']  = float(stratum == 'title_corroborated')
    feats['stratum_title_only']  = float(stratum == 'title_only')
    feats['stratum_curated_kw']  = float(stratum == 'curated_keyword')
    feats['stratum_curated_pure']= float(stratum == 'curated_pure')

    # Primo resource type
    primo_type = primo_cache.get(bid, '')
    feats['primo_book']        = float(primo_type in ('book', 'books'))
    feats['primo_edited_book'] = float(primo_type == 'edited_book')
    feats['primo_proceedings'] = float(primo_type in ('proceedings',
                                                        'conference_proceeding'))
    feats['primo_found']       = float(bool(primo_type))

    # Publisher signals (trade vs academic)
    pub_lower = publisher.lower()
    feats['pub_trade'] = float(any(p in pub_lower for p in
        ['penguin', 'random house', 'harper', 'simon', 'picador',
         'vintage', 'anchor', 'bantam', 'crown', 'doubleday']))
    feats['pub_springer'] = float('springer' in pub_lower)
    feats['pub_routledge'] = float('routledge' in pub_lower)
    feats['pub_mit'] = float('mit press' in pub_lower)

    return feats

# Build feature rows (metadata + heuristic text features)
feature_rows = []
book_ids_all = []

for _, row in meta.iterrows():
    bid = str(row.get('id', ''))
    book_ids_all.append(bid)
    feats = build_features(row.to_dict(), primo_cache)
    # Add heuristic text features
    if USE_HEURISTICS:
        book = books_clean.get(bid, {})
        text = book.get('clean_text', '')
        feats.update(extract_heuristics(text))
    feature_rows.append(feats)

feature_names = list(feature_rows[0].keys())
X_all = np.array([[r[f] for f in feature_names] for r in feature_rows])
id_to_idx = {bid: i for i, bid in enumerate(book_ids_all)}

print(f"  Feature matrix: {X_all.shape[0]} books × {X_all.shape[1]} features")
print(f"  Features: {feature_names}")

# ── 5b. Merge review labels into expert_labels ────────────────────────────────
# Add labels from manual review of predicted samples (Monograph_Review.xlsx)
# These are new expert judgements — NOT machine-inferred labels
REVIEW_LABELS = {
    # From pos sample (predicted monograph):
    '1207': 'monograph',
    '1231': 'anthology',       # false positive — correctly identified anthology
    '1114': 'monograph',
    '1751': 'monograph, textbook',
    '1755': 'monograph',
    '765':  'anthology',       # false positive
    '1757': 'monograph',
    '244':  'monograph',
    '1435': 'anthology',       # false positive
    '1525': 'monograph',
    '389':  'monograph',
    '1182': 'monograph',
    '325':  'monograph',
    '1622': 'monograph',
    '1747': 'monograph',
    '1698': 'monograph',
    '1661': 'monograph',
    '1419': 'monograph',
    '1384': 'monograph',
    '368':  'monograph',
    # From neg sample (predicted not-monograph):
    '1725': 'monograph',       # false negative
    '185':  'monograph, textbook',
    '350':  'monograph',
    '1227': 'monograph',
    '762':  'monograph',
    '373':  'monograph',
    '743':  'monograph, collected works',
    '283':  'monograph, textbook',
    '1524': 'monograph',
    '1523': 'monograph',
    '1667': 'monograph',
    '259':  'monograph',
    '1715': 'monograph',
    '348':  'monograph',
    '254':  'monograph',
    '1278': 'monograph',
    '257':  'monograph',
    '1260': 'monograph',
    '1204': 'anthology',
    '445':  'monograph',
}
added = 0
for bid, label in REVIEW_LABELS.items():
    if bid not in expert_labels:
        expert_labels[bid] = label
        added += 1
print(f"  Added {added} review labels → total expert labels: {len(expert_labels)}")

# ── 6. Build training set ──────────────────────────────────────────────────────
print("\n[6] Building training set from expert labels...")
print("\n[6] Building training set from expert labels...")

train_indices = []
y_train = []

for bid, raw in expert_labels.items():
    if bid in id_to_idx:
        train_indices.append(id_to_idx[bid])
        y_train.append(1 if is_monograph(raw) else 0)
    else:
        print(f"  WARNING: labelled book {bid} not in metadata — skipping")

X_train = X_all[train_indices]
y_train = np.array(y_train)
print(f"  Training set: {len(y_train)} books")
print(f"  Positive (monograph):     {y_train.sum()}")
print(f"  Negative (not-monograph): {(y_train == 0).sum()}")

# ── 7. Cross-validated evaluation ─────────────────────────────────────────────
print("\n[7] Cross-validated evaluation (5-fold stratified)...")

clf = LogisticRegression(
    class_weight='balanced',
    C=1.0,
    max_iter=1000,
    random_state=args.seed
)

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=args.seed)
y_cv_pred = cross_val_predict(clf, X_train, y_train, cv=skf)
y_cv_prob = cross_val_predict(clf, X_train, y_train, cv=skf, method='predict_proba')

print("\n  Cross-validated agreement with expert labels:")
print(classification_report(y_train, y_cv_pred,
                             target_names=['not-monograph', 'monograph']))
print("  Confusion matrix (rows=expert, cols=predicted):")
cm = confusion_matrix(y_train, y_cv_pred)
print(f"    {'':15s} pred-not  pred-mono")
print(f"    {'expert-not':15s} {cm[0,0]:8d}  {cm[0,1]:8d}")
print(f"    {'expert-mono':15s} {cm[1,0]:8d}  {cm[1,1]:8d}")

# ── 8. Train final model on all labelled data ──────────────────────────────────
print("\n[8] Training final model on all expert-labelled books...")
clf.fit(X_train, y_train)

# Feature importance (logistic regression coefficients)
coef = clf.coef_[0]
importance = sorted(zip(feature_names, coef), key=lambda x: abs(x[1]), reverse=True)
print("\n  Top features by importance:")
for fname, fcoef in importance[:10]:
    direction = '→ monograph' if fcoef > 0 else '→ not-mono'
    print(f"    {fcoef:+.3f}  {fname:<30s} {direction}")

# ── 9. Predict all books ───────────────────────────────────────────────────────
print("\n[9] Predicting all 726 books...")
probs = clf.predict_proba(X_all)[:, 1]  # P(monograph)
THRESHOLD = 0.4  # lowered from 0.5 — recovers monographs with Springer/Routledge publishers
preds = (probs >= THRESHOLD).astype(int)

# Build output dataframe
titles = dict(zip(meta['id'].astype(str), meta.get('title', meta.iloc[:,1])))
authors_map = dict(zip(meta['id'].astype(str), meta.get('authors', '')))
pubdate_map = dict(zip(meta['id'].astype(str), meta.get('pubdate', '')))

results = []
for i, bid in enumerate(book_ids_all):
    in_training = bid in {str(b) for b in expert_labels.keys()}
    expert = expert_labels.get(bid, '')
    results.append({
        'id': bid,
        'title': titles.get(bid, ''),
        'authors': authors_map.get(bid, ''),
        'pubdate': pubdate_map.get(bid, ''),
        'expert_label': expert,
        'in_training': in_training,
        'pred_monograph': int(preds[i]),
        'prob_monograph': round(float(probs[i]), 4),
        'confidence': round(abs(float(probs[i]) - 0.5) * 2, 4),  # 0=uncertain, 1=certain
    })

df = pd.DataFrame(results)
out_path = CSV_DIR / 'monograph_predictions.csv'
df.to_csv(out_path, index=False, sep='\t')
print(f"  Saved: {out_path}")

# Summary
unlabelled = df[~df['in_training']]
print(f"\n  Unlabelled books: {len(unlabelled)}")
print(f"    Predicted monograph:     {(unlabelled['pred_monograph']==1).sum()}")
print(f"    Predicted not-monograph: {(unlabelled['pred_monograph']==0).sum()}")
print(f"    Low confidence (<0.5):   {(unlabelled['confidence']<0.5).sum()}")

# ── 10. Random sampling for expert review ──────────────────────────────────────
if not args.no_sample:
    print(f"\n[10] Random sampling {args.sample_size} books per class for review...")
    np.random.seed(args.seed)

    for label_val, label_name, fname in [
        (1, 'monograph',     'monograph_sample_positive.csv'),
        (0, 'not-monograph', 'monograph_sample_negative.csv'),
    ]:
        pool = unlabelled[unlabelled['pred_monograph'] == label_val].copy()
        n = min(args.sample_size, len(pool))
        sample = pool.sample(n=n, random_state=args.seed)
        sample = sample.sort_values('confidence', ascending=True)  # uncertain first
        out = CSV_DIR / fname
        sample[['id','title','authors','pubdate','prob_monograph',
                'confidence','expert_label']].to_csv(out, index=False, sep='\t')
        print(f"  Saved {n} {label_name} samples → {out}")
        print(f"    (sorted by confidence ascending — least certain first)")

# ── 11. Save model metadata ────────────────────────────────────────────────────
model_meta = {
    'date': '2026-04-07',
    'model': 'LogisticRegression',
    'class_weight': 'balanced',
    'C': 1.0,
    'threshold': 0.4,
    'seed': args.seed,
    'n_training': int(len(y_train)),
    'n_positive': int(y_train.sum()),
    'n_negative': int((y_train == 0).sum()),
    'features': feature_names,
    'feature_importance': {f: round(float(c), 4) for f, c in importance},
    'cv_folds': 5,
    'note': (
        'Labels are expert judgements (Paul Wong), not ground truth. '
        'Agreement rate estimated from random sample review. '
        'Machine-inferred book_styles.json labels were NOT used as training data.'
    ),
}
meta_out = JSON / 'monograph_classifier.json'
json.dump(model_meta, open(meta_out, 'w'), indent=2)
print(f"\n  Saved model metadata → {meta_out}")

print("\n" + "=" * 65)
print("DONE")
print("=" * 65)
print(f"\nNext steps:")
print(f"  1. Review csv/monograph_sample_positive.csv ({args.sample_size} books)")
print(f"     — these were predicted monograph; are they?")
print(f"  2. Review csv/monograph_sample_negative.csv ({args.sample_size} books)")
print(f"     — these were predicted not-monograph; do you agree?")
print(f"  3. Add disagreements to Calibre custom_column_5")
print(f"  4. Re-run this script to retrain with expanded expert labels")
print(f"  5. Agreement rate = (correct in sample) / {args.sample_size} per class")
