import os
import json
from PIL import Image
import sys

# Import the Instagram generator
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from instagram_generator import generate_instagram_post

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
OG_DIR = os.path.join(IMAGES_DIR, "og")
INSTAGRAM_DIR = os.path.join(PROJECT_ROOT, "instagram")

os.makedirs(OG_DIR, exist_ok=True)
os.makedirs(INSTAGRAM_DIR, exist_ok=True)

def generate_og_image(slug, cover_path):
    """Generate a 1200x630 OG image from the cover image by cropping the center."""
    og_path = os.path.join(OG_DIR, f"{slug}.jpg")
    try:
        with Image.open(cover_path) as img:
            img = img.convert("RGB")
            # Covers are 1200x675. We need 1200x630.
            width, height = img.size
            target_width, target_height = 1200, 630
            
            if width == target_width and height == target_height:
                img.save(og_path, "JPEG", quality=90)
                return True
                
            # Resize exactly to 1200 width if not already
            if width != target_width:
                aspect = height / width
                new_height = int(target_width * aspect)
                img = img.resize((target_width, new_height), Image.LANCZOS)
                width, height = img.size
                
            # Crop to 630 height
            top = (height - target_height) // 2
            bottom = top + target_height
            img = img.crop((0, top, target_width, bottom))
            img.save(og_path, "JPEG", quality=90)
        return True
    except Exception as e:
        print(f"Error generating OG for {slug}: {e}")
        return False

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
            
        # 1. Generate OG image
        if generate_og_image(slug, cover_path):
            og_count += 1
            print("  ✅ OG Image Generated")
            
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
