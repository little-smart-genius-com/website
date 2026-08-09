import json
import shutil
import os

files = {
    'data/archive_posts/fine-motor-busy-book-pages-for-toddlers-printable-1779274941.json': {
        'search': 'fine-motor-busy-book-pages-for-toddlers-printable-best-resources-img4-thumb main my nine d animated recent detail similar technique works ages range download skill whole set turn advance powerful scenario essential positive high progress later small included total room home handle full better stock  solution across skill among families permanent years other resources continue but place separate rotation front confidence turn progress benefit constant manageable value more pattern skill effective moment additional comfortable major shape standard play limited I clever yet age usage</p loading=',
        'replace': "fine-motor-busy-book-pages-for-toddlers-printable-best-resources-img4-1779274813.webp' alt='fine motor' loading="
    },
    'data/archive_posts/spot-the-difference-activities-sharpen-focus-in-6-year-olds-1777027975.json': {
        'search': 'how-spot-the-difference-activities-sharpen-focus-in-6-year-olds-various family sized comfort steady reading page . Glet→ simple clean session images loading=',
        'replace': "how-spot-the-difference-activities-sharpen-focus-in-6-year-olds-img5-1777027855.webp' alt='spot the difference' loading="
    },
    'data/archive_posts/stem-building-challenges-with-craft-sticks5-proven-mistakes-1780741220.json': {
        'search': 'stem-building-challenges-for-kids-using-craft-sticks-2-proven-mistakes-to-avoid-img2-1780740781.webp',
        'replace': 'stem-building-challenges-for-kids-using-craft-sticks-5-proven-mistakes-to-avoid-img2-1780740781.webp'
    },
    'data/archive_posts/stem-building-challenges-with-craft-sticks5-proven-mistakes-1780741220.json_2': {
        'file': 'data/archive_posts/stem-building-challenges-with-craft-sticks5-proven-mistakes-1780741220.json',
        'search': 'stem-building-challenges-for-kids-using-craft-sticks-4-proven-mistakes-to-avoid-img4-1780740781.webp',
        'replace': 'stem-building-challenges-for-kids-using-craft-sticks-5-proven-mistakes-to-avoid-img4-1780740781.webp'
    },
    'data/archive_posts/spot-the-difference-sharpens-kids-visual-processing-1779279079.json': {
        'search': 'how-spot-the-difference-activities-sharpen-visual-processing-in-kids-img4 changing change flexible low anyway',
        'replace': "how-spot-the-difference-activities-sharpen-visual-processing-in-kids-img4-1779278879.webp' alt='visual processing' loading="
    }
}

for key, action in files.items():
    file_path = action.get('file', key)
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    html = data['content_html']
    # If the search string isn't exactly as we think, let's find a fuzzy match using re
    if action['search'] not in html:
        print(f"[{file_path}] Exact string not found! Trying fallback...")
        if 'fine-motor' in key:
            import re
            html = re.sub(r'fine-motor-busy-book-pages-for-toddlers-printable-best-resources-img4-thumb.*?</p loading=', action['replace'], html, flags=re.DOTALL)
        elif 'spot-the-difference-activities-sharpen-focus' in key:
            import re
            html = re.sub(r'how-spot-the-difference-activities-sharpen-focus-in-6-year-olds-various.*?loading=', action['replace'], html, flags=re.DOTALL)
        elif 'visual-processing' in key:
            import re
            html = re.sub(r'how-spot-the-difference-activities-sharpen-visual-processing-in-kids-img4.*?anyway', action['replace'], html, flags=re.DOTALL)
    else:
        html = html.replace(action['search'], action['replace'])
        
    data['content_html'] = html
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    shutil.copy(file_path, 'posts/')
    html_path = 'articles/' + os.path.basename(file_path).split('-17')[0] + '.html'
    if os.path.exists(html_path): os.remove(html_path)

print('Done applying manual fixes')
