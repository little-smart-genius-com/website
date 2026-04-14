#!/usr/bin/env python3
"""Generate a complete sitemap.xml for littlesmartgenius.com"""

import json
import os
import glob
from datetime import datetime

DOMAIN = "https://littlesmartgenius.com"
OUTPUT = "sitemap.xml"
TODAY = datetime.now().strftime("%Y-%m-%d")

def _get_file_lastmod(filepath):
    """Get the last modification date of a file as YYYY-MM-DD string."""
    try:
        if os.path.exists(filepath):
            mtime = os.path.getmtime(filepath)
            return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
    except OSError:
        pass
    return TODAY


def build_sitemap():
    urls = []
    
    # ── 1. Main pages ──
    main_pages = [
        "/",
        "/products.html",
        "/freebies.html",
    ]
    for path in main_pages:
        filepath = "index.html" if path == "/" else path.lstrip("/")
        urls.append({"loc": f"{DOMAIN}{path}", "lastmod": _get_file_lastmod(filepath)})
    
    # ── 2. Blog index (skip pagination pages — they waste crawl budget) ──
    urls.append({"loc": f"{DOMAIN}/blog/", "lastmod": _get_file_lastmod("blog/index.html")})
    
    # ── 3. Blog category pages ──
    category_pages = []
    for f in sorted(glob.glob("blog/*.html")):
        name = os.path.basename(f)
        if name in ("index.html",) or name.startswith("page-"):
            continue
        category_pages.append(name)
    
    for name in category_pages:
        urls.append({"loc": f"{DOMAIN}/blog/{name}", "lastmod": _get_file_lastmod(f"blog/{name}")})
    
    # Load canonical map to filter out non-pillar articles
    canonical_map = {}
    try:
        with open("canonical_map.json", "r", encoding="utf-8") as f:
            canonical_map = json.load(f)
    except FileNotFoundError:
        pass

    # 🌟 4. All articles 🌟
    try:
        with open("articles.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        articles = data.get("articles", data) if isinstance(data, dict) else data
        
        for article in articles:
            slug = article.get("slug", "")
            
            # Skip non-pillar articles mapped in canonical_map
            if slug in canonical_map and canonical_map[slug].get("pillar_slug") != slug:
                continue

            date_pub = article.get("iso_date", article.get("date_published", TODAY))
            if isinstance(date_pub, str) and "T" in date_pub:
                date_pub = date_pub.split("T")[0]
            
            urls.append({
                "loc": f"{DOMAIN}/articles/{slug}.html",
                "lastmod": date_pub,
            })
    except FileNotFoundError:
        # Fallback: scan articles directory
        for f in sorted(glob.glob("articles/*.html")):
            name = os.path.basename(f)
            slug = name.replace(".html", "")
            
            # Skip non-pillar articles
            if slug in canonical_map and canonical_map[slug].get("pillar_slug") != slug:
                continue

            urls.append({
                "loc": f"{DOMAIN}/articles/{name}",
                "lastmod": _get_file_lastmod(f"articles/{name}"),
            })
    
    # ── 5. Author pages ──
    if os.path.exists("authors"):
        authors_index = "authors/index.html"
        if os.path.exists(authors_index):
            urls.append({"loc": f"{DOMAIN}/authors/", "lastmod": _get_file_lastmod(authors_index)})
        for f in sorted(glob.glob("authors/*.html")):
            name = os.path.basename(f)
            if name == "index.html":
                continue
            urls.append({"loc": f"{DOMAIN}/authors/{name}", "lastmod": _get_file_lastmod(f"authors/{name}")})
    
    # ── 6. Legal / info pages ──
    legal_pages = [
        "/about.html", "/contact.html", "/terms.html", 
        "/privacy.html", "/education.html", "/legal.html"
    ]
    for path in legal_pages:
        filepath = path.lstrip("/")
        if os.path.exists(filepath):
            urls.append({"loc": f"{DOMAIN}{path}", "lastmod": _get_file_lastmod(filepath)})
    
    # ── Build XML (clean: no deprecated changefreq/priority) ──
    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_parts.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    for url in urls:
        xml_parts.append("  <url>")
        xml_parts.append(f"    <loc>{url['loc']}</loc>")
        if "lastmod" in url:
            xml_parts.append(f"    <lastmod>{url['lastmod']}</lastmod>")
        xml_parts.append("  </url>")
    
    xml_parts.append("</urlset>")
    
    sitemap_content = "\n".join(xml_parts) + "\n"
    
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(sitemap_content)
    
    print(f"[OK] Sitemap generated: {OUTPUT}")
    print(f"   Total URLs: {len(urls)}")
    print(f"   - Main pages: {len(main_pages)}")
    print(f"   - Blog index: 1")
    print(f"   - Categories: {len(category_pages)}")
    print(f"   - Articles: {len([u for u in urls if '/articles/' in u['loc']])}")
    print(f"   - Authors: {len([u for u in urls if '/authors/' in u['loc']])}")
    print(f"   - Legal pages: {len([u for u in urls if any(p in u['loc'] for p in legal_pages)])}")

if __name__ == "__main__":
    build_sitemap()
