import os
import json
import subprocess
import time

articles_file = 'articles.json'
images_dir = 'images'

with open(articles_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

articles = data.get('articles', [])
two_hours_ago = time.time() - (3 * 3600)

slugs_to_regen = set()

for article in articles:
    slug = article['slug']
    slug_images = [f for f in os.listdir(images_dir) if f.startswith(f"{slug}-cover") or f.startswith(f"{slug}-img")]
    
    if len(slug_images) == 0:
        slugs_to_regen.add(slug)
        continue
        
    for img in slug_images:
        path = os.path.join(images_dir, img)
        mtime = os.path.getmtime(path)
        if mtime < two_hours_ago:
            slugs_to_regen.add(slug)
            break

print(f"Found {len(slugs_to_regen)} articles that need regeneration.")

# Copy the corresponding JSON files to posts/
if not os.path.exists('posts'):
    os.makedirs('posts')

for slug in slugs_to_regen:
    # Find matching JSON in archive
    archives = [f for f in os.listdir("data/archive_posts") if f.startswith(slug) and f.endswith(".json")]
    if archives:
        # Get the newest one
        newest = max(archives, key=lambda f: os.path.getmtime(os.path.join("data/archive_posts", f)))
        import shutil
        shutil.copy2(os.path.join("data/archive_posts", newest), os.path.join("posts", newest))
        print(f"Prepared {newest} for regeneration.")

print("\nStarting regeneration for missing/outdated articles...")
if slugs_to_regen:
    # Run fix_images.py for the prepared posts
    subprocess.run(["python", "scripts/fix_images.py", "--force", "--model", "zimage"])
    print("Regeneration complete!")
else:
    print("Everything is up to date!")
