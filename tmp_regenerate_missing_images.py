"""
Regenerate 4 unique content images for articles that have 0 inline images.
Uses Pollinations API (same as V6).
Run: python tmp_regenerate_missing_images.py
"""
import asyncio, aiohttp, json, glob, os, re, sys, time, urllib.parse
from PIL import Image
from io import BytesIO

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(BASE, 'posts')
IMAGES_DIR = os.path.join(BASE, 'images')

# Image concepts for each article
ARTICLE_CONCEPTS = {
    "best-sudoku-puzzles-for-beginners-kids-ultimate-guide": [
        "A curious child age 8 focused on solving a colorful sudoku puzzle grid, bright classroom setting, educational toy building blocks around",
        "A teacher helping two diverse smiling children understand number placement in a printed sudoku worksheet, warm orange tones",
        "A top-down view of a printed beginner sudoku puzzle with large colored pencils and an eraser on a wooden desk",
        "Cartoon illustration of joyful kids celebrating completing a sudoku puzzle, confetti, bright colors, educational theme",
    ],
    "ultimate-printable-logic-puzzles-for-kids-6-10": [
        "Diverse children age 6-10 sitting around a table solving logic puzzle worksheets together, bright classroom, warm lighting",
        "A top-down flat-lay of colorful printable logic puzzle sheets arranged neatly with crayons, pencils and a ruler",
        "A smiling girl concentrating on filling in a grid-based logic deduction puzzle, cozy home learning environment",
        "A teacher pointing at a logic grid on a whiteboard while excited children raise their hands, bright educational setting",
    ],
    "how-to-use-cooking-activities-to-boost-executive-function-proven-method": [
        "A parent and young child cooking together in a bright colorful kitchen, measuring ingredients, smiling and learning",
        "A child aged 5 carefully pouring liquid into a measuring cup with concentration, colorful kitchen backdrop",
        "Top-down flat-lay of child-friendly cooking tools: whisk, measuring spoons, bowls with colorful ingredients on a white counter",
        "Two diverse children following a simple illustrated recipe card at a kitchen table, bright warm tones, educational setting",
    ],
}

IMG_STYLE = "3D Pixar-style illustration, vibrant colors, educational, children aged 4-12, family-friendly, no text or watermarks"

async def fetch_image(session, prompt, out_path, seed, idx):
    clean = re.sub(r'[^a-zA-Z0-9 ,.-]', '', prompt)
    encoded = urllib.parse.quote(clean)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1200&height=675&seed={seed}&model=flux&nologo=true"
    
    for attempt in range(5):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=90)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    img = Image.open(BytesIO(data)).convert("RGB")
                    img = img.resize((1200, 675), Image.LANCZOS)
                    img.save(out_path, "WEBP", quality=88)
                    size_kb = os.path.getsize(out_path) // 1024
                    print(f"    [OK] img{idx+1} saved ({size_kb}KB): {os.path.basename(out_path)}")
                    return out_path
                else:
                    print(f"    [WARN] Attempt {attempt+1}: HTTP {resp.status}")
        except Exception as e:
            print(f"    [ERR] Attempt {attempt+1}: {e}")
        await asyncio.sleep(15)
    print(f"    [FAIL] All attempts failed for img{idx+1}")
    return None

async def process_article(session, slug, concepts):
    print(f"\n{'=' * 65}")
    print(f"REGENERATE: {slug}")
    
    # Find the JSON file
    matches = glob.glob(os.path.join(POSTS_DIR, f"{slug}-*.json"))
    if not matches:
        print(f"  ERROR: No JSON found for {slug}")
        return
    pf = matches[0]
    
    with open(pf, 'r', encoding='utf-8') as f:
        d = json.load(f)
    
    cover_path = d.get('image', '')
    cover_name = os.path.basename(cover_path)
    ts = int(time.time())
    
    # Generate 4 content images SEQUENTIALLY to avoid rate limiting
    results = []
    for i, concept in enumerate(concepts):
        print(f"  Generating img{i+1}...")
        full_prompt = f"{concept}, {IMG_STYLE}"
        out_name = f"{slug}-img{i+1}-{ts}.webp"
        out_path = os.path.join(IMAGES_DIR, out_name)
        seed = ts + i * 100 + 42
        result = await fetch_image(session, full_prompt, out_path, seed, i)
        results.append(result)
        if result:
            await asyncio.sleep(5)  # small gap between successful downloads
        else:
            await asyncio.sleep(20)  # longer gap after failure
    
    # Build new inline HTML
    new_img_html = []
    for i, result in enumerate(results):
        if result:
            rel_path = f"images/{os.path.basename(result)}"
            alt = f"Educational activity illustration {i+1} for {slug.replace('-', ' ')}"
            new_img_html.append(f'\n<figure class="article-image my-8">\n  <img src="../{rel_path}" alt="{alt}" loading="lazy" width="1200" height="675" class="w-full rounded-xl shadow-md">\n</figure>\n')
    
    # Inject images evenly into existing content
    content = d.get('content', '')
    # Strip any existing img tags that might be empty references
    content = re.sub(r'<figure[^>]*>\s*<img[^>]*src="[^"]*"[^>]*/?>\s*</figure>\s*', '', content, flags=re.DOTALL)
    
    # Find H2 positions to inject after
    h2_matches = list(re.finditer(r'</h2>', content, re.IGNORECASE))
    
    if len(h2_matches) >= 4 and new_img_html:
        # Insert images after H2s (in reverse order to not mess up offsets)
        positions = [h2_matches[min(i*2, len(h2_matches)-1)].end() for i in range(len(new_img_html))]
        positions.reverse()
        imgs_rev = list(reversed(new_img_html))
        for pos, img in zip(positions, imgs_rev):
            content = content[:pos] + img + content[pos:]
    else:
        # Append all images at the end
        content += ''.join(new_img_html)
    
    d['content'] = content
    with open(pf, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    print(f"  [SAVED] {os.path.basename(pf)} with {len([r for r in results if r])} new images")

async def main():
    async with aiohttp.ClientSession() as session:
        for slug, concepts in ARTICLE_CONCEPTS.items():
            await process_article(session, slug, concepts)
            await asyncio.sleep(10)  # pause between articles
    print("\n\nDone! Run: python scripts/build_articles.py")

asyncio.run(main())
