"""Rebuild articles.json and search_index.json from existing HTML files in articles/."""
import os, json, glob, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_DIR = os.path.join(ROOT, "articles")

articles = []
for f in sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html"))):
    bn = os.path.basename(f)
    if bn == "index.html":
        continue
    slug = bn.replace(".html", "")
    with open(f, "r", encoding="utf-8") as fh:
        content = fh.read()

    # Title
    m = re.search(r"<title>(.*?)</title>", content)
    title = m.group(1).split("|")[0].strip() if m else slug

    # Meta description
    m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']', content)
    desc = m.group(1) if m else ""

    # Category
    m = re.search(r'<meta\s+property=["\']article:section["\']\s+content=["\']([^"\']*)["\']', content)
    cat = m.group(1) if m else ""

    # Date
    m = re.search(r'<meta\s+property=["\']article:published_time["\']\s+content=["\']([^"\']*)["\']', content)
    date = m.group(1)[:10] if m else "2025-01-01"

    # Author
    m = re.search(r'<meta\s+name=["\']author["\']\s+content=["\']([^"\']*)["\']', content)
    author = m.group(1) if m else "Little Smart Genius Team"

    # Reading time
    text_len = len(re.sub(r"<[^>]+>", "", content))
    reading_time = max(5, text_len // 1200)

    articles.append({
        "slug": slug,
        "title": title,
        "excerpt": desc[:200],
        "category": cat,
        "date": date,
        "author": author,
        "reading_time": reading_time,
        "url": f"/articles/{bn}",
    })

with open(os.path.join(ROOT, "articles.json"), "w", encoding="utf-8") as f:
    json.dump(articles, f, ensure_ascii=False, indent=2)
print(f"articles.json rebuilt: {len(articles)} articles")

search = [
    {"slug": a["slug"], "title": a["title"], "excerpt": a["excerpt"],
     "category": a["category"], "url": a["url"]}
    for a in articles
]
with open(os.path.join(ROOT, "search_index.json"), "w", encoding="utf-8") as f:
    json.dump(search, f, ensure_ascii=False, indent=2)
print(f"search_index.json rebuilt: {len(search)} articles")
