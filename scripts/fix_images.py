"""
FIX IMAGES — Scan articles for missing images and regenerate them.
Uses the EXACT same Art Director + Master Prompt pipeline as auto_blog_v6_ultimate.py.
Referenced by autoblog.yml workflow (fix-images action).

Usage:
  python scripts/fix_images.py                                          # Fix missing images for all articles
  python scripts/fix_images.py --slug my-slug                           # Fix missing for one article
  python scripts/fix_images.py --slug my-slug --force                   # Force regen ALL images for one article
  python scripts/fix_images.py --slug my-slug --force --image-type cover  # Regen ONLY the cover
  python scripts/fix_images.py --slug my-slug --force --image-type img3   # Regen ONLY img3

Key principle: SAME filename, SAME pipeline, SAME style.
When regenerating, the image file is overwritten in-place so no JSON/HTML changes are needed.
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

# === IMPORT THE EXACT SAME MASTER PROMPT TEMPLATES AS V6 ===
sys.path.insert(0, SCRIPT_DIR)
from master_prompt import build_prompt as master_build_prompt  # V8 master prompts (6 lighting templates)

# === EXACT SAME CONFIG AS V6 ===
POLLINATIONS_MODEL = "klein-large"
IMAGE_WIDTH, IMAGE_HEIGHT = 1200, 675

# Load all API keys (primary + backup) — same as V6
POLLINATIONS_KEYS = [os.getenv(f"POLLINATIONS_API_KEY_{i}") for i in range(1, 6)]
POLLINATIONS_KEYS = [k for k in POLLINATIONS_KEYS if k and len(k) > 5]
POLLINATIONS_BACKUP_KEYS = [os.getenv(f"POLLINATIONS_API_KEY_BCK_{i}") for i in range(1, 6)]
POLLINATIONS_BACKUP_KEYS = [k for k in POLLINATIONS_BACKUP_KEYS if k and len(k) > 5]

if not POLLINATIONS_KEYS:
    POLLINATIONS_KEYS = [""]  # anonymous fallback

# === V8 ART DIRECTOR SYSTEM PROMPT — EXACT COPY FROM V6 ===
ART_DIRECTOR_SYSTEM_V8 = (
    "You are an expert Art Director for educational children's content. "
    "Your ONLY job is to return a highly descriptive, unique, and highly creative subject text (around 60 to 90 words). "
    "This text will replace the [SUJET] placeholder in a film-grade Pixar template. "
    "You MUST be extremely creative. Each image in the article must have a completely distinct scene, action, "
    "and materials based specifically on the provided H2 Section Context. "
    "CRITICAL REQUIREMENTS:\n"
    "1. All characters (children AND adults) MUST be explicitly described as joyful, happy, and having glowing smiles.\n"
    "2. NO characters should have their tongues sticking out (mouths closed or gently smiling).\n"
    "3. IMPORTANT: Include a mix of characters. Do not only feature children. Frequently include a parent or a teacher actively enthusiastically playing, guiding, or cooperating with the kids.\n"
    "4. Detail specific, tangible, interactive educational props (e.g., holding a shiny magnifying glass, assembling large colorful floor puzzles, moving pieces on a board game, coloring on vibrant worksheets).\n"
    "5. Emphasize a warm, cozy, highly detailed classroom or home environment with sunlight streaming in.\n"
    "6. DO NOT output full prompts, lighting terminology, or style formatting. DO NOT include 'Pixar', '3D', 'Golden hour', etc.\n"
    "7. DIVERSIFY compositions based on your assigned 'Role'. If assigned a wide shot, show the environment AND people. If assigned a flat-lay or detailed shot, focus tightly on HANDS and MATERIALS from an overhead/bird's-eye or close-up perspective, explicitly mentioning hands holding tools.\n"
    "Just describe the specific unique characters (or just hands), their activity with props, and their surroundings."
)

# === V8 IMAGE ROLES — EXACT COPY FROM V6 ===
IMAGE_ROLES = [
    "Image 1 (Cover): Wide shot of children/parents engaged in activity (current style)",
    "Image 2: CLOSE-UP flat-lay of hands working on the worksheet/puzzle (bird's-eye angle, focus on hands and materials)",
    "Image 3: OVERHEAD shot of multiple children's hands collaborating on a shared activity page",
    "Image 4: DETAIL SHOT of the actual educational material with art supplies around (colored pencils, scissors)",
    "Image 5: Close-up of a child's hands interacting with a specific prop (puzzle piece, game board, coloring page)",
    "Image 6: Wide or medium shot showing the learning environment with visible worksheets on the table",
]

NO_TEXT_SUFFIX = (
    ", ABSOLUTELY NO text, letters, words, numbers, titles, captions, labels, "
    "watermarks, or UI overlays in the image, pure visual storytelling only"
)


def get_image_index(image_type):
    """Convert image type to index: cover=0, img1=1, img2=2, ..., img5=5."""
    if image_type == 'cover':
        return 0
    m = re.match(r'img(\d+)', image_type)
    return int(m.group(1)) if m else 0


def build_art_director_subject(title, concept, image_type):
    """Build a fallback Art Director subject (used when DeepSeek is not available).
    Matches V6 fallback pattern exactly."""
    idx = get_image_index(image_type)
    role = IMAGE_ROLES[idx % len(IMAGE_ROLES)]

    if idx == 0:
        return (
            f"a group of joyful, diverse children and a smiling teacher "
            f"engaged in {concept} activities together, carefully placing "
            f"pieces and smiling, in a warm cozy classroom with sunlight streaming in"
        )
    elif idx == 1:
        return (
            f"an overhead flat-lay view of small hands carefully working on colorful worksheets "
            f"about {concept}, with colored pencils, stickers, and a magnifying glass scattered around "
            f"on a warm wooden table in soft morning light"
        )
    elif idx == 2:
        return (
            f"multiple children's hands reaching across a large shared activity page about {concept}, "
            f"collaborating together, with markers, glue sticks, and craft materials, "
            f"on a bright classroom table with sunlight streaming through windows"
        )
    elif idx == 3:
        return (
            f"a detail shot of beautifully designed educational materials about {concept}, "
            f"surrounded by colorful art supplies like scissors, colored pencils, glitter glue, "
            f"and stickers on a neat desk with a plant in the background"
        )
    elif idx == 4:
        return (
            f"a close-up of a child's small hands joyfully interacting with a puzzle piece "
            f"related to {concept}, with a parent's hands gently guiding nearby, "
            f"in a cozy home setting with warm natural light"
        )
    else:
        return (
            f"a wide shot of a warm, inviting learning environment where children and a teacher "
            f"sit around a table covered with worksheets about {concept}, all smiling and engaged, "
            f"with educational posters on the walls and sunlight through large windows"
        )


async def fetch_image(session, prompt, out_path, idx):
    """Fetch image using V6 method: gen.pollinations.ai with auth bearer.
    EXACT same implementation as auto_blog_v6_ultimate.py fetch_and_save_image."""
    clean_prompt = re.sub(r'[^a-zA-Z0-9 ,.-]', '', prompt + NO_TEXT_SUFFIX)
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

                        # Auto-generate thumbnail for cover images (same as V6)
                        if idx == 0:
                            thumb_path = out_path.replace(".webp", "-thumb.webp")
                            if img.width > 600:
                                aspect_ratio = img.height / img.width
                                new_height = int(600 * aspect_ratio)
                                thumb_img = img.resize((600, new_height), Image.LANCZOS)
                            else:
                                thumb_img = img.copy()
                            thumb_img.save(thumb_path, "WEBP", quality=80, optimize=True)
                            print(f"      [OK] Thumbnail saved: {os.path.basename(thumb_path)}")

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


def find_existing_images(slug, post_data):
    """Find ALL existing image filenames for a given article (from JSON + HTML)."""
    images = {}  # type -> filename

    # Cover image from JSON
    cover = post_data.get('image', '')
    if cover:
        cover_file = os.path.basename(cover)
        images['cover'] = cover_file

    # Content images from JSON content
    content = post_data.get('content', '')
    img_pattern = re.compile(r'src=["\'](?:\.\./)?images/([^"\']+)["\']', re.IGNORECASE)
    for match in img_pattern.finditer(content):
        img_file = match.group(1)
        if '-img' in img_file:
            idx_match = re.search(r'-img(\d+)', img_file)
            if idx_match:
                idx = int(idx_match.group(1))
                images[f'img{idx}'] = img_file

    # Also check HTML file
    html_path = os.path.join(ARTICLES_DIR, f"{slug}.html")
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()
        for match in img_pattern.finditer(html):
            img_file = match.group(1)
            if '-img' in img_file:
                idx_match = re.search(r'-img(\d+)', img_file)
                if idx_match:
                    idx = int(idx_match.group(1))
                    if f'img{idx}' not in images:
                        images[f'img{idx}'] = img_file
            elif '-cover' in img_file and 'cover' not in images:
                images['cover'] = img_file

    return images


def find_missing_images(slug, post_data):
    """Check which images are missing for a given article."""
    images = find_existing_images(slug, post_data)
    missing = []

    for img_type, img_file in images.items():
        img_path = os.path.join(IMAGES_DIR, img_file)
        if not os.path.exists(img_path):
            missing.append((img_type, img_file))

    # If no cover at all
    if 'cover' not in images:
        missing.append(('cover', f'{slug}-cover-missing.webp'))

    return missing


async def regenerate_images(session, post_file, targets, title, slug):
    """
    Regenerate the specified images using the EXACT V6 Art Director pipeline.
    KEEPS THE SAME FILENAME — overwrites in-place.
    """
    fixed = 0

    for img_type, existing_filename in targets:
        idx = get_image_index(img_type)

        # Build subject description using Art Director fallback
        # (same as V6 fallback when DeepSeek is unavailable)
        concept = title.replace('-', ' ')
        subject = build_art_director_subject(title, concept, img_type)

        # Wrap with the V8 master prompt template (same as V6 agent_5_art_director)
        full_prompt = master_build_prompt(subject, image_index=idx)

        # === KEEP THE SAME FILENAME ===
        # If we have an existing filename, overwrite it in-place
        out_path = os.path.join(IMAGES_DIR, existing_filename)

        print(f"      🎨 [{img_type}] Using master template #{idx+1} ({IMAGE_ROLES[idx % len(IMAGE_ROLES)][:40]}...)")
        print(f"      📄 Target: {existing_filename} (overwrite in-place)")
        print(f"      Generating...")

        result = await fetch_image(session, full_prompt, out_path, idx)

        if result:
            fixed += 1
            print(f"      ✅ {img_type} regenerated — same file, same references, no JSON/HTML change needed")
            await asyncio.sleep(2)
        else:
            print(f"      ❌ Failed to generate {img_type}")

    return fixed


async def fix_article_images(session, post_file, force=False, image_type_filter=None):
    """Fix missing (or force-regenerate) images for a single article."""
    with open(post_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    slug = data.get('slug', os.path.basename(post_file).replace('.json', ''))
    title = data.get('title', slug)
    existing = find_existing_images(slug, data)

    if force:
        # Force mode: regenerate specified image(s) even if they exist
        targets = []
        if image_type_filter:
            # Single image type requested
            if image_type_filter in existing:
                targets.append((image_type_filter, existing[image_type_filter]))
            else:
                print(f"  ⚠️  {slug}: Image type '{image_type_filter}' not found in article references")
                print(f"      Available: {list(existing.keys())}")
                return 0
        else:
            # All images
            for img_type in sorted(existing.keys(), key=lambda x: get_image_index(x)):
                targets.append((img_type, existing[img_type]))

        if not targets:
            print(f"  ⚠️  {slug}: No images found to regenerate")
            return 0

        print(f"  🔄 {slug}: Force regenerating {len(targets)} image(s)")
        for img_type, fname in targets:
            print(f"      - {img_type}: {fname}")

        return await regenerate_images(session, post_file, targets, title, slug)

    else:
        # Normal mode: only fix missing
        missing = find_missing_images(slug, data)
        if not missing:
            print(f"  ✅ {slug}: All images present")
            return 0

        print(f"  ⚠️  {slug}: {len(missing)} missing image(s)")
        for img_type, img_file in missing:
            print(f"      - {img_type}: {img_file}")

        # For missing images, we generate with the same Art Director pipeline
        # but create a new file (since the original doesn't exist)
        fixed = 0
        ts = int(time.time())
        json_updated = False

        for img_type, old_filename in missing:
            idx = get_image_index(img_type)

            # Use the SAME filename if it's a real reference (not "missing" placeholder)
            if 'missing' in old_filename:
                new_name = f"{slug}-{img_type}-{ts}.webp"
            else:
                new_name = old_filename  # Keep original name

            out_path = os.path.join(IMAGES_DIR, new_name)

            # Build Art Director subject + master prompt
            concept = title.replace('-', ' ')
            subject = build_art_director_subject(title, concept, img_type)
            full_prompt = master_build_prompt(subject, image_index=idx)

            print(f"      🎨 [{img_type}] Using master template #{idx+1}")
            print(f"      Generating {new_name}...")
            result = await fetch_image(session, full_prompt, out_path, idx)

            if result:
                fixed += 1
                # Only update JSON if we created a brand new filename
                if new_name != old_filename:
                    if img_type == 'cover':
                        data['image'] = f"images/{new_name}"
                        json_updated = True
                    else:
                        content = data.get('content', '')
                        old_pattern = re.escape(old_filename)
                        content = re.sub(
                            rf'(?:\.\./)?images/{old_pattern}',
                            f"../images/{new_name}",
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
            print(f"      📝 Updated JSON references")

        return fixed


async def main():
    parser = argparse.ArgumentParser(description="Fix/regenerate article images (V6 pipeline)")
    parser.add_argument('--slug', type=str, default='', help='Target a single article by slug')
    parser.add_argument('--force', action='store_true', help='Force regenerate even if images exist')
    parser.add_argument('--image-type', type=str, default='', help='Target specific image: cover, img1, img2...')
    args = parser.parse_args()

    mode_label = "FORCE REGEN" if args.force else "Fix missing"
    type_label = f" ({args.image_type})" if args.image_type else ""
    print(f"\n{'='*65}")
    print(f"FIX IMAGES — {mode_label}{type_label}")
    print(f"Pipeline: V8 Art Director + Master Prompt Templates (same as V6)")
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
        if fixed > 0 and not args.force:
            print("Now run: python scripts/build_articles.py")
    else:
        if args.force:
            print("⚠️  --force without --slug will regenerate ALL images for ALL articles!")
            print("    Use --slug to target a specific article.")
            sys.exit(1)

        # All articles - scan for missing only
        posts = sorted(glob.glob(os.path.join(POSTS_DIR, '*.json')))
        print(f"\nScanning {len(posts)} articles for missing images...\n")

        total_fixed = 0
        total_missing = 0

        async with aiohttp.ClientSession() as session:
            for i, pf in enumerate(posts, 1):
                slug = os.path.basename(pf).replace('.json', '')
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
