"""
SMART LINKER — V4.0
Scans existing articles and injects related article links using word-overlap scoring.
Replaces the old inject_internal_links() function.
"""

import os
import re
from typing import List, Dict, Tuple
from html.parser import HTMLParser

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(BASE_DIR, "articles")
SITE_BASE_URL = "https://littlesmartgenius.com"

INTERNAL_LINKS = {
    "freebies": f"{SITE_BASE_URL}/freebies.html",
    "products": f"{SITE_BASE_URL}/products.html",
    "blog": f"{SITE_BASE_URL}/blog.html",
    "about": f"{SITE_BASE_URL}/about.html",
}

# Common words to skip when scoring relevance
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "has", "have", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "this", "that", "these", "those",
    "it", "its", "they", "them", "their", "we", "our", "you", "your",
    "how", "what", "which", "who", "where", "when", "why", "not", "no",
    "all", "each", "every", "both", "few", "more", "most", "other",
    "some", "such", "than", "too", "very", "just", "about", "into",
}


class TitleExtractor(HTMLParser):
    """Extract the title from an article HTML file."""

    def __init__(self):
        super().__init__()
        self._in_title = False
        self._in_h1 = False
        self.title = ""

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True
        elif tag == "h1":
            self._in_h1 = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False

    def handle_data(self, data):
        if self._in_h1 and not self.title:
            self.title = data.strip()
        elif self._in_title and not self.title:
            self.title = data.strip()


class SmartLinker:
    """
    Scans existing articles and provides related-article suggestions.
    Uses word-overlap scoring for relevance matching.
    """

    def __init__(self, articles_dir: str = None):
        self.articles_dir = articles_dir or ARTICLES_DIR
        self.articles = self._scan_articles()

    def _scan_articles(self) -> List[Dict]:
        """Scan articles/ directory and extract title + filename for each."""
        articles = []

        if not os.path.exists(self.articles_dir):
            return articles

        for fname in os.listdir(self.articles_dir):
            if not fname.endswith(".html"):
                continue

            filepath = os.path.join(self.articles_dir, fname)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                extractor = TitleExtractor()
                extractor.feed(content)
                title = extractor.title

                if not title:
                    # Fallback: derive title from filename
                    title = fname.replace(".html", "").replace("-", " ").title()

                articles.append({
                    "filename": fname,
                    "title": title,
                    "url": f"articles/{fname}",
                    "words": self._extract_words(title),
                })
            except Exception:
                continue

        return articles

    def _extract_words(self, text: str) -> set:
        """Extract meaningful words from text, filtering stop words."""
        words = set(re.findall(r"[a-z]+", text.lower()))
        return words - STOP_WORDS

    def find_related_articles(
        self,
        title: str,
        category: str = "",
        keywords: str = "",
        max_results: int = 3,
        exclude_slug: str = ""
    ) -> List[Dict]:
        """
        Find related articles using word-overlap scoring.
        
        Scoring:
          - Title word overlap: 3 points per word
          - Category word overlap: 2 points per word
          - Keyword word overlap: 1 point per word
        """
        if not self.articles:
            return []

        query_words = self._extract_words(title)
        category_words = self._extract_words(category) if category else set()
        keyword_words = self._extract_words(keywords) if keywords else set()

        scored = []
        for article in self.articles:
            # Skip self
            if exclude_slug and exclude_slug in article["filename"]:
                continue

            a_words = article["words"]

            score = 0
            score += len(query_words & a_words) * 3
            score += len(category_words & a_words) * 2
            score += len(keyword_words & a_words) * 1

            if score > 0:
                scored.append((score, article))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        return [
            {
                "title": item[1]["title"],
                "url": item[1]["url"],
                "score": item[0],
            }
            for item in scored[:max_results]
        ]

    def inject_smart_links(
        self,
        content: str,
        title: str,
        category: str,
        keywords: str,
        slug: str = "",
        logger=None,
    ) -> str:
        """
        Inject smart internal links into article HTML content.
        
        Adds:
        1. Related articles card section (if articles exist)
        2. Standard internal links (freebies, products, blog)
        3. CTA box with product link
        """
        if logger:
            logger.info("Smart linking: scanning for related articles", 3)

        # --- 1. Standard internal links (always applied) ---
        # Freebies link
        freebies_patterns = [
            (r"\bfree\s+worksheets?\b", f'<a href="{INTERNAL_LINKS["freebies"]}">free worksheets</a>'),
            (r"\bfree\s+printables?\b", f'<a href="{INTERNAL_LINKS["freebies"]}">free printables</a>'),
            (r"\bfree\s+resources?\b", f'<a href="{INTERNAL_LINKS["freebies"]}">free resources</a>'),
        ]
        for pattern, replacement in freebies_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                content = re.sub(pattern, replacement, content, count=1, flags=re.IGNORECASE)
                if logger:
                    logger.debug("Freebies link injected", 4)
                break

        # Products link
        products_patterns = [
            (r"\bpremium\s+worksheets?\b", f'<a href="{INTERNAL_LINKS["products"]}">premium worksheets</a>'),
            (r"\bpremium\s+resources?\b", f'<a href="{INTERNAL_LINKS["products"]}">premium resources</a>'),
            (r"\bquality\s+worksheets?\b", f'<a href="{INTERNAL_LINKS["products"]}">quality worksheets</a>'),
        ]
        for pattern, replacement in products_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                content = re.sub(pattern, replacement, content, count=1, flags=re.IGNORECASE)
                if logger:
                    logger.debug("Products link injected", 4)
                break

        # Blog link
        blog_replacement = f'<a href="{INTERNAL_LINKS["blog"]}">our blog</a>'
        if re.search(r"\bblog\b", content, re.IGNORECASE):
            content = re.sub(r"\bblog\b", blog_replacement, content, count=1, flags=re.IGNORECASE)
            if logger:
                logger.debug("Blog link injected", 4)

        # --- 2. Related articles section (if we have articles) ---
        related = self.find_related_articles(title, category, keywords, max_results=3, exclude_slug=slug)

        if related:
            related_html = """
<div class="related-articles" style="background: var(--card-bg, #f8fafc); border: 1px solid var(--bord, #e2e8f0); border-radius: 12px; padding: 24px; margin: 30px 0;">
    <h3 style="margin-bottom: 16px; font-size: 1.2em;">You Might Also Like</h3>
    <ul style="list-style: none; padding: 0; margin: 0;">"""

            for article in related:
                related_html += f"""
        <li style="padding: 8px 0; border-bottom: 1px solid var(--bord, #e2e8f0);">
            <a href="{SITE_BASE_URL}/{article['url']}" style="color: var(--brand, #6366f1); text-decoration: none; font-weight: 500;">{article['title']}</a>
        </li>"""

            related_html += """
    </ul>
</div>"""

            # Insert before FAQ if it exists, otherwise before closing
            if '<div class="faq-section' in content:
                content = content.replace(
                    '<div class="faq-section',
                    related_html + '\n<div class="faq-section'
                )
            else:
                content += related_html

            if logger:
                logger.success(f"Related articles section added ({len(related)} links)", 3)
        else:
            if logger:
                logger.info("No related articles found yet (articles/ empty)", 3)

        if logger:
            logger.success("Smart linking complete", 3)

        return content


# --- Self-test ---
if __name__ == "__main__":
    print("=" * 60)
    print("SMART LINKER — Self Test")
    print("=" * 60)

    sl = SmartLinker()
    print(f"\nArticles found: {len(sl.articles)}")

    if sl.articles:
        for a in sl.articles[:5]:
            print(f"  - {a['title'][:60]}...")

    related = sl.find_related_articles(
        "Math Puzzles for Kids",
        "Math Skills",
        "math puzzles, number games, arithmetic"
    )
    print(f"\nRelated articles: {len(related)}")
    for r in related:
        print(f"  - {r['title']} (score: {r['score']})")

    # Test link injection on dummy content
    dummy = "<p>Check out our free worksheets and premium resources on our blog.</p>"
    result = sl.inject_smart_links(dummy, "Math Puzzles", "Math", "math puzzles")
    assert INTERNAL_LINKS["freebies"] in result
    print("\nLink injection: OK")

    print("\nAll tests passed!")
