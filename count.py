import json
f1 = 'data/archive_posts/fine-motor-busy-book-pages-for-toddlers-printable-1779274941.json'
with open(f1, 'r', encoding='utf-8') as f:
    d = json.load(f)
c = d['content']
print("Count 1:", c.count('fine-motor-busy-book-pages-for-toddlers-printable-best-resources-img4-thumb'))

f2 = 'data/archive_posts/spot-the-difference-activities-sharpen-focus-in-6-year-olds-1777027975.json'
with open(f2, 'r', encoding='utf-8') as f:
    d2 = json.load(f)
c2 = d2['content']
print("Count 2:", c2.count('how-spot-the-difference-activities-sharpen-focus-in-6-year-olds-various'))
