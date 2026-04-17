import json, numpy as np, pandas as pd


# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_metadata_full.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


with open(str(JSON_DIR / 'nlp_results.json')) as f: R = json.load(f)
with open(str(JSON_DIR / 'summaries.json')) as f: S = json.load(f)
with open(str(JSON_DIR / 'books_clean.json')) as f: B = json.load(f)

book_ids = R['book_ids']
doc_topic = np.array(R['doc_topic'])

# Sheet 1: Master results
rows = []
for i, bid in enumerate(book_ids):
    if bid not in S:  # skip OCR failures excluded from generate_summaries_api
        continue
    s = S[bid]
    kp = R['keyphrases'].get(bid, [])
    row = {
        'Book ID': bid,
        'Title': s['title'],
        'Author': s['author'],
        'Pub Year': B[bid].get('pubdate',''),
        'Dominant Topic': f"Topic {R['dominant_topics'][i]+1}",
        'Cluster': f"Cluster {R['cluster_labels'][i]+1}",
        'Key Phrases': '; '.join(kp[:8]),
    }
    for t in range(R['n_topics']):
        row[f'Topic {t+1} Score'] = round(doc_topic[i, t], 4)
    row['Top Topic Words'] = ', '.join(R['top_words'][R['dominant_topics'][i]][:8])
    row['Summary - Descriptive'] = s.get('descriptive','')
    row['Summary - Argumentative'] = s.get('argumentative','')
    row['Summary - Critical'] = s.get('critical','')
    rows.append(row)

df_main = pd.DataFrame(rows)

# Sheet 2: Topics
topic_rows = []
for t, words in enumerate(R['top_words']):
    docs = [R['titles'][i] for i, d in enumerate(R['dominant_topics']) if d == t]
    topic_rows.append({
        'Topic': f'Topic {t+1}',
        'Top Keywords': ', '.join(words[:12]),
        'Assigned Documents': len(docs),
        'Book Titles': '; '.join(docs)
    })
df_topics = pd.DataFrame(topic_rows)

# Sheet 3: Perplexity
df_perp = pd.DataFrame([{'N Topics': int(k), 'Perplexity': round(v,2)} 
                         for k, v in sorted(R['perplexities'].items(), key=lambda x:int(x[0]))])
df_perp['Optimal'] = df_perp['N Topics'] == R['n_topics']

# Sheet 4: Clusters
cluster_rows = []
for c in range(R['best_k']):
    docs = [R['titles'][i] for i, cl in enumerate(R['cluster_labels']) if cl == c]
    cluster_rows.append({'Cluster': f'Cluster {c+1}', 'Size': len(docs), 'Books': '; '.join(docs)})
df_clusters = pd.DataFrame(cluster_rows)

# Sheet 5: Cosine similarity
cos_df = pd.DataFrame(np.array(R['cos_sim']).round(4),
                      index=[f"[{bid}] {R['titles'][i][:30]}" for i,bid in enumerate(book_ids)],
                      columns=[f"[{bid}] {R['titles'][i][:30]}" for i,bid in enumerate(book_ids)])

# Write Excel
out = 'data/outputs/book_nlp_results.xlsx'
with pd.ExcelWriter(out, engine='openpyxl') as writer:
    df_main.to_excel(writer, sheet_name='Master Results', index=False)
    df_topics.to_excel(writer, sheet_name='LDA Topics', index=False)
    df_perp.to_excel(writer, sheet_name='Perplexity Scores', index=False)
    df_clusters.to_excel(writer, sheet_name='Clusters', index=False)
    cos_df.to_excel(writer, sheet_name='Cosine Similarity')

print(f"Excel saved: {out}")