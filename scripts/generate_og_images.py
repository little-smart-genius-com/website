#!/usr/bin/env python3
"""
generate_og_images.py — Premium OpenGraph Image Generator V2
============================================================
Generates stunning 1200×630 branded OpenGraph images for all articles.

Design:
  - Deep dark gradient background (navy → dark indigo)
  - Brand orange accents (#F48C06)
  - Inter font (auto-downloaded, cross-platform, works on Linux CI)
  - Category badge + title + excerpt + branding

Cross-platform: no Windows-only fonts. Automatically downloads Inter Bold/Regular
from Google Fonts static CDN and caches in scripts/fonts/.

Usage:
  python scripts/generate_og_images.py              # All articles
  python scripts/generate_og_images.py --slug slug  # One article
  python scripts/generate_og_images.py --force      # Re-generate all

Output: images/og/<slug>.jpg (1200×630, quality=92)
"""

import os
import sys
import json
import math
import textwrap
import argparse
import urllib.request
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("[ERROR] Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

# ─────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
BASE_DIR     = SCRIPT_DIR.parent
FONTS_DIR    = SCRIPT_DIR / "fonts"
INDEX_PATH   = BASE_DIR / "search_index.json"
OUTPUT_DIR   = BASE_DIR / "images" / "og"

FONTS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────
# INTER FONT — Auto-download from Google Fonts static CDN
# ─────────────────────────────────────────────────────────
# Inter font CDN URLs (jsDelivr mirrors the rsms/inter GitHub repo reliably)
_CDN = "https://cdn.jsdelivr.net/gh/rsms/inter@main/docs/font-files"
FONT_URLS = {
    "bold":     ("inter-bold.ttf",     f"{_CDN}/Inter-Bold.ttf"),
    "regular":  ("inter-regular.ttf",  f"{_CDN}/Inter-Regular.ttf"),
    "semibold": ("inter-semibold.ttf", f"{_CDN}/Inter-SemiBold.ttf"),
}

def _download_font(key: str) -> Path | None:
    filename, url = FONT_URLS[key]
    dest = FONTS_DIR / filename
    if dest.exists():
        return dest
    print(f"  [FONT] Downloading {filename}...")
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"  [FONT] Saved {filename} ({dest.stat().st_size // 1024} KB)")
        return dest
    except Exception as e:
        print(f"  [FONT] Download failed for {filename}: {e}")
        return None


def _load_font(key: str, size: int) -> ImageFont.FreeTypeFont:
    path = _download_font(key)
    if path:
        try:
            return ImageFont.truetype(str(path), size)
        except Exception:
            pass
    return ImageFont.load_default()


# ─────────────────────────────────────────────────────────
# DESIGN CONSTANTS
# ─────────────────────────────────────────────────────────
W, H  = 1200, 630
BRAND = "#F48C06"        # orange
DARK1 = (10,  14,  39)   # #0A0E27 deep navy
DARK2 = (20,  16,  60)   # #14103C dark indigo
ACCENT_DARK = (30, 25, 70)  # slightly lighter indigo
WHITE      = (255, 255, 255)
OFF_WHITE  = (240, 240, 255)
LIGHT_GRAY = (160, 165, 200)
ORANGE     = (244, 140,   6)
ORANGE_DIM = (180, 102,   4)

CATEGORY_COLORS = {
    "math":             (99,  102, 241),
    "critical thinking":(139, 92,  246),
    "language arts":    (20,  184, 166),
    "visual skills":    (59,  130, 246),
    "fine motor skills":(236, 72,  153),
    "creative arts":    (168, 85,  247),
    "problem solving":  (234, 179, 8),
    "montessori":       (34,  197, 94),
    "coloring":         (251, 113, 133),
    "education":        (244, 140, 6),
}

def _cat_color(category: str) -> tuple:
    key = category.lower()
    for k, c in CATEGORY_COLORS.items():
        if k in key:
            return c
    return ORANGE


# ─────────────────────────────────────────────────────────
# GRADIENT BACKGROUND
# ─────────────────────────────────────────────────────────
def _draw_gradient(img: Image.Image):
    """Premium dark multi-stop radial + linear gradient."""
    draw = ImageDraw.Draw(img)

    # Base: linear top→bottom diagonal
    for y in range(H):
        t = y / H
        r = int(DARK1[0] + (DARK2[0] - DARK1[0]) * t)
        g = int(DARK1[1] + (DARK2[1] - DARK1[1]) * t)
        b = int(DARK1[2] + (DARK2[2] - DARK1[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Radial glow top-left (orange)
    glow = Image.new("RGBA", (600, 600), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(glow)
    for r in range(290, 0, -1):
        alpha = int(55 * (1 - r / 290) ** 2.5)
        gd.ellipse([290-r, 290-r, 290+r, 290+r], fill=(244, 140, 6, alpha))
    img.paste(glow, (-220, -200), glow)

    # Radial glow bottom-right (indigo/purple)
    glow2 = Image.new("RGBA", (700, 700), (0, 0, 0, 0))
    gd2   = ImageDraw.Draw(glow2)
    for r in range(340, 0, -1):
        alpha = int(60 * (1 - r / 340) ** 2.2)
        gd2.ellipse([340-r, 340-r, 340+r, 340+r], fill=(120, 60, 220, alpha))
    img.paste(glow2, (700, 300), glow2)


# ─────────────────────────────────────────────────────────
# DECORATIVE ELEMENTS
# ─────────────────────────────────────────────────────────
def _draw_decorations(img: Image.Image, cat_color: tuple):
    draw = ImageDraw.Draw(img, "RGBA")

    # Top-right decorative arc ring
    draw.ellipse([W-180, -90, W+90, 180],
                 outline=(*cat_color, 35), width=2)
    draw.ellipse([W-130, -50, W+60, 150],
                 outline=(*ORANGE, 20), width=1)

    # Bottom-left small circles cluster
    for cx, cy, cr, a in [(50, H-50, 30, 25), (90, H-30, 18, 18), (30, H-90, 12, 15)]:
        draw.ellipse([cx-cr, cy-cr, cx+cr, cy+cr],
                     fill=(*cat_color, a))

    # Thin separating line (branded)
    draw.line([(60, 120), (W-60, 120)], fill=(*ORANGE, 40), width=1)
    draw.line([(60, H-70), (W-60, H-70)], fill=(*ORANGE, 30), width=1)

    # Grid dots pattern (top right corner)
    for gx in range(W-160, W-20, 18):
        for gy in range(20, 110, 18):
            draw.ellipse([gx-2, gy-2, gx+2, gy+2],
                         fill=(*WHITE, 18))


# ─────────────────────────────────────────────────────────
# GLASSMORPHISM CARD
# ─────────────────────────────────────────────────────────
def _draw_glass_card(img: Image.Image, x1, y1, x2, y2, radius=20, opacity=30):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rounded_rectangle([x1, y1, x2, y2], radius=radius,
                         fill=(255, 255, 255, opacity))
    img.paste(overlay, (0, 0), overlay)

    # Subtle border
    border = Image.new("RGBA", img.size, (0, 0, 0, 0))
    db = ImageDraw.Draw(border)
    db.rounded_rectangle([x1, y1, x2, y2], radius=radius,
                          outline=(255, 255, 255, 40), width=1)
    img.paste(border, (0, 0), border)


# ─────────────────────────────────────────────────────────
# CATEGORY BADGE
# ─────────────────────────────────────────────────────────
def _draw_badge(draw: ImageDraw.Draw, text: str, cat_color: tuple,
                font_sm, x=60, y=145):
    text_upper = text.upper()
    try:
        tw = draw.textlength(text_upper, font=font_sm)
    except AttributeError:
        tw = len(text_upper) * 11
    pad = 18
    bw = int(tw + pad * 2)
    bh = 34
    # Badge background
    overlay = Image.new("RGBA", (bw + 4, bh + 4), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle([2, 2, bw, bh], radius=17, fill=(*cat_color, 220))

    # We'll draw it later directly on draw
    draw.rounded_rectangle([x, y, x + bw, y + bh], radius=17,
                            fill=(*cat_color, 255))
    draw.text((x + pad, y + 6), text_upper, fill=WHITE, font=font_sm)
    return y + bh + 22   # returns next y position


# ─────────────────────────────────────────────────────────
# TITLE (multi-line, large, bold)
# ─────────────────────────────────────────────────────────
def _draw_title(draw: ImageDraw.Draw, title: str, font_xl, font_lg, start_y: int) -> int:
    # Try large font first; fall back to medium if title is long
    max_chars = 28 if len(title) <= 50 else 32
    lines = textwrap.wrap(title, width=max_chars)[:3]  # max 3 lines

    font = font_xl if len(title) <= 50 else font_lg
    line_h = 80 if font == font_xl else 66

    y = start_y
    for line in lines:
        # Subtle text shadow
        draw.text((62, y + 2), line, fill=(0, 0, 0, 80), font=font)
        draw.text((60, y), line, fill=WHITE, font=font)
        y += line_h
    return y + 10


# ─────────────────────────────────────────────────────────
# EXCERPT / HOOK
# ─────────────────────────────────────────────────────────
def _draw_excerpt(draw: ImageDraw.Draw, excerpt: str, font_sm, y: int):
    if len(excerpt) > 100:
        excerpt = excerpt[:97] + "…"
    lines = textwrap.wrap(excerpt, width=65)[:2]
    for line in lines:
        draw.text((60, y), line, fill=LIGHT_GRAY, font=font_sm)
        y += 32


# ─────────────────────────────────────────────────────────
# BOTTOM BAR — Brand
# ─────────────────────────────────────────────────────────
def _draw_bottom(draw: ImageDraw.Draw, font_brand, font_url, cat_color):
    y = H - 62
    # Bullet/orb accent
    draw.ellipse([60, y + 8, 76, y + 24], fill=(*cat_color, 255))

    # Brand name
    draw.text((88, y + 2), "Little Smart Genius", fill=(*ORANGE, 255), font=font_brand)

    # URL (right-aligned)
    url_text = "littlesmartgenius.com"
    try:
        uw = draw.textlength(url_text, font=font_url)
    except AttributeError:
        uw = len(url_text) * 10
    draw.text((W - 60 - uw, y + 8), url_text, fill=LIGHT_GRAY, font=font_url)

    # Star rating decoration
    draw.text((60, H - 30), "⭐ Educational Resources for Kids 4–12", fill=(*WHITE, 60), font=font_url)


# ─────────────────────────────────────────────────────────
# MAIN: CREATE ONE OG IMAGE
# ─────────────────────────────────────────────────────────
def create_og_image(article: dict, font_cache: dict, force: bool = False) -> str | None:
    slug    = article.get("slug", "default")
    title   = article.get("title", "Little Smart Genius")
    category= article.get("category", "Education")
    excerpt = article.get("excerpt") or article.get("meta_description", "")
    if not excerpt:
        excerpt = "Discover amazing educational activities and printable resources for kids."

    out_path = OUTPUT_DIR / f"{slug}.jpg"
    if out_path.exists() and not force:
        return str(out_path)   # already exists, skip

    cat_color = _cat_color(category)

    # 1. Base image
    img  = Image.new("RGB", (W, H), DARK1)
    _draw_gradient(img)

    # 2. Decorations (before glass card so card is on top)
    _draw_decorations(img, cat_color)

    # 3. Glass card for content area
    _draw_glass_card(img, 40, 100, W - 40, H - 50, radius=24, opacity=22)

    # 4. Draw text on top
    draw = ImageDraw.Draw(img)

    # Brand header (top)
    draw.text((60, 48), "● Little Smart Genius", fill=ORANGE, font=font_cache["sm_bold"])

    # Category badge
    next_y = _draw_badge(draw, category, cat_color, font_cache["sm"], x=60, y=138)

    # Title
    next_y = _draw_title(draw, title, font_cache["xl"], font_cache["lg"], next_y)

    # Excerpt
    _draw_excerpt(draw, excerpt, font_cache["sm"], next_y + 8)

    # Bottom bar
    _draw_bottom(draw, font_cache["brand"], font_cache["url"], cat_color)

    # 5. Save as high-quality JPEG
    img.save(str(out_path), "JPEG", quality=92, optimize=True, progressive=True)
    return str(out_path)


# ─────────────────────────────────────────────────────────
# FONT CACHE (load once, reuse for all images)
# ─────────────────────────────────────────────────────────
def build_font_cache() -> dict:
    print("  [FONT] Loading Inter fonts (downloading if needed)...")
    return {
        "xl":      _load_font("bold",     72),
        "lg":      _load_font("bold",     58),
        "brand":   _load_font("bold",     26),
        "sm_bold": _load_font("semibold", 22),
        "sm":      _load_font("regular",  20),
        "url":     _load_font("regular",  18),
    }


# ─────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Generate premium OG images for all articles")
    parser.add_argument("--slug",  help="Generate for a single article by slug")
    parser.add_argument("--force", action="store_true", help="Re-generate even if already exists")
    args = parser.parse_args()

    print("\n" + "=" * 62)
    print("  OG IMAGE GENERATOR V2 — Little Smart Genius")
    print("=" * 62)

    if not INDEX_PATH.exists():
        print(f"[ERROR] {INDEX_PATH} not found. Run build_articles.py first.")
        sys.exit(1)

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    articles = data.get("articles", [])
    if args.slug:
        articles = [a for a in articles if a.get("slug") == args.slug]
        if not articles:
            print(f"[ERROR] Slug '{args.slug}' not found in search_index.json")
            sys.exit(1)

    print(f"  Articles: {len(articles)}")
    print(f"  Output:   images/og/")
    print(f"  Force:    {'yes' if args.force else 'skip existing'}\n")

    font_cache = build_font_cache()
    print()

    ok = skip = fail = 0
    for art in articles:
        slug = art.get("slug", "?")
        out_path = OUTPUT_DIR / f"{slug}.jpg"
        if out_path.exists() and not args.force:
            skip += 1
            continue
        try:
            result = create_og_image(art, font_cache, args.force)
            size_kb = os.path.getsize(result) // 1024
            print(f"  [OK]   {slug[:55]:<55} {size_kb}KB")
            ok += 1
        except Exception as e:
            print(f"  [FAIL] {slug}: {e}")
            fail += 1

    print(f"\n{'=' * 62}")
    print(f"  Generated : {ok}")
    print(f"  Skipped   : {skip} (already exist)")
    print(f"  Errors    : {fail}")
    print(f"{'=' * 62}\n")


if __name__ == "__main__":
    main()
