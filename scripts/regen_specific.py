import asyncio, aiohttp, json, glob, os, re, sys, time, urllib.parse
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
IMAGES_DIR = os.path.join(PROJECT_ROOT, 'images')

load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

POLLINATIONS_MODEL = "klein-large"
IMAGE_WIDTH, IMAGE_HEIGHT = 1200, 675

POLLINATIONS_KEYS = [os.getenv(f"POLLINATIONS_API_KEY_{i}") for i in range(1, 6)]
POLLINATIONS_KEYS = [k for k in POLLINATIONS_KEYS if k and len(k) > 5]
POLLINATIONS_BACKUP_KEYS = [os.getenv(f"POLLINATIONS_API_KEY_BCK_{i}") for i in range(1, 6)]
POLLINATIONS_BACKUP_KEYS = [k for k in POLLINATIONS_BACKUP_KEYS if k and len(k) > 5]

if not POLLINATIONS_KEYS:
    POLLINATIONS_KEYS = [""]

IMAGE_STYLE_PRESETS = [
    {
        "name": "Hero Scene",
        "style": "3D Pixar-style, vibrant, ultra-detailed, colorful, educational",
        "palette": "Brand orange (#F48C06), white, slate blue, sunshine yellow",
        "lighting": "Soft rim lighting, warm golden hour",
    },
    {
        "name": "Action Learning",
        "style": "3D Pixar-style, dynamic composition, bright classroom",
        "palette": "Warm coral, teal accent, off-white background",
        "lighting": "Bright natural classroom light",
    },
    {
        "name": "Close-Up Detail",
        "style": "3D illustration, macro product shot, high detail, educational material",
        "palette": "Pastel tones, brand orange highlight",
        "lighting": "Even studio lighting",
    },
    {
        "name": "Group Activity",
        "style": "3D Pixar-style, diverse children, collaborative, joyful",
        "palette": "Rainbow accents, warm white background, brand orange",
        "lighting": "Bright diffused classroom light",
    },
    {
        "name": "Creative Workspace",
        "style": "Top-down flat lay, 3D Pixar-style, colorful, vibrant, ultra-detailed",
        "palette": "Brand orange (#F48C06), white, slate blue, sunshine yellow",
        "lighting": "Bright even studio lighting, clean background",
    },
]

# TARGETED FILES
TARGET_FILES = [
    "data/archive_posts/therapeutic-coloring-pages-for-anxious-kids-ultimate-guide-1773036450.json",
    "data/archive_posts/word-searches-boost-kids-vocabulary-cognitive-skills-1773063472.json",
    "data/archive_posts/word-searches-build-thanksgiving-vocabulary-for-kids-1773065007.json"
]

async def fetch_image_v6(session, prompt, out_path, idx, attempt_offset=0):
    clean_prompt = re.sub(r'[^a-zA-Z0-9 ,.-]', '', prompt)
    encoded_prompt = urllib.parse.quote(clean_prompt)
    seed = int(time.time()) + idx * 100

    for attempt in range(8):
        if attempt < 3:
            api_key = POLLINATIONS_KEYS[(idx + attempt) % len(POLLINATIONS_KEYS)] if POLLINATIONS_KEYS else ""
        elif POLLINATIONS_BACKUP_KEYS:
            api_key = POLLINATIONS_BACKUP_KEYS[(idx + attempt) % len(POLLINATIONS_BACKUP_KEYS)]
        else:
            api_key = POLLINATIONS_KEYS[0] if POLLINATIONS_KEYS else ""

        url = f"https://gen.pollinations.ai/image/{encoded_prompt}"
        params = {
            "width": IMAGE_WIDTH,
            "height": IMAGE_HEIGHT,
            "seed": seed,
            "model": POLLINATIONS_MODEL,
            "nologo": "true",
            "enhance": "true"
        }
        headers = {"User-Agent": "Mozilla/5.0"}
        if api_key: headers["Authorization"] = f"Bearer {api_key}"

        try:
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=90)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    if len(data) > 1024:
                        img = Image.open(BytesIO(data)).convert("RGB")
                        img.thumbnail((1200, 1200)) # Compress
                        img.save(out_path, "WEBP", quality=85, optimize=True, method=6)
                        print(f"      [OK] {os.path.basename(out_path)}")
                        return out_path
                    else:
                        print(f"      [WARN] too small ({len(data)} bytes) ATTEMPT {attempt+1}")
                else:
                    print(f"      [WARN] HTTP {resp.status} ATTEMPT {attempt+1}")
        except Exception as e:
            pass
        await asyncio.sleep(2)
        seed += 1
    return None

NO_TEXT_SUFFIX = ", ABSOLUTELY NO text, letters, words, numbers, titles, captions, labels, watermarks, or UI overlays in the image, pure visual storytelling only"

def build_image_prompt(concept, slug, preset_idx):
    preset = IMAGE_STYLE_PRESETS[preset_idx % len(IMAGE_STYLE_PRESETS)]
    topic = slug.replace('-', ' ')
    return (
        f"{concept}, topic: {topic}, "
        f"style: {preset['style']}, "
        f"palette: {preset['palette']}, "
        f"lighting: {preset['lighting']}, "
        f"children aged 4-12, educational, child-safe, family-friendly, "
        f"no text no watermarks, no brand logos, no written words or numbers, "
        f"diverse children, joyful and engaged"
        + NO_TEXT_SUFFIX
    )

async def regenerate_article_images(session, pf):
    full_path = os.path.join(PROJECT_ROOT, pf)
    print(full_path)
    with open(full_path, 'r', encoding='utf-8') as f:
        d = json.load(f)

    slug = d.get('slug', os.path.basename(pf))
    title = d.get('title', slug)
    ts = int(time.time())

    print(f"\nARTICLE: {title}")
    
    # === COVER IMAGE ===
    cover_out_name = f"{slug}-cover-{ts}.webp"
    cover_out_path = os.path.join(IMAGES_DIR, cover_out_name)
    cover_prompt = build_image_prompt(f"Children learning about {title}, bright educational scene", slug, 0)
    print(f"  [img 1/6] cover...")
    cover_result = await fetch_image_v6(session, cover_prompt, cover_out_path, 0)

    # === 5 CONTENT IMAGES ===
    content_results = []
    for i in range(1, 6):
        content_prompt = build_image_prompt(f"Educational activity scene {i} related to '{title}', engaging children", slug, i)
        out_name = f"{slug}-img{i}-{ts}.webp"
        out_path = os.path.join(IMAGES_DIR, out_name)
        print(f"  [img {i+1}/6] content img{i}...")
        result = await fetch_image_v6(session, content_prompt, out_path, i)
        content_results.append((i, result))
        await asyncio.sleep(1)

    # Update cover
    if cover_result:
        d['image'] = f"images/{cover_out_name}"

    # Rebuild content HTML
    content = d.get('content', '')
    
    # The JSON files either have NO figures or placehold figures. Let's just remove all figures.
    content = re.sub(r'<figure[^>]*>.*?</figure>', '', content, flags=re.DOTALL | re.IGNORECASE)

    # If placehold.co images are generated via pure <img> tags, let's remove those too.
    content = re.sub(r'<img[^>]+placehold[^>]+>', '', content, flags=re.DOTALL | re.IGNORECASE)

    new_fig_html = []
    for i, result in content_results:
        if result:
            rel_path = f"images/{os.path.basename(result)}"
            alt = f"{title.replace('\"', '')[:80]} illustrative snippet {i}"
            new_fig_html.append(
                f'\n<figure class="article-image my-8">\n'
                f'  <img src="../{rel_path}" alt="{alt}" loading="lazy" width="1200" height="675" class="w-full rounded-xl shadow-md">\n'
                f'</figure>\n'
            )

    # Inject evenly before/after h2s. We can split by <h2>
    parts = re.split(r'(<h2[^>]*>)', content, flags=re.IGNORECASE)
    # the parts will be: [text1, h2, text2, h2, text3...]
    
    final_content = parts[0]
    for idx in range(1, len(parts), 2):
        h2_tag = parts[idx]
        section_text = parts[idx+1]
        
        # Inject figure if we have any left
        if len(new_fig_html) > 0 and idx/2 <= len(content_results): 
           # Simplistic injection: just pop one and put it after the H2 tag closing, or right after the H2 element
           # Let's just inject it at the end of the section text, before the next H2
           final_content += h2_tag + section_text
           fig = new_fig_html.pop(0)
           final_content += fig
        else:
           final_content += h2_tag + section_text
           
    # if any leftover
    if new_fig_html:
        final_content += "\n".join(new_fig_html)

    d['content'] = final_content

    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)

    print(f"  SAVED JSON UPDATE: {os.path.basename(pf)}")

async def main():
    async with aiohttp.ClientSession() as session:
        for pf in TARGET_FILES:
            await regenerate_article_images(session, pf)
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
