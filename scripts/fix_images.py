#!/usr/bin/env python3
"""
fix_images.py — Regenerate missing images for existing articles
===============================================================
Scans articles/ for HTML files, checks if images/ has the corresponding
cover and content images, and regenerates any that are missing.

Usage:
  python fix_images.py                    # Fix all articles
  python fix_images.py --slug my-article  # Fix a specific article
  python fix_images.py --dry-run          # Preview what would be fixed
"""

import os, sys, re, json, time, random, argparse, urllib.parse
from pathlib import Path

try:
    import requests
    from PIL import Image
    from io import BytesIO
except ImportError:
    print("[ERROR] Missing dependencies: pip install requests Pillow")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent.parent
ARTICLES_DIR = BASE_DIR / "articles"
IMAGES_DIR = BASE_DIR / "images"
ARTICLES_JSON = BASE_DIR / "articles.json"

# Pollinations config
POLLINATIONS_MODEL = "klein-large"
_keys = [os.environ.get(f"POLLINATIONS_API_KEY_{i}") for i in range(1, 6)]
POLLINATIONS_KEYS = [k for k in _keys if k and len(k) > 5]

# Fallback: Pollinations works without keys too (just slower)
if not POLLINATIONS_KEYS:
    POLLINATIONS_KEYS = [""]
    print("[INFO] No Pollinations API keys found, using keyless mode")


def download_image(prompt: str, width: int = 1200, height: int = 675) -> bytes:
    """Download image from Pollinations API."""
    safe_prompt = urllib.parse.quote(prompt[:500])
    seed = random.randint(0, 999999)

    for key_idx, api_key in enumerate(POLLINATIONS_KEYS, 1):
        try:
            url = f"https://gen.pollinations.ai/image/{safe_prompt}"
            params = {
                "width": width, "height": height, "seed": seed,
                "model": POLLINATIONS_MODEL, "nologo": "true", "enhance": "true"
            }
            headers = {"User-Agent": "Mozilla/5.0"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            print(f"  [DL] Pollinations key #{key_idx}...")
            resp = requests.get(url, params=params, headers=headers, timeout=120)

            if resp.status_code == 200 and len(resp.content) > 2048:
                print(f"  [OK] {len(resp.content) // 1024} KB")
                return resp.content
            else:
                print(f"  [FAIL] Status {resp.status_code}")
                if resp.status_code == 429:
                    time.sleep(5)
        except Exception as e:
            print(f"  [ERR] {str(e)[:60]}")

    return None


def save_webp(image_data: bytes, filepath: str) -> bool:
    """Convert and save image as optimized WebP."""
    try:
        img = Image.open(BytesIO(image_data))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail((1200, 1200))
        img.save(filepath, "WEBP", quality=85, optimize=True, method=6)
        size_kb = os.path.getsize(filepath) // 1024
        print(f"  [SAVED] {os.path.basename(filepath)} ({size_kb} KB)")
        return True
    except Exception as e:
        print(f"  [ERR] Save failed: {e}")
        return False


def extract_title_from_html(html_path: str) -> str:
    """Extract article title from HTML file."""
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read(5000)
        m = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL | re.IGNORECASE)
        if m:
            return re.sub(r'<[^>]+>', '', m.group(1)).strip()
        m = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
        if m:
            return m.group(1).strip().split("|")[0].strip()
    except:
        pass
    return ""


def extract_category_from_html(html_path: str) -> str:
    """Extract category from HTML meta or content."""
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read(5000)
        m = re.search(r'<meta\s+property="article:section"\s+content="([^"]+)"', content, re.IGNORECASE)
        if m:
            return m.group(1)
        m = re.search(r'class="[^"]*category[^"]*"[^>]*>([^<]+)', content, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    except:
        pass
    return "Education"


def scan_missing_images(target_slug: str = None) -> list:
    """Scan articles for missing images."""
    results = []

    if not ARTICLES_DIR.exists():
        print(f"[ERROR] Articles directory not found: {ARTICLES_DIR}")
        return results

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    img_files = set(f.name for f in IMAGES_DIR.iterdir() if f.is_file())

    html_files = sorted(ARTICLES_DIR.glob("*.html"))
    if target_slug:
        html_files = [f for f in html_files if f.stem == target_slug]

    for html_file in html_files:
        slug = html_file.stem
        title = extract_title_from_html(str(html_file))
        category = extract_category_from_html(str(html_file))

        # Check cover image
        has_cover = any(f.startswith(slug) and "cover" in f for f in img_files)
        # Check content images (expect 4: img1 to img4)
        content_imgs = [f for f in img_files if f.startswith(slug) and "-img" in f]
        missing_content = max(0, 4 - len(content_imgs))

        if not has_cover or missing_content > 0:
            results.append({
                "slug": slug,
                "title": title or slug,
                "category": category,
                "missing_cover": not has_cover,
                "existing_content_imgs": len(content_imgs),
                "missing_content_count": missing_content,
            })

    return results


def fix_article_images(article: dict, dry_run: bool = False) -> dict:
    """Generate missing images for a single article."""
    slug = article["slug"]
    title = article["title"]
    category = article["category"]
    generated = []
    failed = []

    print(f"\n{'=' * 60}")
    print(f"  FIXING: {title[:50]}")
    print(f"  Slug:   {slug}")
    print(f"  Cat:    {category}")
    print(f"{'=' * 60}")

    # ── Cover image ──
    if article["missing_cover"]:
        cover_prompt = (
            f"Educational children illustration about {title}, "
            f"category {category}, "
            f"vibrant colorful 3D Pixar style, high quality, "
            f"fun and engaging for kids, bright background, "
            f"educational theme, professional cover image"
        )
        if dry_run:
            print(f"  [DRY] Would generate cover: {slug}-cover-*.webp")
        else:
            seed = random.randint(1000000, 9999999)
            filename = f"{slug}-cover-{seed}.webp"
            data = download_image(cover_prompt)
            if data and save_webp(data, str(IMAGES_DIR / filename)):
                generated.append(filename)
            else:
                failed.append("cover")
            time.sleep(3)

    # ── Content images ──
    existing = article["existing_content_imgs"]
    for i in range(existing + 1, 5):  # Generate img1 to img4 as needed
        content_prompts = [
            f"Child learning {title}, hands-on activity, colorful classroom, 3D Pixar style",
            f"Happy kids doing {category} activities, educational game, vibrant illustration",
            f"Cute children exploring {title}, interactive learning, fun educational scene",
            f"Young students engaged in {category}, creative play, bright cheerful illustration",
        ]
        prompt = content_prompts[(i - 1) % len(content_prompts)]

        if dry_run:
            print(f"  [DRY] Would generate content img #{i}: {slug}-img{i}-*.webp")
        else:
            seed = random.randint(1000000, 9999999)
            filename = f"{slug}-img{i}-{seed}.webp"
            data = download_image(prompt)
            if data and save_webp(data, str(IMAGES_DIR / filename)):
                generated.append(filename)
            else:
                failed.append(f"img{i}")
            time.sleep(3)

    return {"slug": slug, "generated": generated, "failed": failed}


def update_article_html_images(slug: str, images: list):
    """Update article HTML to reference the new images."""
    html_path = ARTICLES_DIR / f"{slug}.html"
    if not html_path.exists():
        return

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    modified = False

    # Fix cover image in og:image
    cover_imgs = [img for img in images if "cover" in img]
    if cover_imgs:
        cover = cover_imgs[0]
        # Update og:image
        content, n = re.subn(
            r'(<meta\s+property="og:image"\s+content=")[^"]*(")',
            rf'\1/images/{cover}\2',
            content
        )
        if n > 0:
            modified = True

        # Update first/hero image
        content, n = re.subn(
            r'(class="[^"]*cover[^"]*"[^>]*src=")[^"]*(")',
            rf'\1/images/{cover}\2',
            content, count=1
        )
        if n > 0:
            modified = True

    if modified:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [HTML] Updated {html_path.name}")


def main():
    parser = argparse.ArgumentParser(description="Fix missing images for blog articles")
    parser.add_argument("--slug", help="Fix a specific article by slug")
    parser.add_argument("--dry-run", action="store_true", help="Preview without generating")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  FIX IMAGES — Regenerate Missing Article Images")
    print("=" * 60)
    print(f"  Articles dir: {ARTICLES_DIR}")
    print(f"  Images dir:   {IMAGES_DIR}")
    print(f"  Pollinations keys: {len(POLLINATIONS_KEYS)}")
    if args.dry_run:
        print("  MODE: DRY RUN (no images will be generated)")

    # Scan
    missing = scan_missing_images(args.slug)

    if not missing:
        print("\n  [OK] All articles have their images!")
        return

    print(f"\n  Found {len(missing)} articles with missing images:")
    for m in missing:
        parts = []
        if m["missing_cover"]:
            parts.append("COVER")
        if m["missing_content_count"] > 0:
            parts.append(f"{m['missing_content_count']} content imgs")
        print(f"    - {m['slug'][:50]}  [{', '.join(parts)}]")

    # Fix
    total_gen = 0
    total_fail = 0

    for article in missing:
        result = fix_article_images(article, args.dry_run)
        if not args.dry_run and result["generated"]:
            update_article_html_images(article["slug"], result["generated"])
        total_gen += len(result["generated"])
        total_fail += len(result["failed"])

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  Articles processed: {len(missing)}")
    print(f"  Images generated:   {total_gen}")
    print(f"  Failures:           {total_fail}")

    if not args.dry_run and total_gen > 0:
        print("\n  [!] Run 'python build_articles.py' to update articles.json")
        print("  [!] Then commit and push to deploy the new images")


if __name__ == "__main__":
    main()
