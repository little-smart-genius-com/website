"""
SEO FIX SCRIPT — Applies all critical fixes to build_articles.py and rebuild_blog_pages.py
Run this once to patch the autoblog pipeline.
"""
import re

SCRIPT_DIR = r"c:\Users\Omar\Desktop\little-smart-genius-site\Nouveau dossier\online\Little_Smart_Genius\scripts"

# ═══════════════════════════════════════════════════════════════════════════════
# FIX 1: build_articles.py
# ═══════════════════════════════════════════════════════════════════════════════
path = SCRIPT_DIR + r"\build_articles.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

changes = 0

# T2: Nav links — desktop (../products.html → /products.html etc.)
nav_replacements = {
    'href="../products.html"': 'href="/products.html"',
    'href="../freebies.html"': 'href="/freebies.html"',
    'href="../about.html"': 'href="/about.html"',
    'href="../contact.html"': 'href="/contact.html"',
    'href="../blog/"': 'href="/blog/"',
    'href="../privacy.html"': 'href="/privacy.html"',
    'href="../terms.html"': 'href="/terms.html"',
    'href="../education.html"': 'href="/education.html"',
    'href="../legal.html"': 'href="/legal.html"',
    'src="../exit-intent.js"': 'src="/exit-intent.js"',
}
for old, new in nav_replacements.items():
    count = content.count(old)
    if count > 0:
        content = content.replace(old, new)
        changes += count
        print(f"  T2: Replaced {count}x  {old}  →  {new}")

# T1: Tags href — ../blog.html → /blog/
old_tag = 'href="../blog.html"'
new_tag = 'href="/blog/"'
count = content.count(old_tag)
if count > 0:
    content = content.replace(old_tag, new_tag)
    changes += count
    print(f"  T1: Replaced {count}x  {old_tag}  →  {new_tag}")

# T3: Sitemap — blog.html → blog/
old_sitemap = "('blog.html', '0.9', 'daily')"
new_sitemap = "('blog/', '0.9', 'daily')"
if old_sitemap in content:
    content = content.replace(old_sitemap, new_sitemap)
    changes += 1
    print(f"  T3: Fixed sitemap entry blog.html → blog/")

# T3: Add missing legal pages to sitemap
old_sitemap_block = """        ('contact.html', '0.7', 'monthly'),
    ]"""
new_sitemap_block = """        ('contact.html', '0.7', 'monthly'),
        ('terms.html', '0.5', 'yearly'),
        ('privacy.html', '0.5', 'yearly'),
        ('education.html', '0.6', 'monthly'),
        ('legal.html', '0.5', 'yearly'),
    ]"""
if old_sitemap_block in content:
    content = content.replace(old_sitemap_block, new_sitemap_block)
    changes += 1
    print(f"  T3: Added terms, privacy, education, legal to sitemap")

# T4: Add fix_placeholder_links function after fix_domain_urls
# Also update fix_domain_urls docstring and logic (../ → /)
old_domain_func = """    # Convert all other domain links to ../path
    content = re.sub(
        r'https?://(?:www\\.)?littlesmartgenius\\.com/([^\"\\'>\\s]*)',
        r'../\\1',
        content,
        flags=re.IGNORECASE
    )
    
    # Edge case: root domain with no path → ../index.html
    content = re.sub(
        r'https?://(?:www\\.)?littlesmartgenius\\.com/?([\"\\'])',
        r'../index.html\\1',
        content,
        flags=re.IGNORECASE
    )
    
    return content"""

new_domain_func = """    # Convert all other domain links to absolute /path
    content = re.sub(
        r'https?://(?:www\\.)?littlesmartgenius\\.com/([^\"\\'>\\s]*)',
        r'/\\1',
        content,
        flags=re.IGNORECASE
    )
    
    # Edge case: root domain with no path → /
    content = re.sub(
        r'https?://(?:www\\.)?littlesmartgenius\\.com/?([\"\\'])',
        r'/\\1',
        content,
        flags=re.IGNORECASE
    )
    
    return content"""

if old_domain_func in content:
    content = content.replace(old_domain_func, new_domain_func)
    changes += 1
    print(f"  T4a: Updated fix_domain_urls to use absolute /paths")

# T4b: Add fix_placeholder_links after fix_domain_urls
placeholder_func = '''

def fix_placeholder_links(content: str) -> str:
    """Remove or fix AI-generated placeholder links that lead to 404s.
    
    The AI content generator sometimes produces links to non-existent pages like:
      - another-topic.html
      - placeholder.html
    
    Strategy: unwrap the <a> tag but keep the inner text visible.
    """
    PLACEHOLDER_PATTERNS = [
        r'another-topic\\.html',
        r'placeholder\\.html',
        r'example-.*?\\.html',
        r'related-topic\\.html',
        r'sample-.*?\\.html',
        r'your-.*?\\.html',
        r'insert-.*?\\.html',
        r'link-to-.*?\\.html',
    ]
    
    for pattern in PLACEHOLDER_PATTERNS:
        content = re.sub(
            rf'<a\\s+href="[^"]*{pattern}"[^>]*>(.*?)</a>',
            r'\\1',
            content,
            flags=re.IGNORECASE | re.DOTALL
        )
    
    # Fix nested/malformed <a> tags (e.g. <a href="x"><a href="y">text</a>text</a>)
    content = re.sub(
        r'<a\\s+href="[^"]*"[^>]*>\\s*<a\\s+href="([^"]*)"[^>]*>(.*?)</a>(.*?)</a>',
        r'<a href="\\1">\\2\\3</a>',
        content,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    return content

'''

# Insert placeholder_func right before the CONTENT POST-PROCESSORS comment
marker = "# " + "═" * 79 + "\r\n# CONTENT POST-PROCESSORS"
if marker not in content:
    marker = "# " + "═" * 79 + "\n# CONTENT POST-PROCESSORS"

if marker in content:
    content = content.replace(marker, placeholder_func.rstrip() + "\r\n\r\n" + marker)
    changes += 1
    print(f"  T4b: Added fix_placeholder_links() function")
else:
    print(f"  [!] Could not find CONTENT POST-PROCESSORS marker")

# T4c: Hook fix_placeholder_links into the content pipeline
# It should be called right after fix_domain_urls
old_pipeline = "    content = fix_domain_urls(content)"
new_pipeline = "    content = fix_domain_urls(content)\r\n    content = fix_placeholder_links(content)"
if old_pipeline in content and "fix_placeholder_links" not in content.split("fix_domain_urls(content)")[1][:100]:
    content = content.replace(old_pipeline, new_pipeline, 1)
    changes += 1
    print(f"  T4c: Hooked fix_placeholder_links into content pipeline")

# Write back
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print(f"\n  ✅ build_articles.py: {changes} changes applied\n")


# ═══════════════════════════════════════════════════════════════════════════════
# FIX 2: rebuild_blog_pages.py — T6: Footer links
# ═══════════════════════════════════════════════════════════════════════════════
path2 = SCRIPT_DIR + r"\rebuild_blog_pages.py"
with open(path2, "r", encoding="utf-8") as f:
    content2 = f.read()

changes2 = 0

# Fix footer links in the hardcoded footer template
footer_fixes = {
    'href="terms.html"': 'href="/terms.html"',
    'href="privacy.html"': 'href="/privacy.html"',
    'href="education.html"': 'href="/education.html"',
    'href="legal.html"': 'href="/legal.html"',
}
for old, new in footer_fixes.items():
    count = content2.count(old)
    if count > 0:
        content2 = content2.replace(old, new)
        changes2 += count
        print(f"  T6: Replaced {count}x  {old}  →  {new}")

with open(path2, "w", encoding="utf-8") as f:
    f.write(content2)
print(f"\n  ✅ rebuild_blog_pages.py: {changes2} changes applied\n")


# ═══════════════════════════════════════════════════════════════════════════════
# FIX 3: Batch fix existing articles — T11: another-topic.html
# ═══════════════════════════════════════════════════════════════════════════════
import os, glob

ARTICLES_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "articles")
fixed_articles = 0
total_links_fixed = 0

for html_file in glob.glob(os.path.join(ARTICLES_DIR, "*.html")):
    with open(html_file, "r", encoding="utf-8") as f:
        html = f.read()
    
    original = html
    
    # Fix another-topic.html — unwrap the <a> tag, keep inner text
    html = re.sub(
        r'<a\s+href="another-topic\.html"[^>]*>(.*?)</a>',
        r'\1',
        html,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    # Fix nested <a> tags (e.g. <a href="x"><a href="y">text</a>text</a>)
    html = re.sub(
        r'<a\s+href="[^"]*"[^>]*>\s*<a\s+href="([^"]*)"[^>]*>(.*?)</a>(.*?)</a>',
        r'<a href="\1">\2\3</a>',
        html,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    if html != original:
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)
        links_count = len(re.findall(r'another-topic\.html', original))
        total_links_fixed += links_count
        fixed_articles += 1
        print(f"  T11: Fixed {os.path.basename(html_file)} ({links_count} placeholder links)")

print(f"\n  ✅ Batch fix: {fixed_articles} articles fixed, {total_links_fixed} placeholder links removed\n")

print("=" * 70)
print("  ALL CRITICAL FIXES APPLIED SUCCESSFULLY")
print("=" * 70)
