"""
fix_related_thumbs.py
Fixes the "You Might Also Like" section in all 29 articles.
Each related article card should show the TARGET article's own cover image,
not the current article's cover.
"""
import os, re, glob
from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
THUMBS_DIR = os.path.join(IMAGES_DIR, "thumbs")

def build_cover_map():
    """Build a map: article_slug -> cover image filename"""
    cover_map = {}
    for f in sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html"))):
        slug = os.path.basename(f).replace(".html", "")
        html = open(f, encoding="utf-8").read()
        match = re.search(
            r'<img[^>]*(?:class="w-full h-auto object-cover"[^>]*src="([^"]+)"|src="([^"]+)"[^>]*class="w-full h-auto object-cover")',
            html
        )
        if match:
            src = match.group(1) or match.group(2)
            cover_map[slug] = os.path.basename(src)
    return cover_map


def ensure_thumb(cover_name):
    """Ensure thumbnail exists for the given cover image."""
    thumb_path = os.path.join(THUMBS_DIR, cover_name)
    full_path = os.path.join(IMAGES_DIR, cover_name)
    
    if os.path.exists(thumb_path):
        return True
    
    if not os.path.exists(full_path):
        return False
    
    try:
        img = Image.open(full_path)
        img.thumbnail((480, 270))
        os.makedirs(THUMBS_DIR, exist_ok=True)
        img.save(thumb_path, "WEBP", quality=80, optimize=True, method=6)
        print(f"    [THUMB] Created thumbnail: {cover_name}")
        return True
    except Exception as e:
        print(f"    [ERROR] Could not create thumbnail for {cover_name}: {e}")
        return False


def fix_related_section(html_path, cover_map):
    """Fix the 'You Might Also Like' section in one article."""
    slug = os.path.basename(html_path).replace(".html", "")
    
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Find the "You Might Also Like" section
    related_pos = html.find("You Might Also Like")
    if related_pos == -1:
        print(f"  SKIP: {slug[:50]} (no related section)")
        return False
    
    # Work only on the related section (from "You Might Also Like" to end of that div block)
    # Find the closing </div> block after the grid
    related_end = html.find("<!-- ═══ TPT PRODUCT", related_pos)
    if related_end == -1:
        related_end = len(html)
    
    related_section = html[related_pos:related_end]
    original_section = related_section
    
    # Find each <a href="...article.html"> card block
    # Pattern: <a href="../articles/SLUG.html" ...>...<img...srcset="...">...</a>
    card_pattern = re.compile(
        r'(<a\s+href="(?:\.\./articles/)?([^"]+\.html)"[^>]*>.*?</a>)',
        re.DOTALL
    )
    
    fixes = 0
    for card_match in card_pattern.finditer(related_section):
        card_html = card_match.group(1)
        target_file = card_match.group(2)
        target_slug = os.path.basename(target_file).replace(".html", "")
        
        target_cover = cover_map.get(target_slug)
        if not target_cover:
            print(f"    WARNING: No cover found for {target_slug}")
            continue
        
        # Ensure thumbnail exists
        ensure_thumb(target_cover)
        
        # Build the correct src and srcset
        correct_thumb_src = f"../images/thumbs/{target_cover}"
        correct_srcset = f"../images/thumbs/{target_cover} 480w, ../images/{target_cover} 1200w"
        
        # Replace the src in this card
        new_card = re.sub(r'src="[^"]*"', f'src="{correct_thumb_src}"', card_html, count=1)
        # Replace the srcset in this card
        new_card = re.sub(r'srcset="[^"]*"', f'srcset="{correct_srcset}"', new_card, count=1)
        
        if new_card != card_html:
            related_section = related_section.replace(card_html, new_card)
            fixes += 1
    
    if fixes > 0:
        html = html[:related_pos] + related_section + html[related_end:]
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  FIXED: {slug[:50]} ({fixes} cards updated)")
        return True
    else:
        print(f"  OK:    {slug[:50]} (no changes needed)")
        return False


def main():
    print("=" * 60)
    print("  FIX RELATED ARTICLE THUMBNAILS")
    print("=" * 60)
    
    cover_map = build_cover_map()
    print(f"\nCover map built: {len(cover_map)} articles\n")
    
    articles = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html")))
    fixed = 0
    
    for f in articles:
        if fix_related_section(f, cover_map):
            fixed += 1
    
    print(f"\n{'=' * 60}")
    print(f"  DONE: {fixed} / {len(articles)} articles had their related thumbnails fixed")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
