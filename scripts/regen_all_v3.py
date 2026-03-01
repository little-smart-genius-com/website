"""
REGEN ALL IMAGES V3 — Art Director Edition
Uses DeepSeek API (Art Director) to perfect the Prompts to strictly 3D Pixar Style,
then uses Pollinations (with backup keys) to generate 174 images.
Updates HTML files directly.
"""
import os, re, sys, json, glob, time, asyncio, urllib.parse
from io import BytesIO
import requests

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

try:
    import aiohttp
    from PIL import Image
except ImportError:
    os.system(f"{sys.executable} -m pip install aiohttp Pillow python-dotenv requests")
    import aiohttp
    from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
THUMBS_DIR = os.path.join(IMAGES_DIR, "thumbs")

# DeepSeek Config for Art Director
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY_1")
if not DEEPSEEK_API_KEY:
    print("FATAL: DEEPSEEK_API_KEY_1 not found in .env")
    sys.exit(1)

# Pollinations config
POLLINATIONS_MODEL = "klein-large"
IMAGE_WIDTH = 1200
IMAGE_HEIGHT = 675

# Hardcoded new keys provided by user
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

# Image presets per position
IMAGE_PRESETS = [
    {"name": "Hero Cover", "lighting": "bright studio lighting, vibrant colors"},
    {"name": "Activity Close-up", "lighting": "warm natural lighting, top-down view"},
    {"name": "Interactive Scene", "lighting": "isometric view, sunny"},
    {"name": "Detailed Tutorial", "lighting": "child's eye view, bright classroom"},
    {"name": "Group Activity", "lighting": "wide shot, colorful room"},
    {"name": "Results & Joy", "lighting": "vibrant, happy lighting"},
]

def generate_art_director_prompt(title, section_context, img_idx):
    """Call DeepSeek to generate a strict 3D Pixar style prompt."""
    preset = IMAGE_PRESETS[img_idx % len(IMAGE_PRESETS)]
    concept = f"educational scene about {section_context}" if section_context else "main cover hero image"
    
    sys_prompt = "You are an expert Art Director. Return ONLY a 1-sentence image generation prompt. NO markdown, NO quotes."
    user_prompt = f"""Write a PREMIUM prompt for an AI image generator.
    
ARTICLE TITLE: {title}
SPECIFIC SCENE CONTEXT: {concept}
ROLE: {preset['name']}
LIGHTING/ANGLE: {preset['lighting']}

CRITICAL RULES YOU MUST OBEY:
1. The image MUST be explicitly described as: "3D Pixar-style character illustration"
2. The style MUST be extremely colorful, vibrant, and ultra-detailed.
3. The subjects must be diverse, cute children aged 4-8.
4. NO text, NO words, NO letters, NO UI overlays, NO watermarks anywhere in the image.

Output ONLY the prompt sentence."""

    for attempt in range(3):
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
                # Safety enforcement
                if "3D Pixar" not in prompt_text:
                    prompt_text = "3D Pixar-style character illustration, " + prompt_text
                
                no_text = ", ABSOLUTELY NO text, letters, words, numbers, titles, captions, labels, watermarks, or UI overlays"
                return prompt_text.strip().strip('"').strip("'") + no_text
        except Exception as e:
            time.sleep(2)
            
    # Fallback if API fails
    return f"3D Pixar-style character illustration, diverse cute children learning about {section_context}, {preset['lighting']}, vibrant colorful educational scene, highly detailed, ABSOLUTELY NO text, letters, words, numbers, titles, captions, labels, watermarks, or UI overlays"


async def fetch_image(session, prompt, out_path, idx):
    """Download image from Pollinations API with retry logic."""
    clean_prompt = re.sub(r'[^a-zA-Z0-9 ,.-]', '', prompt)
    encoded = urllib.parse.quote(clean_prompt)
    seed = int(time.time()) + idx * 100

    for attempt in range(8):
        # Key rotation
        key_idx = (idx + attempt) % len(ALL_KEYS)
        api_key = ALL_KEYS[key_idx]

        url = f"https://gen.pollinations.ai/image/{encoded}"
        params = {
            "width": IMAGE_WIDTH,
            "height": IMAGE_HEIGHT,
            "seed": seed + attempt,
            "model": POLLINATIONS_MODEL,
            "nologo": "true",
            "enhance": "true"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Authorization": f"Bearer {api_key}"
        }

        try:
            async with session.get(url, params=params, headers=headers,
                                    timeout=aiohttp.ClientTimeout(total=90)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    if len(data) > 2048:
                        img = Image.open(BytesIO(data)).convert("RGB")
                        img.thumbnail((1200, 1200))
                        img.save(out_path, "WEBP", quality=85, optimize=True, method=6)
                        size_kb = os.path.getsize(out_path) // 1024
                        print(f"      [OK] ({size_kb}KB) {os.path.basename(out_path)}")
                        return out_path
                    else:
                        print(f"      [WARN] attempt {attempt+1}: too small ({len(data)}B)")
                else:
                    print(f"      [WARN] attempt {attempt+1}: HTTP {resp.status}")
        except Exception as e:
            print(f"      [ERR] attempt {attempt+1}: {str(e)[:60]}")

        await asyncio.sleep(3)

    print(f"      [FAIL] All attempts failed: {os.path.basename(out_path)}")
    return None

def get_h2_contexts(html):
    h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)
    contexts = []
    for h2 in h2s:
        text = re.sub(r'<[^>]+>', '', h2).strip()
        if text and 'faq' not in text.lower() and 'frequently' not in text.lower():
            contexts.append(text)
    return contexts

async def process_article(session, html_path, article_num, total):
    slug = os.path.basename(html_path).replace(".html", "")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Check if this article was already processed with v3 images
    if "-v3.webp" in html:
        print(f"\n{'=' * 65}")
        print(f"[{article_num}/{total}] {slug[:60]}")
        print("  SKIP — Already generated (v3 images present)")
        return 0

    title_match = re.search(r'<title>([^<]+)</title>', html)
    title = title_match.group(1).replace(" | Little Smart Genius", "").strip() if title_match else slug
    ts = int(time.time())
    
    print(f"\n{'=' * 65}")
    print(f"[{article_num}/{total}] {title[:60]}")
    
    h2_contexts = get_h2_contexts(html)
    
    # 1. GENERATE COVER
    cover_name = f"{slug}-cover-{ts}-v3.webp"
    cover_path = os.path.join(IMAGES_DIR, cover_name)
    print("  [1/6] Art Director generating COVER prompt...")
    cover_prompt = generate_art_director_prompt(title, "main cover hero image", 0)
    print(f"      -> {cover_prompt[:80]}...")
    
    cover_result = await fetch_image(session, cover_prompt, cover_path, 0)
    
    if not cover_result:
        print("  SKIP — cover failed")
        return 0
        
    # Generate thumbnail
    thumb_name = f"{slug}-cover-{ts}-v3.webp"
    thumb_path = os.path.join(THUMBS_DIR, thumb_name)
    img = Image.open(cover_path)
    img.thumbnail((480, 270))
    img.save(thumb_path, "WEBP", quality=80, optimize=True, method=6)
    
    # 2. GENERATE INLINE IMAGES
    inline_results = []
    for i in range(1, 6):
        context = h2_contexts[i-1] if i <= len(h2_contexts) else f"educational activity {i}"
        print(f"  [{i+1}/6] Art Director generating img{i} prompt...")
        prompt = generate_art_director_prompt(title, context, i)
        print(f"      -> {prompt[:80]}...")
        
        img_name = f"{slug}-img{i}-{ts}-v3.webp"
        img_path = os.path.join(IMAGES_DIR, img_name)
        
        result = await fetch_image(session, prompt, img_path, i)
        inline_results.append((i, result, img_name))
        await asyncio.sleep(2)
        
    # 3. UPDATE HTML
    cover_rel = f"../images/{cover_name}"
    thumb_rel = f"../images/thumbs/{thumb_name}"
    
    # Cover src
    html = re.sub(
        r'(<img[^>]*class="w-full h-auto object-cover"[^>]*src=")[^"]+(")',
        lambda m: m.group(1) + cover_rel + m.group(2),
        html
    )
    # Cover srcset
    html = re.sub(
        r'(srcset=")[^"]*(' + re.escape('" sizes="(max-width: 768px) 480px, 1200px"') + ')',
        lambda m: m.group(1) + thumb_rel + " 480w, " + cover_rel + " 1200w" + m.group(2),
        html
    )
    
    # Inline images
    figure_pattern = re.compile(
        r"(<figure[^>]*>\s*<img\s+src=')[^']+('[^>]*>)",
        re.DOTALL
    )
    inline_iter = iter([(i, r, n) for i, r, n in inline_results if r])
    def replace_figure_img(match):
        try:
            idx, result, name = next(inline_iter)
            return match.group(1) + f"../images/{name}" + match.group(2)
        except StopIteration:
            return match.group(0)
            
    html = figure_pattern.sub(replace_figure_img, html)
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    ok_count = 1 + sum(1 for _, r, _ in inline_results if r)
    print(f"  SAVED ({ok_count}/6 images) -> {slug[:50]}")
    return ok_count

async def main():
    html_files = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html")))
    print(f"\n{'=' * 65}")
    print("  REGEN ALL IMAGES V3 -- ART DIRECTOR (DEEPSEEK)")
    print(f"  {len(html_files)} articles x 6 images = {len(html_files) * 6} total")
    print(f"{'=' * 65}")
    
    total_ok = 0
    total_expected = len(html_files) * 6
    
    async with aiohttp.ClientSession() as session:
        for i, fp in enumerate(html_files, 1):
            ok = await process_article(session, fp, i, len(html_files))
            total_ok += ok
            if i < len(html_files):
                print("  Pausing 3s...")
                await asyncio.sleep(3)
                
    print(f"\n{'=' * 65}")
    print(f"  COMPLETE: {total_ok}/{total_expected} images generated")
    print(f"{'=' * 65}")

if __name__ == "__main__":
    asyncio.run(main())
