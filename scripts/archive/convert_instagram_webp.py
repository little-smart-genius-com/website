"""
Convert all JPG/PNG images in instagram/ to WebP.
Originals are kept as .jpg.bak for safety (or can be deleted).
Run: python scripts/convert_instagram_webp.py
"""
import os, sys, time
try:
    from PIL import Image
except ImportError:
    print("[ERROR] pip install Pillow")
    sys.exit(1)

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTA_DIR  = os.path.join(BASE_DIR, "instagram")
QUALITY    = 82   # good quality, much smaller than JPEG

print("=" * 60)
print("  JPG -> WebP Converter  (instagram folder)")
print("=" * 60)
t0 = time.time()

converted = skipped = errors = 0
saved_bytes = 0

for fname in sorted(os.listdir(INSTA_DIR)):
    if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
        continue
    src = os.path.join(INSTA_DIR, fname)
    dst = os.path.join(INSTA_DIR, os.path.splitext(fname)[0] + ".webp")

    if os.path.exists(dst):
        skipped += 1
        continue

    try:
        with Image.open(src) as img:
            img.convert("RGB").save(dst, "WEBP", quality=QUALITY, method=6)
        src_kb = os.path.getsize(src) // 1024
        dst_kb = os.path.getsize(dst) // 1024
        saved_bytes += os.path.getsize(src) - os.path.getsize(dst)
        print(f"  OK {fname[:50]:<50} {src_kb:>4}KB -> {dst_kb:>3}KB")
        converted += 1
    except Exception as e:
        print(f"  ERR {fname}: {e}")
        errors += 1

elapsed = round(time.time() - t0, 1)
print(f"\n{'='*60}")
print(f"  Converted : {converted}  |  Skipped: {skipped}  |  Errors: {errors}")
print(f"  Saved     : {saved_bytes//1024} KB  ({round(saved_bytes/1_000_000,2)} MB)")
print(f"  Time      : {elapsed}s")
print(f"{'='*60}")
print("\n  NOTE: Original JPGs kept intact. Delete manually if desired.")
