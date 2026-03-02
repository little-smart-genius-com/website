"""
REGEN ALL IMAGES V4 — Master Prompt Edition
Uses DeepSeek Art Director to generate ONLY the [SUBJECT] portion,
then inserts it into the user's canonical Master Prompt template.
Overwrites existing v3 images in-place (same filenames) so HTML refs stay valid.
Does NOT touch article structure.
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

# Import master prompt
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

# API keys — user-provided backup keys
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

# Image roles for variety (used by Art Director to vary scenes)
IMAGE_ROLES = [
    "Hero Cover — main article visual, wide establishing shot",
    "Activity Close-up — children actively engaged, warm natural view",
    "Interactive Scene — kids collaborating, isometric angle",
    "Tutorial Step — focused learning moment, classroom setting",
    "Group Fun — multiple children, wide colorful scene",
    "Achievement — joy and pride, celebrating results",
]

# Track global key usage
key_usage_idx = 0

def ask_art_director(title, section_context, role):
    """
    Call DeepSeek to generate ONLY the [SUBJECT] portion.
    Returns a short activity description (max ~20 words).
    """
    user_msg = ART_DIRECTOR_USER_TEMPLATE.format(
        title=title,
        section=section_context,
        role=role
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
                # Clean up any quotes or markdown
                subject = subject.strip('"').strip("'").strip('`').strip()
                # Remove any accidental prompt artifacts
                for bad in ["3D", "Pixar", "Disney", "no text", "watermark", "8k", "masterpiece"]:
                    if bad.lower() in subject.lower():
                        # Art director leaked template words — clean it
                        subject = re.sub(re.escape(bad), '', subject, flags=re.IGNORECASE).strip()
                subject = re.sub(r'\s+', ' ', subject).strip(' ,.')
                return subject
        except Exception:
            time.sleep(2)

    # Fallback: generate a simple subject from the context
    return f"eagerly working on {section_context} activities together"


async def fetch_image(session, prompt, out_path):
    """Download image from Pollinations API with key rotation and retry."""
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
                    body = await resp.text()
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


def find_current_images(slug):
    """Find the current v3 image files for this slug on disk."""
    result = {}
    for suffix in ["cover", "img1", "img2", "img3", "img4", "img5"]:
        matches = glob.glob(os.path.join(IMAGES_DIR, f"{slug}-{suffix}-*-v3.webp"))
        if matches:
            matches.sort(key=os.path.getmtime, reverse=True)
            result[suffix] = matches[0]
    return result


async def process_article(session, html_path, article_num, total):
    """Regenerate all 6 images for one article using the Master Prompt."""
    slug = os.path.basename(html_path).replace(".html", "")

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    title_match = re.search(r'<title>([^<]+)</title>', html)
    title = title_match.group(1).replace(" | Little Smart Genius", "").strip() if title_match else slug

    h2_contexts = get_h2_contexts(html)
    current_images = find_current_images(slug)

    print(f"\n{'=' * 65}")
    print(f"[{article_num}/{total}] {title[:60]}")
    print(f"  Existing images on disk: {list(current_images.keys())}")

    generated = 0

    # --- COVER ---
    cover_path = current_images.get("cover")
    if not cover_path:
        print("  [SKIP] No existing cover file found, cannot overwrite")
        return 0

    print("  [1/6] Art Director -> SUBJECT for cover...")
    subject = ask_art_director(title, "main cover hero image for the article", IMAGE_ROLES[0])
    full_prompt = build_prompt(subject)
    print(f"      Subject: \"{subject}\"")

    ok = await fetch_image(session, full_prompt, cover_path)
    if ok:
        generated += 1
        # Regenerate thumbnail
        thumb_path = os.path.join(THUMBS_DIR, os.path.basename(cover_path))
        img = Image.open(cover_path)
        img.thumbnail((480, 270))
        img.save(thumb_path, "WEBP", quality=80, optimize=True, method=6)
    else:
        print("  [WARN] Cover generation failed, keeping old image")

    # --- INLINE IMAGES ---
    for i in range(1, 6):
        suffix = f"img{i}"
        img_path = current_images.get(suffix)
        if not img_path:
            print(f"  [{i+1}/6] [SKIP] No existing {suffix} file found")
            continue

        ctx = h2_contexts[i-1] if i <= len(h2_contexts) else f"educational activity number {i}"
        role = IMAGE_ROLES[i % len(IMAGE_ROLES)]

        print(f"  [{i+1}/6] Art Director -> SUBJECT for {suffix}...")
        subject = ask_art_director(title, ctx, role)
        full_prompt = build_prompt(subject)
        print(f"      Subject: \"{subject}\"")

        ok = await fetch_image(session, full_prompt, img_path)
        if ok:
            generated += 1
        else:
            print(f"  [WARN] {suffix} generation failed, keeping old image")

        await asyncio.sleep(1)

    print(f"  DONE: {generated}/6 images regenerated for {slug[:50]}")
    return generated


async def main():
    html_files = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html")))

    print("\n" + "=" * 65)
    print("  REGEN ALL IMAGES V4 — MASTER PROMPT EDITION")
    print(f"  {len(html_files)} articles x 6 images = {len(html_files) * 6} total")
    print(f"  Model: {POLLINATIONS_MODEL}")
    print(f"  Keys available: {len(ALL_KEYS)}")
    print("=" * 65)
    print(f"\n  MASTER PROMPT preview:")
    print(f"  {MASTER_PROMPT[:120]}...")
    print(f"  [...] [SUBJECT] [...]")
    print()

    total_generated = 0
    total_expected = len(html_files) * 6

    async with aiohttp.ClientSession() as session:
        for i, fp in enumerate(html_files, 1):
            ok = await process_article(session, fp, i, len(html_files))
            total_generated += ok
            if i < len(html_files):
                await asyncio.sleep(2)

    print(f"\n{'=' * 65}")
    print(f"  COMPLETE: {total_generated}/{total_expected} images regenerated")
    print(f"  Images overwritten in-place. HTML references unchanged.")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    asyncio.run(main())
