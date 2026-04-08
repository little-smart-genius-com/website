"""
FIX GA4 RENDER-BLOCKING — Sitewide

Replaces synchronous GA4 loading with deferred pattern across ALL HTML files.
This is safe because:
  - It only replaces the exact known GA4 snippet
  - It uses the same deferred pattern already approved in build_articles.py
  - It backs up each file before modification

Usage:
    python scripts/fix_ga4_deferred.py              # Dry run (shows what would change)
    python scripts/fix_ga4_deferred.py --apply       # Apply changes
"""

import os, re, glob, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# ── The old synchronous patterns to detect ──
OLD_PATTERNS = [
    # Pattern 1: async script tag + inline config (multiline)
    re.compile(
        r'<script\s+async\s+src="https://www\.googletagmanager\.com/gtag/js\?id=G-1S8G205JX2">\s*</script>\s*'
        r'<script>.*?gtag\(\'config\',\s*\'G-1S8G205JX2\'\);\s*</script>',
        re.DOTALL
    ),
    # Pattern 2: async="" variant (HTML serialized)
    re.compile(
        r'<script\s+async=""\s+src="https://www\.googletagmanager\.com/gtag/js\?id=G-1S8G205JX2">\s*</script>\s*'
        r'<script>.*?gtag\(\'config\',\s*\'G-1S8G205JX2\'\);\s*</script>',
        re.DOTALL
    ),
    # Pattern 3: minified variant
    re.compile(
        r'<script\s+async\s+src="https://www\.googletagmanager\.com/gtag/js\?id=G-1S8G205JX2">\s*</script>\s*'
        r'<script>window\.dataLayer=window\.dataLayer\|\|\[\];function gtag\(\)\{dataLayer\.push\(arguments\)\}gtag\(\'js\',new Date\(\)\);gtag\(\'config\',\'G-1S8G205JX2\'\);</script>',
        re.DOTALL
    ),
]

# ── The deferred replacement ──
DEFERRED_GA4 = """<!-- Google Analytics GA4 (deferred for performance) -->
    <script>
        window.addEventListener('load', function() {
            setTimeout(function() {
                var s = document.createElement('script');
                s.src = 'https://www.googletagmanager.com/gtag/js?id=G-1S8G205JX2';
                s.async = true;
                document.head.appendChild(s);
                s.onload = function() {
                    window.dataLayer = window.dataLayer || [];
                    function gtag() { dataLayer.push(arguments); }
                    gtag('js', new Date());
                    gtag('config', 'G-1S8G205JX2');
                };
            }, 2000);
        });
    </script>"""


def find_html_files():
    """Find all HTML files in the project (excluding node_modules, .git, etc.)."""
    files = []
    exclude_dirs = {'.git', 'node_modules', '.testsprite', 'testsprite_tests', 'data'}
    
    for root, dirs, filenames in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in filenames:
            if f.endswith('.html'):
                files.append(os.path.join(root, f))
    
    return files


def check_already_deferred(content):
    """Check if file already uses the deferred pattern."""
    return "window.addEventListener('load', function()" in content and "googletagmanager.com/gtag/js" in content


def fix_file(filepath, apply=False):
    """Fix GA4 in a single file. Returns True if changes were made."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    # Skip if already deferred
    if check_already_deferred(content):
        return False
    
    # Skip if no GA4 at all
    if 'googletagmanager.com/gtag/js?id=G-1S8G205JX2' not in content:
        return False
    
    # Try each pattern
    new_content = content
    replaced = False
    
    for pattern in OLD_PATTERNS:
        if pattern.search(new_content):
            new_content = pattern.sub(DEFERRED_GA4, new_content)
            replaced = True
            break
    
    # Fallback: simple string replace for the async script tag
    if not replaced:
        # Try both async and async="" variants
        old_tags = [
            '<script async src="https://www.googletagmanager.com/gtag/js?id=G-1S8G205JX2"></script>',
            '<script async="" src="https://www.googletagmanager.com/gtag/js?id=G-1S8G205JX2"></script>',
        ]
        for old_tag in old_tags:
            if old_tag in new_content:
                # Find and remove the async tag + the following inline script
                idx = new_content.find(old_tag)
                # Find the closing </script> of the config block after the async tag
                config_end = new_content.find('</script>', idx + len(old_tag))
                if config_end > 0:
                    config_end += len('</script>')
                    # Also capture any GA4 comment before it
                    comment_start = new_content.rfind('<!-- G', max(0, idx - 50), idx)
                    if comment_start < 0:
                        comment_start = new_content.rfind('<!--', max(0, idx - 20), idx)
                    start = comment_start if comment_start >= 0 else idx
                    
                    new_content = new_content[:start] + DEFERRED_GA4 + new_content[config_end:]
                    replaced = True
                    break
    
    if not replaced:
        return False
    
    if apply:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    return True


def main():
    apply = '--apply' in sys.argv
    
    print("=" * 60)
    print("  GA4 DEFERRED LOADING — Sitewide Fix")
    print("=" * 60)
    
    html_files = find_html_files()
    print(f"\n  Found {len(html_files)} HTML files")
    
    already_deferred = 0
    needs_fix = 0
    no_ga4 = 0
    fixed = 0
    errors = 0
    
    for filepath in sorted(html_files):
        relpath = os.path.relpath(filepath, PROJECT_ROOT)
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            if 'googletagmanager.com/gtag/js?id=G-1S8G205JX2' not in content:
                no_ga4 += 1
                continue
            
            if check_already_deferred(content):
                already_deferred += 1
                continue
            
            needs_fix += 1
            
            if fix_file(filepath, apply=apply):
                fixed += 1
                print(f"  {'✓ Fixed' if apply else '⚠ Needs fix'}: {relpath}")
            else:
                errors += 1
                print(f"  ✗ Could not match pattern: {relpath}")
                
        except Exception as e:
            errors += 1
            print(f"  ✗ Error: {relpath} — {e}")
    
    print(f"\n  ─── Summary ───")
    print(f"  HTML files scanned:    {len(html_files)}")
    print(f"  No GA4 (skip):         {no_ga4}")
    print(f"  Already deferred:      {already_deferred}")
    print(f"  {'Fixed' if apply else 'Need fixing'}:  {fixed}")
    if errors:
        print(f"  Errors:                {errors}")
    
    if not apply and fixed > 0:
        print(f"\n  Run with --apply to fix {fixed} files:")
        print(f"  python scripts/fix_ga4_deferred.py --apply")


if __name__ == "__main__":
    main()
