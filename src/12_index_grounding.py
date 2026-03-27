"""


12_index_grounding.py — Index-term topic labelling + Concept Density + Velocity
─────────────────────────────────────────────────────────────────────────────────
Reads: index_analysis.json, index_terms.json, nlp_results.json,
       nlp_results_chapters.json, books_clean.json
Writes: topic_index_grounding.json, concept_density.json, concept_velocity.json
        data/outputs/book_nlp_index_grounding.html

Three analyses:
  1. Index-term topic labelling  — which established terms ground each LDA/NMF topic
  2. Concept Density             — (unique index terms) / word count per book
  3. Concept Velocity            — how index terms migrate between topic clusters over decades
"""

# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_lang.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


import json, re, os, numpy as np
from collections import defaultdict

os.makedirs('data/outputs', exist_ok=True)


# ── Verify working directory has required data files ────────────────────────
import os as _os
if not _os.path.exists(str(JSON_DIR / 'books_clean.json')):
    print('ERROR: books_clean.json not found in current directory.')
    print(f'Run this script from your project root, not from {_os.getcwd()}')
    print('Example: cd /path/to/project && python3 src/generate_summaries_api.py')
    import sys as _sys; _sys.exit(1)

print("Loading data...")
with open(str(JSON_DIR / 'index_analysis.json')) as f: IA = json.load(f)
with open(str(JSON_DIR / 'index_terms.json'))    as f: IT = json.load(f)
with open(str(JSON_DIR / 'nlp_results.json'))    as f: R  = json.load(f)
with open(str(JSON_DIR / 'nlp_results_chapters.json')) as f: RC = json.load(f)
with open(str(JSON_DIR / 'books_clean.json'))    as f: BC = json.load(f)

book_ids   = R['book_ids']
dom_topics = R['dominant_topics']
n_topics   = R['n_topics']
# pub_years: fall back to books_clean.json if missing from nlp_results.json
if 'pub_years' in R:
    pub_years = dict(zip(R['book_ids'], R['pub_years']))
else:
    import re as _re
    pub_years = {}
    for _bid in R['book_ids']:
        _raw = BC.get(_bid, {}).get('pub_year') or BC.get(_bid, {}).get('pubdate', '')
        _m = _re.search(r'\b(19|20)\d{2}\b', str(_raw)) if _raw else None
        pub_years[_bid] = int(_m.group()) if _m else None
titles     = dict(zip(R['book_ids'], R['titles']))
vocab      = IA['vocab']
book_terms = IA['book_terms']

_LDA_BASE = [
    'Human & Social Experience', 'Mathematical & Formal Systems',
    'General Systems Theory', 'History & Philosophy of Cybernetics',
    '2nd-Order Cybernetics & Bateson', 'Control Theory & Engineering',
    'Popular & Applied Cybernetics',
]
# Pad with generic labels if the pipeline found more topics than the base list
LDA_NAMES = (R.get('topic_names') or (_LDA_BASE + [f'Topic {i+1}' for i in range(len(_LDA_BASE), n_topics)]))[:n_topics]

_NMF_BASE = [
    'Human & Social Experience', 'Mathematical & Formal Systems',
    'General Systems Theory', 'Management & Organisational Cybernetics',
    'Control Theory & Engineering', 'Popular & Applied Cybernetics',
]
_nmf_k = RC.get('n_topics', len(_NMF_BASE))
NMF_NAMES = (_NMF_BASE + [f'Topic {i+1}' for i in range(len(_NMF_BASE), _nmf_k)])[:_nmf_k]

DECADES = list(range(1950, 2030, 10))

# ── 1. INDEX-TERM TOPIC LABELLING ────────────────────────────────────────────
print("\n[1] Computing index-term topic lift scores...")

global_lda_frac = defaultdict(float)
for t in dom_topics:
    global_lda_frac[t] += 1/len(book_ids)

OCR_NOISE = re.compile(
    r'\d{3,}|[^\w\s\-\',\.\(\)\/]+|\?|this author|your reading|list of|date due',
    re.IGNORECASE)
SKIP_TERMS = {
    'index', 'subject index', 'name index', 'systems', 'science', 'technology',
    'model', 'time', 'theory', 'system', 'environment', 'automation',
}

def is_clean(tl, v):
    if v['n_books'] < 5: return False
    if tl in SKIP_TERMS: return False
    t = v['term']
    if not t: return False
    if not t[0].isalpha(): return False       # starts with digit/symbol
    if t.isupper() and ' ' not in t and len(t) > 5: return False  # ALL-CAPS noise
    if len(t) < 3 or len(t) > 80: return False
    if OCR_NOISE.search(t): return False
    return True

useful_vocab = {tl: v for tl, v in vocab.items() if is_clean(tl, v)}
print(f"  Clean vocab terms (≥5 books): {len(useful_vocab)}")

# LDA lift
lda_lift = defaultdict(list)
for tl, v in useful_vocab.items():
    td = v['topic_dist']
    total = sum(td.values())
    if total < 5: continue
    for t_str, count in td.items():
        t = int(t_str)
        lift = (count/total) / max(global_lda_frac[t], 0.001)
        if lift > 1.5 and count >= 5:
            lda_lift[t].append({'lift': round(lift,3), 'term': v['term'],
                                 'count': count, 'total': total})

# NMF lift (via book → dominant NMF topic)
book_to_nmf = dict(zip(RC['book_ids'], RC['dominant_topics']))
global_nmf_dist = defaultdict(int)
for t in RC['dominant_topics']:
    global_nmf_dist[t] += 1
global_nmf_frac = {t: c/len(RC['dominant_topics']) for t,c in global_nmf_dist.items()}

nmf_lift = defaultdict(list)
for tl, v in useful_vocab.items():
    td_nmf = defaultdict(int)
    total_nmf = 0
    for bid, bterms in book_terms.items():
        if tl not in [t.lower() for t in bterms]: continue
        nmf_t = book_to_nmf.get(bid)
        if nmf_t is None: continue
        td_nmf[nmf_t] += 1
        total_nmf += 1
    if total_nmf < 5: continue
    for t, count in td_nmf.items():
        lift = (count/total_nmf) / max(global_nmf_frac.get(t, 0.001), 0.001)
        if lift > 1.5 and count >= 4:
            nmf_lift[t].append({'lift': round(lift,3), 'term': v['term'],
                                 'count': count, 'total': total_nmf})

# Sort and clip
lda_top = {t: sorted(lda_lift[t], key=lambda x: x['lift'], reverse=True)[:20]
           for t in range(n_topics)}
nmf_top = {t: sorted(nmf_lift[t], key=lambda x: x['lift'], reverse=True)[:20]
           for t in range(RC['n_topics'])}

grounding = {
    'lda_top_terms': {str(t): v for t,v in lda_top.items()},
    'nmf_top_terms': {str(t): v for t,v in nmf_top.items()},
    'lda_names': LDA_NAMES,
    'nmf_names': NMF_NAMES,
}
with open(str(JSON_DIR / 'topic_index_grounding.json'), 'w') as f:
    json.dump(grounding, f, ensure_ascii=False)

for t in range(n_topics):
    terms_str = ', '.join(x['term'] for x in lda_top[t][:5])
    print(f"  LDA T{t+1} {LDA_NAMES[t][:30]:30s}: {terms_str}")

# ── 2. CONCEPT DENSITY ────────────────────────────────────────────────────────
print("\n[2] Computing Concept Density...")

concept_density = {}
for bid in book_ids:
    terms  = IT.get(bid, {}).get('terms', [])
    status = IT.get(bid, {}).get('status', 'no_index')
    text   = BC.get(bid, {}).get('clean_text', '')
    wc     = len(text.split())
    unique = len(set(t.lower() for t in terms))
    density = round(unique / max(wc, 1) * 1000, 4)  # per 1000 words
    concept_density[bid] = {
        'unique_terms': unique,
        'word_count':   wc,
        'density':      density,
        'status':       status,
    }

dens = [v['density'] for v in concept_density.values() if v['status'] != 'no_index']
print(f"  Books with index: {len(dens)}")
print(f"  Density (per 1000w): mean={np.mean(dens):.2f}  "
      f"median={np.median(dens):.2f}  max={max(dens):.2f}")

with open(str(JSON_DIR / 'concept_density.json'), 'w') as f:
    json.dump(concept_density, f)

# ── 3. CONCEPT VELOCITY ───────────────────────────────────────────────────────
print("\n[3] Computing Concept Velocity...")

top_terms_vel = [(tl, v) for tl, v in useful_vocab.items()
                 if v['n_books'] >= 10][:60]

dom_topics_map = dict(zip(book_ids, dom_topics))
velocity_data  = {}

for tl, v in top_terms_vel:
    decade_topic = defaultdict(lambda: defaultdict(int))
    decade_total = defaultdict(int)
    for bid, bterms in book_terms.items():
        if tl not in [t.lower() for t in bterms]: continue
        year = pub_years.get(bid)
        if not year: continue
        decade = (year // 10) * 10
        topic  = dom_topics_map.get(bid)
        if topic is None: continue
        decade_topic[decade][topic] += 1
        decade_total[decade] += 1

    dominant = {}
    for d in DECADES:
        if decade_total[d] >= 2:
            dom = max(decade_topic[d], key=decade_topic[d].get)
            dominant[str(d)] = {
                'topic':      dom,
                'topic_name': LDA_NAMES[dom],
                'count':      decade_total[d],
                'dist':       {str(t): c for t,c in decade_topic[d].items()},
            }

    velocity_data[tl] = {
        'term':        v['term'],
        'total_books': v['n_books'],
        'decades':     dominant,
    }

migrations = []
for tl, vd in velocity_data.items():
    dec_info = [(int(d), vd['decades'][d]) for d in sorted(vd['decades'])
                if vd['decades'][d]['count'] >= 2]
    topics = [i['topic'] for _,i in dec_info]
    if len(set(topics)) > 1:
        migrations.append((tl, vd['term'], len(set(topics)), dec_info))

migrations.sort(key=lambda x: x[2], reverse=True)
print(f"  Terms with topic migration: {len(migrations)}/{len(top_terms_vel)}")
for tl, term, n_topics_seen, _ in migrations[:5]:
    print(f"  {term}: {n_topics_seen} distinct topics")

with open(str(JSON_DIR / 'concept_velocity.json'), 'w') as f:
    json.dump(velocity_data, f, ensure_ascii=False)

print("\nSaved: topic_index_grounding.json, concept_density.json, concept_velocity.json")

# ── BUILD HTML REPORT ─────────────────────────────────────────────────────────
print("\nBuilding HTML report...")

PAL = ['#2563eb','#16a34a','#dc2626','#d97706','#7c3aed',
       '#0891b2','#be185d','#0f766e','#c2410c','#065f46']

# Prepare scatter data: coords + density bubble size
# coords_2d: compute on-the-fly if missing from older nlp_results.json
if 'coords_2d' in R:
    coords_2d = R['coords_2d']
else:
    from sklearn.feature_extraction.text import TfidfVectorizer as _TV
    from sklearn.decomposition import TruncatedSVD as _SVD
    from sklearn.preprocessing import normalize as _norm
    def _sample(t): n=len(t); return ' '.join(t[max(int(n*p),4000):max(int(n*p),4000)+20000] for p in (.10,.50,.85))
    _texts = [_sample(BC[b]['clean_text']) for b in book_ids]
    _X = _TV(max_features=3000,min_df=2,max_df=0.95,ngram_range=(1,2),
             sublinear_tf=True,token_pattern=r'(?u)\b[a-zA-Z]{4,}\b').fit_transform(_texts)
    coords_2d = _norm(_SVD(n_components=2,random_state=99).fit_transform(_X)).tolist()
    print('  [coords_2d] computed on-the-fly (re-run 03_nlp_pipeline.py to persist)')
pub_years_list = R.get('pub_years', [pub_years.get(bid) for bid in book_ids])
cluster_labels = R['cluster_labels']

# Normalise density to bubble size (6–30px range)
densities_list = [concept_density.get(bid,{}).get('density', 0) for bid in book_ids]
d_arr = np.array(densities_list)
d_max = d_arr.max() if d_arr.max() > 0 else 1
bubble_sizes = (np.sqrt(d_arr / d_max) * 24 + 6).tolist()

# Velocity chart data — top 15 migrating terms
vel_chart_terms = [tl for tl,_,_,_ in migrations[:15]]
vel_chart_data  = {tl: velocity_data[tl] for tl in vel_chart_terms}

j_grounding = json.dumps(grounding)
j_density   = json.dumps({bid: concept_density[bid]['density'] for bid in book_ids})
j_bubble    = json.dumps(bubble_sizes)
j_scatter   = json.dumps({
    'x':       [c[0] for c in coords_2d],
    'y':       [c[1] for c in coords_2d],
    'titles':  R['titles'],
    'authors': R['authors'],
    'topics':  dom_topics,
    'clusters': cluster_labels,
    'pub_years': pub_years_list,
    'lda_names': LDA_NAMES,
    'density': densities_list,
    'bubble':  bubble_sizes,
})
j_velocity  = json.dumps({
    'terms': vel_chart_data,
    'decades': [str(d) for d in DECADES],
    'lda_names': LDA_NAMES,
    'palette': PAL,
})
j_pal = json.dumps(PAL)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Index Grounding — Topic Labels, Concept Density & Velocity</title>
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
.desc{{font-size:.9rem;color:#475569;margin-bottom:1rem}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:1.2rem;box-shadow:0 1px 3px rgba(0,0,0,.06);margin-bottom:1.5rem}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem}}
.topic-card{{background:#fff;border:1px solid var(--border);border-radius:8px;padding:1rem;margin-bottom:.8rem}}
.topic-head{{display:flex;align-items:center;gap:.6rem;margin-bottom:.5rem}}
.badge{{color:#fff;padding:.2rem .7rem;border-radius:4px;font-size:.8rem;font-weight:700}}
.term-row{{display:flex;align-items:center;padding:.2rem 0;font-size:.84rem;border-bottom:1px solid #f1f5f9}}
.term-row:last-child{{border-bottom:none}}
.lift-bar{{background:#bfdbfe;height:6px;border-radius:3px;margin-left:.5rem}}
.lift-val{{color:#2563eb;font-weight:600;font-size:.78rem;margin-left:auto;white-space:nowrap}}
.ctrls{{display:flex;gap:.6rem;flex-wrap:wrap;margin-bottom:.8rem;align-items:center}}
.ctrls label{{font-size:.82rem;color:#475569;font-weight:500}}
.ctrls select{{padding:.3rem .6rem;border:1px solid var(--border);border-radius:5px;font-size:.82rem;background:#fff}}
.stat-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:1.5rem}}
.stat-card{{background:#fff;border:1px solid var(--border);border-radius:8px;padding:1rem;text-align:center}}
.stat-card .val{{font-size:1.5rem;font-weight:700;color:var(--blue)}}
.stat-card .lbl{{font-size:.78rem;color:#64748b;text-transform:uppercase}}
@media(max-width:800px){{.grid2,.stat-grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="header">
  <h1>📖 Index Grounding Analysis</h1>
  <p>Topic labelling from expert index terms · Concept Density · Concept Velocity across decades</p>
</div>
<nav>
  <a href="#labelling">🏷 Topic Labels</a>
  <a href="#density">⚖ Concept Density</a>
  <a href="#scatter">🗺 Density Scatter</a>
  <a href="#velocity">⚡ Concept Velocity</a>
</nav>
<div class="container">

<div class="stat-grid">
  <div class="stat-card"><div class="val">{len(useful_vocab)}</div><div class="lbl">Clean index terms</div></div>
  <div class="stat-card"><div class="val">{len([b for b in book_ids if concept_density[b]['status']!='no_index'])}</div><div class="lbl">Books with index</div></div>
  <div class="stat-card"><div class="val">{len(migrations)}</div><div class="lbl">Migrating terms</div></div>
  <div class="stat-card"><div class="val">{len(top_terms_vel)}</div><div class="lbl">Terms tracked over time</div></div>
</div>

<!-- 1. Topic Labelling -->
<section id="labelling">
  <h2>1 · Index-Term Topic Labelling</h2>
  <p class="desc">For each LDA/NMF topic, the index terms most over-represented relative to their
  corpus-wide frequency (lift score). A lift of 3× means the term appears in that topic's books
  3× more often than chance. These are the established, human-curated concepts that define each topic.</p>

  <div class="ctrls">
    <label>Topic model:</label>
    <select id="label_model" onchange="drawLabels()">
      <option value="lda">LDA (book-level, 7 topics)</option>
      <option value="nmf">NMF (chapter-level, 6 topics)</option>
    </select>
  </div>
  <div id="label_cards"></div>
</section>

<!-- 2. Concept Density -->
<section id="density">
  <h2>2 · Concept Density Rankings</h2>
  <p class="desc">Unique index terms per 1,000 words — a proxy for how "concept-dense"
  each book is. High density = encyclopaedic or highly technical. Low density = narrative,
  philosophical, or popular science.</p>
  <div class="card" id="density_chart"></div>
</section>

<!-- 3. Density Scatter -->
<section id="scatter">
  <h2>3 · Semantic Map — Bubble Size = Concept Density</h2>
  <p class="desc">LSA 2D projection. Bubble size proportional to concept density (index terms per 1,000 words).
  Larger bubbles are more terminologically dense. Colour by LDA topic or cluster.</p>
  <div class="ctrls">
    <label>Colour by:</label>
    <select id="scatter_col" onchange="drawScatter()">
      <option value="topic">LDA topic</option>
      <option value="cluster">Cluster</option>
    </select>
  </div>
  <div class="card" id="scatter_div"></div>
</section>

<!-- 4. Concept Velocity -->
<section id="velocity">
  <h2>4 · Concept Velocity — Term Migration Across Decades</h2>
  <p class="desc">How the dominant LDA topic of books containing each index term shifts over
  publication decades. Select a term to see its trajectory. Terms that cross multiple topic
  boundaries reveal intellectual migration patterns in the corpus.</p>
  <div class="ctrls">
    <label>Term:</label>
    <select id="vel_term" onchange="drawVelocity()"></select>
  </div>
  <div class="card" id="velocity_chart"></div>
  <div class="card" id="velocity_sankey" style="margin-top:.8rem"></div>
</section>

</div>
<footer style="text-align:center;padding:1.5rem;color:#94a3b8;font-size:.8rem;border-top:1px solid var(--border);margin-top:2rem">
  Index Grounding Analysis · {len(book_ids)} books · Plotly.js
</footer>

<script>
const GR = {j_grounding};
const SC = {j_scatter};
const VL = {j_velocity};
const PAL = {j_pal};
const LAYOUT = {{paper_bgcolor:'transparent',plot_bgcolor:'#f8fafc',
                 hoverlabel:{{bgcolor:'#1e293b',font:{{color:'white',size:12}}}}}};

// ── 1. Topic label cards ─────────────────────────────────────────────────────
function drawLabels() {{
  const model  = document.getElementById('label_model').value;
  const data   = model === 'lda' ? GR.lda_top_terms : GR.nmf_top_terms;
  const names  = model === 'lda' ? GR.lda_names     : GR.nmf_names;
  const wrap   = document.getElementById('label_cards');
  wrap.innerHTML = '';
  const maxLift = Math.max(...Object.values(data).flat().map(x=>x.lift||0));

  Object.entries(data).forEach(([t, terms]) => {{
    const col  = PAL[+t % PAL.length];
    const name = names[+t] || ('Topic ' + (+t+1));
    let rows = terms.slice(0,10).map(x => {{
      const barW = Math.round(x.lift/maxLift*180);
      return `<div class="term-row">
        <span style="min-width:160px">${{x.term}}</span>
        <div class="lift-bar" style="width:${{barW}}px"></div>
        <span class="lift-val">${{x.lift.toFixed(2)}}× (${{x.count}} books)</span>
      </div>`;
    }}).join('');
    wrap.innerHTML += `<div class="topic-card">
      <div class="topic-head">
        <span class="badge" style="background:${{col}}">T${{+t+1}}</span>
        <strong>${{name}}</strong>
      </div>
      ${{rows}}
    </div>`;
  }});
}}
drawLabels();

// ── 2. Concept Density bar chart ─────────────────────────────────────────────
(function(){{
  const pairs = SC.titles.map((t,i)=>{{
    return {{title:t.substring(0,45), density:SC.density[i],
             topic:SC.topics[i], year:SC.pub_years[i]||''}};
  }}).filter(p=>p.density>0)
    .sort((a,b)=>b.density-a.density)
    .slice(0,40);

  Plotly.react('density_chart',[{{
    x: pairs.map(p=>p.density),
    y: pairs.map(p=>p.title),
    type:'bar', orientation:'h',
    marker:{{color:pairs.map(p=>PAL[(p.topic||0)%PAL.length])}},
    hovertemplate:'<b>%{{y}}</b><br>Density: %{{x:.2f}} / 1000w<extra></extra>',
  }}],{{
    ...LAYOUT, height: Math.max(400, pairs.length*18+80),
    margin:{{t:10,b:60,l:320,r:20}},
    xaxis:{{title:'Index terms per 1,000 words'}},
    yaxis:{{autorange:'reversed',tickfont:{{size:9}}}},
  }});
}})();

// ── 3. Density scatter ────────────────────────────────────────────────────────
function drawScatter() {{
  const colBy = document.getElementById('scatter_col').value;
  const groups = colBy==='topic' ? SC.topics : SC.clusters;
  const n_g   = Math.max(...groups)+1;
  const traces = [];
  for(let g=0; g<n_g; g++) {{
    const idx = groups.map((v,i)=>v===g?i:-1).filter(i=>i>=0);
    if(!idx.length) continue;
    const nm = colBy==='topic'?(SC.lda_names[g]||'T'+(g+1)):'Cluster '+(g+1);
    traces.push({{
      x: idx.map(i=>SC.x[i]), y: idx.map(i=>SC.y[i]),
      mode:'markers', type:'scatter', name:nm,
      marker:{{
        color:PAL[g%PAL.length],
        size: idx.map(i=>SC.bubble[i]),
        opacity:.75, line:{{color:'white',width:0.5}},
      }},
      text: idx.map(i=>`<b>${{SC.titles[i].substring(0,50)}}</b><br>${{SC.authors[i]}}<br>`+
                        `Density: ${{SC.density[i].toFixed(2)}} / 1000w`),
      hovertemplate:'%{{text}}<extra></extra>',
    }});
  }}
  Plotly.react('scatter_div',traces,{{
    ...LAYOUT, height:540,
    margin:{{t:10,b:60,l:60,r:20}},
    xaxis:{{title:'LSA Dim 1',zeroline:false}},
    yaxis:{{title:'LSA Dim 2',zeroline:false}},
    legend:{{orientation:'h',y:-0.2,font:{{size:9}}}},
  }});
}}
drawScatter();

// ── 4. Concept Velocity ───────────────────────────────────────────────────────
const termKeys = Object.keys(VL.terms);
const sel = document.getElementById('vel_term');
termKeys.forEach(tl => {{
  const o=document.createElement('option');
  o.value=tl; o.textContent=VL.terms[tl].term+' ('+VL.terms[tl].total_books+' books)';
  sel.appendChild(o);
}});

function drawVelocity() {{
  const tl  = document.getElementById('vel_term').value;
  const vd  = VL.terms[tl];
  if (!vd) return;

  const decades = Object.keys(vd.decades).map(Number).sort();
  const x  = decades.map(d=>d+'s');

  // Stacked bar: topic distribution per decade
  const traces = VL.lda_names.map((name,t) => {{
    const y = decades.map(d=>{{
      const dist = vd.decades[String(d)]?.dist || {{}};
      const total = vd.decades[String(d)]?.count || 0;
      return total > 0 ? (dist[String(t)]||0)/total : 0;
    }});
    return {{
      x, y, type:'bar', name:name,
      marker:{{color:VL.palette[t%VL.palette.length]}},
      hovertemplate:`${{name}}: %{{y:.0%}}<br>Decade: %{{x}}<extra></extra>`,
    }};
  }});

  const bookCounts = decades.map(d=>vd.decades[String(d)]?.count||0);
  traces.push({{
    x, y:bookCounts, type:'scatter', mode:'lines+markers',
    name:'Books', yaxis:'y2',
    line:{{color:'#64748b',dash:'dot',width:1.5}},
    marker:{{size:6,color:'#64748b'}},
    hovertemplate:'Books: %{{y}}<br>%{{x}}<extra></extra>',
  }});

  Plotly.react('velocity_chart', traces, {{
    ...LAYOUT, barmode:'stack', height:360,
    title:{{text:`"${{vd.term}}" — topic distribution by decade (${{vd.total_books}} books total)`,
            font:{{size:13}}}},
    margin:{{t:50,b:60,l:60,r:60}},
    xaxis:{{title:'Publication decade'}},
    yaxis:{{title:'Proportion of books that decade',tickformat:'.0%',range:[0,1]}},
    yaxis2:{{title:'Book count',overlaying:'y',side:'right',showgrid:false}},
    legend:{{orientation:'h',y:-0.25,font:{{size:9}}}},
  }});
}}
if(termKeys.length>0) drawVelocity();
</script>
</body></html>"""

out_path = 'data/outputs/book_nlp_index_grounding.html'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Saved: {out_path}  ({len(html)//1024} KB)")