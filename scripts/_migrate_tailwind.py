"""
MIGRATE TAILWIND CDN → PRODUCTION CSS
Replaces <script src="https://cdn.tailwindcss.com"></script> and inline
tailwind.config blocks with a single <link> to compiled CSS across all HTML pages.
"""
import os, re, glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Patterns to remove
CDN_PATTERNS = [
    # The CDN script tag (with or without closing slash, whitespace variants)
    r'<script\s+src="https://cdn\.tailwindcss\.com"\s*>\s*</script>\s*\n?',
    # The inline tailwind.config block (multi-line)
    r'\s*<script>\s*\n?\s*tailwind\.config\s*=\s*\{[^}]*\{[^}]*\}[^}]*\}\s*\n?\s*</script>\s*\n?',
]

# The replacement <link> tag
CSS_LINK = '<link rel="stylesheet" href="/styles/tailwind.min.css">'

def get_depth_prefix(filepath):
    """Compute relative path prefix for files in subdirectories."""
    rel = os.path.relpath(filepath, PROJECT_ROOT).replace('\\', '/')
    depth = rel.count('/')
    if depth == 0:
        return '/'
    return '/' 

def migrate_file(filepath):
    """Replace Tailwind CDN with production CSS link in a single HTML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Check if already migrated
    if 'tailwind.min.css' in content:
        return 'SKIP (already migrated)'
    
    # Check if CDN is present
    if 'cdn.tailwindcss.com' not in content:
        return 'SKIP (no CDN found)'
    
    # Remove CDN script tag
    for pattern in CDN_PATTERNS:
        content = re.sub(pattern, '', content)
    
    # Insert CSS link after viewport meta or before </head>
    if CSS_LINK not in content:
        if '<meta' in content and 'viewport' in content:
            # Insert after the viewport meta tag
            content = re.sub(
                r'(<meta[^>]*viewport[^>]*/>)\s*\n?',
                r'\1\n    ' + CSS_LINK + '\n',
                content,
                count=1
            )
        elif '</head>' in content:
            content = content.replace('</head>', f'    {CSS_LINK}\n</head>')
    
    if content == original:
        return 'SKIP (no changes)'
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return 'OK'

def main():
    print("=" * 60)
    print("  TAILWIND CDN → PRODUCTION CSS MIGRATION")
    print("=" * 60)
    
    # Collect all HTML files
    html_files = []
    html_files += glob.glob(os.path.join(PROJECT_ROOT, '*.html'))
    html_files += glob.glob(os.path.join(PROJECT_ROOT, 'articles', '*.html'))
    html_files += glob.glob(os.path.join(PROJECT_ROOT, 'blog', '*.html'))
    
    print(f"\n  Found {len(html_files)} HTML files")
    
    stats = {'OK': 0, 'SKIP (already migrated)': 0, 'SKIP (no CDN found)': 0, 'SKIP (no changes)': 0}
    
    for filepath in sorted(html_files):
        result = migrate_file(filepath)
        rel = os.path.relpath(filepath, PROJECT_ROOT)
        stats[result] = stats.get(result, 0) + 1
        if result == 'OK':
            print(f"  ✓ {rel}")
    
    print(f"\n  Results:")
    for k, v in stats.items():
        if v > 0:
            print(f"    {k}: {v}")
    
    print(f"\n  DONE!")

if __name__ == '__main__':
    main()
