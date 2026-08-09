import re
import os
import shutil

f1 = 'data/archive_posts/fine-motor-busy-book-pages-for-toddlers-printable-1779274941.json'
with open(f1, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace any sequence starting with the bad prefix and ending with loading=
text = re.sub(r'fine-motor-busy-book-pages-for-toddlers-printable-best-resources-img4-thumb.*?loading=', "fine-motor-busy-book-pages-for-toddlers-printable-best-resources-img4-1779274813.webp' alt='fine motor' loading=", text)

with open(f1, 'w', encoding='utf-8') as f:
    f.write(text)

shutil.copy(f1, 'posts/')
html_path = 'articles/fine-motor-busy-book-pages-for-toddlers-printable.html'
if os.path.exists(html_path): os.remove(html_path)


f2 = 'data/archive_posts/spot-the-difference-activities-sharpen-focus-in-6-year-olds-1777027975.json'
with open(f2, 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'how-spot-the-difference-activities-sharpen-focus-in-6-year-olds-various.*?loading=', "how-spot-the-difference-activities-sharpen-focus-in-6-year-olds-img5-1777027855.webp' alt='spot the difference' loading=", text)

with open(f2, 'w', encoding='utf-8') as f:
    f.write(text)

shutil.copy(f2, 'posts/')
html_path = 'articles/spot-the-difference-activities-sharpen-focus-in-6-year-olds.html'
if os.path.exists(html_path): os.remove(html_path)

print('Done')
