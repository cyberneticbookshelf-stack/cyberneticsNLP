"""


05_visualize_chapters.py
─────────────────────────────────────────────────────────────────────────────
Produces 7 figures for the chapter-level analysis report.

Fig 1 – NMF reconstruction error curve
Fig 2 – Topic-word heatmap  (topics × top words)
Fig 3 – Book × Topic heatmap (chapter counts per topic per book)
Fig 4 – K-Means elbow + silhouette
Fig 5 – Chapter scatter 2-D (coloured by NMF topic)
Fig 6 – Chapter scatter 2-D (coloured by cluster)
Fig 7 – Topic proportions per book (stacked bar)

Input:  nlp_results_chapters.json, summaries.json
Output: figures/chfig1_*.png … figures/chfig7_*.png
"""

# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_metadata_full.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


import json, os, textwrap
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns

os.makedirs('figures', exist_ok=True)

with open(str(JSON_DIR / 'nlp_results_chapters.json')) as f:
    R = json.load(f)
with open(str(JSON_DIR / 'summaries.json')) as f:
    S = json.load(f)

n_topics    = R['n_topics']
n_clusters  = R['best_k']
chs         = R['chapters']
book_ids    = R['book_ids']
dom_topics  = R['dominant_topics']
clusters    = R['cluster_labels']
top_words   = R['top_words']
book_tc     = R['book_topic_counts']
coords_2d   = np.array(R['coords_2d'])

# Colour palettes
TOPIC_COLORS   = plt.cm.Set1(np.linspace(0, 1, n_topics))
CLUSTER_COLORS = plt.cm.tab20(np.linspace(0, 1, n_clusters))
BG             = '#F7F9FC'

# Abbreviated topic labels
_BASE_LABELS = [
    'Human &\nSocial Experience',
    'Mathematical &\nFormal Systems',
    'General Systems\nTheory',
    'History & Philosophy\nof Cybernetics',
    'Management &\nOrg. Cybernetics',
    'Control Theory\n& Engineering',
    'Topic 7', 'Topic 8', 'Topic 9',
]
TOPIC_LABELS = (_BASE_LABELS + [f'Topic\n{i+1}' for i in range(9, 25)])[:n_topics]

SHORT_LABELS = [f"T{i+1}" for i in range(n_topics)]

# ── Fig 1: NMF reconstruction error curve ────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 4), facecolor=BG)
ax.set_facecolor(BG)
ks   = sorted(int(k) for k in R['recon_errors'])
errs = [R['recon_errors'][str(k)] for k in ks]
ax.plot(ks, errs, 'o-', color='#2563EB', lw=2.5, ms=7, zorder=3)
ax.axvline(n_topics, color='#DC2626', lw=1.8, ls='--', label=f'Chosen k={n_topics}')
ax.fill_between(ks, errs, alpha=0.12, color='#2563EB')
ax.set_xlabel('Number of Topics (k)', fontsize=11)
ax.set_ylabel('Reconstruction Error', fontsize=11)
ax.set_title('NMF Topic Selection: Reconstruction Error vs k', fontsize=13, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('figures/chfig1_nmf_error.png', dpi=150, bbox_inches='tight')
plt.close()
print("Fig 1 saved")

# ── Fig 2: Topic-word heatmap ─────────────────────────────────────────────────
n_words  = 10
word_mat = np.zeros((n_topics, n_words))
col_labs = []
for t, words in enumerate(top_words):
    for w, word in enumerate(words[:n_words]):
        word_mat[t, w] = n_words - w   # rank score for colouring

fig, ax = plt.subplots(figsize=(13, 0.75 * n_topics + 1.5), facecolor=BG)
ax.set_facecolor(BG)
word_labels = [words[:n_words] for words in top_words]
flat_words  = [words[:n_words] for words in top_words]

cmap = LinearSegmentedColormap.from_list('bluewhite', ['#F0F4FF', '#1D4ED8'])
im   = ax.imshow(word_mat, cmap=cmap, aspect='auto', vmin=0, vmax=n_words)

# Annotate cells with word text
for t in range(n_topics):
    for w in range(min(n_words, len(top_words[t]))):
        ax.text(w, t, top_words[t][w], ha='center', va='center',
                fontsize=8.5, fontweight='semibold', color='#1e293b')

ax.set_xticks(range(n_words))
ax.set_xticklabels([f'#{i+1}' for i in range(n_words)], fontsize=9)
ax.set_yticks(range(n_topics))
ax.set_yticklabels([f"T{i+1} — {TOPIC_LABELS[i].replace(chr(10),' ')}"
                    for i in range(n_topics)], fontsize=9.5)
ax.set_title('NMF Topics: Top Words by Rank', fontsize=13, fontweight='bold', pad=10)
plt.tight_layout()
plt.savefig('figures/chfig2_topic_words.png', dpi=150, bbox_inches='tight')
plt.close()
print("Fig 2 saved")

# ── Fig 3: Book × Topic heatmap ───────────────────────────────────────────────
# Matrix: rows = books, cols = topics, cell = chapter count
book_short = [S[bid]['title'][:35] + ('…' if len(S[bid]['title'])>35 else '')
              for bid in book_ids]
mat = np.array([[book_tc.get(bid, [0]*n_topics)[t] for t in range(n_topics)]
                for bid in book_ids], dtype=float)

# Normalise rows to show proportion (so all books are comparable)
row_sums = mat.sum(axis=1, keepdims=True)
mat_norm = np.divide(mat, row_sums, where=row_sums>0)

fig, ax = plt.subplots(figsize=(14, 0.55 * len(book_ids) + 2), facecolor=BG)
ax.set_facecolor(BG)
cmap2 = LinearSegmentedColormap.from_list('heat', ['#F8FAFC', '#1D4ED8'])
im = ax.imshow(mat_norm, cmap=cmap2, aspect='auto', vmin=0, vmax=1)

for i in range(len(book_ids)):
    for j in range(n_topics):
        v = mat[i, j]
        if v > 0:
            ax.text(j, i, str(int(v)), ha='center', va='center',
                    fontsize=8, color='#1e293b' if mat_norm[i,j] < 0.6 else 'white')

ax.set_xticks(range(n_topics))
ax.set_xticklabels(SHORT_LABELS, fontsize=10, fontweight='bold')
ax.set_yticks(range(len(book_ids)))
ax.set_yticklabels(book_short, fontsize=7.5)
ax.set_xlabel('Topic', fontsize=11)
ax.set_title('Book × Topic: Chapter Count (shading = row proportion)', fontsize=12, fontweight='bold')

# Legend for topic labels
legend_text = '  '.join(f"{SHORT_LABELS[i]}: {TOPIC_LABELS[i].replace(chr(10),' ')}"
                         for i in range(n_topics))
fig.text(0.01, -0.01, textwrap.fill(legend_text, 120), fontsize=7.5,
         color='#475569', va='top')

cbar = plt.colorbar(im, ax=ax, fraction=0.02, pad=0.02)
cbar.set_label('Proportion of book chapters', fontsize=9)
plt.tight_layout()
plt.savefig('figures/chfig3_book_topic_heatmap.png', dpi=150, bbox_inches='tight',
            bbox_extra_artists=[])
plt.close()
print("Fig 3 saved")

# ── Fig 4: K-Means elbow + silhouette ─────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4), facecolor=BG)
for ax in (ax1, ax2):
    ax.set_facecolor(BG)
ks2  = sorted(int(k) for k in R['inertias'])
ine  = [R['inertias'][str(k)]  for k in ks2]
sils = [R['silhouettes'][str(k)] for k in ks2]

ax1.plot(ks2, ine, 'o-', color='#7C3AED', lw=2.5, ms=7)
ax1.axvline(n_clusters, color='#DC2626', ls='--', lw=1.8, label=f'k={n_clusters}')
ax1.set_xlabel('k'); ax1.set_ylabel('Inertia')
ax1.set_title('Elbow — K-Means Inertia', fontsize=12, fontweight='bold')
ax1.legend(); ax1.grid(True, alpha=0.3)

ax2.plot(ks2, sils, 's-', color='#059669', lw=2.5, ms=7)
ax2.axvline(n_clusters, color='#DC2626', ls='--', lw=1.8, label=f'k={n_clusters}')
ax2.set_xlabel('k'); ax2.set_ylabel('Silhouette Score')
ax2.set_title('Silhouette Score', fontsize=12, fontweight='bold')
ax2.legend(); ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('figures/chfig4_kmeans_elbow.png', dpi=150, bbox_inches='tight')
plt.close()
print("Fig 4 saved")

# ── Figs 5 & 6: Chapter scatter (topic colour, then cluster colour) ───────────
book_markers = ['o','s','^','D','P','X','*','h','8','v','<','>','p',
                'H','+','x','1','2','3','4'] * 3
book_marker_map = {bid: book_markers[i % len(book_markers)]
                   for i, bid in enumerate(book_ids)}

for fig_no, (label_arr, colors, title, fname) in enumerate([
    (dom_topics,  TOPIC_COLORS,   'Chapters by NMF Topic',   'chfig5_scatter_topics'),
    (clusters,    CLUSTER_COLORS, 'Chapters by K-Means Cluster', 'chfig6_scatter_clusters'),
]):
    fig, ax = plt.subplots(figsize=(12, 9), facecolor=BG)
    ax.set_facecolor(BG)
    n_groups = n_topics if fig_no == 0 else n_clusters

    for grp in range(n_groups):
        mask = [i for i, v in enumerate(label_arr) if v == grp]
        if not mask: continue
        x = coords_2d[mask, 0]
        y = coords_2d[mask, 1]
        ax.scatter(x, y, c=[colors[grp]], s=55, alpha=0.72,
                   edgecolors='white', lw=0.4, zorder=3)

    # Legend
    patches = [mpatches.Patch(color=colors[g],
               label=(TOPIC_LABELS[g].replace('\n',' ') if fig_no==0 else f'Cluster {g+1}'))
               for g in range(n_groups)]
    ax.legend(handles=patches, loc='upper left', fontsize=7.5,
              framealpha=0.9, ncol=2 if n_groups > 8 else 1)

    ax.set_xlabel('LSA Dimension 1', fontsize=11)
    ax.set_ylabel('LSA Dimension 2', fontsize=11)
    ax.set_title(f'Chapter 2-D Projection — {title}', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.2)
    plt.tight_layout()
    plt.savefig(f'figures/{fname}.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Fig {5+fig_no} saved")

# ── Fig 7: Topic proportions per book (stacked bar) ──────────────────────────
fig, ax = plt.subplots(figsize=(14, 7), facecolor=BG)
ax.set_facecolor(BG)
y_pos   = np.arange(len(book_ids))
bottoms = np.zeros(len(book_ids))

for t in range(n_topics):
    vals = [mat[i, t] / max(row_sums[i, 0], 1) for i in range(len(book_ids))]
    bars = ax.barh(y_pos, vals, left=bottoms, color=TOPIC_COLORS[t],
                   height=0.8, label=f"T{t+1} {TOPIC_LABELS[t].replace(chr(10),' ')}",
                   alpha=0.9)
    # Label bars that are >10%
    for j, (v, b) in enumerate(zip(vals, bottoms)):
        if v > 0.12:
            ax.text(b + v/2, j, f"T{t+1}", ha='center', va='center',
                    fontsize=7.5, fontweight='bold', color='white')
    bottoms += np.array(vals)

ax.set_yticks(y_pos)
ax.set_yticklabels(book_short, fontsize=7.5)
ax.set_xlabel('Proportion of Chapters', fontsize=11)
ax.set_title('Topic Mix per Book (chapter-level NMF)', fontsize=13, fontweight='bold')
ax.set_xlim(0, 1)
ax.legend(loc='lower right', fontsize=7.5, ncol=2, framealpha=0.9)
ax.grid(True, axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig('figures/chfig7_topic_proportions.png', dpi=150, bbox_inches='tight')
plt.close()
print("Fig 7 saved")

print("\nAll figures complete!")