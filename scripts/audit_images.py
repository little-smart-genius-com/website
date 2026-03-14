"""Audit: show per-article image count and find placeholder covers."""
import os, re, glob, json

ARTICLES_DIR = 'articles'

with open('articles.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
articles = data.get('articles', [])

print("=" * 80)
print("  PER-ARTICLE IMAGE AUDIT")
print("=" * 80)

total = 0
placeholder_articles = []
irregular_articles = []

for article in articles:
    slug = article['slug']
    html_file = os.path.join(ARTICLES_DIR, slug + '.html')
    
    if not os.path.exists(html_file):
        print(f"  ❌ {slug}: NO HTML FILE")
        continue
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count local image refs (../images/...)
    local_imgs = re.findall(r'src=["\'](?:\.\./)?(?:/)?images/([^"\'?#]+)', content)
    local_imgs = list(set(local_imgs))
    
    # Count external image refs (https://...)
    external_imgs = re.findall(r'src=["\'](https?://[^"\']+)', content)
    external_imgs = list(set(external_imgs))
    
    # Check if cover is placeholder
    cover_img = article.get('image', '')
    is_placeholder = cover_img.startswith('http') and 'placehold' in cover_img
    
    # Check OG meta image too
    og_imgs = re.findall(r'content=["\'](https?://placehold[^"\']+)', content)
    
    total += len(local_imgs)
    
    status = ""
    if is_placeholder:
        status = " 🔴 PLACEHOLDER COVER"
        placeholder_articles.append(slug)
    
    if len(local_imgs) != 6:
        irregular_articles.append((slug, len(local_imgs)))
    
    print(f"  {slug}")
    print(f"      Local images: {len(local_imgs)} | External: {len(external_imgs)}{status}")
    
    # Show breakdown
    covers = [i for i in local_imgs if '-cover-' in i]
    content_imgs = [i for i in local_imgs if '-img' in i]
    other = [i for i in local_imgs if '-cover-' not in i and '-img' not in i]
    print(f"      Covers: {len(covers)} | Content: {len(content_imgs)} | Other: {len(other)}")
    if other:
        print(f"      Other files: {other[:3]}")
    print()

print("=" * 80)
print(f"  TOTAL local image refs: {total}")
print(f"  Expected (36×6): 216")
print(f"  Excess: {total - 216}")
print()
print(f"  Articles with PLACEHOLDER cover: {len(placeholder_articles)}")
for s in placeholder_articles:
    print(f"    🔴 {s}")
print()
print(f"  Articles with != 6 local images: {len(irregular_articles)}")
for s, c in irregular_articles:
    print(f"    ⚠️ {s}: {c} images")
print("=" * 80)
