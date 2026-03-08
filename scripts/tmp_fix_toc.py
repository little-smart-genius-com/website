import os
import glob
import re

ARTICLE_DIR = r"c:\Users\Omar\Desktop\little-smart-genius-site\Nouveau dossier\online\Little_Smart_Genius\articles"

files = glob.glob(os.path.join(ARTICLE_DIR, "*.html"))
count = 0

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    # The corrupted emoji looks like ðŸ“‘ or similar. We look for the Table of Contents header span.
    # It might be <span>ðŸ“‘</span> or something else before Table of Contents.
    # Let's match any span inside the h3 of toc-container.
    # Easiest way is to do a direct replace of the known corrupted lines.
    
    # We can also just replace the entire h3 if it contains "Table of Contents".
    # Pattern: <span>.*?</span> Table of Contents
    old_content = content
    content = re.sub(
        r'<span>[^<]*</span>\s*Table of Contents',
        r'<span>&#128209;</span> Table of Contents',
        content,
        flags=re.IGNORECASE
    )
    
    if content != old_content:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        count += 1

print(f"Fixed Table of Contents emoji in {count} HTML articles.")
