"""
Fix image duplication issues in article JSON files.
1. Removes cover image from inline <img> tags in article content.
2. Removes duplicate inline images (same image appearing twice).
3. Rebuilds articles after fixing.
"""
import json, glob, os, re, sys

sys.stdout.reconfigure(encoding='utf-8')

PROJ = os.path.dirname(os.path.abspath(__file__))
POSTS = os.path.join(PROJ, 'posts')
IMAGES = os.path.join(PROJ, 'images')

def remove_duplicate_img_tags(content, cover_basename):
    """Remove inline <img> or <figure> elements referencing the cover or already-seen images."""
    seen = set()
    changed = False

    # Pattern: any <figure>...</figure> or standalone <img ...> containing a known duplicate
    # Strategy: extract all figure blocks first
    figure_pattern = re.compile(r'<figure[^>]*>.*?<img[^>]+src=["\']([^"\']*)["\'][^>]*>.*?</figure>', re.DOTALL | re.IGNORECASE)
    img_pattern = re.compile(r'<img[^>]+src=["\']([^"\']*)["\'][^>]*/?>', re.IGNORECASE)

    # Remove entire <figure> blocks containing duplicate images
    def figure_replacer(m):
        nonlocal changed
        src = m.group(1)
        basename = os.path.basename(src)
        if basename == cover_basename:
            changed = True
            print(f"    [REMOVE COVER INLINE] {basename}")
            return ''
        if basename in seen:
            changed = True
            print(f"    [REMOVE DUPLICATE] {basename}")
            return ''
        seen.add(basename)
        return m.group(0)

    content = figure_pattern.sub(figure_replacer, content)

    # Also handle standalone <img> not inside a <figure>
    def img_replacer(m):
        nonlocal changed
        src = m.group(1)
        basename = os.path.basename(src)
        if basename == cover_basename:
            changed = True
            print(f"    [REMOVE COVER STANDALONE IMG] {basename}")
            return ''
        if basename in seen:
            changed = True
            print(f"    [REMOVE DUPLICATE STANDALONE IMG] {basename}")
            return ''
        seen.add(basename)
        return m.group(0)

    content = img_pattern.sub(img_replacer, content)

    return content, changed


total_changed = 0
posts = sorted(glob.glob(os.path.join(POSTS, '*.json')))
for pf in posts:
    with open(pf, 'r', encoding='utf-8') as f:
        d = json.load(f)
    
    slug = d.get('slug', os.path.basename(pf))
    cover_path = d.get('image', '')
    cover_name = os.path.basename(cover_path)
    content = d.get('content', '')

    raw_imgs = re.findall(r'<img[^>]+src=["\'][^"\']*images/([^"\']+)["\']', content)
    inline_names = [os.path.basename(x) for x in raw_imgs]
    
    has_cover_inline = cover_name and cover_name in inline_names
    has_dupes = len(inline_names) != len(set(inline_names))

    if not has_cover_inline and not has_dupes:
        continue

    print(f"\n{'=' * 65}")
    print(f"FIXING: {slug}")
    print(f"  Cover: {cover_name}")
    print(f"  Inline before: {inline_names}")

    new_content, changed = remove_duplicate_img_tags(content, cover_name)
    
    if changed:
        d['content'] = new_content
        with open(pf, 'w', encoding='utf-8') as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
        total_changed += 1

        # Verify what we have now
        new_imgs = re.findall(r'<img[^>]+src=["\'][^"\']*images/([^"\']+)["\']', new_content)
        new_inline = [os.path.basename(x) for x in new_imgs]
        print(f"  Inline after:  {new_inline}")
        print(f"  [SAVED] {os.path.basename(pf)}")

print(f"\n{'=' * 65}")
print(f"DONE. Fixed {total_changed} JSON files.")
print("Now run: python scripts/build_articles.py")
