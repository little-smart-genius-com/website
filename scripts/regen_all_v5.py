"""
REGEN ALL IMAGES V5 — Clean Slate Master Prompt Edition
1. Deletes ALL existing images from images/ and images/thumbs/
2. For each article, generates cover + img1..img4 (5 images) via Art Director + Master Prompt
3. Creates cover thumbnails (480px)
4. Updates all HTML src/srcset references to point at the new filenames
Uses all 24 Pollinations keys in rotation. Model: klein-large.
"""
import os, re, sys, glob, time, asyncio, urllib.parse, shutil
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

from master_prompt import MASTER_PROMPT, build_prompt, ART_DIRECTOR_SYSTEM, ART_DIRECTOR_USER_TEMPLATE

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

# Load ALL Pollinations API keys from .env
ALL_KEYS = []
for env_key, env_val in os.environ.items():
    if env_key.startswith("POLLINATIONS_API_KEY") and env_val.startswith("sk_"):
        ALL_KEYS.append(env_val)

# De-duplicate, keep order
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
    "Hero Cover -- main article visual, wide establishing shot",
    "Activity Close-up -- children actively engaged, warm natural view",
    "Interactive Scene -- kids collaborating, isometric angle",
    "Tutorial Step -- focused learning moment, classroom setting",
    "Group Fun -- multiple children, wide colorful scene",
]

key_usage_idx = 0
TIMESTAMP = str(int(time.time()))


def ask_art_director(title, section_context, role):
    """Call DeepSeek for a short [SUBJECT] description."""
    user_msg = ART_DIRECTOR_USER_TEMPLATE.format(
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
                        {"role": "system", "content": ART_DIRECTOR_SYSTEM},
                        {"role": "user", "content": user_msg}
                    ],
                    "temperature": 0.6,
                    "max_tokens": 60
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
    return f"eagerly working on {section_context} activities together"


async def fetch_image(session, prompt, out_path):
    """Download image with key rotation."""
    global key_usage_idx
    clean_prompt = re.sub(r'[^a-zA-Z0-9 ,.\-]', '', prompt)
    encoded = urllib.parse.quote(clean_prompt)
    seed = int(time.time() * 1000) % 999999

    for attempt in range(len(ALL_KEYS)):
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
                        img.thumbnail((1200, 1200))
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

    print(f"      [FAIL] All keys exhausted for {os.path.basename(out_path)}")
    return False


def get_h2_contexts(html):
    """Extract H2 section titles (excluding FAQ)."""
    h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)
    return [
        re.sub(r'<[^>]+>', '', h2).strip()
        for h2 in h2s
        if 'faq' not in h2.lower() and 'frequently' not in h2.lower()
    ]


def delete_all_images():
    """Delete ALL existing images and thumbs."""
    count = 0
    for f in glob.glob(os.path.join(IMAGES_DIR, "*.webp")):
        os.remove(f)
        count += 1
    for f in glob.glob(os.path.join(IMAGES_DIR, "*.png")):
        os.remove(f)
        count += 1
    for f in glob.glob(os.path.join(IMAGES_DIR, "*.jpg")):
        os.remove(f)
        count += 1
    for f in glob.glob(os.path.join(THUMBS_DIR, "*.webp")):
        os.remove(f)
        count += 1
    for f in glob.glob(os.path.join(THUMBS_DIR, "*.png")):
        os.remove(f)
        count += 1
    return count


def update_html_images(html_path, slug, new_files):
    """
    Replace ALL old image src/srcset references in the article HTML with new filenames.
    new_files = {"cover": "slug-cover-TS.webp", "img1": "...", ...}
    """
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    cover_fn = new_files.get("cover", "")
    thumb_fn = cover_fn  # thumb has same filename, different directory

    # ------- COVER IMAGE (the hero image at the top) -------
    # Match the existing cover <img> block — it has fetchpriority="high"
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
    # These look like: <figure class='my-8'><img src='../images/OLD.webp' ...></figure>
    inline_pattern = re.compile(
        r"src='\.\.\/images\/[^']*?\.webp'"
    )
    inline_refs = inline_pattern.findall(html)

    # Map old inline srcs to new ones in order
    inline_idx = 0
    for suffix in ["img1", "img2", "img3", "img4"]:
        fn = new_files.get(suffix)
        if not fn:
            continue
        # Find the (inline_idx)-th match of figure img src and replace it
        # We need to replace them in order, so we do sequential replacement
        new_src = f"src='../images/{fn}'"
        # Replace first occurrence of src='../images/SOMETHING.webp' inside figure
        html = re.sub(
            r"<figure class='my-8'>\s*<img src='\.\.\/images\/[^']*?\.webp'",
            f"<figure class='my-8'><img {new_src}",
            html,
            count=1
        )
        inline_idx += 1

    # ------- RELATED ARTICLE THUMBNAILS -------
    # For the "You Might Also Like" section, we need to update other articles'
    # thumbnails to point to their NEW cover files. But we can only do that after
    # all articles are processed. So we skip this here — we'll run fix_related_thumbs.py after.

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)


async def process_article(session, html_path, article_num, total, all_covers):
    """Generate cover + img1..img4 for one article."""
    slug = os.path.basename(html_path).replace(".html", "")

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    title_match = re.search(r'<title>([^<]+)</title>', html)
    title = title_match.group(1).replace(" | Little Smart Genius", "").strip() if title_match else slug

    h2_contexts = get_h2_contexts(html)
    new_files = {}

    print(f"\n{'=' * 65}")
    print(f"[{article_num}/{total}] {title[:60]}")

    # --- COVER ---
    cover_fn = f"{slug}-cover-{TIMESTAMP}.webp"
    cover_path = os.path.join(IMAGES_DIR, cover_fn)

    print("  [1/5] Art Director -> SUBJECT for cover...")
    subject = ask_art_director(title, "main cover hero image for the article", IMAGE_ROLES[0])
    full_prompt = build_prompt(subject)
    print(f"      Subject: \"{subject}\"")

    ok = await fetch_image(session, full_prompt, cover_path)
    if ok:
        new_files["cover"] = cover_fn
        # Generate thumbnail
        thumb_path = os.path.join(THUMBS_DIR, cover_fn)
        img = Image.open(cover_path)
        img.thumbnail((480, 270))
        img.save(thumb_path, "WEBP", quality=80, optimize=True, method=6)
        all_covers[slug] = cover_fn

    # --- INLINE IMAGES img1..img4 ---
    for i in range(1, 5):
        suffix = f"img{i}"
        img_fn = f"{slug}-{suffix}-{TIMESTAMP}.webp"
        img_path = os.path.join(IMAGES_DIR, img_fn)

        ctx = h2_contexts[i-1] if i <= len(h2_contexts) else f"educational activity number {i}"
        role = IMAGE_ROLES[i % len(IMAGE_ROLES)]

        print(f"  [{i+1}/5] Art Director -> SUBJECT for {suffix}...")
        subject = ask_art_director(title, ctx, role)
        full_prompt = build_prompt(subject)
        print(f"      Subject: \"{subject}\"")

        ok = await fetch_image(session, full_prompt, img_path)
        if ok:
            new_files[suffix] = img_fn

        await asyncio.sleep(1)

    # Update HTML references
    if new_files:
        update_html_images(html_path, slug, new_files)

    generated = len(new_files)
    print(f"  DONE: {generated}/5 images generated for {slug[:50]}")
    return generated


def fix_related_thumbnails(all_covers):
    """Update 'You Might Also Like' sections to use new cover thumbnails."""
    articles = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html")))
    fixes = 0

    print(f"\n{'=' * 65}")
    print("  FIXING RELATED ARTICLE THUMBNAILS")
    print(f"{'=' * 65}")

    for html_path in articles:
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        modified = False
        # Find all related article links
        for rel_slug, rel_cover in all_covers.items():
            # Match the href and update the img inside that <a> block
            pattern = re.compile(
                r'(<a\s+href="../articles/' + re.escape(rel_slug) + r'\.html"[^>]*>.*?'
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
    print("  REGEN ALL IMAGES V5 — CLEAN SLATE EDITION")
    print(f"  {len(html_files)} articles x 5 images = {len(html_files) * 5} total")
    print(f"  Model: {POLLINATIONS_MODEL}")
    print(f"  Keys available: {len(ALL_KEYS)}")
    print(f"  Timestamp: {TIMESTAMP}")
    print("=" * 65)

    # Step 1: Delete all existing images
    print("\n  STEP 1: Deleting ALL existing images...")
    os.makedirs(THUMBS_DIR, exist_ok=True)
    deleted = delete_all_images()
    print(f"  Deleted {deleted} files\n")

    # Step 2: Generate all images
    total_generated = 0
    total_expected = len(html_files) * 5
    all_covers = {}  # slug -> cover filename

    async with aiohttp.ClientSession() as session:
        for i, fp in enumerate(html_files, 1):
            ok = await process_article(session, fp, i, len(html_files), all_covers)
            total_generated += ok
            if i < len(html_files):
                await asyncio.sleep(2)

    # Step 3: Fix related article thumbnails
    fix_related_thumbnails(all_covers)

    # Summary
    print(f"\n{'=' * 65}")
    print(f"  COMPLETE: {total_generated}/{total_expected} images generated")
    print(f"  Covers with thumbs: {len(all_covers)}")
    print(f"  HTML references updated for all articles.")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    asyncio.run(main())
