"""Inject search_index.json data inline into all blog HTML pages."""
import os
import json
import glob
import re

# Resolve project root (parent of scripts/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Load search index
search_index_path = os.path.join(PROJECT_ROOT, 'search_index.json')
with open(search_index_path, 'r', encoding='utf-8') as f:
    index = json.load(f)

# Create the inline script tag
inline_data = json.dumps(index, ensure_ascii=False)
script_tag = '<script>window.__SEARCH_INDEX__=' + inline_data + ';</script>\n    <script src="blog-search.js" defer></script>'

# Process all blog pages
old_tag = '<script src="blog-search.js" defer></script>'

blog_files = [os.path.join(PROJECT_ROOT, 'blog.html')] + sorted(glob.glob(os.path.join(PROJECT_ROOT, 'blog-[0-9]*.html')))
for blog_file in blog_files:
    if not os.path.exists(blog_file):
        continue
    with open(blog_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Clean up any previous injection first
    if 'window.__SEARCH_INDEX__=' in content:
        # Remove old inline data
        content = re.sub(
            r'<script>window\.__SEARCH_INDEX__=.*?;</script>\s*\n\s*',
            '',
            content,
            flags=re.DOTALL
        )
    
    if old_tag in content:
        content = content.replace(old_tag, script_tag)
        with open(blog_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'[OK] {os.path.basename(blog_file)} updated with inline search data')
    else:
        print(f'[SKIP] {os.path.basename(blog_file)} - script tag not found')

print(f'\nIndex size: {len(inline_data)} chars ({len(index["articles"])} articles)')
