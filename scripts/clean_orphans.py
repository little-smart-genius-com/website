import os
import glob
import json
import re

images_dir = 'images'
og_dir = os.path.join(images_dir, 'og')
articles_dir = 'articles'

# 1. Get valid slugs
with open('articles.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    valid_slugs = set(a['slug'] for a in data.get('articles', []))

# 2. Extract explicitly referenced images from HTML
referenced_images = set()

for html_file in glob.glob(os.path.join(articles_dir, '*.html')):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
        # Find all src="..." and href="..."
        matches = re.findall(r'(?:src|href)=[\"\'](\/?images/[^\"\']+)', content)
        for match in matches:
            referenced_images.add(os.path.basename(match))

# Pre-add static known images
referenced_images.update([
    'logo.png', 'favicon.ico', 'placeholder.jpg', 'default-og.jpg',
    'hero-bg.jpg', 'about-bg.jpg', 'missing-image.webp', 'icon-kids.png', 'instagram-icon.png',
    'logo.webp', 'little-smart-genius-logo.webp'
])

# 3. Find candidates for deletion
# PROTECTED: Never delete from these subdirectories
PROTECTED_DIRS = {'products-thumbs', 'banners', 'thumbs', 'og'}

to_delete = []
for root, _, files in os.walk(images_dir):
    # Skip any protected subdirectory entirely
    dir_name = os.path.basename(root)
    if dir_name in PROTECTED_DIRS:
        continue

    for f in files:
        img_path = os.path.join(root, f)
        basename = os.path.basename(img_path)
        
        # Don't delete from og/ unless it's orphaned (legacy check)
        if 'og' in root:
            if basename.endswith('.jpg'):
                slug = basename[:-4]
                if slug not in valid_slugs and slug != 'default-og':
                    to_delete.append(img_path)
            continue

        # Keep explicitly referenced images
        if basename in referenced_images:
            continue
            
        # Keep dynamic images for active slugs
        is_valid_dynamic = False
        for slug in valid_slugs:
            if basename.startswith(f"{slug}-cover-") or basename.startswith(f"{slug}-img"):
                is_valid_dynamic = True
                break
                
        if not is_valid_dynamic:
            to_delete.append(img_path)

print(f"Deleting {len(to_delete)} orphaned images...")
for path in to_delete:
    try:
        os.remove(path)
        print(f" Deleted: {path}")
    except Exception as e:
        print(f" Error deleting {path}: {e}")

# Clean up logs
print("\nCleaning up logs directory...")
logs_dir = "logs"
if os.path.exists(logs_dir):
    for f in os.listdir(logs_dir):
        if f.endswith(".json"):
            path = os.path.join(logs_dir, f)
            os.remove(path)
            print(f" Deleted log: {path}")
