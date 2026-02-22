"""
Deep audit of all generated articles, images, and Instagram posts.
"""
import json, os, glob

BASE = r'c:\Users\Omar\Desktop\little-smart-genius-site\Nouveau dossier\online\Little_Smart_Genius'
posts_dir = os.path.join(BASE, 'posts')
images_dir = os.path.join(BASE, 'images')
ig_dir = os.path.join(BASE, 'instagram')

# Count all files
post_files = sorted(glob.glob(os.path.join(posts_dir, '*.json')))
image_files = glob.glob(os.path.join(images_dir, '*.webp'))
ig_jpg = sorted(glob.glob(os.path.join(ig_dir, '*.jpg')))
ig_txt = sorted(glob.glob(os.path.join(ig_dir, '*.txt')))

print("=" * 130)
print("  COMPREHENSIVE POST-GENERATION AUDIT")
print("=" * 130)

print(f"\n--- FILE COUNTS ---")
print(f"  Article JSONs : {len(post_files)}")
print(f"  Images (webp) : {len(image_files)}")
print(f"  Instagram JPG : {len(ig_jpg)}")
print(f"  Instagram TXT : {len(ig_txt)}")

# Analyze each article
sep = "=" * 130
print(f"\n{sep}")
header = f"{'#':>2} {'SLOT':>8} {'WORDS':>6} {'SEO':>4} {'H2':>3} {'H3':>3} {'IMG':>4} {'FAQ':>4} {'META':>5} {'IMGTAG':>6}  TITLE"
print(header)
print(sep)

total_words = 0
issues = []
all_articles = []

for i, pf in enumerate(post_files, 1):
    with open(pf, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    title_full = data.get('title', 'NO TITLE')
    title = title_full[:58]
    slug = data.get('slug', '')
    slot = data.get('slot', '?')
    words = data.get('word_count', 0)
    seo = data.get('seo_score', 0)
    meta = data.get('meta_description', '')
    content = data.get('content', '')
    imgs = data.get('images', [])
    faq = data.get('faq', [])
    
    h2_count = content.count('<h2')
    h3_count = content.count('<h3')
    meta_len = len(meta)
    img_count = len(imgs)
    faq_count = len(faq)
    total_words += words
    
    # Count <img> tags in HTML content
    img_tags = content.count('<img ')
    
    # Check for issues
    art_issues = []
    if words < 1500: art_issues.append(f'LOW WORDS ({words})')
    if seo < 70: art_issues.append(f'LOW SEO ({seo})')
    if h2_count < 3: art_issues.append(f'FEW H2 ({h2_count})')
    if img_count < 3: art_issues.append(f'FEW IMGS ({img_count})')
    if meta_len < 90 or meta_len > 170: art_issues.append(f'META LEN ({meta_len})')
    if len(title_full) > 70: art_issues.append(f'TITLE LONG ({len(title_full)}c)')
    
    # Check images exist on disk
    missing_imgs = 0
    for img in imgs:
        img_path = os.path.join(BASE, img.get('path', '').lstrip('/'))
        if not os.path.exists(img_path):
            missing_imgs += 1
    if missing_imgs > 0: art_issues.append(f'MISSING {missing_imgs} IMGS ON DISK')
    
    if img_tags == 0: art_issues.append('NO <img> IN HTML')
    
    # Check Instagram post exists
    ig_match = [f for f in ig_jpg if slug in os.path.basename(f).replace('-ig-', '-')]
    if not ig_match: art_issues.append('NO IG POST')
    
    print(f"{i:>2} {slot:>8} {words:>6} {seo:>4} {h2_count:>3} {h3_count:>3} {img_count:>4} {faq_count:>4} {meta_len:>5} {img_tags:>6}  {title}")
    if art_issues:
        issues.append((i, title, art_issues))
    
    all_articles.append({
        'num': i, 'title': title_full, 'slot': slot, 'words': words,
        'seo': seo, 'h2': h2_count, 'h3': h3_count, 'imgs': img_count,
        'faq': faq_count, 'meta_len': meta_len, 'img_tags': img_tags,
        'issues': art_issues
    })

print(sep)
avg_words = total_words // max(len(post_files), 1)
avg_imgs = len(image_files) // max(len(post_files), 1)
print(f"TOTAL: {len(post_files)} articles, {total_words:,} words, {len(image_files)} images, {len(ig_jpg)} IG posts")
print(f"AVG  : {avg_words} words/article, {avg_imgs} images/article")

# SEO score distribution
seo_scores = [a['seo'] for a in all_articles]
print(f"\nSEO SCORES: min={min(seo_scores)}, max={max(seo_scores)}, avg={sum(seo_scores)//len(seo_scores)}")
above_90 = sum(1 for s in seo_scores if s >= 90)
above_80 = sum(1 for s in seo_scores if s >= 80)
below_80 = sum(1 for s in seo_scores if s < 80)
print(f"  90+: {above_90}  |  80-89: {above_80-above_90}  |  <80: {below_80}")

# Word count distribution
word_counts = [a['words'] for a in all_articles]
print(f"\nWORD COUNTS: min={min(word_counts)}, max={max(word_counts)}, avg={sum(word_counts)//len(word_counts)}")
above_2000 = sum(1 for w in word_counts if w >= 2000)
in_range = sum(1 for w in word_counts if 1600 <= w < 2000)
below_1600 = sum(1 for w in word_counts if w < 1600)
print(f"  2000+: {above_2000}  |  1600-1999: {in_range}  |  <1600: {below_1600}")

# Check articles.json
print(f"\n--- DATA FILES ---")
articles_json = os.path.join(BASE, 'articles.json')
with open(articles_json, 'r', encoding='utf-8') as f:
    aj = json.load(f)
print(f"  articles.json    : {len(aj)} entries")

search_json = os.path.join(BASE, 'search_index.json')
with open(search_json, 'r', encoding='utf-8') as f:
    sj = json.load(f)
print(f"  search_index.json: {len(sj)} entries")

used_json = os.path.join(BASE, 'used_topics.json')
with open(used_json, 'r', encoding='utf-8') as f:
    uj = json.load(f)
print(f"  used_topics.json : {len(uj)} topics used")

# Check sitemap
sitemap = os.path.join(BASE, 'sitemap.xml')
with open(sitemap, 'r', encoding='utf-8') as f:
    sm = f.read()
url_count = sm.count('<url>')
print(f"  sitemap.xml      : {url_count} URLs")

# Issues summary
if issues:
    print(f"\n{'='*130}")
    print(f"  ISSUES FOUND: {len(issues)} articles with problems")
    print(f"{'='*130}")
    for idx, title, probs in issues:
        print(f"\n  Article #{idx}: {title}")
        for p in probs:
            print(f"    [!!] {p}")
else:
    print(f"\n{'='*130}")
    print("  ALL ARTICLES PASS QUALITY CHECKS")
    print(f"{'='*130}")

# Check for orphan images (images without matching article)
print(f"\n--- ORPHAN CHECK ---")
article_slugs = set()
for pf in post_files:
    with open(pf, 'r', encoding='utf-8') as f:
        data = json.load(f)
    article_slugs.add(data.get('slug', ''))

orphan_imgs = 0
for img in image_files:
    basename = os.path.basename(img)
    matched = any(slug in basename for slug in article_slugs if slug)
    if not matched:
        orphan_imgs += 1
        print(f"  [ORPHAN IMG] {basename}")

orphan_ig = 0
for ig in ig_jpg:
    basename = os.path.basename(ig)
    matched = any(slug in basename for slug in article_slugs if slug)
    if not matched:
        orphan_ig += 1
        print(f"  [ORPHAN IG] {basename}")

if orphan_imgs == 0 and orphan_ig == 0:
    print("  No orphan files found - all images/IG match articles")

print(f"\n{'='*130}")
print("  AUDIT COMPLETE")
print(f"{'='*130}")
