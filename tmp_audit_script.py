import os
import json
import re
import glob

PROJECT_ROOT = r"c:\Users\Omar\Desktop\little-smart-genius-site\Nouveau dossier\online\Little_Smart_Genius"
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive_posts")
POSTS_DIR = os.path.join(PROJECT_ROOT, "posts")

report = []

def log(msg):
    report.append(msg)
    print(msg)

log("# Final Project Audit Report")
log("Checking consistency across the auto-blogging system...\n")

# 1. Directory Checks
log("## 1. Directory Structure & Status")
html_files = glob.glob(os.path.join(ARTICLES_DIR, "*.html"))
archive_files = glob.glob(os.path.join(ARCHIVE_DIR, "*.json"))
post_files = glob.glob(os.path.join(POSTS_DIR, "*.json"))

log(f"- **Articles (HTML)**: {len(html_files)}")
log(f"- **Archived Posts (JSON)**: {len(archive_files)}")
log(f"- **Pending Posts (JSON)**: {len(post_files)} (Should ideally be 0 if build is complete)")

# 2. Index Checks
log("\n## 2. Search & Article Indexes")
try:
    with open(os.path.join(PROJECT_ROOT, "search_index.json"), "r", encoding="utf-8") as f:
        search_data = json.load(f)
        log(f"- `search_index.json`: Contains {search_data.get('total_articles', 0)} articles")
except Exception as e:
    log(f"- `search_index.json` check failed: {e}")

try:
    with open(os.path.join(PROJECT_ROOT, "articles.json"), "r", encoding="utf-8") as f:
        articles_data = json.load(f)
        log(f"- `articles.json`: Contains {len(articles_data.get('articles', []))} articles")
except Exception as e:
    log(f"- `articles.json` check failed: {e}")

# 3. used_topics.json Consistency
log("\n## 3. Topic Pool Consistency (used_topics.json)")
try:
    with open(os.path.join(DATA_DIR, "used_topics.json"), "r", encoding="utf-8") as f:
        used_topics = json.load(f)
        log(f"- Published Keywords: {len(used_topics.get('keyword', []))}")
        log(f"- Published Products: {len(used_topics.get('product', []))}")
        log(f"- Published Freebies: {len(used_topics.get('freebie', []))}")
except Exception as e:
    log(f"- `used_topics.json` check failed: {e}")

# 4. Article Health Check (Nav, TPT, Images)
log("\n## 4. Article HTML Health Check")
tpt_duplicates = []
missing_nav = []
placeholder_images = []
malformed_h2 = []

tpt_marker = "<!-- ═══ TPT PRODUCT RECOMMENDATION & SCHEMA ═══ -->"

for html_file in html_files:
    basename = os.path.basename(html_file)
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Check TPT Dups
    if content.count(tpt_marker) > 1:
        tpt_duplicates.append(basename)
        
    # Check Nav
    if 'id="prevArticleNav"' not in content or 'id="nextArticleNav"' not in content:
        missing_nav.append(basename)
        
    # Check placeholders
    if "placeholder.webp" in content:
        placeholder_images.append(basename)
        
    # Check H2
    h2_open = content.count("<h2")
    h2_close = content.count("</h2>")
    if h2_open != h2_close:
        malformed_h2.append(basename)

log(f"- Articles with duplicate TPT products: {len(tpt_duplicates)}")
if tpt_duplicates: log(f"  -> {tpt_duplicates}")

log(f"- Articles missing Next/Prev Navigation: {len(missing_nav)}")
if missing_nav: log(f"  -> {missing_nav}")

log(f"- Articles containing placeholder images: {len(placeholder_images)}")
if placeholder_images: log(f"  -> {placeholder_images}")

log(f"- Articles with malformed H2 tags (mismatched open/close): {len(malformed_h2)}")
if malformed_h2: log(f"  -> {malformed_h2}")

if not tpt_duplicates and not missing_nav and not placeholder_images and not malformed_h2:
    log("\n- **SUCCESS**: All core features are correctly implemented and healthy.")
else:
    log("\n- **NEEDS REVIEW**: Some files flag anomalies.")

# Save to file
output_path = os.path.join(PROJECT_ROOT, "final_audit.md")
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report))
print(f"\nReport written to {output_path}")

