"""
regen_missing_images.py — Regenerate ONLY the missing article images.
Uses the same Art Director + Master Prompt V8 + zimage pipeline as auto_blog_v6_ultimate.py.
"""
import os, sys, json, re, asyncio, time, requests, aiohttp
from urllib.parse import quote
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from prompt_templates import build_art_director_prompt

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
load_dotenv('.env')

IMAGES_DIR = "images"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL_CHAT = "deepseek-chat"
GEN_MODEL = "zimage"

deepseek_key = os.getenv("DEEPSEEK_API_KEY")
if not deepseek_key:
    for i in range(1, 10):
        k = os.getenv(f"DEEPSEEK_API_KEY_{i}")
        if k:
            deepseek_key = k
            break

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
                return key
        except:
            continue
    return None

api_key = get_working_pollinations_key()
poll_headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

# ── Art Director (V5) ──
async def art_director(session, title, concept, image_index):
    SYSTEM_PROMPT_AGENT = "You are Agent 5, the Expert Art Director. You MUST return ONLY the requested image prompt without any markdown, introductory text, or quotes."
    user_prompt = build_art_director_prompt(concept, title, image_index)
    
    payload = {
        "model": MODEL_CHAT,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_AGENT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 1.2
    }
    auth = {"Authorization": f"Bearer {deepseek_key}", "Content-Type": "application/json"}
    for attempt in range(3):
        try:
            async with session.post(DEEPSEEK_API_URL, json=payload, headers=auth, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"].strip().strip('"').strip("'")
        except:
            await asyncio.sleep(2)
    return f"a high-quality educational illustration of children engaged in {concept[:50]} activities"


def center_crop_resize(img, tw, th):
    sw, sh = img.size
    tr = tw / th
    sr = sw / sh
    if sr > tr:
        nw = int(sh * tr)
        off = (sw - nw) // 2
        img = img.crop((off, 0, off + nw, sh))
    elif sr < tr:
        nh = int(sw / tr)
        off = (sh - nh) // 2
        img = img.crop((0, off, sw, off + nh))
    return img.resize((tw, th), Image.LANCZOS)


def generate_image(prompt, filename, retries=6):
    safe = quote(re.sub(r'[^a-zA-Z0-9 ,.\-]', '', prompt))
    fallbacks = ["zimage", "flux", "gptimage"]
    for attempt in range(retries):
        model = GEN_MODEL if attempt == 0 else fallbacks[attempt % len(fallbacks)]
        url = f"https://gen.pollinations.ai/image/{safe}?model={model}&width=1200&height=675&nologo=true&enhance=true"
        print(f"    🎨 Attempt {attempt+1}/{retries} [{model}]: {prompt[:80]}...")
        try:
            res = requests.get(url, headers=poll_headers, timeout=90)
            if res.status_code == 200 and len(res.content) > 1024:
                img = Image.open(BytesIO(res.content)).convert("RGB")
                img = center_crop_resize(img, 1200, 675)
                out = os.path.join(IMAGES_DIR, filename)
                img.save(out, "WEBP", quality=85, optimize=True)
                kb = os.path.getsize(out) // 1024
                print(f"    ✅ {filename} ({kb}KB)")
                return True
        except Exception as e:
            print(f"    ❌ Error: {e}")
        time.sleep(3)
    return False


async def main():
    print("=" * 60)
    print("  MISSING IMAGES REGENERATOR (Art Director + zimage)")
    print("=" * 60)

    with open("articles.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    articles = data.get("articles", data) if isinstance(data, dict) else data

    # Find missing images
    missing = []  # list of (slug, title, category, prefix, timestamp, [missing_indices])
    for art in articles:
        slug = art.get("slug", "")
        title = art.get("title", slug.replace("-", " "))
        category = art.get("category", "Education")
        cover_rel = art.get("image", "")
        if not cover_rel:
            continue
        basename = os.path.basename(cover_rel)
        m = re.match(r'^(.+)-cover-(\d+)\.webp$', basename)
        if not m:
            continue
        prefix, timestamp = m.group(1), m.group(2)
        missing_indices = []
        for i in range(1, 6):
            fname = f"{prefix}-img{i}-{timestamp}.webp"
            if not os.path.exists(os.path.join(IMAGES_DIR, fname)):
                missing_indices.append(i)
        if missing_indices:
            missing.append((slug, title, category, prefix, timestamp, missing_indices))

    total = sum(len(m[5]) for m in missing)
    print(f"\nFound {len(missing)} articles with {total} missing images.\n")

    if total == 0:
        print("All 216 images are present! Nothing to do.")
        return

    generated = 0
    async with aiohttp.ClientSession() as session:
        for slug, title, category, prefix, timestamp, indices in missing:
            print(f"\n{'─'*60}")
            print(f"📄 {slug} — missing img{indices}")

            # Read the HTML to get h2 context for each image
            html_path = os.path.join("articles", f"{slug}.html")
            concepts = {}
            if os.path.exists(html_path):
                with open(html_path, "r", encoding="utf-8") as f:
                    html = f.read()
                h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.IGNORECASE)
                for idx, h2 in enumerate(h2s, 1):
                    concepts[idx] = re.sub(r'<[^>]+>', '', h2).strip()

            for img_idx in indices:
                concept = concepts.get(img_idx, f"Educational activity for {title}")
                print(f"  🖼️  Generating img{img_idx} (Context: {concept[:50]}...)")

                # Art Director generates creative image prompt
                subject = await art_director(session, title, concept, img_idx)
                print(f"    📝 Art Director: {subject[:80]}...")

                full_prompt = subject
                full_prompt += ", ABSOLUTELY NO text, letters, words, numbers, titles, captions, labels, watermarks, or UI overlays in the image, pure visual storytelling only"

                filename = f"{prefix}-img{img_idx}-{timestamp}.webp"
                if generate_image(full_prompt, filename):
                    generated += 1
                else:
                    print(f"    ⚠️  FAILED to generate {filename}")

    print(f"\n{'='*60}")
    print(f"DONE! Generated {generated}/{total} missing images.")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
