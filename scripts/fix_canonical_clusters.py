"""
CONTENT CANNIBALIZATION FIX — Canonical URL Clustering

Analyzes articles.json to detect topic overlap (cannibalization)
and generates a canonical mapping:
  - Groups articles into clusters based on keyword overlap + title similarity
  - Selects the "pillar page" (best canonical) per cluster using:
    longest word count, most recent date, broadest title
  - Outputs a canonical_map.json that build_articles.py uses to set
    <link rel="canonical" href="..."> pointing to the pillar page

Usage:
    python scripts/fix_canonical_clusters.py              # Analyze + generate report
    python scripts/fix_canonical_clusters.py --apply      # Generate canonical_map.json
"""

import os, json, re, sys
from collections import defaultdict
from datetime import datetime
from itertools import combinations

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
SITE_URL = "https://littlesmartgenius.com"

# ── Similarity Thresholds ──
KEYWORD_OVERLAP_THRESHOLD = 0.35    # Jaccard >= 0.35 = likely overlap
TITLE_SIMILARITY_THRESHOLD = 0.50   # Token overlap >= 0.50 = similar title


# ═══════════════════════════════════════════════════════════
#  CORE ANALYSIS
# ═══════════════════════════════════════════════════════════

def load_articles():
    """Load all articles from articles.json."""
    path = os.path.join(PROJECT_ROOT, "articles.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("articles", data) if isinstance(data, dict) else data


def normalize_tokens(text):
    """Extract lowercase word tokens from text, filtering noise."""
    stopwords = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", 
        "for", "of", "with", "by", "is", "are", "was", "were", "be",
        "this", "that", "it", "its", "how", "what", "why", "when",
        "your", "our", "my", "their", "kids", "children", "child",
        "best", "ultimate", "guide", "top",
    }
    tokens = set(re.findall(r'[a-z]+', text.lower()))
    return tokens - stopwords


def jaccard_similarity(set_a, set_b):
    """Compute Jaccard similarity between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def keyword_overlap(article_a, article_b):
    """Compute keyword-based overlap between two articles."""
    kw_a = set(k.lower() for k in article_a.get("keywords", []))
    kw_b = set(k.lower() for k in article_b.get("keywords", []))
    return jaccard_similarity(kw_a, kw_b)


def title_similarity(article_a, article_b):
    """Compute title token overlap."""
    tokens_a = normalize_tokens(article_a.get("title", ""))
    tokens_b = normalize_tokens(article_b.get("title", ""))
    return jaccard_similarity(tokens_a, tokens_b)


def category_match(article_a, article_b):
    """Check if two articles share a parent category theme."""
    cat_a = article_a.get("category", "").lower()
    cat_b = article_b.get("category", "").lower()
    
    # Exact match
    if cat_a == cat_b:
        return True
    
    # Theme-based grouping (e.g., "Spot the Difference (Photorealistic)" ~= "Spot the Difference for Kids")
    theme_groups = [
        ["spot the difference"],
        ["word search"],
        ["coloring"],
        ["fine motor"],
        ["critical thinking"],
        ["math"],
        ["creative arts"],
    ]
    for group in theme_groups:
        a_match = any(theme in cat_a for theme in group)
        b_match = any(theme in cat_b for theme in group)
        if a_match and b_match:
            return True
    
    return False


def compute_overlap_score(article_a, article_b):
    """
    Compute a combined overlap score between two articles.
    Score components:
    - Keyword overlap (Jaccard on keyword lists): weight 0.5
    - Title similarity (Jaccard on title tokens): weight 0.3
    - Category match bonus: weight 0.2
    """
    kw_score = keyword_overlap(article_a, article_b)
    title_score = title_similarity(article_a, article_b)
    cat_bonus = 1.0 if category_match(article_a, article_b) else 0.0
    
    combined = (kw_score * 0.5) + (title_score * 0.3) + (cat_bonus * 0.2)
    return combined


# ═══════════════════════════════════════════════════════════
#  CLUSTERING (Union-Find)
# ═══════════════════════════════════════════════════════════

class UnionFind:
    """Simple union-find for clustering overlapping articles."""
    
    def __init__(self, elements):
        self.parent = {e: e for e in elements}
        self.rank = {e: 0 for e in elements}
    
    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # path compression
            x = self.parent[x]
        return x
    
    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
    
    def clusters(self):
        groups = defaultdict(list)
        for elem in self.parent:
            groups[self.find(elem)].append(elem)
        return list(groups.values())


def build_clusters(articles, threshold=0.40):
    """
    Build clusters of overlapping articles using Union-Find.
    Two articles are merged if their combined overlap score >= threshold.
    """
    slugs = [a["slug"] for a in articles]
    slug_map = {a["slug"]: a for a in articles}
    uf = UnionFind(slugs)
    
    overlaps = []
    
    for i, j in combinations(range(len(articles)), 2):
        a, b = articles[i], articles[j]
        score = compute_overlap_score(a, b)
        
        if score >= threshold:
            uf.union(a["slug"], b["slug"])
            overlaps.append((a["slug"], b["slug"], round(score, 3)))
    
    raw_clusters = uf.clusters()
    
    # Filter: only return clusters with 2+ articles (single articles don't cannibalize)
    multi_clusters = [c for c in raw_clusters if len(c) > 1]
    
    return multi_clusters, overlaps, slug_map


def select_pillar(cluster_slugs, slug_map):
    """
    Select the best "pillar page" from a cluster.
    Criteria (in order):
    1. Highest word count (most comprehensive)
    2. Most recent publication date
    3. Broadest title (fewer niche qualifiers)
    """
    articles = [slug_map[s] for s in cluster_slugs]
    
    def score(art):
        wc = art.get("word_count", 0)
        try:
            date = datetime.fromisoformat(art.get("iso_date", "2000-01-01T00:00:00"))
        except (ValueError, TypeError):
            date = datetime(2000, 1, 1)
        # Prefer fewer title tokens (broader, more pillar-like)
        title_breadth = 1.0 / max(len(art.get("title", "").split()), 1)
        return (wc, date, title_breadth)
    
    articles.sort(key=score, reverse=True)
    return articles[0]["slug"]


# ═══════════════════════════════════════════════════════════
#  OUTPUT
# ═══════════════════════════════════════════════════════════

def generate_report(clusters, slug_map):
    """Print a human-readable cannibalization report."""
    print("\n" + "=" * 70)
    print("  CONTENT CANNIBALIZATION REPORT")
    print("=" * 70)
    print(f"\n  Total clusters found: {len(clusters)}")
    print(f"  Total articles affected: {sum(len(c) for c in clusters)}")
    print()
    
    for i, cluster in enumerate(sorted(clusters, key=len, reverse=True), 1):
        pillar = select_pillar(cluster, slug_map)
        pillar_art = slug_map[pillar]
        
        print(f"  ─── Cluster #{i} ({len(cluster)} articles) ───")
        print(f"  📌 PILLAR: {pillar_art['title']}")
        print(f"     URL:   /articles/{pillar}.html")
        print(f"     Words: {pillar_art.get('word_count', '?')} | Category: {pillar_art.get('category', '?')}")
        print()
        
        for slug in cluster:
            if slug == pillar:
                continue
            art = slug_map[slug]
            print(f"     ↳ {art['title']}")
            print(f"       /articles/{slug}.html ({art.get('word_count', '?')} words)")
        
        print()


def generate_canonical_map(clusters, slug_map):
    """
    Generate canonical_map.json:
    {
        "article-slug": "pillar-slug",
        ...
    }
    Only non-pillar articles get entries (pillar articles are self-canonical).
    """
    canonical_map = {}
    
    for cluster in clusters:
        pillar = select_pillar(cluster, slug_map)
        pillar_url = f"{SITE_URL}/articles/{pillar}.html"
        
        for slug in cluster:
            if slug != pillar:
                canonical_map[slug] = {
                    "canonical_url": pillar_url,
                    "pillar_slug": pillar,
                    "pillar_title": slug_map[pillar]["title"],
                }
    
    return canonical_map


def main():
    apply_mode = "--apply" in sys.argv
    
    print("  Loading articles...")
    articles = load_articles()
    print(f"  Found {len(articles)} articles")
    
    print("  Analyzing keyword & title overlap...")
    clusters, overlaps, slug_map = build_clusters(articles, threshold=0.40)
    
    # Report
    generate_report(clusters, slug_map)
    
    if apply_mode:
        # Generate canonical_map.json
        canonical_map = generate_canonical_map(clusters, slug_map)
        
        output_path = os.path.join(PROJECT_ROOT, "canonical_map.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(canonical_map, f, indent=2, ensure_ascii=False)
        
        print(f"\n  ✅ Generated canonical_map.json")
        print(f"     {len(canonical_map)} articles → canonical pillar redirect")
        print(f"     Location: {output_path}")
        print()
        print("  Next step: integrate canonical_map.json into build_articles.py")
        print("  The build script will read this file and set <link rel='canonical'>")
        print("  to the pillar page URL for each non-pillar article.")
    else:
        print("  ─── DRY RUN ───")
        print("  Run with --apply to generate canonical_map.json")
        print(f"  Example: python scripts/fix_canonical_clusters.py --apply")


if __name__ == "__main__":
    main()
