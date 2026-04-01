import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__)))
from instagram_generator import generate_instagram_post

with open('articles.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

articles = []

def extract_articles(obj):
    if isinstance(obj, dict):
        if 'title' in obj and 'slug' in obj:
            articles.append(obj)
        else:
            for v in obj.values():
                extract_articles(v)
    elif isinstance(obj, list):
        for item in obj:
            extract_articles(item)

extract_articles(data)

print(f"Loaded {len(articles)} articles. Starting Instagram batch generation...")

for art in articles:
    print(f"Generating for: {art['title']}")
    generate_instagram_post(art)

print("Batch generation complete!")
