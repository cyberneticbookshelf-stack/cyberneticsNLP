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
    '<style>body{padding-top:54px!important}</style>'
    '<div style="position:fixed;top:0;left:0;right:0;z-index:9999;'
    'background:#fef3c7;border-bottom:3px solid #d97706;'
    'padding:0.55rem 1.25rem;font-size:.82rem;color:#78350f;'
    'line-height:1.5;box-shadow:0 2px 6px rgba(0,0,0,.12)">'
    '<strong>Provenance notice:</strong> Results are derived from '
    'automated analysis of the CyberneticsNLP corpus and should be '
    'treated as provisional. '
    'Known data quality issues have been characterised and mitigated; '
    'residual errors of uncharacterised distribution remain. '
    'Individual associations should be verified against source material '
    'before being treated as established findings. '
    'See <em>docs/methodology.md</em> &sect;&ldquo;Implication for '
    'dissemination &mdash; all outputs are provisional&rdquo;.'
    '</div>'
)
import json, numpy as np, math
from collections import Counter
from sklearn.metrics import adjusted_rand_score


# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_metadata_full.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


with open(str(JSON_DIR / 'embedding_results.json')) as f:
    R = json.load(f)

titles    = R['titles']
book_ids  = R['book_ids']
lda_tops  = R['lda_topics']
lda_names = R['lda_names']
methods   = R['methods']
nbrs      = R['neighbours']
cl_labels = R['cluster_labels']
coords_2d = R['coords_2d_lsa']
pub_years = R['pub_years']

# Available methods
avail = [m for m in 'ABCD' if methods[m].get('available', True)
         and methods[m].get('silhouette') is not None]
print(f"Available methods: {avail}")

# Zero-summary books
zero_bids = {book_ids[i] for i in range(len(book_ids))
             if nbrs['A'][i][0]['sim'] < 0.01}
good = [i for i,bid in enumerate(book_ids) if bid not in zero_bids]

# Pre-compute analysis
ari_ab = adjusted_rand_score([cl_labels['A'][i] for i in good],
                              [cl_labels['B'][i] for i in good])

def purity(labs):
    k = max(labs)+1
    return sum(Counter(lda_tops[i] for i,l in enumerate(labs) if l==c
               ).most_common(1)[0][1] for c in range(k)) / len(book_ids)

def metric_best(metric, higher_better=True):
    vals = {m: methods[m][metric] for m in avail if metric in methods[m]}
    if not vals: return {}
    best = max(vals, key=vals.get) if higher_better else min(vals, key=vals.get)
    return {m: (v, m==best) for m,v in vals.items()}

def nbr_html(i, method_list):
    rows = ''
    for m in method_list:
        if not nbrs.get(m): continue
        n = nbrs[m][i]
        col = {'A':'#2563eb','B':'#16a34a','C':'#dc2626','D':'#d97706'}[m]
        label = {'A':'LSA 100d','B':'LSA 384d','C':'SentTrans','D':'Voyage'}[m]
        items = ''.join(
            f'<div style="padding:.15rem 0 .15rem 1rem;font-size:.82rem">'
            f'{j+1}. {titles[nb["idx"]][:55]}'
            f'<span style="float:right;color:#2563eb;font-weight:600">{nb["sim"]:.3f}</span>'
            f'</div>'
            for j,nb in enumerate(n[:3])
        )
        rows += (f'<div style="margin-bottom:.4rem">'
                 f'<span style="background:{col};color:#fff;padding:.15rem .5rem;'
                 f'border-radius:3px;font-size:.78rem;font-weight:700">{m}</span> '
                 f'<strong style="font-size:.85rem">{label}</strong>{items}</div>')
    return rows

# Metric table rows
def mrow(label, metric, higher_better=True, fmt='.4f'):
    best_map = metric_best(metric, higher_better)
    cells = ''
    for m in 'ABCD':
        if m not in avail:
            cells += '<td style="color:#94a3b8">—</td>'
        elif m in best_map:
            v, is_best = best_map[m]
            style = ' style="font-weight:700;color:#2563eb"' if is_best else ''
            cells += f'<td{style}>{v:{fmt}}</td>'
        else:
            cells += '<td>—</td>'
    return f'<tr><td>{label}</td>{cells}</tr>'

PAL = ['#2563eb','#16a34a','#dc2626','#d97706','#7c3aed',
       '#0891b2','#be185d','#0f766e','#c2410c','#065f46']

j_r = json.dumps(R)
j_avail = json.dumps(avail)
j_pal   = json.dumps(PAL)
j_zero  = json.dumps(list(zero_bids))

MNAME = {'A':'TF-IDF + LSA 100d','B':'TF-IDF + LSA 384d',
         'C':'Sentence Transformers','D':'Voyage AI Embeddings'}
MCOL  = {'A':'#2563eb','B':'#16a34a','C':'#dc2626','D':'#d97706'}

def method_status_badge(m):
    if m in avail:
        return (f'<span style="background:{MCOL[m]};color:#fff;padding:.2rem .7rem;'
                f'border-radius:4px;font-size:.8rem;font-weight:700">{m} ✓</span>')
    reason = methods[m].get('reason','Not available')[:120]
    return (f'<span style="background:#e2e8f0;color:#64748b;padding:.2rem .7rem;'
            f'border-radius:4px;font-size:.8rem">{m} — {reason}</span>')

# Build interesting sample disagreements
sims_a = [nbrs['A'][i][0]['sim'] for i in good]
disagree_ab = [(i, nbrs['A'][i][0]['idx'], nbrs['A'][i][0]['sim'],
                   nbrs['B'][i][0]['idx'], nbrs['B'][i][0]['sim'])
               for i in good if nbrs['A'][i][0]['idx'] != nbrs['B'][i][0]['idx']]
scored = sorted(disagree_ab, key=lambda x: abs(x[2]-x[4]), reverse=True)

sample_rows = ''
for i,na,sa,nb_,sb in scored[:8]:
    lda_a = lda_names[lda_tops[na]] if na < len(lda_names) else '?'
    lda_b = lda_names[lda_tops[nb_]] if nb_ < len(lda_names) else '?'
    sample_rows += f'''
<tr>
  <td style="font-size:.83rem"><strong>{titles[i][:45]}</strong><br>
    <span style="font-size:.75rem;color:#64748b">{lda_names[lda_tops[i]]}</span></td>
  <td style="font-size:.82rem">{titles[na][:40]}<br>
    <span style="color:#2563eb;font-size:.75rem">sim={sa:.3f} · {lda_a[:25]}</span></td>
  <td style="font-size:.82rem">{titles[nb_][:40]}<br>
    <span style="color:#16a34a;font-size:.75rem">sim={sb:.3f} · {lda_b[:25]}</span></td>
</tr>'''


# ── Dynamic findings based on available methods ────────────────────────────────
from sklearn.metrics import adjusted_rand_score as _ari

_findings = []
_next     = []

# Silhouette winner
_sil = {m: methods[m]['silhouette'] for m in avail}
_sil_best = max(_sil, key=_sil.get)
_sil_worst = min(_sil, key=_sil.get)
_findings.append(f'<li><strong>Method {_sil_best} wins on cluster tightness</strong> '
    f'(silhouette {_sil[_sil_best]:.4f}) — '
    f'Method {_sil_worst} scores lowest ({_sil[_sil_worst]:.4f})</li>')

# Davies-Bouldin winner
_db = {m: methods[m]['davies_bouldin'] for m in avail}
_db_best = min(_db, key=_db.get)
_findings.append(f'<li><strong>Method {_db_best} wins on cluster separation</strong> '
    f'(Davies-Bouldin {_db[_db_best]:.2f}) — lower = better separated clusters</li>')

# Silhouette note
_findings.append('<li><strong>All silhouette scores are low (&lt;0.05)</strong> — '
    'expected for an interdisciplinary corpus with no hard topic boundaries</li>')

# ARI between available methods
for i, ma in enumerate(avail):
    for mb in avail[i+1:]:
        _a = _ari([cl_labels[ma][i] for i in good],
                   [cl_labels[mb][i] for i in good])
        _disagree = [(i, nbrs[ma][i][0]['idx'], nbrs[mb][i][0]['idx'])
                     for i in good if nbrs[ma][i][0]['idx'] != nbrs[mb][i][0]['idx']]
        _rate_a = sum(1 for i,na,_ in _disagree 
                      if lda_tops[na]==lda_tops[i])/max(len(_disagree),1)
        _rate_b = sum(1 for i,_,nb in _disagree 
                      if lda_tops[nb]==lda_tops[i])/max(len(_disagree),1)
        _pct_agree = 100 - len(_disagree)/len(good)*100
        _findings.append(
            f'<li><strong>{ma} and {mb} agree on ~{_pct_agree:.0f}% of nearest neighbours' 
            f' (ARI={_a:.3f})</strong> — {ma} finds same-LDA-topic neighbours ' 
            f'{_rate_a:.0%} of the time vs {mb} at {_rate_b:.0%}</li>')

# Empty summary note
_findings.append(f'<li><strong>{len(zero_bids)} books with empty summaries</strong> ' 
    f'get sim=0.000 in LSA methods — a data quality issue, not a method failure</li>')

findings_items = "\n        ".join(_findings)

# Next steps
if "C" not in avail:
    _next.append('<li><strong>Run Method C</strong> (Sentence Transformers) — ' 
        'upgrade PyTorch to ≥2.4 then ' 
        '<code>pip install sentence-transformers</code></li>')
if "D" not in avail:
    _next.append('<li><strong>Run Method D</strong> (Voyage AI) — ' 
        'free key at dash.voyageai.com, costs ~$0.01 for 695 books</li>')
_next.append('<li><strong>Fix the empty-summary books</strong> — rerun ' 
    f'<code>generate_summaries_api.py</code> for IDs {', '.join(sorted(zero_bids))}</li>')
_next.append('<li><strong>Try <code>--k 7</code></strong> to fix cluster count ' 
    'across all methods for a direct apples-to-apples comparison</li>')
_sil_winner = max({m: methods[m]["silhouette"] for m in avail}, 
                   key=lambda m: methods[m]["silhouette"])
_next.append(f'<li><strong>Method {_sil_winner} remains the recommended default</strong> ' 
    f'for pipeline clustering — fastest among methods with best silhouette</li>')

next_items = "\n        ".join(_next)

# Build warning for missing methods
_missing = [m for m in 'ABCD' if m not in avail]
_install = {
    'C': 'upgrade PyTorch to ≥2.4 then <code>pip install sentence-transformers</code>',
    'D': 'set <code>VOYAGE_API_KEY</code> (free at dash.voyageai.com)',
}
if _missing:
    _parts = [f'Method {m}: {_install[m]}' for m in _missing if m in _install]
    _missing_warning = ('<div class="warning">⚠ '
        + ', '.join([f'Method {m}' for m in _missing])
        + (' did not run. ' if len(_missing) > 1 else ' did not run. ')
        + ' &nbsp;|&nbsp; '.join(_parts)
        + '</div>') if _parts else ''
else:
    _missing_warning = ''

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Embedding Comparison — Analysis Report</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.27.0/plotly.min.js"></script>
<style>
:root{{--blue:#2563eb;--bg:#f8fafc;--card:#fff;--border:#e2e8f0}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:#1e293b;line-height:1.6}}
.header{{background:linear-gradient(135deg,#1e3a5f,#2563eb);color:#fff;padding:2.5rem 2rem;text-align:center}}
.header h1{{font-size:1.8rem;font-weight:700;margin-bottom:.4rem}}
.header p{{opacity:.85;font-size:.95rem}}
nav{{background:#fff;border-bottom:1px solid var(--border);padding:.6rem 1.5rem;position:sticky;top:0;z-index:99;display:flex;gap:1rem;flex-wrap:wrap}}
nav a{{text-decoration:none;color:#475569;font-size:.85rem;padding:.3rem .7rem;border-radius:4px}}
nav a:hover{{background:#eff6ff;color:var(--blue)}}
.container{{max-width:1400px;margin:0 auto;padding:1.5rem}}
section{{margin-bottom:3rem;scroll-margin-top:60px}}
h2{{font-size:1.35rem;font-weight:700;margin-bottom:.5rem;padding-bottom:.5rem;border-bottom:2px solid var(--blue)}}
h3{{font-size:1.05rem;font-weight:600;margin:.8rem 0 .4rem}}
.desc{{font-size:.9rem;color:#475569;margin-bottom:1rem}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:1.2rem;box-shadow:0 1px 3px rgba(0,0,0,.06);margin-bottom:1.5rem}}
.insight{{background:#eff6ff;border-left:4px solid var(--blue);padding:.8rem 1rem;border-radius:0 6px 6px 0;margin-bottom:.8rem;font-size:.88rem}}
.warning{{background:#fffbeb;border-left:4px solid #f59e0b;padding:.8rem 1rem;border-radius:0 6px 6px 0;margin-bottom:.8rem;font-size:.88rem}}
table{{width:100%;border-collapse:collapse;font-size:.88rem}}
th{{background:#f1f5f9;padding:.5rem .9rem;text-align:left;font-weight:600;border-bottom:2px solid var(--border)}}
td{{padding:.45rem .9rem;border-bottom:1px solid #f1f5f9;vertical-align:top}}
tr:last-child td{{border-bottom:none}}
.ctrls{{display:flex;gap:.6rem;flex-wrap:wrap;margin-bottom:.8rem;align-items:center}}
.ctrls label{{font-size:.82rem;color:#475569;font-weight:500}}
.ctrls select{{padding:.3rem .6rem;border:1px solid var(--border);border-radius:5px;font-size:.82rem;background:#fff}}
.search-box{{padding:.45rem .8rem;border:1px solid var(--border);border-radius:5px;font-size:.88rem;width:280px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem}}
.stat-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:1.5rem}}
.stat-card{{background:#fff;border:1px solid var(--border);border-radius:8px;padding:1rem;text-align:center}}
.stat-card .val{{font-size:1.6rem;font-weight:700;color:var(--blue)}}
.stat-card .lbl{{font-size:.78rem;color:#64748b;text-transform:uppercase}}
.avail-row{{display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:1rem}}
@media(max-width:800px){{.grid2,.stat-grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="header">
  <h1>📐 Embedding Method Comparison — Analysis Report</h1>
  <p>TF-IDF + LSA vs Sentence Transformers vs Voyage AI · 695 books · Full metric analysis</p>
</div>
<nav>
  <a href="#status">Status</a>
  <a href="#metrics">📊 Metrics</a>
  <a href="#scatter">🗺 Scatter</a>
  <a href="#neighbours">🔗 Neighbours</a>
  <a href="#disagree">⚡ Disagreements</a>
  <a href="#clusters">📦 Clusters</a>
  <a href="#findings">💡 Findings</a>
</nav>
<div class="container">

<!-- Status -->
<section id="status">
  <h2>Method Status</h2>
  <div class="avail-row">
    {' '.join(method_status_badge(m) for m in 'ABCD')}
  </div>
  {_missing_warning}
  <div class="stat-grid">
    <div class="stat-card"><div class="val">{len(book_ids)}</div><div class="lbl">Books</div></div>
    <div class="stat-card"><div class="val">{len(avail)}</div><div class="lbl">Methods run</div></div>
    <div class="stat-card"><div class="val">{len(zero_bids)}</div><div class="lbl">Empty-summary books</div></div>
    <div class="stat-card"><div class="val">{ari_ab:.3f}</div><div class="lbl">A vs B Adj. Rand Index</div></div>
  </div>
</section>

<!-- Metrics -->
<section id="metrics">
  <h2>1 · Clustering Quality Metrics</h2>
  <p class="desc">K-Means at best k (silhouette sweep k=3..10). Bold blue = best per metric.</p>
  <div class="card">
    <table>
      <thead><tr>
        <th>Metric</th>
        <th><span style="background:#2563eb;color:#fff;padding:.15rem .5rem;border-radius:3px">A</span> TF-IDF + LSA 100d</th>
        <th><span style="background:#16a34a;color:#fff;padding:.15rem .5rem;border-radius:3px">B</span> TF-IDF + LSA 384d</th>
        <th><span style="background:#dc2626;color:#fff;padding:.15rem .5rem;border-radius:3px">C</span> Sentence Transformers</th>
        <th><span style="background:#d97706;color:#fff;padding:.15rem .5rem;border-radius:3px">D</span> Voyage AI</th>
      </tr></thead>
      <tbody>
        <tr><td>Best k</td>{''.join(f'<td>{methods[m].get("best_k","—")}</td>' if m in avail else '<td style="color:#94a3b8">—</td>' for m in "ABCD")}</tr>
        <tr><td>Dimensions</td>{''.join(f'<td>{methods[m].get("dims","—")}</td>' if m in avail else '<td style="color:#94a3b8">—</td>' for m in "ABCD")}</tr>
        <tr><td>Time (s)</td>{''.join(f'<td>{methods[m].get("time","—")}</td>' if m in avail else '<td style="color:#94a3b8">—</td>' for m in "ABCD")}</tr>
        {mrow('Silhouette ↑', 'silhouette', True)}
        {mrow('Davies-Bouldin ↓', 'davies_bouldin', False)}
        {mrow('Calinski-Harabász ↑', 'calinski_harabasz', True)}
        {mrow('Intra-cluster sim ↑', 'intra_sim', True)}
        {mrow('Inter-cluster sim ↓', 'inter_sim', False)}
      </tbody>
    </table>
  </div>
  <div class="insight">
    <strong>A vs B:</strong> LSA 384d scores consistently worse than LSA 100d on all cluster quality
    metrics (silhouette 0.014 vs 0.037, Davies-Bouldin 6.18 vs 4.22). More dimensions from the same
    TF-IDF vocabulary introduce noise rather than signal — the vocabulary is the ceiling, not the
    dimensionality. Adjusted Rand Index between A and B clusters: <strong>{ari_ab:.4f}</strong>
    (moderate agreement — they broadly agree on groupings but differ on ~48% of nearest neighbours).
  </div>
  <div class="insight">
    <strong>Low silhouette scores overall ({methods['A']['silhouette']:.3f}–{methods['B']['silhouette']:.3f})
    are expected</strong>, not a failure. The cybernetics corpus spans pure mathematics, ecology,
    management science, philosophy, and fiction — no clean cluster boundaries exist. This score
    range is typical for highly interdisciplinary academic corpora.
  </div>
</section>

<!-- Scatter -->
<section id="scatter">
  <h2>2 · 2D Semantic Map (LSA projection)</h2>
  <p class="desc">Colour by LDA topic or K-Means cluster assignment from any method.</p>
  <div class="ctrls">
    <label>Colour by:</label>
    <select id="sc_col" onchange="drawScatter()">
      <option value="lda">LDA topic</option>
      {''.join(f'<option value="{m}">Method {m} clusters</option>' for m in avail)}
    </select>
  </div>
  <div class="card" id="scatter_div"></div>
</section>

<!-- Neighbours -->
<section id="neighbours">
  <h2>3 · Nearest Neighbours Explorer</h2>
  <p class="desc">Compare what each method considers the closest books. Differences reveal where
  lexical similarity and structural similarity diverge.</p>
  <div class="ctrls">
    <input class="search-box" id="nbr_q" type="text" placeholder="Search book title…" oninput="filterBooks()">
    <label style="margin-left:.6rem">Show empty-summary books:</label>
    <select id="nbr_zero" onchange="filterBooks()">
      <option value="0">Hide (they have sim=0.000 in LSA)</option>
      <option value="1">Show</option>
    </select>
  </div>
  <div id="nbr_list" style="max-height:200px;overflow-y:auto;margin-bottom:.8rem;
       border:1px solid var(--border);border-radius:6px"></div>
  <div id="nbr_detail"></div>
</section>

<!-- Disagreements -->
<section id="disagree">
  <h2>4 · Method A vs B Disagreements</h2>
  <p class="desc">Books where A and B pick a different top-1 nearest neighbour (48% of books,
  excluding the 6 empty-summary books). Shows where dimensionality changes the similarity ranking.</p>
  <div class="warning">
    <strong>6 books have zero LSA similarity</strong> (IDs: {', '.join(sorted(zero_bids))}) because
    their summaries are empty — the API failed during summary generation. In LSA, an empty document
    has no TF-IDF features and therefore zero cosine similarity to everything. Sentence transformers
    would handle these gracefully using title-level semantics.
  </div>
  <div class="card">
    <table>
      <thead><tr>
        <th>Book (LDA topic)</th>
        <th><span style="background:#2563eb;color:#fff;padding:.1rem .5rem;border-radius:3px">A</span>
            LSA 100d → nearest</th>
        <th><span style="background:#16a34a;color:#fff;padding:.1rem .5rem;border-radius:3px">B</span>
            LSA 384d → nearest</th>
      </tr></thead>
      <tbody>{sample_rows}</tbody>
    </table>
  </div>
</section>

<!-- Cluster vs LDA -->
<section id="clusters">
  <h2>5 · Cluster × LDA Topic Alignment</h2>
  <p class="desc">How do K-Means clusters map to LDA topics? A diagonal-heavy heatmap means the
  two methods agree. Cluster purity: A={purity(cl_labels['A']):.3f}, B={purity(cl_labels['B']):.3f}
  (fraction of books in each cluster's dominant LDA topic).</p>
  <div class="ctrls">
    <label>Method:</label>
    <select id="cl_m" onchange="drawHeatmap()">
      {''.join(f'<option value="{m}">Method {m} — {MNAME[m]}</option>' for m in avail)}
    </select>
  </div>
  <div class="card" id="heatmap_div"></div>
</section>

<!-- Findings -->
<section id="findings">
  <h2>6 · Key Findings & Recommendations</h2>
  <div class="grid2">
    <div class="card">
      <h3>📌 What the results show</h3>
      <ul style="font-size:.88rem;padding-left:1.2rem;line-height:1.8">
        {findings_items}
      </ul>
    </div>
    <div class="card">
      <h3>🔮 What to do next</h3>
      <ul style="font-size:.88rem;padding-left:1.2rem;line-height:1.8">
        {next_items}
      </ul>
    </div>
  </div>
</section>

</div>
<footer style="text-align:center;padding:1.5rem;color:#94a3b8;font-size:.8rem;
  border-top:1px solid var(--border);margin-top:2rem">
  Embedding Comparison · {len(book_ids)} books · Methods run: {', '.join(avail)} · Plotly.js
</footer>

<script>
const R   = {j_r};
const PAL = {j_pal};
const AVAIL = {j_avail};
const ZERO_BIDS = {j_zero};
const LAYOUT = {{paper_bgcolor:'transparent',plot_bgcolor:'#f8fafc',
                 hoverlabel:{{bgcolor:'#1e293b',font:{{color:'white',size:12}}}}}};

// ── Scatter ───────────────────────────────────────────────────────────────────
function drawScatter() {{
  const colBy = document.getElementById('sc_col').value;
  const xy    = R.coords_2d_lsa;
  const groups = colBy === 'lda' ? R.lda_topics : R.cluster_labels[colBy];
  const n_g   = Math.max(...groups) + 1;
  const traces = [];
  for (let g=0; g<n_g; g++) {{
    const idx = groups.map((v,i)=>v===g?i:-1).filter(i=>i>=0);
    if (!idx.length) continue;
    const nm = colBy==='lda' ? (R.lda_names[g]||'T'+(g+1)) : 'Cluster '+(g+1);
    traces.push({{
      x:idx.map(i=>xy[i][0]), y:idx.map(i=>xy[i][1]),
      mode:'markers', type:'scatter', name:nm,
      marker:{{color:PAL[g%PAL.length],size:8,opacity:.75,line:{{color:'white',width:0.5}}}},
      text:idx.map(i=>`<b>${{R.titles[i].substring(0,50)}}</b><br>${{R.authors[i]}}<br>${{R.pub_years[i]||''}}`),
      hovertemplate:'%{{text}}<extra></extra>',
    }});
  }}
  Plotly.react('scatter_div', traces, {{
    ...LAYOUT, height:520,
    margin:{{t:10,b:60,l:60,r:20}},
    xaxis:{{title:'LSA Dim 1',zeroline:false}},
    yaxis:{{title:'LSA Dim 2',zeroline:false}},
    legend:{{orientation:'h',y:-0.2,font:{{size:9}}}},
  }});
}}
drawScatter();

// ── Neighbours ────────────────────────────────────────────────────────────────
function filterBooks() {{
  const q      = document.getElementById('nbr_q').value.toLowerCase();
  const showZ  = document.getElementById('nbr_zero').value === '1';
  const list   = document.getElementById('nbr_list');
  list.innerHTML = '';
  R.book_ids.forEach((bid,i) => {{
    if (!showZ && ZERO_BIDS.includes(bid)) return;
    if (q && !R.titles[i].toLowerCase().includes(q)) return;
    const d = document.createElement('div');
    d.style.cssText = 'padding:.3rem .8rem;cursor:pointer;font-size:.84rem;border-bottom:1px solid #f1f5f9';
    const isZ = ZERO_BIDS.includes(bid);
    d.innerHTML = R.titles[i] + (isZ ? ' <span style="color:#f59e0b;font-size:.75rem">⚠ empty summary</span>' : '');
    d.onclick = () => showNeighbours(i);
    list.appendChild(d);
  }});
}}

function showNeighbours(idx) {{
  const MNAME = {{A:'LSA 100d', B:'LSA 384d', C:'SentTrans', D:'Voyage AI'}};
  const MCOL  = {{A:'#2563eb', B:'#16a34a', C:'#dc2626', D:'#d97706'}};
  const bid   = R.book_ids[idx];
  const isZ   = ZERO_BIDS.includes(bid);
  let html = `<div style="font-weight:700;margin-bottom:.5rem;font-size:.95rem">${{R.titles[idx]}}</div>`;
  if (isZ) html += '<div style="background:#fffbeb;border-left:3px solid #f59e0b;padding:.4rem .8rem;margin-bottom:.5rem;font-size:.82rem">⚠ This book has an empty summary — LSA similarities will be 0.000</div>';
  AVAIL.forEach(m => {{
    const nbr = R.neighbours[m];
    if (!nbr) return;
    html += `<div style="background:#f8fafc;border:1px solid var(--border);border-radius:6px;padding:.6rem .9rem;margin-bottom:.4rem">
      <span style="background:${{MCOL[m]}};color:#fff;padding:.1rem .4rem;border-radius:3px;font-size:.78rem;font-weight:700">${{m}}</span>
      <strong style="font-size:.84rem;margin-left:.4rem">${{MNAME[m]}}</strong>`;
    nbr[idx].forEach((n,j) => {{
      html += `<div style="padding:.15rem 0 .15rem 1rem;font-size:.82rem">${{j+1}}. ${{R.titles[n.idx].substring(0,60)}}
        <span style="float:right;color:#2563eb;font-weight:600">${{n.sim.toFixed(3)}}</span></div>`;
    }});
    html += '</div>';
  }});
  document.getElementById('nbr_detail').innerHTML = html;
}}
filterBooks();
if (R.titles.length > 0) showNeighbours(0);

// ── Cluster heatmap ───────────────────────────────────────────────────────────
function drawHeatmap() {{
  const m  = document.getElementById('cl_m').value;
  const cl = R.cluster_labels[m];
  if (!cl) return;
  const n_lda = R.lda_names.length;
  const n_cl  = Math.max(...cl) + 1;
  const mat   = Array.from({{length:n_cl}},()=>Array(n_lda).fill(0));
  cl.forEach((c,i) => mat[c][R.lda_topics[i]]++);
  const tot   = mat.map(r=>r.reduce((a,b)=>a+b,0));
  const z     = mat.map((r,i)=>r.map(v=>tot[i]>0?+(v/tot[i]).toFixed(3):0));
  const ann   = [];
  z.forEach((r,i)=>r.forEach((v,j)=>{{
    if(v>0) ann.push({{x:j,y:i,text:`${{(v*100).toFixed(0)}}%`,showarrow:false,
      font:{{size:9,color:v>0.4?'white':'#1e3a5f'}}}});
  }}));
  Plotly.react('heatmap_div',[{{
    z, x:R.lda_names, y:mat.map((_,i)=>'Cluster '+(i+1)),
    type:'heatmap',
    colorscale:[[0,'#f0f9ff'],[0.3,'#7dd3fc'],[0.6,'#2563eb'],[1,'#1e3a5f']],
    hovertemplate:'Cluster %{{y}}<br>%{{x}}: %{{z:.0%}}<extra></extra>',
  }}],{{
    ...LAYOUT, height:Math.max(300,n_cl*36+140),
    margin:{{t:10,b:130,l:90,r:20}},
    xaxis:{{tickangle:-40,tickfont:{{size:9}}}},
    annotations:ann,
  }});
}}
drawHeatmap();
</script>
</body></html>"""

html = html.replace('</body>', _PROV_NOTICE + '\n</body>', 1)
with open(str(_pl.Path('data/outputs/book_nlp_embedding_comparison.html')),'w',encoding='utf-8') as f:
    f.write(html)
print(f"Saved: {len(html)//1024} KB")