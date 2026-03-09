import os
import glob
import json

PROJECT_ROOT = r"c:\Users\Omar\Desktop\little-smart-genius-site\Nouveau dossier\online\Little_Smart_Genius"

def clean_blog_data():
    print("Starting factory reset of blog data...")

    # 1. Delete all HTML articles
    articles_dir = os.path.join(PROJECT_ROOT, "articles")
    html_files = glob.glob(os.path.join(articles_dir, "*.html"))
    for f in html_files:
        os.remove(f)
    print(f"Deleted {len(html_files)} HTML articles from /articles/")

    # 2. Delete archived JSON posts
    archive_dir = os.path.join(PROJECT_ROOT, "data", "archive_posts")
    json_archives = glob.glob(os.path.join(archive_dir, "*.json"))
    for f in json_archives:
        os.remove(f)
    print(f"Deleted {len(json_archives)} JSON archives from /data/archive_posts/")

    # 3. Delete active JSON posts (if any)
    posts_dir = os.path.join(PROJECT_ROOT, "posts")
    if os.path.exists(posts_dir):
        json_posts = glob.glob(os.path.join(posts_dir, "*.json"))
        for f in json_posts:
            os.remove(f)
        print(f"Deleted {len(json_posts)} JSON posts from /posts/")

    # 4. Delete article images
    # Convention: [slug]-cover.webp, [slug]-img1.webp, etc.
    images_dir = os.path.join(PROJECT_ROOT, "images")
    if os.path.exists(images_dir):
        img_files = glob.glob(os.path.join(images_dir, "*-cover.webp")) + \
                    glob.glob(os.path.join(images_dir, "*-img*.webp")) + \
                    glob.glob(os.path.join(images_dir, "*-cover.png")) + \
                    glob.glob(os.path.join(images_dir, "*-img*.png")) + \
                    glob.glob(os.path.join(images_dir, "*-cover.jpg")) + \
                    glob.glob(os.path.join(images_dir, "*-img*.jpg"))
        
        # Deduplicate list just in case
        img_files = list(set(img_files))
        for f in img_files:
            # Safely avoid deleting static assets by checking the pattern
            basename = os.path.basename(f)
            if "-cover" in basename or "-img" in basename:
                os.remove(f)
        print(f"Deleted {len(img_files)} article images from /images/")

    # 5. Reset used_topics.json
    used_topics_path = os.path.join(PROJECT_ROOT, "data", "used_topics.json")
    if os.path.exists(used_topics_path):
        reset_data = {
            "keyword": [],
            "product": [],
            "freebie": [],
            "daily_log": []
        }
        with open(used_topics_path, 'w', encoding='utf-8') as f:
            json.dump(reset_data, f, indent=4)
    # 6. Clear index files
    idx1 = os.path.join(PROJECT_ROOT, "articles.json")
    idx2 = os.path.join(PROJECT_ROOT, "search_index.json")
    if os.path.exists(idx1):
        os.remove(idx1)
        print("Deleted articles.json")
    if os.path.exists(idx2):
        os.remove(idx2)
        print("Deleted search_index.json")

    print("\nCleanup complete! You can now run the generation script to start fresh.")

if __name__ == "__main__":
    clean_blog_data()
