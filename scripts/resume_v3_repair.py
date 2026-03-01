"""
resume_v3_repair.py
1. Uses existing -v3.webp images from disk if available (saves API keys).
2. Uses DeepSeek Art Director + Pollinations to generate only the MISSING images.
3. Fixes HTML by directly replacing the old src strings with the new ones.
"""
import os, re, sys, json, glob, time, asyncio, urllib.parse
from io import BytesIO
import requests

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

import aiohttp
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
THUMBS_DIR = os.path.join(IMAGES_DIR, "thumbs")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY_1")

POLLINATIONS_MODEL = "klein-large"
IMAGE_WIDTH = 1200
IMAGE_HEIGHT = 675

ALL_KEYS = [
    "sk_dvPDxsCz5ACODEnsJEZP5sZxLxxQtvkU",
    "sk_S7dHK2TXDCrhnj7OhqwyPDXnrU1WqBhE",
    "sk_DaP8irrYyIkZy6KEDnuFiGgJljJvwjBH",
    "sk_CeCH9yoJFRzFzzWIT24UgJMoELGtUG2U",
    "sk_XWTlslehI3QGvU55liIEqBWj31y0DDN9",
    "sk_XZo3bXo2EFD7e0TOsMvPcF7EFHJQeRzY",
    "sk_TkJy20HE8dgaLZzahuYDoVfFQE29SNTW",
    "sk_9ZZhoTwllyVbpIL4bptGhuwuhTlXfCaZ",
    "sk_036omMRJ1NL7ecpDbuNAC8rrZlcOAtcz",
    "sk_xPnT89GsFGsMm8U116Dr2Z9YtERt6YsE",
    "sk_A5rgXn0ERZ2l4NmOzaZocaKoEe7VetIn",
    "sk_cL9GbYUuRCzeW7ukx8KnSX2dO5ECU2rX",
    "sk_lu6zCblSImYuGO6FwAreKg0ls8Wh7tKl",
    "sk_sv4LPxENndtHsEuCXyLoFZsGDDNPZPNs",
]

IMAGE_PRESETS = [
    {"name": "Hero Cover", "lighting": "bright studio lighting, vibrant colors"},
    {"name": "Activity Close-up", "lighting": "warm natural lighting, top-down view"},
    {"name": "Interactive Scene", "lighting": "isometric view, sunny"},
    {"name": "Detailed Tutorial", "lighting": "child's eye view, bright classroom"},
    {"name": "Group Activity", "lighting": "wide shot, colorful room"},
    {"name": "Results & Joy", "lighting": "vibrant, happy lighting"},
]

def generate_art_director_prompt(title, section_context, img_idx):
    preset = IMAGE_PRESETS[img_idx % len(IMAGE_PRESETS)]
    concept = f"educational scene about {section_context}" if section_context else "main cover hero image"
    
    sys_prompt = "You are an expert Art Director. Return ONLY a 1-sentence image generation prompt. NO markdown, NO quotes."
    user_prompt = f"""Write a PREMIUM prompt for an AI image generator.
    
ARTICLE: {title}
SCENE: {concept}
ROLE: {preset['name']}
LIGHTING: {preset['lighting']}

RULES:
1. MUST include: "3D Pixar-style character illustration"
2. Extremely colorful, vibrant, ultra-detailed.
3. Diverse cute children aged 4-8.
4. ABSOLUTELY NO TEXT.

Output ONLY the prompt sentence."""

    for _ in range(3):
        try:
            resp = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.4,
                    "max_tokens": 150
                },
                timeout=15
            )
            if resp.status_code == 200:
                prompt_text = resp.json()["choices"][0]["message"]["content"].strip()
                if "3D Pixar" not in prompt_text:
                    prompt_text = "3D Pixar-style character illustration, " + prompt_text
                no_text = ", ABSOLUTELY NO text, letters, words, numbers, titles, captions, labels, watermarks, or UI overlays"
                return prompt_text.strip().strip('"').strip("'") + no_text
        except Exception:
            time.sleep(2)
            
    return f"3D Pixar-style character illustration, diverse cute children learning about {section_context}, {preset['lighting']}, vibrant colorful educational scene, highly detailed, ABSOLUTELY NO text, letters, words, numbers, titles, captions, labels, watermarks, or UI overlays"

async def fetch_image(session, prompt, out_path, idx):
    clean_prompt = re.sub(r'[^a-zA-Z0-9 ,.-]', '', prompt)
    encoded = urllib.parse.quote(clean_prompt)
    seed = int(time.time()) + idx * 100

    for attempt in range(8):
        key = ALL_KEYS[(idx + attempt) % len(ALL_KEYS)]
        url = f"https://gen.pollinations.ai/image/{encoded}?width={IMAGE_WIDTH}&height={IMAGE_HEIGHT}&seed={seed+attempt}&model={POLLINATIONS_MODEL}&nologo=true&enhance=true"
        headers = {"User-Agent": "Mozilla/5.0", "Authorization": f"Bearer {key}"}

        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=90)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    if len(data) > 2048:
                        img = Image.open(BytesIO(data)).convert("RGB")
                        img.thumbnail((1200, 1200))
                        img.save(out_path, "WEBP", quality=85, optimize=True, method=6)
                        return out_path
        except Exception:
            pass
        await asyncio.sleep(3)
    return None

def get_existing_v3_image(slug, suffix):
    """Find the newest generated v3 image on disk for this slug and suffix."""
    matches = glob.glob(os.path.join(IMAGES_DIR, f"{slug}-{suffix}-*-v3.webp"))
    if not matches:
        return None
    # Sort by modification time to get the newest
    matches.sort(key=os.path.getmtime, reverse=True)
    return matches[0]

def get_h2_contexts(html):
    h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)
    return [re.sub(r'<[^>]+>', '', h2).strip() for h2 in h2s if 'faq' not in h2.lower() and 'frequently' not in h2.lower()]

async def process_article(session, html_path):
    slug = os.path.basename(html_path).replace(".html", "")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    title_match = re.search(r'<title>([^<]+)</title>', html)
    title = title_match.group(1).replace(" | Little Smart Genius", "").strip() if title_match else slug
    h2_contexts = get_h2_contexts(html)
    ts = int(time.time())

    print(f"\nProcessing -> {slug[:50]}...")
    
    # 1. Resolve Cover
    existing_cover = get_existing_v3_image(slug, "cover")
    if existing_cover:
        cover_name = os.path.basename(existing_cover)
        print(f"  [CACHE] Found existing cover: {cover_name}")
    else:
        print("  [NEW] Generating cover...")
        cover_name = f"{slug}-cover-{ts}-v3.webp"
        cover_path = os.path.join(IMAGES_DIR, cover_name)
        prompt = generate_art_director_prompt(title, "main cover hero image", 0)
        res = await fetch_image(session, prompt, cover_path, 0)
        if not res:
            print("  [FAIL] Failed to generate cover.")
            return

    # Ensure thumb exists
    thumb_path = os.path.join(THUMBS_DIR, cover_name)
    if not os.path.exists(thumb_path) and os.path.exists(os.path.join(IMAGES_DIR, cover_name)):
        img = Image.open(os.path.join(IMAGES_DIR, cover_name))
        img.thumbnail((480, 270))
        img.save(thumb_path, "WEBP", quality=80, optimize=True, method=6)

    # 2. Resolve Inline Images
    inline_names = []
    for i in range(1, 6):
        existing_img = get_existing_v3_image(slug, f"img{i}")
        if existing_img:
            img_name = os.path.basename(existing_img)
            print(f"  [CACHE] Found existing img{i}: {img_name}")
            inline_names.append(img_name)
        else:
            print(f"  [NEW] Generating img{i}...")
            img_name = f"{slug}-img{i}-{ts}-v3.webp"
            img_path = os.path.join(IMAGES_DIR, img_name)
            ctx = h2_contexts[i-1] if i <= len(h2_contexts) else f"educational activity {i}"
            prompt = generate_art_director_prompt(title, ctx, i)
            res = await fetch_image(session, prompt, img_path, i)
            if res:
                inline_names.append(img_name)

    # 3. Update HTML Strings directly!
    # Find all current image srcs
    srcs = re.findall(r'src="([^"]+\.webp)"', html)
    if not srcs:
        srcs = re.findall(r"src='([^']+\.webp)'", html)

    cover_src_match = re.search(r'<img[^>]*(?:class="w-full h-auto object-cover"[^>]*src="([^"]+)"|src="([^"]+)"[^>]*class="w-full h-auto object-cover")', html)
    if cover_src_match:
        old_cover_src = cover_src_match.group(1) or cover_src_match.group(2)
        html = html.replace(old_cover_src, f"../images/{cover_name}")
        # Also replace thumbnail in srcset
        # srcset="../images/thumbs/old.webp 480w, ../images/old.webp 1200w"
        html = re.sub(
            r'srcset="[^"]+"', 
            f'srcset="../images/thumbs/{cover_name} 480w, ../images/{cover_name} 1200w"', 
            html
        )

    # Now replace inline images by order of appearance
    # They are wrapped in <figure class="article-image my-8">
    figure_blocks = re.findall(r'(<figure class="article-image my-8"[^>]*>.*?<\/figure>)', html, re.DOTALL)
    
    # We will replace these verbatim
    for idx, block in enumerate(figure_blocks):
        if idx < len(inline_names):
            new_name = inline_names[idx]
            new_src = f"../images/{new_name}"
            # Replace the src inside this block
            new_block = re.sub(r'src=["\'][^"\']+["\']', f'src="{new_src}"', block)
            html = html.replace(block, new_block)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  [SUCCESS] HTML completely updated for {slug}")

async def main():
    html_files = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html")))
    print(f"Starting repair and completion for {len(html_files)} articles...")
    async with aiohttp.ClientSession() as session:
        for f in html_files:
            await process_article(session, f)
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
