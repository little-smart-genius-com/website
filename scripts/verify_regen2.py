import json, os, re, time

CUTOFF = time.time() - (5 * 3600)

with open('articles.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

articles = data.get('articles', [])
total_fresh = 0
total_old = 0
total_missing = 0
problem_articles = []

for article in articles:
    slug = article['slug']
    html_file = os.path.join('articles', slug + '.html')
    
    if not os.path.exists(html_file):
        problem_articles.append((slug, 'NO HTML FILE'))
        continue
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Match ../images/X or /images/X or images/X
    img_refs = re.findall(r'(?:src|content)=["\'](?:\.\./)?(?:/)?images/([^"\'?#]+)', content)
    
    fresh = 0
    old = 0 
    missing = 0
    old_files = []
    missing_files = []
    
    for img_basename in set(img_refs):
        # Handle thumbs/ subfolder
        img_path = os.path.join('images', img_basename)
        if os.path.exists(img_path):
            if os.path.getmtime(img_path) >= CUTOFF:
                fresh += 1
            else:
                old += 1
                old_files.append(img_basename)
        else:
            missing += 1
            missing_files.append(img_basename)
    
    total_fresh += fresh
    total_old += old
    total_missing += missing
    
    if old > 0 or missing > 0:
        detail = f'fresh={fresh} old={old} missing={missing}'
        if old_files:
            detail += f' OLD_FILES={old_files[:2]}'
        if missing_files:
            detail += f' MISSING_FILES={missing_files[:2]}'
        problem_articles.append((slug, detail))

print(f'=== VERIFICATION REPORT ===')
print(f'Total articles: {len(articles)}')
print(f'Total images FRESH (regenerated in last 5h): {total_fresh}')
print(f'Total images OLD (not regenerated): {total_old}') 
print(f'Total images MISSING (file not found): {total_missing}')
print(f'Total accounted: {total_fresh + total_old + total_missing}')
print()
if problem_articles:
    print(f'Articles needing attention: {len(problem_articles)}')
    for slug, issue in problem_articles:
        print(f'  - {slug}: {issue}')
else:
    print('SUCCESS: All images across all 35 articles are FRESH!')
