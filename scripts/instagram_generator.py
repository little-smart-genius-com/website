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
                              radius: int = 30, opacity: int = 70):
    """Draw a frosted glass card effect (light tinted)."""
    x1, y1, x2, y2 = bbox

    # Create glass overlay
    glass = Image.new("RGBA", IG_SIZE, (0, 0, 0, 0))
    glass_draw = ImageDraw.Draw(glass)
    
    # White glass backing
    glass_draw.rounded_rectangle(
        [x1, y1, x2, y2],
        radius=radius,
        fill=(255, 255, 255, opacity)
    )

    # Subtle bright border for the glass effect
    glass_draw.rounded_rectangle(
        [x1, y1, x2, y2],
        radius=radius,
        outline=(255, 255, 255, 120),
        width=3
    )

    img_rgba = img.convert("RGBA")
    composite = Image.alpha_composite(img_rgba, glass)
    return composite.convert("RGB")


def _draw_category_badge(draw: ImageDraw.Draw, category: str, palette: dict, y_pos: int = 120):
    """Draw a modern category badge/pill."""
    font = _get_font(28, bold=True)
    cat_text = category.upper()

    bbox = draw.textbbox((0, 0), cat_text, font=font, anchor="mm")
    text_w = bbox[2] - bbox[0]

    # Center the pill
    pill_w = text_w + 60
    pill_h = 48
    pill_x = (IG_SIZE[0] - pill_w) // 2
    pill_y = y_pos

    # Draw pill with accent color
    accent = palette["accent"]
    draw.rounded_rectangle(
        [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
        radius=pill_h // 2,  # Full round corners
        fill=accent,
    )

    # Text on pill perfectly centered using mm anchor
    pill_cx = IG_SIZE[0] // 2
    pill_cy = pill_y + pill_h // 2
    
    # Determine text color based on accent brightness
    brightness = (accent[0] * 299 + accent[1] * 587 + accent[2] * 114) / 1000
    text_color = "#1a1a2e" if brightness > 128 else "#ffffff"
    draw.text((pill_cx, pill_cy - 1), cat_text, fill=text_color, font=font, anchor="mm")


def _draw_title_centered(draw: ImageDraw.Draw, lines: list, y_start: int, line_height: int):
    """Draw the article title — large, bold, perfectly centered, with shadow."""
    font = _get_font(76, bold=True)

    for i, line in enumerate(lines):
        y = y_start + i * line_height + line_height // 2

        # Strong double drop shadow for intense white background
        draw.text((IG_SIZE[0] // 2 + 5, y + 5), line, fill=(0, 0, 0, 220), font=font, anchor="mm")
        draw.text((IG_SIZE[0] // 2 + 2, y + 2), line, fill=(0, 0, 0, 180), font=font, anchor="mm")
        
        # Pure white text
        draw.text((IG_SIZE[0] // 2, y), line, fill="#ffffff", font=font, anchor="mm")


def _draw_description(draw: ImageDraw.Draw, lines: list, y_start: int, line_height: int):
    """Draw the meta description paragraph below the title — perfectly centered."""
    font = _get_font(42, bold=False)

    for i, line in enumerate(lines):
        y = y_start + i * line_height + line_height // 2

        # Strong shadow
        draw.text((IG_SIZE[0] // 2 + 3, y + 3), line, fill=(0, 0, 0, 200), font=font, anchor="mm")
        draw.text((IG_SIZE[0] // 2 + 1, y + 1), line, fill=(0, 0, 0, 120), font=font, anchor="mm")
        
        # Pure white text
        draw.text((IG_SIZE[0] // 2, y), line, fill=(255, 255, 255, 255), font=font, anchor="mm")


def _draw_bottom_bar(img: Image.Image, draw: ImageDraw.Draw, palette: dict, card_bottom_y: int):
    """Draw the new Hybrid V8 double pill footer with dark URL/social boxes."""
    import os
    BASE_DIR = 'C:/Users/Omar/Desktop/little-smart-genius-site/Nouveau dossier/online/Little_Smart_Genius'
    
    # Force the dual pills to always be anchored at the absolute bottom
    panel_y = IG_SIZE[1] - 195
    panel_h = 75 # Pill height
    panel_w = 460
    margin_x = 65
    
    # Adaptive border using category accent color, or a fallback gold
    border_color = palette.get("accent", "#E69A0B")
    
    # Left Pill
    lx1 = margin_x
    lx2 = lx1 + panel_w
    
    # Pill background
    draw.rounded_rectangle([lx1, panel_y, lx2, panel_y+panel_h], radius=20, fill="#FFFFFF")
    draw.rounded_rectangle([lx1, panel_y, lx2, panel_y+panel_h], radius=20, outline=border_color, width=4)
    
    font_small = _get_font(22, bold=False)
    font_bold = _get_font(26, bold=True)
    
    draw.text((lx1 + panel_w//2, panel_y + 24), "+40 FREE Educational Printables", fill="#D32F2F", font=font_bold, anchor="mm")
    draw.text((lx1 + panel_w//2, panel_y + 51), "Waiting for You", fill="#212121", font=font_small, anchor="mm")
    
    # Red Arrow Pointing Down
    arrow_y = panel_y + panel_h + 5
    cx = lx1 + panel_w//2
    # Simple downward arrow
    draw.polygon([(cx-10, arrow_y), (cx+10, arrow_y), (cx+10, arrow_y+15), (cx+20, arrow_y+15), (cx, arrow_y+30), (cx-20, arrow_y+15), (cx-10, arrow_y+15)], fill="#D32F2F", outline="#FFFFFF", width=2)
    
    # Dark URL box
    box_y = arrow_y + 35
    box_h = 55
    # Dark purple/black semi-transparent footer block
    draw.rounded_rectangle([lx1, box_y, lx2, box_y+box_h], radius=8, fill=(35, 25, 35, 230))
    draw.rounded_rectangle([lx1+2, box_y+2, lx2-2, box_y+box_h-2], radius=6, outline=(255, 255, 255, 180), width=1)
    
    draw.text((lx1 + panel_w//2, box_y + box_h//2), f"www.{BRAND_URL}", fill="#FFFFFF", font=_get_font(26, bold=True), anchor="mm")
    
    # Right Pill
    rx2 = IG_SIZE[0] - margin_x
    rx1 = rx2 - panel_w
    
    draw.rounded_rectangle([rx1, panel_y, rx2, panel_y+panel_h], radius=20, fill="#FFFFFF")
    draw.rounded_rectangle([rx1, panel_y, rx2, panel_y+panel_h], radius=20, outline=border_color, width=4)
    
    draw.text((rx1 + panel_w//2, panel_y + 24), "Share & Follow", fill="#D32F2F", font=font_bold, anchor="mm")
    draw.text((rx1 + panel_w//2, panel_y + 51), "for more Freebies", fill="#D32F2F", font=font_bold, anchor="mm")
    
    # Red Arrow Pointing Down
    cx_r = rx1 + panel_w//2
    draw.polygon([(cx_r-10, arrow_y), (cx_r+10, arrow_y), (cx_r+10, arrow_y+15), (cx_r+20, arrow_y+15), (cx_r, arrow_y+30), (cx_r-20, arrow_y+15), (cx_r-10, arrow_y+15)], fill="#D32F2F", outline="#FFFFFF", width=2)

    # Dark Social box
    draw.rounded_rectangle([rx1, box_y, rx2, box_y+box_h], radius=8, fill=(35, 25, 35, 230))
    draw.rounded_rectangle([rx1+2, box_y+2, rx2-2, box_y+box_h-2], radius=6, outline=(255, 255, 255, 180), width=1)
    
    icon_size = 32
    spacing = 15
    handle = "LittleSmartGenius_com"
    handle_font = _get_font(26, bold=True)
    
    temp_bbox = draw.textbbox((0, 0), handle, font=handle_font)
    handle_w = temp_bbox[2] - temp_bbox[0]
    total_social_w = icon_size + spacing + icon_size + spacing + handle_w
    
    sx = rx1 + (panel_w - total_social_w) // 2
    sy = box_y + box_h//2
    
    from PIL import Image
    # Ig
    ig_path = os.path.join(BASE_DIR, "images", "banners", "instagram-new.png")
    if os.path.exists(ig_path):
        ig_icon = Image.open(ig_path).convert("RGBA").resize((icon_size, icon_size), Image.LANCZOS)
        # Paste white icon since it's on a dark background
        white_fill = Image.new("RGBA", (icon_size, icon_size), "#FFFFFF")
        img.paste(white_fill, (sx, sy - icon_size//2), mask=ig_icon)
    
    sx += icon_size + spacing
    
    # Pin
    pin_path = os.path.join(BASE_DIR, "images", "banners", "pinterest.png")
    if os.path.exists(pin_path):
        pin_icon = Image.open(pin_path).convert("RGBA").resize((icon_size, icon_size), Image.LANCZOS)
        white_fill = Image.new("RGBA", (icon_size, icon_size), "#FFFFFF")
        img.paste(white_fill, (sx, sy - icon_size//2), mask=pin_icon)
        
    sx += icon_size + spacing
    draw.text((sx, sy), handle, fill="#FFFFFF", font=handle_font, anchor="lm")


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
    # Create empty margin between logo and brand block
    line_y = logo_bottom + 35
    line_margin = 340
    draw.line(
        [(line_margin, line_y), (IG_SIZE[0] - line_margin, line_y)],
        fill=(255, 255, 255, 80), width=2
    )

    # ── Text layout calculation to perfectly center vertically ──
    def _wrap_text(text: str, width: int, max_lines: int = 3) -> list:
        wrapped = textwrap.fill(text, width=width)
        return wrapped.split("\n")[:max_lines]

    # Force up to 25 characters per line to keep it short vertically
    title_lines = _wrap_text(title, width=25, max_lines=3)
    desc_lines = _wrap_text(description, width=38, max_lines=4) if description else []

    title_line_height = 92
    desc_line_height = 54
    
    title_total_h = len(title_lines) * title_line_height
    desc_total_h = len(desc_lines) * desc_line_height
    
    badge_h = 48
    gap_badge_title = 40
    gap_title_desc = 40
    
    # FIX: Lock the structural height to maximums so the entire frame is uniformly sized
    fixed_title_lines = 3
    fixed_desc_lines = 4
    max_title_h = fixed_title_lines * title_line_height
    max_desc_h = fixed_desc_lines * desc_line_height
    
    # Inner content is hardcoded to the maximum boundary so the card size never changes
    inner_content_h = max_title_h + gap_title_desc + max_desc_h
        
    # Vertical bounds (between top brand tag bottom-edge and social handles top-edge)
    top_limit = line_y + 43
    bottom_limit = IG_SIZE[1] - 220
    
    # total footprint is badge (top overlaps card) + card padding + inner content + card padding
    card_padding_top = 40
    card_padding_bottom = 30
    total_footprint = (badge_h // 2) + card_padding_top + inner_content_h + card_padding_bottom
    
    # Center the entire footprint in available space
    start_y = top_limit + (bottom_limit - top_limit - total_footprint) // 2
    
    # ── Step 5: Glassmorphism Card Behind Text ──
    card_margin = 55
    card_top = start_y + badge_h // 2
    card_bottom = card_top + card_padding_top + inner_content_h + card_padding_bottom
    img = _draw_glassmorphism_card(img, draw, (card_margin, card_top, IG_SIZE[0] - card_margin, card_bottom), radius=35, opacity=45)
    draw = ImageDraw.Draw(img) # Refresh drawing context after alpha composite
    
    # White border around the card
    draw.rounded_rectangle([card_margin, card_top, IG_SIZE[0] - card_margin, card_bottom], radius=35, outline=(255, 255, 255, 180), width=2)
    
    # Brand Title ABOVE the card (centered perfectly on the white line)
    brand_font = _get_font(28, bold=True)
    brand_text = BRAND_NAME.upper()
    temp_bbox = draw.textbbox((0, 0), brand_text, font=brand_font, anchor="mm")
    brand_w = temp_bbox[2] - temp_bbox[0]
    bx, by = IG_SIZE[0] // 2, line_y
    draw.rectangle([bx - brand_w//2 - 20, by - 16, bx + brand_w//2 + 20, by + 18], fill=(30, 20, 30, 150), outline=(255, 255, 255, 230), width=2)
    draw.text((bx+2, by+2), brand_text, fill=(0,0,0,180), font=brand_font, anchor="mm")
    draw.text((bx, by), brand_text, fill=palette.get("accent", "#E69A0B"), font=brand_font, anchor="mm")

    # ── Step 6: Category badge (overlaps top edge of card) ──
    badge_y = start_y
    _draw_category_badge(draw, category, palette, y_pos=badge_y)
    
    # ── Step 7: Title — centered inside fixed boundary block ──
    title_block_y = card_top + card_padding_top
    title_y_offset = title_block_y + (max_title_h - title_total_h) // 2
    _draw_title_centered(draw, title_lines, title_y_offset, line_height=title_line_height)
    
    # ── Step 8: Meta description paragraph inside fixed boundary block ──
    if desc_lines:
        desc_block_y = title_block_y + max_title_h + gap_title_desc
        desc_y_offset = desc_block_y + (max_desc_h - desc_total_h) // 2
        _draw_description(draw, desc_lines, desc_y_offset, line_height=desc_line_height)

    # ── Step 9: Bottom branded bar ──
    _draw_bottom_bar(img, draw, palette, card_bottom)

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
