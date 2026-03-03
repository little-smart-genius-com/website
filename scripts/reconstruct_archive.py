import os
import sys
import json
import glob
import asyncio
import re
import aiohttp
from datetime import datetime
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
POSTS_DIR = os.path.join(PROJECT_ROOT, "posts")
ARCHIVE_DIR = os.path.join(POSTS_DIR, "archive")

sys.path.insert(0, SCRIPT_DIR)
from auto_blog_v6_ultimate import AutoBlogV6, call_deepseek_async, DetailedLogger, PERSONAS
from prompt_templates import _get_lsi_keywords
import random

class RewriteAutoBlogV6(AutoBlogV6):
    def __init__(self, topic, persona, logger, existing_text, existing_title):
        super().__init__("keyword", topic, persona, logger)
        self.existing_text = existing_text
        self.existing_title = existing_title

    async def agent_1_architect(self, session):
        self.logger.step_start("ARCHITECT (REWRITE)", "Rebuilding plan from existing text")
        
        lsi_keywords = _get_lsi_keywords(self.topic_name)
        lsi_str = ", ".join(lsi_keywords[:8])
        
        plan_prompt = f"""You are a Senior SEO Content Strategist. Your task is to REWRITE an existing article to meet our new premium standards.

IDENTITY: {self.persona['role']}

═══ ORIGINAL ARTICLE CONTENT TO REWRITE ═══
Title: {self.existing_title}
Text:
{self.existing_text[:3000]}  # Cap length to avoid massive prompts if needed
═══════════════════════════════════════════

═══ MISSION ═══
Create a DETAILED JSON blueprint that structures this existing content into at least 6 H2 sections. You MUST expand on it if it's too short.

PRIMARY KEYWORD: "{self.topic_name}"
LSI KEYWORDS: {lsi_str}

═══ OUTPUT FORMAT (JSON ONLY) ═══
{{
  "title": "{self.existing_title}",
  "meta_description": "120-155 chars, summary of the rewritten article",
  "primary_keyword": "{self.topic_name}",
  "lsi_keywords": {json.dumps(lsi_keywords[:6])},
  "target_keyword_density": "1.5-2.5%",
  "cover_concept": "Detailed visual: [SCENE] + [SUBJECTS] + [ACTION] + [MOOD] + [COLORS]",
  "sections": [
    {{
      "h2": "Section title — MUST include keyword variation or LSI keyword",
      "h3_subsections": ["Sub 1", "Sub 2", "Sub 3"],
      "key_points": ["Point based on original text or expanded", "Point 2", "Point 3"],
      "image_concept": "UNIQUE visual concept",
      "internal_link_opportunity": "Phrase to link"
    }}
  ],
  "faq": [
    {{"q": "Question?", "a": "Direct answer."}}
  ]
}}

═══ MANDATORY REQUIREMENTS ═══
- EXACTLY 6 sections (H2 headings) MINIMUM. If the original text is short, YOU MUST INVENT AND EXPAND new logical sections to reach 6 H2s.
- 5 UNIQUE image concepts for the inline images.
- 5 FAQ questions.
- Preserve the core message of the original text but dramatically improve its structure and SEO value."""

        def custom_content_builder(plan, target_words=2000):
            sections_json = json.dumps(
                [{"h2": s.get("h2"), "h3": s.get("h3_subsections", []), "points": s.get("key_points", [])} 
                 for s in plan.get("sections", [])], indent=2)
            
            return f"""You are {self.persona['role']} rewriting an article for the "Little Smart Genius" educational blog.

═══ ORIGINAL REFERENCE TEXT ═══
{self.existing_text[:3000]}
═══════════════════════════════

═══ NEW ASSIGNED STRUCTURE ═══
{sections_json}
══════════════════════════════

YOUR TASK:
Write the assigned HTML sections using the new structure above, drawing inspiration, facts, and messaging from the ORIGINAL REFERENCE TEXT. 
Expand creatively where necessary to ensure high quality, sufficient length (2000+ words total), and SEO density.
- Use conversational tone (NO AI phrases like "In conclusion", "Delve into").
- Use varied paragraph lengths.
- Output ONLY the raw HTML (<h2>, <h3>, <p>, <ul>). No markdown blocks."""

        # Call deepseek
        sys_prompt = "You are an expert SEO Architect. Output only raw JSON."
        for attempt in range(3):
            raw = await call_deepseek_async(session, sys_prompt, plan_prompt, agent_id=1, temperature=0.7, logger=self.logger)
            try:
                clean = re.sub(r'```json|```', '', raw).strip()
                self.plan = json.loads(clean)
                break
            except Exception as e:
                self.logger.warning(f"JSON parse error attempt {attempt+1}: {e}", 1)
                
        if not self.plan:
            raise Exception("Failed to generate plan.")
            
        # Ensure 6 H2s
        while len(self.plan.get('sections', [])) < 6:
            idx = len(self.plan['sections']) + 1
            self.plan['sections'].append({
                "h2": f"Additional Information on {self.topic_name} (Part {idx})",
                "h3_subsections": ["Key Concept", "Practical Tips", "Final Thoughts"],
                "key_points": ["Point 1", "Point 2", "Point 3"],
                "image_concept": "Educational activity related to the topic",
                "internal_link_opportunity": "Click here"
            })
            
        self.content_builder_fn = custom_content_builder
        self.logger.step_end("ARCHITECT (REWRITE)")

async def process_archived_article(filepath):
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Processing archived article: {os.path.basename(filepath)}")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    old_title = data.get("title", "Educational Article")
    old_content_html = data.get("content", "")
    old_category = data.get("category", "Education")
    old_keywords = data.get("keywords", [])
    
    # Clean HTML to extract text
    # Replace block level tags with newlines, then strip tags
    text = re.sub(r'</(p|div|h[1-6]|li)>', '\n\n', old_content_html)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    
    if not text:
        print(f"Skipping {os.path.basename(filepath)} - no content found.")
        return
        
    topic = {
        "topic_name": old_title.replace("Ultimate Guide", "").strip() or old_title,
        "category": old_category,
        "keywords": old_keywords,
    }
    
    weights = [p.get('weight', 1) for p in PERSONAS]
    persona = random.choices(PERSONAS, weights=weights, k=1)[0]

    slug_base = os.path.basename(filepath).replace('.json', '')
    # Remove old timestamps from slug if any
    slug_base = re.sub(r'-\d{10}$', '', slug_base)
    
    logger = DetailedLogger(f"rewrite_{slug_base}")
    
    engine = RewriteAutoBlogV6(topic, persona, logger, existing_text=text, existing_title=old_title)
    
    try:
        result = await engine.run_pipeline()
        if result:
            print(f"SUCCESS: Rewrote {os.path.basename(filepath)}")
        else:
            print(f"FAILED: Pipeline returned None for {os.path.basename(filepath)}")
    except Exception as e:
        print(f"FAILED: Exception while rewriting {os.path.basename(filepath)}: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("="*60)
    print("RECONSTRUCT ARCHIVED ARTICLES (V6 UPGRADE)")
    print("="*60)
    
    # 1. Find all files in posts/archive
    archived_files = glob.glob(os.path.join(ARCHIVE_DIR, "*.json"))
    
    if not archived_files:
        print("No archived files found in posts/archive/")
        return
        
    print(f"Found {len(archived_files)} archived articles to reconstruct.")
    
    # Verify DeepSeek API Key
    if not os.environ.get("DEEPSEEK_API_KEY"):
        from dotenv import load_dotenv
        load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
        
    for i, filepath in enumerate(archived_files):
        print(f"\n--- Article {i+1} of {len(archived_files)} ---")
        await process_archived_article(filepath)
        print("Waiting 10 seconds before next article (rate limit protection)...")
        time.sleep(10)
        
    print("\nAll archived articles processed!")
    print("You can now run 'python scripts/build_articles.py' and 'python scripts/rebuild_blog_pages.py' to update the site.")

if __name__ == "__main__":
    asyncio.run(main())
