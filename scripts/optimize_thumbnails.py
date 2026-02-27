"""
THUMBNAIL OPTIMIZER — V1.0
Generates lightweight WebP thumbnails from the images/ directory.

Output: images/thumbs/<original-name>.webp   (size: 480×270, quality: 75)

Run:  python scripts/optimize_thumbnails.py
Deps: pip install Pillow
"""

import os
import sys
import time

try:
    from PIL import Image
except ImportError:
    print("[ERROR] Pillow is not installed. Run: pip install Pillow")
    sys.exit(1)

# ─────────────────────────────────────────────
#  Configuration
# ─────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
BASE_DIR    = os.path.dirname(SCRIPT_DIR)
IMAGES_DIR  = os.path.join(BASE_DIR, "images")
THUMBS_DIR  = os.path.join(IMAGES_DIR, "thumbs")

THUMB_WIDTH   = 480      # px  – fits comfortably in a 3-column grid card
THUMB_HEIGHT  = 270      # px  – 16:9 aspect ratio (same as original covers)
WEBP_QUALITY  = 75       # 0-100  – good quality / small file
SKIP_DIRS     = {"thumbs", "banners"}   # sub-folders to ignore

# Only process files ending with these suffixes (covers + article images)
INCLUDE_SUFFIXES = ("-cover-", "-img1-", "-img2-", "-img3-", "-img4-")


def should_process(filename: str) -> bool:
    """Return True for files we want to thumbnail."""
    name_lower = filename.lower()
    return (
        name_lower.endswith(".webp") or
        name_lower.endswith(".jpg")  or
        name_lower.endswith(".jpeg") or
        name_lower.endswith(".png")
    )


def generate_thumb(src_path: str, dst_path: str) -> tuple[bool, int, int]:
    """
    Open src_path, resize to THUMB_WIDTH × THUMB_HEIGHT (cover crop),
    save as WebP at WEBP_QUALITY. Returns (success, src_bytes, dst_bytes).
    """
    try:
        with Image.open(src_path) as img:
            img = img.convert("RGB")

            # Smart crop: fill the target box, keeping center visible
            src_ratio  = img.width / img.height
            tgt_ratio  = THUMB_WIDTH / THUMB_HEIGHT

            if src_ratio > tgt_ratio:
                # Wide image → scale by height, then center-crop width
                new_h = THUMB_HEIGHT
                new_w = int(img.width * THUMB_HEIGHT / img.height)
            else:
                # Tall image → scale by width, then center-crop height
                new_w = THUMB_WIDTH
                new_h = int(img.height * THUMB_WIDTH / img.width)

            img = img.resize((new_w, new_h), Image.LANCZOS)

            left = (new_w - THUMB_WIDTH)  // 2
            top  = (new_h - THUMB_HEIGHT) // 2
            img  = img.crop((left, top, left + THUMB_WIDTH, top + THUMB_HEIGHT))

            img.save(dst_path, "WEBP", quality=WEBP_QUALITY, method=6)

        src_size = os.path.getsize(src_path)
        dst_size = os.path.getsize(dst_path)
        return True, src_size, dst_size

    except Exception as e:
        print(f"    [!] Error processing {os.path.basename(src_path)}: {e}")
        return False, 0, 0


def main():
    print("=" * 62)
    print("  THUMBNAIL OPTIMIZER — Little Smart Genius")
    print("=" * 62)
    t0 = time.time()

    # Ensure thumbs output dir exists
    os.makedirs(THUMBS_DIR, exist_ok=True)
    print(f"\n[1] Output dir:  images/thumbs/")
    print(f"[2] Target size: {THUMB_WIDTH}×{THUMB_HEIGHT}px  |  quality: {WEBP_QUALITY}")

    # Collect candidate files (flat list from images/ root only)
    candidates = [
        f for f in os.listdir(IMAGES_DIR)
        if os.path.isfile(os.path.join(IMAGES_DIR, f)) and should_process(f)
    ]

    print(f"[3] Found {len(candidates)} image files to process\n")

    generated = 0
    skipped   = 0
    errors    = 0
    saved_bytes = 0

    for fname in sorted(candidates):
        src_path = os.path.join(IMAGES_DIR, fname)
        # Output filename: strip original extension, always .webp
        base_name = os.path.splitext(fname)[0] + ".webp"
        dst_path  = os.path.join(THUMBS_DIR, base_name)

        # Skip if thumb already up-to-date (src not newer than dst)
        if os.path.exists(dst_path):
            src_mtime = os.path.getmtime(src_path)
            dst_mtime = os.path.getmtime(dst_path)
            if dst_mtime >= src_mtime:
                skipped += 1
                continue

        ok, src_sz, dst_sz = generate_thumb(src_path, dst_path)
        if ok:
            ratio  = round(dst_sz / src_sz * 100) if src_sz else 0
            saving = src_sz - dst_sz
            saved_bytes += saving
            print(f"  OK {fname[:55]:<55}  {src_sz//1024:>4}KB -> {dst_sz//1024:>3}KB  ({ratio}%)")
            generated += 1
        else:
            errors += 1

    elapsed = round(time.time() - t0, 1)
    saved_kb = saved_bytes // 1024
    saved_mb = round(saved_bytes / 1_000_000, 2)

    print(f"\n{'=' * 62}")
    print(f"  RESULTS:")
    print(f"    Generated : {generated}")
    print(f"    Skipped   : {skipped}  (already up-to-date)")
    print(f"    Errors    : {errors}")
    print(f"    Saved     : {saved_kb} KB  ({saved_mb} MB) vs original files")
    print(f"    Time      : {elapsed}s")
    print(f"{'=' * 62}\n")

    if generated > 0:
        print("  TIP: Update your JS to use 'images/thumbs/<filename>'")
        print("       instead of the full-size images for card grids.")
        print("       Full-size images remain unchanged in images/.")


if __name__ == "__main__":
    main()
