"""
REGEN ALL IMAGES V2 — Regenerate ALL images for ALL 28 articles.
Generates 5 inline images per article via Pollinations API.
Updates HTML files directly with new image paths.
Also generates thumbnails.

Uses dotenv to load .env keys.
"""
import os, re, sys, json, glob, time, asyncio, urllib.parse
from io import BytesIO

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

try:
    import aiohttp
    from PIL import Image
except ImportError:
    print("Installing required packages...")
    os.system(f"{sys.executable} -m pip install aiohttp Pillow python-dotenv")
    import aiohttp
    from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
THUMBS_DIR = os.path.join(IMAGES_DIR, "thumbs")
POSTS_DIR = os.path.join(PROJECT_ROOT, "posts")

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(THUMBS_DIR, exist_ok=True)

# Pollinations config
POLLINATIONS_MODEL = "klein-large"
IMAGE_WIDTH = 1200
IMAGE_HEIGHT = 675

# Hardcoded backup keys (confirmed working)
ALL_KEYS = [
    "sk_zFSrdglC0wCer6A9QOuT9LNcxeraudoS",
    "sk_MuNrWlfnjYPhHUWiFDdIssBlDTz7O9LQ",
    "sk_lbGdwBcJksNBBUmG3Ue0c5dFH4uy8Qjs",
    "sk_6vowoM6O3RhZUiK8i5YJRyyaERJLPxe2",
    "sk_Clz42THes7uwrIXueXUxsb5zyq4gYnhu",
]
POLLINATIONS_BACKUP_KEYS = ALL_KEYS

print(f"Pollinations backup keys loaded: {len(ALL_KEYS)}")

# Image presets per position (matching V6 style)
IMAGE_PRESETS = [
    {"name": "Hero Cover", "style": "3D Pixar-style character illustration, vibrant, ultra-detailed, colorful educational scene"},
    {"name": "Activity Close-up", "style": "3D Pixar-style character illustration, close-up overhead shot, warm natural lighting, cute child hands with educational materials"},
    {"name": "Interactive Scene", "style": "3D Pixar-style character illustration, isometric view, diverse cute children joyfully engaged in learning activity"},
    {"name": "Detailed Tutorial", "style": "3D Pixar-style character illustration, child's eye view looking down at hands working on educational activity"},
    {"name": "Group Activity", "style": "3D Pixar-style character illustration, top-down flat lay of diverse cute children in modern classroom, bright colorful"},
    {"name": "Results & Joy", "style": "3D Pixar-style character illustration, wide shot of excited diverse cute children proudly showing completed work"},
]

NO_TEXT_SUFFIX = (
    ", ABSOLUTELY NO text, letters, words, numbers, titles, captions, labels, "
    "watermarks, or UI overlays in the image, pure visual storytelling only"
)


def build_prompt(title, section_context, img_idx):
    """Build a rich image prompt based on article context."""
    preset = IMAGE_PRESETS[img_idx % len(IMAGE_PRESETS)]
    
    # Clean title for prompt
    clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', title)[:80]
    
    if img_idx == 0:
        # Cover image
        prompt = (
            f"{preset['style']}, children learning about {clean_title}, "
            f"bright educational scene with diverse kids aged 4-12, "
            f"warm inviting atmosphere, premium quality illustration"
        )
    else:
        # Content images - use section context
        prompt = (
            f"{preset['style']}, {section_context}, "
            f"educational scene related to {clean_title}, "
            f"diverse children engaged in learning, warm lighting"
        )
    
    return prompt + NO_TEXT_SUFFIX


async def fetch_image(session, prompt, out_path, idx):
    """Download image from Pollinations API with retry logic."""
    clean_prompt = re.sub(r'[^a-zA-Z0-9 ,.-]', '', prompt)
    encoded = urllib.parse.quote(clean_prompt)
    seed = int(time.time()) + idx * 100

    for attempt in range(8):
        # Key rotation
        key_idx = (idx + attempt) % len(ALL_KEYS) if ALL_KEYS else 0
        api_key = ALL_KEYS[key_idx] if ALL_KEYS else ""

        url = f"https://gen.pollinations.ai/image/{encoded}"
        params = {
            "width": IMAGE_WIDTH,
            "height": IMAGE_HEIGHT,
            "seed": seed + attempt,
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
    """Extract H2 section titles to use as image context."""
    h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)
    contexts = []
    for h2 in h2s:
        text = re.sub(r'<[^>]+>', '', h2).strip()
        if text and 'faq' not in text.lower() and 'frequently' not in text.lower():
            contexts.append(text)
    return contexts


async def process_article(session, html_path, article_num, total):
    """Regenerate all images for one article."""
    slug = os.path.basename(html_path).replace(".html", "")
    
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Extract title
    title_match = re.search(r'<title>([^<]+)</title>', html)
    title = title_match.group(1).replace(" | Little Smart Genius", "").strip() if title_match else slug
    
    ts = int(time.time())
    
    print(f"\n{'=' * 65}")
    print(f"[{article_num}/{total}] {title[:60]}")
    
    # Get H2 sections for contextual prompts
    h2_contexts = get_h2_contexts(html)
    
    # === GENERATE COVER IMAGE ===
    cover_name = f"{slug}-cover-{ts}.webp"
    cover_path = os.path.join(IMAGES_DIR, cover_name)
    cover_prompt = build_prompt(title, "main cover hero image", 0)
    
    print(f"  [1/6] cover...")
    cover_result = await fetch_image(session, cover_prompt, cover_path, 0)
    
    if not cover_result:
        print(f"  SKIP — cover failed")
        return 0
    
    # Generate thumbnail
    thumb_name = f"{slug}-cover-{ts}.webp"
    thumb_path = os.path.join(THUMBS_DIR, thumb_name)
    img = Image.open(cover_path)
    img.thumbnail((480, 270))
    img.save(thumb_path, "WEBP", quality=80, optimize=True, method=6)
    
    await asyncio.sleep(2)
    
    # === GENERATE 5 INLINE IMAGES ===
    inline_results = []
    for i in range(1, 6):
        context = h2_contexts[i-1] if i <= len(h2_contexts) else f"educational activity {i}"
        prompt = build_prompt(title, context, i)
        
        img_name = f"{slug}-img{i}-{ts}.webp"
        img_path = os.path.join(IMAGES_DIR, img_name)
        
        print(f"  [{i+1}/6] img{i}...")
        result = await fetch_image(session, prompt, img_path, i)
        inline_results.append((i, result, img_name))
        await asyncio.sleep(2)
    
    # === UPDATE HTML ===
    # 1. Replace cover image src
    cover_rel = f"../images/{cover_name}"
    thumb_rel = f"../images/thumbs/{thumb_name}"
    
    # Update cover src
    html = re.sub(
        r'(<img[^>]*class="w-full h-auto object-cover"[^>]*src=")[^"]+(")',
        lambda m: m.group(1) + cover_rel + m.group(2),
        html
    )
    # Also update cover srcset if it exists
    html = re.sub(
        r'(srcset=")[^"]*(' + re.escape('" sizes="(max-width: 768px) 480px, 1200px"') + ')',
        lambda m: m.group(1) + thumb_rel + " 480w, " + cover_rel + " 1200w" + m.group(2),
        html
    )
    
    # 2. Replace inline images (figure > img tags in article-content)
    # Find all figure img tags and replace them in order
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
    
    # 3. Also fix any remaining placeholder.webp references
    for i, result, name in inline_results:
        if result:
            html = html.replace("../images/placeholder.webp", f"../images/{name}", 1)
    
    # 4. Update related articles thumbnails if they reference this article's cover
    # (These will be updated by their own articles' regeneration)
    
    # Save updated HTML
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    ok_count = 1 + sum(1 for _, r, _ in inline_results if r)
    print(f"  SAVED ({ok_count}/6 images) -> {slug[:50]}")
    
    return ok_count


async def main():
    html_files = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html")))
    
    print(f"\n{'=' * 65}")
    print(f"  REGEN ALL IMAGES V2")
    print(f"  {len(html_files)} articles x 6 images = {len(html_files) * 6} total")
    print(f"  Backup keys: {len(POLLINATIONS_BACKUP_KEYS)}")
    print(f"{'=' * 65}")
    
    total_ok = 0
    total_expected = len(html_files) * 6
    
    async with aiohttp.ClientSession() as session:
        for i, fp in enumerate(html_files, 1):
            ok = await process_article(session, fp, i, len(html_files))
            total_ok += ok
            if i < len(html_files):
                print(f"  Pausing 3s...")
                await asyncio.sleep(3)
    
    print(f"\n{'=' * 65}")
    print(f"  COMPLETE: {total_ok}/{total_expected} images generated")
    print(f"  Success rate: {total_ok * 100 // total_expected}%")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    asyncio.run(main())
