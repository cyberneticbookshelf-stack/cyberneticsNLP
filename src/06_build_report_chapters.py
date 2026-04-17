"""


06_build_report_chapters.py  —  Chapter-level HTML report with interactive charts.

Interactive (Plotly.js):
  • 2D chapter scatter — hover for chapter/book details, filter by topic or cluster
  • Book × Topic heatmap — hover for counts and proportions
  • Keyphrases — searchable, filterable by topic/cluster

Static PNG figures kept for NMF error curve, K-Means elbow, and stacked bar.
"""

# ── METHODOLOGICAL NOTE — all outputs are provisional ────────────────────────
# This script generates HTML from automated analysis of a 542-book corpus.
# Results should be treated as provisional: known data quality issues have been
# characterised and mitigated; residual errors of uncharacterised distribution
# remain. Algorithm infection — residual input errors propagate into downstream
# computations (LDA, PMI, TF-IDF, etc.) with effects that cannot be quantified
# in advance. Individual associations should be verified against source material
# before being treated as established findings.
# Full argument: docs/methodology.md §"Implication for dissemination —
# all outputs are provisional"
# ─────────────────────────────────────────────────────────────────────────────

_PROV_NOTICE = (
    '\n<div style="margin:1.5rem 1rem 0.5rem;padding:0.9rem 1.25rem;'
    'background:#fef3c7;border-left:4px solid #d97706;border-radius:4px;'
    'font-size:.82rem;color:#78350f;line-height:1.6">'
    '<strong>Provenance notice:</strong> Results are derived from automated '
    'analysis of a 542-book corpus and should be treated as provisional. '
    'Known data quality issues have been characterised and mitigated; residual '
    'errors of uncharacterised distribution remain. Individual associations '
    'should be verified against source material before being treated as '
    'established findings. '
    'See <em>docs/methodology.md</em> §&ldquo;Implication for dissemination '
    '&mdash; all outputs are provisional&rdquo;.</div>'
)

# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_metadata_full.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


import json, base64
import numpy as np

with open(str(JSON_DIR / 'nlp_results_chapters.json')) as f: R  = json.load(f)
try:
    with open(str(JSON_DIR / 'nlp_results.json')) as _f: _RB = json.load(_f)
    R['topic_names'] = _RB.get('topic_names')  # carry book-level names
except Exception: pass
with open(str(JSON_DIR / 'summaries.json'))            as f: S  = json.load(f)

book_ids     = R['book_ids']
n_topics     = R['n_topics']
n_clusters   = R['best_k']
dom_topics   = R['dominant_topics']
clusters     = R['cluster_labels']
top_words    = R['top_words']
chs_meta     = R['chapters']
keyphrases   = R['keyphrases']
book_tc      = R['book_topic_counts']
coords_2d    = R['coords_2d']
cosine_sim   = R['cosine_sim']
total_ch     = len(chs_meta)

PALETTE = ['#2563eb','#16a34a','#dc2626','#d97706','#7c3aed','#0891b2',
           '#be185d','#0f766e','#c2410c','#065f46','#9333ea','#0369a1',
           '#b45309','#1d4ed8','#166534','#be123c','#7e22ce','#0369a1']

_BASE_NAMES = [
    'Human & Social Experience',
    'Mathematical & Formal Systems',
    'General Systems Theory',
    'History & Philosophy of Cybernetics',
    'Management & Organisational Cybernetics',
    'Control Theory & Engineering',
    'Topic 7', 'Topic 8', 'Topic 9',
]
# Build TOPIC_NAMES for chapter-level NMF.
# Carried book-level LDA names are used as a fallback only; NMF k may differ
# from LDA k, so we always pad to exactly n_topics entries with generic labels.
_carried = (R.get('topic_names') or _BASE_NAMES)[:]
TOPIC_NAMES = (_carried + [f'Topic {i+1}' for i in range(len(_carried), n_topics)])[:n_topics]

def img_b64(path):
    with open(path,'rb') as f:
        return 'data:image/png;base64,' + base64.b64encode(f.read()).decode()

imgs = {
    'err':     img_b64('figures/chfig1_nmf_error.png'),
    'words':   img_b64('figures/chfig2_topic_words.png'),
    'elbow':   img_b64('figures/chfig4_kmeans_elbow.png'),
    'stackbar':img_b64('figures/chfig7_topic_proportions.png'),
}

# ── Topic table ───────────────────────────────────────────────────────────────
topic_rows = ''
for t in range(n_topics):
    words    = ', '.join(top_words[t][:10])
    ch_count = sum(1 for d in dom_topics if d==t)
    books_in = sorted({chs_meta[i]['book_id'] for i,d in enumerate(dom_topics) if d==t})
    bt = '; '.join((S[bid]['title'][:30]+'…' if len(S[bid]['title'])>30 else S[bid]['title'])
                   for bid in books_in[:5])
    col = PALETTE[t % len(PALETTE)]
    topic_rows += f"""
    <tr>
      <td><span class="badge" style="background:{col}">T{t+1}</span></td>
      <td><strong>{TOPIC_NAMES[t]}</strong></td>
      <td>{words}</td><td>{ch_count}</td>
      <td style="font-size:.8em;color:#475569">{bt}{'…' if len(books_in)>5 else ''}</td>
    </tr>"""

# ── Book cards ────────────────────────────────────────────────────────────────
ch_by_id = {ch['chapter_id']: (i, ch) for i, ch in enumerate(chs_meta)}

def chapter_accordion(bid):
    items = ''
    for ch in S[bid]['chapters']:
        idx = ch['index']
        cid = f"{bid}_ch{idx:03d}"
        if cid in ch_by_id:
            ci, cm  = ch_by_id[cid]
            t, cl   = dom_topics[ci], clusters[ci]
            tcol, ccol = PALETTE[t%len(PALETTE)], PALETTE[cl%len(PALETTE)]
            kps = keyphrases.get(cid,[])
            kp_html = ''.join(f'<span class="kp">{k}</span>' for k in kps[:6])
        else:
            tcol=ccol='#94a3b8'; t=cl=0; kp_html=''
        summ = ch.get('summary','').strip() or '<em>No summary available.</em>'
        wc   = ch.get('word_count',0)
        items += f"""
        <div class="acc-item">
          <button class="acc-btn" onclick="toggleAcc(this)">
            <span class="ch-num">Ch {idx}</span>
            <span class="ch-title">{ch['title'][:60]}{'…' if len(ch['title'])>60 else ''}</span>
            <span class="badge" style="background:{tcol};font-size:.65rem">T{t+1}</span>
            <span class="badge" style="background:{ccol};font-size:.65rem">C{cl+1}</span>
            <span class="ch-wc">{wc:,}w</span>
            <span class="acc-arrow">▼</span>
          </button>
          <div class="acc-body"><div class="kp-row">{kp_html}</div>{summ}</div>
        </div>"""
    return f'<div class="accordion">{items}</div>'

book_cards = ''
for bid in book_ids:
    sv    = S[bid]
    tc    = book_tc.get(bid,[0]*n_topics)
    dom_t = int(np.argmax(tc))
    col   = PALETTE[dom_t % len(PALETTE)]
    book_cards += f"""
<div class="book-card" id="book-{bid}">
  <div class="book-header" style="border-left:5px solid {col}">
    <div>
      <div class="book-title">{sv['title']}</div>
      <div class="book-meta">✍️ {sv['author']} &nbsp;|&nbsp;
        <span class="badge" style="background:{col}">T{dom_t+1} {TOPIC_NAMES[dom_t]}</span>
        <span class="ch-count-badge">{sv['n_chapters']} chapters</span>
      </div>
    </div>
  </div>
  <div class="book-body">
    <div class="section-label">📖 Book Summary</div>
    <div class="summary-tabs">
      <div class="tab-btns">
        <button class="tab-btn active" onclick="showTab(this,'desc-{bid}')">📋 Descriptive</button>
        <button class="tab-btn" onclick="showTab(this,'arg-{bid}')">💡 Argumentative</button>
        <button class="tab-btn" onclick="showTab(this,'crit-{bid}')">🔍 Critical</button>
      </div>
      <div id="desc-{bid}" class="tab-content active">{sv.get('descriptive','')}</div>
      <div id="arg-{bid}"  class="tab-content">{sv.get('argumentative','')}</div>
      <div id="crit-{bid}" class="tab-content">{sv.get('critical','')}</div>
    </div>
    <div class="section-label" style="margin-top:1rem">📑 Chapters</div>
    {chapter_accordion(bid)}
  </div>
</div>"""

# ── Plotly data payloads ──────────────────────────────────────────────────────
scatter_data = json.dumps({
    'x':         [c[0] for c in coords_2d],
    'y':         [c[1] for c in coords_2d],
    'ch_titles': [ch['ch_title'] for ch in chs_meta],
    'bk_titles': [ch['book_title'] for ch in chs_meta],
    'topics':    dom_topics,
    'clusters':  clusters,
    'n_topics':  n_topics,
    'best_k':    n_clusters,
    'topic_names': TOPIC_NAMES,
    'palette':   PALETTE,
})

# Book x Topic heatmap
bk_short   = [S[bid]['title'][:40]+'…' if len(S[bid]['title'])>40 else S[bid]['title']
               for bid in book_ids]
mat        = [[book_tc.get(bid,[0]*n_topics)[t] for t in range(n_topics)]
              for bid in book_ids]
row_sums   = [max(sum(r),1) for r in mat]
mat_norm   = [[mat[i][t]/row_sums[i] for t in range(n_topics)]
              for i in range(len(book_ids))]
bt_data    = json.dumps({
    'z':        mat_norm,
    'counts':   mat,
    'books':    bk_short,
    'topics':   [f'T{t+1} {TOPIC_NAMES[t]}' for t in range(n_topics)],
})

# Keyphrases
kp_data = json.dumps({
    'ch_ids':    [ch['chapter_id'] for ch in chs_meta],
    'ch_titles': [ch['ch_title'] for ch in chs_meta],
    'bk_titles': [ch['book_title'] for ch in chs_meta],
    'bk_authors':[ch['book_author'] for ch in chs_meta],
    'topics':    dom_topics,
    'clusters':  clusters,
    'keyphrases': keyphrases,
    'n_topics':  n_topics,
    'best_k':    n_clusters,
    'palette':   PALETTE,
})

# ── Assemble HTML ─────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Chapter-Level NLP Analysis</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.27.0/plotly.min.js"></script>
<style>
:root{{--blue:#2563eb;--green:#16a34a;--bg:#f8fafc;--card:#fff;--border:#e2e8f0}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:#1e293b;line-height:1.6}}
.header{{background:linear-gradient(135deg,#1e3a5f,#2563eb);color:#fff;padding:2.5rem 2rem;text-align:center}}
.header h1{{font-size:1.8rem;font-weight:700;margin-bottom:.4rem}}
.stats-bar{{display:flex;justify-content:center;gap:2.5rem;background:#1e293b;color:#fff;padding:.9rem;flex-wrap:wrap}}
.stat{{text-align:center}}.stat span{{display:block;font-size:1.5rem;font-weight:700;color:#60a5fa}}
.stat small{{font-size:.7rem;opacity:.7;text-transform:uppercase}}
nav{{background:#fff;border-bottom:1px solid var(--border);padding:.6rem 1.5rem;position:sticky;top:0;z-index:99;display:flex;gap:1rem;flex-wrap:wrap}}
nav a{{text-decoration:none;color:#475569;font-size:.85rem;padding:.3rem .7rem;border-radius:4px}}
nav a:hover{{background:#eff6ff;color:var(--blue)}}
.container{{max-width:1400px;margin:0 auto;padding:1.5rem}}
section{{margin-bottom:3rem}}
h2{{font-size:1.3rem;font-weight:700;color:#1e293b;margin-bottom:1rem;padding-bottom:.5rem;border-bottom:2px solid var(--blue)}}
.fig{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:1rem;margin-bottom:1.2rem;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.fig img{{width:100%}}.fig-caption{{font-size:.8rem;color:#64748b;margin-top:.5rem;text-align:center}}
.plotly-chart{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:1rem;margin-bottom:1.2rem;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.chart-controls{{display:flex;gap:.6rem;flex-wrap:wrap;margin-bottom:.6rem;align-items:center}}
.chart-controls label{{font-size:.82rem;color:#475569;font-weight:500}}
.chart-controls select,.kp-search{{padding:.3rem .6rem;border:1px solid var(--border);border-radius:5px;font-size:.82rem;background:#fff;color:#1e293b}}
.kp-search{{width:240px}}
table{{width:100%;border-collapse:collapse;background:var(--card);border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
th{{background:#1e3a5f;color:#fff;padding:.7rem 1rem;text-align:left;font-size:.85rem;font-weight:600}}
td{{padding:.6rem 1rem;border-bottom:1px solid var(--border);font-size:.85rem;vertical-align:top}}
tr:hover td{{background:#f1f5f9}}
.badge{{display:inline-block;color:#fff;padding:.15rem .55rem;border-radius:9999px;font-size:.75rem;font-weight:600;margin:.1rem}}
.ch-count-badge{{display:inline-block;background:#e2e8f0;color:#475569;padding:.15rem .6rem;border-radius:9999px;font-size:.75rem;margin:.1rem}}
.book-card{{background:var(--card);border:1px solid var(--border);border-radius:10px;margin-bottom:1.4rem;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.07)}}
.book-header{{padding:.9rem 1.2rem}}.book-title{{font-weight:700;font-size:.95rem;color:#0f172a;margin-bottom:.3rem}}
.book-meta{{font-size:.8rem;color:#64748b}}.book-body{{padding:.8rem 1.2rem 1.2rem}}
.section-label{{font-weight:600;font-size:.82rem;color:#475569;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem}}
.tab-btns{{display:flex;gap:.4rem;margin-bottom:.6rem;flex-wrap:wrap}}
.tab-btn{{padding:.3rem .75rem;border:1px solid var(--border);background:#f8fafc;border-radius:5px;cursor:pointer;font-size:.79rem;color:#475569;transition:all .2s}}
.tab-btn.active{{background:var(--blue);color:#fff;border-color:var(--blue)}}
.tab-content{{display:none;font-size:.85rem;color:#334155;line-height:1.7;background:#f8fafc;padding:.8rem;border-radius:6px;border:1px solid var(--border)}}
.tab-content.active{{display:block}}
.accordion{{border:1px solid var(--border);border-radius:8px;overflow:hidden;margin-top:.3rem}}
.acc-item{{border-bottom:1px solid var(--border)}}.acc-item:last-child{{border-bottom:none}}
.acc-btn{{width:100%;display:flex;align-items:center;gap:.5rem;padding:.5rem .9rem;background:#f8fafc;border:none;cursor:pointer;text-align:left;transition:background .15s;flex-wrap:wrap}}
.acc-btn:hover,.acc-btn.open{{background:#eff6ff}}
.ch-num{{font-size:.72rem;font-weight:700;color:#fff;background:#94a3b8;padding:.1rem .4rem;border-radius:4px;white-space:nowrap;min-width:2.5rem;text-align:center}}
.ch-title{{flex:1;font-size:.81rem;font-weight:600;color:#1e293b;min-width:120px}}
.ch-wc{{font-size:.72rem;color:#94a3b8;white-space:nowrap}}
.acc-arrow{{font-size:.65rem;color:#94a3b8;transition:transform .2s;margin-left:auto}}
.acc-btn.open .acc-arrow{{transform:rotate(180deg)}}
.acc-body{{display:none;padding:.65rem 1rem;font-size:.83rem;color:#334155;line-height:1.7;background:#fff;border-top:1px solid var(--border)}}
.acc-body.open{{display:block}}
.kp-row{{margin-bottom:.5rem}}
.kp{{display:inline-block;background:#eff6ff;color:#2563eb;border:1px solid #bfdbfe;border-radius:4px;padding:.12rem .45rem;font-size:.72rem;margin:.15rem .1rem}}
.kp-table th{{background:#1e3a5f;color:#fff;padding:.5rem .8rem;text-align:left}}
.kp-table td{{padding:.45rem .8rem;border-bottom:1px solid var(--border);vertical-align:top}}
.kp-table tr:hover td{{background:#f1f5f9}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:1rem}}
@media(max-width:700px){{.grid2{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="header">
  <h1>📚 Chapter-Level NLP Analysis</h1>
  <p>NMF Topic Modelling · Clustering · Keyphrase Extraction · Interactive Visualisation</p>
</div>
<div class="stats-bar">
  <div class="stat"><span>{len(book_ids)}</span><small>Books</small></div>
  <div class="stat"><span>{total_ch}</span><small>Chapters</small></div>
  <div class="stat"><span>{n_topics}</span><small>NMF Topics</small></div>
  <div class="stat"><span>{n_clusters}</span><small>Clusters</small></div>
</div>
<nav>
  <a href="#topics">📊 Topics</a>
  <a href="#scatter">🗺 Scatter</a>
  <a href="#heatmap">🔥 Heatmap</a>
  <a href="#keyphrases">🔑 Keyphrases</a>
  <a href="#books">📝 Books</a>
</nav>
<div class="container">

<section id="topics">
  <h2>1 · NMF Topic Modelling (k={n_topics})</h2>
  <div class="grid2">
    <div class="fig"><img src="{imgs['err']}" alt="error">
      <div class="fig-caption">Fig 1 — NMF reconstruction error (elbow at k={n_topics})</div></div>
    <div class="fig"><img src="{imgs['elbow']}" alt="elbow">
      <div class="fig-caption">Fig 4 — K-Means elbow + silhouette</div></div>
  </div>
  <div class="fig"><img src="{imgs['words']}" alt="words">
    <div class="fig-caption">Fig 2 — Top words per NMF topic</div></div>
  <table><thead><tr><th>#</th><th>Name</th><th>Top Keywords</th><th>Chapters</th><th>Books (sample)</th></tr></thead>
  <tbody>{topic_rows}</tbody></table>
</section>

<section id="scatter">
  <h2>2 · Chapter Scatter (interactive)</h2>
  <div class="plotly-chart">
    <div class="chart-controls">
      <label>Colour by:</label>
      <select id="ch_scatter_colour" onchange="updateChScatter()">
        <option value="topic">NMF Topic</option>
        <option value="cluster">Cluster</option>
      </select>
      <label style="margin-left:.8rem">Filter:</label>
      <select id="ch_scatter_filter" onchange="updateChScatter()">
        <option value="all">All</option>
      </select>
    </div>
    <div id="ch_scatter_chart"></div>
    <div class="fig-caption">Hover for chapter title, book, topic &amp; cluster</div>
  </div>
</section>

<section id="heatmap">
  <h2>3 · Book × Topic Heatmap (interactive)</h2>
  <div class="plotly-chart">
    <div id="bt_heatmap"></div>
    <div class="fig-caption">Hover for chapter count and proportion — shading = proportion of book's chapters in each topic</div>
  </div>
  <div class="plotly-chart">
    <div class="chart-controls">
      <label>Filter to books where topic proportion &gt;</label>
      <select id="mix_thresh" onchange="drawMix()">
        <option value="0">Show all books</option>
        <option value="0.3">30%</option>
        <option value="0.5" selected>50%</option>
        <option value="0.7">70%</option>
      </select>
      <label style="margin-left:.8rem">for topic:</label>
      <select id="mix_topic" onchange="drawMix()">
        <option value="-1">Any topic</option>
      </select>
    </div>
    <div id="mix_chart"></div>
    <div class="fig-caption">Topic mix per book — each bar = 100% of a book's chapters. Filter to focus on specific topics or dominant books.</div>
  </div>
</section>

<section id="keyphrases">
  <h2>4 · Chapter Keyphrases (searchable)</h2>
  <div class="plotly-chart">
    <div class="chart-controls">
      <input class="kp-search" id="ch_kp_search" type="text" placeholder="Search chapters or keyphrases…" oninput="filterChKP()">
      <label style="margin-left:.8rem">Topic:</label>
      <select id="ch_kp_topic" onchange="filterChKP()"><option value="all">All</option></select>
      <label style="margin-left:.5rem">Cluster:</label>
      <select id="ch_kp_cluster" onchange="filterChKP()"><option value="all">All</option></select>
    </div>
    <div id="ch_kp_count" style="font-size:.82rem;color:#64748b;margin-bottom:.4rem"></div>
    <table class="kp-table" id="ch_kp_table">
      <thead><tr><th>Book</th><th>Chapter</th><th>Topic</th><th>Cluster</th><th>Key Phrases</th></tr></thead>
      <tbody id="ch_kp_tbody"></tbody>
    </table>
  </div>
</section>

<section id="books">
  <h2>5 · Books — Chapter Detail</h2>
  {book_cards}
</section>

</div>
<footer style="text-align:center;padding:1.5rem;color:#94a3b8;font-size:.8rem;border-top:1px solid var(--border);margin-top:2rem">
  Chapter NLP · NMF ({n_topics} topics) · K-Means ({n_clusters} clusters) · {total_ch} chapters · Interactive charts via Plotly.js
</footer>

<script>
const SD = {scatter_data};
const BTD = {bt_data};
const KD = {kp_data};
const PALETTE = {json.dumps(PALETTE)};

// ── Chapter scatter ───────────────────────────────────────────────────────────
function buildChTraces(colourBy, filterVal) {{
  const groupKey = colourBy === 'topic' ? SD.topics : SD.clusters;
  const nGroups  = colourBy === 'topic' ? SD.n_topics : SD.best_k;
  const traces   = [];
  for (let g = 0; g < nGroups; g++) {{
    if (filterVal !== 'all' && String(g) !== String(filterVal)) continue;
    const idx = groupKey.map((v,i) => v===g ? i : -1).filter(i=>i>=0);
    const label = colourBy==='topic'
      ? `T${{g+1}} ${{SD.topic_names[g] || ''}}` : `Cluster ${{g+1}}`;
    traces.push({{
      x: idx.map(i=>SD.x[i]), y: idx.map(i=>SD.y[i]),
      mode:'markers', type:'scatter', name: label,
      marker:{{color:PALETTE[g%PALETTE.length], size:6, opacity:.75,
               line:{{color:'white',width:0.4}}}},
      text: idx.map(i=>`<b>${{SD.ch_titles[i].substring(0,50)}}</b><br>${{SD.bk_titles[i].substring(0,45)}}<br>Topic ${{SD.topics[i]+1}} · Cluster ${{SD.clusters[i]+1}}`),
      hovertemplate:'%{{text}}<extra></extra>'
    }});
  }}
  return traces;
}}

function populateChFilter() {{
  const mode = document.getElementById('ch_scatter_colour').value;
  const sel  = document.getElementById('ch_scatter_filter');
  const n = mode==='topic' ? SD.n_topics : SD.best_k;
  sel.innerHTML = '<option value="all">All</option>' +
    Array.from({{length:n}},(_,i)=>`<option value="${{i}}">${{mode==='topic'?`T${{i+1}} ${{SD.topic_names[i]||''}}`:`Cluster ${{i+1}}`}}</option>`).join('');
}}

function updateChScatter() {{
  populateChFilter();
  const mode   = document.getElementById('ch_scatter_colour').value;
  const filter = document.getElementById('ch_scatter_filter').value;
  Plotly.react('ch_scatter_chart', buildChTraces(mode, filter), {{
    height:560, margin:{{t:20,b:60,l:60,r:20}},
    xaxis:{{title:'LSA Dimension 1',zeroline:false}},
    yaxis:{{title:'LSA Dimension 2',zeroline:false}},
    legend:{{orientation:'v'}},
    paper_bgcolor:'transparent', plot_bgcolor:'#f8fafc',
    hoverlabel:{{bgcolor:'#1e293b',font:{{color:'white',size:12}}}}
  }});
}}
populateChFilter();
updateChScatter();

// ── Book × Topic heatmap ──────────────────────────────────────────────────────
(function() {{
  const annotations = [];
  BTD.counts.forEach((row,i) => row.forEach((v,j) => {{
    if (v > 0) annotations.push({{
      x: BTD.topics[j], y: BTD.books[i],
      text: `<b>${{v}}</b>`,
      showarrow:false,
      font:{{size:10, color: BTD.z[i][j] > 0.4 ? 'white' : '#1e3a5f',
             family:'monospace'}}
    }});
  }}));
  Plotly.newPlot('bt_heatmap', [{{
    z: BTD.z, x: BTD.topics, y: BTD.books,
    type:'heatmap',
    colorscale: [[0,'#f0f9ff'],[0.25,'#7dd3fc'],[0.5,'#2563eb'],[1,'#1e3a5f']],
    zmin:0, zmax:1,
    hovertemplate:'<b>%{{y}}</b><br>%{{x}}<br>Chapters: %{{customdata[0]}}<br>Proportion: %{{z:.1%}}<extra></extra>',
    customdata: BTD.counts
  }}], {{
    height: Math.max(400, BTD.books.length * 24 + 140),
    margin:{{t:20,b:100,l:320,r:80}},
    xaxis:{{tickangle:-40, tickfont:{{size:10}}, side:'bottom'}},
    yaxis:{{tickfont:{{size:9}}}},
    annotations: annotations,
    paper_bgcolor:'transparent',
    hoverlabel:{{bgcolor:'#1e293b',font:{{color:'white',size:12}}}}
  }});
}})();

// ── Keyphrases ────────────────────────────────────────────────────────────────
(function() {{
  const st = document.getElementById('ch_kp_topic');
  const sc = document.getElementById('ch_kp_cluster');
  for (let t=0;t<KD.n_topics;t++)
    st.innerHTML+=`<option value="${{t}}">T${{t+1}}</option>`;
  for (let c=0;c<KD.best_k;c++)
    sc.innerHTML+=`<option value="${{c}}">C${{c+1}}</option>`;
}})();

function filterChKP() {{
  const q  = document.getElementById('ch_kp_search').value.toLowerCase();
  const ft = document.getElementById('ch_kp_topic').value;
  const fc = document.getElementById('ch_kp_cluster').value;
  let html='', count=0;
  KD.ch_ids.forEach((cid,i) => {{
    const t=KD.topics[i], c=KD.clusters[i];
    const kps=(KD.keyphrases[cid]||[]).join(', ');
    const ct=KD.ch_titles[i], bt=KD.bk_titles[i];
    if (ft!=='all' && String(t)!==ft) return;
    if (fc!=='all' && String(c)!==fc) return;
    if (q && !ct.toLowerCase().includes(q) && !bt.toLowerCase().includes(q) && !kps.toLowerCase().includes(q)) return;
    const tcol=PALETTE[t%PALETTE.length], ccol=PALETTE[c%PALETTE.length];
    html+=`<tr>
      <td style="font-size:.8em;color:#64748b;max-width:180px">${{bt.substring(0,45)}}</td>
      <td style="font-weight:600;max-width:200px">${{ct.substring(0,55)}}</td>
      <td><span class="badge" style="background:${{tcol}}">T${{t+1}}</span></td>
      <td><span class="badge" style="background:${{ccol}}">C${{c+1}}</span></td>
      <td>${{(KD.keyphrases[cid]||[]).slice(0,8).map(k=>`<span class="kp">${{k}}</span>`).join('')}}</td>
    </tr>`;
    count++;
  }});
  document.getElementById('ch_kp_tbody').innerHTML = html;
  document.getElementById('ch_kp_count').textContent = `Showing ${{count}} of ${{KD.ch_ids.length}} chapters`;
}}
filterChKP();

// ── Topic mix per book (interactive) ─────────────────────────────────────────
(function(){{
  KD.ch_ids; // ensure KD is loaded
  // Populate topic dropdown
  const sel=document.getElementById('mix_topic');
  SD.topic_names.forEach((nm,i)=>{{
    const o=document.createElement('option');o.value=i;o.textContent=nm;sel.appendChild(o);
  }});
}})();

function drawMix(){{
  const thresh=+document.getElementById('mix_thresh').value;
  const topicFilter=+document.getElementById('mix_topic').value;

  // BTD already has books/topics/counts/z
  let indices=BTD.books.map((_,i)=>i);
  if(topicFilter>=0||thresh>0){{
    indices=indices.filter(i=>{{
      if(topicFilter>=0){{
        return BTD.z[i][topicFilter]>=thresh;
      }}
      return Math.max(...BTD.z[i])>=thresh;
    }});
  }}

  const books=indices.map(i=>BTD.books[i]);
  const traces=BTD.topics.map((tname,t)=>{{
    return{{
      x:indices.map(i=>BTD.z[i][t]),
      y:books,
      type:'bar',orientation:'h',name:tname,
      marker:{{color:PALETTE[t%PALETTE.length]}},
      hovertemplate:`${{tname}}: %{{x:.0%}}<br><b>%{{y}}</b><extra></extra>`,
    }};
  }});

  const h=Math.max(300, books.length*22+120);
  Plotly.react('mix_chart',traces,{{
    barmode:'stack',
    height:h,
    margin:{{t:10,b:50,l:320,r:20}},
    xaxis:{{title:'Proportion of chapters',tickformat:'.0%',range:[0,1]}},
    yaxis:{{autorange:'reversed',tickfont:{{size:9}}}},
    legend:{{orientation:'h',y:-0.12,font:{{size:9}}}},
    paper_bgcolor:'transparent',plot_bgcolor:'#f8fafc',
    hoverlabel:{{bgcolor:'#1e293b',font:{{color:'white',size:12}}}},
  }});
}}
drawMix();

function showTab(btn,id){{
  const card=btn.closest('.book-card');
  card.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
  card.querySelectorAll('.tab-content').forEach(c=>c.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById(id).classList.add('active');
}}
function toggleAcc(btn){{
  const body=btn.nextElementSibling;
  btn.classList.toggle('open',!btn.classList.contains('open'));
  body.classList.toggle('open',!body.classList.contains('open'));
}}
</script>
</body></html>"""

html = html.replace('</body>', _PROV_NOTICE + '\n</body>', 1)
out = 'data/outputs/book_nlp_analysis_chapters.html'
with open(out,'w',encoding='utf-8') as f:
    f.write(html)
print(f"Saved: {out}  ({len(html)//1024} KB)")