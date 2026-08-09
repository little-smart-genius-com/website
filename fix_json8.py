import json
import os
import shutil

f1 = 'data/archive_posts/fine-motor-busy-book-pages-for-toddlers-printable-1779274941.json'
with open(f1, 'r', encoding='utf-8') as f:
    d = json.load(f)
c = d['content']
idx = c.find("<img src='../images/fine-motor-busy-book-pages-for-toddlers-printable-best-resources-img4-thumb")
if idx != -1:
    end_idx = c.find("</p>", idx)
    if end_idx != -1:
        c = c[:idx] + "<img src='../images/fine-motor-busy-book-pages-for-toddlers-printable-best-resources-img4-1779274813.webp' alt='fine motor' loading='lazy'>" + c[end_idx:]
        d['content'] = c
        with open(f1, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)

f2 = 'data/archive_posts/spot-the-difference-activities-sharpen-focus-in-6-year-olds-1777027975.json'
with open(f2, 'r', encoding='utf-8') as f:
    d2 = json.load(f)
c2 = d2['content']
idx2 = c2.find("<img src='../images/how-spot-the-difference-activities-sharpen-focus-in-6-year-olds-various")
if idx2 != -1:
    end_idx2 = c2.find("<h2>Why Spot the Difference Puzzles Matter", idx2)
    if end_idx2 != -1:
        c2 = c2[:idx2] + "<img src='../images/how-spot-the-difference-activities-sharpen-focus-in-6-year-olds-img5-1777027855.webp' alt='spot the difference' loading='lazy'></figure>\n\n" + c2[end_idx2:]
        d2['content'] = c2
        with open(f2, 'w', encoding='utf-8') as f:
            json.dump(d2, f, ensure_ascii=False, indent=2)

print('Replaced!')
