"""
FIX: Inject tailwind.min.css link into pages that are missing it.
Targets pages where the CDN was removed but the CSS link wasn't inserted.
"""
import os, re, glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

CSS_LINK = '<link rel="stylesheet" href="/styles/tailwind.min.css">'

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already has the CSS link
    if 'tailwind.min.css' in content:
        return False
    
    # Skip if no <head> tag (not a real HTML page)
    if '</head>' not in content:
        return False
    
    # Insert before </head>
    content = content.replace('</head>', f'    {CSS_LINK}\n</head>')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return True

def main():
    html_files = []
    html_files += glob.glob(os.path.join(PROJECT_ROOT, '*.html'))
    html_files += glob.glob(os.path.join(PROJECT_ROOT, 'articles', '*.html'))
    html_files += glob.glob(os.path.join(PROJECT_ROOT, 'blog', '*.html'))
    
    fixed = 0
    for fp in sorted(html_files):
        if fix_file(fp):
            fixed += 1
    
    print(f"Injected CSS link into {fixed} pages")

if __name__ == '__main__':
    main()
