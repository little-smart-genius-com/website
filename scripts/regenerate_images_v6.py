import os
import json
import re
import asyncio
import aiohttp
import time
import shutil
import urllib.parse
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

# Ensure we're in the right directory
os.chdir(r'c:\Users\Omar\Desktop\little-smart-genius-site\Nouveau dossier\online\Little_Smart_Genius')
load_dotenv('.env')

# Setup paths
DATA_DIR = "data"
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive_posts")
POSTS_DIR = "posts"
IMAGES_DIR = "images"

# DeepSeek setup
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
# Use V3/chat model to generate prompts consistently and quickly
MODEL_CHAT = "deepseek-chat"
deepseek_key = os.getenv("DEEPSEEK_API_KEY")
if not deepseek_key:
    # Try alternate keys if available
    for i in range(1, 10):
        k = os.getenv(f"DEEPSEEK_API_KEY_{i}")
        if k:
            deepseek_key = k
            break

# Pollinations setup
POLLINATIONS_KEYS = []
for k, v in os.environ.items():
    if k.startswith("POLLINATIONS_API_KEY") and v and len(v) > 5:
        POLLINATIONS_KEYS.append(v)

async def check_balance(session, key):
    try:
        url = "https://gen.pollinations.ai/account/balance"
        headers = {"Authorization": f"Bearer {key}"}
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                data = await resp.json()
                return key, float(data.get("balance", 0.0))
    except Exception:
        pass
    return key, 0.0

# Master Build Prompt (from prompt_templates.py)
def master_build_prompt(subject_instruction: str, image_index: int = 0) -> str:
    """Wraps subject instruction in the highly optimized V6 Master Prompt format."""
    
    # Slight stylistic variations based on image position for extreme consistency but enough variety to look natural
    angle_variation = ""
    if image_index == 0:
        angle_variation = "ultra-wide cinematic framing, dynamic dramatic composition layout"
    elif image_index == 1:
        angle_variation = "intimate mid-shot flat lay composition, overhead tracking perspective"
    elif image_index == 2:
        angle_variation = "low-angle dramatic perspective, intense character focus portrait"
    elif image_index == 3:
        angle_variation = "ultra-close-up macro photography depth of field on hands and props"
    else:
        angle_variation = "dynamic sweeping action shot, perfect rule of thirds composition"

    base_prompt = (
        f"A pristine, ultra-detailed 3D CGI animated render in the pinnacle style of modern Disney/Pixar blockbuster animation. "
        f"Vibrant, incredibly crisp educational illustration featuring {subject_instruction}. "
        f"The characters possess glowing, joyful, profoundly expressive 3D sculpted facial geometry with brilliant sparkling eyes and soft perfectly smoothed skin textures. "
        f"Zero deformities. 100% anatomically correct hands with precisely 5 fingers. "
        f"The atmosphere is warm, bathed in spectacular cinematic golden-hour volumetric lighting, with gorgeous light rays highlighting dust motes in the air. "
        f"Perfectly soft raytraced ambient shadows. "
        f"The background is a highly intentional, depth-of-field blurred educational environment. "
        f"Unreal Engine 5 architectural visualization quality, 8k resolution, masterful color grading, "
        f"{angle_variation}. "
        f"ABSOLUTELY NO TEXT, NO WATERMARKS, NO GIBBERISH LETTERS, NO FONTS. PURE MAGICAL EDUCATIONAL ART."
    )
    return base_prompt

async def agent_5_art_director(session, article_title, concepts):
    print(f"   [ART DIRECTOR] Drafting 6 image prompts for: {article_title}")

    ART_DIRECTOR_SYSTEM_V8 = (
        "You are an expert Art Director for educational children's content. "
        "Your ONLY job is to return a highly descriptive, unique, and highly creative subject text (around 60 to 90 words). "
        "This text will replace the [SUJET] placeholder in a film-grade Pixar template. "
        "You MUST be extremely creative. Each image in the article must have a completely distinct scene, action, "
        "and materials. "
        "CRITICAL REQUIREMENTS:\n"
        "1. All characters (children AND adults) MUST be explicitly described as joyful, happy, and having glowing smiles.\n"
        "2. NO characters should have their tongues sticking out (mouths closed or gently smiling).\n"
        "3. IMPORTANT: Include a mix of characters. Do not only feature children. Frequently include a parent or a teacher actively enthusiastically playing, guiding, or cooperating with the kids.\n"
        "4. Detail specific, tangible, interactive educational props (e.g., holding a shiny magnifying glass, assembling large colorful floor puzzles, moving pieces on a board game, coloring on vibrant worksheets).\n"
        "5. Emphasize a warm, cozy, highly detailed classroom or home environment with sunlight streaming in.\n"
        "6. DO NOT output full prompts, lighting terminology, or style formatting. DO NOT include 'Pixar', '3D', 'Golden hour', etc.\n"
        "7. DIVERSIFY compositions based on your assigned 'Role'. If assigned a wide shot, show the environment AND people. If assigned a flat-lay or detailed shot, focus tightly on HANDS and MATERIALS from an overhead/bird's-eye or close-up perspective, explicitly mentioning hands holding tools.\n"
        "Just describe the specific unique characters (or just hands), their activity with props, and their surroundings."
    )

    IMAGE_ROLES = [
        "Image 1 (Cover): Wide shot of children/parents engaged in activity (current style)",
        "Image 2: CLOSE-UP flat-lay of hands working on the worksheet/puzzle (bird's-eye angle, focus on hands and materials)",
        "Image 3: OVERHEAD shot of multiple children's hands collaborating on a shared activity page",
        "Image 4: DETAIL SHOT of the actual educational material with art supplies around (colored pencils, scissors)",
        "Image 5: Close-up of a child's hands interacting with a specific prop (puzzle piece, game board, coloring page)",
        "Image 6: Wide or medium shot showing the learning environment with visible worksheets on the table",
    ]

    while len(concepts) < 6:
        concepts.append(f"Educational activity scene related to {article_title}")
    concepts = concepts[:6]

    tasks = []
    headers = {"Authorization": f"Bearer {deepseek_key}", "Content-Type": "application/json"}
    
    for i, concept in enumerate(concepts):
        role = IMAGE_ROLES[i % len(IMAGE_ROLES)]
        user_prompt = (
            f"Article Title: {article_title}\n"
            f"Context: {concept}\n"
            f"Role: {role}\n\n"
            f"Write the ~60-90 word unique children's activity description:"
        )
        
        payload = {
            "model": MODEL_CHAT,
            "messages": [
                {"role": "system", "content": ART_DIRECTOR_SYSTEM_V8},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 1.2
        }
        
        async def fetch_prompt(payload_data):
            for retry in range(3):
                try:
                    async with session.post(DEEPSEEK_API_URL, json=payload_data, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            return data["choices"][0]["message"]["content"]
                except Exception as e:
                    await asyncio.sleep(2)
            return None
            
        tasks.append(fetch_prompt(payload))

    raw_prompts = await asyncio.gather(*tasks)

    validated_prompts = []
    for i, (subject, concept) in enumerate(zip(raw_prompts, concepts)):
        if not subject or len(str(subject).strip()) < 20:
            fallback_subject = (
                f"a group of joyful, diverse children and a smiling teacher "
                f"engaged in {concept} activities together, carefully placing "
                f"pieces and smiling, in a warm cozy classroom with sunlight streaming in"
            )
            subject_text = fallback_subject
        else:
            subject_text = str(subject).strip().strip('"').strip("'")
            import re as _re
            for bad in ["3D", "Pixar", "Disney", "Golden hour", "lighting", "shadow"]:
                if bad.lower() in subject_text.lower():
                    subject_text = _re.sub(_re.escape(bad), '', subject_text, flags=_re.IGNORECASE).strip()
            subject_text = _re.sub(r'\s+', ' ', subject_text).strip(' ,.')

        full_prompt = master_build_prompt(subject_text, image_index=i)
        validated_prompts.append(full_prompt)

    return validated_prompts

def optimize_slug(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug[:80]

async def fetch_and_save_image(session, prompt, idx, title, all_valid_keys):
    width, height = 1200, 675
    seed = int(time.time()) + idx * 100
    no_text_suffix = ", ABSOLUTELY NO text, letters, words, numbers, titles, captions, labels, watermarks, or UI overlays in the image, pure visual storytelling only"
    clean_prompt = re.sub(r'[^a-zA-Z0-9 ,.-]', '', prompt + no_text_suffix)
    encoded_prompt = urllib.parse.quote(clean_prompt)

    slug = optimize_slug(title)
    ts = int(time.time())
    suffix = "cover" if idx == 0 else f"img{idx}"
    out_name = f"{slug}-{suffix}-{ts}.webp"
    out_path = os.path.join(IMAGES_DIR, out_name)
    os.makedirs(IMAGES_DIR, exist_ok=True)

    for attempt in range(8):
        api_key = all_valid_keys[(idx + attempt) % len(all_valid_keys)] if all_valid_keys else None
        url = f"https://gen.pollinations.ai/image/{encoded_prompt}"
        
        if attempt < 3:
            current_model = "gptimage"
        elif attempt < 6:
            current_model = "zimage"
        else:
            current_model = "flux"
            
        params = {
            "width": width, "height": height, "seed": seed,
            "model": current_model, "nologo": "true", "enhance": "true"
        }
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=90)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    if len(data) > 1024:
                        img = Image.open(BytesIO(data)).convert("RGB")
                        img.thumbnail((1200, 1200))
                        img.save(out_path, "WEBP", quality=85, optimize=True, method=6)
                        
                        if idx == 0:
                            thumbs_dir = os.path.join(os.path.dirname(out_path), "thumbs")
                            os.makedirs(thumbs_dir, exist_ok=True)
                            thumb_path = os.path.join(thumbs_dir, os.path.basename(out_path))
                            if img.width > 600:
                                aspect_ratio = img.height / img.width
                                new_height = int(600 * aspect_ratio)
                                thumb_img = img.resize((600, new_height), Image.LANCZOS)
                            else:
                                thumb_img = img.copy()
                            thumb_img.save(thumb_path, "WEBP", quality=80, optimize=True)
                            
                        print(f"      ✅ Created {out_name} (Attempt {attempt+1})")
                        return f"images/{out_name}"
        except Exception as e:
            await asyncio.sleep(2)
            seed += 1

    print(f"      ❌ Failed to generate {out_name}")
    return "https://placehold.co/1200x675/F48C06/FFFFFF/png?text=Smart+Genius"

async def process_article(session, json_path, all_valid_keys):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    title = data.get('title', '')
    content = data.get('content', '')
    print(f"\nProcessing: {title}")
    
    # 1. Generate Prompts using Art Director
    # Extract concepts roughly from H2s if possible
    h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', content)
    concepts = [f"Educational activity about {h2}" for h2 in h2s]
    if not concepts:
        concepts = [f"Educational activity scene related to {title}"] * 6
    
    prompts = await agent_5_art_director(session, title, concepts)
    
    # 2. Generate Images
    print(f"   [ARTISTS] Generating 6 images...")
    tasks = [fetch_and_save_image(session, p, i, title, all_valid_keys) for i, p in enumerate(prompts)]
    image_paths = await asyncio.gather(*tasks)
    
    # 3. Replace old images in JSON
    # Cover image
    data['image'] = image_paths[0]
    
    # Inline images (replace up to 5 <img src=...> in the content)
    # The previous script might have used placehold.co or duplicate images
    img_pattern = re.compile(r"<img[^>]+src=['\"](\.\./)?([^'\"]+)['\"][^>]+alt=['\"](.*?)['\"]", re.IGNORECASE)
    matches = img_pattern.findall(content)
    
    img_idx = 1
    # We replace sequentially based on occurrences in content
    # First, let's find all actual <img> tags to replace to preserve location
    
    def replacer(match):
        nonlocal img_idx
        if img_idx < len(image_paths):
            old_src = match.group(1)
            res = match.group(0).replace(old_src, image_paths[img_idx])
            img_idx += 1
            return res
        return match.group(0)
    
    new_content = re.sub(r"<img[^>]+src=['\"](?:\.\./)?([^'\"]+)['\"][^>]+>", replacer, content)
    data['content'] = new_content
    
    # Save back directly to posts/
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        
    print(f"   ✅ Saved {os.path.basename(json_path)}")

async def main():
    target_slugs = [
        "benefits-of-puzzles-for-child-brain-development-across-ages",
        "nurikabe-for-kids-a-smarter-screen-time-alternative",
        "word-search-activities-build-vocabulary-skills",
        "spot-the-difference-puzzles-kids-printable-challenge-guide",
        "free-joke-book-transforms-shy-kids-into-confident-learners",
        "how-coloring-activities-boost-fine-motor-skills-in-children",
        "spring-logic-puzzles-for-kids-ages-6-10",
    ]
    
    # 1. Bring files from archive to posts/
    os.makedirs(POSTS_DIR, exist_ok=True)
    json_files = []
    
    for slug in target_slugs:
        # Find the matching archive file
        for f in os.listdir(ARCHIVE_DIR):
            if f.startswith(slug) and f.endswith(".json"):
                src = os.path.join(ARCHIVE_DIR, f)
                dst = os.path.join(POSTS_DIR, f)
                shutil.copy2(src, dst)
                json_files.append(dst)
                break
                
    print(f"Found {len(json_files)} target articles to process.")
    
    async with aiohttp.ClientSession() as session:
        # Validating keys
        print("Validating Pollinations Keys...")
        tasks = [check_balance(session, k) for k in POLLINATIONS_KEYS]
        results = await asyncio.gather(*tasks)
        valid_keys = [k for k, bal in results if bal > 0]
        
        if not valid_keys:
            print("❌ No valid Pollinations keys with positive balance found.")
            return
            
        print(f"✅ Found {len(valid_keys)} valid keys.")
        
        # Process each article sequentially to avoid blowing up memory/api limits
        for file in json_files:
            await process_article(session, file, valid_keys)

if __name__ == "__main__":
    asyncio.run(main())
