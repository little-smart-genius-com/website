import json
f1 = 'data/archive_posts/fine-motor-busy-book-pages-for-toddlers-printable-1779274941.json'
with open(f1, 'r', encoding='utf-8') as f:
    d = json.load(f)
c = d['content']
import re
m = re.search(r'fine-motor-busy-book-pages-for-toddlers-printable-best-resources-img4-thumb.{0,400}loading=', c, re.DOTALL)
print("MATCH 1:", m)
if m: print(repr(m.group(0)))

f2 = 'data/archive_posts/spot-the-difference-activities-sharpen-focus-in-6-year-olds-1777027975.json'
with open(f2, 'r', encoding='utf-8') as f:
    d2 = json.load(f)
c2 = d2['content']
m2 = re.search(r'how-spot-the-difference-activities-sharpen-focus-in-6-year-olds-various.{0,400}loading=', c2, re.DOTALL)
print("MATCH 2:", m2)
if m2: print(repr(m2.group(0)))
