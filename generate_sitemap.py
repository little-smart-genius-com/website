#!/usr/bin/env python3
"""Generate a complete sitemap.xml for littlesmartgenius.com"""

import json
import os
import glob
from datetime import datetime

DOMAIN = "https://littlesmartgenius.com"
OUTPUT = "sitemap.xml"
TODAY = datetime.now().strftime("%Y-%m-%d")

def build_sitemap():
    urls = []
    
    # ── 1. Main pages (priority 1.0 - 0.8) ──
    main_pages = [
        ("/", "daily", "1.0"),
        ("/products.html", "weekly", "0.9"),
        ("/freebies.html", "weekly", "0.9"),
    ]
    for path, freq, prio in main_pages:
        urls.append({"loc": f"{DOMAIN}{path}", "changefreq": freq, "priority": prio})
    
    # ── 2. Blog index + pagination (priority 0.8) ──
    urls.append({"loc": f"{DOMAIN}/blog/", "changefreq": "daily", "priority": "0.8"})
    
    blog_pages = sorted(glob.glob("blog/page-*.html"))
    for p in blog_pages:
        name = os.path.basename(p)
        urls.append({"loc": f"{DOMAIN}/blog/{name}", "changefreq": "weekly", "priority": "0.7"})
    
    # ── 3. Blog category pages (priority 0.7) ──
    category_pages = []
    for f in sorted(glob.glob("blog/*.html")):
        name = os.path.basename(f)
        if name in ("index.html",) or name.startswith("page-"):
            continue
        category_pages.append(name)
    
    for name in category_pages:
        urls.append({"loc": f"{DOMAIN}/blog/{name}", "changefreq": "weekly", "priority": "0.7"})
    
    # ── 4. All articles (priority 0.6) ──
    try:
        with open("articles.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        articles = data.get("articles", data) if isinstance(data, dict) else data
        
        for article in articles:
            slug = article.get("slug", "")
            date_pub = article.get("iso_date", article.get("date_published", TODAY))
            if isinstance(date_pub, str) and "T" in date_pub:
                date_pub = date_pub.split("T")[0]
            
            urls.append({
                "loc": f"{DOMAIN}/articles/{slug}.html",
                "lastmod": date_pub,
                "changefreq": "monthly",
                "priority": "0.6"
            })
    except FileNotFoundError:
        # Fallback: scan articles directory
        for f in sorted(glob.glob("articles/*.html")):
            name = os.path.basename(f)
            urls.append({
                "loc": f"{DOMAIN}/articles/{name}",
                "changefreq": "monthly",
                "priority": "0.6"
            })
    
    # ── 5. Legal / info pages (priority 0.4) ──
    legal_pages = [
        "/about.html", "/contact.html", "/terms.html", 
        "/privacy.html", "/education.html", "/legal.html"
    ]
    for path in legal_pages:
        if os.path.exists(path.lstrip("/")):
            urls.append({"loc": f"{DOMAIN}{path}", "changefreq": "monthly", "priority": "0.4"})
    
    # ── Build XML ──
    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_parts.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    for url in urls:
        xml_parts.append("  <url>")
        xml_parts.append(f"    <loc>{url['loc']}</loc>")
        if "lastmod" in url:
            xml_parts.append(f"    <lastmod>{url['lastmod']}</lastmod>")
        xml_parts.append(f"    <changefreq>{url['changefreq']}</changefreq>")
        xml_parts.append(f"    <priority>{url['priority']}</priority>")
        xml_parts.append("  </url>")
    
    xml_parts.append("</urlset>")
    
    sitemap_content = "\n".join(xml_parts) + "\n"
    
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(sitemap_content)
    
    print(f"✅ Sitemap generated: {OUTPUT}")
    print(f"   Total URLs: {len(urls)}")
    print(f"   - Main pages: {len(main_pages)}")
    print(f"   - Blog pages: {1 + len(blog_pages)}")
    print(f"   - Categories: {len(category_pages)}")
    print(f"   - Articles: {len([u for u in urls if '/articles/' in u['loc']])}")
    print(f"   - Legal pages: {len([u for u in urls if u['priority'] == '0.4'])}")

if __name__ == "__main__":
    build_sitemap()
