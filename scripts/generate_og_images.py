#!/usr/bin/env python3
"""
generate_og_images.py — Premium OpenGraph Image Generator V4 (Artistic + Emojis)
================================================================================
DESIGN V4:
  - Full title support (Dynamic font sizing to ensure no text is cut).
  - High-converting marketing hook instead of simple text cutoff.
  - Twemoji (Twitter emojis) injected dynamically based on category.
  - Artistic blurred background + glassmorphism overlays + elegant typography.

Usage: python scripts/generate_og_images.py --force
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
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    print("[ERROR] Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

# ─── PATHS ────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).resolve().parent
BASE_DIR    = SCRIPT_DIR.parent
FONTS_DIR   = SCRIPT_DIR / "fonts"
EMOJI_DIR   = SCRIPT_DIR / "emojis"
INDEX_PATH  = BASE_DIR / "search_index.json"
IMAGES_DIR  = BASE_DIR / "images"
OUTPUT_DIR  = BASE_DIR / "images" / "og"
LOGO_PATH   = BASE_DIR / "images" / "banners" / "Little_Smart_Genius_Logo.webp"

FONTS_DIR.mkdir(exist_ok=True)
EMOJI_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── DOWNLOADING FONTS ────────────────────────────────────────────────────
_NOTO_BASE = "https://github.com/notofonts/noto-fonts/raw/main/hinted/ttf/NotoSans"
FONT_FILES = {
    "bold":     ("noto-bold.ttf",     f"{_NOTO_BASE}/NotoSans-Bold.ttf"),
    "semibold": ("noto-semibold.ttf", f"{_NOTO_BASE}/NotoSans-SemiBold.ttf"),
    "regular":  ("noto-regular.ttf",  f"{_NOTO_BASE}/NotoSans-Regular.ttf"),
}

def _download_font(key: str) -> Path | None:
    filename, url = FONT_FILES[key]
    dest = FONTS_DIR / filename
    if not dest.exists():
        try:
            urllib.request.urlretrieve(url, dest)
        except Exception as e:
            print(f"  [FONT] Failed: {e}")
            return None
    return dest

def _load_font(key: str, size: int) -> ImageFont.FreeTypeFont:
    path = _download_font(key)
    if path:
        try:
            return ImageFont.truetype(str(path), size)
        except Exception:
            pass
    return ImageFont.load_default()

# ─── DOWNLOADING EMOJIS (TWEMOJI CDN) ─────────────────────────────────────
# We map categories to their Unicode Hex representations to download the exactly right PNG.
CATEGORY_EMOJIS = {
    "math":             "1f9ee", # 🧮
    "critical thinking":"1f9e0", # 🧠
    "language arts":    "1f4da", # 📚
    "visual skills":    "1f3af", # 🎯
    "fine motor skills":"1f58d", # 🖍️
    "creative arts":    "1f3a8", # 🎨
    "problem solving":  "1f9e9", # 🧩
    "coloring":         "1f58d", # 🖍️
    "education":        "1f393", # 🎓
    "default":          "2728",  # ✨
}

def _get_emoji_img(category: str) -> Image.Image | None:
    key = category.lower()
    hex_code = CATEGORY_EMOJIS.get("default")
    for k, v in CATEGORY_EMOJIS.items():
        if k in key:
            hex_code = v
            break
            
    dest = EMOJI_DIR / f"{hex_code}.png"
    if not dest.exists():
        # Download from Cloudflare Twemoji CDN
        url = f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/{hex_code}.png"
        try:
            urllib.request.urlretrieve(url, dest)
        except Exception:
            return None
            
    try:
        return Image.open(dest).convert("RGBA")
    except Exception:
        return None

# ─── DESIGN CONSTANTS ─────────────────────────────────────────────────────
W, H   = 1200, 630
ORANGE = (244, 140, 6)
WHITE  = (255, 255, 255)
GRAY   = (210, 215, 230)
DARK   = (10, 12, 30)

CATEGORY_PALETTES = {
    "math":             ((99,  102, 241), (129, 140, 248)),
    "critical thinking":(( 88,  28, 135), (168, 85,  247)),
    "language arts":    (( 13, 148, 136), ( 45, 212, 191)),
    "visual skills":    (( 29,  78, 216), ( 96, 165, 250)),
    "fine motor skills":((190,  18,  60), (251, 113, 133)),
    "creative arts":    ((126,  34, 206), (216, 180, 254)),
    "problem solving":  ((180,  83,   9), (251, 191,  36)),
    "coloring":         ((190,  18,  60), (253, 164, 175)),
    "education":        ((180,  83,   9), (251, 191,  36)),
}

def _cat_palette(category: str) -> tuple:
    key = category.lower()
    for k, v in CATEGORY_PALETTES.items():
        if k in key:
            return v
    return (ORANGE, (255, 180, 80))

# ─── HIGH CONVERTING HOOK ─────────────────────────────────────────────────
HOOK_TEXT = "✨ Give your child the edge they need! Download this highly engaging, premium printable activity today. Perfectly designed to boost cognitive skills, focus, and creativity while having fun! 🚀"

# ─── BACKGROUND & OVERLAYS ────────────────────────────────────────────────
def _make_background(slug: str) -> Image.Image:
    img = None
    for f in IMAGES_DIR.iterdir():
        if f.is_file() and slug in f.name and "cover" in f.name:
            try:
                img = Image.open(f).convert("RGBA")
                break
            except Exception:
                continue

    if img is None:
        return Image.new("RGBA", (W, H), DARK + (255,))

    src_ratio = img.width / img.height
    tgt_ratio = W / H
    if src_ratio > tgt_ratio:
        new_h = H
        new_w = int(img.width * H / img.height)
    else:
        new_w = W
        new_h = int(img.height * W / img.width)

    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - W) // 2
    top  = (new_h - H) // 2
    img  = img.crop((left, top, left + W, top + H))
    
    # Very heavy blur for artistic, moody background
    img = img.filter(ImageFilter.GaussianBlur(radius=25))
    return img.convert("RGBA")

def _apply_overlays(base: Image.Image, cat_color1: tuple) -> Image.Image:
    result = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    result.paste(base, (0, 0))

    # Darker base overlay (80% opacity for maximum text readability)
    overlay = Image.new("RGBA", (W, H), DARK + (210,))
    result = Image.alpha_composite(result, overlay)

    draw = ImageDraw.Draw(result)

    # Vignette
    for i in range(120, 0, -1):
        alpha = int(115 * (1 - i / 120) ** 2.5)
        draw.rectangle([0, 0, W, H], outline=(0, 0, 0, alpha), width=3) # Approximated vignette

    # Glow in center where text is
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(glow)
    r, g, b = cat_color1
    for radius in range(250, 0, -1):
        alpha = int(35 * (1 - radius / 250) ** 3.0)
        gd.ellipse([W//2 - int(radius*1.5), H//2 - radius, W//2 + int(radius*1.5), H//2 + radius], fill=(r, g, b, alpha))
    result = Image.alpha_composite(result, glow)

    return result

# ─── ELEMENTS ─────────────────────────────────────────────────────────────
def _draw_logo(img: Image.Image) -> int:
    if not LOGO_PATH.exists(): return 40
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo.thumbnail((72, 72), Image.LANCZOS)
        img.paste(logo, ((W - logo.width) // 2, 28), logo)
        return 28 + logo.height + 15
    except Exception:
        return 40

def _draw_rule(draw: ImageDraw.Draw, y: int, color: tuple):
    line_w = 320
    x1 = (W - line_w) // 2
    x2 = x1 + line_w
    draw.line([(x1, y), (W//2 - 24, y)], fill=(*color, 160), width=1)
    draw.polygon([(W//2, y - 4), (W//2 + 6, y), (W//2, y + 4), (W//2 - 6, y)], fill=(*color, 240))
    draw.line([(W//2 + 24, y), (x2, y)], fill=(*color, 160), width=1)

def _draw_badge(draw: ImageDraw.Draw, img: Image.Image, text: str, color1: tuple, color2: tuple, font, y: int, emoji_img: Image.Image = None) -> int:
    text_up = text.upper()
    try:
        tw = draw.textlength(text_up, font=font)
    except AttributeError:
        tw = len(text_up) * 10

    pad_x, pad_y = 24, 8
    bw = int(tw + pad_x * 2)
    if emoji_img:
        bw += 30 # space for emoji inside badge
        
    bh = 38
    bx = (W - bw) // 2
    by = y

    # Pill background
    pill = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pill)
    
    # Gradient pill
    for xi in range(bw):
        t = xi / max(bw, 1)
        rc = int(color1[0] + (color2[0] - color1[0]) * t)
        gc = int(color1[1] + (color2[1] - color1[1]) * t)
        bc = int(color1[2] + (color2[2] - color1[2]) * t)
        pd.rounded_rectangle([xi, 0, xi+1, bh], radius=0, fill=(rc, gc, bc, 240))
    # Clip corners to round shape
    mask = Image.new("L", (bw, bh), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, bw, bh], radius=bh//2, fill=255)
    pill.putalpha(mask)
    
    img.paste(pill, (bx, by), pill)
    
    # Optionally paste emoji inside pill
    text_start_x = bx + pad_x
    if emoji_img:
        em = emoji_img.copy()
        em.thumbnail((22, 22), Image.LANCZOS)
        img.paste(em, (bx + 14, by + 8), em)
        text_start_x += 26

    # Text
    draw.text((text_start_x + 1, by + pad_y + 1), text_up, fill=(0, 0, 0, 80), font=font)
    draw.text((text_start_x, by + pad_y), text_up, fill=WHITE, font=font)

    return by + bh + 24

def _text_center(draw: ImageDraw.Draw, text: str, y: int, font, fill=(255, 255, 255)) -> int:
    try:
        tw = draw.textlength(text, font=font)
    except AttributeError:
        tw = len(text) * 20
    tx = (W - tw) // 2
    draw.text((tx + 2, y + 2), text, fill=(0, 0, 0, 150), font=font)
    draw.text((tx, y), text, fill=fill, font=font)
    return y

def _draw_dynamic_title(draw: ImageDraw.Draw, title: str, start_y: int, max_h: int) -> int:
    """Dynamic font sizing to ensure FULL TITLE fits inside the allowed height max_h."""
    # We start with size 72, and go down to minimum 36
    for size in range(72, 34, -2):
        font = _load_font("bold", size)
        
        # Estimate characters per line for this size (rough approx: ~1200 width / (size*0.55))
        chars_per_line = int(W * 0.85 / (size * 0.55))
        lines = textwrap.wrap(title, width=chars_per_line)
        
        line_height = int(size * 1.25)
        total_height = len(lines) * line_height
        
        if total_height <= max_h:
            # We found a font size that fits!
            # Center vertically within the max_h box
            current_y = start_y + (max_h - total_height) // 2
            for line in lines:
                _text_center(draw, line, current_y, font, fill=WHITE)
                current_y += line_height
            return start_y + max_h
            
    # If it still doesn't fit (very long title), we use the smallest font (36) and just write it.
    font = _load_font("bold", 36)
    lines = textwrap.wrap(title, width=50)
    current_y = start_y
    for line in lines:
        _text_center(draw, line, current_y, font, fill=WHITE)
        current_y += int(36 * 1.25)
    return current_y

def _draw_bottom(draw: ImageDraw.Draw, fonts: dict, color1: tuple):
    y_bar = H - 85
    _draw_rule(draw, y_bar, color1)
    
    brand_text = "✦  Little Smart Genius  ✦"
    _text_center(draw, brand_text, y_bar + 16, fonts["brand"], fill=ORANGE)
    
    url_text = "www.LittleSmartGenius.com"
    _text_center(draw, url_text, y_bar + 42, fonts["url"], fill=(*GRAY, 220))


# ─── MAIN PROCESS ─────────────────────────────────────────────────────────
def create_og_image(article: dict, fonts: dict, force: bool = False) -> str | None:
    slug     = article.get("slug", "default")
    title    = article.get("title", "Little Smart Genius")
    category = article.get("category", "Education")

    out_path = OUTPUT_DIR / f"{slug}.jpg"
    if out_path.exists() and not force:
        return str(out_path)

    color1, color2 = _cat_palette(category)
    bg = _make_background(slug)
    canvas = _apply_overlays(bg, color1)
    draw = ImageDraw.Draw(canvas)

    # Emoji
    emoji_img = _get_emoji_img(category)

    # 1. Logo
    y = _draw_logo(canvas)
    _draw_rule(draw, y + 8, ORANGE)
    
    # 2. Category badge with EMOJI
    y += 24
    y = _draw_badge(draw, canvas, category, color1, color2, fonts["badge"], y, emoji_img=emoji_img)

    # 3. Dynamic Title (we allocate ~180px of vertical space for the title)
    y = _draw_dynamic_title(draw, title, y, max_h=180)

    # 4. High-Converting Hook (fixed 2 lines, gray)
    y += 18
    lines = textwrap.wrap(HOOK_TEXT, width=70)[:2]
    for line in lines:
        _text_center(draw, line, y, fonts["excerpt"], fill=GRAY)
        y += 34

    # 5. Bottom Brand & URL
    _draw_bottom(draw, fonts, color1)

    # Save
    final = canvas.convert("RGB")
    final.save(str(out_path), "JPEG", quality=94, optimize=True, progressive=True)
    return str(out_path)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not INDEX_PATH.exists():
        sys.exit(1)

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        articles = json.load(f).get("articles", [])
        
    if args.slug:
        articles = [a for a in articles if a.get("slug") == args.slug]

    fonts = {
        "badge":   _load_font("bold", 18),
        "excerpt": _load_font("regular", 23),
        "brand":   _load_font("semibold", 22),
        "url":     _load_font("semibold", 20),
    }

    ok = 0
    for art in articles:
        try:
            create_og_image(art, fonts, args.force)
            ok += 1
        except Exception as e:
            print(f"Error on {art.get('slug')}: {e}")
            
    print(f"Generated {ok} OG images with Creative Design V4.")

if __name__ == "__main__":
    main()
