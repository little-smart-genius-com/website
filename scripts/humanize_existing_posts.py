"""
RETROACTIVE HUMANIZER
Rewrites the 25 existing JSON articles using DeepSeek-V3.2 to remove AI markers
and inject human-like burstiness and perplexity while preserving all HTML tags.
"""

import os
import json
import glob
import asyncio
import aiohttp
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
POSTS_DIR = os.path.join(PROJECT_ROOT, "posts")

load_dotenv(os.path.join(PROJECT_ROOT, '.env'))
ALL_DEEPSEEK_KEYS = [os.getenv(f"DEEPSEEK_API_KEY_{i}") for i in range(1, 8) if os.getenv(f"DEEPSEEK_API_KEY_{i}")]
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# Import strictly enforced AI detection phrases
from prompt_templates import AI_DETECTION_PHRASES, TRANSITION_WORDS

async def call_deepseek_rewrite(session, raw_html):
    sys_prompt = f"""You are an elite Educational Copywriter tasked with "Humanizing" an old article.
The user has strict editorial guidelines (E-E-A-T) to defeat detectors and guarantee true value.

YOUR EXACT TASKS:
1. READ the provided HTML content.
2. REWRITE the text to sound like a passionate, experienced educator or parent.
3. INJECT E-E-A-T TONE: Show real Expertise, Experience, Authority, and Trust. Add subtle tips ("In my experience...", "What I've found works...").
4. INJECT "Burstiness": Alternate between very short sentences (2-5 words) and longer ones.
5. REMOVE ALL AI-sounding symmetry (like perfectly matching paragraph lengths).
6. DESTROY ANY OF THESE BANNED PHRASES:
{', '.join(AI_DETECTION_PHRASES)}
7. USE THESE NATURAL TRANSITIONS FREQUENTLY:
{', '.join(TRANSITION_WORDS)}
8. CRITICAL: PRESERVE EVERY HTML TAG EXACTLY. Do not touch `<img src="...">`, `<a href="...">`, `<h2>`, `<h3>`, `<ul>`, `<li>`. Return the SAME HTML structure, just with better text inside.
9. RETURN ONLY THE HTML OUTPUT. No markdown code blocks surrounding it."""

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": f"REWRITE THIS HTML:\n\n{raw_html}"}
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }

    last_error = None
    if not ALL_DEEPSEEK_KEYS:
        raise Exception("No DeepSeek API keys found in .env")

    for attempt, current_key in enumerate(ALL_DEEPSEEK_KEYS):
        headers = {
            "Authorization": f"Bearer {current_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with session.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=240) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    last_error = f"HTTP {resp.status}: {text}"
                    print(f"   [API WARNING] Key {attempt + 1} failed with {resp.status}. Trying next...")
                    continue
                
                data = await resp.json()
                content = data['choices'][0]['message']['content']
                
                # Clean markdown if present
                if content.startswith("```html"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                    
                return content.strip()
        except Exception as e:
            last_error = str(e)
            print(f"   [API WARNING] Exception with Key {attempt + 1}: {e}. Trying next...")
            
    raise Exception(f"CRITICAL: All {len(ALL_DEEPSEEK_KEYS)} DeepSeek API keys failed. Last error: {last_error}")

async def rewrite_article(session, filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    old_content = data.get('content', '')
    if not old_content:
        return
        
    print(f"🔄 Rewriting: {data.get('title')}")
    try:
        new_content = await call_deepseek_rewrite(session, old_content)
        data['content'] = new_content
        data['humanized'] = True
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"✅ Success: {data.get('title')}")
    except Exception as e:
        print(f"❌ Failed to rewrite {filepath}: {e}")

async def main():
    json_files = glob.glob(os.path.join(POSTS_DIR, "*.json"))
    print(f"Found {len(json_files)} existing posts to humanize.")
    
    async with aiohttp.ClientSession() as session:
        # We process in batches of 5 to avoid API rate limits
        batch_size = 5
        for i in range(0, len(json_files), batch_size):
            batch = json_files[i:i+batch_size]
            tasks = [rewrite_article(session, f) for f in batch]
            await asyncio.gather(*tasks)
            if i + batch_size < len(json_files):
                print("Pausing 10s for API limits...")
                await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
