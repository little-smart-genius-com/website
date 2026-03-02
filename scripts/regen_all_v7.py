"""
REGEN ALL IMAGES V7 — Multi-Prompt + OG + Unique Variations
1. Deletes ALL existing images from images/, images/thumbs/, AND images/og/
2. For each article, generates Cover (Index 0), Img1 (Index 1), Img2 (Index 2), Img3 (Index 3), Img4 (Index 4)
   Each image position uses a distinct template from master_prompt.py (Golden Hour, Bright Morning, etc.)
3. Creates cover thumbnails (480x270)
4. Creates OG images (Open Graph) cropped/resized for social media sharing (1200x630) saved in images/og/
5. Updates all HTML src/srcset, og:image, twitter:image references to point to new filenames
Uses all 24 Pollinations keys in rotation. Model: klein-large.
DeepSeek Art Director writes ~40-60 word unique variations for the [SUBJECT] placeholder.
"""
import os, re, sys, glob, time, asyncio, urllib.parse
from io import BytesIO
import requests

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

try:
    import aiohttp
    from PIL import Image
except ImportError:
    os.system(f"{sys.executable} -m pip install aiohttp Pillow python-dotenv requests")
    import aiohttp
    from PIL import Image

from master_prompt import build_prompt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
THUMBS_DIR = os.path.join(IMAGES_DIR, "thumbs")
OG_DIR = os.path.join(IMAGES_DIR, "og")

# DeepSeek Config
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY_1")
if not DEEPSEEK_API_KEY:
    print("FATAL: DEEPSEEK_API_KEY_1 not found in .env")
    sys.exit(1)

# Pollinations config
POLLINATIONS_MODEL = "klein-large"
IMAGE_WIDTH = 1200
IMAGE_HEIGHT = 675

# Load ALL Pollinations API keys from .env
ALL_KEYS = []
for env_key, env_val in os.environ.items():
    if env_key.startswith("POLLINATIONS_API_KEY") and env_val.startswith("sk_"):
        ALL_KEYS.append(env_val)

seen = set()
unique_keys = []
for k in ALL_KEYS:
    if k not in seen:
        seen.add(k)
        unique_keys.append(k)
ALL_KEYS = unique_keys

if not ALL_KEYS:
    print("FATAL: No Pollinations API keys found in .env")
    sys.exit(1)

# Image roles for variety
IMAGE_ROLES = [
    "Cover -- main establishing shot",
    "Close-up -- children actively engaged",
    "Isometric -- kids collaborating from above",
    "Classroom -- focused learning moment",
    "Wide Shot -- group fun and achievement",
]

key_usage_idx = 0
TIMESTAMP = str(int(time.time()))

ART_DIRECTOR_SYSTEM_V7 = (
    "You are an expert Art Director for educational children's content. "
    "You will receive an article title, a section context, and an image role. "
    "Your ONLY job is to return a highly descriptive but concise subject text (around 40 to 60 words). "
    "This text will replace the [SUJET] placeholder in a master template. "
    "Ensure each description is unique, deeply tied to the core educational subject of the article, "
    "but offering a fresh variation on what the children are doing (different materials, interactions, expressions). "
    "DO NOT output full prompts, lighting, or style formatting. DO NOT include 'Pixar', '3D', 'no text', etc. "
    "Just describe the children's specific activity and immediate surroundings."
)

ART_DIRECTOR_USER_V7 = (
    "Article Title: {title}\n"
    "Context: {section}\n"
    "Role: {role}\n\n"
    "Write the ~40-60 word unique children's activity description:"
)

def ask_art_director(title, section_context, role):
    """Call DeepSeek for a ~60 word [SUJET] description."""
    user_msg = ART_DIRECTOR_USER_V7.format(
        title=title, section=section_context, role=role
    )
    for attempt in range(3):
        try:
            resp = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": ART_DIRECTOR_SYSTEM_V7},
                        {"role": "user", "content": user_msg}
                    ],
                    "temperature": 0.8,
                    "max_tokens": 150
                },
                timeout=15
            )
            if resp.status_code == 200:
                subject = resp.json()["choices"][0]["message"]["content"].strip()
                subject = subject.strip('"').strip("'").strip('`').strip()
                for bad in ["3D", "Pixar", "Disney", "no text", "watermark", "8k", "masterpiece"]:
                    if bad.lower() in subject.lower():
                        subject = re.sub(re.escape(bad), '', subject, flags=re.IGNORECASE).strip()
                subject = re.sub(r'\s+', ' ', subject).strip(' ,.')
                return subject
        except Exception:
            time.sleep(2)
    return f"eagerly working on {section_context} activities together, carefully placing pieces and smiling"


async def fetch_image(session, prompt, out_path):
    """Download image with key rotation."""
    global key_usage_idx
    clean_prompt = re.sub(r'[^a-zA-Z0-9 ,.\-]', '', prompt)
    encoded = urllib.parse.quote(clean_prompt)
    seed = int(time.time() * 1000) % 999999

    for attempt in range(len(ALL_KEYS) * 2): # Try wrapped around if needed
        key = ALL_KEYS[key_usage_idx % len(ALL_KEYS)]
        key_usage_idx += 1

        url = f"https://gen.pollinations.ai/image/{encoded}"
        params = {
            "width": IMAGE_WIDTH, "height": IMAGE_HEIGHT,
            "seed": seed + attempt, "model": POLLINATIONS_MODEL,
            "nologo": "true", "enhance": "true"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Authorization": f"Bearer {key}"
        }

        try:
            async with session.get(url, params=params, headers=headers,
                                   timeout=aiohttp.ClientTimeout(total=90)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    if len(data) > 2048:
                        img = Image.open(BytesIO(data)).convert("RGB")
                        img.save(out_path, "WEBP", quality=85, optimize=True, method=6)
                        size_kb = os.path.getsize(out_path) // 1024
                        print(f"      [OK] {size_kb}KB -> {os.path.basename(out_path)}")
                        return True
                    else:
                        print(f"      [WARN] attempt {attempt+1}: too small")
                else:
                    print(f"      [WARN] attempt {attempt+1}: HTTP {resp.status}")
        except Exception as e:
            print(f"      [ERR] attempt {attempt+1}: {str(e)[:50]}")

        await asyncio.sleep(2)

    print(f"      [FAIL] All keys exhausted/failed for {os.path.basename(out_path)}")
    return False


def get_h2_contexts(html):
    """Extract H2 section titles (excluding FAQ)."""
    h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)
    # Default fallbacks if fewer than 4 H2s
    contexts = [
        re.sub(r'<[^>]+>', '', h2).strip()
        for h2 in h2s
        if 'faq' not in h2.lower() and 'frequently' not in h2.lower()
    ]
    while len(contexts) < 4:
        contexts.append(f"Educational Activity {len(contexts) + 1}")
    return contexts


def delete_all_images():
    """Delete ALL existing images, thumbs, and og."""
    count = 0
    dirs = [IMAGES_DIR, THUMBS_DIR, OG_DIR]
    exts = ["*.webp", "*.png", "*.jpg", "*.jpeg"]
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)
            continue
        for ext in exts:
            for f in glob.glob(os.path.join(d, ext)):
                try:
                    os.remove(f)
                    count += 1
                except:
                    pass
    return count

def update_html_images(html_path, slug, new_files):
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    cover_fn = new_files.get("cover", "")
    thumb_fn = cover_fn
    og_fn = new_files.get("og", "")

    # ------- META TAGS (OG and Twitter) -------
    if og_fn:
        # og:image
        html = re.sub(
            r'<meta property="og:image"\s+content="[^"]*?"\s*>',
            f'<meta property="og:image" content="https://littlesmartgenius.com/images/og/{og_fn}">',
            html
        )
        html = re.sub(
            r'<meta property="og:image"\s+content="[^"]*?"\s*/>',
            f'<meta property="og:image" content="https://littlesmartgenius.com/images/og/{og_fn}">',
            html
        )
        # twitter:image
        html = re.sub(
            r'<meta name="twitter:image"\s+content="[^"]*?"\s*>',
            f'<meta name="twitter:image" content="https://littlesmartgenius.com/images/og/{og_fn}">',
            html
        )
        html = re.sub(
            r'<meta name="twitter:image"\s+content="[^"]*?"\s*/>',
            f'<meta name="twitter:image" content="https://littlesmartgenius.com/images/og/{og_fn}">',
            html
        )

    # ------- COVER IMAGE -------
    cover_pattern = re.compile(
        r'(<img\s[^>]*?fetchpriority="high"[^>]*?)src="\.\.\/images\/[^"]*?"(.*?)srcset="[^"]*?"',
        re.DOTALL
    )
    if cover_fn:
        def cover_replace(m):
            return (
                f'{m.group(1)}src="../images/{cover_fn}"{m.group(2)}'
                f'srcset="../images/thumbs/{thumb_fn} 480w, ../images/{cover_fn} 1200w"'
            )
        html = cover_pattern.sub(cover_replace, html)

    # ------- INLINE FIGURE IMAGES (img1..img4) -------
    for i in range(1, 5):
        suffix = f"img{i}"
        fn = new_files.get(suffix)
        if not fn:
            continue
        new_src = f"src='../images/{fn}'"
        # Regex replaces the first match iteratively to keep them in order
        html = re.sub(
            r"<figure class='my-8'>\s*<img src='\.\.\/images\/[^']*?\.(?:webp|jpg|png)'",
            f"<figure class='my-8'><img {new_src}",
            html,
            count=1
        )

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)


async def process_article(session, html_path, article_num, total, all_covers):
    slug = os.path.basename(html_path).replace(".html", "")

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    title_match = re.search(r'<title>([^<]+)</title>', html)
    title = title_match.group(1).replace(" | Little Smart Genius", "").strip() if title_match else slug

    h2_contexts = get_h2_contexts(html)
    new_files = {}

    print(f"\n{'=' * 65}")
    print(f"[{article_num}/{total}] {title[:60]}")

    # --- COVER (Index 0 - Golden Hour) ---
    cover_fn = f"{slug}-cover-{TIMESTAMP}.webp"
    cover_path = os.path.join(IMAGES_DIR, cover_fn)

    print("  [1/5] Art Director -> SUBJECT for cover...")
    subject = ask_art_director(title, "main cover hero image for the entire article", IMAGE_ROLES[0])
    full_prompt = build_prompt(subject, image_index=0)

    ok = await fetch_image(session, full_prompt, cover_path)
    if ok:
        new_files["cover"] = cover_fn
        # Create Thumb
        thumb_path = os.path.join(THUMBS_DIR, cover_fn)
        img = Image.open(cover_path)
        img.thumbnail((480, 270))
        img.save(thumb_path, "WEBP", quality=80, optimize=True, method=6)
        all_covers[slug] = cover_fn
        
        # Create OG image (crop 1200x675 to 1200x630)
        og_fn = f"{slug}-og-{TIMESTAMP}.webp"
        og_path = os.path.join(OG_DIR, og_fn)
        og_img = img.copy()
        width, height = og_img.size
        left = 0
        top = (height - 630) / 2 if height > 630 else 0
        right = width
        bottom = (height + 630) / 2 if height > 630 else height
        og_cropped = og_img.crop((left, top, right, bottom))
        og_cropped.save(og_path, "WEBP", quality=85, optimize=True, method=6)
        new_files["og"] = og_fn

    # --- INLINE IMAGES (Index 1 to 4) ---
    for i in range(1, 5):
        suffix = f"img{i}"
        img_fn = f"{slug}-{suffix}-{TIMESTAMP}.webp"
        img_path = os.path.join(IMAGES_DIR, img_fn)

        ctx = h2_contexts[i-1]
        role = IMAGE_ROLES[i % len(IMAGE_ROLES)]

        print(f"  [{i+1}/5] Art Director -> SUBJECT for {suffix}...")
        subject = ask_art_director(title, ctx, role)
        # We pass image_index = i
        full_prompt = build_prompt(subject, image_index=i)

        ok = await fetch_image(session, full_prompt, img_path)
        if ok:
            new_files[suffix] = img_fn

        await asyncio.sleep(1)

    # Update HTML
    if new_files:
        update_html_images(html_path, slug, new_files)

    generated = len(new_files) - 1 # excluding og
    print(f"  DONE: {generated}/5 base images (+ thumb & og) for {slug}")
    return generated

def fix_related_thumbnails(all_covers):
    articles = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html")))
    fixes = 0
    print(f"\n{'=' * 65}\n  FIXING RELATED ARTICLE THUMBNAILS\n{'=' * 65}")
    for html_path in articles:
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        modified = False
        for rel_slug, rel_cover in all_covers.items():
            pattern = re.compile(
                r'(<a\s+href="\.\.\/articles/' + re.escape(rel_slug) + r'\.html"[^>]*>.*?'
                r'<img\s[^>]*?)src="[^"]*?"(.*?)srcset="[^"]*?"(.*?</a>)',
                re.DOTALL
            )
            def repl(m):
                return (
                    f'{m.group(1)}src="../images/thumbs/{rel_cover}"'
                    f'{m.group(2)}srcset="../images/thumbs/{rel_cover} 480w, ../images/{rel_cover} 1200w"'
                    f'{m.group(3)}'
                )
            new_html, n = pattern.subn(repl, html)
            if n > 0:
                html = new_html
                modified = True
                fixes += n

        if modified:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
    print(f"  Fixed {fixes} related thumbnail references")
    return fixes

async def main():
    html_files = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html")))
    print("\n" + "=" * 65)
    print("  REGEN ALL IMAGES V7 — MULTI-PROMPT + OG + UNIQUE VARIATIONS")
    print(f"  {len(html_files)} articles. Generating Cover(Idx 0) and Img1-4(Idx 1-4).")
    print("=" * 65)

    print("\n  STEP 1: Deleting ALL existing images (images/, thumbs/, og/)...")
    deleted = delete_all_images()
    print(f"  Deleted {deleted} files")

    total_base_generated = 0
    all_covers = {}

    async with aiohttp.ClientSession() as session:
        for i, fp in enumerate(html_files, 1):
            ok = await process_article(session, fp, i, len(html_files), all_covers)
            total_base_generated += ok

    fix_related_thumbnails(all_covers)

    print(f"\n{'=' * 65}")
    print(f"  COMPLETE: {total_base_generated} base images generated.")
    print("  All HTML references (src, srcset, og:image, twitter:image) updated.")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(main())
