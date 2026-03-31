"""Inject PNG favicon fallback into all HTML files that have the ICO-only favicon."""
import os
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ico_tag = '<link rel="icon" type="image/x-icon" href="/favicon.ico">'
png_tag = '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">'

count = 0
for root, dirs, files in os.walk(PROJECT_ROOT):
    # Skip hidden dirs and node_modules
    dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules' and d != 'data']
    for f in files:
        if not f.endswith('.html'):
            continue
        fp = os.path.join(root, f)
        with open(fp, 'r', encoding='utf-8') as fh:
            content = fh.read()
        
        if ico_tag in content and png_tag not in content:
            content = content.replace(ico_tag, f'{ico_tag}\n    {png_tag}')
            with open(fp, 'w', encoding='utf-8') as fh:
                fh.write(content)
            count += 1

print(f"Injected PNG favicon into {count} HTML files")
