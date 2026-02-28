"""
Inject temporary fallback images for articles missing inline images.
Uses thematically appropriate existing images from the images/ directory.
Run: python tmp_inject_fallback_images.py
"""
import json, glob, os, re, sys, shutil, time

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(BASE, 'posts')
IMAGES_DIR = os.path.join(BASE, 'images')

# Articles needing fallback images + source images to copy from (thematically closest)
FALLBACK_MAP = {
    "best-sudoku-puzzles-for-beginners-kids-ultimate-guide": [
        "best-benefits-of-puzzles-for-child-brain-development-img1-1771634114.webp",
        "best-benefits-of-puzzles-for-child-brain-development-img2-1771634114.webp",
        "best-fine-motor-skills-worksheets-for-preschoolers-the-ultimate-guide-img3-1771633341.webp",
        "ultimate-critical-thinking-activities-for-kindergarten-img4-1771632132.webp",
    ],
    "ultimate-printable-logic-puzzles-for-kids-6-10": [
        "best-benefits-of-puzzles-for-child-brain-development-img3-1771634114.webp",
        "best-benefits-of-puzzles-for-child-brain-development-img4-1771634114.webp",
        "how-to-teach-logical-reasoning-to-kids-the-ultimate-guide-img1-1772269372.webp",
        "how-to-teach-logical-reasoning-to-kids-the-ultimate-guide-img2-1772269372.webp",
    ],
    "how-to-use-cooking-activities-to-boost-executive-function-proven-method": [
        "engaging-classroom-activities-top-early-learner-essentials-img1-1771633341.webp",
        "engaging-classroom-activities-top-early-learner-essentials-img2-1771633341.webp",
        "how-to-use-mazes-to-unlock-your-childs-problem-solving-skills-img3-1771633341.webp",
        "how-to-use-stickers-to-boost-fine-motor-cognitive-skills-img4-1771751376.webp",
    ],
}

def inject_images(slug, source_img_names):
    matches = glob.glob(os.path.join(POSTS_DIR, f"{slug}-*.json"))
    if not matches:
        print(f"  ERROR: No JSON found for {slug}")
        return

    pf = matches[0]
    with open(pf, 'r', encoding='utf-8') as f:
        d = json.load(f)

    ts = int(time.time())
    content = d.get('content', '')
    new_img_html = []

    for i, src_name in enumerate(source_img_names):
        src_path = os.path.join(IMAGES_DIR, src_name)
        if not os.path.exists(src_path):
            # Try matching from images dir
            matches2 = glob.glob(os.path.join(IMAGES_DIR, f"*img{i+1}*"))
            if matches2:
                src_path = matches2[0]
                src_name = os.path.basename(src_path)
            else:
                print(f"  SKIP img{i+1}: source not found ({src_name})")
                continue

        # Copy with new name so it's linked to this article
        dest_name = f"{slug}-img{i+1}-{ts}.webp"
        dest_path = os.path.join(IMAGES_DIR, dest_name)
        shutil.copy2(src_path, dest_path)
        print(f"  COPIED img{i+1}: {src_name} -> {dest_name}")

        alt = f"Educational activity illustration {i+1}, {slug.replace('-', ' ')}"
        new_img_html.append(
            f'\n<figure class="article-image my-8">\n'
            f'  <img src="../images/{dest_name}" alt="{alt}" loading="lazy" width="1200" height="675" class="w-full rounded-xl shadow-md">\n'
            f'</figure>\n'
        )

    if not new_img_html:
        print(f"  No images injected for {slug}")
        return

    # Clear existing stale figure blocks
    content = re.sub(r'<figure[^>]*>.*?</figure>', '', content, flags=re.DOTALL | re.IGNORECASE)

    # Inject 4 images evenly after H2 tags
    h2_matches = list(re.finditer(r'</h2>', content, re.IGNORECASE))
    if len(h2_matches) >= len(new_img_html):
        step = max(1, len(h2_matches) // len(new_img_html))
        positions = [h2_matches[min(i * step, len(h2_matches)-1)].end() for i in range(len(new_img_html))]
        # Insert in reverse order to maintain positions
        for pos, html in sorted(zip(positions, new_img_html), reverse=True):
            content = content[:pos] + html + content[pos:]
    else:
        # Fall back: append all at end
        content += '\n'.join(new_img_html)

    d['content'] = content
    with open(pf, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    print(f"  SAVED {os.path.basename(pf)} with {len(new_img_html)} images")

for slug, imgs in FALLBACK_MAP.items():
    print(f"\n{'=' * 65}")
    print(f"PATCHING: {slug}")
    inject_images(slug, imgs)

print("\nDone! Now run: python scripts/build_articles.py")
