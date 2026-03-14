import os
import json
import time

articles_file = 'articles.json'
images_dir = 'images'

if not os.path.exists(articles_file):
    print("Error: articles.json not found.")
    exit(1)

with open(articles_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

articles = data.get('articles', [])
print(f"Checking images for {len(articles)} articles...")

missing = 0
not_updated = 0
updated = 0

current_time = time.time()
two_hours_ago = current_time - (2.5 * 3600) # Give 2.5 hours leeway

for article in articles:
    slug = article['slug']
    # Each article should have a cover and img1 to img5 (typically 6 images)
    # The filenames are slug-cover-TIMESTAMP.webp and slug-imgX-TIMESTAMP.webp
    
    # Let's find all images starting with the slug in the images directory
    slug_images = [f for f in os.listdir(images_dir) if f.startswith(f"{slug}-")]
    
    if len(slug_images) == 0:
        print(f"❌ '{slug}' has NO images in the directory!")
        missing += 1
        continue
        
    for img in slug_images:
        path = os.path.join(images_dir, img)
        mtime = os.path.getmtime(path)
        if mtime < two_hours_ago:
            print(f"⚠️ '{img}' was NOT regenerated (last modified {time.ctime(mtime)})")
            not_updated += 1
        else:
            updated += 1

print("\n--- Summary ---")
print(f"Total articles checked: {len(articles)}")
print(f"✅ Images successfully regenerated: {updated}")
print(f"⚠️ Images NOT regenerated (old timestamp): {not_updated}")
print(f"❌ Articles with missing images: {missing}")

if not_updated > 0 or missing > 0:
    print("\nAction needed: Some images were missed by the script.")
else:
    print("\nSUCCESS: All images have been successfully touched/regenerated in the last 2 hours.")
