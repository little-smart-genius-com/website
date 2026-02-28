import os
import json
import textwrap
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "search_index.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "images", "og")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Load fonts (Windows specific paths)
try:
    font_title = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 64)
    font_text = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", 32)
    font_bold = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 36)
except IOError:
    print("Warning: Segoe UI font not found. Using default PIL font.")
    font_title = ImageFont.load_default()
    font_text = ImageFont.load_default()
    font_bold = ImageFont.load_default()

def create_og_image(article):
    title = article.get("title", "Little Smart Genius")
    slug = article.get("slug", "default")
    category = article.get("category", "Blog")
    excerpt = article.get("excerpt", "Discover amazing educational resources for kids.")
    
    if len(excerpt) > 110:
        excerpt = excerpt[:107] + "..."

    # 1200x630 standard OpenGraph size
    img = Image.new("RGB", (1200, 630), color="#1e293b")
    draw = ImageDraw.Draw(img)
    
    # Draw simple gradient/shapes for branding
    # Orange brand strip at the bottom
    draw.rectangle([(0, 610), (1200, 630)], fill="#F48C06")
    # Soft background decoration
    draw.ellipse([(-200, -200), (300, 300)], fill="#334155")
    draw.ellipse([(1000, 400), (1400, 800)], fill="#334155")
    
    # Branding
    draw.text((60, 60), "Little Smart Genius.", fill="#FFFFFF", font=font_bold)
    
    # Category badge
    cat_text = category.upper()
    try:
        cat_w = draw.textlength(cat_text, font=font_text)
    except AttributeError:
        cat_w = len(cat_text) * 20 # Fallback for older Pillow versions
        
    draw.rectangle([(1140 - cat_w - 40, 50), (1140, 110)], fill="#F48C06")
    draw.text((1140 - cat_w - 20, 65), cat_text, fill="#FFFFFF", font=font_text)
    
    # Title (Wrapped)
    # 30 chars per line for a 64px font should fit nicely in 1200px width
    wrapped_title = textwrap.wrap(title, width=32)
    y_text = 200
    for line in wrapped_title:
        draw.text((60, y_text), line, fill="#F8FAFC", font=font_title)
        y_text += 80
        
    # Excerpt (Hook)
    draw.text((60, y_text + 40), excerpt, fill="#94A3B8", font=font_text)
    
    out_path = os.path.join(OUTPUT_DIR, f"{slug}.jpg")
    img.save(out_path, quality=90)
    return out_path

def main():
    if not os.path.exists(INDEX_PATH):
        print(f"Error: Could not find {INDEX_PATH}")
        return
        
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    articles = data.get("articles", [])
    print(f"Generating {len(articles)} OpenGraph images...")
    
    count = 0
    for art in articles:
        try:
            out = create_og_image(art)
            print(f"  [OK]  {os.path.basename(out)}")
            count += 1
        except Exception as e:
            print(f"  [ERR] Failed for {art.get('slug')}: {e}")
            
    print(f"\\nSuccessfully generated {count} OG images!")

if __name__ == "__main__":
    main()
