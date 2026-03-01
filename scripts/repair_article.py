import os
import sys
import json
import asyncio
import re
import argparse
import aiohttp
from typing import Dict, Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
POSTS_DIR = os.path.join(PROJECT_ROOT, "posts")

# Import utilities from auto_blog_v6_ultimate if possible
sys.path.append(SCRIPT_DIR)
from auto_blog_v6_ultimate import call_deepseek_async, DetailedLogger, generate_article_v6, TopicSelector
from build_articles import build_all

logger = DetailedLogger("repair_script")

async def fix_short_keyword(session: aiohttp.ClientSession, data: Dict[str, Any]) -> bool:
    kw = data.get("keywords", [])
    if not kw:
        focus = data.get("title", "")
    else:
        focus = kw[0]
        
    prompt = f"Convert this short keyword '{focus}' into a highly searchable, descriptive long-tail keyword (3-5 words) suitable for a blog post titled '{data.get('title')}'. Output ONLY the exact long-tail keyword string, nothing else."
    
    new_kw = await call_deepseek_async(session, "You are an SEO expert.", prompt, agent_id=1, logger=logger)
    new_kw = new_kw.strip().strip('"').strip("'")
    
    if kw:
        kw[0] = new_kw
    else:
        kw = [new_kw]
    
    data["keywords"] = kw
    logger.success(f"Updated focus keyword to: {new_kw}")
    return True

async def fix_short_tags(session: aiohttp.ClientSession, data: Dict[str, Any]) -> bool:
    kw = data.get("keywords", [])
    if not kw:
        return False
        
    prompt = f"Given these short tags: {kw}, convert them all into long-tail keywords (2-4 words each) related to '{data.get('title')}'. Return them as a comma-separated list. Output ONLY the list, nothing else."
    
    new_tags_raw = await call_deepseek_async(session, "You are an SEO expert.", prompt, agent_id=1, logger=logger)
    new_tags = [t.strip() for t in new_tags_raw.split(',')]
    
    data["keywords"] = new_tags
    logger.success(f"Updated related tags to: {new_tags}")
    return True

async def fix_truncated_title(session: aiohttp.ClientSession, data: Dict[str, Any]) -> bool:
    old_title = data.get("title", "")
    prompt = f"This blog article title is truncated or ends with '...': '{old_title}'. Based on its category '{data.get('category')}' and keywords '{data.get('keywords')}', suggest a complete, catchy, SEO-optimized title without any ellipses or truncation. Output ONLY the title."
    
    new_title = await call_deepseek_async(session, "You are an expert copywriter.", prompt, agent_id=1, logger=logger)
    new_title = new_title.strip().strip('"').strip("'").replace("...", "")
    
    data["title"] = new_title
    logger.success(f"Updated title to: {new_title}")
    return True

async def fix_missing_toc(data: Dict[str, Any]) -> bool:
    # If TOC is missing, it's usually because build_articles skipped it due to missing H2s
    # Or malformed HTML. Let's ask AI to inject H2s into the content.
    return False # Too complex for a simple script, better to rebuild article via agent 6

async def run_repair(slug: str, action: str):
    import glob
    matching_files = glob.glob(os.path.join(POSTS_DIR, f"{slug}*.json"))
    if not matching_files:
        logger.error(f"JSON file not found for slug: {slug}")
        return
    # Use the most recently modified file if multiple match
    json_path = max(matching_files, key=os.path.getmtime)

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    changed = False
    async with aiohttp.ClientSession() as session:
        if action == "Short Focus Keyword" or action == "Missing Focus Keyword":
            changed = await fix_short_keyword(session, data)
        elif action == "Short Related Tags":
            changed = await fix_short_tags(session, data)
        elif action == "Truncated Title":
            changed = await fix_truncated_title(session, data)
        elif action == "Missing TOC" or "Invalid Image Count" in action:
            logger.warning(f"{action}: Regenerating article to fix structural issues...")
            
            # Extract topic info
            topic_name = data.get('title', slug.replace('-', ' ').title())
            category = data.get('category', 'education')
            keywords = data.get('keywords', topic_name)
            if isinstance(keywords, list):
                keywords = ', '.join(keywords)
            
            # Clean up old files to avoid duplicates
            if os.path.exists(json_path):
                try: os.remove(json_path)
                except Exception: pass
            html_path = os.path.join(PROJECT_ROOT, "articles", f"{slug}.html")
            if os.path.exists(html_path):
                try: os.remove(html_path)
                except Exception: pass
                
            ts = TopicSelector()
            topic = {"topic_name": topic_name, "category": category, "keywords": keywords, "product_data": None}
            generate_article_v6("keyword", topic, ts)
            
            # Force rebuild and exit immediately
            print("\nRebuilding articles to apply the full regeneration...")
            build_all()
            os.system(f"{sys.executable} scripts/_post_process.py")
            logger.success("Regeneration and rebuild complete!")
            return

    if changed:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.success(f"Saved changes to {json_path}")
        
        # Rebuild articles to apply changes
        print("\nRebuilding articles to apply the fix...")
        build_all()
        # Post process
        os.system(f"{sys.executable} scripts/_post_process.py")
        logger.success("Repair and rebuild complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Repair specific blog article issues.")
    parser.add_argument("--slug", required=True, help="Slug of the article to repair")
    parser.add_argument("--action", required=True, help="Error action to fix (e.g., 'Truncated Title')")
    
    args = parser.parse_args()
    
    asyncio.run(run_repair(args.slug, args.action))
