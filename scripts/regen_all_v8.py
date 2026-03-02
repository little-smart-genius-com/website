"""
REGEN ALL IMAGES V8 — Ultimate 6-Image Prompts + DeepSeek Art Director
1. Deletes ALL existing images from images/ and images/thumbs/
2. For each article, generates 6 images:
   - Cover (Index 0): Intense Golden Hour
   - Img1 (Index 1): Bright & Airy Morning
   - Img2 (Index 2): Cozy Evening Intimacy
   - Img3 (Index 3): Soft Dappled Natural Light
   - Img4 (Index 4): Vibrant & Joyful Daytime
   - Img5 (Index 5): Soft Overcast Diffused Light
3. Creates cover thumbnails (480x270).
4. Updates HTML src/srcset to reflect new names. Injects Img5 if missing in HTML.
5. Employs 24 Pollinations keys in rotation to bypass HTTP 402.

NOTE: OG generation is omitted from this script, to be run subsequently via `generate_og_images.py`.
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

# DeepSeek Config
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY_1")
if not DEEPSEEK_API_KEY:
    print("FATAL: DEEPSEEK_API_KEY_1 not found in .env")
    sys.exit(1)

# Pollinations config
POLLINATIONS_MODEL = "klein-large"
IMAGE_WIDTH = 1200
IMAGE_HEIGHT = 675

# Load ALL Pollinations API keys
ALL_KEYS = []
for env_key, env_val in os.environ.items():
    if env_key.startswith("POLLINATIONS_API_KEY") and env_val.startswith("sk_"):
        ALL_KEYS.append(env_val)

unique_keys = list(set(ALL_KEYS))
if not unique_keys:
    print("FATAL: No Pollinations API keys found in .env")
    sys.exit(1)
ALL_KEYS = unique_keys

# Image roles for variety
IMAGE_ROLES = [
    "Cover -- main establishing shot",
    "Close-up -- children actively engaged",
    "Isometric -- kids collaborating from above",
    "Classroom -- focused learning moment",
    "Wide Shot -- group fun and achievement",
    "Over-the-shoulder -- detailed view of hands/materials",
]

key_usage_idx = 0
TIMESTAMP = str(int(time.time()))

ART_DIRECTOR_SYSTEM_V8 = (
    "You are an expert Art Director for educational children's content. "
    "Your ONLY job is to return a highly descriptive, unique, and highly creative subject text (around 60 to 90 words). "
    "This text will replace the [SUJET] placeholder in a film-grade Pixar template. "
    "You MUST be extremely creative. Each image in the article must have a completely distinct scene, action, "
    "and materials based specifically on the provided H2 Section Context. "
    "CRITICAL REQUIREMENTS:\n"
    "1. All characters (children AND adults) MUST be explicitly described as joyful, happy, and having glowing smiles.\n"
    "2. NO characters should have their tongues sticking out (mouths closed or gently smiling).\n"
    "3. IMPORTANT: Include a mix of characters. Do not only feature children. Frequently include a parent or a teacher actively enthusiastically playing, guiding, or cooperating with the kids.\n"
    "4. Detail specific, tangible, interactive educational props (e.g., holding a shiny magnifying glass, assembling large colorful floor puzzles, moving pieces on a board game, coloring on vibrant worksheets).\n"
    "5. Emphasize a warm, cozy, highly detailed classroom or home environment with sunlight streaming in.\n"
    "6. DO NOT output full prompts, lighting terminology, or style formatting. DO NOT include 'Pixar', '3D', 'Golden Hour', etc.\n"
    "Just describe the specific unique characters, their activity with props, their physical appearance, and their surroundings."
)

ART_DIRECTOR_USER_V8 = (
    "Article Title: {title}\n"
    "Context: {section}\n"
    "Role: {role}\n\n"
    "Write the ~40-60 word unique children's activity description:"
)

def ask_art_director(title, section_context, role):
    user_msg = ART_DIRECTOR_USER_V8.format(title=title, section=section_context, role=role)
    for attempt in range(3):
        try:
            resp = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": ART_DIRECTOR_SYSTEM_V8},
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
                # Clean out instructions leak
                for bad in ["3D", "Pixar", "Disney", "Golden hour", "lighting", "shadow"]:
                    if bad.lower() in subject.lower():
                        subject = re.sub(re.escape(bad), '', subject, flags=re.IGNORECASE).strip()
                subject = re.sub(r'\s+', ' ', subject).strip(' ,.')
                return subject
        except Exception:
            time.sleep(2)
    return f"engaged in {section_context} activities together, carefully placing pieces and smiling"

async def fetch_image(session, prompt, out_path):
    global key_usage_idx
    clean_prompt = re.sub(r'[^a-zA-Z0-9 ,.\-]', '', prompt)
    encoded = urllib.parse.quote(clean_prompt)
    seed = int(time.time() * 1000) % 999999

    for attempt in range(len(ALL_KEYS) * 2): # Wrap around retries
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
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=90)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    if len(data) > 2048:
                        img = Image.open(BytesIO(data)).convert("RGB")
                        img.save(out_path, "WEBP", quality=85, optimize=True, method=6)
                        size_kb = os.path.getsize(out_path) // 1024
                        print(f"      [OK] {size_kb}KB -> {os.path.basename(out_path)}")
                        return True
                    else:
                        print(f"      [WARN] attempt {attempt+1}: image too small")
                else:
                    print(f"      [WARN] attempt {attempt+1}: HTTP {resp.status}")
        except Exception as e:
            print(f"      [ERR] attempt {attempt+1}: {str(e)[:50]}")

        await asyncio.sleep(2)

    print(f"      [FAIL] All keys exhausted/failed for {os.path.basename(out_path)}")
    return False

def get_h2_contexts(html):
    h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)
    contexts = [
        re.sub(r'<[^>]+>', '', h2).strip()
        for h2 in h2s
        if 'faq' not in h2.lower() and 'frequently' not in h2.lower()
    ]
    while len(contexts) < 5:  # We need up to 5 inline images
        contexts.append(f"Educational Activity {len(contexts) + 1}")
    return contexts

def delete_all_images():
    count = 0
    dirs = [IMAGES_DIR, THUMBS_DIR, os.path.join(IMAGES_DIR, "og")]
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

    # ------- COVER -------
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

    # ------- INLINE IMAGES (img1 to img5) -------
    for i in range(1, 6):
        suffix = f"img{i}"
        fn = new_files.get(suffix)
        if not fn:
            continue

        new_figure = (
            f"<div style=\"margin: 2.5rem 0;\">"
            f"<figure class='my-8'><img src='../images/{fn}' alt='{slug}-{suffix}' "
            f"loading='lazy' width='1200' height='675' class='w-full rounded-xl shadow-md' "
            f"style=\"background: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy5wMy5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9IiNlMmU4ZjAiLz48L3N2Zz4=') center/cover; background-color: var(--bord);\"></figure>"
            f"</div>"
        )
        
        pattern = r"<div style=\"margin: 2\.5rem 0;\"><figure class='my-8'><img src='\.\.\/images\/[^']*?\.(?:webp|jpg|png)'[^>]*><\/figure><\/div>"
        new_html, count = re.subn(pattern, new_figure, html, count=1)
        
        if count == 0:
            # Inject before cta-box if not found (mostly for img5)
            html = html.replace(
                '<div class="cta-box"',
                f'{new_figure}\n<div class="cta-box"'
            )
        else:
            html = new_html

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

    # --- COVER (Index 0) ---
    cover_fn = f"{slug}-cover-{TIMESTAMP}.webp"
    cover_path = os.path.join(IMAGES_DIR, cover_fn)

    print("  [1/6] Art Director -> SUBJECT for cover (Idx 0: Golden Hour)...")
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

    # --- INLINE IMAGES (Index 1 to 5) ---
    for i in range(1, 6):
        suffix = f"img{i}"
        img_fn = f"{slug}-{suffix}-{TIMESTAMP}.webp"
        img_path = os.path.join(IMAGES_DIR, img_fn)

        ctx = h2_contexts[(i-1) % len(h2_contexts)]
        role = IMAGE_ROLES[i % len(IMAGE_ROLES)]

        print(f"  [{i+1}/6] Art Director -> SUBJECT for {suffix} (Idx {i})...")
        subject = ask_art_director(title, ctx, role)
        full_prompt = build_prompt(subject, image_index=i)

        ok = await fetch_image(session, full_prompt, img_path)
        if ok:
            new_files[suffix] = img_fn

        await asyncio.sleep(1)

    if new_files:
        update_html_images(html_path, slug, new_files)

    generated = len(new_files)
    if "cover" in new_files: generated -= 1 # 5 inlines
    print(f"  DONE: {generated}/5 inline + cover for {slug}")
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
    print("  REGEN ALL IMAGES V8 — ULTIMATE 6-IMAGE PROMPTS + API ROTATION")
    print(f"  {len(html_files)} articles. Cover(Idx 0) + Img1-5(Idx 1-5).")
    print("=" * 65)

    print("\n  STEP 1: Deleting ALL existing base images (images/, thumbs/)...")
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
    print(f"  COMPLETE: {total_base_generated} inline images + covers generated.")
    print("  All HTML references (src, srcset) updated. Img5 injected where missing.")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(main())
