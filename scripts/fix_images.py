"""
FIX IMAGES — Scan articles for missing images and regenerate them.
Referenced by autoblog.yml workflow (fix-images action).

Usage:
  python scripts/fix_images.py                           # Fix missing images for all articles
  python scripts/fix_images.py --slug my-slug            # Fix missing for one article
  python scripts/fix_images.py --slug my-slug --force    # Force regen ALL images for one article
  python scripts/fix_images.py --slug my-slug --force --image-type cover   # Regen ONLY the cover
  python scripts/fix_images.py --slug my-slug --force --image-type img3    # Regen ONLY img3

Scans each post JSON + corresponding HTML to find images that are referenced
but don't exist on disk, then regenerates only the missing ones.
With --force, regenerates images even if they already exist.
"""
import asyncio, aiohttp, json, glob, os, re, sys, time, urllib.parse, argparse
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
POSTS_DIR = os.path.join(PROJECT_ROOT, 'posts')
IMAGES_DIR = os.path.join(PROJECT_ROOT, 'images')
ARTICLES_DIR = os.path.join(PROJECT_ROOT, 'articles')

load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# === EXACT SAME CONFIG AS V6 ===
POLLINATIONS_MODEL = "klein-large"
IMAGE_WIDTH, IMAGE_HEIGHT = 1200, 675

# Load all API keys (primary + backup)
POLLINATIONS_KEYS = [os.getenv(f"POLLINATIONS_API_KEY_{i}") for i in range(1, 6)]
POLLINATIONS_KEYS = [k for k in POLLINATIONS_KEYS if k and len(k) > 5]
POLLINATIONS_BACKUP_KEYS = [os.getenv(f"POLLINATIONS_API_KEY_BCK_{i}") for i in range(1, 6)]
POLLINATIONS_BACKUP_KEYS = [k for k in POLLINATIONS_BACKUP_KEYS if k and len(k) > 5]

if not POLLINATIONS_KEYS:
    POLLINATIONS_KEYS = [""]  # anonymous fallback

ALL_KEYS = POLLINATIONS_KEYS + POLLINATIONS_BACKUP_KEYS

# === IMAGE STYLE PRESETS (matching V6) ===
IMAGE_STYLE_PRESETS = [
    {
        "name": "Hero Scene",
        "style": "3D Pixar-style, vibrant, ultra-detailed, colorful, educational",
        "palette": "Brand orange (#F48C06), white, slate blue, sunshine yellow",
        "lighting": "Soft rim lighting, warm golden hour",
    },
    {
        "name": "Action Learning",
        "style": "3D Pixar-style, dynamic composition, bright classroom",
        "palette": "Warm coral, teal accent, off-white background",
        "lighting": "Bright natural classroom light",
    },
    {
        "name": "Close-Up Detail",
        "style": "3D illustration, macro product shot, high detail, educational material",
        "palette": "Pastel tones, brand orange highlight",
        "lighting": "Even studio lighting",
    },
    {
        "name": "Group Activity",
        "style": "3D Pixar-style, diverse children, collaborative, joyful",
        "palette": "Rainbow accents, warm white background, brand orange",
        "lighting": "Bright diffused classroom light",
    },
    {
        "name": "Creative Workspace",
        "style": "Top-down flat lay, 3D Pixar-style, colorful, vibrant, ultra-detailed",
        "palette": "Brand orange (#F48C06), white, slate blue, sunshine yellow",
        "lighting": "Bright even studio lighting, clean background",
    },
]

NO_TEXT_SUFFIX = (
    ", ABSOLUTELY NO text, letters, words, numbers, titles, captions, labels, "
    "watermarks, or UI overlays in the image, pure visual storytelling only"
)


async def fetch_image(session, prompt, out_path, idx):
    """Fetch image using V6 method: gen.pollinations.ai with auth bearer."""
    clean_prompt = re.sub(r'[^a-zA-Z0-9 ,.-]', '', prompt)
    encoded_prompt = urllib.parse.quote(clean_prompt)
    seed = int(time.time()) + idx * 100

    for attempt in range(8):
        if attempt < 3:
            api_key = POLLINATIONS_KEYS[(idx + attempt) % len(POLLINATIONS_KEYS)] if POLLINATIONS_KEYS else ""
        elif POLLINATIONS_BACKUP_KEYS:
            api_key = POLLINATIONS_BACKUP_KEYS[(idx + attempt) % len(POLLINATIONS_BACKUP_KEYS)]
        else:
            api_key = POLLINATIONS_KEYS[0] if POLLINATIONS_KEYS else ""

        url = f"https://gen.pollinations.ai/image/{encoded_prompt}"
        params = {
            "width": IMAGE_WIDTH, "height": IMAGE_HEIGHT,
            "seed": seed, "model": POLLINATIONS_MODEL,
            "nologo": "true", "enhance": "true"
        }
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            async with session.get(url, params=params, headers=headers,
                                    timeout=aiohttp.ClientTimeout(total=90)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    if len(data) > 1024:
                        img = Image.open(BytesIO(data)).convert("RGB")
                        img.thumbnail((1200, 1200))
                        img.save(out_path, "WEBP", quality=85, optimize=True, method=6)
                        size_kb = os.path.getsize(out_path) // 1024
                        print(f"      [OK] ({size_kb}KB) {os.path.basename(out_path)}")
                        return out_path
                    else:
                        print(f"      [WARN] attempt {attempt+1}: too small ({len(data)}B)")
                else:
                    print(f"      [WARN] attempt {attempt+1}: HTTP {resp.status}")
        except Exception as e:
            print(f"      [ERR] attempt {attempt+1}: {e}")

        await asyncio.sleep(3)
        seed += 1

    print(f"      [FAIL] All attempts failed for {os.path.basename(out_path)}")
    return None


def build_prompt(concept, slug, preset_idx):
    """Build a rich image prompt matching V6 Art Director style."""
    preset = IMAGE_STYLE_PRESETS[preset_idx % len(IMAGE_STYLE_PRESETS)]
    topic = slug.replace('-', ' ')
    return (
        f"{concept}, topic: {topic}, "
        f"style: {preset['style']}, "
        f"palette: {preset['palette']}, "
        f"lighting: {preset['lighting']}, "
        f"children aged 4-12, educational, child-safe, family-friendly, "
        f"no text no watermarks, no brand logos, no written words or numbers, "
        f"diverse children, joyful and engaged"
        + NO_TEXT_SUFFIX
    )


def find_missing_images(slug, post_data):
    """Check which images are missing for a given article."""
    missing = []

    # Check cover image
    cover = post_data.get('image', '')
    if cover:
        cover_file = os.path.basename(cover)
        cover_path = os.path.join(IMAGES_DIR, cover_file)
        if not os.path.exists(cover_path):
            missing.append(('cover', cover_file))
    else:
        # No cover at all
        missing.append(('cover', f'{slug}-cover-missing.webp'))

    # Check inline content images from HTML
    content = post_data.get('content', '')
    img_pattern = re.compile(r'src=["\'](?:\.\./)?images/([^"\']+)["\']', re.IGNORECASE)
    for match in img_pattern.finditer(content):
        img_file = match.group(1)
        img_path = os.path.join(IMAGES_DIR, img_file)
        if not os.path.exists(img_path):
            # Determine type from filename
            if '-img' in img_file:
                idx_match = re.search(r'-img(\d+)', img_file)
                idx = int(idx_match.group(1)) if idx_match else 1
                missing.append((f'img{idx}', img_file))
            elif '-cover' in img_file:
                missing.append(('cover', img_file))

    # Also check HTML file for missing images
    html_path = os.path.join(ARTICLES_DIR, f"{slug}.html")
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()
        for match in img_pattern.finditer(html):
            img_file = match.group(1)
            img_path = os.path.join(IMAGES_DIR, img_file)
            if not os.path.exists(img_path):
                already = any(m[1] == img_file for m in missing)
                if not already:
                    if '-img' in img_file:
                        idx_match = re.search(r'-img(\d+)', img_file)
                        idx = int(idx_match.group(1)) if idx_match else 1
                        missing.append((f'img{idx}', img_file))
                    elif '-cover' in img_file:
                        missing.append(('cover', img_file))

    # Deduplicate by type
    seen = set()
    deduped = []
    for img_type, img_file in missing:
        if img_type not in seen:
            seen.add(img_type)
            deduped.append((img_type, img_file))

    return deduped


async def fix_article_images(session, post_file, force=False, image_type_filter=None):
    """Fix missing (or force-regenerate) images for a single article."""
    with open(post_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    slug = data.get('slug', os.path.basename(post_file).replace('.json', ''))
    title = data.get('title', slug)

    if force:
        # Force mode: regenerate specified image(s) even if they exist
        targets = []
        if image_type_filter:
            # Single image type requested
            targets.append((image_type_filter, f'{slug}-{image_type_filter}-old.webp'))
        else:
            # All images: cover + 5 content
            targets.append(('cover', data.get('image', f'{slug}-cover.webp')))
            content = data.get('content', '')
            img_pattern = re.compile(r'src=["\'](?:\.\./)?images/([^"\']+)["\']', re.IGNORECASE)
            existing_imgs = set()
            for m in img_pattern.finditer(content):
                fname = m.group(1)
                if '-img' in fname:
                    idx_m = re.search(r'-img(\d+)', fname)
                    if idx_m:
                        existing_imgs.add(int(idx_m.group(1)))
            # Add existing content images
            for idx in sorted(existing_imgs):
                targets.append((f'img{idx}', f'{slug}-img{idx}.webp'))
            # If no content imgs found, assume 5
            if not existing_imgs:
                for idx in range(1, 6):
                    targets.append((f'img{idx}', f'{slug}-img{idx}.webp'))

        print(f"  🔄 {slug}: Force regenerating {len(targets)} image(s)")
        for img_type, _ in targets:
            print(f"      - {img_type}")

        return await _generate_images(session, data, post_file, slug, title, targets)
    else:
        # Normal mode: only fix missing
        missing = find_missing_images(slug, data)
        if not missing:
            print(f"  ✅ {slug}: All images present")
            return 0

        print(f"  ⚠️  {slug}: {len(missing)} missing image(s)")
        for img_type, img_file in missing:
            print(f"      - {img_type}: {img_file}")

        return await _generate_images(session, data, post_file, slug, title, missing)


async def _generate_images(session, data, post_file, slug, title, targets):
    """Generate the specified images and update the post JSON."""
    ts = int(time.time())
    fixed = 0
    json_updated = False

    for img_type, old_filename in targets:
        if img_type == 'cover':
            new_name = f"{slug}-cover-{ts}.webp"
            concept = f"Children learning about {title}, bright educational scene"
            prompt = build_prompt(concept, slug, 0)
        else:
            idx = int(img_type.replace('img', ''))
            new_name = f"{slug}-img{idx}-{ts}.webp"
            concept = f"Educational activity scene {idx} related to '{title}', engaging children"
            prompt = build_prompt(concept, slug, idx)

        out_path = os.path.join(IMAGES_DIR, new_name)
        print(f"      Generating {img_type}...")
        result = await fetch_image(session, prompt, out_path, fixed)

        if result:
            fixed += 1
            # Update references in post JSON
            if img_type == 'cover':
                data['image'] = f"images/{new_name}"
                json_updated = True
            else:
                # Update content HTML to reference new image
                content = data.get('content', '')
                old_pattern = re.escape(old_filename)
                new_ref = f"images/{new_name}"
                content = re.sub(
                    rf'(?:\.\./)?images/{old_pattern}',
                    f"../{new_ref}",
                    content
                )
                data['content'] = content
                json_updated = True

            await asyncio.sleep(2)
        else:
            print(f"      ❌ Failed to generate {img_type}")

    if json_updated:
        with open(post_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"      📝 Updated JSON with {fixed} new image(s)")

    return fixed


async def main():
    parser = argparse.ArgumentParser(description="Fix missing article images")
    parser.add_argument('--slug', type=str, default='', help='Fix a single article by slug')
    parser.add_argument('--force', action='store_true', help='Force regenerate even if images exist')
    parser.add_argument('--image-type', type=str, default='', help='Target specific image: cover, img1, img2...')
    args = parser.parse_args()

    mode_label = "FORCE REGEN" if args.force else "Fix missing"
    type_label = f" ({args.image_type})"
    print(f"\n{'='*65}")
    print(f"FIX IMAGES — {mode_label}{type_label if args.image_type else ''}")
    print(f"Keys: {len(POLLINATIONS_KEYS)} primary + {len(POLLINATIONS_BACKUP_KEYS)} backup")
    print(f"{'='*65}")

    if args.slug:
        # Single article mode
        post_file = os.path.join(POSTS_DIR, f"{args.slug}.json")
        # Also try numbered format
        if not os.path.exists(post_file):
            candidates = glob.glob(os.path.join(POSTS_DIR, f"{args.slug}*.json"))
            post_file = candidates[0] if candidates else post_file

        if not os.path.exists(post_file):
            print(f"❌ Post file not found: {post_file}")
            sys.exit(1)

        async with aiohttp.ClientSession() as session:
            fixed = await fix_article_images(session, post_file, force=args.force, image_type_filter=args.image_type or None)
        print(f"\n{'='*65}")
        print(f"Done. {'Regenerated' if args.force else 'Fixed'} {fixed} image(s) for {args.slug}")
    else:
        if args.force:
            print("⚠️  --force without --slug will regenerate ALL images for ALL articles!")
            print("    Use --slug to target a specific article.")
            sys.exit(1)
        # All articles
        posts = sorted(glob.glob(os.path.join(POSTS_DIR, '*.json')))
        print(f"\nScanning {len(posts)} articles for missing images...\n")

        total_fixed = 0
        total_missing = 0

        async with aiohttp.ClientSession() as session:
            for i, pf in enumerate(posts, 1):
                slug = os.path.basename(pf).replace('.json', '')
                # Remove timestamp suffix if present
                slug_match = re.match(r'^(.+)-\d+$', slug)
                if slug_match:
                    slug = slug_match.group(1)

                with open(pf, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                actual_slug = data.get('slug', slug)
                missing = find_missing_images(actual_slug, data)

                if missing:
                    total_missing += len(missing)
                    fixed = await fix_article_images(session, pf)
                    total_fixed += fixed
                    if i < len(posts):
                        await asyncio.sleep(3)
                else:
                    print(f"  ✅ [{i}/{len(posts)}] {actual_slug}: OK")

        print(f"\n{'='*65}")
        print(f"SUMMARY: {total_missing} missing → {total_fixed} fixed")
        if total_fixed > 0:
            print("Now run: python scripts/build_articles.py")


if __name__ == '__main__':
    asyncio.run(main())
