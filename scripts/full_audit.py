"""
FULL PIPELINE AUDIT — checks every post JSON and HTML article for:
1. H2 count (must be >= 6)
2. Keyword quality (flags single-word, generic stop words)
3. Duplicate images within articles 
4. Git merge conflict markers in HTML
5. Raw markdown/code artifacts in HTML
"""
import os, sys, json, glob, re
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
POSTS_DIR = os.path.join(PROJECT_ROOT, "posts")
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")

GENERIC_WORDS = {
    'the', 'their', 'just', 'what', 'first', 'this', 'that', 'with', 'from',
    'your', 'they', 'them', 'when', 'been', 'have', 'will', 'more', 'each',
    'also', 'about', 'into', 'like', 'make', 'some', 'very', 'than', 'even',
    'most', 'much', 'such', 'only', 'many', 'over', 'well', 'here', 'then',
    'right', 'look', 'every', 'good', 'give', 'keep', 'help', 'think',
    'number', 'brain', 'grid', 'puzzle', 'kids', 'child', 'things', 'start',
    'really', 'great', 'these', 'those', 'where', 'could', 'would', 'should',
    'sudoku', 'which', 'there', 'other', 'after', 'before', 'still', 'while'
}

print("=" * 80)
print("  FULL PIPELINE AUDIT")
print("=" * 80)

# ─── 1. AUDIT POST JSONs ──────────────────────────────────────────────────
post_files = sorted(glob.glob(os.path.join(POSTS_DIR, "*.json")))
print(f"\n  Found {len(post_files)} post JSONs in posts/\n")

issues = {
    "h2_deficient": [],
    "bad_keywords": [],
    "duplicate_images": [],
    "git_conflicts": [],
    "raw_code": []
}

for pf in post_files:
    slug = os.path.basename(pf).replace('.json', '')
    try:
        with open(pf, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [ERR] Cannot read {slug}: {e}")
        continue
    
    content = data.get('content', '')
    title = data.get('title', 'Unknown')
    
    # ── H2 count ──
    h2_count = len(re.findall(r'<h2', content, re.IGNORECASE))
    if h2_count < 6:
        issues["h2_deficient"].append((slug, title[:50], h2_count))
        print(f"  [H2 FAIL] {h2_count}/6 H2s — {title[:60]}")
    
    # ── Keywords quality ──
    keywords = data.get('keywords', [])
    bad_kw = [kw for kw in keywords if kw.lower().strip() in GENERIC_WORDS or (len(kw.split()) == 1 and len(kw) < 6)]
    if bad_kw:
        issues["bad_keywords"].append((slug, title[:50], bad_kw))
    
    # ── Duplicate images ──
    img_srcs = re.findall(r'src=["\']([^"\']+)["\']', content)
    img_basenames = [os.path.basename(s) for s in img_srcs]
    dups = [item for item, count in Counter(img_basenames).items() if count > 1]
    if dups:
        issues["duplicate_images"].append((slug, title[:50], dups))

# ─── 2. AUDIT HTML ARTICLES ───────────────────────────────────────────────
html_files = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html")))
print(f"\n  Found {len(html_files)} HTML articles in articles/\n")

for hf in html_files:
    slug = os.path.basename(hf).replace('.html', '')
    try:
        with open(hf, 'r', encoding='utf-8') as f:
            html = f.read()
    except Exception as e:
        continue
    
    # ── Git conflict markers ──
    conflicts = re.findall(r'(<{7}|={7}|>{7})', html)
    if conflicts:
        issues["git_conflicts"].append((slug, len(conflicts)))
        print(f"  [GIT CONFLICT] {len(conflicts)} markers — {slug}")
    
    # ── Raw markdown/code artifacts ──
    raw_code = re.findall(r'(```|<<<<<<|======|>>>>>>)', html)
    if raw_code:
        issues["raw_code"].append((slug, raw_code[:5]))
        print(f"  [RAW CODE] {slug}")

# ─── 3. SUMMARY REPORT ───────────────────────────────────────────────────
print("\n" + "=" * 80)
print("  AUDIT RESULTS SUMMARY")
print("=" * 80)

print(f"\n  Total post JSONs:     {len(post_files)}")
print(f"  Total HTML articles:  {len(html_files)}")

print(f"\n  --- H2 DEFICIENCY (< 6 H2s) ---")
if issues["h2_deficient"]:
    for slug, title, count in issues["h2_deficient"]:
        print(f"    [{count}/6] {title}")
else:
    print("    ALL PASS ✓")

print(f"\n  --- BAD KEYWORDS (single-word or generic) ---")
if issues["bad_keywords"]:
    for slug, title, bad in issues["bad_keywords"]:
        print(f"    {title}")
        print(f"      Bad: {', '.join(bad[:8])}")
else:
    print("    ALL PASS ✓")

print(f"\n  --- DUPLICATE IMAGES ---")
if issues["duplicate_images"]:
    for slug, title, dups in issues["duplicate_images"]:
        print(f"    {title}")
        print(f"      Dups: {', '.join(dups[:3])}")
else:
    print("    ALL PASS ✓")

print(f"\n  --- GIT CONFLICT MARKERS IN HTML ---")
if issues["git_conflicts"]:
    for slug, count in issues["git_conflicts"]:
        print(f"    {slug} ({count} markers)")
else:
    print("    ALL PASS ✓")

print(f"\n  --- RAW CODE/MARKDOWN IN HTML ---")
if issues["raw_code"]:
    for slug, codes in issues["raw_code"]:
        print(f"    {slug}")
else:
    print("    ALL PASS ✓")

# Save machine-readable report
report = {
    "total_posts": len(post_files),
    "total_html": len(html_files),
    "h2_deficient": [{"slug": s, "title": t, "h2_count": c} for s, t, c in issues["h2_deficient"]],
    "bad_keywords": [{"slug": s, "title": t, "bad_keywords": b} for s, t, b in issues["bad_keywords"]],
    "duplicate_images": [{"slug": s, "title": t, "duplicates": d} for s, t, d in issues["duplicate_images"]],
    "git_conflicts": [{"slug": s, "count": c} for s, c in issues["git_conflicts"]],
    "raw_code": [{"slug": s} for s, _ in issues["raw_code"]]
}

report_path = os.path.join(PROJECT_ROOT, "audit_report.json")
with open(report_path, 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)
print(f"\n  Report saved to: {report_path}")
print("=" * 80)
