import json
import os
import glob

# CLEAN MARCH 09
with open("articles.json", "r", encoding="utf-8") as f:
    data = json.load(f)

new_articles = []
removed_slugs = []

for art in data.get("articles", []):
    date_str = art.get("date", "")
    iso_date = art.get("iso_date", "")
    
    if "March 09" in date_str or "2026-03-09" in iso_date:
        removed_slugs.append(art.get("slug"))
    else:
        new_articles.append(art)

data["articles"] = new_articles

with open("articles.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

for slug in removed_slugs:
    path = os.path.join("articles", f"{slug}.html")
    if os.path.exists(path):
        os.remove(path)

print(f"Cleaned {len(removed_slugs)} test articles from March 09.")

# FIX DOUBLE SLASHES
files = glob.glob('blog/*.html') + glob.glob('articles/*.html') + ['index.html']
count = 0
for fpath in files:
    if not os.path.exists(fpath): continue
    with open(fpath, 'r', encoding='utf-8') as f:
        c = f.read()

    new_c = c.replace('href="//favicon.ico"', 'href="/favicon.ico"')
    new_c = new_c.replace('src="//images/', 'src="/images/')
    new_c = new_c.replace('href="//blog/', 'href="/blog/')
    new_c = new_c.replace('href="//freebies.html', 'href="/freebies.html')
    new_c = new_c.replace('href="//products.html', 'href="/products.html')
    new_c = new_c.replace('href="//terms.html', 'href="/terms.html')

    if new_c != c:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new_c)
        count += 1

print(f"Fixed double slashes in {count} HTML files.")
