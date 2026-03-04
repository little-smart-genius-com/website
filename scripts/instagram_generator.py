"""
INSTAGRAM GENERATOR — V5.0 PREMIUM
Creates stunning 1080x1080 Instagram posts from article data.
Features: Multi-gradient backgrounds, glassmorphism effects, dynamic text layouts,
category-specific color palettes, branded visual identity.
"""

import os
import math
import textwrap
from datetime import datetime
from typing import Dict, Optional, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
INSTAGRAM_DIR = os.path.join(BASE_DIR, "instagram")

# Instagram post size
IG_SIZE = (1080, 1080)

# ═══════════════════════════════════════════════════════════
# BRAND DESIGN SYSTEM V5.0
# ═══════════════════════════════════════════════════════════

BRAND_NAME = "Little Smart Genius"
BRAND_URL = "LittleSmartGenius.com"
BRAND_TAGLINE = "Learning Made Fun!"

# Category-specific color palettes (gradient pairs + accent)
CATEGORY_PALETTES = {
    "math": {
        "gradient_start": (99, 102, 241),    # Indigo
        "gradient_end": (168, 85, 247),       # Purple
        "accent": (251, 191, 36),             # Amber
        "icon": "1+2",
        "emoji_icon": "🧮",
    },
    "critical thinking": {
        "gradient_start": (16, 185, 129),     # Emerald
        "gradient_end": (6, 95, 70),          # Dark emerald
        "accent": (253, 224, 71),             # Yellow
        "icon": "💡",
        "emoji_icon": "🧠",
    },
    "word search": {
        "gradient_start": (59, 130, 246),     # Blue
        "gradient_end": (37, 99, 235),        # Darker blue
        "accent": (251, 146, 60),             # Orange
        "icon": "ABC",
        "emoji_icon": "🔤",
    },
    "spot the difference": {
        "gradient_start": (244, 140, 6),      # Orange
        "gradient_end": (220, 38, 38),        # Red
        "accent": (255, 255, 255),            # White
        "icon": "👁",
        "emoji_icon": "🔍",
    },
    "coloring": {
        "gradient_start": (236, 72, 153),     # Pink
        "gradient_end": (168, 85, 247),       # Purple
        "accent": (253, 224, 71),             # Yellow
        "icon": "🎨",
        "emoji_icon": "🖍️",
    },
    "montessori": {
        "gradient_start": (34, 197, 94),      # Green
        "gradient_end": (21, 128, 61),        # Dark green
        "accent": (254, 240, 138),            # Cream yellow
        "icon": "🌿",
        "emoji_icon": "🌱",
    },
    "printable": {
        "gradient_start": (14, 165, 233),     # Sky blue
        "gradient_end": (2, 132, 199),        # Dark sky
        "accent": (254, 215, 170),            # Peach
        "icon": "📄",
        "emoji_icon": "🖨️",
    },
    "default": {
        "gradient_start": (99, 102, 241),     # Indigo
        "gradient_end": (30, 27, 75),         # Dark indigo
        "accent": (244, 140, 6),              # Orange
        "icon": "⭐",
        "emoji_icon": "✨",
    }
}


def _get_palette(category: str) -> dict:
    """Get the best matching color palette for a category."""
    cat_lower = category.lower()
    for key, palette in CATEGORY_PALETTES.items():
        if key in cat_lower:
            return palette
    return CATEGORY_PALETTES["default"]


# ═══════════════════════════════════════════════════════════
# FONT MANAGEMENT
# ═══════════════════════════════════════════════════════════

_FONT_CACHE = {}

def _get_font(size: int, bold: bool = False) -> 'ImageFont.FreeTypeFont':
    """Load font with caching. Prefers bold for titles."""
    cache_key = (size, bold)
    if cache_key in _FONT_CACHE:
        return _FONT_CACHE[cache_key]

    font_paths_bold = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    font_paths_regular = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    paths = font_paths_bold if bold else font_paths_regular
    for path in paths:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, size)
                _FONT_CACHE[cache_key] = font
                return font
            except Exception:
                continue

    font = ImageFont.load_default()
    _FONT_CACHE[cache_key] = font
    return font


# ═══════════════════════════════════════════════════════════
# VISUAL EFFECTS
# ═══════════════════════════════════════════════════════════

def _create_premium_gradient(palette: dict) -> Image.Image:
    """Create a premium multi-stop diagonal gradient background."""
    img = Image.new("RGB", IG_SIZE)
    pixels = img.load()

    r1, g1, b1 = palette["gradient_start"]
    r2, g2, b2 = palette["gradient_end"]

    for y in range(IG_SIZE[1]):
        for x in range(IG_SIZE[0]):
            # Diagonal gradient: top-left to bottom-right
            ratio = (x / IG_SIZE[0] * 0.4 + y / IG_SIZE[1] * 0.6)
            # Add subtle curve for depth effect
            ratio = ratio ** 0.8
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            pixels[x, y] = (r, g, b)

    return img


def _draw_decorative_circles(draw: ImageDraw.Draw, palette: dict):
    """Draw decorative floating circles for visual depth."""
    accent = palette["accent"]

    # Top-right large circle (semi-transparent)
    for offset in range(3):
        alpha = 25 - offset * 8
        color = (accent[0], accent[1], accent[2])
        r = 200 + offset * 40
        draw.ellipse(
            [IG_SIZE[0] - r + 60, -r + 100, IG_SIZE[0] + r + 60, r + 100],
            outline=color, width=2
        )

    # Bottom-left small circles
    for offset in range(2):
        r = 80 + offset * 50
        draw.ellipse(
            [-r + 40, IG_SIZE[1] - r - 40, r + 40, IG_SIZE[1] + r - 40],
            outline=accent, width=1
        )


def _draw_glassmorphism_card(img: Image.Image, draw: ImageDraw.Draw,
                              bbox: Tuple[int, int, int, int],
                              radius: int = 30, opacity: int = 40):
    """Draw a frosted glass card effect."""
    x1, y1, x2, y2 = bbox

    # Create glass overlay
    glass = Image.new("RGBA", IG_SIZE, (0, 0, 0, 0))
    glass_draw = ImageDraw.Draw(glass)
    glass_draw.rounded_rectangle(
        [x1, y1, x2, y2],
        radius=radius,
        fill=(255, 255, 255, opacity)
    )

    # Subtle border
    glass_draw.rounded_rectangle(
        [x1, y1, x2, y2],
        radius=radius,
        outline=(255, 255, 255, 70),
        width=2
    )

    img_rgba = img.convert("RGBA")
    composite = Image.alpha_composite(img_rgba, glass)
    return composite.convert("RGB")


def _draw_category_badge(draw: ImageDraw.Draw, category: str, palette: dict, y_pos: int = 120):
    """Draw a modern category badge/pill."""
    font = _get_font(26, bold=True)
    cat_text = category.upper()

    bbox = draw.textbbox((0, 0), cat_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Center the pill
    pill_w = text_w + 50
    pill_h = text_h + 24
    pill_x = (IG_SIZE[0] - pill_w) // 2
    pill_y = y_pos

    # Draw pill with accent color
    accent = palette["accent"]
    draw.rounded_rectangle(
        [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
        radius=pill_h // 2,  # Full round corners
        fill=accent,
    )

    # Text on pill (dark for contrast)
    text_x = pill_x + 25
    text_y = pill_y + 10
    # Determine text color based on accent brightness
    brightness = (accent[0] * 299 + accent[1] * 587 + accent[2] * 114) / 1000
    text_color = "#1a1a2e" if brightness > 128 else "#ffffff"
    draw.text((text_x, text_y), cat_text, fill=text_color, font=font)


def _draw_title_centered(draw: ImageDraw.Draw, title: str, y_start: int) -> int:
    """Draw the article title — large, bold, centered, multi-line with shadow."""
    font = _get_font(56, bold=True)

    # Word wrap for 1080px with good padding
    wrapped = textwrap.fill(title, width=20)
    lines = wrapped.split("\n")[:4]  # Max 4 lines

    line_height = 74
    total_height = len(lines) * line_height

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (IG_SIZE[0] - text_w) // 2
        y = y_start + i * line_height

        # Drop shadow
        draw.text((x + 3, y + 3), line, fill=(0, 0, 0, 120), font=font)
        # Main text
        draw.text((x, y), line, fill="#ffffff", font=font)

    return y_start + total_height


def _draw_description(draw: ImageDraw.Draw, description: str, y_start: int) -> int:
    """Draw the meta description paragraph below the title — lighter italic style."""
    font = _get_font(24, bold=False)

    wrapped = textwrap.fill(description, width=42)
    lines = wrapped.split("\n")[:4]  # Max 4 lines

    line_height = 34
    total_height = len(lines) * line_height
    y = y_start + 20  # Gap after title

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (IG_SIZE[0] - text_w) // 2

        # Shadow
        draw.text((x + 2, y + i * line_height + 2), line, fill=(0, 0, 0, 80), font=font)
        # Text in soft white
        draw.text((x, y + i * line_height), line, fill=(255, 255, 255, 210), font=font)

    return y + total_height


def _draw_bottom_bar(draw: ImageDraw.Draw, palette: dict):
    """Draw the branded bottom section: horizontal line + brand name + URL."""
    accent = palette["accent"]

    # Horizontal decorative line
    line_y = IG_SIZE[1] - 155
    line_margin = 260
    draw.line(
        [(line_margin, line_y), (IG_SIZE[0] - line_margin, line_y)],
        fill=(255, 255, 255, 100), width=2
    )

    # Brand name — bold, uppercase style
    brand_font = _get_font(28, bold=True)
    brand_text = BRAND_NAME.upper()
    brand_bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text(
        ((IG_SIZE[0] - brand_w) // 2, IG_SIZE[1] - 120),
        brand_text, fill=accent, font=brand_font
    )

    # URL below brand name
    url_font = _get_font(20, bold=False)
    url_text = f"www.{BRAND_URL}"
    url_bbox = draw.textbbox((0, 0), url_text, font=url_font)
    url_w = url_bbox[2] - url_bbox[0]
    draw.text(
        ((IG_SIZE[0] - url_w) // 2, IG_SIZE[1] - 80),
        url_text, fill=(255, 255, 255, 160), font=url_font
    )


def _draw_top_icon(img: Image.Image, palette: dict) -> int:
    """Draw the brand logo at the top center. Returns the bottom Y position."""
    logo_path = os.path.join(BASE_DIR, "images", "banners", "Little_Smart_Genius_Logo.webp")
    if not os.path.exists(logo_path):
        logo_path = os.path.join(BASE_DIR, "images", "logo.png")
    
    logo_bottom = 120  # default
    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            target_h = 90
            aspect = logo.width / logo.height
            target_w = int(target_h * aspect)
            logo = logo.resize((target_w, target_h), Image.LANCZOS)
            
            x = (IG_SIZE[0] - target_w) // 2
            y = 35
            img.paste(logo, (x, y), mask=logo)
            logo_bottom = y + target_h
        except Exception as e:
            print(f"Error drawing logo: {e}")
    else:
        # Fallback to text icon
        draw = ImageDraw.Draw(img)
        icon_font = _get_font(50, bold=True)
        icon_text = palette.get("icon", "⭐")
        try:
            bbox = draw.textbbox((0, 0), icon_text, font=icon_font)
            w = bbox[2] - bbox[0]
            draw.text(((IG_SIZE[0] - w) // 2, 45), icon_text, fill="#ffffff", font=icon_font)
            logo_bottom = 100
        except Exception:
            pass
    return logo_bottom


def _draw_frame_border(draw: ImageDraw.Draw):
    """Draw a subtle thin frame border around the image edges."""
    margin = 22
    draw.rounded_rectangle(
        [margin, margin, IG_SIZE[0] - margin, IG_SIZE[1] - margin],
        radius=4,
        outline=(255, 255, 255, 60),
        width=2
    )


# ═══════════════════════════════════════════════════════════
# MAIN POST CREATION
# ═══════════════════════════════════════════════════════════

def _create_post_image(title: str, category: str, description: str = "",
                       cover_path: str = None) -> Image.Image:
    """
    Create a premium 1080x1080 Instagram post image.
    
    Design: Cover image as lightly blurred background (still visible),
    semi-transparent overlay, logo, category badge, title, description, brand footer.
    """
    palette = _get_palette(category)

    # ── Step 1: Background ──
    if cover_path and os.path.exists(cover_path):
        # Use cover image as background with LIGHT blur
        bg = Image.open(cover_path).convert("RGB")
        w, h = bg.size
        min_dim = min(w, h)
        left = (w - min_dim) // 2
        top = (h - min_dim) // 2
        bg = bg.crop((left, top, left + min_dim, top + min_dim))
        bg = bg.resize(IG_SIZE, Image.LANCZOS)

        # Light Gaussian blur — cover remains visible
        bg = bg.filter(ImageFilter.GaussianBlur(radius=10))

        # Semi-transparent dark overlay with category tint
        overlay = Image.new("RGBA", IG_SIZE, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        gs = palette["gradient_start"]
        # Uniform darkening overlay — not too heavy so cover shows through
        for y in range(IG_SIZE[1]):
            ratio = y / IG_SIZE[1]
            # Darker at top and bottom, lighter in the middle
            if ratio < 0.15:
                alpha = int(160 - ratio * 400)
            elif ratio > 0.85:
                alpha = int(80 + (ratio - 0.85) * 600)
            else:
                alpha = 110
            overlay_draw.line(
                [(0, y), (IG_SIZE[0], y)],
                fill=(gs[0] // 4, gs[1] // 4, gs[2] // 4, alpha)
            )
        img = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    else:
        # Fallback: premium gradient background
        img = _create_premium_gradient(palette)

    # Convert to RGBA for all compositing
    img = img.convert("RGBA")
    draw = ImageDraw.Draw(img)

    # ── Step 2: Subtle frame border ──
    _draw_frame_border(draw)

    # ── Step 3: Logo at top center ──
    logo_bottom = _draw_top_icon(img, palette)

    # ── Step 4: Decorative line below logo ──
    line_y = logo_bottom + 12
    line_margin = 340
    draw.line(
        [(line_margin, line_y), (IG_SIZE[0] - line_margin, line_y)],
        fill=(255, 255, 255, 80), width=2
    )

    # ── Step 5: Category badge ──
    badge_y = line_y + 18
    _draw_category_badge(draw, category, palette, y_pos=badge_y)
    badge_font = _get_font(26, bold=True)
    badge_bbox = draw.textbbox((0, 0), category.upper(), font=badge_font)
    badge_bottom = badge_y + (badge_bbox[3] - badge_bbox[1]) + 30

    # ── Step 6: Title — centered ──
    title_y = badge_bottom + 20
    title_bottom = _draw_title_centered(draw, title, title_y)

    # ── Step 7: Meta description paragraph ──
    if description:
        _draw_description(draw, description, title_bottom)

    # ── Step 8: Bottom branded bar ──
    _draw_bottom_bar(draw, palette)

    return img.convert("RGB")


# ═══════════════════════════════════════════════════════════
# CAPTION & HASHTAGS
# ═══════════════════════════════════════════════════════════

def _generate_caption(title: str, category: str, keyword: str, excerpt: str) -> str:
    """Generate an engaging Instagram caption with emojis and CTA."""
    palette = _get_palette(category)
    emoji = palette.get("emoji_icon", "✨")

    # Select a random CTA variation
    ctas = [
        "👆 Link in bio for FREE printable worksheets!",
        "👆 Tap the link in bio for free resources!",
        "📥 Get your FREE printable — link in bio!",
    ]
    import random
    cta = random.choice(ctas)

    return f"""{emoji} {title}

{excerpt}

💡 Did you know? Educational activities like these can improve your child's focus, problem-solving skills, and academic performance — while keeping them entertained!

{cta}

🏷️ Category: {category}

🔗 {BRAND_URL}
"""


def _generate_hashtags(category: str, keyword: str) -> str:
    """Generate optimized Instagram hashtags (mix of high-volume + niche)."""
    # Core brand hashtags (always included)
    core = [
        "#LittleSmartGenius", "#KidsEducation", "#LearnThroughPlay",
        "#FunLearning", "#PrintableWorksheets",
    ]

    # High-volume education hashtags (reach)
    reach = [
        "#HomeschoolMom", "#TeacherResources", "#KidsLearning",
        "#ParentingTips", "#EducationalActivities", "#MomLife",
        "#KidsOfInstagram", "#Homeschooling",
    ]

    # Category-specific hashtags (relevance)
    cat_lower = category.lower()
    niche = []
    if "math" in cat_lower:
        niche = ["#MathForKids", "#MathWorksheets", "#NumberGames", "#MathIsFun", "#STEMkids"]
    elif "thinking" in cat_lower or "logic" in cat_lower:
        niche = ["#CriticalThinking", "#LogicPuzzles", "#BrainGames", "#SmartKids", "#ProblemSolving"]
    elif "word" in cat_lower or "language" in cat_lower:
        niche = ["#WordSearch", "#VocabularyBuilding", "#ReadingIsFun", "#Literacy", "#SpellingBee"]
    elif "spot" in cat_lower or "visual" in cat_lower:
        niche = ["#SpotTheDifference", "#VisualLearning", "#PicturePuzzles", "#EyeSpy", "#ObservationSkills"]
    elif "color" in cat_lower or "art" in cat_lower:
        niche = ["#ColoringPages", "#KidsArt", "#FineMotorSkills", "#ArtForKids", "#CreativeKids"]
    elif "montessori" in cat_lower:
        niche = ["#MontessoriAtHome", "#MontessoriActivities", "#HandsOnLearning", "#ChildLed", "#MontessoriMom"]
    else:
        niche = ["#STEM", "#EarlyLearning", "#KidsActivities", "#PreschoolFun", "#ElementarySchool"]

    # Keyword-derived tags
    kw_tags = []
    if keyword:
        kw_words = [w for w in keyword.split() if len(w) > 3][:3]
        for w in kw_words:
            tag = f"#{w.capitalize()}"
            kw_tags.append(tag)

    # Combine: core + niche + reach + keyword (max 30)
    all_tags = core + niche + reach + kw_tags
    # Deduplicate while preserving order
    seen = set()
    unique_tags = []
    for tag in all_tags:
        if tag.lower() not in seen:
            seen.add(tag.lower())
            unique_tags.append(tag)

    return " ".join(unique_tags[:30])


# ═══════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════

def generate_instagram_post(
    article_data: Dict,
    cover_image_path: str = None,
    output_dir: str = None,
) -> Optional[Dict]:
    """
    Generate a premium Instagram post from article data.

    Args:
        article_data: Dict with keys title, slug, category, primary_keyword, excerpt
        cover_image_path: Path to cover image (optional, uses premium gradient if missing)
        output_dir: Override output directory

    Returns:
        Dict with image_path, caption, hashtags
        None if Pillow is not installed
    """
    if not PIL_AVAILABLE:
        print("[Instagram] Pillow not installed — skipping Instagram generation")
        print("[Instagram] Install with: pip install Pillow")
        return None

    out_dir = output_dir or INSTAGRAM_DIR
    os.makedirs(out_dir, exist_ok=True)

    title = article_data.get("title", "New Article")
    slug = article_data.get("slug", "article")
    category = article_data.get("category", "Education")
    keyword = article_data.get("primary_keyword", "")
    excerpt = article_data.get("excerpt", "")[:140]
    description = article_data.get("meta_description", excerpt)[:160]

    # Resolve cover image path from article data if not explicitly provided
    if not cover_image_path:
        cover_rel = article_data.get("image", "")
        if cover_rel and os.path.exists(cover_rel):
            cover_image_path = cover_rel

    # --- Create premium image ---
    img = _create_post_image(title, category, description, cover_image_path)

    # Save as high-quality JPEG
    ts = int(datetime.now().timestamp())
    filename = f"{slug}-ig-{ts}.jpg"
    filepath = os.path.join(out_dir, filename)
    img.save(filepath, "JPEG", quality=95, optimize=True)

    # --- Generate caption & hashtags ---
    caption = _generate_caption(title, category, keyword, excerpt)
    hashtags = _generate_hashtags(category, keyword)

    # Save caption + hashtags in separate file
    caption_file = os.path.join(out_dir, f"{slug}-ig-{ts}.txt")
    with open(caption_file, "w", encoding="utf-8") as f:
        f.write(caption + "\n" + hashtags)

    return {
        "image_path": filepath,
        "caption_path": caption_file,
        "caption": caption,
        "hashtags": hashtags,
    }


# ═══════════════════════════════════════════════════════════
# MAKE.COM WEBHOOK INTEGRATION
# ═══════════════════════════════════════════════════════════

def _upload_image_to_host(image_path: str) -> Optional[str]:
    """
    Upload an image to catbox.moe (free, no registration, no API key needed)
    and return the public URL. Files are hosted permanently.
    """
    import requests

    try:
        filename = os.path.basename(image_path)
        with open(image_path, "rb") as f:
            resp = requests.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": (filename, f, "image/jpeg")},
                timeout=60,
            )

        if resp.status_code == 200 and resp.text.startswith("https://"):
            url = resp.text.strip()
            print(f"[ImageHost] Uploaded OK: {url}")
            return url
        else:
            print(f"[ImageHost] Upload failed: {resp.status_code} - {resp.text[:80]}")
            return None

    except Exception as e:
        print(f"[ImageHost] Upload error: {str(e)[:80]}")
        return None


def send_to_makecom(ig_result: Dict, article_url: str = "") -> bool:
    """
    Send Instagram post data to Make.com webhook for auto-posting.

    Flow:
      1. Upload image to catbox.moe (free, no API key) to get a public URL
      2. Send the public URL + caption + hashtags to Make.com webhook
      3. Make.com passes the URL to Instagram's "Create Photo Post" module

    Required .env variables:
      - MAKECOM_WEBHOOK_URL: your Make.com webhook URL

    Returns True if webhook was sent successfully.
    """
    import requests

    webhook_url = os.environ.get("MAKECOM_WEBHOOK_URL", "")
    if not webhook_url:
        print("[Make.com] No MAKECOM_WEBHOOK_URL configured -- skipping webhook")
        return False

    try:
        image_path = ig_result.get("image_path", "")
        if not image_path or not os.path.exists(image_path):
            print(f"[Make.com] Image not found: {image_path}")
            return False

        # Step 1: Upload image to get a public URL
        image_url = _upload_image_to_host(image_path)
        if not image_url:
            print("[Make.com] Image upload failed -- cannot send to Instagram")
            return False

        # Step 2: Send public URL + metadata to Make.com
        payload = {
            "image_url": image_url,
            "image_filename": os.path.basename(image_path),
            "caption": ig_result.get("caption", ""),
            "hashtags": ig_result.get("hashtags", ""),
            "article_url": article_url,
            "brand": BRAND_NAME,
            "timestamp": datetime.now().isoformat(),
        }

        resp = requests.post(webhook_url, json=payload, timeout=30)

        if resp.status_code == 200:
            print(f"[Make.com] Webhook sent OK -- Instagram post queued")
            return True
        else:
            print(f"[Make.com] Webhook failed: HTTP {resp.status_code}")
            return False

    except Exception as e:
        print(f"[Make.com] Webhook error: {str(e)[:80]}")
        return False


# ═══════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("INSTAGRAM GENERATOR V5.0 PREMIUM — Self Test")
    print("=" * 60)

    if not PIL_AVAILABLE:
        print("\nPillow not installed. Install with: pip install Pillow")
        print("Skipping image generation test.")
    else:
        # Test each category palette
        test_categories = [
            ("Math Skills", "10 Fun Math Activities for Kids"),
            ("Critical Thinking", "How to Teach Critical Thinking Through Play"),
            ("Spot the Difference", "Boost Focus with Spot the Difference Puzzles"),
            ("Coloring", "Best Coloring Pages for Fine Motor Development"),
            ("Word Search", "Essential Word Search Puzzles for Vocabulary"),
            ("Education", "Top Learning Activities for Preschoolers"),
        ]

        results = []
        for category, title in test_categories:
            test_data = {
                "title": title,
                "slug": f"test-{category.lower().replace(' ', '-')}",
                "category": category,
                "primary_keyword": title.lower(),
                "excerpt": f"Discover amazing {category.lower()} resources for kids aged 4-12.",
            }

            result = generate_instagram_post(test_data)
            if result:
                size_kb = os.path.getsize(result["image_path"]) // 1024
                results.append((category, size_kb))
                print(f"\n  [OK] {category}: {result['image_path']} ({size_kb} KB)")
            else:
                print(f"\n  [FAIL] {category}")

        print(f"\n  Generated {len(results)} posts")
        for cat, size in results:
            print(f"    - {cat}: {size} KB")

        print(f"\n  Palettes loaded: {len(CATEGORY_PALETTES)}")
        print(f"  Font cache entries: {len(_FONT_CACHE)}")

    print("\nAll V5.0 tests passed!")
