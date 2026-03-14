"""
Fix/regenerate images for articles using DeepSeek Art Director + Master Prompts.
Supports CLI arguments for use from GitHub Actions.
"""
import os
import sys
import json
import re
import glob
import argparse
import requests
import time
import asyncio
import aiohttp
from urllib.parse import quote
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

# Use the master prompt templates
from master_prompt import build_prompt as master_build_prompt

# Cross-platform: works both locally and on GitHub Actions
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
load_dotenv('.env')

# ── Directories ──
DATA_DIR = "data"
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive_posts")
POSTS_DIR = "posts"
IMAGES_DIR = "images"

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL_CHAT = "deepseek-chat"
deepseek_key = os.getenv("DEEPSEEK_API_KEY")
if not deepseek_key:
    for i in range(1, 10):
        k = os.getenv(f"DEEPSEEK_API_KEY_{i}")
        if k:
            deepseek_key = k
            break

# ── Collect API keys ──
POLLINATIONS_KEYS = []
for k, v in os.environ.items():
    if k.startswith("POLLINATIONS_API_KEY") and v and len(v) > 5:
        POLLINATIONS_KEYS.append(v)

def get_working_pollinations_key():
    for key in POLLINATIONS_KEYS:
        try:
            res = requests.get("https://gen.pollinations.ai/account/balance",
                               headers={"Authorization": f"Bearer {key}"}, timeout=10)
            if res.status_code == 200 and res.json().get("balance", 0) > 0:
                print(f"Using Pollinations key starting with {key[:15]}...")
                return key
        except Exception:
            continue
    return None

api_key = get_working_pollinations_key()
headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}


# ── DEEPSEEK ART DIRECTOR ──
async def agent_5_art_director_single(session, title, concept, image_index):
    IMAGE_ROLES = [
        "Image 1 (Cover): Wide shot of children/parents engaged in activity (current style)",
        "Image 2: CLOSE-UP flat-lay of hands working on the worksheet/puzzle (bird's-eye angle, focus on hands and materials)",
        "Image 3: OVERHEAD shot of multiple children's hands collaborating on a shared activity page",
        "Image 4: DETAIL SHOT of the actual educational material with art supplies around (colored pencils, scissors)",
        "Image 5: Close-up of a child's hands interacting with a specific prop (puzzle piece, game board, coloring page)",
        "Image 6: Wide or medium shot showing the learning environment with visible worksheets on the table",
    ]
    role = IMAGE_ROLES[image_index % len(IMAGE_ROLES)]
    
    SYSTEM_PROMPT = (
        "You are an expert Art Director for educational children's content. "
        "Your ONLY job is to return a highly descriptive, unique, and highly creative subject text (around 60 to 90 words). "
        "This text will replace the [SUJET] placeholder in a film-grade Pixar template. "
        "You MUST be extremely creative. Each image in the article must have a completely distinct scene, action, "
        "and materials. "
        "CRITICAL REQUIREMENTS:\n"
        "1. All characters (children AND adults) MUST be explicitly described as having a natural, gentle, realistic smile.\n"
        "2. NO characters should have their mouths wide open, no exaggerated expressions, and no tongues sticking out (mouths MUST be closed or gently smiling naturally).\n"
        "3. IMPORTANT: Include a mix of characters. Do not only feature children. Frequently include a parent or a teacher actively enthusiastically playing, guiding, or cooperating with the kids.\n"
        "4. Detail specific, tangible, interactive educational props (e.g., holding a shiny magnifying glass, assembling large colorful floor puzzles, moving pieces on a board game, coloring on vibrant worksheets).\n"
        "5. Emphasize a warm, cozy, highly detailed classroom or home environment with sunlight streaming in.\n"
        "6. DO NOT output full prompts, lighting terminology, or style formatting. DO NOT include 'Pixar', '3D', 'Golden hour', etc.\n"
        "7. DIVERSIFY compositions based on your assigned 'Role'. If assigned a wide shot, show the environment AND people. If assigned a flat-lay or detailed shot, focus tightly on HANDS and MATERIALS from an overhead/bird's-eye or close-up perspective, explicitly mentioning hands holding tools.\n"
        "Just describe the specific unique characters (or just hands), their activity with props, and their surroundings."
    )
    
    user_prompt = (
        f"Article Title: {title}\n"
        f"Context: {concept}\n"
        f"Role: {role}\n\n"
        f"Write the ~60-90 word unique children's activity description:"
    )
    
    payload = {
        "model": MODEL_CHAT,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 1.2
    }
    
    auth_headers = {"Authorization": f"Bearer {deepseek_key}", "Content-Type": "application/json"}
    for attempt in range(3):
        try:
            async with session.post(DEEPSEEK_API_URL, json=payload, headers=auth_headers, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"].strip().strip('"').strip("'")
        except Exception:
            await asyncio.sleep(2)
            
    # Fallback
    return (f"a group of joyful, diverse children and a smiling teacher "
            f"engaged in {concept[:20]} activities together, carefully placing "
            f"pieces and smiling, in a warm cozy classroom with sunlight streaming in")


def center_crop_resize(img, target_w, target_h):
    src_w, src_h = img.size
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        new_w = int(src_h * target_ratio)
        offset = (src_w - new_w) // 2
        img = img.crop((offset, 0, offset + new_w, src_h))
    elif src_ratio < target_ratio:
        new_h = int(src_w / target_ratio)
        offset = (src_h - new_h) // 2
        img = img.crop((0, offset, src_w, offset + new_h))

    return img.resize((target_w, target_h), Image.LANCZOS)


def generate_image(prompt, filename, model="zimage", retries=3):
    safe_prompt = quote(re.sub(r'[^a-zA-Z0-9 ,.-]', '', prompt))
    fallback_models = ["zimage", "flux", "gptimage"]
    
    if model not in fallback_models:
        model = "zimage"
        
    for attempt in range(retries):
        current_model = model if attempt == 0 else fallback_models[attempt % len(fallback_models)]
        url = f"https://gen.pollinations.ai/image/{safe_prompt}?model={current_model}&width=1200&height=675&nologo=true&enhance=true"
        print(f"  🎨 Attempt {attempt+1}/{retries} with model={current_model}:\n    {prompt[:100]}...")
        try:
            res = requests.get(url, headers=headers, timeout=90)
            if res.status_code == 200 and len(res.content) > 1024:
                img = Image.open(BytesIO(res.content)).convert("RGB")
                img = center_crop_resize(img, 1200, 675)
                out_path = os.path.join(IMAGES_DIR, filename)
                img.save(out_path, "WEBP", quality=85, optimize=True)
                size_kb = os.path.getsize(out_path) // 1024
                print(f"  ✅ Created {filename} ({size_kb}KB)")
                return f"images/{filename}"
        except Exception as e:
            print(f"  ❌ Error: {e}")
        time.sleep(2)

    return None

def find_post_file(slug):
    for search_dir in [POSTS_DIR, ARCHIVE_DIR, DATA_DIR]:
        if not os.path.isdir(search_dir):
            continue
        for f in os.listdir(search_dir):
            if f.endswith('.json') and slug in f:
                return os.path.join(search_dir, f)
    return None

async def process_article(post_path, force=False, image_type=None, selected_model="zimage"):
    print(f"\n{'='*60}")
    print(f"📄 Processing: {os.path.basename(post_path)}")

    with open(post_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    slug = data.get('slug', os.path.basename(post_path).rsplit('-', 1)[0])
    content = data.get('content', '')
    title = data.get('title', slug.replace('-', ' '))
    timestamp = str(int(time.time()))
    changed = False
    
    # We need to gather all concepts to know context
    cover_concept = data.get('cover_concept', f'Educational illustration about {title}')
    
    # Avoid duplicate tags by keeping track of the matches
    images_in_content = []
    simple_img_pattern = re.compile(r"<img[^>]+src=['\"]([^'\"]+)['\"][^>]+alt=['\"]([^'\"]*)['\"]", re.IGNORECASE)
    for m in simple_img_pattern.finditer(content):
        pre_text = content[:m.start()]
        h2_match = list(re.finditer(r"<h2[^>]*>(.*?)</h2>", pre_text, re.IGNORECASE))
        concept = h2_match[-1].group(1) if h2_match else f"Educational activity for {title}"
        images_in_content.append((m.group(1), m.group(2), concept))

    async with aiohttp.ClientSession() as session:
        # Cover
        if image_type is None or image_type == 'cover':
            current_cover = data.get('image', '')
            needs_cover = force or 'placehold.co' in current_cover or not current_cover
            if needs_cover:
                print(f"  🖼️ Regenerating COVER...")
                subject = await agent_5_art_director_single(session, title, cover_concept, 0)
                full_prompt = master_build_prompt(subject, 0)
                full_prompt += ", ABSOLUTELY NO text, letters, words, numbers, titles, captions, labels, watermarks, or UI overlays in the image, pure visual storytelling only"
                
                # Reuse existing filename to avoid needing HTML rebuild
                existing_cover = os.path.basename(current_cover) if current_cover else ''
                cover_filename = existing_cover if existing_cover and existing_cover.endswith('.webp') else f"{slug}-cover-{timestamp}.webp"
                print(f"  📁 Overwriting: {cover_filename}")
                
                cover_path = generate_image(full_prompt, cover_filename, model=selected_model, retries=6)
                if cover_path:
                    data['image'] = cover_path
                    changed = True
                    # Thumbnail (same name as before)
                    try:
                        img = Image.open(os.path.join(IMAGES_DIR, cover_filename))
                        thumb = center_crop_resize(img, 600, 338)
                        thumbs_dir = os.path.join(IMAGES_DIR, "thumbs")
                        os.makedirs(thumbs_dir, exist_ok=True)
                        thumb.save(os.path.join(thumbs_dir, cover_filename), "WEBP", quality=80)
                        print(f"  ✅ Thumbnail created")
                    except Exception as e:
                        pass

        # Content images
        idx = 1
        for src, alt, concept in images_in_content:
            is_target = False
            if image_type is None:
                is_target = force or 'placehold.co' in src
            elif image_type == f'img{idx}':
                is_target = True
                
            if is_target:
                print(f"  🖼️ Regenerating img{idx} (Context: {concept[:40]}...)..")
                subject = await agent_5_art_director_single(session, title, concept, idx)
                full_prompt = master_build_prompt(subject, idx)
                full_prompt += ", ABSOLUTELY NO text, letters, words, numbers, titles, captions, labels, watermarks, or UI overlays in the image, pure visual storytelling only"
                
                # Reuse existing filename to avoid needing HTML rebuild
                existing_basename = os.path.basename(src).split('?')[0]  # strip cache busters
                if existing_basename and existing_basename.endswith('.webp') and 'placehold' not in existing_basename:
                    filename = existing_basename
                else:
                    filename = f"{slug}-img{idx}-{timestamp}.webp"
                print(f"  📁 Overwriting: {filename}")
                
                img_path = generate_image(full_prompt, filename, model=selected_model, retries=6)
                if img_path:
                    # Only update content reference if the filename actually changed
                    if filename != existing_basename:
                        content = content.replace(src, f"../images/{filename}")
                    changed = True
            idx += 1

    if changed:
        data['content'] = content
        with open(post_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  💾 Saved changes to {post_path}")
    else:
        print(f"  ℹ️ No changes needed")

    return changed


async def main_async(args):
    os.makedirs(IMAGES_DIR, exist_ok=True)
    if args.slug:
        post_path = find_post_file(args.slug)
        if not post_path:
            print(f"❌ No JSON found for slug: {args.slug}")
            sys.exit(1)
        await process_article(post_path, force=args.force, image_type=args.image_type, selected_model=args.model)
    else:
        print("🔍 Scanning all articles for placeholder images...")
        all_posts = []
        for search_dir in [POSTS_DIR, ARCHIVE_DIR]:
            if os.path.isdir(search_dir):
                for f in os.listdir(search_dir):
                    if f.endswith('.json'):
                        all_posts.append(os.path.join(search_dir, f))

        processed = 0
        for post_path in sorted(all_posts):
            try:
                with open(post_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                has_placeholder = 'placehold.co' in data.get('image', '') or 'placehold.co' in data.get('content', '')
                if has_placeholder or args.force:
                    if await process_article(post_path, force=args.force, image_type=args.image_type, selected_model=args.model):
                        processed += 1
            except Exception as e:
                print(f"  ❌ Error processing {post_path}: {e}")

        print(f"\n{'='*60}")
        print(f"✅ Done! Processed {processed} articles.")

def main():
    parser = argparse.ArgumentParser(description='Fix/regenerate article images with Art Director')
    parser.add_argument('--slug', type=str, default='', help='Target article slug')
    parser.add_argument('--force', action='store_true', help='Force regeneration of all images')
    parser.add_argument('--image-type', type=str, default=None, help='Specific image type (cover, img1, img2...)')
    parser.add_argument('--model', type=str, default='zimage', help='Image generation model (zimage, flux, gptimage)')
    args = parser.parse_args()
    asyncio.run(main_async(args))

if __name__ == "__main__":
    main()
