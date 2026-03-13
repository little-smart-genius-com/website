"""
Fix/regenerate images for articles.
Supports CLI arguments for use from GitHub Actions:
  --slug <slug>        Target a specific article by slug
  --force              Force regeneration of all images (not just placeholders)
  --image-type <type>  Regenerate only a specific image (cover, img1, img2, ...)
Without arguments, processes ALL articles that have placeholder images.
"""
import os
import sys
import json
import re
import glob
import argparse
import requests
import time
from urllib.parse import quote
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

# Cross-platform: works both locally and on GitHub Actions
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
load_dotenv('.env')

# ── Directories ──
DATA_DIR = "data"
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive_posts")
POSTS_DIR = "posts"
IMAGES_DIR = "images"

# ── Collect API keys ──
keys = []
for k, v in os.environ.items():
    if k.startswith("POLLINATIONS_API_KEY") and v and len(v) > 5:
        keys.append(v)

api_key = None
for key in keys:
    try:
        res = requests.get("https://gen.pollinations.ai/account/balance",
                           headers={"Authorization": f"Bearer {key}"}, timeout=10)
        if res.status_code == 200 and res.json().get("balance", 0) > 0:
            api_key = key
            break
    except Exception:
        continue

headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}


def center_crop_resize(img, target_w, target_h):
    """Resize and center-crop an image to exact target dimensions."""
    src_w, src_h = img.size
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        new_w = int(src_h * target_ratio)
        offset = (src_w - new_w) // 2
        img = img.crop((offset, 0, offset + new_w, src_h))
    elif src_ratio < target_ratio:
        new_h = int(src_w / target_ratio)
        offset = (src_h - new_h) // 2
        img = img.crop((0, offset, src_w, offset + new_h))

    return img.resize((target_w, target_h), Image.LANCZOS)


def generate_image(prompt, filename, retries=3):
    """Generate an image via Pollinations, enforce 1200x675, save as WebP."""
    safe_prompt = quote(re.sub(r'[^a-zA-Z0-9 ,.-]', '', prompt))
    models = ["zimage", "flux", "gptimage"]

    for attempt in range(retries):
        model = models[attempt % len(models)]
        url = f"https://gen.pollinations.ai/image/{safe_prompt}?model={model}&width=1200&height=675&nologo=true&enhance=true"
        print(f"  🎨 Attempt {attempt+1}/{retries} with model={model}: {prompt[:60]}...")
        try:
            res = requests.get(url, headers=headers, timeout=90)
            if res.status_code == 200 and len(res.content) > 1024:
                img = Image.open(BytesIO(res.content)).convert("RGB")
                img = center_crop_resize(img, 1200, 675)
                out_path = os.path.join(IMAGES_DIR, filename)
                img.save(out_path, "WEBP", quality=85, optimize=True)
                size_kb = os.path.getsize(out_path) // 1024
                print(f"  ✅ Created {filename} ({size_kb}KB)")
                return f"images/{filename}"
            else:
                print(f"  ⚠️ HTTP {res.status_code}, size={len(res.content)}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        time.sleep(2)

    print(f"  ❌ Failed to generate {filename} after {retries} attempts")
    return None


def find_post_file(slug):
    """Find the JSON file for a given slug across all possible directories."""
    # Search in posts/, data/archive_posts/, data/
    for search_dir in [POSTS_DIR, ARCHIVE_DIR, DATA_DIR]:
        if not os.path.isdir(search_dir):
            continue
        for f in os.listdir(search_dir):
            if f.endswith('.json') and slug in f:
                return os.path.join(search_dir, f)
    return None


def process_article(post_path, force=False, image_type=None):
    """Process a single article: regenerate missing or all images."""
    print(f"\n{'='*60}")
    print(f"📄 Processing: {os.path.basename(post_path)}")

    with open(post_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    slug = data.get('slug', os.path.basename(post_path).rsplit('-', 1)[0])
    content = data.get('content', '')
    title = data.get('title', slug)
    timestamp = str(int(time.time()))
    changed = False

    # ── Cover image ──
    if image_type is None or image_type == 'cover':
        current_cover = data.get('image', '')
        needs_cover = force or 'placehold.co' in current_cover or not current_cover
        if needs_cover:
            print(f"  🖼️ Regenerating COVER...")
            prompt = f"A high quality educational illustration for '{title}', vibrant colorful children's educational content, modern disney pixar style, no text no words"
            cover_filename = f"{slug}-cover-{timestamp}.webp"
            cover_path = generate_image(prompt, cover_filename, retries=6)
            if cover_path:
                data['image'] = cover_path
                changed = True

                # Also generate thumbnail
                try:
                    img = Image.open(os.path.join(IMAGES_DIR, cover_filename))
                    thumb = center_crop_resize(img, 600, 338)
                    thumbs_dir = os.path.join(IMAGES_DIR, "thumbs")
                    os.makedirs(thumbs_dir, exist_ok=True)
                    thumb.save(os.path.join(thumbs_dir, cover_filename), "WEBP", quality=80)
                    print(f"  ✅ Thumbnail created")
                except Exception as e:
                    print(f"  ⚠️ Thumbnail error: {e}")

    # ── Content images ──
    if image_type is None:
        # Process all content images
        img_pattern = re.compile(
            r"<img[^>]+src=['\"]([^'\"]+)['\"][^>]+alt=['\"]([^'\"]*)['\"]",
            re.IGNORECASE
        )
        matches = img_pattern.findall(content)

        idx = 1
        for src, alt in matches:
            is_placeholder = 'placehold.co' in src
            if force or is_placeholder:
                print(f"  🖼️ Regenerating img{idx} (alt: {alt[:50]}...)...")
                prompt = alt if alt else f"educational illustration for {title}, vibrant colorful, no text"
                filename = f"{slug}-img{idx}-{timestamp}.webp"
                img_path = generate_image(prompt, filename, retries=6)
                if img_path:
                    # Replace src in content
                    content = content.replace(src, f"../images/{filename}")
                    changed = True
            idx += 1
    elif image_type and image_type.startswith('img'):
        # Process a specific content image
        img_idx = int(image_type.replace('img', ''))
        print(f"  🖼️ Regenerating {image_type}...")
        # Extract alt text from the specific image
        img_pattern = re.compile(
            r"<img[^>]+src=['\"]([^'\"]+)['\"][^>]+alt=['\"]([^'\"]*)['\"]",
            re.IGNORECASE
        )
        matches = img_pattern.findall(content)
        if img_idx <= len(matches):
            src, alt = matches[img_idx - 1]
            prompt = alt if alt else f"educational illustration for {title}, vibrant colorful, no text"
            filename = f"{slug}-{image_type}-{timestamp}.webp"
            img_path = generate_image(prompt, filename, retries=6)
            if img_path:
                content = content.replace(src, f"../images/{filename}")
                changed = True

    if changed:
        data['content'] = content
        with open(post_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  💾 Saved changes to {post_path}")
    else:
        print(f"  ℹ️ No changes needed")

    return changed


def main():
    parser = argparse.ArgumentParser(description='Fix/regenerate article images')
    parser.add_argument('--slug', type=str, default='', help='Target article slug')
    parser.add_argument('--force', action='store_true', help='Force regeneration of all images')
    parser.add_argument('--image-type', type=str, default=None, help='Specific image type (cover, img1, img2...)')
    args = parser.parse_args()

    os.makedirs(IMAGES_DIR, exist_ok=True)

    if args.slug:
        # Process a single article
        post_path = find_post_file(args.slug)
        if not post_path:
            print(f"❌ No JSON found for slug: {args.slug}")
            sys.exit(1)
        process_article(post_path, force=args.force, image_type=args.image_type)
    else:
        # Process ALL articles with placeholder images
        print("🔍 Scanning all articles for placeholder images...")
        all_posts = []
        for search_dir in [POSTS_DIR, ARCHIVE_DIR]:
            if os.path.isdir(search_dir):
                for f in os.listdir(search_dir):
                    if f.endswith('.json'):
                        all_posts.append(os.path.join(search_dir, f))

        processed = 0
        for post_path in sorted(all_posts):
            try:
                with open(post_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                has_placeholder = 'placehold.co' in data.get('image', '') or 'placehold.co' in data.get('content', '')
                if has_placeholder or args.force:
                    if process_article(post_path, force=args.force, image_type=args.image_type):
                        processed += 1
            except Exception as e:
                print(f"  ❌ Error processing {post_path}: {e}")

        print(f"\n{'='*60}")
        print(f"✅ Done! Processed {processed} articles.")

    print("\nFinished updating images!")


if __name__ == "__main__":
    main()
