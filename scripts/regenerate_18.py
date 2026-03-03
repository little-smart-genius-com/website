"""
REGENERATE 18 — Master Orchestrator
Cleans everything, then generates exactly 18 articles through the V6 pipeline.
Mix of keyword (12), product (3), and freebie (3) slots.

Usage:
  python regenerate_18.py

(c) 2026 Little Smart Genius
"""

import os
import sys
import json
import shutil
import time
import random
import glob
from datetime import datetime

# Setup paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# Import the V6 pipeline
from auto_blog_v6_ultimate import (
    generate_article_v6, PERSONAS, POSTS_DIR, IMAGES_DIR,
    SEOUtils, TopicSelector
)
from data_parsers import parse_products_tpt, parse_download_links
from topic_selector import FREEBIE_CATEGORIES

# Directories
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
THUMBS_DIR = os.path.join(IMAGES_DIR, "thumbs")
ARCHIVE_DIR = os.path.join(POSTS_DIR, "archive", f"pre_regen_{int(time.time())}")

# ===================================================================
# 18 CURATED TOPICS — Balanced categories, long-tail SEO keywords
# ===================================================================

# 12 Keyword articles (diverse categories, long-tail SEO)
KEYWORD_TOPICS = [
    {
        "topic_name": "printable logic puzzles for kids ages 6-10",
        "category": "Critical Thinking",
        "keywords": "printable logic puzzles, logic puzzles for kids, brain teasers, critical thinking activities, problem solving worksheets, logic games, reasoning skills, deductive thinking, cognitive development, analytical skills",
    },
    {
        "topic_name": "critical thinking activities for kindergarten",
        "category": "Critical Thinking",
        "keywords": "critical thinking kindergarten, thinking skills, problem solving, cognitive development, brain games, reasoning activities, sorting and classifying, pattern recognition, logical thinking, early learners",
    },
    {
        "topic_name": "sudoku puzzles for beginners kids",
        "category": "Math Skills",
        "keywords": "sudoku for kids, beginner sudoku, number puzzles, logical thinking, math games, number placement, grid puzzles, cognitive skills, concentration, pattern recognition",
    },
    {
        "topic_name": "counting exercises for preschoolers printable",
        "category": "Math Skills",
        "keywords": "counting worksheets, preschool math, number sense, counting activities, early math, number recognition, printable worksheets, hands-on counting, numeracy, kindergarten math",
    },
    {
        "topic_name": "spot the difference puzzles for kids printable",
        "category": "Visual Skills",
        "keywords": "spot the difference, visual perception, observation skills, attention to detail, picture puzzles, find differences, brain games, focus activities, visual discrimination, cognitive development",
    },
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
        "topic_name": "spelling practice worksheets for elementary students",
        "category": "Education",
        "keywords": "spelling worksheets, elementary spelling, practice worksheets, language arts, vocabulary, word study, phonics, spelling rules, writing skills, literacy",
    },
    {
        "topic_name": "best educational printables for homeschool families",
        "category": "Education",
        "keywords": "homeschool printables, educational worksheets, learning activities, homeschooling resources, teaching materials, curriculum supplements, activity sheets, printable PDFs, home education, family learning",
    },
    {
        "topic_name": "benefits of puzzles for child brain development",
        "category": "Education",
        "keywords": "puzzles brain development, cognitive benefits, child development, problem solving, spatial reasoning, fine motor skills, memory improvement, concentration, learning through play, educational games",
    },
    {
        "topic_name": "fine motor skills worksheets for preschoolers",
        "category": "Fine Motor Skills",
        "keywords": "fine motor worksheets, preschool activities, hand-eye coordination, pencil grip, tracing worksheets, cutting practice, writing readiness, motor development, sensory activities, dexterity",
    },
    {
        "topic_name": "engaging classroom activities for early learners",
        "category": "Education",
        "keywords": "classroom activities, early learners, kindergarten activities, interactive learning, hands-on activities, group activities, educational games, teaching strategies, student engagement, active learning",
    },
]

# 3 Product articles (different TPT product categories)
PRODUCT_TOPICS = [
    {
        "product_name": "Spot the Difference | Picture Puzzle Visual Perception Activity | Animals Vol.1",
        "product_url": "https://www.teacherspayteachers.com/Product/Spot-the-Difference-Picture-Puzzle-Visual-Perception-Activity-Animals-Vol1-10436437",
        "product_price": "$3.00",
        "product_category": "Spot the Difference (Photorealistic)",
    },
    {
        "product_name": "Thanksgiving Word Search Adventure | Fun Activity Worksheet Collection",
        "product_url": "https://www.teacherspayteachers.com/Product/Thanksgiving-Word-Search-Adventure-Fun-Activity-Worksheet-Collection-10534022",
        "product_price": "$12.00",
        "product_category": "Word Search Activity Worksheet",
    },
    {
        "product_name": "Happy Thanksgiving Coloring Page | Coloring Pages Thanksgiving | Turkey Vol.1",
        "product_url": "https://www.teacherspayteachers.com/Product/Happy-Thanksgiving-Coloring-Page-Coloring-Pages-Thanksgiving-Turkey-Vol1-10533959",
        "product_price": "$1.00",
        "product_category": "Coloring Book",
    },
]

# 3 Freebie articles (different freebie types)
FREEBIE_TOPICS = [
    {
        "freebie_name": "Maze for Kids",
        "freebie_url": "https://drive.google.com/uc?export=download&id=16TVMRA-ynjzluisizspL2Gy7mWNCxwPU",
        "freebie_desc": "Navigate the labyrinth to the exit. Develops problem-solving and pen control.",
        "freebie_category": "Problem Solving",
    },
    {
        "freebie_name": "Word Search",
        "freebie_url": "https://drive.google.com/uc?export=download&id=1jkLi6Wpv3fq7KZbQTBIV_-1U2Yge3LMl",
        "freebie_desc": "Find hidden words in the grid. Improves pattern recognition and vocabulary.",
        "freebie_category": "Word Search Activity Worksheet",
    },
    {
        "freebie_name": "Sudoku",
        "freebie_url": "https://drive.google.com/uc?export=download&id=1kMsX9yB_YhSkC_isuQoo_8Lg8JZfwgld",
        "freebie_desc": "The classic number placement puzzle. Builds pure logic and deductive skills.",
        "freebie_category": "Math Skills",
    },
]


def banner(text, char="="):
    print(f"\n{char * 80}")
    print(f"  {text}")
    print(f"{char * 80}\n")


def step_1_archive_old_content():
    """Archive existing posts and clean articles/images."""
    banner("STEP 1/5: ARCHIVE OLD CONTENT")

    # Archive posts/*.json
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    post_files = glob.glob(os.path.join(POSTS_DIR, "*.json"))
    archived = 0
    for f in post_files:
        shutil.move(f, os.path.join(ARCHIVE_DIR, os.path.basename(f)))
        archived += 1
    print(f"   [OK] Archived {archived} post JSONs to {ARCHIVE_DIR}")

    # Clean articles/*.html
    article_files = glob.glob(os.path.join(ARTICLES_DIR, "*.html"))
    for f in article_files:
        os.remove(f)
    print(f"   [OK] Removed {len(article_files)} article HTMLs")

    # Clean images (but preserve essential files)
    preserve = {"logo.webp", "og-default.webp", "favicon.ico", "hero-bg.webp"}
    img_files = glob.glob(os.path.join(IMAGES_DIR, "*.webp"))
    img_files += glob.glob(os.path.join(IMAGES_DIR, "*.png"))
    img_files += glob.glob(os.path.join(IMAGES_DIR, "*.jpg"))
    removed_imgs = 0
    for f in img_files:
        if os.path.basename(f) not in preserve:
            os.remove(f)
            removed_imgs += 1
    print(f"   [OK] Removed {removed_imgs} old images (preserved {len(preserve)} essential)")

    # Clean thumbs
    if os.path.isdir(THUMBS_DIR):
        thumb_files = glob.glob(os.path.join(THUMBS_DIR, "*.webp"))
        for f in thumb_files:
            os.remove(f)
        print(f"   [OK] Removed {len(thumb_files)} thumbnails")

    used_topics_file = os.path.join(PROJECT_ROOT, "data", "used_topics.json")
    if os.path.exists(used_topics_file):
        with open(used_topics_file, 'w', encoding='utf-8') as f:
            json.dump({"keyword": [], "product": [], "freebie": [], "daily_log": []}, f, indent=2)
        print(f"   [OK] Reset used_topics.json")

    print(f"\n   ARCHIVE COMPLETE")


def step_2_generate_keyword_articles():
    """Generate 12 keyword articles through V6 pipeline."""
    banner("STEP 2/5: GENERATE 12 KEYWORD ARTICLES")

    ts = TopicSelector()
    results = []

    for i, topic_data in enumerate(KEYWORD_TOPICS):
        print(f"\n{'=' * 80}")
        print(f"  KEYWORD ARTICLE {i+1}/12: {topic_data['topic_name'][:60]}")
        print(f"{'=' * 80}")

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
                results.append({
                    "slot": "keyword",
                    "title": result["title"],
                    "slug": result["slug"],
                    "words": result["word_count"],
                    "images": len([img for img in result.get("content", "").split("img") if "src=" in img]),
                })
                print(f"\n   [OK] Article {i+1}/12 saved: {result['title'][:50]}")
            else:
                print(f"\n   [FAIL] Article {i+1}/12 failed: {topic_data['topic_name'][:50]}")
        except Exception as e:
            print(f"\n   [ERROR] Article {i+1}/12 exception: {str(e)[:100]}")
            import traceback
            traceback.print_exc()

        # Pause between articles to avoid API rate limits
        if i < len(KEYWORD_TOPICS) - 1:
            pause = 20
            print(f"\n   [PAUSE] Waiting {pause}s before next article...")
            time.sleep(pause)

    print(f"\n   KEYWORD ARTICLES: {len(results)}/12 completed")
    return results


def step_3_generate_product_articles():
    """Generate 3 product review articles through V6 pipeline."""
    banner("STEP 3/5: GENERATE 3 PRODUCT ARTICLES")

    ts = TopicSelector()
    results = []

    for i, prod in enumerate(PRODUCT_TOPICS):
        print(f"\n{'=' * 80}")
        print(f"  PRODUCT ARTICLE {i+1}/3: {prod['product_name'][:60]}")
        print(f"{'=' * 80}")

        product_data = {
            "name": prod["product_name"],
            "url": prod["product_url"],
            "price": prod["product_price"],
            "category": prod["product_category"],
        }

        topic = {
            "slot": "product",
            "topic_name": prod["product_name"],
            "category": prod["product_category"],
            "keywords": f"{prod['product_category'].lower()}, educational activities, printable worksheets, kids learning",
            "product_data": product_data,
        }

        try:
            result = generate_article_v6("product", topic, ts)
            if result:
                results.append({
                    "slot": "product",
                    "title": result["title"],
                    "slug": result["slug"],
                    "words": result["word_count"],
                })
                print(f"\n   [OK] Product article {i+1}/3 saved: {result['title'][:50]}")
            else:
                print(f"\n   [FAIL] Product article {i+1}/3 failed")
        except Exception as e:
            print(f"\n   [ERROR] Product article {i+1}/3 exception: {str(e)[:100]}")
            import traceback
            traceback.print_exc()

        if i < len(PRODUCT_TOPICS) - 1:
            pause = 20
            print(f"\n   [PAUSE] Waiting {pause}s...")
            time.sleep(pause)

    print(f"\n   PRODUCT ARTICLES: {len(results)}/3 completed")
    return results


def step_4_generate_freebie_articles():
    """Generate 3 freebie tutorial articles through V6 pipeline."""
    banner("STEP 4/5: GENERATE 3 FREEBIE ARTICLES")

    ts = TopicSelector()
    results = []

    for i, free in enumerate(FREEBIE_TOPICS):
        print(f"\n{'=' * 80}")
        print(f"  FREEBIE ARTICLE {i+1}/3: {free['freebie_name']}")
        print(f"{'=' * 80}")

        product_data = {
            "name": free["freebie_name"],
            "url": free["freebie_url"],
            "desc": free["freebie_desc"],
            "category": free["freebie_category"],
        }

        topic = {
            "slot": "freebie",
            "topic_name": free["freebie_name"],
            "category": free["freebie_category"],
            "keywords": f"{free['freebie_name'].lower()}, free printable, educational activity, kids learning, {free['freebie_category'].lower()}",
            "product_data": product_data,
        }

        try:
            result = generate_article_v6("freebie", topic, ts)
            if result:
                results.append({
                    "slot": "freebie",
                    "title": result["title"],
                    "slug": result["slug"],
                    "words": result["word_count"],
                })
                print(f"\n   [OK] Freebie article {i+1}/3 saved: {result['title'][:50]}")
            else:
                print(f"\n   [FAIL] Freebie article {i+1}/3 failed")
        except Exception as e:
            print(f"\n   [ERROR] Freebie article {i+1}/3 exception: {str(e)[:100]}")
            import traceback
            traceback.print_exc()

        if i < len(FREEBIE_TOPICS) - 1:
            pause = 20
            print(f"\n   [PAUSE] Waiting {pause}s...")
            time.sleep(pause)

    print(f"\n   FREEBIE ARTICLES: {len(results)}/3 completed")
    return results


def step_5_build_and_verify():
    """Build HTML articles and verify everything."""
    banner("STEP 5/5: BUILD HTML + VERIFY")

    # Step 5a: Verify all images exist in post JSONs
    print("   [5a] Verifying image files in posts...")
    import re
    post_files = glob.glob(os.path.join(POSTS_DIR, "*.json"))
    total_missing = 0
    total_images = 0

    for pf in post_files:
        try:
            with open(pf, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check cover image
            cover = data.get("image", "")
            if cover and not cover.startswith("http"):
                cover_path = os.path.join(PROJECT_ROOT, cover)
                total_images += 1
                if not os.path.exists(cover_path):
                    print(f"      [MISSING COVER] {cover} in {os.path.basename(pf)}")
                    total_missing += 1

            # Check inline content images
            content = data.get("content", "")
            img_srcs = re.findall(r'src=["\']\.\./(images/[^"\']+\.webp)["\']', content)
            for img_src in img_srcs:
                img_path = os.path.join(PROJECT_ROOT, img_src)
                total_images += 1
                if not os.path.exists(img_path):
                    print(f"      [MISSING] {img_src} in {os.path.basename(pf)}")
                    total_missing += 1

        except Exception as e:
            print(f"      [ERROR] Reading {os.path.basename(pf)}: {e}")

    print(f"   [5a] Image verification: {total_images - total_missing}/{total_images} images OK, {total_missing} missing")

    # Step 5b: Replace any placeholder image references with actual generated images
    if total_missing > 0:
        print("   [5b] Attempting to fix missing image references...")
        for pf in post_files:
            try:
                with open(pf, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                content = data.get("content", "")
                modified = False

                # Remove references to placeholder.webp
                if "placeholder.webp" in content:
                    content = re.sub(
                        r"<figure[^>]*>\s*<img[^>]*src=['\"][^'\"]*placeholder\.webp['\"][^>]*>\s*</figure>",
                        "",
                        content
                    )
                    data["content"] = content
                    modified = True
                    print(f"      [FIX] Removed placeholder refs in {os.path.basename(pf)}")

                # Fix cover if placeholder
                cover = data.get("image", "")
                if "placeholder" in cover or cover.startswith("http"):
                    # Find an actual generated cover image for this slug
                    slug = data.get("slug", "")
                    matching = glob.glob(os.path.join(IMAGES_DIR, f"*{slug[:30]}*cover*.webp"))
                    if matching:
                        data["image"] = f"images/{os.path.basename(matching[0])}"
                        modified = True
                        print(f"      [FIX] Fixed cover in {os.path.basename(pf)}")

                if modified:
                    with open(pf, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

            except Exception as e:
                print(f"      [ERROR] Fixing {os.path.basename(pf)}: {e}")

    # Step 5c: Run build_articles.py
    print("\n   [5c] Building HTML articles from post JSONs...")
    try:
        build_script = os.path.join(SCRIPT_DIR, "build_articles.py")
        exit_code = os.system(f'python "{build_script}"')
        if exit_code == 0:
            print("   [OK] build_articles.py completed successfully")
        else:
            print(f"   [WARN] build_articles.py exited with code {exit_code}")
    except Exception as e:
        print(f"   [ERROR] build_articles.py failed: {e}")

    # Step 5d: Run rebuild_blog_pages.py
    print("\n   [5d] Rebuilding blog listing pages...")
    try:
        rebuild_script = os.path.join(SCRIPT_DIR, "rebuild_blog_pages.py")
        exit_code2 = os.system(f'python "{rebuild_script}"')
        if exit_code2 == 0:
            print("   [OK] rebuild_blog_pages.py completed successfully")
        else:
            print(f"   [WARN] rebuild_blog_pages.py exited with code {exit_code2}")
    except Exception as e:
        print(f"   [ERROR] rebuild_blog_pages.py failed: {e}")

    # Step 5e: Run generate_og_images.py
    print("\n   [5e] Generating OpenGraph images...")
    try:
        og_script = os.path.join(SCRIPT_DIR, "generate_og_images.py")
        exit_code3 = os.system(f'python "{og_script}" --force')
        if exit_code3 == 0:
            print("   [OK] generate_og_images.py completed successfully")
        else:
            print(f"   [WARN] generate_og_images.py exited with code {exit_code3}")
    except Exception as e:
        print(f"   [ERROR] generate_og_images.py failed: {e}")

    # Step 5f: Final count
    post_count = len(glob.glob(os.path.join(POSTS_DIR, "*.json")))
    article_count = len(glob.glob(os.path.join(ARTICLES_DIR, "*.html")))
    image_count = len(glob.glob(os.path.join(IMAGES_DIR, "*.webp")))
    thumb_count = len(glob.glob(os.path.join(THUMBS_DIR, "*.webp"))) if os.path.isdir(THUMBS_DIR) else 0

    print(f"\n   FINAL COUNTS:")
    print(f"   Posts JSON:  {post_count}/18")
    print(f"   Articles:    {article_count}/18")
    print(f"   Images:      {image_count}")
    print(f"   Thumbnails:  {thumb_count}")

    return post_count, article_count


def main():
    start_time = time.time()

    banner("REGENERATE 18 — MASTER ORCHESTRATOR", "=")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Plan: 12 keyword + 3 product + 3 freebie = 18 articles")
    print(f"  Pipeline: V6 Ultimate (7 agents + art director)")
    print(f"  Images: Pollinations API with key rotation")

    # Step 1: Archive old content
    step_1_archive_old_content()

    # Step 2: Generate 12 keyword articles
    keyword_results = step_2_generate_keyword_articles()

    # Step 3: Generate 3 product articles
    product_results = step_3_generate_product_articles()

    # Step 4: Generate 3 freebie articles
    freebie_results = step_4_generate_freebie_articles()

    # Step 5: Build HTML and verify
    post_count, article_count = step_5_build_and_verify()

    # Final summary
    elapsed = time.time() - start_time
    all_results = keyword_results + product_results + freebie_results

    banner("REGENERATION COMPLETE", "=")
    print(f"  Total articles generated: {len(all_results)}/18")
    print(f"  - Keywords: {len(keyword_results)}/12")
    print(f"  - Products: {len(product_results)}/3")
    print(f"  - Freebies: {len(freebie_results)}/3")
    print(f"  Total time: {elapsed/60:.1f} minutes")
    print()

    for r in all_results:
        print(f"    [{r['slot'].upper():8s}] {r['title'][:55]:55s} ({r['words']} words)")

    print(f"\n  Next steps:")
    print(f"    1. Run: python scripts/audit_articles.py")
    print(f"    2. Check: blog_health_report.csv")
    print(f"    3. Open: blog.html in browser")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\n\nCRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
