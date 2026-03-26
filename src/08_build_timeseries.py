"""


08_build_timeseries.py
─────────────────────────────────────────────────────────────────────────────
Builds a self-contained interactive HTML report of publication-year time
series charts. All charts use Plotly.js (loaded from CDN).

Charts:
  1. Publications per year (bar) with 5-year rolling average
  2. Topic mix over time — stacked area (book-level LDA topics by year)
  3. NMF topic mix over time — stacked area (chapter-level, by book pub year)
  4. Cluster composition over time — stacked bar by decade
  5. Scatter: year vs LSA dimension 1 (coloured by topic)
  6. Cumulative publications by topic over time

Input:  nlp_results.json, nlp_results_chapters.json, summaries.json
Output: data/outputs/book_nlp_timeseries.html
"""
# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_lang.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)



import json
import numpy as np
from collections import defaultdict


# ── Verify working directory has required data files ────────────────────────
import os as _os
if not _os.path.exists(str(JSON_DIR / 'books_clean.json')):
    print('ERROR: books_clean.json not found in current directory.')
    print(f'Run this script from your project root, not from {_os.getcwd()}')
    print('Example: cd /path/to/project && python3 src/generate_summaries_api.py')
    import sys as _sys; _sys.exit(1)

with open(str(JSON_DIR / 'nlp_results.json'))          as f: R  = json.load(f)
with open(str(JSON_DIR / 'nlp_results_chapters.json')) as f: RC = json.load(f)
with open(str(JSON_DIR / 'summaries.json'))            as f: S  = json.load(f)

book_ids   = R['book_ids']
titles     = R['titles']
authors    = R.get('authors', ['Unknown'] * len(book_ids))
# pub_years: load from nlp_results.json if present, else derive from books_clean.json
if 'pub_years' in R:
    pub_years = R['pub_years']
else:
    import re as _re
    try:
        with open(str(JSON_DIR / 'books_clean.json')) as _f:
            _BC = json.load(_f)
        pub_years = []
        for _bid in book_ids:
            _raw = _BC.get(_bid, {}).get('pub_year') or _BC.get(_bid, {}).get('pubdate', '')
            _m = _re.search(r'\b(19|20)\d{2}\b', str(_raw)) if _raw else None
            pub_years.append(int(_m.group()) if _m else None)
    except FileNotFoundError:
        pub_years = [None] * len(book_ids)
        print('  [08] Warning: pub_years missing from nlp_results.json and '
              'books_clean.json not found — re-run 03_nlp_pipeline.py')
dominant   = R['dominant_topics']
clusters   = R.get('cluster_labels', [0] * len(book_ids))
doc_topic  = np.array(R['doc_topic'])
n_topics   = R['n_topics']
best_k     = R['best_k']
coords_2d  = R.get('coords_2d', [[0,0]] * len(book_ids))
n_topics_ch = RC.get('n_topics', 6)
dom_ch     = RC.get('dominant_topics', [0] * len(RC.get('chapters', [])))
# pub_years_per_ch: load defensively — three fallback levels
if 'pub_years_per_ch' in RC:
    pub_years_ch = RC['pub_years_per_ch']
elif 'book_id_per_ch' in RC:
    _py_map = dict(zip(book_ids, pub_years))
    pub_years_ch = [_py_map.get(bid) for bid in RC['book_id_per_ch']]
else:
    _py_map = dict(zip(book_ids, pub_years))
    pub_years_ch = [_py_map.get(ch.get('book_id'))
                    for ch in RC.get('chapters', [])]
if not pub_years_ch:
    pub_years_ch = [None] * len(RC.get('dominant_topics', []))
    print('  [08] Warning: could not derive pub_years_ch — '  
          're-run 03_nlp_pipeline_chapters.py')

PALETTE = ['#2563eb','#16a34a','#dc2626','#d97706','#7c3aed',
           '#0891b2','#be185d','#0f766e','#c2410c','#065f46',
           '#9333ea','#0369a1']

_BASE_CH = [
    'Human & Social Experience',
    'Mathematical & Formal Systems',
    'General Systems Theory',
    'History & Philosophy of Cybernetics',
    'Management & Organisational Cybernetics',
    'Control Theory & Engineering',
    'Topic 7', 'Topic 8', 'Topic 9']
TOPIC_NAMES_CH = (_BASE_CH + [f'Topic {i+1}' for i in range(9,25)])[:n_topics_ch]

# ── Helper: filter to valid years ─────────────────────────────────────────────
valid = [(i, pub_years[i]) for i in range(len(book_ids)) if pub_years[i]]
valid_years   = sorted(set(y for _,y in valid))
year_min, year_max = min(valid_years), max(valid_years)
all_years = list(range(year_min, year_max + 1))

# ── Chart 1 data: publications per year + 5yr rolling avg ────────────────────
count_by_year = defaultdict(int)
for _, y in valid:
    count_by_year[y] += 1
counts = [count_by_year.get(y, 0) for y in all_years]
# 5-year rolling average
window = 5
rolling = []
for i in range(len(all_years)):
    w = counts[max(0,i-window//2): i+window//2+1]
    rolling.append(round(sum(w)/len(w), 2))

# Hover text for each year bar: list titles
year_to_titles = defaultdict(list)
for i, y in valid:
    year_to_titles[y].append(f"{titles[i][:45]} ({authors[i].split(',')[0]})")
bar_hover = [('<br>').join(year_to_titles.get(y,[])) for y in all_years]

chart1 = json.dumps({
    'years': all_years, 'counts': counts, 'rolling': rolling,
    'hover': bar_hover,
})

_LDA_BASE = ['Human & Social Experience', 'Mathematical & Formal Systems',
             'General Systems Theory', 'History & Philosophy of Cybernetics',
             '2nd-Order Cybernetics & Bateson', 'Control Theory & Engineering',
             'Popular & Applied Cybernetics']
LDA_NAMES = (R.get('topic_names') or (_LDA_BASE + [f'Topic {i+1}' for i in range(len(_LDA_BASE), n_topics)]))[:n_topics]

# ── Chart 2 data: LDA topic mix by year (stacked area, book-level) ────────────
# For each year, sum topic proportions across books published that year
topic_by_year = {t: defaultdict(float) for t in range(n_topics)}
count_by_year2 = defaultdict(int)
for i, y in valid:
    count_by_year2[y] += 1
    for t in range(n_topics):
        topic_by_year[t][y] += doc_topic[i, t]
# Normalise to proportion
topic_props = {}
for t in range(n_topics):
    topic_props[t] = [
        round(topic_by_year[t].get(y, 0) / max(count_by_year2.get(y, 1), 1), 4)
        for y in all_years
    ]
chart2 = json.dumps({
    'years':     all_years,
    'topics':    topic_props,
    'n_topics':  n_topics,
    'palette':   PALETTE,
    'lda_names': LDA_NAMES[:n_topics],
})

# ── Chart 3 data: NMF chapter topic mix by book pub year ─────────────────────
ch_topic_by_year = {t: defaultdict(int) for t in range(n_topics_ch)}
ch_count_by_year = defaultdict(int)
for i, y in enumerate(pub_years_ch):
    if not y: continue
    ch_count_by_year[y] += 1
    ch_topic_by_year[dom_ch[i]][y] += 1
ch_topic_props = {}
for t in range(n_topics_ch):
    ch_topic_props[t] = [
        round(ch_topic_by_year[t].get(y, 0) / max(ch_count_by_year.get(y, 1), 1), 4)
        for y in all_years
    ]
chart3 = json.dumps({
    'years': all_years,
    'topics': ch_topic_props,
    'n_topics': n_topics_ch,
    'topic_names': TOPIC_NAMES_CH,
    'palette': PALETTE,
})

# ── Chart 4 data: cluster composition by decade ───────────────────────────────
decades = sorted(set((y // 10) * 10 for _, y in valid))
cluster_by_decade = {c: defaultdict(int) for c in range(best_k)}
for i, y in valid:
    d = (y // 10) * 10
    cluster_by_decade[clusters[i]][d] += 1
chart4 = json.dumps({
    'decades': [f'{d}s' for d in decades],
    'clusters': {str(c): [cluster_by_decade[c].get(d, 0) for d in decades]
                 for c in range(best_k)},
    'best_k': best_k,
    'palette': PALETTE,
})

# ── Chart 5 data: year vs LSA dim (scatter, coloured by topic) ───────────────
chart5 = json.dumps({
    'years':   [pub_years[i] for i, _ in valid],
    'x':       [coords_2d[i][0] for i, _ in valid],
    'y':       [coords_2d[i][1] for i, _ in valid],
    'titles':  [titles[i] for i, _ in valid],
    'authors': [authors[i] for i, _ in valid],
    'topics':  [dominant[i] for i, _ in valid],
    'n_topics': n_topics,
    'palette': PALETTE,
})

# ── Chart 6 data: cumulative publications by dominant topic ───────────────────
cum_by_topic = {}
for t in range(n_topics):
    running = 0
    cumvals = []
    for y in all_years:
        running += sum(1 for i, yr in valid if yr == y and dominant[i] == t)
        cumvals.append(running)
    cum_by_topic[t] = cumvals
chart6 = json.dumps({
    'years':     all_years,
    'topics':    cum_by_topic,
    'n_topics':  n_topics,
    'palette':   PALETTE,
    'lda_names': LDA_NAMES[:n_topics],
})

# ── Chart 7 data: index-term band prevalence + concept velocity ──────────────────
try:
    with open(str(JSON_DIR / 'index_analysis.json')) as _f:
        _IA = json.load(_f)
    with open(str(JSON_DIR / 'concept_velocity.json')) as _f:
        _CV = json.load(_f)
    _all_items   = sorted(_IA['vocab'].items(),
                          key=lambda x: x[1]['n_books'], reverse=True)
    _total       = len(_all_items)
    _anchor_keys = {tl for tl, _ in _all_items[:int(_total*0.05)]}
    _signal_keys = {tl for tl, _ in _all_items[int(_total*0.05):int(_total*0.40)]}
    _front_keys  = {tl for tl, _ in _all_items[int(_total*0.40):]
                    if _['n_books'] >= 2}
    _band_dec = {'Anchor': {}, 'Signal': {}, 'Frontier': {}}
    for _dec in decades:
        _dbids = [book_ids[i] for i, y in valid if (y // 10) * 10 == _dec]
        if not _dbids: continue
        for _bname, _bkeys in [('Anchor', _anchor_keys),
                               ('Signal', _signal_keys),
                               ('Frontier', _front_keys)]:
            _cts = [len({t.lower() for t in _IA['book_terms'].get(b, [])}
                        & _bkeys) for b in _dbids]
            _band_dec[_bname][_dec] = round(sum(_cts)/len(_cts),2) if _cts else 0
    _vel_items = sorted(
        [(tl, vd) for tl, vd in _CV.items()
         if len(vd['decades']) >= 3
         and len({vd['decades'][d]['topic'] for d in vd['decades']}) > 1],
        key=lambda x: len({x[1]['decades'][d]['topic']
                           for d in x[1]['decades']}), reverse=True)[:12]
    chart7 = json.dumps({
        'decades':    [f'{d}s' for d in decades],
        'band_means': {b: [_band_dec[b].get(d,0) for d in decades]
                       for b in ('Anchor','Signal','Frontier')},
        'band_cols':  {'Anchor':'#2563eb','Signal':'#16a34a','Frontier':'#d97706'},
        'vel_terms':  [{'term':vd['term'],'key':tl,
                        'decades':{d:vd['decades'][d] for d in vd['decades']},
                        'total':vd['total_books']} for tl,vd in _vel_items],
        'lda_names':  LDA_NAMES[:n_topics],
        'palette':    PALETTE,
    })
    print(f'  Chart 7: {len(_vel_items)} velocity terms ready')
except Exception as _e:
    chart7 = '{}'
    print(f'  Chart 7 skipped: {_e}')

# ── Assemble HTML ─────────────────────────────────────────────────────────────
total_with_year = len(valid)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Book Corpus — Publication Year Analysis</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.27.0/plotly.min.js"></script>
<style>
:root{{--blue:#2563eb;--bg:#f8fafc;--card:#fff;--border:#e2e8f0}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:#1e293b;line-height:1.6}}
.header{{background:linear-gradient(135deg,#1e3a5f,#2563eb);color:#fff;padding:2.5rem 2rem;text-align:center}}
.header h1{{font-size:1.9rem;font-weight:700;margin-bottom:.4rem}}
.header p{{opacity:.85;font-size:.95rem}}
.stats-bar{{display:flex;justify-content:center;gap:2rem;background:#1e293b;color:#fff;padding:.8rem;flex-wrap:wrap}}
.stat{{text-align:center}}.stat span{{display:block;font-size:1.4rem;font-weight:700;color:#60a5fa}}
.stat small{{font-size:.75rem;opacity:.7;text-transform:uppercase}}
nav{{background:#fff;border-bottom:1px solid var(--border);padding:.6rem 1.5rem;position:sticky;top:0;z-index:99;display:flex;gap:1rem;flex-wrap:wrap}}
nav a{{text-decoration:none;color:#475569;font-size:.85rem;padding:.3rem .7rem;border-radius:4px;transition:all .2s}}
nav a:hover{{background:#eff6ff;color:var(--blue)}}
.container{{max-width:1300px;margin:0 auto;padding:1.5rem}}
section{{margin-bottom:3rem}}
h2{{font-size:1.35rem;font-weight:700;color:#1e293b;margin-bottom:.5rem;padding-bottom:.5rem;border-bottom:2px solid var(--blue)}}
.desc{{font-size:.9rem;color:#475569;margin-bottom:1rem}}
.chart-wrap{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:1.2rem;box-shadow:0 1px 3px rgba(0,0,0,.06);margin-bottom:1.5rem}}
.chart-controls{{display:flex;gap:.6rem;flex-wrap:wrap;margin-bottom:.6rem;align-items:center}}
.chart-controls label{{font-size:.82rem;color:#475569;font-weight:500}}
.chart-controls select{{padding:.3rem .6rem;border:1px solid var(--border);border-radius:5px;font-size:.82rem;background:#fff}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem}}
@media(max-width:800px){{.grid2{{grid-template-columns:1fr}}}}
</style>
</head>
<body>

<div class="header">
  <h1>📅 Publication Year Analysis</h1>
  <p>Topic trends · Cluster evolution · Temporal distribution across the corpus</p>
</div>
<div class="stats-bar">
  <div class="stat"><span>{len(book_ids)}</span><small>Books</small></div>
  <div class="stat"><span>{total_with_year}</span><small>With valid year</small></div>
  <div class="stat"><span>{year_min}</span><small>Earliest</small></div>
  <div class="stat"><span>{year_max}</span><small>Latest</small></div>
  <div class="stat"><span>{year_max - year_min + 1}</span><small>Year span</small></div>
</div>
<nav>
  <a href="#publications">📊 Publications/yr</a>
  <a href="#lda-topics">🏷 LDA Topics</a>
  <a href="#nmf-topics">🔬 NMF Topics</a>
  <a href="#clusters">🗂 Clusters</a>
  <a href="#scatter">🗺 Scatter</a>
  <a href="#cumulative">📈 Cumulative</a>
</nav>

<div class="container">

<!-- Chart 1 -->
<section id="publications">
  <h2>1 · Publications per Year</h2>
  <p class="desc">Number of books published each year. Hover a bar to see titles. The line shows a 5-year rolling average.</p>
  <div class="chart-wrap" id="chart1"></div>
</section>

<!-- Chart 2 -->
<section id="lda-topics">
  <h2>2 · LDA Topic Mix Over Time (book-level)</h2>
  <p class="desc">Average proportion of each LDA topic across books published each year. Shows how the intellectual focus of the corpus shifted over time.</p>
  <div class="chart-controls">
    <label>Display:</label>
    <select id="lda_mode" onchange="updateLDA()">
      <option value="area">Stacked area</option>
      <option value="line">Lines</option>
      <option value="bar">Stacked bar</option>
    </select>
  </div>
  <div class="chart-wrap" id="chart2"></div>
</section>

<!-- Chart 3 -->
<section id="nmf-topics">
  <h2>3 · NMF Chapter Topic Mix Over Time (chapter-level)</h2>
  <p class="desc">Proportion of chapters assigned to each NMF topic, grouped by the book's publication year.</p>
  <div class="chart-controls">
    <label>Display:</label>
    <select id="nmf_mode" onchange="updateNMF()">
      <option value="area">Stacked area</option>
      <option value="line">Lines</option>
      <option value="bar">Stacked bar</option>
    </select>
  </div>
  <div class="chart-wrap" id="chart3"></div>
</section>

<!-- Chart 4 -->
<section id="clusters">
  <h2>4 · Cluster Composition by Decade</h2>
  <p class="desc">How many books per cluster were published in each decade.</p>
  <div class="chart-controls">
    <label>Display:</label>
    <select id="cluster_mode" onchange="updateClusters()">
      <option value="stack">Stacked</option>
      <option value="group">Grouped</option>
      <option value="pct">100% stacked</option>
    </select>
  </div>
  <div class="chart-wrap" id="chart4"></div>
</section>

<!-- Chart 5 -->
<section id="scatter">
  <h2>5 · Publication Year vs Semantic Position</h2>
  <p class="desc">Each point is a book. X-axis = publication year, Y-axis = LSA semantic dimension 1. Coloured by dominant LDA topic. Hover for details.</p>
  <div class="chart-controls">
    <label>Colour by:</label>
    <select id="scatter_colour" onchange="updateScatter5()">
      <option value="topic">LDA Topic</option>
      <option value="cluster">Cluster</option>
    </select>
    <label style="margin-left:.8rem">Y-axis:</label>
    <select id="scatter_y" onchange="updateScatter5()">
      <option value="lsa1">LSA Dim 1</option>
      <option value="lsa2">LSA Dim 2</option>
    </select>
  </div>
  <div class="chart-wrap" id="chart5"></div>
</section>

<!-- Chart 6 -->
<section id="cumulative">
  <h2>6 · Cumulative Publications by Topic</h2>
  <p class="desc">Running total of books per dominant LDA topic, showing when each topic entered the corpus and how it grew.</p>
  <div class="chart-wrap" id="chart6"></div>
</section>

<section id="bands">
  <h2>7 · Index-Term Band Prevalence &amp; Concept Velocity</h2>
  <p class="desc">
    <strong>Left:</strong> Mean Anchor / Signal / Frontier index terms per book per decade —
    tracks whether the field’s conceptual core is stable, expanding, or shifting.<br>
    <strong>Right:</strong> How a term’s dominant LDA topic shifts across decades
    (Concept Velocity).
  </p>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem">
    <div class="card" style="padding:1rem"><div id="c7_band"></div></div>
    <div class="card" style="padding:1rem">
      <div style="margin-bottom:.5rem;display:flex;align-items:center;gap:.5rem">
        <label style="font-size:.82rem;color:#475569;font-weight:500">Term:</label>
        <select id="c7_sel" onchange="drawVel()"
          style="padding:.3rem .6rem;border:1px solid var(--border);border-radius:5px;font-size:.82rem;background:#fff"></select>
      </div>
      <div id="c7_vel"></div>
    </div>
  </div>
</section>

</div>

<footer style="text-align:center;padding:1.5rem;color:#94a3b8;font-size:.8rem;border-top:1px solid var(--border);margin-top:2rem">
  Book NLP Pipeline · Time Series Analysis · {total_with_year} books · {year_min}–{year_max} · Plotly.js
</footer>

<script>
const C1 = {chart1};
const C2 = {chart2};
const C3 = {chart3};
const C4 = {chart4};
const C5 = {chart5};
const C6 = {chart6};
const C7 = {chart7};
const PAL = {json.dumps(PALETTE)};

const LAYOUT_BASE = {{
  paper_bgcolor: 'transparent',
  plot_bgcolor:  '#f8fafc',
  margin: {{t:20, b:60, l:60, r:20}},
  hoverlabel: {{bgcolor:'#1e293b', font:{{color:'white', size:12}}}},
  legend: {{orientation:'h', y:-0.25}},
}};

// ── Chart 1: Publications per year ───────────────────────────────────────────
Plotly.newPlot('chart1', [
  {{
    x: C1.years, y: C1.counts, type: 'bar', name: 'Books published',
    marker: {{color: '#2563eb', opacity: 0.75}},
    text: C1.hover,
    hovertemplate: '<b>%{{x}}</b>: %{{y}} books<br><br>%{{text}}<extra></extra>',
  }},
  {{
    x: C1.years, y: C1.rolling, type: 'scatter', mode: 'lines', name: '5-yr avg',
    line: {{color: '#dc2626', width: 2.5, dash: 'dot'}},
    hovertemplate: '<b>%{{x}}</b>: %{{y:.1f}} (5-yr avg)<extra></extra>',
  }}
], {{...LAYOUT_BASE, height: 380,
     xaxis: {{title: 'Publication Year'}},
     yaxis: {{title: 'Number of Books'}},
     barmode: 'overlay',
}});

// ── Chart 2: LDA topic mix over time ─────────────────────────────────────────
function buildLDATraces(mode) {{
  return Array.from({{length: C2.n_topics}}, (_, t) => ({{
    x: C2.years, y: C2.topics[t], name: C2.lda_names?C2.lda_names[t]:`Topic ${{t+1}}`,
    type: mode === 'bar' ? 'bar' : 'scatter',
    mode: mode === 'line' ? 'lines' : undefined,
    stackgroup: (mode === 'area' || mode === 'bar') ? 'one' : undefined,
    fill: mode === 'area' ? 'tonexty' : undefined,
    line: {{color: PAL[t % PAL.length], width: 2}},
    marker: {{color: PAL[t % PAL.length]}},
    hovertemplate: `Topic ${{t+1}}: %{{y:.1%}}<br>Year: %{{x}}<extra></extra>`,
  }}));
}}
function updateLDA() {{
  const mode = document.getElementById('lda_mode').value;
  Plotly.react('chart2', buildLDATraces(mode), {{
    ...LAYOUT_BASE, height: 380,
    barmode: 'stack',
    xaxis: {{title: 'Publication Year'}},
    yaxis: {{title: 'Avg topic proportion', tickformat: '.0%'}},
  }});
}}
updateLDA();

// ── Chart 3: NMF chapter topic mix over time ──────────────────────────────────
function buildNMFTraces(mode) {{
  return Array.from({{length: C3.n_topics}}, (_, t) => ({{
    x: C3.years, y: C3.topics[t], name: C3.topic_names[t],
    type: mode === 'bar' ? 'bar' : 'scatter',
    mode: mode === 'line' ? 'lines' : undefined,
    stackgroup: (mode === 'area' || mode === 'bar') ? 'one' : undefined,
    fill: mode === 'area' ? 'tonexty' : undefined,
    line: {{color: PAL[t % PAL.length], width: 2}},
    marker: {{color: PAL[t % PAL.length]}},
    hovertemplate: `${{C3.topic_names[t]}}: %{{y:.1%}}<br>Year: %{{x}}<extra></extra>`,
  }}));
}}
function updateNMF() {{
  const mode = document.getElementById('nmf_mode').value;
  Plotly.react('chart3', buildNMFTraces(mode), {{
    ...LAYOUT_BASE, height: 380,
    barmode: 'stack',
    xaxis: {{title: 'Publication Year (of book)'}},
    yaxis: {{title: 'Proportion of chapters', tickformat: '.0%'}},
  }});
}}
updateNMF();

// ── Chart 4: Cluster composition by decade ────────────────────────────────────
function buildClusterTraces(mode) {{
  const decades = C4.decades;
  return Array.from({{length: C4.best_k}}, (_, c) => {{
    const raw = C4.clusters[String(c)];
    const tots = decades.map((_,di) => C4.clusters[Object.keys(C4.clusters)[0]].map((_,i)=>i).reduce((s,ci)=>s+(C4.clusters[String(ci)]||[])[di]||0, 0));
    const y = mode === 'pct'
      ? raw.map((v,i) => tots[i] > 0 ? v/tots[i] : 0)
      : raw;
    return {{
      x: decades, y, name: `Cluster ${{c+1}}`,
      type: 'bar',
      marker: {{color: PAL[c % PAL.length]}},
      hovertemplate: mode === 'pct'
        ? `Cluster ${{c+1}}: %{{y:.1%}}<br>%{{x}}<extra></extra>`
        : `Cluster ${{c+1}}: %{{y}} books<br>%{{x}}<extra></extra>`,
    }};
  }});
}}
function updateClusters() {{
  const mode = document.getElementById('cluster_mode').value;
  Plotly.react('chart4', buildClusterTraces(mode), {{
    ...LAYOUT_BASE, height: 380,
    barmode: mode === 'group' ? 'group' : 'stack',
    xaxis: {{title: 'Decade'}},
    yaxis: {{title: mode === 'pct' ? 'Proportion' : 'Books',
             tickformat: mode === 'pct' ? '.0%' : ''}},
  }});
}}
updateClusters();

// ── Chart 5: Year vs semantic position ───────────────────────────────────────
function updateScatter5() {{
  const colBy = document.getElementById('scatter_colour').value;
  const yDim  = document.getElementById('scatter_y').value;
  const groupKey = colBy === 'topic' ? C5.topics : null;
  const n = colBy === 'topic' ? C5.n_topics : 1;
  const traces = [];
  if (colBy === 'topic') {{
    for (let g = 0; g < C5.n_topics; g++) {{
      const idx = C5.topics.map((v,i) => v===g ? i : -1).filter(i=>i>=0);
      traces.push({{
        x: idx.map(i => C5.years[i]),
        y: idx.map(i => yDim === 'lsa1' ? C5.x[i] : C5.y[i]),
        mode: 'markers', type: 'scatter', name: C5.lda_names?C5.lda_names[g]:`Topic ${{g+1}}`,
        marker: {{color: PAL[g%PAL.length], size:8, opacity:0.75, line:{{color:'white',width:0.5}}}},
        text: idx.map(i => `<b>${{C5.titles[i].substring(0,50)}}</b><br>${{C5.authors[i]}}<br>${{C5.years[i]}}<br>${{C5.lda_names?C5.lda_names[C5.topics[i]]:'Topic '+(C5.topics[i]+1)}}`),
        hovertemplate: '%{{text}}<extra></extra>',
      }});
    }}
  }} else {{
    traces.push({{
      x: C5.years,
      y: yDim === 'lsa1' ? C5.x : C5.y,
      mode: 'markers', type: 'scatter', name: 'Books',
      marker: {{
        color: C5.years, colorscale: 'Viridis', showscale: true,
        colorbar: {{title: 'Year', thickness: 14}},
        size: 8, opacity: 0.8, line: {{color:'white',width:0.5}},
      }},
      text: C5.titles.map((t,i) => `<b>${{t.substring(0,50)}}</b><br>${{C5.authors[i]}}<br>${{C5.years[i]}}`),
      hovertemplate: '%{{text}}<extra></extra>',
    }});
  }}
  Plotly.react('chart5', traces, {{
    ...LAYOUT_BASE, height: 480,
    xaxis: {{title: 'Publication Year'}},
    yaxis: {{title: yDim === 'lsa1' ? 'LSA Dimension 1' : 'LSA Dimension 2', zeroline:false}},
  }});
}}
updateScatter5();

// ── Chart 6: Cumulative publications by topic ─────────────────────────────────
const cumTraces = Array.from({{length: C6.n_topics}}, (_, t) => ({{
  x: C6.years, y: C6.topics[t], name: C6.lda_names?C6.lda_names[t]:`Topic ${{t+1}}`,
  type: 'scatter', mode: 'lines',
  stackgroup: 'one', fill: 'tonexty',
  line: {{color: PAL[t % PAL.length], width: 1.5}},
  hovertemplate: `${{C6.lda_names?C6.lda_names[t]:'Topic '+(t+1)}}: %{{y}} books total<br>Year: %{{x}}<extra></extra>`,
}}));
Plotly.newPlot('chart6', cumTraces, {{
  ...LAYOUT_BASE, height: 380,
  xaxis: {{title: 'Publication Year'}},
  yaxis: {{title: 'Cumulative books'}},
}});

// ── Chart 7: Band prevalence + Concept Velocity ───────────────────────────────────────────────
if (C7 && C7.band_means) {{
  const dec7  = C7.decades || [];
  const btraces = Object.entries(C7.band_means).map(([band, vals]) => ({{
    x: dec7, y: vals, type: 'scatter', mode: 'lines+markers', name: band,
    line:   {{ color: C7.band_cols[band], width: 2.5 }},
    marker: {{ size: 7 }},
    hovertemplate: band + ': %{{y:.1f}} terms/book<br>%{{x}}<extra></extra>',
  }}));
  Plotly.newPlot('c7_band', btraces, {{
    ...LAYOUT_BASE, height: 300,
    title: {{ text: 'Mean index terms per book by decade', font: {{ size: 12 }} }},
    xaxis: {{ title: 'Decade' }},
    yaxis: {{ title: 'Mean terms / book' }},
    legend: {{ orientation: 'h', y: -0.38, font: {{ size: 10 }} }},
  }});

  const vsel = document.getElementById('c7_sel');
  if (vsel && C7.vel_terms) {{
    C7.vel_terms.forEach(vt => {{
      const o = document.createElement('option');
      o.value = vt.key;
      o.textContent = vt.term + ' (' + vt.total + ' books)';
      vsel.appendChild(o);
    }});
    drawVel();
  }}
}}

function drawVel() {{
  if (!C7 || !C7.vel_terms) return;
  const key = document.getElementById('c7_sel')?.value;
  const vt  = C7.vel_terms.find(v => v.key === key);
  if (!vt) return;
  const decs = Object.keys(vt.decades).map(Number).sort();
  const lnames = C7.lda_names || [];
  const traces = lnames.map((nm, t) => ({{
    x: decs.map(d => d + 's'),
    y: decs.map(d => {{
      const dist  = vt.decades[String(d)]?.dist || {{}};
      const total = vt.decades[String(d)]?.count || 0;
      return total > 0 ? (+(dist[String(t)] || 0)) / total : 0;
    }}),
    type: 'bar', name: nm.substring(0, 22),
    marker: {{ color: C7.palette[t % C7.palette.length] }},
    hovertemplate: nm.substring(0,22) + ': %{{y:.0%}}<br>%{{x}}<extra></extra>',
  }}));
  Plotly.react('c7_vel', traces, {{
    barmode: 'stack', ...LAYOUT_BASE, height: 300,
    title: {{ text: '\u201c' + vt.term + '\u201d \u2014 topic drift by decade',
              font: {{ size: 12 }} }},
    xaxis: {{ title: 'Decade', tickangle: -35 }},
    yaxis: {{ title: 'Proportion', tickformat: '.0%', range: [0,1] }},
    legend: {{ orientation: 'h', y: -0.55, font: {{ size: 9 }} }},
  }});
}}
</script>
</body>
</html>
"""

out = 'data/outputs/book_nlp_timeseries.html'
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Saved: {out}  ({len(html)//1024} KB)")