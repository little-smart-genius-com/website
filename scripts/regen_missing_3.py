"""
REGENERATE 3 MISSING + THUMBNAILS
Generates thumbnails for existing articles, then regenerates the 3 failed keyword articles.
"""
import os, sys, glob, json, time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

from PIL import Image

IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
THUMBS_DIR = os.path.join(IMAGES_DIR, "thumbs")
POSTS_DIR = os.path.join(PROJECT_ROOT, "posts")

os.makedirs(THUMBS_DIR, exist_ok=True)

# ===================================================================
# STEP 1: Generate thumbnails for all existing cover images
# ===================================================================
print("=" * 70)
print("  STEP 1: GENERATE THUMBNAILS FOR EXISTING COVERS")
print("=" * 70)

posts = sorted(glob.glob(os.path.join(POSTS_DIR, "*.json")))
thumb_count = 0

for pf in posts:
    with open(pf, 'r', encoding='utf-8') as f:
        data = json.load(f)
    cover = data.get("image", "")
    if cover and not cover.startswith("http"):
        cover_path = os.path.join(PROJECT_ROOT, cover)
        if os.path.exists(cover_path):
            cover_fn = os.path.basename(cover_path)
            thumb_path = os.path.join(THUMBS_DIR, cover_fn)
            if not os.path.exists(thumb_path):
                try:
                    img = Image.open(cover_path)
                    img.thumbnail((480, 270))
                    img.save(thumb_path, "WEBP", quality=80, optimize=True, method=6)
                    thumb_count += 1
                    print(f"  [OK] Thumb: {cover_fn}")
                except Exception as e:
                    print(f"  [ERR] {cover_fn}: {e}")
            else:
                print(f"  [SKIP] {cover_fn} (exists)")

print(f"\n  Generated {thumb_count} thumbnails\n")

# ===================================================================
# STEP 2: Regenerate the 3 missing keyword articles
# ===================================================================
print("=" * 70)
print("  STEP 2: REGENERATE 3 MISSING KEYWORD ARTICLES")
print("=" * 70)

from auto_blog_v6_ultimate import generate_article_v6, TopicSelector

MISSING_TOPICS = [
    {
        "topic_name": "shadow matching worksheets for toddlers",
        "category": "Visual Skills",
        "keywords": "shadow matching, visual discrimination, toddler activities, matching worksheets, shape recognition, visual perception, preschool worksheets, cognitive skills, fine motor, early learning",
    },
    {
        "topic_name": "word search puzzles for kids vocabulary building",
        "category": "Word Search Activity Worksheet",
        "keywords": "word search, vocabulary building, spelling practice, word puzzles, language arts, letter recognition, reading skills, word games, hidden words, phonics",
    },
    {
        "topic_name": "best educational printables for homeschool families",
        "category": "Education",
        "keywords": "homeschool printables, educational worksheets, learning activities, homeschooling resources, teaching materials, curriculum supplements, activity sheets, printable PDFs, home education, family learning",
    },
]

ts = TopicSelector()
results = []

for i, topic_data in enumerate(MISSING_TOPICS):
    print(f"\n{'=' * 70}")
    print(f"  MISSING ARTICLE {i+1}/3: {topic_data['topic_name']}")
    print(f"{'=' * 70}")

    topic = {
        "slot": "keyword",
        "topic_name": topic_data["topic_name"],
        "category": topic_data["category"],
        "keywords": topic_data["keywords"],
        "product_data": None,
    }

    try:
        result = generate_article_v6("keyword", topic, ts)
        if result:
            results.append(result)
            print(f"\n  [OK] Article saved: {result['title'][:60]}")
            
            # Generate thumbnail for the new cover
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
                        print(f"  [OK] Thumb generated: {cover_fn}")
                    except Exception as e:
                        print(f"  [ERR] Thumb error: {e}")
        else:
            print(f"\n  [FAIL] Article failed: {topic_data['topic_name'][:60]}")
    except Exception as e:
        print(f"\n  [ERROR] {str(e)[:100]}")
        import traceback
        traceback.print_exc()

    if i < len(MISSING_TOPICS) - 1:
        print(f"\n  [PAUSE] Waiting 20s...")
        time.sleep(20)

# ===================================================================
# STEP 3: Rebuild HTML articles
# ===================================================================
print(f"\n{'=' * 70}")
print("  STEP 3: REBUILD HTML ARTICLES")
print(f"{'=' * 70}")

build_script = os.path.join(SCRIPT_DIR, "build_articles.py")
os.system(f'python "{build_script}"')

# Final count
post_count = len(glob.glob(os.path.join(POSTS_DIR, "*.json")))
article_count = len(glob.glob(os.path.join(PROJECT_ROOT, "articles", "*.html")))
image_count = len(glob.glob(os.path.join(IMAGES_DIR, "*.webp")))
thumb_count_final = len(glob.glob(os.path.join(THUMBS_DIR, "*.webp")))

print(f"\n{'=' * 70}")
print(f"  FINAL STATUS")
print(f"{'=' * 70}")
print(f"  Posts:      {post_count}/18")
print(f"  Articles:   {article_count}/18")
print(f"  Images:     {image_count}")
print(f"  Thumbnails: {thumb_count_final}")
print(f"  Results:    {len(results)}/3 missing articles regenerated")
print(f"{'=' * 70}")
