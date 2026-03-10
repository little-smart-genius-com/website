import re
import os
import subprocess
import sys

fp = 'articles/shadow-matching-sheets-for-toddlers-boost-cognitive-skills.html'
with open(fp, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('<!-- ═══ RELATED ARTICLES ═══ -->', '')
text = text.replace('<!-- ═══ TPT PRODUCT RECOMMENDATION & SCHEMA ═══ -->', '')
text = re.sub(r'<div class="related-articles".*?</div>\s*</div>\s*</div>', '', text, flags=re.DOTALL)

with open(fp, 'w', encoding='utf-8') as f:
    f.write(text)

print('Cleaned shadow-matching article.')
subprocess.run([sys.executable, 'scripts/_post_process.py'])
print('Done.')
