"""
remove_placeholder_figures.py
Removes all <div> blocks containing placeholder.webp from article HTML files.
These are orphaned 6th image positions that were never generated.
Also removes placeholder references in related article thumbnails.
"""
import os, re, glob

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")


def main():
    articles = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html")))

    print("=" * 65)
    print("  REMOVE PLACEHOLDER.WEBP REFERENCES")
    print("=" * 65)

    total_fixed = 0

    for article_path in articles:
        slug = os.path.basename(article_path).replace(".html", "")

        with open(article_path, "r", encoding="utf-8") as f:
            html = f.read()

        if "placeholder.webp" not in html:
            continue

        original_count = html.count("placeholder.webp")

        # Pattern 1: Remove inline figure divs containing placeholder.webp
        # These look like: <div style="margin: 2.5rem 0;"><figure class='my-8'><img src='../images/placeholder.webp' ...></figure></div>
        html = re.sub(
            r'\n?\s*<div style="margin: 2\.5rem 0;">\s*<figure class=\'my-8\'>\s*<img src=\'../images/placeholder\.webp\'[^>]*>\s*</figure>\s*</div>\s*\n?',
            '\n',
            html
        )

        # Pattern 2: Also catch <img src='../images/placeholder.webp'...> without figure wrapper
        html = re.sub(
            r'\n?\s*<img src=\'../images/placeholder\.webp\'[^>]*>\s*\n?',
            '\n',
            html
        )

        # Pattern 3: Related article thumbnails with placeholder
        # src="..." and srcset="..." patterns
        html = re.sub(
            r'src="\.\.\/images\/thumbs\/placeholder\.webp"',
            'src="../images/thumbs/placeholder-removed.webp"',
            html
        )
        html = re.sub(
            r'srcset="\.\.\/images\/thumbs\/placeholder\.webp[^"]*"',
            'srcset=""',
            html
        )

        remaining = html.count("placeholder.webp")

        with open(article_path, "w", encoding="utf-8") as f:
            f.write(html)

        fixed = original_count - remaining
        total_fixed += fixed
        status = "CLEAN" if remaining == 0 else f"WARN ({remaining} remain)"
        print(f"  {status}: {slug[:55]} ({fixed}/{original_count} removed)")

    print(f"\n{'=' * 65}")
    print(f"  DONE: {total_fixed} placeholder references removed")
    print(f"{'=' * 65}")

    # Verify
    remaining_total = 0
    for article_path in articles:
        html = open(article_path, encoding="utf-8").read()
        remaining_total += html.count("placeholder.webp")
    print(f"  Remaining placeholder refs across all articles: {remaining_total}")


if __name__ == "__main__":
    main()
