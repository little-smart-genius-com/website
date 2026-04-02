"""
MEDIUM HTML BUILDER — Convert Markdown abstracts to importable HTML pages
Creates clean HTML pages in /medium/ that Medium's "Import Story" can scrape.

Each page includes:
- Clean semantic HTML (article tag, proper headings)
- Canonical tag → original article (prevents duplicate content)
- noindex meta (keeps Google focused on the original article)
- Backlinks to blog, freebies, products
- Medium-friendly formatting

Usage:
  python build_medium_pages.py              # Build all from outputs/medium/*.md
  python build_medium_pages.py --slug SLUG  # Build one specific page
  python build_medium_pages.py --list       # List generated pages

(c) 2026 Little Smart Genius
"""

import os
import re
import glob
import json
import argparse
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

MEDIUM_MD_DIR = os.path.join(PROJECT_ROOT, "outputs", "medium")
MEDIUM_HTML_DIR = os.path.join(PROJECT_ROOT, "medium")
SITE_BASE = "https://littlesmartgenius.com"


# ─── MARKDOWN → HTML CONVERTER (lightweight, no dependencies) ───────

def md_to_html(md_text: str) -> str:
    """Convert simple Markdown to clean HTML."""
    html = md_text

    # Remove horizontal rules
    html = re.sub(r'^---+\s*$', '', html, flags=re.MULTILINE)

    # Headers
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

    # Italic
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

    # Links
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', html)

    # Tables → convert to simple list (Medium doesn't support tables well)
    # Match table rows like "| content | link |"
    table_rows = re.findall(r'^\| (.+?) \| (.+?) \|$', html, re.MULTILINE)
    if table_rows:
        # Remove table header and separator
        html = re.sub(r'^\| Resource.*\|$', '', html, flags=re.MULTILINE)
        html = re.sub(r'^\|[-|]+\|$', '', html, flags=re.MULTILINE)
        # Convert data rows to list items
        for content, link in table_rows:
            if '---' in content or 'Resource' in content:
                continue
            row_html = f'<li>{content.strip()} — {link.strip()}</li>'
            html = re.sub(
                re.escape(f'| {content} | {link} |'),
                row_html,
                html
            )
        # Wrap list items in <ul>
        html = re.sub(r'((?:<li>.*?</li>\s*)+)', r'<ul>\1</ul>', html, flags=re.DOTALL)

    # Paragraphs — wrap remaining text lines
    lines = html.split('\n')
    result = []
    for line in lines:
        line = line.strip()
        if not line:
            result.append('')
        elif line.startswith('<h') or line.startswith('<ul') or line.startswith('<li') or line.startswith('</'):
            result.append(line)
        elif line.startswith('<p'):
            result.append(line)
        else:
            result.append(f'<p>{line}</p>')
    
    html = '\n'.join(result)

    # Clean up empty paragraphs
    html = re.sub(r'<p>\s*</p>', '', html)
    html = re.sub(r'\n{3,}', '\n\n', html)

    return html.strip()


# ─── HTML TEMPLATE ──────────────────────────────────────────────────

def build_html_page(title: str, author: str, body_html: str,
                    article_url: str, slug: str) -> str:
    """Build a clean, Medium-importable HTML page."""
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="A summary of '{title}' from Little Smart Genius — expert educational resources for children aged 3-10.">
    <meta name="robots" content="noindex, follow">
    <link rel="canonical" href="{article_url}">

    <!-- Open Graph -->
    <meta property="og:title" content="{title}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{SITE_BASE}/medium/{slug}.html">
    <meta property="article:author" content="{author}">

    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Georgia', 'Times New Roman', serif;
            max-width: 720px;
            margin: 0 auto;
            padding: 40px 20px;
            color: #1a1a1a;
            line-height: 1.8;
            background: #fff;
        }}
        h1 {{
            font-size: 2rem;
            margin-bottom: 8px;
            line-height: 1.3;
            color: #1a1a1a;
        }}
        h2 {{
            font-size: 1.4rem;
            margin: 32px 0 12px;
            color: #1a1a1a;
        }}
        .byline {{
            color: #757575;
            font-size: 0.95rem;
            margin-bottom: 24px;
            font-style: italic;
        }}
        p {{
            margin-bottom: 16px;
            font-size: 1.1rem;
        }}
        a {{
            color: #1a8917;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        ul {{
            margin: 16px 0;
            padding-left: 24px;
        }}
        li {{
            margin-bottom: 8px;
            font-size: 1.05rem;
        }}
        .cta-box {{
            background: #f7f7f7;
            border-left: 4px solid #1a8917;
            padding: 20px 24px;
            margin: 32px 0;
            border-radius: 4px;
        }}
        .cta-box a {{
            font-weight: bold;
        }}
        .footer-note {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e6e6e6;
            color: #757575;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <article>
        {body_html}
    </article>
    <div class="footer-note">
        <p><em>Little Smart Genius creates printable educational resources for children aged 3–10. All resources are crafted by experienced educators.</em></p>
        <p><em>Originally published on <a href="{SITE_BASE}">littlesmartgenius.com</a></em></p>
    </div>
</body>
</html>"""


# ─── PARSE MARKDOWN FILE ────────────────────────────────────────────

def parse_medium_md(md_path: str) -> dict:
    """Extract title, author, and body from a Medium markdown file."""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract title (first # heading)
    title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "Untitled"

    # Extract author from byline
    author_match = re.search(r'^\*By (.+?) ·', content, re.MULTILINE)
    author = author_match.group(1).strip() if author_match else "Little Smart Genius"

    # Extract slug from filename
    slug = os.path.splitext(os.path.basename(md_path))[0]

    # Build article URL
    article_url = f"{SITE_BASE}/articles/{slug}.html"

    # Get body (everything after the byline)
    body = content
    # Remove the title line
    body = re.sub(r'^# .+$', '', body, count=1, flags=re.MULTILINE)
    # Remove the byline
    body = re.sub(r'^\*By .+\*$', '', body, count=1, flags=re.MULTILINE)

    return {
        "title": title,
        "author": author,
        "slug": slug,
        "article_url": article_url,
        "body_md": body.strip()
    }


# ─── BUILD SINGLE PAGE ──────────────────────────────────────────────

def build_page(md_path: str) -> str:
    """Convert a single Markdown abstract to an HTML page."""
    data = parse_medium_md(md_path)

    body_html = md_to_html(data['body_md'])

    html = build_html_page(
        title=data['title'],
        author=data['author'],
        body_html=body_html,
        article_url=data['article_url'],
        slug=data['slug']
    )

    os.makedirs(MEDIUM_HTML_DIR, exist_ok=True)
    output_path = os.path.join(MEDIUM_HTML_DIR, f"{data['slug']}.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return output_path


# ─── CLI ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Build HTML pages from Medium abstracts for Import Story",
    )
    parser.add_argument("--slug", metavar="SLUG", help="Build a specific page")
    parser.add_argument("--list", action="store_true", help="List generated pages")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  MEDIUM HTML PAGE BUILDER")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if args.list:
        pages = glob.glob(os.path.join(MEDIUM_HTML_DIR, "*.html"))
        print(f"\n  Generated pages: {len(pages)}")
        for p in sorted(pages):
            slug = os.path.splitext(os.path.basename(p))[0]
            url = f"{SITE_BASE}/medium/{slug}.html"
            print(f"  ✅ {url}")
        return

    md_files = []
    if args.slug:
        md_path = os.path.join(MEDIUM_MD_DIR, f"{args.slug}.md")
        if os.path.exists(md_path):
            md_files = [md_path]
        else:
            print(f"\n  [ERROR] Not found: {md_path}")
            return
    else:
        md_files = glob.glob(os.path.join(MEDIUM_MD_DIR, "*.md"))
        # Exclude the tracker file
        md_files = [f for f in md_files if not os.path.basename(f).startswith('_')]

    print(f"\n  Markdown files found: {len(md_files)}")

    results = []
    for md_path in sorted(md_files):
        slug = os.path.splitext(os.path.basename(md_path))[0]
        try:
            output = build_page(md_path)
            url = f"{SITE_BASE}/medium/{slug}.html"
            print(f"  ✅ {slug} → {url}")
            results.append(url)
        except Exception as e:
            print(f"  ❌ {slug}: {str(e)[:60]}")

    print(f"\n{'='*60}")
    print(f"  COMPLETE: {len(results)}/{len(md_files)} HTML pages built")
    print(f"  Output: {MEDIUM_HTML_DIR}")
    print(f"\n  After deploying, use these URLs in Medium's 'Import Story':")
    print(f"  Example: {SITE_BASE}/medium/<slug>.html")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
