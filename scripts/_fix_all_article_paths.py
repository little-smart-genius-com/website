"""Mass fix ALL remaining ../ paths in article HTML files.
Converts ../images/ → /images/, ../products.html → /products.html, etc."""
import os
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")

html_files = sorted([
    os.path.join(ARTICLES_DIR, f)
    for f in os.listdir(ARTICLES_DIR) if f.endswith(".html")
])

print(f"Scanning {len(html_files)} article files for ../ paths...")

fixed = 0
total_replacements = 0

for fp in html_files:
    with open(fp, "r", encoding="utf-8") as f:
        content = f.read()
    
    original = content
    
    # Fix href="../something" → href="/something"
    content = re.sub(r'href="\.\./([^"]*)"', r'href="/\1"', content)
    # Fix src="../something" → src="/something" 
    content = re.sub(r'src="\.\./([^"]*)"', r'src="/\1"', content)
    # Fix srcset="../something" entries
    content = re.sub(r'srcset="\.\./([^"]*)"', r'srcset="/\1"', content)
    # Fix inside srcset with multiple entries: ../path 480w, ../path 1200w
    content = re.sub(r'srcset="\.\./', r'srcset="/', content)
    # Catch any remaining ../ inside attribute values
    content = re.sub(r'"\.\./([^"]*)"', r'"/\1"', content)
    
    if content != original:
        replacements = len(re.findall(r'\.\./(?!\.)', original)) - len(re.findall(r'\.\./(?!\.)', content))
        total_replacements += replacements
        with open(fp, "w", encoding="utf-8") as f:
            f.write(content)
        fixed += 1

print(f"Fixed {fixed} files with {total_replacements} total replacements")

# Verify
remaining = 0
for fp in html_files:
    with open(fp, "r", encoding="utf-8") as f:
        content = f.read()
    count = len(re.findall(r'(href|src|srcset)="\.\\./', content))
    if count > 0:
        remaining += count
        print(f"  STILL HAS ../ : {os.path.basename(fp)} ({count} occurrences)")

print(f"\nRemaining ../ in href/src/srcset: {remaining}")
