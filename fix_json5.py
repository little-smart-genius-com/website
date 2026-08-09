import json
import re
import os
import shutil

f1 = 'data/archive_posts/fine-motor-busy-book-pages-for-toddlers-printable-1779274941.json'
with open(f1, 'r', encoding='utf-8') as f:
    data1 = json.load(f)

content1 = data1['content']
content1 = re.sub(r'fine-motor-busy-book-pages-for-toddlers-printable-best-resources-img4-thumb[^"]*?loading=', "fine-motor-busy-book-pages-for-toddlers-printable-best-resources-img4-1779274813.webp' alt='fine motor' loading=", content1)
data1['content'] = content1

with open(f1, 'w', encoding='utf-8') as f:
    json.dump(data1, f, ensure_ascii=False, indent=2)

shutil.copy(f1, 'posts/')

f2 = 'data/archive_posts/spot-the-difference-activities-sharpen-focus-in-6-year-olds-1777027975.json'
with open(f2, 'r', encoding='utf-8') as f:
    data2 = json.load(f)

content2 = data2['content']
content2 = re.sub(r'how-spot-the-difference-activities-sharpen-focus-in-6-year-olds-various[^"]*?loading=', "how-spot-the-difference-activities-sharpen-focus-in-6-year-olds-img5-1777027855.webp' alt='spot the difference' loading=", content2)
data2['content'] = content2

with open(f2, 'w', encoding='utf-8') as f:
    json.dump(data2, f, ensure_ascii=False, indent=2)

shutil.copy(f2, 'posts/')
print('Done modifying JSONs.')
