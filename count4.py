import json
f1 = 'data/archive_posts/fine-motor-busy-book-pages-for-toddlers-printable-1779274941.json'
with open(f1, 'r', encoding='utf-8') as f:
    d = json.load(f)
c = d['content']
idx = c.find('<img', c.find('fine-motor-busy-book-pages-for-toddlers-printable-best-resources-img4-thumb') - 200)
print("TAG 1:", repr(c[idx:idx+800]))

f2 = 'data/archive_posts/spot-the-difference-activities-sharpen-focus-in-6-year-olds-1777027975.json'
with open(f2, 'r', encoding='utf-8') as f:
    d2 = json.load(f)
c2 = d2['content']
idx2 = c2.find('<img', c2.find('how-spot-the-difference-activities-sharpen-focus-in-6-year-olds-various') - 200)
print("TAG 2:", repr(c2[idx2:idx2+800].encode('utf-8')))

