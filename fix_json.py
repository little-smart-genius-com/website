import glob
import re
import os
import shutil
import json

base = 'data/archive_posts'

def fix_json(file_path, fixes):
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("Could not decode", file_path)
            return

    content = data.get('content_html', '')
    original_content = content
    
    for fix_func in fixes:
        content = fix_func(content)
        
    if content != original_content:
        data['content_html'] = content
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        shutil.copy(file_path, 'posts/')
        html_path = 'articles/' + os.path.basename(file_path).split('-17')[0] + '.html'
        if os.path.exists(html_path):
            os.remove(html_path)
            print("Removed HTML:", html_path)
        print("Fixed:", file_path)

# 1. fine motor
fine_files = glob.glob(os.path.join(base, 'fine-motor-busy-book-pages-for-toddlers-printable*.json'))
for f in fine_files:
    fix_json(f, [
        lambda c: re.sub(r'fine-motor-busy-book-pages-for-toddlers-printable-best-resources-img4-thumb.*?</p loading=', "fine-motor-busy-book-pages-for-toddlers-printable-best-resources-img4-1779274813.webp' alt='fine motor' loading=", c, flags=re.DOTALL)
    ])

# 2. spot 6
spot6_files = glob.glob(os.path.join(base, 'spot-the-difference-activities-sharpen-focus-in-6-year-olds*.json'))
for f in spot6_files:
    fix_json(f, [
        lambda c: re.sub(r'how-spot-the-difference-activities-sharpen-focus-in-6-year-olds-various.*?loading=', "how-spot-the-difference-activities-sharpen-focus-in-6-year-olds-img5-1777027855.webp' alt='spot the difference' loading=", c, flags=re.DOTALL)
    ])

# 3. spot visual
spot_vis_files = glob.glob(os.path.join(base, 'spot-the-difference-sharpens-kids-visual-processing*.json'))
for f in spot_vis_files:
    fix_json(f, [
        lambda c: c.replace('how-spot-the-difference-activities-sharpen-visual-processing-in-kids-img4 changing change flexible low anyway', 'how-spot-the-difference-activities-sharpen-visual-processing-in-kids-img4-1779278879.webp')
    ])

# 4. stem 5
stem5_files = glob.glob(os.path.join(base, 'stem-building-challenges-with-craft-sticks5-proven-mistakes*.json'))
for f in stem5_files:
    fix_json(f, [
        lambda c: c.replace('stem-building-challenges-for-kids-using-craft-sticks-3-proven-mistakes-to-avoid-img3-1780740781.webp', 'stem-building-challenges-for-kids-using-craft-sticks-5-proven-mistakes-to-avoid-img3-1780740781.webp'),
        lambda c: c.replace('stem-building-challenges-for-kids-using-craft-sticks-2-proven-mistakes-to-avoid-img2-1780740781.webp', 'stem-building-challenges-for-kids-using-craft-sticks-5-proven-mistakes-to-avoid-img2-1780740781.webp')
    ])

print('Done applying fixes')
