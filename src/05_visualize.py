import json, re, numpy as np, matplotlib

# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_lang.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity

with open(str(JSON_DIR / 'nlp_results.json')) as f:
    R = json.load(f)
with open(str(JSON_DIR / 'books_clean.json')) as f:
    books = json.load(f)

book_ids = R['book_ids']
titles_short = [t[:35]+'…' if len(t)>35 else t for t in R['titles']]
n_topics = R['n_topics']
top_words = R['top_words']
doc_topic = np.array(R['doc_topic'])
dominant = R['dominant_topics']
cluster_labels = R['cluster_labels']
best_k = R['best_k']
cos_sim = np.array(R['cos_sim'])
X = np.array(R['tfidf_matrix'])

PALETTE = ['#2563eb','#16a34a','#dc2626','#d97706','#7c3aed','#0891b2','#be185d']
TOPIC_NAMES = [f"Topic {i+1}" for i in range(n_topics)]

# ── FIG 1: LDA Perplexity Curve ───────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7,4))
ks = [int(k) for k in sorted(R['perplexities'].keys())]
perps = [R['perplexities'][str(k)] for k in ks]
ax.plot(ks, perps, 'o-', color='#2563eb', lw=2, ms=8)
best_n = R['n_topics']
ax.axvline(best_n, color='#dc2626', ls='--', lw=1.5, label=f'Optimal k={best_n}')
ax.set_xlabel('Number of Topics'); ax.set_ylabel('Perplexity (lower = better)')
ax.set_title('LDA Coherence: Perplexity vs Number of Topics', fontweight='bold')
ax.legend(); ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('figures/fig1_lda_perplexity.png', dpi=130)
plt.close()
print("Fig 1 saved")

# ── FIG 2: Topic-Word Heatmap ─────────────────────────────────────────────────
top_n = 10
words_flat = []
heat_data = []
for t_idx, words in enumerate(top_words):
    top = words[:top_n]
    words_flat.extend(top)
    heat_data.append(top)

all_words = list(dict.fromkeys(words_flat))[:40]
mat = np.zeros((n_topics, len(all_words)))
for t_idx, words in enumerate(top_words):
    for rank, w in enumerate(words[:top_n]):
        if w in all_words:
            mat[t_idx, all_words.index(w)] = top_n - rank

fig, ax = plt.subplots(figsize=(16, 4))
sns.heatmap(mat, xticklabels=all_words, yticklabels=[f'Topic {i+1}' for i in range(n_topics)],
            cmap='YlOrRd', ax=ax, linewidths=0.3)
ax.set_title('LDA Topic-Word Distribution (top words per topic)', fontweight='bold')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=8)
plt.tight_layout()
plt.savefig('figures/fig2_topic_word_heatmap.png', dpi=130, bbox_inches='tight')
plt.close()
print("Fig 2 saved")

# ── FIG 3: Document-Topic Distribution (stacked bar) ─────────────────────────
fig, ax = plt.subplots(figsize=(14, 7))
x = np.arange(len(book_ids))
bottoms = np.zeros(len(book_ids))
for t in range(n_topics):
    vals = doc_topic[:, t]
    ax.bar(x, vals, bottom=bottoms, color=PALETTE[t % len(PALETTE)], label=f'Topic {t+1}', alpha=0.85)
    bottoms += vals
ax.set_xticks(x)
ax.set_xticklabels(titles_short, rotation=60, ha='right', fontsize=7)
ax.set_ylabel('Topic Proportion')
ax.set_title('Document–Topic Distribution (LDA)', fontweight='bold')
ax.legend(loc='upper right')
plt.tight_layout()
plt.savefig('figures/fig3_doc_topic_dist.png', dpi=130, bbox_inches='tight')
plt.close()
print("Fig 3 saved")

# ── FIG 4: Elbow Curve (K-Means) ─────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
ks = [int(k) for k in sorted(R['inertias'].keys())]
inertias = [R['inertias'][str(k)] for k in ks]
silhs = [R['silhouettes'].get(str(k), 0) for k in ks]

axes[0].plot(ks, inertias, 'o-', color='#2563eb', lw=2, ms=8)
axes[0].axvline(R['best_k'], color='#dc2626', ls='--', lw=1.5, label=f'Elbow k={R["best_k"]}')
axes[0].set_xlabel('k'); axes[0].set_ylabel('Inertia')
axes[0].set_title('Elbow Method', fontweight='bold')
axes[0].legend(); axes[0].grid(alpha=0.3)

axes[1].plot(ks, silhs, 's-', color='#16a34a', lw=2, ms=8)
axes[1].axvline(R['best_k'], color='#dc2626', ls='--', lw=1.5)
axes[1].set_xlabel('k'); axes[1].set_ylabel('Silhouette Score')
axes[1].set_title('Silhouette Scores', fontweight='bold')
axes[1].grid(alpha=0.3)

plt.suptitle('K-Means Cluster Optimisation', fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('figures/fig4_kmeans_elbow.png', dpi=130, bbox_inches='tight')
plt.close()
print("Fig 4 saved")

# ── FIG 5: Cosine Similarity Heatmap ─────────────────────────────────────────
sort_idx = np.argsort(cluster_labels)
sim_sorted = cos_sim[np.ix_(sort_idx, sort_idx)]
labels_sorted = [titles_short[i] for i in sort_idx]

fig, ax = plt.subplots(figsize=(14, 12))
sns.heatmap(sim_sorted, xticklabels=labels_sorted, yticklabels=labels_sorted,
            cmap='Blues', ax=ax, vmin=0, vmax=1, linewidths=0.2,
            annot=False)
ax.set_title('Cosine Similarity Matrix (books sorted by cluster)', fontweight='bold')
ax.set_xticklabels(ax.get_xticklabels(), rotation=60, ha='right', fontsize=7)
ax.set_yticklabels(ax.get_yticklabels(), fontsize=7)
plt.tight_layout()
plt.savefig('figures/fig5_cosine_heatmap.png', dpi=130, bbox_inches='tight')
plt.close()
print("Fig 5 saved")

# ── FIG 6: 2D Cluster Scatter (SVD/LSA) ──────────────────────────────────────
X_norm = normalize(X, norm='l2')
svd = TruncatedSVD(n_components=2, random_state=99)
X_2d = svd.fit_transform(X_norm)

fig, ax = plt.subplots(figsize=(13, 9))
for c in range(best_k):
    mask = np.array(cluster_labels) == c
    ax.scatter(X_2d[mask, 0], X_2d[mask, 1],
               color=PALETTE[c % len(PALETTE)], s=120,
               label=f'Cluster {c+1}', zorder=3, alpha=0.85, edgecolors='white', lw=0.5)
    for i, (x, y) in enumerate(zip(X_2d[:, 0][mask], X_2d[:, 1][mask])):
        idx = np.where(mask)[0][i]
        ax.annotate(titles_short[idx], (x, y), fontsize=6.5,
                    xytext=(4, 4), textcoords='offset points', zorder=4)

ax.set_xlabel(f'LSA Component 1 ({svd.explained_variance_ratio_[0]*100:.1f}% var)')
ax.set_ylabel(f'LSA Component 2 ({svd.explained_variance_ratio_[1]*100:.1f}% var)')
ax.set_title(f'Document Clustering — K-Means (k={best_k}) on TF-IDF/LSA space', fontweight='bold')
ax.legend(loc='upper right')
ax.grid(alpha=0.2)
plt.tight_layout()
plt.savefig('figures/fig6_cluster_scatter.png', dpi=130, bbox_inches='tight')
plt.close()
print("Fig 6 saved")

# ── FIG 7: Key Phrases per book (dynamic grid) ───────────────────────────────
kp    = R['keyphrases']
n     = len(book_ids)
ncols = 5
nrows = (n + ncols - 1) // ncols
fig, axes = plt.subplots(nrows, ncols, figsize=(20, max(4, 3 * nrows)))
axes = axes.flatten()
for i, bid in enumerate(book_ids):
    phrases = kp[bid][:6]
    scores  = list(range(len(phrases), 0, -1))
    color   = PALETTE[dominant[i] % len(PALETTE)]
    axes[i].barh(range(len(phrases)), scores, color=color, alpha=0.75)
    axes[i].set_yticks(range(len(phrases)))
    axes[i].set_yticklabels(phrases, fontsize=7)
    axes[i].set_title(R['titles'][i][:28]+'…' if len(R['titles'][i])>28 else R['titles'][i],
                      fontsize=7, fontweight='bold')
    axes[i].set_xticks([])
    axes[i].invert_yaxis()
for j in range(i + 1, len(axes)):
    axes[j].set_visible(False)
plt.suptitle('Key Phrases per Book (coloured by dominant LDA topic)', fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('figures/fig7_keyphrases.png', dpi=120, bbox_inches='tight')
plt.close()
print("Fig 7 saved")

print("\nAll visualizations complete!")