"""
DEEPSEEK V3.2 MULTI-AGENT ORCHESTRATOR (V5)
Architecture: 7 AI Agents + 3 Pollinations Artists running asynchronously.
Goal: Produce 100% human-like, AI-undetectable SEO articles scoring 92+/100.
"""

import os
import sys
import json
import re
import time
import asyncio
import aiohttp
from datetime import datetime
from dotenv import load_dotenv

# Existing tools
from prompt_templates import get_prompt_builder
from data_parsers import parse_products_tpt, parse_download_links
import instagram_cleanup
import requests
from instagram_generator import generate_instagram_post

# Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

DEEPSEEK_KEYS = {
    1: os.getenv("DEEPSEEK_API_KEY_1"),
    2: os.getenv("DEEPSEEK_API_KEY_2"),
    3: os.getenv("DEEPSEEK_API_KEY_3"),
    4: os.getenv("DEEPSEEK_API_KEY_4"),
    5: os.getenv("DEEPSEEK_API_KEY_5"),
    6: os.getenv("DEEPSEEK_API_KEY_6"),
    7: os.getenv("DEEPSEEK_API_KEY_7"),
}

POLLINATIONS_KEYS = [os.getenv(f"POLLINATIONS_API_KEY_{i}") for i in range(1, 6)]
POLLINATIONS_BACKUP_KEYS = [os.getenv(f"POLLINATIONS_API_KEY_BCK_{i}") for i in range(1, 6)]

if not DEEPSEEK_KEYS[1]:
    print("FATAL: DEEPSEEK_API_KEY_1 not found in .env")
    sys.exit(1)

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
# The user specified using DeepSeek-V3.2 (Thinking Mode). The exact model name on the API
# might be "deepseek-reasoner" for thinking mode, or "deepseek-chat". We'll default to reasoner.
MODEL_NAME = "deepseek-reasoner" 

# =============================================================================
# ASYNC DEEPSEEK CLIENT
# =============================================================================

async def call_deepseek_async(session, system_prompt, user_prompt, agent_id=1, temperature=0.3, require_json=False):
    """
    Core async function to call DeepSeek API using a specific Agent's API Key.
    """
    all_keys = [DEEPSEEK_KEYS.get(i) for i in range(1, 8) if DEEPSEEK_KEYS.get(i)]
    if not all_keys:
        raise Exception("No DeepSeek API keys configured")
        
    start_idx = (agent_id - 1) % len(all_keys)
    max_retries = len(all_keys)
    
    last_error = None
    for attempt in range(max_retries):
        current_key = all_keys[(start_idx + attempt) % len(all_keys)]
        
        headers = {
            "Authorization": f"Bearer {current_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": 4000
        }

        if require_json:
            payload["response_format"] = {"type": "json_object"}
            payload["model"] = "deepseek-chat"

        try:
            async with session.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=180)) as response:
                if response.status != 200:
                    text = await response.text()
                    last_error = f"HTTP {response.status}: {text}"
                    print(f"   [API WARNING] Key {((start_idx + attempt) % len(all_keys)) + 1} failed: {response.status}. Trying next...")
                    continue # Try next key
                
                data = await response.json()
                content = data['choices'][0]['message']['content']
                
                if require_json:
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.startswith("```"):
                        content = content[3:]
                    if content.endswith("```"):
                        content = content[:-3]
                    try:
                        return json.loads(content.strip())
                    except json.JSONDecodeError as e:
                        print(f"[API ERROR] Failed to parse JSON: {content[:100]}...")
                        # Let it retry or fail
                        last_error = f"JSON Parse Error: {e}"
                        continue
                return content
        except Exception as e:
            last_error = str(e)
            print(f"   [API WARNING] Exception with Key {((start_idx + attempt) % len(all_keys)) + 1}: {e}. Trying next...")
            
    # If we get here, all keys failed
    raise Exception(f"CRITICAL: All DeepSeek API keys failed. Last error: {last_error}")

# =============================================================================
# THE 7 AGENTS
# =============================================================================

class AutoBlogV5:
    def __init__(self, slot, topic_name, topic_data, persona):
        self.slot = slot
        self.topic_name = topic_name
        self.topic_data = topic_data
        self.persona = persona
        self.plan = None
        self.builders = get_prompt_builder(slot)
        self.html_sections = []
        self.image_prompts = []
        self.image_paths = []
        self.final_content = ""

    async def run_pipeline(self):
        print(f"\n🚀 STARTING V5 DEEPSEEK MULTI-AGENT PIPELINE")
        print(f"Topic: {self.topic_name} | Concept: {self.slot}")
        
        async with aiohttp.ClientSession() as session:
            # 1. 🔵 AGENT 1 - ARCHITECT (Sequential, Temp 0.3)
            print("\n[🔵 AGENT 1] The Architect is drafting the JSON blueprint...")
            await self.agent_1_architect(session)
            print("✅ Blueprint generated successfully!")

            # Prepare tasks for parallel execution (Agents 2, 3, 4 + Agent 5)
            # We will split the architecture into 3 logic parts
            print("\n[🟢🟡 PARALLEL EXECUTION] Launching 3 SEO Writers + 1 Art Director...")
            
            # Since sections can vary, let's divide them evenly among 3 writers
            total_sections = len(self.plan.get('sections', []))
            if total_sections < 3:
                # Fallback if too few sections
                chunks = [self.plan['sections']]
            else:
                chunk_size = total_sections // 3
                rem = total_sections % 3
                chunks = []
                idx = 0
                for i in range(3):
                    sz = chunk_size + (1 if i < rem else 0)
                    chunks.append(self.plan['sections'][idx:idx+sz])
                    idx += sz

            # 2. 🟢 AGENTS 2, 3, 4 - SEO WRITERS (Parallel, Temp 0.7)
            writer_tasks = []
            for i, chunk in enumerate(chunks):
                if chunk: # Only if chunk is not empty
                    writer_tasks.append(self.agent_seo_writer(session, i+1, chunk))
            
            # 3. 🟡 AGENT 5 - ART DIRECTOR (Parallel, Temp 0.4)
            art_task = self.agent_5_art_director(session)

            # Await Phase 2 parallel execution
            results = await asyncio.gather(*writer_tasks, art_task)
            
            # Extract results
            writer_results = results[:-1]
            self.image_prompts = results[-1]
            
            # Sort writer results by chunk ID to maintain order
            writer_results.sort(key=lambda x: x[0])
            self.html_sections = [res[1] for res in writer_results]

            print(f"✅ 3 Writers and Art Director finished! Prompts generated: {len(self.image_prompts)}")

            # 4. 🎨 ARTISTS 1, 2, 3 - POLLINATIONS AI (Parallel)
            print("\n[🎨 PARALLEL EXECUTION] 3 Artists generating 5 images via Pollinations...")
            self.image_paths = await self.artists_generate_images(session, self.image_prompts)
            print("✅ 5 Images generated and saved!")

            # 5. 🔴 AGENT 6 - ASSEMBLER (Temp 0.3)
            print("\n[🔴 AGENT 6] The Assembler is merging the content...")
            await self.agent_6_assembler()

            # 6. 🔴 AGENT 7 - SEO VALIDATOR
            print("\n[🔴 AGENT 7] The SEO Validator is auditing the article...")
            score = await self.agent_7_validator(session)
            
            # --- COMPILE FINAL JSON ---
            word_count = len(re.sub(r'<[^>]+>', '', self.final_content).split())
            reading_time = max(1, round(word_count / 250))
            
            slug = self.plan.get('slug', self.topic_name.lower().replace(' ', '-'))
            slug = re.sub(r'[^a-z0-9\-]', '', slug)
            
            ts_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            
            final_data = {
                "title": self.plan.get('title', self.topic_name),
                "slug": slug,
                "date": datetime.now().strftime("%B %d, %Y"),
                "iso_date": ts_str,
                "category": self.plan.get('category', 'education'),
                "excerpt": self.plan.get('meta_description', ''),
                "keywords": self.plan.get('keywords', []),
                "primary_keyword": self.plan.get('primary_keyword', ''),
                "reading_time": reading_time,
                "image": self.image_paths[0] if self.image_paths else "images/placeholder.webp",
                "cover_concept": self.plan.get('cover_concept', ''),
                "content": self.final_content,
                "faq_schema": self.plan.get('faq_schema', [])
            }
            
            # --- SAVE JSON ---
            posts_dir = os.path.join(PROJECT_ROOT, "posts")
            os.makedirs(posts_dir, exist_ok=True)
            ts_stamp = int(time.time())
            out_file = os.path.join(posts_dir, f"{slug}-{ts_stamp}.json")
            
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ PIPELINE COMPLETE. Final SEO Score: {score}/100")
            print(f"✅ Saved to: {out_file}")
            
            # --- INSTAGRAM SYNDICATION ---
            print("\n[📸 INSTAGRAM] Generating Social Media Post...")
            ig_cover = None
            if self.image_paths:
                ig_cover = os.path.join(PROJECT_ROOT, self.image_paths[0])
                
            try:
                ig_result = generate_instagram_post(final_data, ig_cover)
                if ig_result:
                    print(f"✅ Instagram post generated: {ig_result['image_path']}")
                    article_url = f"{os.getenv('SITE_BASE_URL', 'https://littlesmartgenius.com')}/articles/{slug}.html"
                    if send_to_makecom(ig_result, article_url):
                        print("✅ Send webhook to Make.com")
                        instagram_cleanup.mark(os.path.basename(ig_result['image_path']))
            except Exception as e:
                print(f"❌ Instagram Generation Failed: {e}")
            
            return self.final_content, self.plan

    # --- AGENT METHODS ---

    async def agent_1_architect(self, session):
        """Produces a structured JSON plan."""
        # Execute the outer builder function to get the plan prompt and the inner content builder
        builder_fn = get_prompt_builder(self.slot)
        if self.slot == "product":
            prompts = builder_fn(self.topic_name, self.product_data, self.persona)
        else:
            prompts = builder_fn(self.topic_name, self.persona)
            
        # Prompts is a dict: {"plan_prompt": string, "content_prompt_builder": function}
        plan_prompt = prompts['plan_prompt']
        self.content_builder_fn = prompts['content_prompt_builder']
        
        system_prompt = "You are Agent 1, the Master Architect. Return ONLY valid JSON."
        user_prompt = plan_prompt
        
        self.plan = await call_deepseek_async(session, system_prompt, user_prompt, agent_id=1, temperature=0.3, require_json=True)
        # Ensure 'primary_keyword' exists
        if 'primary_keyword' not in self.plan:
            self.plan['primary_keyword'] = self.topic_name

    async def agent_seo_writer(self, session, writer_id, sections_chunk):
        """Writes a portion of the article. (Agents 2, 3, 4)"""
        print(f"   [🟢 AGENT {writer_id+1}] Start writing {len(sections_chunk)} sections...")
        
        # We build a modified plan that ONLY contains the sections this writer is responsible for,
        # but we also pass the full context so they know what they are writing about.
        partial_plan = dict(self.plan)
        partial_plan['sections'] = sections_chunk

        # Get        system_prompt = "You are an Elite Educational SEO Copywriter. You write ONLY in HTML."
        user_prompt = self.content_builder_fn(partial_plan, target_words=2000)

        # But we rigorously instruct the agent to ONLY output the sections assigned to it.
        # This prevents duplication and forces it to focus its 4000 tokens on just a few sections (extreme quality).
        system_prompt = f"""You are SEO Writer #{writer_id}. You are part of a 3-agent team writing this article.
YOUR SOLE JOB is to write the specific sections assigned to you below in HTML format.

ASSIGNED SECTIONS TO WRITE:
{json.dumps([s.get('h2') for s in sections_chunk], indent=2)}

CRITICAL RULES:
1. ONLY return the HTML (<h2>, <h3>, <p>, <ul>) for your assigned sections.
2. DO NOT write the Introduction (unless you are Writer 1 and it's in your prompt).
3. DO NOT write the Conclusion or FAQ (unless you are Writer 3).
4. Do NOT output markdown code blocks (```html). Just the raw HTML.
5. Apply the strictest 'Anti-AI' humanization rules from your instructions."""

        user_prompt = f"""Here are the project guidelines and full article context:
{base_prompt}

Now, WRITE YOUR ASSIGNED SECTIONS ONLY. Remember: varied paragraph lengths, conversational tone, NO AI phrases."""

        # Temperature 0.7 for maximum human-like creativity and burstiness
        # Agent IDs for writers are 2, 3, 4 based on their writer_id (1, 2, 3)
        agent_id = writer_id + 1
        html_output = await call_deepseek_async(session, system_prompt, user_prompt, agent_id=agent_id, temperature=0.7, require_json=False)
        print(f"   [🟢 AGENT {writer_id+1}] Finished! ({len(html_output.split())} words)")
        
        return (writer_id, html_output)

    async def agent_5_art_director(self, session):
        """Generates 5 image prompts. (Agent 5)"""
        print("   [🟡 AGENT 5] Art Director is drafting 5 Pollinations prompts...")
        from prompt_templates import build_art_director_prompt
        
        # Extract the cover concept and section image concepts
        concepts = [self.plan.get('cover_concept', 'A relevant educational image')]
        for s in self.plan.get('sections', []):
            if 'image_concept' in s:
                concepts.append(s['image_concept'])
        
        # We need exactly 5. Pad or truncate.
        while len(concepts) < 5:
            concepts.append(f"Educational vector illustration related to {self.topic_name}")
        concepts = concepts[:5]

        tasks = []
        for i, concept in enumerate(concepts):
            sys_prompt = "You are Agent 5, the Art Director. Return strictly a 1-2 sentence prompt for an image generator. NO conversational text."
            user_prompt = build_art_director_prompt(concept, f"Article about {self.topic_name}", i)
            # Temp 0.4 for guided creativity
            tasks.append(call_deepseek_async(session, sys_prompt, user_prompt, agent_id=5, temperature=0.4))

        prompts = await asyncio.gather(*tasks)
        print("   [🟡 AGENT 5] 5 Prompts generated.")
        return prompts

    async def fetch_and_save_image(self, session, prompt, idx):
        import urllib.parse
        from PIL import Image
        from io import BytesIO
        
        # Cover image (1200x630) vs Internal images (800x800)
        width = 1200 if idx == 0 else 800
        height = 630 if idx == 0 else 800
        
        seed = int(time.time()) + idx * 100
        encoded_prompt = urllib.parse.quote(prompt)
        
        # Primary key mapping: Image 1 -> Key 1, etc.
        primary_key = POLLINATIONS_KEYS[idx % len(POLLINATIONS_KEYS)] if POLLINATIONS_KEYS else None
        
        out_name = f"blog_{int(time.time())}_{idx}.webp"
        out_path = os.path.join(PROJECT_ROOT, "images", out_name)
        
        # Super robust retry mechanism: 5 attempts with primary, then switch to backup keys
        max_attempts = 8
        for attempt in range(max_attempts):
            # Select key based on attempt number (first 3 with primary, then backup)
            if attempt < 3:
                api_key = primary_key
            else:
                backup_idx = (idx + attempt) % len(POLLINATIONS_BACKUP_KEYS)
                api_key = POLLINATIONS_BACKUP_KEYS[backup_idx] if POLLINATIONS_BACKUP_KEYS else None
                
            # Construct URL with auth header approach if provided, or query param if supported by API
            auth_str = f"&token={api_key}" if api_key else ""
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true&enhance=true&seed={seed}{auth_str}"
            
            try:
                # We add the key to headers just in case Pollinations prefers it there
                headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
                
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        img = Image.open(BytesIO(data)).convert("RGB")
                        # Compress and save as WEBP
                        img.save(out_path, "WEBP", quality=85, method=6)
                        print(f"   [🎨 ARTIST] Saved Image {idx+1} (Attempt {attempt+1})")
                        return f"images/{out_name}"
            except Exception as e:
                print(f"   [🎨 ARTIST ERROR] Image {idx+1}, attempt {attempt+1}: {e}")
                await asyncio.sleep(3)
                seed += 1 # change seed on retry
        
        # If we reach here, all generation attempts failed. The user explicitly said NO placeholders.
        # We raise a fatal error to force the whole process to abort rather than generate a bad article.
        raise Exception(f"CRITICAL: Failed to generate Image {idx+1} after {max_attempts} attempts. Aborting to avoid placeholders.")

    async def artists_generate_images(self, session, prompts):
        """Downloads images from Pollinations. (3 Artists logic handled by asyncio)"""
        tasks = []
        for i, prompt in enumerate(prompts):
            tasks.append(self.fetch_and_save_image(session, prompt, i))
            
        # Run all 5 image generations simultaneously
        image_paths = await asyncio.gather(*tasks)
        return image_paths

    async def agent_6_assembler(self, session):
        """Merges text and images, harmonizes transitions. (Agent 6)"""
        raw_html = "".join(self.html_sections)
        
        sys_prompt = """You are Agent 6, the Chief Editor and Assembler.
Your job is to take raw drafted sections and merge them into a single, cohesive, perfectly flowing article in HTML.

RULES:
1. Harmonize the tone so it sounds like ONE single passionate human author.
2. Ensure transitions between sections are smooth and natural.
3. Replace the placeholders [IMAGE_1], [IMAGE_2], [IMAGE_3], [IMAGE_4] with the provided image paths. Include the cover image at the very top.
4. DO NOT change the core meaning or remove keywords.
5. Provide ONLY the final HTML output (No markdown blocks)."""

        # Format image objects for the prompt
        images_info = f"Cover Image: <img src='../{self.image_paths[0]}' alt='Cover' class='w-full rounded-2xl mb-8'>\n"
        for i in range(1, 5):
            path = self.image_paths[i] if i < len(self.image_paths) else "images/placeholder.webp"
            images_info += f"[IMAGE_{i}]: <figure class='my-8'><img src='../{path}' alt='Educational illustration' class='w-full rounded-xl shadow-md'></figure>\n"

        user_prompt = f"""IMAGES TO INJECT:
{images_info}

RAW DRAFT SECTIONS:
{raw_html}

Please assemble the final HTML article now. Ensure all [IMAGE_X] placeholders are replaced with the actual <figure> tags provided above."""

        self.final_content = await call_deepseek_async(session, sys_prompt, user_prompt, agent_id=6, temperature=0.3, require_json=False)
        print("   [🔴 AGENT 6] Assembly complete! HTML is unified and images are injected.")
    
    async def agent_7_validator(self, session):
        """Audits the SEO score based on strict criteria. (Agent 7)"""
        # We will ask DeepSeek to act as the strict auditor
        sys_prompt = """You are Agent 7, the Premium SEO & Compliance Auditor.
Analyze the provided HTML article against our strict 50-criteria (1000 points total) grid.
Be entirely objective. Note the points for each category.

CRITERIA & SCORING MATRICES:

1. INTENT & KEYWORDS (200 pts)
   - Primary keyword in H1, URL, Intro, & at least one H2 (40 pts)
   - Secondary/LSI keywords naturally present (40 pts)
   - Title/Meta descriptive with clear reader benefit (parent/teacher focus) (40 pts)
   - Answers the user's intent immediately in the intro (40 pts)
   - One clear subject, not diluted (40 pts)

2. CONTENT & PEDAGOGY (200 pts)
   - Length is sufficient (1000+ words) and well contextualized (40 pts)
   - Pedagogical explanations for adults (How to use, age, goals) (40 pts)
   - Clear structure (Objective, Materials, Instructions, Variations) (40 pts)
   - Dedicated FAQ addressing real parent/teacher questions (40 pts)
   - Vocabulary is accessible, sentences are short/punchy (40 pts)

3. MEDIA & UX (200 pts)
   - 5 Images present (Cover + 4 figures) with descriptive Alt Text (50 pts)
   - Content is well spaced, easy to read on mobile (short paragraphs) (50 pts)
   - No aggressive elements (plain, clean HTML structure) (50 pts)
   - Clear and visible formatting for download/print CTAs (50 pts)

4. INTERNAL LINKING (200 pts)
   - Mentions/Hooks for internal links are natural (100 pts)
   - No duplicated or keyword-stuffed anchor text (100 pts)

5. E-E-A-T & HUMAN TONE (200 pts)
   - VERY STRICT: ZERO AI phrases ("In conclusion", "Moreover", "It is important") (100 pts)
   - Tone is authentic, experienced, and trustworthy (E-E-A-T) (100 pts)

Return a strictly formatted JSON object:
{
  "score": 950,
  "issues": ["List of missing things or penalties"],
  "verdict": "PASS" // "PASS" if score >= 900, otherwise "REJECT"
}"""
        
        user_prompt = f"Primary Keyword: {self.plan.get('primary_keyword')}\n\nARTICLE HTML:\n{self.final_content}"
        
        audit = await call_deepseek_async(session, sys_prompt, user_prompt, agent_id=7, temperature=0.1, require_json=True)
        score = audit.get("score", 0)
        
        print(f"   [🔴 AGENT 7] Audit Score: {score}/100")
        if audit.get("issues"):
            for issue in audit.get("issues"):
                print(f"      - {issue}")
                
        return score

# =============================================================================
# WEBHOOK UTILS
# =============================================================================

def send_to_makecom(ig_result, article_url):
    webhook_url = os.environ.get('MAKE_WEBHOOK_URL')
    if not webhook_url:
        return False
        
    base_url = os.environ.get('SITE_BASE_URL', 'https://littlesmartgenius.com')
    img_name = os.path.basename(ig_result['image_path'])
    img_url = f"{base_url}/images/instagram/{img_name}"

    payload = {
        "article_url": article_url,
        "image_url": img_url,
        "instagram_caption": ig_result['caption']
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Make.com Webhook error: {e}")
        return False

# =============================================================================
# CLI ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Auto Blog V5 DeepSeek")
    parser.add_argument("--test", action="store_true", help="Run a quick test pipeline")
    args = parser.parse_args()
    
    if args.test:
        topic = "Fun Math Games for 1st Graders"
        print(f"Testing V5 Pipeline with topic: {topic}")
        test_persona = {
            "role": "Experienced 1st Grade Teacher", 
            "expertise": "Early Childhood Education & Math Pedagogy",
            "tone": "Enthusiastic and practical"
        }
        bot = AutoBlogV5("keyword", topic, None, test_persona)
        asyncio.run(bot.run_pipeline())
    else:
        print("V5 Orchestrator framework created. Run with --test to try it.")
