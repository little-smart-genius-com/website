"""Generate images for 6 placeholder articles using fix_images.py --slug."""
import subprocess, os
from PIL import Image

IMAGES_DIR = 'images'
THUMBS_DIR = os.path.join(IMAGES_DIR, 'thumbs')

PLACEHOLDER_SLUGS = [
    'fix-parents-four-in-a-row-mistakes-for-smarter-play',
    'photorealistic-spot-difference-puzzles-build-visual-skills',
    'word-search-boosts-reading-confidence-for-6-year-olds',
    'spot-the-difference-builds-siblings-visual-discrimination',
    'proven-montessori-inspired-worksheets-for-toddlers-that-work',
    'budget-friendly-guide-to-teach-kids-logic',
]

for i, slug in enumerate(PLACEHOLDER_SLUGS):
    print(f"\n{'='*60}")
    print(f"  [{i+1}/{len(PLACEHOLDER_SLUGS)}] {slug}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            ["python", "scripts/fix_images.py", "--slug", slug, "--force", "--model", "zimage"],
            timeout=600
        )
        if result.returncode == 0:
            print(f"  ✅ Done!")
        else:
            print(f"  ⚠️ Return code: {result.returncode}")
    except subprocess.TimeoutExpired:
        print(f"  ⏰ Timed out!")

# Generate any missing thumbnails
print(f"\n{'='*60}")
print(f"  Generating missing thumbnails...")
print(f"{'='*60}")
os.makedirs(THUMBS_DIR, exist_ok=True)

for f in os.listdir(IMAGES_DIR):
    if '-cover-' in f and f.endswith('.webp'):
        thumb = os.path.join(THUMBS_DIR, f)
        if not os.path.exists(thumb):
            try:
                img = Image.open(os.path.join(IMAGES_DIR, f))
                w, h = img.size
                nw = 400
                nh = int(h * (nw / w))
                img = img.resize((nw, nh), Image.LANCZOS)
                img.save(thumb, 'WEBP', quality=75)
                print(f"  ✅ Thumb: {f}")
            except Exception as e:
                print(f"  ❌ {e}")

print(f"\nFinal thumb count: {len(os.listdir(THUMBS_DIR))}")
print("ALL DONE!")
