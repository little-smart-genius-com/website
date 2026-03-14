"""Generate missing thumbnails for covers that don't have them."""
import os, re, glob
from PIL import Image

IMAGES_DIR = 'images'
THUMBS_DIR = os.path.join(IMAGES_DIR, 'thumbs')
ARTICLES_DIR = 'articles'

os.makedirs(THUMBS_DIR, exist_ok=True)

# Get all cover images referenced in HTML
covers = set()
for html_file in glob.glob(os.path.join(ARTICLES_DIR, '*.html')):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    for m in re.findall(r'src=["\'](?:\.\./)?(?:/)?images/([^"\'?#]+)', content):
        basename = os.path.basename(m)
        if '-cover-' in basename:
            covers.add(basename)

# Also check blog listing pages
for html_file in glob.glob('blog*.html'):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    for m in re.findall(r'src=["\'](?:\.\./)?(?:/)?images/(?:thumbs/)?([^"\'?#]+)', content):
        basename = os.path.basename(m)
        if '-cover-' in basename:
            covers.add(basename)

existing_thumbs = set(os.listdir(THUMBS_DIR))
missing = covers - existing_thumbs

print(f"Total covers referenced: {len(covers)}")
print(f"Existing thumbnails: {len(existing_thumbs)}")
print(f"Missing thumbnails: {len(missing)}")

for cover_name in sorted(missing):
    src = os.path.join(IMAGES_DIR, cover_name)
    dst = os.path.join(THUMBS_DIR, cover_name)
    
    if not os.path.exists(src):
        print(f"  ⚠️ Source cover not found: {cover_name}")
        continue
    
    try:
        img = Image.open(src)
        # Resize to 400px wide, maintaining aspect ratio
        w, h = img.size
        new_w = 400
        new_h = int(h * (new_w / w))
        img = img.resize((new_w, new_h), Image.LANCZOS)
        img.save(dst, 'WEBP', quality=75)
        size_kb = os.path.getsize(dst) // 1024
        print(f"  ✅ Created thumbnail: {cover_name} ({size_kb}KB)")
    except Exception as e:
        print(f"  ❌ Error creating thumbnail for {cover_name}: {e}")

final_count = len(os.listdir(THUMBS_DIR))
print(f"\nFinal thumbnail count: {final_count}")
