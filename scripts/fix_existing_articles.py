"""
Fix existing article HTML files:
1. Restore truncated titles from slug names
2. Fix broken image paths (absolute server paths → relative)
3. Update <title>, <meta og:title>, <h1>, breadcrumb
"""
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_DIR = os.path.join(BASE, "articles")

# ── Title reconstruction from slug ─────────────────────────

# Words that should stay lowercase (title case exceptions)
LOWERCASE_WORDS = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'by', 'in', 'of', 'vs'}
# Words that should be capitalized specially
SPECIAL_WORDS = {
    'seo': 'SEO', 'tpt': 'TpT', 'ai': 'AI', 'diy': 'DIY', 'iq': 'IQ',
    'adhd': 'ADHD', 'stem': 'STEM', 'pdf': 'PDF', 'usa': 'USA',
}


def slug_to_title(slug):
    """Convert a slug to a properly capitalized title."""
    words = slug.replace('-', ' ').split()
    result = []
    for i, w in enumerate(words):
        low = w.lower()
        if low in SPECIAL_WORDS:
            result.append(SPECIAL_WORDS[low])
        elif i == 0 or low not in LOWERCASE_WORDS:
            # Capitalize first letter, handle apostrophes
            if "'" in w or "'" in w:
                result.append(w.title())
            else:
                result.append(w.capitalize())
        else:
            result.append(low)
    title = ' '.join(result)
    # Fix common patterns
    title = title.replace(' s ', "'s ")  # childs → child's
    title = title.replace('Childs', "Child's")
    title = title.replace(' i ', ' I ')  # Capitalize lone I
    return title


def fix_image_paths_in_html(html):
    """Fix all absolute server paths in image src attributes."""
    # Pattern: src="..//home/runner/work/.../images/xxx.webp"
    html = re.sub(
        r'src="\.\./(/[^"]*?/images/([^"]+))"',
        r'src="../images/\2"',
        html
    )
    # Pattern: src="/home/runner/work/.../images/xxx.webp" (without ../)
    html = re.sub(
        r'src="(/[^"]*?/images/([^"]+))"',
        r'src="../images/\2"',
        html
    )
    return html


def fix_title_in_html(html, full_title):
    """Replace truncated title in <h1>, <title>, og:title, and breadcrumbs."""
    # Fix <h1> — match any h1 content ending with ...
    html = re.sub(
        r'(<h1[^>]*>)\s*(.*?)\s*(</h1>)',
        lambda m: f'{m.group(1)}\n                    {full_title}\n                {m.group(3)}',
        html,
        flags=re.S
    )
    
    # Fix <title> tag
    html = re.sub(
        r'<title>.*?</title>',
        f'<title>{full_title} | Little Smart Genius</title>',
        html,
        flags=re.S
    )
    
    # Fix og:title
    html = re.sub(
        r'<meta property="og:title" content="[^"]*"',
        f'<meta property="og:title" content="{full_title}"',
        html
    )
    
    # Fix twitter:title
    html = re.sub(
        r'<meta name="twitter:title" content="[^"]*"',
        f'<meta name="twitter:title" content="{full_title}"',
        html
    )
    
    # Fix breadcrumb last item
    html = re.sub(
        r'(<span class="font-medium text-brand">)\s*(.*?)\s*(</span>\s*</li>\s*</ol>)',
        lambda m: f'{m.group(1)}{full_title}{m.group(3)}',
        html,
        count=1,
        flags=re.S
    )
    
    return html


def process_article(filepath):
    """Process a single article file."""
    fn = os.path.basename(filepath)
    slug = fn.replace('.html', '')
    
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
    
    original = html
    changes = []
    
    # 1. Fix broken image paths
    html = fix_image_paths_in_html(html)
    broken_before = len(re.findall(r'src="[^"]*(?:/home/|/runner/|/work/)[^"]*"', original))
    broken_after = len(re.findall(r'src="[^"]*(?:/home/|/runner/|/work/)[^"]*"', html))
    if broken_before > 0:
        changes.append(f"Fixed {broken_before - broken_after}/{broken_before} broken image paths")
    
    # 2. Check for truncated title
    m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S)
    if m:
        h1 = m.group(1).strip()
        if h1.endswith('...'):
            full_title = slug_to_title(slug)
            html = fix_title_in_html(html, full_title)
            changes.append(f"Title: '{h1[:50]}...' -> '{full_title}'")
    
    # 3. Write if changed
    if html != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        return changes
    return []


def main():
    total_fixed = 0
    total_titles = 0
    total_images = 0
    
    print("=" * 70)
    print("FIXING EXISTING ARTICLES")
    print("=" * 70)
    
    for fn in sorted(os.listdir(ARTICLES_DIR)):
        if not fn.endswith('.html'):
            continue
        
        filepath = os.path.join(ARTICLES_DIR, fn)
        changes = process_article(filepath)
        
        if changes:
            total_fixed += 1
            print(f"\n[FIXED] {fn}")
            for c in changes:
                print(f"  -> {c}")
                if 'Title' in c:
                    total_titles += 1
                if 'image' in c.lower():
                    total_images += 1
        else:
            print(f"[OK   ] {fn}")
    
    print("\n" + "=" * 70)
    print(f"DONE: {total_fixed} files modified, {total_titles} titles restored, {total_images} image fixes")
    print("=" * 70)


if __name__ == '__main__':
    main()
