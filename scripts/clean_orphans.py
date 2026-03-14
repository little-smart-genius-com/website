"""
Safe cleanup: remove orphaned article images and extra thumbnails.
NEVER touches: products-thumbs, banners, og
"""
import os, json, re, glob

IMAGES_DIR = 'images'
THUMBS_DIR = os.path.join(IMAGES_DIR, 'thumbs')
ARTICLES_DIR = 'articles'

# ── 1. Collect every image referenced by any HTML article ──────────────
referenced = set()

for html_file in glob.glob(os.path.join(ARTICLES_DIR, '*.html')):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    # Match ../images/X or /images/X
    for m in re.findall(r'(?:src|content)=["\'](?:\.\./)?(?:/)?images/([^"\'?#]+)', content):
        referenced.add(m)  # e.g. "slug-cover-123.webp" or "thumbs/slug-cover-123.webp"

# Also scan blog pages & static pages for image references
for html_file in glob.glob('*.html'):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    for m in re.findall(r'(?:src|content)=["\'](?:\.\./)?(?:/)?images/([^"\'?#]+)', content):
        referenced.add(m)

print(f"Total unique image references found in HTML: {len(referenced)}")

# ── 2. Get the set of valid cover filenames (for thumbnail matching) ───
valid_covers = set()
for ref in referenced:
    basename = os.path.basename(ref)
    if '-cover-' in basename:
        valid_covers.add(basename)

print(f"Valid cover images found: {len(valid_covers)}")

# ── 3. Clean up root images/ (article images & covers only) ───────────
PROTECTED_DIRS = {'products-thumbs', 'banners', 'thumbs', 'og'}
deleted_images = 0

for f in os.listdir(IMAGES_DIR):
    full_path = os.path.join(IMAGES_DIR, f)
    
    # Skip directories
    if os.path.isdir(full_path):
        continue
    
    # Check if this file is referenced
    if f in referenced:
        continue
    
    # Check if it's a known static asset (logos, icons etc)
    if f in {'logo.webp', 'little-smart-genius-logo.webp', 'favicon.ico', 
             'placeholder.jpg', 'hero-bg.jpg', 'about-bg.jpg', 'missing-image.webp',
             'icon-kids.png', 'instagram-icon.png', 'logo.png', 'default-og.jpg'}:
        continue

    # It's orphaned — delete it
    os.remove(full_path)
    print(f"  🗑️ Deleted orphan: {f}")
    deleted_images += 1

print(f"\nDeleted {deleted_images} orphaned images from images/")

# ── 4. Clean up thumbs/ — keep only thumbnails for valid covers ────────
deleted_thumbs = 0
kept_thumbs = 0

if os.path.exists(THUMBS_DIR):
    for f in os.listdir(THUMBS_DIR):
        full_path = os.path.join(THUMBS_DIR, f)
        if os.path.isdir(full_path):
            continue
        
        # A valid thumbnail must correspond to a valid cover
        if f in valid_covers:
            kept_thumbs += 1
        else:
            os.remove(full_path)
            print(f"  🗑️ Deleted orphan thumb: {f}")
            deleted_thumbs += 1

print(f"\nThumbnails: kept {kept_thumbs}, deleted {deleted_thumbs}")

# ── 5. Final counts ───────────────────────────────────────────────────
remaining_images = len([f for f in os.listdir(IMAGES_DIR) if os.path.isfile(os.path.join(IMAGES_DIR, f))])
remaining_thumbs = len(os.listdir(THUMBS_DIR)) if os.path.exists(THUMBS_DIR) else 0
products_count = len(os.listdir(os.path.join(IMAGES_DIR, 'products-thumbs'))) if os.path.exists(os.path.join(IMAGES_DIR, 'products-thumbs')) else 0
banners_count = len(os.listdir(os.path.join(IMAGES_DIR, 'banners'))) if os.path.exists(os.path.join(IMAGES_DIR, 'banners')) else 0

print(f"\n{'='*50}")
print(f"  CLEANUP COMPLETE")
print(f"{'='*50}")
print(f"  Root images/:        {remaining_images} files")
print(f"  Thumbnails:          {remaining_thumbs} files")
print(f"  Products-thumbs:     {products_count} files (untouched)")
print(f"  Banners:             {banners_count} files (untouched)")
print(f"  Total deleted:       {deleted_images + deleted_thumbs}")
