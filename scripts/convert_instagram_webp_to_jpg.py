"""
Convert instagram/*.webp files BACK to .jpg (Instagram doesn't accept WebP).
The original JPGs were deleted previously — this restores them from WebP.

Run: python scripts/convert_instagram_webp_to_jpg.py
"""
import os, sys
try:
    from PIL import Image
except ImportError:
    print("[ERROR] pip install Pillow")
    sys.exit(1)

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTA_DIR = os.path.join(BASE_DIR, "instagram")
QUALITY   = 95   # high quality JPG since Instagram will re-compress anyway

print("=" * 60)
print("  WebP -> JPG Converter  (instagram folder)")
print("=" * 60)

converted = skipped = errors = 0

for fname in sorted(os.listdir(INSTA_DIR)):
    if not fname.lower().endswith(".webp"):
        continue
    src = os.path.join(INSTA_DIR, fname)
    dst = os.path.join(INSTA_DIR, os.path.splitext(fname)[0] + ".jpg")

    if os.path.exists(dst):
        skipped += 1
        continue

    try:
        with Image.open(src) as img:
            img.convert("RGB").save(dst, "JPEG", quality=QUALITY, optimize=True)
        src_kb = os.path.getsize(src) // 1024
        dst_kb = os.path.getsize(dst) // 1024
        print(f"  OK {fname[:52]:<52} {src_kb:>3}KB -> {dst_kb:>3}KB")
        converted += 1
    except Exception as e:
        print(f"  ERR {fname}: {e}")
        errors += 1

print(f"\n{'='*60}")
print(f"  Converted: {converted}  |  Skipped: {skipped}  |  Errors: {errors}")
print(f"{'='*60}")
print("\n  NOTE: WebP originals kept for website use. JPGs are for Instagram upload only.")
