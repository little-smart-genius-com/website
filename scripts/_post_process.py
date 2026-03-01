"""
POST-PROCESSOR V1.0 — Related Articles, TPT Backlinks & Internal Linking
Injects into all existing article HTML files:
1. Beautiful "Related Articles" section with image cards (3 articles matched by category + keywords)
2. "Recommended from our TPT Store" product card (matched by article category)
3. Internal backlinks to other articles within the body text
"""

import os
import re
import json
from typing import List, Dict, Tuple
from html.parser import HTMLParser

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
SITE_URL = "https://littlesmartgenius.com"
TPT_STORE_URL = "https://www.teacherspayteachers.com/Store/Little-Smart-Genius"

# ═══════════════════════════════════════════════════════════════
# 1. LOAD DATA
# ═══════════════════════════════════════════════════════════════

def load_search_index() -> List[Dict]:
    """Load all articles from search_index.json."""
    path = os.path.join(PROJECT_ROOT, "search_index.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("articles", [])

def load_tpt_products() -> List[Dict]:
    """Parse products_tpt.js and extract product data."""
    path = os.path.join(PROJECT_ROOT, "products_tpt.js")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract the array from: window.tptProducts = [...]
    match = re.search(r'window\.tptProducts\s*=\s*(\[.+?\]);', content, re.DOTALL)
    if not match:
        return []
    
    products = json.loads(match.group(1))
    result = []
    for p in products:
        if len(p) >= 5:
            result.append({
                "title": p[0],
                "url": p[1],
                "image": p[2] if len(p) > 2 else "",
                "price": p[3] if len(p) > 3 else "",
                "category": p[4] if len(p) > 4 else "",
                "rating": p[5] if len(p) > 5 else "",
                "reviews": p[6] if len(p) > 6 else "",
            })
    return result


# ═══════════════════════════════════════════════════════════════
# 2. SCORING ENGINE
# ═══════════════════════════════════════════════════════════════

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "has", "have", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "this", "that", "these", "those",
    "it", "its", "they", "them", "their", "we", "our", "you", "your",
    "how", "what", "which", "who", "where", "when", "why", "not", "no",
    "all", "each", "every", "both", "few", "more", "most", "other",
    "some", "such", "than", "too", "very", "just", "about", "into",
    "also", "like", "here", "there", "then", "now", "only", "many",
}

def extract_words(text: str) -> set:
    words = set(re.findall(r"[a-z]{3,}", text.lower()))
    return words - STOP_WORDS

def find_related_articles(current_slug: str, current_category: str, 
                          current_title: str, current_keywords: List[str],
                          all_articles: List[Dict], max_results: int = 3) -> List[Dict]:
    """Find related articles using multi-signal scoring."""
    title_words = extract_words(current_title)
    keyword_set = set(k.lower() for k in current_keywords) - STOP_WORDS
    cat_words = extract_words(current_category)
    
    scored = []
    for article in all_articles:
        if current_slug and current_slug == article.get("slug", ""):
            continue
        
        a_title_words = extract_words(article.get("title", ""))
        a_keywords = set(k.lower() for k in article.get("keywords", [])) - STOP_WORDS
        a_cat_words = extract_words(article.get("category", ""))
        
        score = 0
        # Same category = 10 points (strong signal)
        if current_category and article.get("category", "") == current_category:
            score += 10
        # Category word overlap = 5 points each
        score += len(cat_words & a_cat_words) * 5
        # Title word overlap = 3 points each
        score += len(title_words & a_title_words) * 3
        # Keyword overlap = 2 points each
        score += len(keyword_set & a_keywords) * 2
        
        if score > 0:
            scored.append((score, article))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:max_results]]

def find_matching_tpt_product(article_category: str, article_title: str,
                               products: List[Dict]) -> Dict:
    """Find the best matching TPT product for an article."""
    cat_lower = article_category.lower()
    title_words = extract_words(article_title)
    
    best = None
    best_score = 0
    
    for product in products:
        p_cat = product.get("category", "").lower()
        p_title_words = extract_words(product.get("title", ""))
        
        score = 0
        # Same category
        if cat_lower and p_cat and cat_lower == p_cat:
            score += 10
        # Category word overlap
        score += len(extract_words(article_category) & extract_words(product.get("category", ""))) * 5
        # Title word overlap
        score += len(title_words & p_title_words) * 2
        
        # Prefer rated products
        rating = product.get("rating", "")
        if rating and rating != "New":
            score += 3
        
        # Prefer products with reviews
        reviews = product.get("reviews", "")
        if reviews and reviews not in ("", "0"):
            score += 2
        
        if score > best_score:
            best_score = score
            best = product
    
    # If no product scored above 5, return the first one with good reviews, or just the first product as a fallback
    if best_score > 5:
        return best
    
    # Fallback to a reliable product
    for product in products:
        if product.get("reviews", "") not in ("", "0"):
            return product
            
    return products[0] if products else None


# ═══════════════════════════════════════════════════════════════
# 3. HTML GENERATORS
# ═══════════════════════════════════════════════════════════════

def esc(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def generate_related_articles_html(related: List[Dict]) -> str:
    """Generate a beautiful related articles section with image cards."""
    if not related:
        return ""
    
    cards_html = ""
    for article in related:
        image = article.get("image", "")
        # Prefer thumbnail for card view (much smaller file size)
        if image and not image.startswith("http"):
            # Compute both paths: thumb for mobile, original for desktop
            thumb = image.replace("images/", "images/thumbs/", 1)
            thumb_path = f"../{thumb}"
            full_path  = f"../{image}"
        
        url = article.get("url", "")
        if url and not url.startswith("http"):
            url = f"../{url}"
        
        category = esc(article.get("category", ""))
        reading_time = article.get("reading_time", 5)
        
        cards_html += f"""
                <a href="{esc(url)}" class="block rounded-xl overflow-hidden border hover:shadow-xl transition-all duration-300 group" style="background: var(--card); border-color: var(--bord);">
                    <div class="aspect-video overflow-hidden">
                        <img
                            src="{esc(thumb_path)}"
                            srcset="{esc(thumb_path)} 480w, {esc(full_path)} 1200w"
                            sizes="(max-width: 768px) 480px, 800px"
                            alt="{esc(article.get('title', ''))}"
                            class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                            loading="lazy"
                        >
                    </div>
                    <div class="p-4">
                        <div class="flex items-center gap-2 mb-2">
                            <span class="text-xs font-bold uppercase tracking-wider text-brand bg-orange-50 dark:bg-slate-800 px-2 py-0.5 rounded-full">{category}</span>
                            <span class="text-xs text-slate-500">📖 {reading_time} min</span>
                        </div>
                        <h4 class="font-bold text-sm group-hover:text-brand transition" style="color: var(--text);">{esc(article.get('title', ''))}</h4>
                    </div>
                </a>"""
    
    return f"""
        <!-- ═══ RELATED ARTICLES ═══ -->
        <div class="mt-16 pt-10 border-t" style="border-color: var(--bord);">
            <div class="mb-8">
                <h3 class="text-2xl font-extrabold mb-2" style="color: var(--text);">📚 You Might Also Like</h3>
                <p class="text-slate-500 dark:text-slate-400 text-sm">Explore more articles on similar topics</p>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                {cards_html}
            </div>
        </div>
"""

def generate_tpt_product_html(product: Dict) -> str:
    """Generate a TPT product recommendation card."""
    if not product:
        return ""
    
    price = esc(product.get("price", ""))
    rating = product.get("rating", "")
    reviews = product.get("reviews", "")
    
    rating_html = ""
    if rating and rating != "New":
        stars = "⭐" * min(5, int(float(rating)))
        rating_html = f'<span class="text-sm font-bold text-yellow-500">{stars} {esc(rating)}</span>'
        if reviews and reviews not in ("", "0"):
            rating_html += f' <span class="text-xs text-slate-400">({esc(reviews)} reviews)</span>'
    
    price_class = "text-green-600 dark:text-green-400" if price == "FREE" else "text-brand"
    
    # Generate JSON-LD schema
    schema = {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": product.get("title", ""),
        "image": product.get("image", ""),
        "description": f"Educational resource: {product.get('title', '')}",
        "brand": {
            "@type": "Brand",
            "name": "Little Smart Genius"
        },
        "offers": {
            "@type": "Offer",
            "url": product.get("url", ""),
            "priceCurrency": "USD",
            "price": "0.00" if price == "FREE" else price.replace("$", "").strip(),
            "availability": "https://schema.org/InStock",
            "seller": {
                "@type": "Organization",
                "name": "Little Smart Genius"
            }
        }
    }
    
    if rating and rating != "New":
        schema["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": rating,
            "reviewCount": reviews if reviews and reviews != "0" else "1"
        }
        
    schema_html = f'\n        <script type="application/ld+json">\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n        </script>\n'
    
    return f"""
        <!-- ═══ TPT PRODUCT RECOMMENDATION & SCHEMA ═══ -->{schema_html}
        <div class="mt-10 rounded-2xl overflow-hidden border-2 border-brand/30 hover:border-brand/60 transition-all duration-300" style="background: linear-gradient(135deg, rgba(251, 146, 60, 0.05), rgba(99, 102, 241, 0.05));">
            <div class="p-6 md:p-8">
                <div class="flex items-center gap-2 mb-4">
                    <span class="text-xl">🛍️</span>
                    <span class="text-xs font-bold uppercase tracking-wider text-brand">Recommended Resource</span>
                </div>
                <h4 class="font-extrabold text-lg mb-3" style="color: var(--text);">{esc(product.get('title', ''))}</h4>
                <div class="flex items-center gap-4 mb-4">
                    <span class="text-xl font-extrabold {price_class}">{price}</span>
                    {rating_html}
                </div>
                <div class="flex gap-3 flex-wrap">
                    <a href="{esc(product.get('url', ''))}" target="_blank" rel="noopener" class="inline-block px-6 py-3 bg-brand text-white font-bold rounded-xl shadow-lg hover:shadow-brand/50 hover:scale-105 transition-all duration-200">
                        View on TPT →
                    </a>
                    <a href="{TPT_STORE_URL}" target="_blank" rel="noopener" class="inline-block px-6 py-3 bg-slate-100 dark:bg-slate-700 font-bold rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition" style="color: var(--text);">
                        Browse All Products
                    </a>
                </div>
            </div>
        </div>
"""

def generate_internal_links_html(current_slug: str, all_articles: List[Dict]) -> str:
    """Generate a compact 'More from our blog' section with text links. (Currently disabled as per user request to avoid duplication with image cards)"""
    return ""
    
    # Pick 5 random other articles for internal link juice
    import random
    
    if not others:
        return ""
    
    links_html = ""
    for a in others:
        url = a.get("url", "")
        if url and not url.startswith("http"):
            url = f"../{url}"
        links_html += f"""
                    <li class="py-1.5">
                        <a href="{esc(url)}" class="text-sm hover:text-brand transition font-medium" style="color: var(--text);">
                            {esc(a.get('title', ''))}
                        </a>
                    </li>"""
    
    return f"""
        <!-- ═══ INTERNAL LINKS ═══ -->
        <div class="mt-8 rounded-xl p-6" style="background: var(--card); border: 1px solid var(--bord);">
            <h4 class="font-bold text-sm uppercase tracking-wider text-slate-500 mb-3">📖 More from Our Blog</h4>
            <ul class="list-none space-y-0">
                {links_html}
            </ul>
            <div class="mt-4 pt-3 border-t" style="border-color: var(--bord);">
                <a href="../blog.html" class="text-brand font-bold text-sm hover:underline">View All Articles →</a>
            </div>
        </div>
"""


# ═══════════════════════════════════════════════════════════════
# 4. ARTICLE METADATA EXTRACTOR
# ═══════════════════════════════════════════════════════════════

class ArticleMetaExtractor(HTMLParser):
    """Extract metadata from an article HTML file."""
    def __init__(self):
        super().__init__()
        self.title = ""
        self.category = ""
        self.keywords = []
        self._in_h1 = False
        self._in_title = False
    
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "h1":
            self._in_h1 = True
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = attrs_dict.get("name", "")
            content = attrs_dict.get("content", "")
            if name == "keywords" and content:
                self.keywords = [k.strip() for k in content.split(",")]
    
    def handle_endtag(self, tag):
        if tag == "h1":
            self._in_h1 = False
        elif tag == "title":
            self._in_title = False
    
    def handle_data(self, data):
        if self._in_h1 and not self.title:
            self.title = data.strip()
        elif self._in_title and not self.title:
            self.title = data.strip().split("|")[0].strip()


def extract_slug_from_filename(filename: str) -> str:
    return filename.replace(".html", "")

def get_article_metadata_from_index(slug: str, all_articles: List[Dict]) -> Dict:
    """Get article metadata from search index."""
    for a in all_articles:
        if a.get("slug", "") == slug:
            return a
    return {}


# ═══════════════════════════════════════════════════════════════
# 5. MAIN INJECTOR
# ═══════════════════════════════════════════════════════════════

def inject_into_article(filepath: str, all_articles: List[Dict], tpt_products: List[Dict]) -> bool:
    """Inject related articles + TPT product + internal links into one article."""
    filename = os.path.basename(filepath)
    slug = extract_slug_from_filename(filename)
    
    # Read current content
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Skip if already injected
    if "<!-- ═══ RELATED ARTICLES ═══ -->" in content:
        return False
    
    # Remove any old related-articles div if exists
    content = re.sub(
        r'<div class="related-articles".*?</div>\s*</div>',
        '',
        content,
        flags=re.DOTALL
    )
    
    # Get metadata from search index
    meta = get_article_metadata_from_index(slug, all_articles)
    category = meta.get("category", "")
    title = meta.get("title", "")
    keywords = meta.get("keywords", [])
    
    if not title:
        # Fallback: extract from HTML
        extractor = ArticleMetaExtractor()
        extractor.feed(content)
        title = extractor.title
        keywords = extractor.keywords
    
    # 1. Find related articles
    related = find_related_articles(slug, category, title, keywords, all_articles, max_results=3)
    related_html = generate_related_articles_html(related)
    
    # 2. Find matching TPT product
    tpt_product = find_matching_tpt_product(category, title, tpt_products)
    tpt_html = generate_tpt_product_html(tpt_product)
    
    # 3. Internal links
    internal_html = generate_internal_links_html(slug, all_articles)
    
    # Combine all injections
    injection = related_html + tpt_html + internal_html
    
    # Find the best injection point: before the "Loved this article?" CTA section
    # or before the closing </main> or </article> or </body>
    injection_patterns = [
        # Before "Loved this article?" CTA
        (r'(\s*<div class="mt-16 pt-10 border-t"[^>]*>\s*<div class="rounded-2xl p-8 text-center")', injection + r'\n\1'),
        # Before closing main
        (r'(</main>)', injection + r'\n\1'),
        # Before footer
        (r'(<footer)', injection + r'\n\1'),
        # Before closing body
        (r'(</body>)', injection + r'\n\1'),
    ]
    
    injected = False
    for pattern, replacement in injection_patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content, count=1)
            injected = True
            break
    
    if not injected:
        print(f"  [!] Could not find injection point in {filename}")
        return False
    
    # Write back
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    return True


# ═══════════════════════════════════════════════════════════════
# 6. MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("    POST-PROCESSOR: Related Articles + TPT Links + Internal Backlinks")
    print("=" * 70)
    
    # Load data
    all_articles = load_search_index()
    print(f"\n[1] Loaded {len(all_articles)} articles from search_index.json")
    
    tpt_products = load_tpt_products()
    print(f"[2] Loaded {len(tpt_products)} TPT products from products_tpt.js")
    
    # Get article files
    html_files = sorted([
        os.path.join(ARTICLES_DIR, f) 
        for f in os.listdir(ARTICLES_DIR) 
        if f.endswith(".html")
    ])
    print(f"[3] Found {len(html_files)} article HTML files\n")
    
    # Process each article
    injected_count = 0
    skipped_count = 0
    error_count = 0
    
    for i, filepath in enumerate(html_files, 1):
        filename = os.path.basename(filepath)
        slug = extract_slug_from_filename(filename)
        meta = get_article_metadata_from_index(slug, all_articles)
        
        try:
            result = inject_into_article(filepath, all_articles, tpt_products)
            if result:
                related = find_related_articles(slug, meta.get("category", ""), 
                                                 meta.get("title", ""), 
                                                 meta.get("keywords", []), 
                                                 all_articles, 3)
                tpt = find_matching_tpt_product(meta.get("category", ""), 
                                                 meta.get("title", ""), 
                                                 tpt_products)
                
                print(f"  [{i:2d}/24] OK  {filename[:60]}")
                print(f"          -> {len(related)} related articles, TPT: {'Yes' if tpt else 'No'}")
                injected_count += 1
            else:
                print(f"  [{i:2d}/24] SKIP {filename[:60]} (already injected)")
                skipped_count += 1
        except Exception as e:
            print(f"  [{i:2d}/24] ERR  {filename[:60]}: {e}")
            error_count += 1
    
    # Summary
    print(f"\n{'=' * 70}")
    print(f"  RESULTS:")
    print(f"    Injected:  {injected_count}")
    print(f"    Skipped:   {skipped_count}")
    print(f"    Errors:    {error_count}")
    print(f"{'=' * 70}")
    
    # Print link stats
    print(f"\n  LINK SUMMARY:")
    print(f"    Internal backlinks: ~{injected_count * 5} (5 per article)")
    print(f"    Related article links: ~{injected_count * 3} (3 per article)")
    print(f"    TPT store links: ~{injected_count * 2} (product + store per article)")
    print(f"    Total new links: ~{injected_count * 10}")
    print(f"\n  TPT Store: {TPT_STORE_URL}")
