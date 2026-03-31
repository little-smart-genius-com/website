"""Generate a complete sitemap.xml with all articles, static pages, and blog category pages."""
import os
import re
import json
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
SITE_URL = "https://littlesmartgenius.com"

# 1. Load all articles from articles.json
with open(os.path.join(PROJECT_ROOT, "articles.json"), "r", encoding="utf-8") as f:
    data = json.load(f)
articles = data.get("articles", [])
print(f"Loaded {len(articles)} articles from articles.json")

# 2. Discover blog category pages
blog_dir = os.path.join(PROJECT_ROOT, "blog")
blog_pages = []
if os.path.isdir(blog_dir):
    for f in sorted(os.listdir(blog_dir)):
        if f.endswith(".html"):
            blog_pages.append(f"blog/{f}")
print(f"Found {len(blog_pages)} blog pages in blog/")

# 3. Build sitemap entries
entries = []

# Static pages
static_pages = [
    ('index.html', '1.0', 'daily'),
    ('blog/', '0.9', 'daily'),
    ('products.html', '0.8', 'weekly'),
    ('freebies.html', '0.8', 'weekly'),
    ('about.html', '0.7', 'monthly'),
    ('contact.html', '0.7', 'monthly'),
    ('education.html', '0.6', 'monthly'),
    ('terms.html', '0.5', 'yearly'),
    ('privacy.html', '0.5', 'yearly'),
    ('legal.html', '0.5', 'yearly'),
]

for page, priority, changefreq in static_pages:
    path = os.path.join(PROJECT_ROOT, page.replace("/", os.sep))
    if page.endswith("/"):
        path = os.path.join(PROJECT_ROOT, page.rstrip("/"), "index.html")
    if os.path.exists(path):
        entries.append(f"""  <url>
    <loc>{SITE_URL}/{page}</loc>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>""")

# Blog category and pagination pages (exclude index.html which is already covered by blog/)
for bp in blog_pages:
    if bp == "blog/index.html":
        continue  # Already covered by blog/
    # Category pages get higher priority, pagination pages get lower
    if "page-" in bp:
        priority = "0.6"
    else:
        priority = "0.7"
    entries.append(f"""  <url>
    <loc>{SITE_URL}/{bp}</loc>
    <changefreq>weekly</changefreq>
    <priority>{priority}</priority>
  </url>""")

# All articles
for article in articles:
    url = article.get("url", "")
    iso_date = article.get("iso_date", datetime.now().isoformat())
    entries.append(f"""  <url>
    <loc>{SITE_URL}/{url}</loc>
    <lastmod>{iso_date.split('T')[0]}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")

# 4. Write sitemap.xml
sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(entries)}
</urlset>"""

sitemap_path = os.path.join(PROJECT_ROOT, "sitemap.xml")
with open(sitemap_path, "w", encoding="utf-8") as f:
    f.write(sitemap_xml)

print(f"\n=== SITEMAP GENERATED ===")
print(f"  Static pages: {len(static_pages)}")
print(f"  Blog pages: {len([bp for bp in blog_pages if bp != 'blog/index.html'])}")
print(f"  Articles: {len(articles)}")
print(f"  TOTAL URLs: {len(entries)}")
print(f"  Written to: {sitemap_path}")
