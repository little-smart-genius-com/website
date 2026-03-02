"""
fix_placeholder_refs.py
Finds all placeholder.webp references in article HTML files
and replaces them with the actual img5 v3 image that exists on disk.
Also fixes related article thumbnails that point to placeholder.webp.
"""
import os, re, glob

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
THUMBS_DIR = os.path.join(IMAGES_DIR, "thumbs")


def find_img5_for_slug(slug):
    """Find the img5 v3 file on disk for a given article slug."""
    matches = glob.glob(os.path.join(IMAGES_DIR, f"{slug}-img5-*-v3.webp"))
    if matches:
        matches.sort(key=os.path.getmtime, reverse=True)
        return os.path.basename(matches[0])
    # Fallback: any img5
    matches = glob.glob(os.path.join(IMAGES_DIR, f"{slug}-img5-*.webp"))
    if matches:
        matches.sort(key=os.path.getmtime, reverse=True)
        return os.path.basename(matches[0])
    return None


def main():
    articles = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html")))

    print("=" * 65)
    print("  FIX PLACEHOLDER.WEBP REFERENCES")
    print("=" * 65)

    total_fixed = 0
    total_articles_fixed = 0

    for article_path in articles:
        slug = os.path.basename(article_path).replace(".html", "")

        with open(article_path, "r", encoding="utf-8") as f:
            html = f.read()

        if "placeholder.webp" not in html:
            continue

        count = html.count("placeholder.webp")
        img5 = find_img5_for_slug(slug)

        if not img5:
            print(f"  [WARN] {slug[:50]} — no img5 found on disk! ({count} refs)")
            continue

        # Replace inline figure references: src='../images/placeholder.webp'
        html = html.replace(
            "src='../images/placeholder.webp'",
            f"src='../images/{img5}'"
        )

        # Replace src="..." variants
        html = html.replace(
            'src="../images/placeholder.webp"',
            f'src="../images/{img5}"'
        )

        # Replace srcset references
        html = html.replace(
            'src="../images/thumbs/placeholder.webp"',
            f'src="../images/thumbs/{img5}"'
        )
        html = html.replace(
            "../images/thumbs/placeholder.webp 480w, ../images/placeholder.webp 1200w",
            f"../images/thumbs/{img5} 480w, ../images/{img5} 1200w"
        )

        # Catch any remaining
        html = html.replace("../images/placeholder.webp", f"../images/{img5}")

        with open(article_path, "w", encoding="utf-8") as f:
            f.write(html)

        remaining = html.count("placeholder.webp")
        fixed = count - remaining
        total_fixed += fixed
        total_articles_fixed += 1
        print(f"  FIXED: {slug[:50]} ({fixed} refs replaced -> {img5})")
        if remaining > 0:
            print(f"         WARNING: {remaining} placeholder refs remain!")

    print(f"\n{'=' * 65}")
    print(f"  DONE: {total_fixed} placeholder refs fixed across {total_articles_fixed} articles")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    main()
