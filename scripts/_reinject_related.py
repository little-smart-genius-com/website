"""Strip old post-processor injections from all articles, then re-run _post_process.py.
This forces fresh injection with the corrected absolute paths."""
import os
import re
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")

html_files = sorted([
    os.path.join(ARTICLES_DIR, f)
    for f in os.listdir(ARTICLES_DIR) if f.endswith(".html")
])

print(f"Stripping old post-processor markers from {len(html_files)} articles...")

stripped = 0
for fp in html_files:
    with open(fp, "r", encoding="utf-8") as f:
        content = f.read()
    
    original = content
    
    # Strip RELATED ARTICLES section
    content = re.sub(
        r'\s*<!-- ═══ RELATED ARTICLES ═══ -->.*?(?=\s*<!-- ═══ TPT PRODUCT|\s*<div class="mt-16 pt-10 border-t"[^>]*>\s*<div class="rounded-2xl p-8 text-center"|\s*</main>|\s*<footer)',
        '',
        content,
        flags=re.DOTALL
    )
    
    # Strip TPT PRODUCT section  
    content = re.sub(
        r'\s*<!-- ═══ TPT PRODUCT RECOMMENDATION & SCHEMA ═══ -->.*?(?=\s*<div class="mt-16 pt-10 border-t"[^>]*>\s*<div class="rounded-2xl p-8 text-center"|\s*</main>|\s*<footer)',
        '',
        content,
        flags=re.DOTALL
    )
    
    if content != original:
        with open(fp, "w", encoding="utf-8") as f:
            f.write(content)
        stripped += 1

print(f"Stripped markers from {stripped} articles.")
print(f"\nRe-running _post_process.py with fixed paths...")

# Run the corrected post-processor
pp_script = os.path.join(SCRIPT_DIR, "_post_process.py")
subprocess.run([sys.executable, pp_script])
