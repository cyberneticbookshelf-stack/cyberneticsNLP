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

import json, re, math
from collections import defaultdict


# ── Verify working directory has required data files ────────────────────────
import os as _os

# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_metadata_full.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


if not _os.path.exists(str(JSON_DIR / 'books_clean.json')):
    print('ERROR: books_clean.json not found in current directory.')
    print(f'Run this script from your project root, not from {_os.getcwd()}')
    print('Example: cd /path/to/project && python3 src/generate_summaries_api.py')
    import sys as _sys; _sys.exit(1)

with open(str(JSON_DIR / 'index_analysis.json')) as f: D = json.load(f)
with open(str(JSON_DIR / 'nlp_results.json')) as f: R = json.load(f)
with open(str(JSON_DIR / 'index_snippets.json')) as f: snippets = json.load(f)

top200     = D['top200']
cooc       = D['cooc_top50']
book_terms = D['book_terms']
pub_years  = D['pub_years']
dom_topics = D['dom_topics']
titles     = D['titles']
n_topics   = R['n_topics']  # 7

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
TOPIC_NAMES = (_carried + [f'Topic {i+1}' for i in range(len(_carried), n_topics)])[:n_topics]

PAL = ['#2563eb','#16a34a','#dc2626','#d97706','#7c3aed',
       '#0891b2','#be185d','#0f766e']

decades = list(range(1950, 2030, 10))

# Books per decade for normalisation
bpd = defaultdict(int)
for bid, y in pub_years.items():
    if y: bpd[(y//10)*10] += 1

# Fix 2: clean index terms — strip "see also" fragments, page-number prefixes
SEE_NOISE   = re.compile(r'(?i)\s+see\s+(?:also\s+)?.*$|\s*;\s*see\s+.*$')
LEAD_DIGITS = re.compile(r'^\d[\d,\s–\-]+')
SKIP_TERMS  = {'index','subject index','name index','author index','general index'}

def clean_term(t):
    t = SEE_NOISE.sub('', t).strip()          # strip trailing "see also..."
    t = LEAD_DIGITS.sub('', t).strip()        # strip leading page numbers
    t = re.sub(r',\s*$', '', t).strip()       # trailing comma
    return t if len(t) >= 3 and t[0].isalpha() else ''

# ── Split top200 into concepts and persons ────────────────────────────────────
top200_concepts = [v for v in top200 if not v.get('is_person')]
top200_persons  = [v for v in top200 if     v.get('is_person')]

# Build charts data — each chart carries both splits; JS toggles between them
def _freq(items, n=80):
    return {'terms': [v['term'] for v in items[:n]],
            'counts': [v['count'] for v in items[:n]]}

freq_data = {'concepts': _freq(top200_concepts), 'persons': _freq(top200_persons)}

def _ts(items, n=30):
    top = items[:n]
    abs_  = {v['term']: [v['year_dist'].get(str(d), v['year_dist'].get(d, 0)) for d in decades] for v in top}
    norm_ = {v['term']: [round(v['year_dist'].get(str(d), v['year_dist'].get(d, 0)) / max(bpd.get(d, 1), 1), 4)
                         for d in decades] for v in top}
    return {'decades': [f'{d}s' for d in decades], 'terms': [v['term'] for v in top],
            'abs': abs_, 'norm': norm_}

ts_data = {'concepts': _ts(top200_concepts), 'persons': _ts(top200_persons)}

# Co-occurrence network — concepts only (concept-to-concept links are more meaningful)
nodes_set = {}
for p in cooc[:50]:
    for t in [p['a'], p['b']]:
        if t not in nodes_set:
            for v in top200_concepts:
                if v['term'] == t: nodes_set[t] = v['count']; break
nodes = [{'name': k, 'count': v} for k, v in nodes_set.items()]
N = len(nodes)
for i, nd in enumerate(nodes):
    a = 2 * math.pi * i / N
    nd['x'] = round(math.cos(a), 4); nd['y'] = round(math.sin(a), 4)
ni = {nd['name']: i for i, nd in enumerate(nodes)}
edges = [{'s': ni[p['a']], 't': ni[p['b']], 'v': p['count']}
         for p in cooc[:50] if p['a'] in ni and p['b'] in ni]
cooc_data = {'nodes': nodes, 'edges': edges}

def _topic(items, n=50):
    top = items[:n]
    return {
        'terms':  [v['term'] for v in top],
        'names':  TOPIC_NAMES,
        'matrix': [[v['topic_dist'].get(str(t), v['topic_dist'].get(t, 0))
                    for t in range(n_topics)] for v in top],
    }

topic_data = {'concepts': _topic(top200_concepts), 'persons': _topic(top200_persons)}

# Explorer data with cleaned terms and snippets
top200_lower = {v['term'].lower() for v in top200}
explorer = {
    'book_terms': {
        bid: [clean_term(t) for t in terms
              if clean_term(t) and t.lower() not in SKIP_TERMS
              and not re.match(r'(?i)^see\s', t)][:150]
        for bid, terms in book_terms.items()
    },
    'titles':      titles,
    'pub_years':   pub_years,
    'dom_topics':  dom_topics,
    'topic_names': TOPIC_NAMES,
    'palette':     PAL,
    'snippets':    snippets,   # term_lower -> {bid: sentence}
}

# Serialise
jf  = json.dumps(freq_data)
jts = json.dumps(ts_data)
jcc = json.dumps(cooc_data)
jtm = json.dumps(topic_data)
jex = json.dumps(explorer)
jp  = json.dumps(PAL)
print(f"Concepts in top200: {len(top200_concepts)}  Persons: {len(top200_persons)}")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Index Term Analysis — Controlled Vocabulary</title>
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
nav a{{text-decoration:none;color:#475569;font-size:.85rem;padding:.3rem .7rem;border-radius:4px}}
nav a:hover{{background:#eff6ff;color:var(--blue)}}
.container{{max-width:1400px;margin:0 auto;padding:1.5rem}}
section{{margin-bottom:3rem;scroll-margin-top:60px}}
h2{{font-size:1.35rem;font-weight:700;margin-bottom:.5rem;padding-bottom:.5rem;border-bottom:2px solid var(--blue)}}
.desc{{font-size:.9rem;color:#475569;margin-bottom:1rem}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:1.2rem;box-shadow:0 1px 3px rgba(0,0,0,.06);margin-bottom:1.5rem}}
.ctrls{{display:flex;gap:.6rem;flex-wrap:wrap;margin-bottom:.8rem;align-items:center}}
.ctrls label{{font-size:.82rem;color:#475569;font-weight:500}}
.ctrls select,.search-box{{padding:.3rem .6rem;border:1px solid var(--border);border-radius:5px;font-size:.82rem;background:#fff;color:#1e293b}}
.search-box{{width:300px;padding:.5rem .8rem;font-size:.9rem}}
.term-btns{{display:flex;flex-wrap:wrap;gap:.35rem;margin-bottom:.8rem}}
.tbtn{{padding:.25rem .65rem;border-radius:4px;font-size:.76rem;cursor:pointer;border:1px solid var(--border);background:#f8fafc;color:#475569;transition:all .15s}}
.tbtn.on{{background:var(--blue);color:#fff;border-color:var(--blue)}}
.results{{max-height:560px;overflow-y:auto;margin-top:.6rem}}
.bk{{background:#f8fafc;border:1px solid var(--border);border-radius:6px;padding:.75rem 1rem;margin-bottom:.5rem}}
.bk h4{{font-size:.88rem;font-weight:600;margin-bottom:.25rem}}
.bk .meta{{font-size:.78rem;color:#64748b;margin-bottom:.4rem}}
.tags{{display:flex;flex-wrap:wrap;gap:.3rem;margin-bottom:.4rem}}
.tag{{background:#eff6ff;color:#2563eb;border:1px solid #bfdbfe;border-radius:3px;padding:.1rem .4rem;font-size:.73rem}}
.tag.hi{{background:#dcfce7;color:#16a34a;border-color:#86efac}}
.snippet{{font-size:.82rem;color:#374151;font-style:italic;background:#fff;border-left:3px solid #bfdbfe;padding:.35rem .7rem;border-radius:0 4px 4px 0;margin-top:.3rem;line-height:1.6}}
.badge{{display:inline-block;color:#fff;padding:.12rem .55rem;border-radius:9999px;font-size:.73rem;font-weight:600}}
#exp-count{{font-size:.82rem;color:#64748b;margin:.35rem 0}}
</style>
</head>
<body>
<div class="header">
  <h1>📖 Controlled Vocabulary — Index Term Analysis</h1>
  <p>Back-of-book index extraction · Term frequency · Time series · Co-occurrence · Topic enrichment · Explorer with text context</p>
</div>
<div class="stats-bar">
  <div class="stat"><span>9,807</span><small>Unique terms (≥2 books)</small></div>
  <div class="stat"><span>270</span><small>Books with clean index</small></div>
  <div class="stat"><span>126</span><small>Max books (Wiener)</small></div>
  <div class="stat"><span>200</span><small>Top terms analysed</small></div>
  <div class="stat"><span>1950–2025</span><small>Year span</small></div>
</div>
<nav>
  <a href="#freq">📊 Frequency</a>
  <a href="#ts">📅 Time Series</a>
  <a href="#cooc">🔗 Co-occurrence</a>
  <a href="#topic">🏷 By Topic</a>
  <a href="#explorer">🔍 Explorer</a>
</nav>
<div class="container">

<section id="freq">
  <h2>1 · Term Frequency Ranking</h2>
  <p class="desc">Number of corpus books each index term appears in.</p>
  <div class="ctrls">
    <label>Show:</label>
    <button class="tbtn on" id="freq_c" onclick="setFreqSplit('concepts')">📚 Concepts</button>
    <button class="tbtn"    id="freq_p" onclick="setFreqSplit('persons')">👤 Persons</button>
    <label style="margin-left:.8rem">Top</label>
    <select id="fn" onchange="drawFreq()">
      <option value="30">30</option><option value="50" selected>50</option><option value="80">80</option>
    </select><label>terms</label>
  </div>
  <div class="card" id="freq_div"></div>
</section>

<section id="ts">
  <h2>2 · Term Density Over Time</h2>
  <p class="desc">Occurrences per decade, normalised by books published that decade. Select up to 8 terms.</p>
  <div class="ctrls">
    <label>Show:</label>
    <button class="tbtn on" id="ts_c" onclick="setTSSplit('concepts')">📚 Concepts</button>
    <button class="tbtn"    id="ts_p" onclick="setTSSplit('persons')">👤 Persons</button>
    <label style="margin-left:.8rem">Mode:</label>
    <select id="ts_mode" onchange="drawTS()">
      <option value="norm">Normalised (per book that decade)</option>
      <option value="abs">Absolute count</option>
    </select>
  </div>
  <div class="term-btns" id="ts_btns"></div>
  <div class="card" id="ts_div"></div>
</section>

<section id="cooc">
  <h2>3 · Co-occurrence Network</h2>
  <p class="desc">Concept terms that frequently appear together in the same books. Node size = corpus frequency. Hover edges for shared book count.</p>
  <div class="ctrls">
    <label>Show top</label>
    <select id="cn" onchange="drawCooc()">
      <option value="20">20</option><option value="35" selected>35</option><option value="50">50</option>
    </select><label>pairs</label>
  </div>
  <div class="card" id="cooc_div"></div>
</section>

<section id="topic">
  <h2>4 · Term × Topic Distribution</h2>
  <p class="desc">Proportion of books containing each term that belong to each LDA topic. Cross-cutting terms show an even spread; topic-specific terms are dominated by one colour.</p>
  <div class="ctrls">
    <label>Show:</label>
    <button class="tbtn on" id="tm_c" onclick="setTMSplit('concepts')">📚 Concepts</button>
    <button class="tbtn"    id="tm_p" onclick="setTMSplit('persons')">👤 Persons</button>
    <label style="margin-left:.8rem">Sort by:</label>
    <select id="tsort" onchange="drawTopic()">
      <option value="freq">Frequency</option><option value="dom">Dominant topic</option>
    </select>
    <label style="margin-left:.6rem">Show top</label>
    <select id="tn" onchange="drawTopic()">
      <option value="30">30</option><option value="50" selected>50</option>
    </select>
  </div>
  <div class="card" id="topic_div"></div>
</section>

<section id="explorer">
  <h2>5 · Term Explorer</h2>
  <p class="desc">Search any index term. Each result shows matching index entries and a sentence from the book where the term appears in context.</p>
  <div class="ctrls">
    <input class="search-box" id="eq" type="text"
           placeholder="e.g. autopoiesis, feedback, Wiener…" oninput="drawExp()">
    <label style="margin-left:.6rem">Topic:</label>
    <select id="et" onchange="drawExp()"><option value="-1">All topics</option></select>
  </div>
  <div id="exp-count"></div>
  <div class="results" id="exp_div"><p style="color:#94a3b8;font-size:.9rem">Type a term to search.</p></div>
</section>

</div>
<footer style="text-align:center;padding:1.5rem;color:#94a3b8;font-size:.8rem;border-top:1px solid var(--border);margin-top:2rem">
  Controlled Vocabulary Analysis · 695 books · Plotly.js
</footer>

<script>
const FD={jf};
const TS={jts};
const CC={jcc};
const TM={jtm};
const EX={jex};
const PAL={jp};
const L={{paper_bgcolor:'transparent',plot_bgcolor:'#f8fafc',
          hoverlabel:{{bgcolor:'#1e293b',font:{{color:'white',size:12}}}}}};

// ── Split toggle helpers ──────────────────────────────────────────────────────
let freqSplit='concepts', tsSplit='concepts', tmSplit='concepts';

function setFreqSplit(s){{
  freqSplit=s;
  document.getElementById('freq_c').classList.toggle('on',s==='concepts');
  document.getElementById('freq_p').classList.toggle('on',s==='persons');
  drawFreq();
}}
function setTSSplit(s){{
  tsSplit=s;
  ts_sel = s==='concepts'
    ? ['Cybernetics','Feedback','Information','Control','Homeostasis','Entropy']
    : ['Wiener, Norbert','Turing, Alan','Shannon, Claude','Von Foerster, Heinz','Beer, Stafford'];
  document.getElementById('ts_c').classList.toggle('on',s==='concepts');
  document.getElementById('ts_p').classList.toggle('on',s==='persons');
  buildTSBtns();drawTS();
}}
function setTMSplit(s){{
  tmSplit=s;
  document.getElementById('tm_c').classList.toggle('on',s==='concepts');
  document.getElementById('tm_p').classList.toggle('on',s==='persons');
  drawTopic();
}}

// 1. Frequency
function drawFreq(){{
  const src=FD[freqSplit];
  const n=+document.getElementById('fn').value;
  const t=src.terms.slice(0,n),c=src.counts.slice(0,n);
  Plotly.react('freq_div',[{{
    x:c,y:t,type:'bar',orientation:'h',
    marker:{{color:c.map((_,i)=>`hsl(${{freqSplit==='persons'?280:210}},68%,${{55-i*0.3}}%)`)}},
    hovertemplate:'<b>%{{y}}</b><br>%{{x}} books<extra></extra>',
  }}],{{...L,height:Math.max(400,n*17),
       margin:{{t:10,b:50,l:210,r:20}},
       xaxis:{{title:'Books containing term'}},
       yaxis:{{autorange:'reversed',tickfont:{{size:10}}}}}});
}}
drawFreq();

// 2. Time series
let ts_sel=['Cybernetics','Feedback','Information','Control','Homeostasis','Entropy'];
function buildTSBtns(){{
  const src=TS[tsSplit];
  const w=document.getElementById('ts_btns');w.innerHTML='';
  src.terms.forEach(t=>{{
    const b=document.createElement('button');
    b.className='tbtn'+(ts_sel.includes(t)?' on':'');
    b.textContent=t;
    b.onclick=()=>{{
      if(ts_sel.includes(t)) ts_sel=ts_sel.filter(x=>x!==t);
      else if(ts_sel.length<8) ts_sel.push(t);
      buildTSBtns();drawTS();
    }};
    w.appendChild(b);
  }});
}}
function drawTS(){{
  const src=TS[tsSplit];
  const mode=document.getElementById('ts_mode').value;
  const data=mode==='norm'?src.norm:src.abs;
  Plotly.react('ts_div',ts_sel.map((t,i)=>{{
    const y=data[t]||src.decades.map(()=>0);
    return{{x:src.decades,y,type:'scatter',mode:'lines+markers',name:t,
            line:{{color:PAL[i%PAL.length],width:2.5}},marker:{{size:7}},
            hovertemplate:`<b>${{t}}</b><br>%{{x}}: %{{y:.3f}}<extra></extra>`}};
  }}),{{...L,height:400,margin:{{t:10,b:60,l:60,r:20}},
        xaxis:{{title:'Decade'}},
        yaxis:{{title:mode==='norm'?'Proportion of that decade\\'s books':'Books containing term'}},
        legend:{{orientation:'h',y:-0.25}}}});
}}
buildTSBtns();drawTS();

// 3. Co-occurrence
function drawCooc(){{
  const n=+document.getElementById('cn').value;
  const edges=CC.edges.slice(0,n);
  const active=new Set(edges.flatMap(e=>[e.s,e.t]));
  const nodes=CC.nodes.filter((_,i)=>active.has(i));
  const N=nodes.length;
  // Recompute circle positions for active nodes
  nodes.forEach((nd,i)=>{{
    const a=2*Math.PI*i/N;
    nd.px=Math.cos(a);nd.py=Math.sin(a);
  }});
  const idxOf={{}};CC.nodes.forEach((nd,i)=>idxOf[i]=nodes.indexOf(nd));
  const ex=[],ey=[],lx=[],ly=[],ltext=[];
  edges.forEach(e=>{{
    const s=CC.nodes[e.s],t=CC.nodes[e.t];
    if(!s||!t) return;
    ex.push(s.x,t.x,null);ey.push(s.y,t.y,null);
    lx.push((s.x+t.x)/2);ly.push((s.y+t.y)/2);
    ltext.push(`${{s.name}} + ${{t.name}}<br>${{e.v}} shared books`);
  }});
  Plotly.react('cooc_div',[
    {{x:ex,y:ey,mode:'lines',line:{{color:'#cbd5e1',width:1.2}},hoverinfo:'none',showlegend:false}},
    {{x:lx,y:ly,mode:'markers',marker:{{size:6,color:'rgba(0,0,0,0)'}},
      text:ltext,hovertemplate:'%{{text}}<extra></extra>',showlegend:false}},
    {{x:nodes.map(n=>n.x),y:nodes.map(n=>n.y),mode:'markers+text',
      marker:{{size:nodes.map(n=>Math.sqrt(n.count)*4+10),
              color:'#2563eb',opacity:.8,line:{{color:'white',width:1.5}}}},
      text:nodes.map(n=>n.name),textposition:'top center',
      textfont:{{size:9}},
      hovertemplate:'<b>%{{text}}</b><br>%{{customdata}} books<extra></extra>',
      customdata:nodes.map(n=>n.count),showlegend:false}},
  ],{{...L,plot_bgcolor:'white',height:540,
       margin:{{t:10,b:10,l:10,r:10}},
       xaxis:{{visible:false}},yaxis:{{visible:false}}}});
}}
drawCooc();

// 4. Topic matrix
function drawTopic(){{
  const src=TM[tmSplit];
  const sort=document.getElementById('tsort').value;
  const n=+document.getElementById('tn').value;
  let rows=src.terms.map((t,i)=>{{
    const r=src.matrix[i],tot=r.reduce((a,b)=>a+b,0);
    return{{t,r,tot,dom:r.indexOf(Math.max(...r))}};
  }});
  if(sort==='dom') rows.sort((a,b)=>a.dom-b.dom||b.tot-a.tot);
  rows=rows.slice(0,n);
  Plotly.react('topic_div',src.names.map((nm,ti)=>{{
    const norm=rows.map(d=>d.tot>0?+(d.r[ti]/d.tot).toFixed(3):0);
    return{{x:norm,y:rows.map(d=>d.t),type:'bar',orientation:'h',name:nm,
            marker:{{color:PAL[ti%PAL.length]}},
            hovertemplate:`${{nm}}: %{{x:.0%}}<br><b>%{{y}}</b><extra></extra>`}};
  }}),{{...L,barmode:'stack',height:Math.max(400,n*16+100),
        margin:{{t:10,b:40,l:220,r:20}},
        xaxis:{{title:'Proportion of containing books per topic',tickformat:'.0%'}},
        yaxis:{{autorange:'reversed',tickfont:{{size:9}}}},
        legend:{{orientation:'h',y:-0.12,font:{{size:10}}}}}});
}}
drawTopic();

// 5. Explorer — populate topic filter
EX.topic_names.forEach((nm,i)=>{{
  const o=document.createElement('option');o.value=i;o.textContent=nm;
  document.getElementById('et').appendChild(o);
}});

function drawExp(){{
  const q=document.getElementById('eq').value.toLowerCase().trim();
  const ft=+document.getElementById('et').value;
  if(!q){{
    document.getElementById('exp_div').innerHTML='<p style="color:#94a3b8;font-size:.9rem">Type a term to search.</p>';
    document.getElementById('exp-count').textContent='';return;
  }}
  const res=[];
  for(const [bid,terms] of Object.entries(EX.book_terms)){{
    if(ft!==-1 && String(EX.dom_topics[bid])!==String(ft)) continue;
    const hits=terms.filter(t=>t&&t.toLowerCase().includes(q));
    if(!hits.length) continue;
    // Find snippet for this book
    let snippet='';
    for(const [tl,bmap] of Object.entries(EX.snippets||{{}})){{
      if(tl.includes(q) && bmap[bid]){{snippet=bmap[bid];break;}}
    }}
    res.push({{bid,hits,snippet,year:EX.pub_years[bid],
               topic:EX.dom_topics[bid],title:EX.titles[bid]}});
  }}
  res.sort((a,b)=>b.hits.length-a.hits.length||(a.year||9999)-(b.year||9999));
  document.getElementById('exp-count').textContent=
    `${{res.length}} book${{res.length!==1?'s':''}} found`;
  if(!res.length){{
    document.getElementById('exp_div').innerHTML='<p style="color:#94a3b8">No matches.</p>';return;
  }}
  document.getElementById('exp_div').innerHTML=res.slice(0,60).map(r=>{{
    const col=PAL[(r.topic||0)%PAL.length];
    const tags=r.hits.slice(0,8).map(t=>`<span class="tag hi">${{t}}</span>`).join('');
    const snip=r.snippet?`<div class="snippet">"${{r.snippet}}"</div>`:'';
    return`<div class="bk">
      <h4>${{r.title||'Unknown'}}</h4>
      <div class="meta">${{r.year||'?'}} &nbsp;·&nbsp;
        <span class="badge" style="background:${{col}}">${{EX.topic_names[r.topic||0]||''}}</span>
      </div>
      <div class="tags">${{tags}}</div>
      ${{snip}}
    </div>`;
  }}).join('');
}}
</script>
</body></html>"""

html = html.replace('</body>', _PROV_NOTICE + '\n</body>', 1)
with open('data/outputs/book_nlp_index_analysis.html','w',encoding='utf-8') as f:
    f.write(html)
print(f"Saved ({len(html)//1024} KB)")