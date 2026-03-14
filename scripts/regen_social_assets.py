import os
import json
from PIL import Image
import sys

# Import the Instagram generator
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from instagram_generator import generate_instagram_post
from generate_og_images import create_og_image, _load_font

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
OG_DIR = os.path.join(IMAGES_DIR, "og")
INSTAGRAM_DIR = os.path.join(PROJECT_ROOT, "instagram")

os.makedirs(OG_DIR, exist_ok=True)
os.makedirs(INSTAGRAM_DIR, exist_ok=True)

def regenerate_all():
    print("="*60)
    print("  SOCIAL ASSETS REGENERATOR (OG + INSTAGRAM)")
    print("="*60)
    
    index_file = os.path.join(PROJECT_ROOT, "search_index.json")
    if not os.path.exists(index_file):
        print("Error: search_index.json not found.")
        return
        
    with open(index_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    articles = data.get("articles", [])
    print(f"Found {len(articles)} active articles in search_index.json.\n")
    
    # Load fonts for the OG Generator exactly as it expects
    fonts = {
        "badge":   _load_font("bold", 18),
        "excerpt": _load_font("regular", 23),
        "brand":   _load_font("semibold", 22),
        "url":     _load_font("semibold", 20),
    }

    og_count = 0
    ig_count = 0
    
    for i, article in enumerate(articles, 1):
        slug = article.get("slug", "")
        print(f"[{i:2d}/{len(articles)}] Processing: {slug}")
        
        # Determine the cover image
        image_rel = article.get("image", "")
        if image_rel.startswith("images/"):
            cover_path = os.path.join(PROJECT_ROOT, image_rel.replace("/", os.sep))
        else:
            # Fallback based on slug
            cover_path = os.path.join(IMAGES_DIR, f"{slug}-cover.webp")
            
        if not os.path.exists(cover_path):
            print(f"  ❌ Cover image not found: {cover_path}")
            continue
            
        # 1. Generate OG image using the Premium V4 template
        try:
            # create_og_image handles its own saving inside the og/ folder and returns path
            og_out = create_og_image(article, fonts, force=True)
            if og_out:
                og_count += 1
                print("  ✅ OG Image Generated (Premium V4 Template)")
        except Exception as e:
            print(f"  ❌ Error generating OG: {e}")
            
        # 2. Generate Instagram Post
        try:
            ig_result = generate_instagram_post(article, cover_image_path=cover_path, output_dir=INSTAGRAM_DIR)
            if ig_result:
                ig_count += 1
                caption_file = os.path.basename(ig_result['caption_path'])
                print(f"  ✅ Instagram Post Generated ({caption_file})")
            else:
                print("  ❌ Failed to generate Instagram post")
        except Exception as e:
            print(f"  ❌ Exception during Instagram generation: {e}")
            
    print("="*60)
    print(f"DONE! Generated {og_count} OG images and {ig_count} Instagram posts.")
    print("="*60)

if __name__ == "__main__":
    regenerate_all()
