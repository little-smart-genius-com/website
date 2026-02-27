"""
Download product thumbnail images from TPT CDN, convert to WebP, save locally.
Output: images/products-thumbs/<slug>.webp  (480x480, quality 80)

Run: python scripts/download_product_thumbs.py
"""
import os, re, sys, time, json
try:
    import urllib.request as req
    from PIL import Image
    from io import BytesIO
except ImportError:
    print("[ERROR] pip install Pillow")
    sys.exit(1)

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS_FILE    = os.path.join(BASE_DIR, "products_tpt.js")
OUT_DIR    = os.path.join(BASE_DIR, "images", "products-thumbs")
MAP_FILE   = os.path.join(BASE_DIR, "images", "products-thumbs", "_map.json")
os.makedirs(OUT_DIR, exist_ok=True)

TPT_BASE   = "https://ecdn.teacherspayteachers.com/cdn-cgi/image/format=webp,width=480,quality=80/thumbitem/"
THUMB_SIZE = (480, 480)
QUALITY    = 80

# ── Parse products_tpt.js to extract [name, slug/img] pairs ─────────────────
with open(JS_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Extract the array literal
match = re.search(r'window\.tptProducts\s*=\s*(\[.*?\]);', content, re.DOTALL)
if not match:
    print("[ERROR] Could not parse window.tptProducts from products_tpt.js")
    sys.exit(1)

import json as json_mod
products_raw = json_mod.loads(match.group(1))
print(f"  Found {len(products_raw)} products in products_tpt.js")

# ── Build slug from image path (p[2]) ────────────────────────────────────────
def slug_from_img(img_path: str) -> str:
    """Extract a clean slug from the TPT image path."""
    name = os.path.splitext(os.path.basename(img_path))[0]  # e.g. 750f-10478133-1
    # Use the product ID portion for uniqueness
    parts = img_path.split("/")
    folder = parts[0] if parts else name   # e.g. Spot-the-Diff...-10478133-1709...
    # Extract numeric ID
    ids = re.findall(r'-(\d{7,})-', folder)
    pid = ids[0] if ids else name
    return pid   # short, numeric, unique


print("=" * 60)
print("  TPT Product Thumbnail Downloader  ->  images/products-thumbs/")
print("=" * 60)

mapping = {}   # product_id -> local_webp filename
downloaded = skipped = errors = 0
t0 = time.time()

for p in products_raw:
    name, _, img_path, *_ = p
    if not img_path:
        continue

    pid = slug_from_img(img_path)
    out_name = f"{pid}.webp"
    out_path = os.path.join(OUT_DIR, out_name)

    if os.path.exists(out_path):
        mapping[img_path] = f"images/products-thumbs/{out_name}"
        skipped += 1
        continue

    # Build the CDN URL for slide 1
    base = img_path.split("-1.jpg")[0] if img_path.endswith("-1.jpg") else img_path.rsplit(".", 1)[0]
    url = f"https://ecdn.teacherspayteachers.com/cdn-cgi/image/format=auto,width=480,quality=80/thumbitem/{img_path}"

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        request = req.Request(url, headers=headers)
        with req.urlopen(request, timeout=15) as resp:
            data = resp.read()

        img = Image.open(BytesIO(data)).convert("RGB")
        img.thumbnail(THUMB_SIZE, Image.LANCZOS)
        img.save(out_path, "WEBP", quality=QUALITY, method=6)

        size_kb = os.path.getsize(out_path) // 1024
        print(f"  OK [{pid}] {name[:45]:<45} -> {size_kb}KB")
        mapping[img_path] = f"images/products-thumbs/{out_name}"
        downloaded += 1
        time.sleep(0.2)  # be polite to TPT CDN

    except Exception as e:
        print(f"  ERR [{pid}] {name[:45]}: {e}")
        errors += 1

# ── Save mapping JSON ─────────────────────────────────────────────────────────
with open(MAP_FILE, "w", encoding="utf-8") as f:
    json_mod.dump(mapping, f, indent=2)

elapsed = round(time.time() - t0, 1)
print(f"\n{'='*60}")
print(f"  Downloaded : {downloaded}  |  Skipped: {skipped}  |  Errors: {errors}")
print(f"  Mapping saved -> images/products-thumbs/_map.json")
print(f"  Time : {elapsed}s")
print(f"{'='*60}")
print("\n  NEXT STEP: run  python scripts/inject_product_thumbs.py  to update products_tpt.js")
