"""
Comprehensive Blog Integrity Verification
Checks: articles, images, blog pages, indexes, sitemap, and asset directories.
"""
import os, json, re, glob

ROOT = '.'
IMAGES_DIR = 'images'
ARTICLES_DIR = 'articles'

print("=" * 70)
print("  COMPREHENSIVE BLOG VERIFICATION")
print("=" * 70)

errors = []
warnings = []

# 1. articles.json integrity
print("\n[1] Checking articles.json...")
with open('articles.json', 'r', encoding='utf-8') as f:
    articles_data = json.load(f)
articles = articles_data.get('articles', [])
print(f"    Articles indexed: {len(articles)}")
if len(articles) != 35:
    errors.append(f"Expected 35 articles, found {len(articles)}")

# 2. HTML files match index
print("\n[2] Checking HTML article files...")
html_files = glob.glob(os.path.join(ARTICLES_DIR, '*.html'))
html_slugs = set(os.path.splitext(os.path.basename(f))[0] for f in html_files)
json_slugs = set(a['slug'] for a in articles)

missing_html = json_slugs - html_slugs
orphan_html = html_slugs - json_slugs
print(f"    HTML files: {len(html_files)}")
if missing_html:
    errors.append(f"Articles in index but missing HTML: {missing_html}")
if orphan_html:
    warnings.append(f"HTML files not in index (orphans): {orphan_html}")

# 3. Image references in HTML all resolve
print("\n[3] Checking image references in HTML...")
broken_images = []
total_img_refs = 0
for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    slug = os.path.splitext(os.path.basename(html_file))[0]
    img_refs = re.findall(r'src=["\'](?:\.\./)?(?:/)?images/([^"\'?#]+)', content)
    for img in set(img_refs):
        total_img_refs += 1
        img_path = os.path.join(IMAGES_DIR, img)
        if not os.path.exists(img_path):
            broken_images.append(f"{slug}: images/{img}")

print(f"    Total image references: {total_img_refs}")
print(f"    Broken image references: {len(broken_images)}")
if broken_images:
    errors.append(f"Broken image refs: {broken_images[:5]}")

# 4. Blog listing pages
print("\n[4] Checking blog listing pages...")
blog_pages = ['blog.html', 'blog-2.html', 'blog-3.html', 'blog-4.html']
for page in blog_pages:
    if os.path.exists(page):
        size = os.path.getsize(page)
        print(f"    ✅ {page} ({size // 1024}KB)")
    else:
        errors.append(f"Missing blog page: {page}")
        print(f"    ❌ {page} MISSING")

# 5. Category pages
print("\n[5] Checking category pillar pages...")
category_pages = glob.glob('blog-*.html')
category_pages = [p for p in category_pages if p not in blog_pages]
print(f"    Category pages: {len(category_pages)}")
for page in sorted(category_pages):
    size = os.path.getsize(page)
    print(f"    ✅ {page} ({size // 1024}KB)")

# 6. search_index.json
print("\n[6] Checking search_index.json...")
if os.path.exists('search_index.json'):
    with open('search_index.json', 'r', encoding='utf-8') as f:
        search_data = json.load(f)
    print(f"    Entries: {len(search_data)}")
    if len(search_data) != len(articles):
        warnings.append(f"search_index has {len(search_data)} entries vs {len(articles)} articles")
else:
    errors.append("search_index.json missing")

# 7. sitemap.xml
print("\n[7] Checking sitemap.xml...")
if os.path.exists('sitemap.xml'):
    with open('sitemap.xml', 'r', encoding='utf-8') as f:
        sitemap = f.read()
    url_count = sitemap.count('<url>')
    print(f"    URLs in sitemap: {url_count}")
else:
    errors.append("sitemap.xml missing")

# 8. Asset directories
print("\n[8] Checking asset directories...")
asset_dirs = {
    'images/thumbs': 'Article thumbnails',
    'images/og': 'Open Graph images',
    'images/products-thumbs': 'Product thumbnails',
    'images/banners': 'Banner images',
}
for dir_path, label in asset_dirs.items():
    if os.path.exists(dir_path):
        count = len(os.listdir(dir_path))
        print(f"    ✅ {label} ({dir_path}): {count} files")
    else:
        errors.append(f"Missing directory: {dir_path}")
        print(f"    ❌ {label} ({dir_path}): MISSING")

# 9. Thumbnails match covers
print("\n[9] Checking cover-thumbnail pairs...")
thumbs_dir = os.path.join(IMAGES_DIR, 'thumbs')
if os.path.exists(thumbs_dir):
    thumb_files = set(os.listdir(thumbs_dir))
    covers_without_thumbs = 0
    for f in os.listdir(IMAGES_DIR):
        if '-cover-' in f and f.endswith('.webp'):
            if f not in thumb_files:
                covers_without_thumbs += 1
    print(f"    Covers without thumbnails: {covers_without_thumbs}")
    if covers_without_thumbs > 0:
        warnings.append(f"{covers_without_thumbs} cover images lack thumbnails")

# FINAL REPORT
print("\n" + "=" * 70)
print("  FINAL REPORT")
print("=" * 70)
if errors:
    print(f"\n  ❌ ERRORS ({len(errors)}):")
    for e in errors:
        print(f"    - {e}")
if warnings:
    print(f"\n  ⚠️ WARNINGS ({len(warnings)}):")
    for w in warnings:
        print(f"    - {w}")
if not errors and not warnings:
    print("\n  ✅ ALL CHECKS PASSED — Blog is fully intact!")
elif not errors:
    print(f"\n  ✅ No critical errors. {len(warnings)} minor warnings.")
else:
    print(f"\n  🚨 {len(errors)} errors need attention.")
print("=" * 70)
