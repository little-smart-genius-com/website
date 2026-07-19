#!/usr/bin/env python3
"""Sitemap Validation Script — SEO Skill Audit"""
import json, os, glob, re

# Load canonical map
with open('canonical_map.json', 'r', encoding='utf-8') as f:
    canonical_map = json.load(f)

# Load articles.json
with open('articles.json', 'r', encoding='utf-8') as f:
    articles_data = json.load(f)
articles = articles_data.get('articles', articles_data)

# Parse sitemap URLs
with open('sitemap.xml', 'r', encoding='utf-8') as f:
    sitemap = f.read()
sitemap_urls = re.findall(r'<loc>([^<]+)</loc>', sitemap)

# 1. Count URL types
article_urls = [u for u in sitemap_urls if '/articles/' in u]
blog_urls = [u for u in sitemap_urls if '/blog/' in u]
author_urls = [u for u in sitemap_urls if '/authors/' in u]
main_urls = [u for u in sitemap_urls if u not in article_urls + blog_urls + author_urls]

print('=== SITEMAP VALIDATION REPORT ===')
print('Total URLs: {}'.format(len(sitemap_urls)))
print('  Articles: {}'.format(len(article_urls)))
print('  Blog/Category: {}'.format(len(blog_urls)))
print('  Authors: {}'.format(len(author_urls)))
print('  Main/Legal: {}'.format(len(main_urls)))

# 2. Check for protocol limit
status = "PASS" if len(sitemap_urls) < 50000 else "FAIL"
print('\n[CHECK] URL Count < 50,000: {}'.format(status))

# 3. HTTPS only
http_urls = [u for u in sitemap_urls if u.startswith('http://')]
status = "PASS" if not http_urls else "FAIL - {} HTTP URLs".format(len(http_urls))
print('[CHECK] HTTPS Only: {}'.format(status))

# 4. No deprecated tags
has_priority = '<priority>' in sitemap
has_changefreq = '<changefreq>' in sitemap
print('[CHECK] No <priority> tag: {}'.format("PASS" if not has_priority else "FAIL"))
print('[CHECK] No <changefreq> tag: {}'.format("PASS" if not has_changefreq else "FAIL"))

# 5. Check lastmod dates are NOT all identical
lastmods = re.findall(r'<lastmod>([^<]+)</lastmod>', sitemap)
unique_lastmods = set(lastmods)
status = "PASS ({} unique dates)".format(len(unique_lastmods)) if len(unique_lastmods) > 1 else "FAIL - all identical"
print('[CHECK] Varied lastmod dates: {}'.format(status))

# 6. Check no canonical-redirected articles in sitemap
canonical_in_sitemap = []
for url in article_urls:
    slug = url.split('/articles/')[-1].replace('.html', '')
    if slug in canonical_map and canonical_map[slug].get('pillar_slug') != slug:
        canonical_in_sitemap.append(slug)
status = "PASS" if not canonical_in_sitemap else "FAIL - {} found".format(len(canonical_in_sitemap))
print('[CHECK] No non-canonical URLs: {}'.format(status))
if canonical_in_sitemap:
    for s in canonical_in_sitemap[:5]:
        print('  LEAKED: {}'.format(s))

# 7. Cross-reference: articles on disk but NOT in sitemap (excluding canonical)
on_disk = set()
for f in glob.glob('articles/*.html'):
    name = os.path.basename(f).replace('.html', '')
    on_disk.add(name)

in_sitemap = set()
for u in article_urls:
    slug = u.split('/articles/')[-1].replace('.html', '')
    in_sitemap.add(slug)

missing_from_sitemap = []
for slug in on_disk - in_sitemap:
    if slug not in canonical_map:
        missing_from_sitemap.append(slug)

status = "PASS" if not missing_from_sitemap else "WARN - {} missing".format(len(missing_from_sitemap))
print('[CHECK] All pillar articles in sitemap: {}'.format(status))
if missing_from_sitemap:
    for s in sorted(missing_from_sitemap)[:10]:
        print('  MISSING: {}'.format(s))

# 8. Duplicate URLs
seen = set()
dupes = set()
for u in sitemap_urls:
    if u in seen:
        dupes.add(u)
    seen.add(u)
status = "PASS" if not dupes else "FAIL - {} duplicates".format(len(dupes))
print('[CHECK] No duplicate URLs: {}'.format(status))

# 9. Verify file existence for article URLs
missing_files = []
for url in article_urls:
    slug = url.split('/articles/')[-1]
    filepath = os.path.join('articles', slug)
    if not os.path.exists(filepath):
        missing_files.append(slug)
status = "PASS" if not missing_files else "FAIL - {} missing files".format(len(missing_files))
print('[CHECK] All article files exist: {}'.format(status))
if missing_files:
    for mf in missing_files[:5]:
        print('  NO FILE: {}'.format(mf))

# 10. Blog page existence
missing_blog = []
for url in blog_urls:
    path = url.replace('https://littlesmartgenius.com/', '')
    if path.endswith('/'):
        path += 'index.html'
    if not os.path.exists(path):
        missing_blog.append(path)
status = "PASS" if not missing_blog else "FAIL - {} missing".format(len(missing_blog))
print('[CHECK] All blog pages exist: {}'.format(status))
if missing_blog:
    for mb in missing_blog[:5]:
        print('  NO FILE: {}'.format(mb))

# 11. Check robots.txt reference
with open('robots.txt', 'r', encoding='utf-8') as f:
    robots = f.read()
has_sitemap_ref = 'Sitemap: https://littlesmartgenius.com/sitemap.xml' in robots
print('[CHECK] Sitemap in robots.txt: {}'.format("PASS" if has_sitemap_ref else "FAIL"))

# 12. Valid XML structure
valid_xml = sitemap.strip().startswith('<?xml') and '<urlset' in sitemap and '</urlset>' in sitemap
print('[CHECK] Valid XML structure: {}'.format("PASS" if valid_xml else "FAIL"))

# 13. Check for noindex in articles that are in sitemap
noindex_in_sitemap = []
for url in article_urls:
    slug = url.split('/articles/')[-1]
    filepath = os.path.join('articles', slug)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            head = f.read(3000)
        if 'noindex' in head.lower():
            noindex_in_sitemap.append(slug)
status = "PASS" if not noindex_in_sitemap else "FAIL - {} noindexed".format(len(noindex_in_sitemap))
print('[CHECK] No noindexed URLs in sitemap: {}'.format(status))
if noindex_in_sitemap:
    for ni in noindex_in_sitemap[:5]:
        print('  NOINDEX: {}'.format(ni))

# Summary
print('\n=== SUMMARY ===')
total_on_disk = len(on_disk)
canonical_count = len(canonical_map)
print('Articles on disk: {}'.format(total_on_disk))
print('Articles in sitemap: {}'.format(len(article_urls)))
print('Canonical redirects (correctly excluded): {}'.format(canonical_count))
print('Expected article count: {} (disk) - {} (canonical) = {}'.format(
    total_on_disk, canonical_count, total_on_disk - canonical_count))
delta = len(article_urls) - (total_on_disk - canonical_count)
if delta == 0:
    print('MATCH: Sitemap article count matches expected!')
else:
    print('DELTA: {} (sitemap has {} {} than expected)'.format(
        abs(delta), abs(delta), 'more' if delta > 0 else 'fewer'))

print('\n=== END VALIDATION ===')
