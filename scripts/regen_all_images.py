"""
Regenerate ALL article images for ALL 29 articles.
Uses the EXACT same Pollinations URL/params/auth as auto_blog_v6_ultimate.py.

URL: https://gen.pollinations.ai/image/{encoded_prompt}
Model: klein-large  (NOT flux)
Auth: Bearer from POLLINATIONS_API_KEY_1..5 env vars
Size: 1200x675 (cover & all content images)

Run: python scripts/regen_all_images.py
"""
import asyncio, aiohttp, json, glob, os, re, sys, time, urllib.parse
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
POSTS_DIR = os.path.join(PROJECT_ROOT, 'posts')
IMAGES_DIR = os.path.join(PROJECT_ROOT, 'images')

load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# === EXACT SAME CONFIG AS V6 ===
POLLINATIONS_MODEL = "klein-large"
IMAGE_WIDTH, IMAGE_HEIGHT = 1200, 675

# Load all API keys (primary + backup)
POLLINATIONS_KEYS = [os.getenv(f"POLLINATIONS_API_KEY_{i}") for i in range(1, 6)]
POLLINATIONS_KEYS = [k for k in POLLINATIONS_KEYS if k and len(k) > 5]
POLLINATIONS_BACKUP_KEYS = [os.getenv(f"POLLINATIONS_API_KEY_BCK_{i}") for i in range(1, 6)]
POLLINATIONS_BACKUP_KEYS = [k for k in POLLINATIONS_BACKUP_KEYS if k and len(k) > 5]

if not POLLINATIONS_KEYS:
    POLLINATIONS_KEYS = [""]  # anonymous fallback

ALL_KEYS = POLLINATIONS_KEYS + POLLINATIONS_BACKUP_KEYS

print(f"Pollinations keys loaded: {len(POLLINATIONS_KEYS)} primary + {len(POLLINATIONS_BACKUP_KEYS)} backup")

# === IMAGE STYLE PRESETS (matching V6 / prompt_templates.py) ===
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

async def fetch_image_v6(session, prompt, out_path, idx, attempt_offset=0):
    """Fetch image using EXACT V6 method: gen.pollinations.ai with auth bearer."""
    clean_prompt = re.sub(r'[^a-zA-Z0-9 ,.-]', '', prompt)
    encoded_prompt = urllib.parse.quote(clean_prompt)
    seed = int(time.time()) + idx * 100

    for attempt in range(8):
        # Key rotation like V6
        if attempt < 3:
            api_key = POLLINATIONS_KEYS[(idx + attempt) % len(POLLINATIONS_KEYS)] if POLLINATIONS_KEYS else ""
        elif POLLINATIONS_BACKUP_KEYS:
            api_key = POLLINATIONS_BACKUP_KEYS[(idx + attempt) % len(POLLINATIONS_BACKUP_KEYS)]
        else:
            api_key = POLLINATIONS_KEYS[0] if POLLINATIONS_KEYS else ""

        # EXACT V6 URL format
        url = f"https://gen.pollinations.ai/image/{encoded_prompt}"
        params = {
            "width": IMAGE_WIDTH,
            "height": IMAGE_HEIGHT,
            "seed": seed,
            "model": POLLINATIONS_MODEL,
            "nologo": "true",
            "enhance": "true"
        }
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            async with session.get(url, params=params, headers=headers,
                                    timeout=aiohttp.ClientTimeout(total=90)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    if len(data) > 1024:
                        img = Image.open(BytesIO(data)).convert("RGB")
                        img.thumbnail((1200, 1200))
                        img.save(out_path, "WEBP", quality=85, optimize=True, method=6)
                        size_kb = os.path.getsize(out_path) // 1024
                        print(f"      [OK] ({size_kb}KB) {os.path.basename(out_path)}")
                        return out_path
                    else:
                        print(f"      [WARN] attempt {attempt+1}: response too small ({len(data)} bytes)")
                else:
                    print(f"      [WARN] attempt {attempt+1}: HTTP {resp.status}")
        except Exception as e:
            print(f"      [ERR] attempt {attempt+1}: {e}")
        
        await asyncio.sleep(3)
        seed += 1

    print(f"      [FAIL] All attempts failed for {os.path.basename(out_path)}")
    return None


def build_image_prompt(concept, slug, preset_idx):
    """Build a rich prompt like V6 Art Director generates."""
    preset = IMAGE_STYLE_PRESETS[preset_idx % len(IMAGE_STYLE_PRESETS)]
    topic = slug.replace('-', ' ')
    return (
        f"{concept}, topic: {topic}, "
        f"style: {preset['style']}, "
        f"palette: {preset['palette']}, "
        f"lighting: {preset['lighting']}, "
        f"children aged 4-12, educational, child-safe, family-friendly, "
        f"no text no watermarks, no brand logos, diverse children, joyful and engaged"
    )


async def regenerate_article_images(session, pf):
    with open(pf, 'r', encoding='utf-8') as f:
        d = json.load(f)

    slug = d.get('slug', os.path.basename(pf))
    title = d.get('title', slug)
    category = d.get('category', 'Education')
    cover_concept = f"Children learning about {title}, bright educational scene"
    ts = int(time.time())

    print(f"\n{'=' * 65}")
    print(f"ARTICLE: {title[:65]}")
    print(f"  Slug:     {slug}")

    # === COVER IMAGE ===
    cover_out_name = f"{slug}-cover-{ts}.webp"
    cover_out_path = os.path.join(IMAGES_DIR, cover_out_name)
    cover_prompt = build_image_prompt(cover_concept, slug, 0)
    print(f"  [img 1/5] cover...")
    cover_result = await fetch_image_v6(session, cover_prompt, cover_out_path, 0)
    
    if not cover_result:
        print(f"  SKIP article — cover generation failed")
        return

    await asyncio.sleep(2)

    # === 4 CONTENT IMAGES ===
    content_results = []
    for i in range(1, 5):
        content_prompt = build_image_prompt(
            f"Educational activity scene {i} related to '{title}', engaging children",
            slug, i
        )
        out_name = f"{slug}-img{i}-{ts}.webp"
        out_path = os.path.join(IMAGES_DIR, out_name)
        print(f"  [img {i+1}/5] content img{i}...")
        result = await fetch_image_v6(session, content_prompt, out_path, i)
        content_results.append((i, result))
        await asyncio.sleep(2)

    # === UPDATE JSON ===
    # Update cover
    d['image'] = f"images/{cover_out_name}"

    # Rebuild inline content images (remove old figures, inject new)
    content = d.get('content', '')
    content = re.sub(r'<figure[^>]*>.*?</figure>', '', content, flags=re.DOTALL | re.IGNORECASE)

    new_fig_html = []
    for i, result in content_results:
        if result:
            rel_path = f"images/{os.path.basename(result)}"
            topic_words = title.replace("'", "").replace('"', '')[:80]
            alt = f"{topic_words} - educational activity illustration {i}"
            new_fig_html.append(
                f'\n<figure class="article-image my-8">\n'
                f'  <img src="../{rel_path}" alt="{alt}" loading="lazy" width="1200" height="675" class="w-full rounded-xl shadow-md">\n'
                f'</figure>\n'
            )

    # Inject after H2 tags evenly
    h2_matches = list(re.finditer(r'</h2>', content, re.IGNORECASE))
    if len(h2_matches) >= len(new_fig_html) and new_fig_html:
        step = max(1, len(h2_matches) // len(new_fig_html))
        positions = [h2_matches[min(i * step, len(h2_matches) - 1)].end() for i in range(len(new_fig_html))]
        for pos, html in sorted(zip(positions, new_fig_html), reverse=True):
            content = content[:pos] + html + content[pos:]
    else:
        content += '\n'.join(new_fig_html)

    d['content'] = content

    with open(pf, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)

    ok_count = 1 + sum(1 for _, r in content_results if r)
    print(f"  SAVED ({ok_count}/5 images ok): {os.path.basename(pf)}")


async def main():
    posts = sorted(glob.glob(os.path.join(POSTS_DIR, '*.json')))
    print(f"\nRegenerate images for {len(posts)} articles using Pollinations klein-large model")
    print(f"=  Exact same URL format as auto_blog_v6_ultimate.py  =\n")

    async with aiohttp.ClientSession() as session:
        for i, pf in enumerate(posts, 1):
            print(f"\n[{i}/{len(posts)}]", end='')
            await regenerate_article_images(session, pf)
            # Pause between articles to avoid rate limiting
            if i < len(posts):
                print(f"  Pausing 5s before next article...")
                await asyncio.sleep(5)

    print(f"\n{'=' * 65}")
    print("All articles updated. Now run: python scripts/build_articles.py")

asyncio.run(main())
