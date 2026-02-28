import json, glob, os, re, sys

sys.stdout.reconfigure(encoding='utf-8')

posts = sorted(glob.glob('posts/*.json'))
ALL_IMGS = {}  # img filename -> list of slugs using it (as cover or inline)

cover_in_inline = []  # articles where cover also appears inline
img_counts = {}  # slug -> nb inline images
too_few = []  # articles with <4 inline content images

for pf in posts:
    with open(pf, 'r', encoding='utf-8') as f:
        d = json.load(f)
    slug = d.get('slug', os.path.basename(pf))
    cover_path = d.get('image', '')
    cover_name = os.path.basename(cover_path)
    
    content = d.get('content', '')
    # Extract filenames from <img src="...images/XXXXX">
    raw = re.findall(r'<img[^>]+src=["\'][^"\']*images/([^"\']+)["\']', content)
    inline_names = [os.path.basename(x) for x in raw]
    
    # Track global image usage
    if cover_name:
        ALL_IMGS.setdefault(cover_name, []).append(f'{slug} [COVER]')
    for n in inline_names:
        ALL_IMGS.setdefault(n, []).append(f'{slug} [inline]')
    
    img_counts[slug] = len(inline_names)
    
    if cover_name and cover_name in inline_names:
        cover_in_inline.append((slug, cover_name, inline_names))
    
    if len(inline_names) < 4:
        too_few.append((slug, len(inline_names)))

print("=" * 70)
print("ARTICLES WHERE COVER IMAGE ALSO APPEARS INLINE:")
print("=" * 70)
if cover_in_inline:
    for slug, cov, inlines in cover_in_inline:
        print(f"  ARTICLE: {slug[:65]}")
        print(f"    COVER: {cov}")
        print(f"    INLINE ({len(inlines)}): {inlines}")
        print()
else:
    print("  NONE - All covers are unique from inline images!")

print()
print("=" * 70)
print("ARTICLES WITH TOO FEW INLINE IMAGES (less than 4):")
print("=" * 70)
for slug, cnt in too_few:
    print(f"  {cnt} images  {slug[:65]}")

print()
print("=" * 70)
print("IMAGES SHARED ACROSS MULTIPLE ARTICLES:")
print("=" * 70)
for img, users in sorted(ALL_IMGS.items()):
    if len(users) > 1:
        print(f"  {img}")
        for u in users:
            print(f"    -> {u}")
        print()

print()
print("=" * 70)
print("INLINE IMAGE COUNT PER ARTICLE:")
print("=" * 70)
for slug, cnt in sorted(img_counts.items(), key=lambda x: x[1]):
    flag = " *** TOO FEW ***" if cnt < 4 else ""
    print(f"  {cnt} imgs  {slug[:65]}{flag}")
