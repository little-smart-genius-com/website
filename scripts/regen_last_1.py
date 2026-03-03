"""Regenerate the ONE last missing keyword article."""
import os, sys, time
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

from auto_blog_v6_ultimate import generate_article_v6, TopicSelector
from PIL import Image

IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
THUMBS_DIR = os.path.join(IMAGES_DIR, "thumbs")

print("=" * 70)
print("  REGENERATING LAST MISSING ARTICLE")
print("=" * 70)

ts = TopicSelector()

topic = {
    "slot": "keyword",
    "topic_name": "spot the difference puzzles for kids printable",
    "category": "Visual Skills",
    "keywords": "spot the difference, visual perception, observation skills, attention to detail, picture puzzles, find differences, brain games, focus activities, visual discrimination, cognitive development",
    "product_data": None,
}

try:
    result = generate_article_v6("keyword", topic, ts)
    if result:
        print(f"\n  [OK] Article saved: {result['title'][:60]}")
        print(f"  Words: {result.get('word_count', 0)}")
        
        # Generate thumbnail
        cover = result.get("image_path", "")
        if cover and not cover.startswith("http"):
            cover_path = os.path.join(PROJECT_ROOT, cover)
            if os.path.exists(cover_path):
                cover_fn = os.path.basename(cover_path)
                thumb_path = os.path.join(THUMBS_DIR, cover_fn)
                try:
                    img = Image.open(cover_path)
                    img.thumbnail((480, 270))
                    img.save(thumb_path, "WEBP", quality=80, optimize=True, method=6)
                    print(f"  [OK] Thumbnail: {cover_fn}")
                except Exception as e:
                    print(f"  [ERR] Thumb: {e}")
    else:
        print("\n  [FAIL] Article generation failed")
except Exception as e:
    print(f"\n  [ERROR] {e}")
    import traceback
    traceback.print_exc()

# Rebuild HTML
print("\n  Rebuilding HTML articles...")
build_script = os.path.join(SCRIPT_DIR, "build_articles.py")
os.system(f'python "{build_script}"')

# Final count
import glob
post_count = len(glob.glob(os.path.join(PROJECT_ROOT, "posts", "*.json")))
article_count = len(glob.glob(os.path.join(PROJECT_ROOT, "articles", "*.html")))
image_count = len(glob.glob(os.path.join(IMAGES_DIR, "*.webp")))
thumb_count = len(glob.glob(os.path.join(THUMBS_DIR, "*.webp")))

print(f"\n{'=' * 70}")
print(f"  FINAL STATUS")
print(f"{'=' * 70}")
print(f"  Posts:      {post_count}/18")
print(f"  Articles:   {article_count}/18")
print(f"  Images:     {image_count}")
print(f"  Thumbnails: {thumb_count}")
print(f"{'=' * 70}")
