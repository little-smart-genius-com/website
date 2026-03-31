"""Audit: Count articles, check March 9, compare sitemap vs articles.json"""
import json, os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1. Count local HTML article files
articles_dir = os.path.join(BASE, "articles")
html_files = [f for f in os.listdir(articles_dir) if f.endswith(".html")]
print(f"\n=== LOCAL ARTICLE FILES ===")
print(f"  HTML files in articles/: {len(html_files)}")

# 2. Count articles in articles.json
aj_path = os.path.join(BASE, "articles.json")
with open(aj_path, "r", encoding="utf-8") as f:
    data = json.load(f)
articles = data.get("articles", [])
print(f"\n=== ARTICLES.JSON INDEX ===")
print(f"  Total in articles.json: {len(articles)}")

# Check March 9 articles
march9 = [a for a in articles if "2026-03-09" in a.get("iso_date", "")]
print(f"  March 09 articles still in index: {len(march9)}")
for a in march9:
    print(f"    - {a['slug']}")

# 3. Check which articles.json entries have no corresponding HTML file
missing_html = []
for a in articles:
    slug = a.get("slug", "")
    html_path = os.path.join(articles_dir, f"{slug}.html")
    if not os.path.exists(html_path):
        missing_html.append(slug)

print(f"\n=== ORPHANED INDEX ENTRIES (in articles.json but no HTML file) ===")
print(f"  Count: {len(missing_html)}")
for s in missing_html:
    print(f"    - {s}")

# 4. Check HTML files with no articles.json entry
indexed_slugs = {a.get("slug", "") for a in articles}
orphan_html = [f.replace(".html", "") for f in html_files if f.replace(".html", "") not in indexed_slugs]
print(f"\n=== ORPHANED HTML FILES (HTML exists but not in articles.json) ===")
print(f"  Count: {len(orphan_html)}")
for s in orphan_html:
    print(f"    - {s}")

# 5. Sitemap analysis
sitemap_path = os.path.join(BASE, "sitemap.xml")
with open(sitemap_path, "r", encoding="utf-8") as f:
    sitemap = f.read()
sitemap_urls = re.findall(r"<loc>(.*?)</loc>", sitemap)
sitemap_article_urls = [u for u in sitemap_urls if "/articles/" in u]
print(f"\n=== SITEMAP ANALYSIS ===")
print(f"  Total URLs in sitemap: {len(sitemap_urls)}")
print(f"  Article URLs: {len(sitemap_article_urls)}")
print(f"  Static pages: {len(sitemap_urls) - len(sitemap_article_urls)}")

# Articles in index but NOT in sitemap
sitemap_slugs = set()
for u in sitemap_article_urls:
    m = re.search(r"/articles/(.+?)\.html", u)
    if m:
        sitemap_slugs.add(m.group(1))

missing_sitemap = [a["slug"] for a in articles if a["slug"] not in sitemap_slugs]
print(f"\n=== ARTICLES MISSING FROM SITEMAP ===")
print(f"  Count: {len(missing_sitemap)}")
if missing_sitemap:
    for s in missing_sitemap[:20]:
        print(f"    - {s}")
    if len(missing_sitemap) > 20:
        print(f"    ... and {len(missing_sitemap)-20} more")

# 6. Check favicon file exists
favicon_path = os.path.join(BASE, "favicon.ico")
print(f"\n=== FAVICON CHECK ===")
print(f"  favicon.ico exists: {os.path.exists(favicon_path)}")
if os.path.exists(favicon_path):
    size = os.path.getsize(favicon_path)
    print(f"  favicon.ico size: {size} bytes ({size//1024}KB)")
else:
    print(f"  !!! favicon.ico is MISSING - this is why the favicon doesn't work!")
    # Check for alternatives
    for name in ["favicon.png", "favicon.svg", "logo.png", "logo.ico"]:
        p = os.path.join(BASE, name)
        if os.path.exists(p):
            print(f"  Found alternative: {name} ({os.path.getsize(p)} bytes)")
    img_dir = os.path.join(BASE, "images")
    if os.path.isdir(img_dir):
        logos = [f for f in os.listdir(img_dir) if "logo" in f.lower() or "icon" in f.lower() or "favicon" in f.lower()]
        for l in logos:
            print(f"  Found in images/: {l}")

# 7. Check _post_process.py for related articles logic
pp_path = os.path.join(BASE, "scripts", "_post_process.py")
print(f"\n=== POST-PROCESSOR CHECK ===")
print(f"  _post_process.py exists: {os.path.exists(pp_path)}")

print("\n=== AUDIT COMPLETE ===\n")
