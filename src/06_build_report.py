"""


06_build_report.py  —  Book-level HTML report with interactive Plotly charts.

Static PNGs are kept for the LDA perplexity, K-Means elbow, topic-word
heatmap, and keyphrases figures.  Four charts are replaced with interactive
Plotly.js equivalents (requires internet connection to load Plotly from CDN):
  • 2D scatter  — hover for title/author/topic/cluster, filter dropdowns
  • Cosine similarity heatmap — hover for book pair + score
  • (Topic distribution stacked bar is also interactive via Plotly)

Input:  nlp_results.json, summaries.json, books_clean.json, figures/fig*.png
Output: data/outputs/book_nlp_analysis.html
"""

# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_metadata_full.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


import json, base64, re
import numpy as np

# Generic verbs and filler words that slip through TF-IDF keyphrase extraction
_KP_BLOCKLIST = {
    # Generic verbs
    'give', 'gives', 'given', 'take', 'takes', 'taken', 'make', 'makes', 'made',
    'come', 'comes', 'came', 'seem', 'seems', 'seemed', 'need', 'needs', 'needed',
    'know', 'knows', 'knew', 'think', 'thinks', 'thought', 'want', 'wants', 'wanted',
    'call', 'called', 'become', 'becomes', 'became', 'keep', 'keeps', 'kept',
    'show', 'shows', 'showed', 'turn', 'turns', 'turned', 'leave', 'leaves', 'left',
    'move', 'moves', 'moved', 'must',
    # Generic nouns / adjectives
    'back', 'still', 'around', 'past', 'example', 'something', 'great', 'thing', 'things',
    'page', 'pages', 'good', 'best', 'better', 'true', 'large', 'small', 'possible',
    'general', 'certain',
    # Google Books digitization artefacts
    'google', 'digitize', 'digitized', 'digitised', 'original', 'california',
}

def _clean_kp(kp_list):
    # Filter any phrase that contains a blocklisted word, and drop duplicate-word phrases
    out = []
    for k in kp_list:
        words = k.split()
        if any(w in _KP_BLOCKLIST for w in words):
            continue
        if len(words) > 1 and len(set(words)) < len(words):  # e.g. "page page"
            continue
        out.append(k)
    return out

with open(str(JSON_DIR / 'nlp_results.json'))   as f: R     = json.load(f)
with open(str(JSON_DIR / 'summaries.json'))     as f: S     = json.load(f)
with open(str(JSON_DIR / 'books_clean.json'))   as f: books = json.load(f)

book_ids       = R['book_ids']
cluster_labels = R['cluster_labels']
best_k         = R['best_k']
doc_topic      = np.array(R['doc_topic'])
dominant       = R['dominant_topics']
n_topics       = R['n_topics']
_LDA_BASE = [
    'Management Cybernetics',
    'Second-Order Cybernetics Applied to Social Systems',
    'Dynamical Systems, Homeostasis & Biological Regulation',
    'Psychological Cybernetics',
    'Non-Anglophone Engineering Cybernetics',
    'Mathematical Foundations of Cybernetics',
    'Cultural Cybernetics, Posthumanism & Digital Media',
    'Applied Cybernetics & Computers in Society',
    'Residual / Outlier Cluster',
]
_carried = R.get('topic_names') or _LDA_BASE
LDA_NAMES = (_carried + [f'Topic {i+1}' for i in range(len(_carried), n_topics)])[:n_topics]
coords_2d      = R.get('coords_2d', [[0,0]]*len(book_ids))
cos_sim        = R['cos_sim']
titles_short   = [t[:40]+'…' if len(t)>40 else t for t in R['titles']]

PALETTE = ['#2563eb','#16a34a','#dc2626','#d97706','#7c3aed',
           '#0891b2','#be185d','#0f766e','#c2410c','#065f46','#9333ea','#0369a1']

def img_b64(path):
    with open(path,'rb') as f:
        return 'data:image/png;base64,' + base64.b64encode(f.read()).decode()

imgs = {k: img_b64(f'figures/fig{i+1}_{k}.png') for i,k in enumerate(
    ['lda_perplexity','topic_word_heatmap','doc_topic_dist',
     'kmeans_elbow','cosine_heatmap','cluster_scatter','keyphrases'])}

# ── Topic table ───────────────────────────────────────────────────────────────
topic_rows = ''
for t, words in enumerate(R['top_words']):
    docs = [R['titles'][i][:40] for i,d in enumerate(dominant) if d==t]
    col  = PALETTE[t % len(PALETTE)]
    name = LDA_NAMES[t] if t < len(LDA_NAMES) else f'Topic {t+1}'
    topic_rows += f"""
    <tr>
      <td><span class="badge" style="background:{col}">T{t+1}</span></td>
      <td><strong>{name}</strong></td>
      <td>{', '.join(words[:8])}</td>
      <td>{len(docs)}</td>
      <td style="font-size:.8em">{'; '.join(docs[:5])}{'…' if len(docs)>5 else ''}</td>
    </tr>"""

# ── Cluster table ─────────────────────────────────────────────────────────────
cluster_rows = ''
for c in range(best_k):
    docs = [R['titles'][i][:48] for i,cl in enumerate(cluster_labels) if cl==c]
    col  = PALETTE[c % len(PALETTE)]
    cluster_rows += f"""
    <tr>
      <td><span class="badge" style="background:{col}">{c+1}</span></td>
      <td>{len(docs)}</td>
      <td style="font-size:.8em">{'; '.join(docs)}</td>
    </tr>"""

# ── Book cards ────────────────────────────────────────────────────────────────
def chapter_accordion(bid):
    chs = S[bid].get('chapters', [])
    if not chs: return '<p style="color:#64748b;font-size:.85em">No chapter data.</p>'
    items = ''
    for ch in chs:
        wc   = ch.get('word_count', 0)
        summ = ch.get('summary','').strip() or '<em>No summary available.</em>'
        items += f"""
        <div class="acc-item">
          <button class="acc-btn" onclick="toggleAcc(this)">
            <span class="ch-num">Ch {ch['index']}</span>
            <span class="ch-title">{ch['title'][:70]}{'…' if len(ch['title'])>70 else ''}</span>
            <span class="ch-wc">{wc:,} words</span>
            <span class="acc-arrow">▼</span>
          </button>
          <div class="acc-body">{summ}</div>
        </div>"""
    return f'<div class="accordion">{items}</div>'

book_cards = ''
# Exclude books without summaries (e.g. OCR failures excluded from generate_summaries_api)
book_ids = [bid for bid in book_ids if bid in S]
for bid in book_ids:
    sv  = S[bid]
    c   = cluster_labels[book_ids.index(bid)]
    t   = dominant[book_ids.index(bid)]
    kp  = _clean_kp(R['keyphrases'].get(bid, []))
    col = PALETTE[c % len(PALETTE)]
    tcol= PALETTE[t % len(PALETTE)]
    book_cards += f"""
<div class="book-card" id="book-{bid}">
  <div class="book-header" style="border-left:5px solid {col}">
    <div>
      <div class="book-title">{sv['title']}</div>
      <div class="book-meta">
        ✍️ {sv['author']} &nbsp;|&nbsp;
        <span class="badge" style="background:{tcol}">{LDA_NAMES[t] if t < len(LDA_NAMES) else 'Topic ' + str(t+1)}</span>
        <span class="badge" style="background:{col}">Cluster {c+1}</span>
        <span class="ch-count-badge">{sv['n_chapters']} chapters</span>
      </div>
    </div>
  </div>
  <div class="book-body">
    <div class="keyphrases">{''.join(f'<span class="kp">{k}</span>' for k in kp[:8])}</div>
    <div class="section-label">📖 Whole-Book Summary</div>
    <div class="summary-tabs">
      <div class="tab-btns">
        <button class="tab-btn active" onclick="showTab(this,'desc-{bid}')">📋 Descriptive</button>
        <button class="tab-btn" onclick="showTab(this,'arg-{bid}')">💡 Argumentative</button>
        <button class="tab-btn" onclick="showTab(this,'crit-{bid}')">🔍 Critical</button>
      </div>
      <div id="desc-{bid}" class="tab-content active">{sv.get('descriptive','N/A')}</div>
      <div id="arg-{bid}"  class="tab-content">{sv.get('argumentative','N/A')}</div>
      <div id="crit-{bid}" class="tab-content">{sv.get('critical','N/A')}</div>
    </div>
    <div class="section-label" style="margin-top:1rem">📑 Chapter Summaries</div>
    {chapter_accordion(bid)}
  </div>
</div>"""

# ── Perplexity pills ──────────────────────────────────────────────────────────
perp_pills = ''.join(
    f'<div class="perp-card{"  best" if str(k)==str(n_topics) else ""}">'
    f'<span>{round(v,0):.0f}</span>'
    f'<small>k={k}{"  ✓" if str(k)==str(n_topics) else ""}</small></div>'
    for k,v in sorted(R['perplexities'].items(), key=lambda x:int(x[0])))

# ── Plotly data ───────────────────────────────────────────────────────────────
scatter_data = json.dumps({
    'x':        [c[0] for c in coords_2d],
    'y':        [c[1] for c in coords_2d],
    'titles':   R['titles'],
    'authors':  R['authors'],
    'topics':   dominant,
    'clusters': cluster_labels,
    'n_topics': n_topics,
    'best_k':   best_k,
    'palette':  PALETTE,
    'lda_names': LDA_NAMES,
})

# Cosine sim — round to 3dp to reduce JSON size
cos_rounded = [[round(v,3) for v in row] for row in cos_sim]
# Sort by cluster for better visual grouping
sort_idx = sorted(range(len(cluster_labels)), key=lambda i: cluster_labels[i])
cos_sorted  = [[cos_rounded[i][j] for j in sort_idx] for i in sort_idx]
labs_sorted = [titles_short[i] for i in sort_idx]
cosine_data = json.dumps({'z': cos_sorted, 'labels': labs_sorted})

# Topic distribution data for stacked bar
topic_dist_data = json.dumps({
    'titles':    [t[:35] for t in R['titles']],
    'doc_topic': doc_topic.tolist(),
    'dominant':  dominant,
    'n_topics':  n_topics,
    'palette':   PALETTE,
    'lda_names': LDA_NAMES,
})

# Keyphrases data
kp_data = json.dumps({
    'book_ids': book_ids,
    'titles':   R['titles'],
    'authors':  R['authors'],
    'topics':   dominant,
    'clusters': cluster_labels,
    'keyphrases': {bid: _clean_kp(R['keyphrases'].get(bid,[])) for bid in book_ids},
    'n_topics': n_topics,
    'best_k':   best_k,
})

# ── Assemble HTML ─────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Book Corpus NLP Analysis</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.27.0/plotly.min.js"></script>
<style>
:root{{--blue:#2563eb;--green:#16a34a;--red:#dc2626;--bg:#f8fafc;--card:#fff;--border:#e2e8f0}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:#1e293b;line-height:1.6}}
.header{{background:linear-gradient(135deg,#1e3a5f,#2563eb);color:#fff;padding:2.5rem 2rem;text-align:center}}
.header h1{{font-size:1.9rem;font-weight:700;margin-bottom:.4rem}}
.stats-bar{{display:flex;justify-content:center;gap:2rem;background:#1e293b;color:#fff;padding:.8rem;flex-wrap:wrap}}
.stat{{text-align:center}}.stat span{{display:block;font-size:1.4rem;font-weight:700;color:#60a5fa}}
.stat small{{font-size:.75rem;opacity:.7;text-transform:uppercase}}
nav{{background:#fff;border-bottom:1px solid var(--border);padding:.6rem 1.5rem;position:sticky;top:0;z-index:99;display:flex;gap:1rem;flex-wrap:wrap}}
nav a{{text-decoration:none;color:#475569;font-size:.85rem;padding:.3rem .7rem;border-radius:4px;transition:all .2s}}
nav a:hover{{background:#eff6ff;color:var(--blue)}}
.container{{max-width:1400px;margin:0 auto;padding:1.5rem}}
section{{margin-bottom:3rem}}
h2{{font-size:1.35rem;font-weight:700;color:#1e293b;margin-bottom:1rem;padding-bottom:.5rem;border-bottom:2px solid var(--blue)}}
h3{{font-size:1.05rem;font-weight:600;color:#334155;margin:.8rem 0}}
.fig{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:1rem;margin-bottom:1.2rem;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.fig img{{width:100%;border-radius:4px}}
.fig-caption{{font-size:.8rem;color:#64748b;margin-top:.5rem;text-align:center}}
.plotly-chart{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:1rem;margin-bottom:1.2rem;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.chart-controls{{display:flex;gap:.6rem;flex-wrap:wrap;margin-bottom:.6rem;align-items:center}}
.chart-controls label{{font-size:.82rem;color:#475569;font-weight:500}}
.chart-controls select{{padding:.3rem .6rem;border:1px solid var(--border);border-radius:5px;font-size:.82rem;background:#fff;color:#1e293b}}
table{{width:100%;border-collapse:collapse;background:var(--card);border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
th{{background:#1e3a5f;color:#fff;padding:.7rem 1rem;text-align:left;font-size:.85rem;font-weight:600}}
td{{padding:.6rem 1rem;border-bottom:1px solid var(--border);font-size:.85rem;vertical-align:top}}
tr:hover td{{background:#f1f5f9}}
.badge{{display:inline-block;color:#fff;padding:.15rem .6rem;border-radius:9999px;font-size:.75rem;font-weight:600;margin:.1rem}}
.ch-count-badge{{display:inline-block;background:#e2e8f0;color:#475569;padding:.15rem .6rem;border-radius:9999px;font-size:.75rem;margin:.1rem}}
.book-card{{background:var(--card);border:1px solid var(--border);border-radius:10px;margin-bottom:1.4rem;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.07)}}
.book-header{{padding:1rem 1.2rem}}
.book-title{{font-weight:700;font-size:.95rem;color:#0f172a;margin-bottom:.3rem}}
.book-meta{{font-size:.8rem;color:#64748b}}
.book-body{{padding:.8rem 1.2rem 1.2rem}}
.keyphrases{{margin-bottom:.8rem}}
.kp{{display:inline-block;background:#eff6ff;color:#2563eb;border:1px solid #bfdbfe;border-radius:4px;padding:.15rem .5rem;font-size:.75rem;margin:.2rem .15rem}}
.section-label{{font-weight:600;font-size:.85rem;color:#475569;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem}}
.tab-btns{{display:flex;gap:.4rem;margin-bottom:.7rem;flex-wrap:wrap}}
.tab-btn{{padding:.3rem .8rem;border:1px solid var(--border);background:#f8fafc;border-radius:5px;cursor:pointer;font-size:.8rem;color:#475569;transition:all .2s}}
.tab-btn.active{{background:var(--blue);color:#fff;border-color:var(--blue)}}
.tab-content{{display:none;font-size:.85rem;color:#334155;line-height:1.7;background:#f8fafc;padding:.8rem;border-radius:6px;border:1px solid var(--border)}}
.tab-content.active{{display:block}}
.accordion{{border:1px solid var(--border);border-radius:8px;overflow:hidden;margin-top:.3rem}}
.acc-item{{border-bottom:1px solid var(--border)}}.acc-item:last-child{{border-bottom:none}}
.acc-btn{{width:100%;display:flex;align-items:center;gap:.6rem;padding:.6rem 1rem;background:#f8fafc;border:none;cursor:pointer;text-align:left;transition:background .15s}}
.acc-btn:hover,.acc-btn.open{{background:#eff6ff}}
.ch-num{{font-size:.75rem;font-weight:700;color:#fff;background:#94a3b8;padding:.1rem .45rem;border-radius:4px;white-space:nowrap;min-width:2.8rem;text-align:center}}
.ch-title{{flex:1;font-size:.83rem;font-weight:600;color:#1e293b}}
.ch-wc{{font-size:.75rem;color:#94a3b8;white-space:nowrap}}
.acc-arrow{{font-size:.7rem;color:#94a3b8;transition:transform .2s}}
.acc-btn.open .acc-arrow{{transform:rotate(180deg)}}
.acc-body{{display:none;padding:.7rem 1rem;font-size:.83rem;color:#334155;line-height:1.7;background:#fff;border-top:1px solid var(--border)}}
.acc-body.open{{display:block}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:1rem}}
.perp-table{{display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:1rem}}
.perp-card{{background:#fff;border:1px solid var(--border);border-radius:8px;padding:.8rem 1.2rem;text-align:center;min-width:90px}}
.perp-card span{{display:block;font-size:1.3rem;font-weight:700;color:var(--blue)}}
.perp-card.best{{border-color:var(--green);background:#f0fdf4}}.perp-card.best span{{color:var(--green)}}
.perp-card small{{font-size:.75rem;color:#64748b}}
.kp-search{{padding:.4rem .8rem;border:1px solid var(--border);border-radius:5px;font-size:.85rem;width:260px}}
.kp-table{{width:100%;border-collapse:collapse;font-size:.83rem}}
.kp-table th{{background:#1e3a5f;color:#fff;padding:.5rem .8rem;text-align:left}}
.kp-table td{{padding:.45rem .8rem;border-bottom:1px solid var(--border);vertical-align:top}}
.kp-table tr:hover td{{background:#f1f5f9}}
@media(max-width:700px){{.grid2{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="header">
  <h1>📚 Book Corpus NLP Analysis</h1>
  <p>Topic Modelling · Summarisation · Key Phrase Extraction · Clustering · Interactive Visualisation</p>
</div>
<div class="stats-bar">
  <div class="stat"><span>{len(book_ids)}</span><small>Books</small></div>
  <div class="stat"><span>{n_topics}</span><small>LDA Topics</small></div>
  <div class="stat"><span>{best_k}</span><small>Clusters</small></div>
  <div class="stat"><span>{sum(S[b]['n_chapters'] for b in book_ids)}</span><small>Chapters</small></div>
</div>
<nav>
  <a href="#topics">📊 Topics</a>
  <a href="#scatter">🗺 Scatter</a>
  <a href="#clusters">🗂 Clusters</a>
  <a href="#cosine">🔗 Similarity</a>
  <a href="#keyphrases">🔑 Keyphrases</a>
  <a href="#summaries">📝 Summaries</a>
</nav>
<div class="container">

<section id="topics">
  <h2>1 · Topic Modelling (LDA, k={n_topics})</h2>
  <p style="margin-bottom:1rem;color:#475569;font-size:.9rem">Optimal k={n_topics} by lowest perplexity ({round(R['perplexities'][str(n_topics)],1)}).</p>
  <div class="perp-table">{perp_pills}</div>
  <div class="grid2">
    <div class="fig"><img src="{imgs['lda_perplexity']}" alt="perplexity">
      <div class="fig-caption">Fig 1 — Perplexity curve</div></div>
    <div class="fig"><img src="{imgs['kmeans_elbow']}" alt="elbow">
      <div class="fig-caption">Fig 4 — K-Means elbow + silhouette</div></div>
  </div>
  <div class="fig"><img src="{imgs['topic_word_heatmap']}" alt="topic-word">
    <div class="fig-caption">Fig 2 — Topic–word heatmap</div></div>

  <div class="plotly-chart">
    <div class="chart-controls">
      <label>Colour by topic, filter to books where dominant topic is:</label>
      <select id="td_filter" onchange="updateTopicDist()">
        <option value="-1">All books</option>
      </select>
      <label style="margin-left:.8rem">Sort by:</label>
      <select id="td_sort" onchange="updateTopicDist()">
        <option value="dom">Dominant topic</option>
        <option value="title">Title</option>
      </select>
    </div>
    <div id="topic_bar_chart"></div>
    <div class="fig-caption">Fig 3 — Per-document topic proportions. Hover for exact values. Filter to a single dominant topic to reduce density.</div>
  </div>

  <h3>Topic Summaries</h3>
  <table><thead><tr><th>#</th><th>Name</th><th>Top Keywords</th><th>Docs</th><th>Books (sample)</th></tr></thead>
  <tbody>{topic_rows}</tbody></table>
</section>

<section id="scatter">
  <h2>2 · 2D Cluster Scatter (interactive)</h2>
  <div class="plotly-chart">
    <div class="chart-controls">
      <label>Colour by:</label>
      <select id="scatter_colour" onchange="updateScatter()">
        <option value="topic">Topic</option>
        <option value="cluster">Cluster</option>
      </select>
      <label style="margin-left:.8rem">Filter:</label>
      <select id="scatter_filter" onchange="updateScatter()">
        <option value="all">All</option>
      </select>
    </div>
    <div id="scatter_chart"></div>
    <div class="fig-caption">LSA 2D projection — hover for title, author, topic &amp; cluster</div>
  </div>
</section>

<section id="clusters">
  <h2>3 · Clusters</h2>
  <table><thead><tr><th>Cluster</th><th>Books</th><th>Titles</th></tr></thead>
  <tbody>{cluster_rows}</tbody></table>
</section>

<section id="cosine">
  <h2>4 · Cosine Similarity (interactive heatmap)</h2>
  <div class="plotly-chart">
    <div class="chart-controls">
      <label>Show top N most similar pairs:</label>
      <select id="cosine_mode" onchange="updateCosine()">
        <option value="heatmap">Full heatmap (sorted by cluster)</option>
        <option value="top50">Top 50 pairs table</option>
      </select>
    </div>
    <div id="cosine_chart"></div>
    <div class="fig-caption">Hover for book names and similarity score</div>
  </div>
</section>

<section id="keyphrases">
  <h2>5 · Key Phrases (searchable)</h2>
  <div class="plotly-chart">
    <div class="chart-controls">
      <input class="kp-search" id="kp_search" type="text" placeholder="Search titles or keyphrases…" oninput="filterKP()">
      <label style="margin-left:.8rem">Topic:</label>
      <select id="kp_topic" onchange="filterKP()"><option value="all">All</option></select>
      <label style="margin-left:.5rem">Cluster:</label>
      <select id="kp_cluster" onchange="filterKP()"><option value="all">All</option></select>
    </div>
    <div id="kp_count" style="font-size:.82rem;color:#64748b;margin-bottom:.4rem"></div>
    <table class="kp-table" id="kp_table">
      <thead><tr><th>Book</th><th>Author</th><th>Topic</th><th>Cluster</th><th>Key Phrases</th></tr></thead>
      <tbody id="kp_tbody"></tbody>
    </table>
  </div>
</section>

<section id="summaries">
  <h2>6 · Book Summaries</h2>
  <p style="margin-bottom:1.2rem;color:#475569;font-size:.9rem">
    Toggle summary style · expand chapters to see per-chapter summaries.
  </p>
  {book_cards}
</section>

</div>
<footer style="text-align:center;padding:1.5rem;color:#94a3b8;font-size:.8rem;border-top:1px solid var(--border);margin-top:2rem">
  Book NLP Pipeline · LDA + TF-IDF + K-Means · Interactive charts via Plotly.js
</footer>

<script>
// ── Data ──────────────────────────────────────────────────────────────────────
const SD = {scatter_data};
const CD = {cosine_data};
const TD = {topic_dist_data};
const KD = {kp_data};
const PALETTE = {json.dumps(PALETTE)};

// ── Interactive scatter ───────────────────────────────────────────────────────
function buildScatterTraces(colourBy, filterVal) {{
  const n = filterVal === 'all' ? SD.n_topics : (colourBy === 'topic' ? SD.n_topics : SD.best_k);
  const groupKey = colourBy === 'topic' ? SD.topics : SD.clusters;
  const traces = [];
  for (let g = 0; g < (colourBy === 'topic' ? SD.n_topics : SD.best_k); g++) {{
    if (filterVal !== 'all' && String(g) !== String(filterVal)) continue;
    const idx = groupKey.map((v,i) => v===g ? i : -1).filter(i=>i>=0);
    traces.push({{
      x: idx.map(i => SD.x[i]), y: idx.map(i => SD.y[i]),
      mode: 'markers', type: 'scatter', name: colourBy==='topic' ? (SD.lda_names?SD.lda_names[g]:`Topic ${{g+1}}`) : `Cluster ${{g+1}}`,
      marker: {{ color: PALETTE[g % PALETTE.length], size: 8, opacity: 0.8,
                 line: {{color:'white', width:0.5}} }},
      text: idx.map(i => `<b>${{SD.titles[i].substring(0,50)}}</b><br>${{SD.authors[i]}}<br>Topic ${{SD.topics[i]+1}} · Cluster ${{SD.clusters[i]+1}}`),
      hovertemplate: '%{{text}}<extra></extra>'
    }});
  }}
  return traces;
}}

function populateScatterFilter() {{
  const mode = document.getElementById('scatter_colour').value;
  const sel  = document.getElementById('scatter_filter');
  const n = mode === 'topic' ? SD.n_topics : SD.best_k;
  sel.innerHTML = '<option value="all">All</option>' +
    Array.from({{length:n}},(_,i)=>`<option value="${{i}}">${{mode==='topic'?(SD.lda_names?SD.lda_names[i]:'Topic '+(i+1)):'Cluster '+(i+1)}}</option>`).join('');
}}

function updateScatter() {{
  populateScatterFilter();
  const mode   = document.getElementById('scatter_colour').value;
  const filter = document.getElementById('scatter_filter').value;
  const traces = buildScatterTraces(mode, filter);
  Plotly.react('scatter_chart', traces, {{
    height: 520, margin: {{t:20,b:60,l:60,r:20}},
    xaxis: {{title:'LSA Dimension 1', zeroline:false}},
    yaxis: {{title:'LSA Dimension 2', zeroline:false}},
    legend: {{orientation:'v'}},
    paper_bgcolor:'transparent', plot_bgcolor:'#f8fafc',
    hoverlabel: {{bgcolor:'#1e293b', font:{{color:'white', size:12}}}}
  }});
}}
populateScatterFilter();
updateScatter();

// ── Topic distribution bar (horizontal, filterable) ──────────────────────────
(function(){{
  const sel = document.getElementById('td_filter');
  for(let t=0;t<TD.n_topics;t++){{
    const o=document.createElement('option');
    o.value=t; o.textContent=TD.lda_names?TD.lda_names[t]:`Topic ${{t+1}}`;
    sel.appendChild(o);
  }}
}})();

function updateTopicDist(){{
  const filterTopic = +document.getElementById('td_filter').value;
  const sortMode    = document.getElementById('td_sort').value;

  // Build index list, optionally filtered to dominant topic
  let idx = TD.doc_topic.map((_,i)=>i);
  if(filterTopic >= 0){{
    idx = idx.filter(i => TD.dominant[i] === filterTopic);
  }}

  // Sort
  if(sortMode === 'dom'){{
    idx.sort((a,b)=>{{
      const da=TD.dominant[a], db=TD.dominant[b];
      if(da!==db) return da-db;
      return TD.doc_topic[b][da]-TD.doc_topic[a][da];
    }});
  }} else {{
    idx.sort((a,b)=>TD.titles[a].localeCompare(TD.titles[b]));
  }}

  const labels = idx.map(i=>TD.titles[i].length>45?TD.titles[i].substring(0,45)+'…':TD.titles[i]);
  const traces = [];
  for(let t=0;t<TD.n_topics;t++){{
    const tnm = TD.lda_names?TD.lda_names[t]:`Topic ${{t+1}}`;
    traces.push({{
      x: idx.map(i=>+TD.doc_topic[i][t].toFixed(3)),
      y: labels,
      type:'bar', orientation:'h', name:tnm,
      marker:{{color:PALETTE[t%PALETTE.length]}},
      hovertemplate:`<b>%{{y}}</b><br>${{tnm}}: %{{x:.1%}}<extra></extra>`,
    }});
  }}

  const h = Math.max(300, idx.length * 18 + 100);
  Plotly.react('topic_bar_chart', traces, {{
    barmode:'stack', height:h,
    margin:{{t:10,b:60,l:300,r:20}},
    xaxis:{{title:'Topic proportion', tickformat:'.0%', range:[0,1]}},
    yaxis:{{autorange:'reversed', tickfont:{{size:9}}}},
    legend:{{orientation:'h', y:-0.1, font:{{size:10}}}},
    paper_bgcolor:'transparent', plot_bgcolor:'#f8fafc',
    hoverlabel:{{bgcolor:'#1e293b',font:{{color:'white',size:12}}}},
  }});
}}
updateTopicDist();

// ── Cosine similarity heatmap ─────────────────────────────────────────────────
let cosineMode = 'heatmap';
function updateCosine() {{
  cosineMode = document.getElementById('cosine_mode').value;
  if (cosineMode === 'heatmap') {{
    Plotly.react('cosine_chart', [{{
      z: CD.z, x: CD.labels, y: CD.labels,
      type: 'heatmap', colorscale: 'Blues', zmin:0, zmax:1,
      hovertemplate: '<b>%{{y}}</b><br>vs<br><b>%{{x}}</b><br>Similarity: %{{z:.3f}}<extra></extra>'
    }}], {{
      height: 680, margin: {{t:20,b:140,l:220,r:80}},
      xaxis: {{tickangle:-55, tickfont:{{size:7}}, side:'bottom'}},
      yaxis: {{tickfont:{{size:7}}}},
      paper_bgcolor:'transparent',
      hoverlabel: {{bgcolor:'#1e293b', font:{{color:'white', size:12}}}}
    }});
  }} else {{
    // Build top-50 pairs
    const n = CD.labels.length;
    const pairs = [];
    for (let i=0; i<n; i++) for (let j=i+1; j<n; j++)
      pairs.push({{a:CD.labels[i], b:CD.labels[j], s:CD.z[i][j]}});
    pairs.sort((a,b)=>b.s-a.s);
    const top = pairs.slice(0,50);
    Plotly.react('cosine_chart', [{{
      type:'bar', orientation:'h',
      x: top.map(p=>p.s), y: top.map(p=>p.a.substring(0,30)+'…'),
      text: top.map(p=>`vs: ${{p.b.substring(0,35)}}`),
      marker: {{color: top.map(p=>p.s), colorscale:'Blues', showscale:true,
               cmin:0, cmax:1}},
      hovertemplate: '<b>%{{y}}</b><br>%{{text}}<br>Score: %{{x:.3f}}<extra></extra>'
    }}], {{
      height: 600, margin: {{t:20,b:60,l:280,r:80}},
      xaxis: {{title:'Cosine Similarity', range:[0,1]}},
      yaxis: {{autorange:'reversed'}},
      paper_bgcolor:'transparent', plot_bgcolor:'#f8fafc',
      hoverlabel: {{bgcolor:'#1e293b', font:{{color:'white', size:12}}}}
    }});
  }}
}}
updateCosine();

// ── Keyphrases table ──────────────────────────────────────────────────────────
(function() {{
  const sel_t = document.getElementById('kp_topic');
  const sel_c = document.getElementById('kp_cluster');
  for (let t=0; t<KD.n_topics; t++)
    sel_t.innerHTML += `<option value="${{t}}">Topic ${{t+1}}</option>`;
  for (let c=0; c<KD.best_k; c++)
    sel_c.innerHTML += `<option value="${{c}}">Cluster ${{c+1}}</option>`;
}})();

function filterKP() {{
  const q  = document.getElementById('kp_search').value.toLowerCase();
  const ft = document.getElementById('kp_topic').value;
  const fc = document.getElementById('kp_cluster').value;
  let html = '', count = 0;
  KD.book_ids.forEach((bid, i) => {{
    const t  = KD.topics[i], c = KD.clusters[i];
    const kps = (KD.keyphrases[bid]||[]).join(', ');
    const title = KD.titles[i], author = KD.authors[i];
    if (ft !== 'all' && String(t) !== ft) return;
    if (fc !== 'all' && String(c) !== fc) return;
    if (q && !title.toLowerCase().includes(q) && !kps.toLowerCase().includes(q)) return;
    const tcol = PALETTE[t % PALETTE.length];
    const ccol = PALETTE[c % PALETTE.length];
    const tname = KD.lda_names?KD.lda_names[t]:'T'+(t+1);
    html += `<tr>
      <td style="font-weight:600;max-width:220px">${{title.substring(0,60)}}</td>
      <td style="color:#64748b;font-size:.8em">${{author.substring(0,30)}}</td>
      <td><span class="badge" style="background:${{tcol}}">${{tname}}</span></td>
      <td><span class="badge" style="background:${{ccol}}">C${{c+1}}</span></td>
      <td>${{(KD.keyphrases[bid]||[]).slice(0,8).map(k=>`<span class="kp">${{k}}</span>`).join('')}}</td>
    </tr>`;
    count++;
  }});
  document.getElementById('kp_tbody').innerHTML = html;
  document.getElementById('kp_count').textContent = `Showing ${{count}} of ${{KD.book_ids.length}} books`;
}}
filterKP();

// ── UI helpers ────────────────────────────────────────────────────────────────
function showTab(btn, id) {{
  const card = btn.closest('.book-card');
  card.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
  card.querySelectorAll('.tab-content').forEach(c=>c.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById(id).classList.add('active');
}}
function toggleAcc(btn) {{
  const body = btn.nextElementSibling;
  btn.classList.toggle('open', !btn.classList.contains('open'));
  body.classList.toggle('open', !body.classList.contains('open'));
}}
</script>
</body></html>"""

out = 'data/outputs/book_nlp_analysis.html'
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Saved: {out}  ({len(html)//1024} KB)")