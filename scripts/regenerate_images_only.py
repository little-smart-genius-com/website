"""
REGENERATE IMAGES ONLY
Iterates over all post JSONs in posts/ and resubmits them to the updated Art Director.
"""
import os, sys, json, glob, asyncio, time
import aiohttp
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
POSTS_DIR = os.path.join(PROJECT_ROOT, "posts")

sys.path.insert(0, SCRIPT_DIR)
from auto_blog_v6_ultimate import AutoBlogV6, DetailedLogger, master_build_prompt

class MockTopic:
    def __init__(self, data):
        self.topic_name = data.get("title", "Educational Topic")
        self.category = data.get("category", "")
        self.keywords = ", ".join(data.get("keywords", []))

async def process_article(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    slug = data.get("slug", "unknown-slug")
    print(f"\nProcessing images for: {slug}")
    
    logger = DetailedLogger(f"regen_imgs_{slug}")
    
    # Mock the minimum data needed for Art Director
    topic = {
        "topic_name": data.get("title", ""),
        "category": data.get("category", ""),
        "keywords": ", ".join(data.get("keywords", [])),
    }
    persona = {"role": "Art Director"}
    
    pipeline = AutoBlogV6("keyword", topic, persona, logger)
    pipeline.plan = data  # The art director reads from self.plan
    
    # Run Agent 5 and 6 logic manually to regenerate images
    async with aiohttp.ClientSession() as session:
        # Generate prompts
        pipeline.image_prompts = await pipeline.agent_5_art_director(session)
        # Generate images
        pipeline.image_paths = await pipeline.artists_generate_images(session)
    
    logger.save()
    
    # Replace cover
    if pipeline.image_paths and len(pipeline.image_paths) > 0:
        data["image"] = pipeline.image_paths[0].replace(PROJECT_ROOT + os.sep, "").replace("\\", "/")
    
    # We won't inject into HTML content directly here since it's already generated.
    # To properly update the article, we'll let build_articles.py handle the JSON.
    # Actually wait - in V6 the images are injected into the HTML during Generation.
    # Since the text is already generated in data["content"], we just need to replace the img srcs.
    
    old_content = data.get("content", "")
    import re
    img_tags = re.findall(r'<img[^>]*src=["\']([^"\']+)["\'][^>]*>', old_content)
    
    new_content = old_content
    # The first image_path is the cover. The rest (1 to 5) are inline images.
    inline_paths = [p.replace(PROJECT_ROOT + os.sep, "").replace("\\", "/") for p in pipeline.image_paths[1:]]
    
    for i, old_src in enumerate(img_tags):
        if i < len(inline_paths):
            new_content = new_content.replace(old_src, f"../{inline_paths[i]}")
    
    data["content"] = new_content
    
    # Calculate reading time and clean up if needed
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    print(f"[{slug}] Saved {len(pipeline.image_paths)} new images and updated JSON.")

async def main():
    print("="*60)
    print("REGENERATE IMAGES ONLY (V8 Diversity Rules)")
    print("="*60)
    
    post_files = glob.glob(os.path.join(POSTS_DIR, "*.json"))
    for i, pf in enumerate(post_files):
        print(f"\n--- Article {i+1}/{len(post_files)} ---")
        try:
            await process_article(pf)
        except Exception as e:
            print(f"Error processing {pf}: {e}")
            import traceback
            traceback.print_exc()
        time.sleep(5)
    
    print("\nTriggering build_articles.py, rebuild_blog_pages.py and generate_og_images.py...")
    os.system(f'python "{os.path.join(SCRIPT_DIR, "build_articles.py")}"')
    os.system(f'python "{os.path.join(SCRIPT_DIR, "rebuild_blog_pages.py")}"')
    os.system(f'python "{os.path.join(SCRIPT_DIR, "generate_og_images.py")}" --force')
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
