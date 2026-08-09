import json
import shutil
import os
import glob

base = 'data/archive_posts'

# 1. fine motor
fine_files = glob.glob(os.path.join(base, 'fine-motor-busy-book-pages-for-toddlers-printable*.json'))
for f in fine_files:
    with open(f, 'r', encoding='utf-8') as file:
        data = json.load(file)
    c = data['content']
    start_str = "fine-motor-busy-book-pages-for-toddlers-printable-best-resources-img4-thumb"
    end_str = "</p loading="
    
    start_idx = c.find(start_str)
    end_idx = c.find(end_str, start_idx)
    
    if start_idx != -1 and end_idx != -1:
        to_replace = c[start_idx:end_idx + len(end_str)]
        new_str = "fine-motor-busy-book-pages-for-toddlers-printable-best-resources-img4-1779274813.webp' alt='fine motor' loading="
        data['content'] = c.replace(to_replace, new_str)
        with open(f, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        shutil.copy(f, 'posts/')
        html_path = 'articles/' + os.path.basename(f).split('-17')[0] + '.html'
        if os.path.exists(html_path): os.remove(html_path)


# 2. spot 6
spot6_files = glob.glob(os.path.join(base, 'spot-the-difference-activities-sharpen-focus-in-6-year-olds*.json'))
for f in spot6_files:
    with open(f, 'r', encoding='utf-8') as file:
        data = json.load(file)
    c = data['content']
    start_str = "how-spot-the-difference-activities-sharpen-focus-in-6-year-olds-various"
    end_str = "loading="
    
    start_idx = c.find(start_str)
    end_idx = c.find(end_str, start_idx)
    
    if start_idx != -1 and end_idx != -1:
        to_replace = c[start_idx:end_idx + len(end_str)]
        new_str = "how-spot-the-difference-activities-sharpen-focus-in-6-year-olds-img5-1777027855.webp' alt='spot the difference' loading="
        data['content'] = c.replace(to_replace, new_str)
        with open(f, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        shutil.copy(f, 'posts/')
        html_path = 'articles/' + os.path.basename(f).split('-17')[0] + '.html'
        if os.path.exists(html_path): os.remove(html_path)

# 3. swap screen time
swap_files = glob.glob(os.path.join(base, 'swap-screen-time-for-stir-time-cookbook-for-kids*.json'))
for f in swap_files:
    with open(f, 'r', encoding='utf-8') as file:
        data = json.load(file)
    c = data['content']
    data['content'] = c.replace('swap-screen-time-for-stir-time-the-cookbook-for-kids-that-teaches-real-skills-img2-1781472174', 'swap-screen-time-for-stir-time-the-cookbook-for-kids-that-teaches-real-skills-img2-1781472174.webp')
    with open(f, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    shutil.copy(f, 'posts/')
    html_path = 'articles/' + os.path.basename(f).split('-17')[0] + '.html'
    if os.path.exists(html_path): os.remove(html_path)

print('Done')
