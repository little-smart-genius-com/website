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

# 2. Extract referenced images from HTML
referenced_images = set()

# Pre-add static known images to prevent deletion
referenced_images.update([
    'logo.png', 'favicon.ico', 'placeholder.jpg', 'default-og.jpg',
    'hero-bg.jpg', 'about-bg.jpg', 'missing-image.webp', 'icon-kids.png', 'instagram-icon.png',
    'logo.webp', 'little-smart-genius-logo.webp'
])

for html_file in glob.glob(os.path.join(articles_dir, '*.html')):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
        # Find all src="..." and href="..."
        matches = re.findall(r'(?:src|href)=[\"\'\']/images/([^\"\']+)', content)
        for match in matches:
            referenced_images.add(os.path.basename(match))

# 3. Find candidates for deletion
all_images = []
for root, _, files in os.walk(images_dir):
    for f in files:
        all_images.append(os.path.join(root, f))

to_delete = []
for img_path in all_images:
    basename = os.path.basename(img_path)
    
    # Don't delete from og/ unless it's orphaned
    if 'images\\og' in img_path or 'images/og' in img_path:
        if basename.endswith('.jpg'):
            slug = basename[:-4]
            if slug not in valid_slugs and slug != 'default-og':
                to_delete.append(img_path)
        continue

    # Keep exactly referenced images
    if basename in referenced_images:
        continue
        
    # Keep dynamic images for active slugs (just in case they aren't directly referenced in HTML but exist in DB)
    is_valid_dynamic = False
    for slug in valid_slugs:
        if basename.startswith(f"{slug}-cover-") or basename.startswith(f"{slug}-img"):
            is_valid_dynamic = True
            break
            
    if not is_valid_dynamic:
        to_delete.append(img_path)

print(f"Total images found: {len(all_images)}")
print(f"Total referenced natively: {len(referenced_images)}")
print(f"Total to delete: {len(to_delete)}")
if to_delete:
    print(f"First 10 to delete: {to_delete[:10]}")
    
with open('to_delete.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(to_delete))

