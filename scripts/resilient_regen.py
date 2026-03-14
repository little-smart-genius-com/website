"""
Resilient targeted regeneration script.
- Only processes articles whose images are missing or outdated.
- Processes ONE article at a time via fix_images.py --slug X --force --model zimage
- After each article, re-checks status and continues.
"""
import os, json, time, subprocess, shutil, sys

IMAGES_DIR = 'images'
ARCHIVE_DIR = 'data/archive_posts'
POSTS_DIR = 'posts'
ARTICLES_FILE = 'articles.json'
CUTOFF_HOURS = 4  # Images older than this many hours are considered outdated

def get_outdated_slugs():
    """Return list of slugs whose images are missing or outdated."""
    with open(ARTICLES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    articles = data.get('articles', [])
    cutoff = time.time() - (CUTOFF_HOURS * 3600)
    outdated = []
    
    for article in articles:
        slug = article['slug']
        # Find images for this slug
        slug_images = [f for f in os.listdir(IMAGES_DIR)
                       if f.startswith(f"{slug}-cover") or f.startswith(f"{slug}-img")]
        
        if len(slug_images) == 0:
            outdated.append(slug)
            continue
        
        # Check if any image is old
        for img in slug_images:
            path = os.path.join(IMAGES_DIR, img)
            if os.path.getmtime(path) < cutoff:
                outdated.append(slug)
                break
    
    return outdated

def prepare_slug(slug):
    """Copy the archive JSON for this slug into posts/."""
    os.makedirs(POSTS_DIR, exist_ok=True)
    # Clear posts dir first
    for f in os.listdir(POSTS_DIR):
        os.remove(os.path.join(POSTS_DIR, f))
    
    archives = [f for f in os.listdir(ARCHIVE_DIR) 
                if f.startswith(slug) and f.endswith('.json')]
    if archives:
        newest = max(archives, key=lambda f: os.path.getmtime(os.path.join(ARCHIVE_DIR, f)))
        shutil.copy2(os.path.join(ARCHIVE_DIR, newest), os.path.join(POSTS_DIR, newest))
        return True
    return False

def main():
    total_processed = 0
    
    while True:
        outdated = get_outdated_slugs()
        if not outdated:
            print(f"\n{'='*60}")
            print(f"  ✅ ALL DONE! All 35 articles have fresh images.")
            print(f"  Total articles processed in this run: {total_processed}")
            print(f"{'='*60}")
            break
        
        slug = outdated[0]
        remaining = len(outdated)
        print(f"\n{'='*60}")
        print(f"  [{remaining} remaining] Processing: {slug}")
        print(f"{'='*60}")
        
        if not prepare_slug(slug):
            print(f"  ❌ No archive found for {slug}, skipping.")
            continue
        
        # Run fix_images.py for just this one slug
        result = subprocess.run(
            ["python", "scripts/fix_images.py", "--slug", slug, "--force", "--model", "zimage"],
            timeout=600  # 10 minute timeout per article
        )
        
        if result.returncode == 0:
            total_processed += 1
            print(f"  ✅ Done with {slug}")
        else:
            print(f"  ⚠️ fix_images.py returned code {result.returncode} for {slug}")
            total_processed += 1  # Still count it, verification will catch failures

if __name__ == '__main__':
    main()
