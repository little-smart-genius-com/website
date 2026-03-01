"""
Fix broken image references:
1. Generate missing thumbnails from existing full-size images
2. Update placeholder.webp to use a nearby existing image (or generate one)
"""
import os, re, glob, shutil
from PIL import Image

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_DIR = os.path.join(PROJECT, "articles")
IMAGES_DIR = os.path.join(PROJECT, "images")
THUMBS_DIR = os.path.join(IMAGES_DIR, "thumbs")

os.makedirs(THUMBS_DIR, exist_ok=True)

# === STEP 1: Find all missing thumbnails and generate from full-size ===
print("=" * 60)
print("STEP 1: Fix missing thumbnails")
print("=" * 60)

thumbs_fixed = 0
thumbs_missing = 0

for fp in sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html"))):
    with open(fp, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Find all thumbnail references
    thumb_refs = re.findall(r'src="(\.\./images/thumbs/[^"]+)"', html)
    
    for ref in thumb_refs:
        thumb_rel = ref.replace("../", "")
        thumb_path = os.path.join(PROJECT, thumb_rel)
        
        if os.path.exists(thumb_path):
            continue  # Already exists
        
        # Try to find the full-size version
        thumb_basename = os.path.basename(thumb_path)
        full_path = os.path.join(IMAGES_DIR, thumb_basename)
        
        if os.path.exists(full_path):
            # Generate thumbnail from full-size
            try:
                img = Image.open(full_path)
                img.thumbnail((480, 270))
                img.save(thumb_path, "WEBP", quality=80, optimize=True)
                size_kb = os.path.getsize(thumb_path) // 1024
                print(f"  [THUMB] Created ({size_kb}KB): {thumb_basename[:60]}")
                thumbs_fixed += 1
            except Exception as e:
                print(f"  [ERR] Failed to create thumb: {thumb_basename[:40]} - {e}")
                thumbs_missing += 1
        else:
            # Full-size doesn't exist either
            thumbs_missing += 1
            print(f"  [MISS] No full-size source: {thumb_basename[:60]}")

print(f"\nThumbnails fixed: {thumbs_fixed}")
print(f"Thumbnails still missing: {thumbs_missing}")

# === STEP 2: Fix placeholder.webp references ===
print("\n" + "=" * 60)
print("STEP 2: Fix placeholder.webp references")
print("=" * 60)

placeholder_fixed = 0

for fp in sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html"))):
    slug = os.path.basename(fp).replace(".html", "")
    with open(fp, "r", encoding="utf-8") as f:
        html = f.read()
    
    if "../images/placeholder.webp" not in html:
        continue
    
    # Find all real article images for this article (not placeholder)
    real_imgs = re.findall(r"src='(\.\./images/[^']*" + re.escape(slug[:30]) + r"[^']*\.webp)'", html)
    if not real_imgs:
        # Try broader match - any image in the article
        real_imgs = re.findall(r"src='(\.\./images/[^']*img[^']*\.webp)'", html)
    
    if real_imgs:
        # Use the 4th image as template to find a related image
        # The placeholder is typically img5 position
        last_good = real_imgs[-1]  # Last valid image
        last_basename = os.path.basename(last_good)
        
        # Try to find an img5 or similar file
        # Get the slug/prefix from the last good image
        prefix_match = re.match(r'(.+?-img)\d+(-\d+\.webp)', last_basename)
        if prefix_match:
            prefix = prefix_match.group(1)
            suffix = prefix_match.group(2)
            # Look for img5 with any timestamp
            potential_img5 = glob.glob(os.path.join(IMAGES_DIR, f"{prefix}5-*.webp"))
            if not potential_img5:
                # Try the img4 with same timestamp as fallback - duplicate it as img5
                img4_path = os.path.join(IMAGES_DIR, last_basename)
                if os.path.exists(img4_path):
                    # Copy img4 as a temporary fix (better than placeholder)
                    img5_name = f"{prefix}5{suffix}"
                    img5_path = os.path.join(IMAGES_DIR, img5_name)
                    shutil.copy2(img4_path, img5_path)
                    potential_img5 = [img5_path]
                    print(f"  [CLONE] Created img5 from img4: {img5_name[:60]}")
            
            if potential_img5:
                new_img_path = f"../images/{os.path.basename(potential_img5[0])}"
                html = html.replace("../images/placeholder.webp", new_img_path)
                
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(html)
                
                placeholder_fixed += 1
                print(f"  [FIX] {slug[:40]} -> {os.path.basename(potential_img5[0])[:40]}")
            else:
                print(f"  [SKIP] No replacement found for {slug[:40]}")
        else:
            print(f"  [SKIP] Can't parse image pattern for {slug[:40]}")
    else:
        print(f"  [SKIP] No real images found in {slug[:40]}")

print(f"\nPlaceholder references fixed: {placeholder_fixed}")

# === STEP 3: Final verification ===
print("\n" + "=" * 60)
print("STEP 3: Verification")
print("=" * 60)

total_broken = 0
for fp in sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html"))):
    slug = os.path.basename(fp).replace(".html", "")
    with open(fp, "r", encoding="utf-8") as f:
        html = f.read()
    
    imgs = re.findall(r'src=["\'](\.\./images/[^"\']+)["\']', html)
    broken = []
    for src in imgs:
        clean = src.replace("../", "")
        full = os.path.join(PROJECT, clean)
        if not os.path.exists(full):
            broken.append(src)
    
    if broken:
        total_broken += len(broken)
        print(f"  [{slug[:45]}] {len(broken)} still broken")

print(f"\nTotal remaining broken: {total_broken}")
