import glob
import re
import os
import shutil

base = 'data/archive_posts'

# Fix fine motor busy book
fine_files = glob.glob(os.path.join(base, 'fine-motor-busy-book-pages-for-toddlers-printable*.json'))
for f in fine_files:
    with open(f, 'r', encoding='utf-8') as file:
        data = file.read()
    
    # Let's find exactly what to replace
    # We look for fine-motor-busy-book-pages-for-toddlers-printable-best-resources-img4-thumb...
    # Up to the next known tag or attribute
    # Actually, let's just do a string replace of the exact massive string reported in the error log
    err_str = "fine-motor-busy-book-pages-for-toddlers-printable-best-resources-img4-thumb main my nine d animated recent detail similar technique works ages range download skill whole set turn advance powerful scenario essential positive high progress later small included total room home handle full better stock  solution across skill among families permanent years other resources continue but place separate rotation front confidence turn progress benefit constant manageable value more pattern skill effective moment additional comfortable major shape standard play limited I clever yet age usage</p loading="
    data = data.replace(err_str, "fine-motor-busy-book-pages-for-toddlers-printable-best-resources-img4-1779274813.webp' alt='fine motor' loading=")

    with open(f, 'w', encoding='utf-8') as file:
        file.write(data)
    shutil.copy(f, 'posts/')
    html_path = 'articles/' + os.path.basename(f).split('-17')[0] + '.html'
    if os.path.exists(html_path):
        os.remove(html_path)

# Fix kakurasu
kakurasu_files = glob.glob(os.path.join(base, 'kakurasu-for-kids-logic-puzzle-to-build-mental-math-focus*.json'))
for f in kakurasu_files:
    with open(f, 'r', encoding='utf-8') as file:
        data = file.read()
    
    data = data.replace('kakurasu-for-kids-a-fun-logic-puzzle-that-builds-mental-math-focus-free-download-img4-1763389205.webp', 'kakurasu-for-kids-a-fun-logic-puzzle-that-builds-mental-math-focus-free-download-img4-1778534632.webp')
    data = data.replace('kakurasu-for-kids-a-fun-logic-puzzle-that-builds-mental-math-focus-free-download-img3-1864218471.webp', 'kakurasu-for-kids-a-fun-logic-puzzle-that-builds-mental-math-focus-free-download-img3-1778534632.webp')
    data = data.replace('kakurasu-for-kids-a-fun-logic-puzzle-that-builds-mental-math-focus-free-download-img2-1873342293.webp', 'kakurasu-for-kids-a-fun-logic-puzzle-that-builds-mental-math-focus-free-download-img2-1778534632.webp')
    data = data.replace('kakurasu-for-kids-a-fun-logic-puzzle-that-builds-mental-math-focus-free-download-img5-1744848493.webp', 'kakurasu-for-kids-a-fun-logic-puzzle-that-builds-mental-math-focus-free-download-img5-1778534632.webp')

    with open(f, 'w', encoding='utf-8') as file:
        file.write(data)
    shutil.copy(f, 'posts/')
    html_path = 'articles/' + os.path.basename(f).split('-17')[0] + '.html'
    if os.path.exists(html_path):
        os.remove(html_path)

print('Done')
