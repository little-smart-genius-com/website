"""
Standardize ALL article images to exact 1200x675 (main) and 600x338 (thumbnails).
Uses center-crop-to-fit to preserve the focus of the image.
Overwrites files in-place so filenames stay identical => no HTML rebuild needed.
"""
import os
from PIL import Image

# Paths
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
IMAGES_DIR = "images"

# Target dimensions
MAIN_SIZE = (1200, 675)
THUMB_SIZE = (600, 338)

def crop_center_resize(img, target_w, target_h):
    """
    Resize and center-crop an image to exact target dimensions.
    Maintains aspect ratio by cropping excess from center.
    """
    src_w, src_h = img.size
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        # Source is wider => crop width
        new_w = int(src_h * target_ratio)
        offset = (src_w - new_w) // 2
        img = img.crop((offset, 0, offset + new_w, src_h))
    elif src_ratio < target_ratio:
        # Source is taller => crop height
        new_h = int(src_w / target_ratio)
        offset = (src_h - new_h) // 2
        img = img.crop((0, offset, src_w, offset + new_h))

    # Now resize to exact target
    img = img.resize((target_w, target_h), Image.LANCZOS)
    return img


def main():
    files = [f for f in os.listdir(IMAGES_DIR) if f.endswith(".webp")]
    print(f"📸 Found {len(files)} .webp images in {IMAGES_DIR}/")

    fixed_main = 0
    fixed_thumb = 0
    skipped = 0
    errors = []

    for fname in sorted(files):
        fpath = os.path.join(IMAGES_DIR, fname)
        is_thumb = "-thumb" in fname

        target_w, target_h = THUMB_SIZE if is_thumb else MAIN_SIZE

        try:
            img = Image.open(fpath)
            w, h = img.size

            if (w, h) == (target_w, target_h):
                skipped += 1
                continue

            print(f"  🔧 {fname}: {w}x{h} → {target_w}x{target_h}")
            img = crop_center_resize(img, target_w, target_h)

            # Save as WebP with same quality settings as V6 script
            quality = 80 if is_thumb else 85
            img.save(fpath, "WEBP", quality=quality)

            if is_thumb:
                fixed_thumb += 1
            else:
                fixed_main += 1

        except Exception as e:
            errors.append((fname, str(e)))
            print(f"  ❌ ERROR {fname}: {e}")

    print(f"\n{'='*60}")
    print(f"✅ Fixed main images:  {fixed_main}")
    print(f"✅ Fixed thumbnails:   {fixed_thumb}")
    print(f"⏩ Already correct:    {skipped}")
    print(f"❌ Errors:             {len(errors)}")
    print(f"{'='*60}")

    if errors:
        for name, err in errors:
            print(f"  ❌ {name}: {err}")


if __name__ == "__main__":
    main()
