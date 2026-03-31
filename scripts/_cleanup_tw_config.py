"""
CLEANUP: Remove leftover inline tailwind.config script blocks
These blocks are dead code now that the CDN is removed.
"""
import os, re, glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Pattern to match the inline config script block (multi-line, various whitespace)
CONFIG_PATTERNS = [
    # Pattern 1: standard multi-line config block
    r'\s*<script>\s*\n\s*tailwind\.config\s*=\s*\{[^<]*?\}\s*\n\s*</script>\s*\n?',
    # Pattern 2: single-line compact
    r'\s*<script>\s*tailwind\.config\s*=\s*\{[^<]*?\}\s*</script>\s*\n?',
]

def clean_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'tailwind.config' not in content:
        return False
    
    original = content
    for pattern in CONFIG_PATTERNS:
        content = re.sub(pattern, '\n', content, flags=re.DOTALL)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    html_files = []
    html_files += glob.glob(os.path.join(PROJECT_ROOT, '*.html'))
    html_files += glob.glob(os.path.join(PROJECT_ROOT, 'articles', '*.html'))
    html_files += glob.glob(os.path.join(PROJECT_ROOT, 'blog', '*.html'))
    
    cleaned = 0
    for fp in sorted(html_files):
        if clean_file(fp):
            cleaned += 1
    
    print(f"Cleaned {cleaned} files of leftover tailwind.config blocks")

if __name__ == '__main__':
    main()
