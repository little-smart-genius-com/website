#!/usr/bin/env python3
"""Add missing orphan articles to articles.json"""
import os, re, json
from datetime import datetime

missing = [
    '4-week-shadow-matching-challenge-builds-skills',
    'how-word-search-puzzles-transform-reading-skills-in-children'
]

entries = []
for slug in missing:
    filepath = os.path.join('articles', slug + '.html')
    if not os.path.exists(filepath):
        print('FILE NOT FOUND: {}'.format(filepath))
        continue
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()
    
    # Extract title
    m = re.search(r'<title>([^<]+)</title>', html)
    title = m.group(1).replace(' | Little Smart Genius','').strip() if m else slug.replace('-', ' ').title()
    
    # Extract meta description
    m = re.search(r'<meta name="description" content="([^"]+)"', html)
    excerpt = m.group(1) if m else ''
    
    # Extract og:image
    m = re.search(r'<meta property="og:image" content="([^"]+)"', html)
    image = m.group(1).replace('https://littlesmartgenius.com/', '') if m else ''
    
    # Extract date
    m = re.search(r'<meta property="article:published_time" content="([^"]+)"', html)
    iso_date = m.group(1) if m else datetime.now().isoformat()
    
    # Word count
    text = re.sub(r'<[^>]+>', '', html)
    word_count = len(text.split())
    reading_time = max(1, word_count // 200)
    
    try:
        date_str = datetime.fromisoformat(iso_date.replace('Z','+00:00')).strftime('%B %d, %Y')
    except Exception:
        date_str = iso_date
    
    entry = {
        'title': title,
        'slug': slug,
        'date': date_str,
        'iso_date': iso_date,
        'category': 'Education',
        'author': 'LSG_Admin',
        'author_name': 'Little Smart Genius',
        'excerpt': excerpt[:200],
        'image': image,
        'reading_time': reading_time,
        'url': 'articles/{}.html'.format(slug),
        'keywords': [],
        'word_count': word_count,
        'slot': 'keyword'
    }
    entries.append(entry)
    print('Prepared: {} '.format(title))

# Add to articles.json
with open('articles.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

data['articles'].extend(entries)
data['total_articles'] = len(data['articles'])
data['generated_at'] = datetime.now().isoformat()

with open('articles.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print('Added {} entries. Total now: {}'.format(len(entries), data['total_articles']))
