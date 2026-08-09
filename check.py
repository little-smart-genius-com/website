import json
f = 'data/archive_posts/fine-motor-busy-book-pages-for-toddlers-printable-1779274941.json'
with open(f, 'r', encoding='utf-8') as f:
    d = json.load(f)
c = d['content']
idx = c.find('fine-motor-busy-book-pages-for-toddlers-printable-best-resources-img4-thumb')
print("IDX:", idx)
