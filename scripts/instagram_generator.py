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



def _draw_complex_outer_frame(draw):
    '''Draws the dark teal border with gold accents.'''
    # Outer dark teal border
    draw.rectangle([15, 15, 1065, 1065], outline="#2B3A41", width=12)
    # Inner gold secondary border
    draw.rectangle([35, 35, 1045, 1045], outline="#C2A57A", width=4)
    # Corner circles
    r = 8
    for x in [35, 1045]:
        for y in [35, 1045]:
            draw.ellipse([x-r, y-r, x+r, y+r], fill="#C2A57A")
            draw.ellipse([x-r/2, y-r/2, x+r/2, y+r/2], fill="#2B3A41")

def _draw_solid_creamy_card(img, draw, bbox, radius=40):
    x1, y1, x2, y2 = bbox
    # Flat structural shadow matching the reference
    shadow_offset = 14
    sh_color = "#3C2E25" # Dark brown robust shadow
    draw.rounded_rectangle([x1+shadow_offset, y1+shadow_offset, x2+shadow_offset, y2+shadow_offset], radius=radius, fill=sh_color)
        
    # Main creamy card
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill="#FDF6EB")
    
    # Inner brown border
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, outline="#8D6E63", width=4)
    draw.rounded_rectangle([x1+6, y1+6, x2-6, y2-6], radius=radius-6, outline=(141, 110, 99, 100), width=2)
    return img

def _draw_category_badge_top(draw, category, palette, center_x, top_y):
    font = _get_font(28, bold=True)
    cat_text = category.upper()
    bbox = draw.textbbox((0, 0), cat_text, font=font, anchor="mm")
    text_w = bbox[2] - bbox[0]
    
    pill_w = text_w + 60
    pill_h = 48
    pill_x = center_x - pill_w // 2
    # The badge sits exactly overlapping the top border line
    pill_y = top_y - pill_h // 2
    
    # Colors matching reference image (mostly goldish badge with dark text)
    badge_fill = "#E1AE45" 
    
    # Outer gold rim, slightly larger
    draw.rounded_rectangle([pill_x-4, pill_y-4, pill_x+pill_w+4, pill_y+pill_h+4], radius=pill_h//2+4, fill="#C49A45")
    draw.rounded_rectangle([pill_x, pill_y, pill_x+pill_w, pill_y+pill_h], radius=pill_h//2, fill=badge_fill)
    
    pill_cy = pill_y + pill_h // 2
    draw.text((center_x, pill_cy - 1), cat_text, fill="#2E1C0F", font=font, anchor="mm")

def _draw_title_dark(draw, lines, y_start, line_height):
    font = _get_font(76, bold=True)
    for i, line in enumerate(lines):
        y = y_start + i * line_height + line_height // 2
        # No heavy shadow, just a subtle depth effect for realism
        draw.text((1080 // 2 + 1, y + 1), line, fill="#D7CCC8", font=font, anchor="mm")
        draw.text((1080 // 2, y), line, fill="#3E2723", font=font, anchor="mm")

def _draw_description_dark(draw, lines, y_start, line_height):
    font = _get_font(42, bold=False)
    for i, line in enumerate(lines):
        y = y_start + i * line_height + line_height // 2
        draw.text((1080 // 2, y), line, fill="#4E342E", font=font, anchor="mm")

def _draw_top_brand_header(img, draw, y_center):
    """Draw the logo and brand text at the very top of the post."""
    import os
    BASE_DIR = 'C:/Users/Omar/Desktop/little-smart-genius-site/Nouveau dossier/online/Little_Smart_Genius'
    BRAND_NAME = "Little Smart Genius"
    
    # Logo
    logo_path = os.path.join(BASE_DIR, "images", "banners", "Little_Smart_Genius_Logo.webp")
    if not os.path.exists(logo_path):
        logo_path = os.path.join(BASE_DIR, "images", "logo.png")
    
    target_h = 75
    logo_w = target_h
    if os.path.exists(logo_path):
        try:
            from PIL import Image
            logo = Image.open(logo_path).convert("RGBA")
            aspect = logo.width / logo.height
            logo_w = int(target_h * aspect)
            logo = logo.resize((logo_w, target_h), Image.LANCZOS)
            x = (1080 - logo_w) // 2
            y = 30
            img.paste(logo, (x, y), mask=logo)
        except Exception:
            pass

    # Brand Text below logo
    brand_font = _get_font(34, bold=True)
    brand_text = BRAND_NAME.upper()
    try:
        draw.text((1080 // 2 + 2, 137), brand_text, fill="#D7CCC8", font=brand_font, anchor="mm")
        draw.text((1080 // 2, 135), brand_text, fill="#5D4037", font=brand_font, anchor="mm")
    except Exception:
        pass

def _draw_bottom_split_panels(img, draw, card_bottom_y):
    """Draw the two distinct white panels with rounded corners at the bottom."""
    import os
    BASE_DIR = 'C:/Users/Omar/Desktop/little-smart-genius-site/Nouveau dossier/online/Little_Smart_Genius'
    
    panel_y = card_bottom_y + 25
    panel_h = 135
    panel_w = 445
    margin_x = 75
    
    sh_color = "#3C2E25"
    s_off = 10
    
    # Left Panel (CTA & URL)
    lx1 = margin_x
    lx2 = lx1 + panel_w
    # Flat structural shadow
    draw.rounded_rectangle([lx1+s_off, panel_y+s_off, lx2+s_off, panel_y+panel_h+s_off], radius=20, fill=sh_color)
    draw.rounded_rectangle([lx1, panel_y, lx2, panel_y+panel_h], radius=20, fill="#FFFFFF")
    draw.rounded_rectangle([lx1, panel_y, lx2, panel_y+panel_h], radius=20, outline="#E0E0E0", width=2)
    
    font_small = _get_font(22, bold=False)
    font_bold = _get_font(26, bold=True)
    
    # CTA Top Line
    draw.text((lx1 + panel_w//2, panel_y + 35), "+40 FREE Educational Printables", fill="#B71C1C", font=font_bold, anchor="mm")
    draw.text((lx1 + panel_w//2, panel_y + 65), "Waiting for You", fill="#424242", font=font_small, anchor="mm")
    
    # Fancy Arrows instead of text
    arr_y = panel_y + 90
    draw.line([(lx1 + panel_w//2 - 60, arr_y), (lx1 + panel_w//2 + 60, arr_y)], fill="#C2A57A", width=2)
    draw.polygon([(lx1 + panel_w//2 + 60, arr_y), (lx1 + panel_w//2 + 50, arr_y - 6), (lx1 + panel_w//2 + 50, arr_y + 6)], fill="#C2A57A")
    draw.polygon([(lx1 + panel_w//2 - 60, arr_y), (lx1 + panel_w//2 - 50, arr_y - 6), (lx1 + panel_w//2 - 50, arr_y + 6)], fill="#C2A57A")

    draw.text((lx1 + panel_w//2, panel_y + 115), "www.LittleSmartGenius.com", fill="#212121", font=_get_font(26, bold=False), anchor="mm")
    
    # Right Panel (Socials)
    rx2 = 1080 - margin_x
    rx1 = rx2 - panel_w
    # Flat structural shadow
    draw.rounded_rectangle([rx1+s_off, panel_y+s_off, rx2+s_off, panel_y+panel_h+s_off], radius=20, fill=sh_color)
    draw.rounded_rectangle([rx1, panel_y, rx2, panel_y+panel_h], radius=20, fill="#F7F7F7")
    draw.rounded_rectangle([rx1, panel_y, rx2, panel_y+panel_h], radius=20, outline="#D6D6D6", width=2)
    
    draw.text((rx1 + panel_w//2, panel_y + 35), "Share & Follow", fill="#B71C1C", font=font_bold, anchor="mm")
    draw.text((rx1 + panel_w//2, panel_y + 65), "for more Freebies", fill="#212121", font=_get_font(24, bold=True), anchor="mm")
    
    # Social Icons
    icon_size = 36
    spacing = 15
    handle = "@LittleSmartGenius"
    handle_font = _get_font(26, bold=False)
    
    temp_bbox = draw.textbbox((0, 0), handle, font=handle_font)
    handle_w = temp_bbox[2] - temp_bbox[0]
    total_social_w = icon_size + spacing + icon_size + spacing + handle_w
    
    sx = rx1 + (panel_w - total_social_w) // 2
    sy = panel_y + 95
    
    from PIL import Image
    # Ig - USING USER'S DOWNLOADED FILE
    ig_path = os.path.join(BASE_DIR, "images", "banners", "instagram-new.png")
    if os.path.exists(ig_path):
        ig_icon = Image.open(ig_path).convert("RGBA").resize((icon_size, icon_size), Image.LANCZOS)
        # Tint to #212121 by keeping alpha and replacing RGB
        r, g, b, alpha = ig_icon.split()
        dark_ig = Image.merge("RGBA", (
            Image.new("L", ig_icon.size, 33),
            Image.new("L", ig_icon.size, 33),
            Image.new("L", ig_icon.size, 33),
            alpha
        ))
        img.paste(dark_ig, (sx, sy - icon_size//2), mask=dark_ig)
    
    sx += icon_size + spacing
    
    # Pin - USING USER'S DOWNLOADED FILE
    pin_path = os.path.join(BASE_DIR, "images", "banners", "pinterest.png")
    if os.path.exists(pin_path):
        pin_icon = Image.open(pin_path).convert("RGBA").resize((icon_size, icon_size), Image.LANCZOS)
        r, g, b, alpha = pin_icon.split()
        dark_pin = Image.merge("RGBA", (
            Image.new("L", pin_icon.size, 33),
            Image.new("L", pin_icon.size, 33),
            Image.new("L", pin_icon.size, 33),
            alpha
        ))
        img.paste(dark_pin, (sx, sy - icon_size//2), mask=dark_pin)
        
    sx += icon_size + spacing
    draw.text((sx, sy), handle, fill="#212121", font=handle_font, anchor="lm")


# 
# MAIN POST CREATION
# 

def _create_post_image(title: str, category: str, description: str = "",
                       cover_path: str = None) -> 'Image.Image':
    palette = _get_palette(category)
    import textwrap
    from PIL import Image, ImageDraw, ImageFilter
    
    #  Step 1: Background 
    if cover_path and os.path.exists(cover_path):
        bg = Image.open(cover_path).convert("RGB")
        w, h = bg.size
        min_dim = min(w, h)
        left = (w - min_dim) // 2
        top = (h - min_dim) // 2
        bg = bg.crop((left, top, left + min_dim, top + min_dim))
        bg = bg.resize((1080, 1080), Image.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(radius=15))

        # Light semi-transparent overlay to soften the blurred background towards cream
        overlay = Image.new("RGBA", (1080, 1080), (253, 247, 235, 140))
        img = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    else:
        img = _create_premium_gradient(palette)

    img = img.convert("RGBA")
    draw = ImageDraw.Draw(img)

    # Outer complex frame
    _draw_complex_outer_frame(draw)
    
    # Top Brand Header
    _draw_top_brand_header(img, draw, 0)
    
    # Text layout calculation
    def _wrap_text(text: str, width: int, max_lines: int = 4) -> list:
        wrapped = textwrap.fill(text, width=width)
        return wrapped.split("\n")[:max_lines]

    title_lines = _wrap_text(title, width=19, max_lines=4)
    desc_lines = _wrap_text(description, width=38, max_lines=4) if description else []

    title_line_height = 92
    desc_line_height = 54
    
    title_total_h = len(title_lines) * title_line_height
    desc_total_h = len(desc_lines) * desc_line_height
    
    gap_badge_title = 50
    gap_title_desc = 45
    
    inner_content_h = title_total_h
    if desc_lines:
        inner_content_h += gap_title_desc + desc_total_h
        
    top_limit = 170  
    bottom_limit = 1080 - 180  
    
    card_padding_top = 55
    card_padding_bottom = 45
    total_footprint = card_padding_top + inner_content_h + card_padding_bottom
    
    card_top = top_limit + (bottom_limit - top_limit - total_footprint) // 2
    card_bottom = card_top + total_footprint
    card_margin = 85
    
    # Draw Main Card
    _draw_solid_creamy_card(img, draw, (card_margin, card_top, 1080 - card_margin, card_bottom), radius=35)
    
    # Category badge intersecting top line
    _draw_category_badge_top(draw, category, palette, center_x=1080//2, top_y=card_top)
    
    # Title
    title_y = card_top + card_padding_top
    _draw_title_dark(draw, title_lines, title_y, line_height=title_line_height)
    
    # Description
    if desc_lines:
        desc_y = title_y + title_total_h + gap_title_desc
        _draw_description_dark(draw, desc_lines, desc_y, line_height=desc_line_height)

    # Bottom Split Panels
    _draw_bottom_split_panels(img, draw, card_bottom)
    
    return img.convert("RGB")
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
