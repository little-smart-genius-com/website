import glob
import re
import os
import shutil

base = 'data/archive_posts'

# 1. preschool
preschool_files = glob.glob(os.path.join(base, 'preschool-counting-mats-6-screen-free-activities*.json'))
for f in preschool_files:
    with open(f, 'r', encoding='utf-8') as file:
        data = file.read()
    data = data.replace('preschool-counting-mats-printable-for-handson-math-6-screen-free-activities-img5-1780213932.webp', 'preschool-counting-mats-printable-for-hands-on-math-6-screen-free-activities-img5-1780213932.webp')
    with open(f, 'w', encoding='utf-8') as file:
        file.write(data)
    shutil.copy(f, 'posts/')
    html_path = 'articles/' + os.path.basename(f).split('-17')[0] + '.html'
    if os.path.exists(html_path): os.remove(html_path)

# 2. rainy
rainy_files = glob.glob(os.path.join(base, 'rainy-day-art-challenge-cards-for-kids-6-ideas*.json'))
for f in rainy_files:
    with open(f, 'r', encoding='utf-8') as file:
        data = file.read()
    data = data.replace('rainy-day-art-challenge-cards-for-kids-printable-best-6-the-ideas5-img5-17771842633e7', 'rainy-day-art-challenge-cards-for-kids-printable-best-6-ideas-img5-1777184263.webp')
    with open(f, 'w', encoding='utf-8') as file:
        file.write(data)
    shutil.copy(f, 'posts/')
    html_path = 'articles/' + os.path.basename(f).split('-17')[0] + '.html'
    if os.path.exists(html_path): os.remove(html_path)

# 3. spot 6
spot6_files = glob.glob(os.path.join(base, 'spot-the-difference-activities-sharpen-focus-in-6-year-olds*.json'))
for f in spot6_files:
    with open(f, 'r', encoding='utf-8') as file:
        data = file.read()
    err_str = 'how-spot-the-difference-activities-sharpen-focus-in-6-year-olds-various family sized comfort steady reading page . Glet→ simple clean session images loading='
    data = data.replace(err_str, "how-spot-the-difference-activities-sharpen-focus-in-6-year-olds-img5-1777027855.webp' alt='spot the difference' loading=")
    with open(f, 'w', encoding='utf-8') as file:
        file.write(data)
    shutil.copy(f, 'posts/')
    html_path = 'articles/' + os.path.basename(f).split('-17')[0] + '.html'
    if os.path.exists(html_path): os.remove(html_path)

# 4. spot 7
spot7_files = glob.glob(os.path.join(base, 'spot-the-difference-animal-puzzles-sharpen-focus-7-year-olds*.json'))
for f in spot7_files:
    with open(f, 'r', encoding='utf-8') as file:
        data = file.read()
    data = data.replace('how-spot-the-difference-animals-puzzles-sharpen-focus-in-7-year-olds-img4-1781970447.webp', 'how-spot-the-difference-animals-puzzles-sharpen-focus-in-7-year-olds-img4-1781970444.webp')
    with open(f, 'w', encoding='utf-8') as file:
        file.write(data)
    shutil.copy(f, 'posts/')
    html_path = 'articles/' + os.path.basename(f).split('-17')[0] + '.html'
    if os.path.exists(html_path): os.remove(html_path)

print('Done')
