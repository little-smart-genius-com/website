import os
import json
import glob
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

def optimize_thumbnail(image_path: str, max_width: int = 600) -> str:
    """Creates a thumbnail image strictly for cover images."""
    if not PIL_AVAILABLE:
        print("[Error] Pillow not installed, cannot generate thumbnail.")
        return None
    
    if not os.path.exists(image_path):
        print(f"[Warning] Image not found: {image_path}")
        return None
        
    try:
        # Prevent double-thumbing: if the image passed IS a thumb, skip
        if "-thumb" in image_path:
            return image_path
            
        base_name, ext = os.path.splitext(image_path)
        thumb_path = f"{base_name}-thumb{ext}"
        
        # Open source image
        img = Image.open(image_path)
        
        # Only resize if larger
        if img.width > max_width:
            aspect_ratio = img.height / img.width
            new_height = int(max_width * aspect_ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)
            
        # Save as webp
        img.save(thumb_path, "WEBP", quality=85, optimize=True)
        print(f"[OK] Generated thumbnail: {thumb_path}")
        return thumb_path
        
    except Exception as e:
        print(f"[Error] Failed to process {image_path}: {str(e)}")
        return None

def process_all_covers():
    posts = glob.glob('posts/*.json')
    print(f"Found {len(posts)} posts. Generating cover thumbnails...")
    
    generated = 0
    for post_file in posts:
        try:
            with open(post_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Only generate thumbnails for the main cover image
            cover = data.get('image', '')
            if cover and cover.startswith('images/'):
                thumb = optimize_thumbnail(cover)
                if thumb:
                    generated += 1
        except Exception as e:
            print(f"Failed parsing {post_file}: {e}")
            
    print(f"\nDone! Processed {generated} cover images.")

if __name__ == "__main__":
    process_all_covers()
