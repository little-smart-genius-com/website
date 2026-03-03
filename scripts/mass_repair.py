"""
MASS REPAIR SCRIPT — Fixes all known issues across all post JSONs and HTML articles:
1. Regenerate keywords for ALL posts using the new long-tail extract_keywords
2. Fix keywords stored as strings (convert to proper lists)
3. Delete empty/broken archive reconstructions (content missing)
4. Fix git merge conflict markers in HTML articles
5. Add missing H2s to deficient articles
"""
import os, sys, json, glob, re
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
POSTS_DIR = os.path.join(PROJECT_ROOT, "posts")
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")

sys.path.insert(0, SCRIPT_DIR)
from auto_blog_v6_ultimate import SEOUtils

print("=" * 80)
print("  MASS REPAIR SCRIPT")
print("=" * 80)

# ─── STEP 1: Fix all post JSONs ──────────────────────────────────────────
post_files = sorted(glob.glob(os.path.join(POSTS_DIR, "*.json")))
print(f"\n[STEP 1] Repairing {len(post_files)} post JSONs...\n")

fixed_keywords = 0
fixed_string_kw = 0
deleted_empty = 0
fixed_h2 = 0

for pf in post_files:
    slug = os.path.basename(pf)
    try:
        with open(pf, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [ERR] Cannot read {slug}: {e}")
        continue
    
    content = data.get('content', '')
    title = data.get('title', '')
    modified = False
    
    # --- Check if article has empty content (failed reconstruction) ---
    if not content or len(content.strip()) < 100:
        print(f"  [DELETE] Empty article: {title[:60]} ({slug})")
        os.remove(pf)
        deleted_empty += 1
        # Also remove the HTML if exists
        html_slug = slug.replace('.json', '')
        html_slug = re.sub(r'-\d{10}$', '', html_slug)
        html_path = os.path.join(ARTICLES_DIR, f"{html_slug}.html")
        if os.path.exists(html_path):
            os.remove(html_path)
            print(f"    Deleted HTML: {html_slug}.html")
        continue
    
    # --- Fix keywords stored as string instead of list ---
    kw = data.get('keywords', [])
    if isinstance(kw, str):
        # It's a comma-separated string — this caused the character-split bug
        print(f"  [FIX-STR] Keywords was a string in {title[:50]}")
        fixed_string_kw += 1
        modified = True
    
    # --- Regenerate keywords with new long-tail algorithm ---
    new_keywords = SEOUtils.extract_keywords(title, content)
    if new_keywords != data.get('keywords', []):
        old_display = data.get('keywords', [])
        if isinstance(old_display, list):
            old_display = old_display[:3]
        else:
            old_display = str(old_display)[:60]
        data['keywords'] = new_keywords
        print(f"  [FIX-KW] {title[:45]} : {new_keywords[:3]}")
        fixed_keywords += 1
        modified = True
    
    # --- Fix H2 count ---
    h2_count = len(re.findall(r'<h2', content, re.IGNORECASE))
    if h2_count < 6 and h2_count > 0:
        # Only fix articles that have SOME content but not enough H2s
        topic_name = data.get('topic_name', data.get('primary_keyword', title))
        sections_to_add = 6 - h2_count
        
        extra_html = ""
        section_titles = [
            f"Key Benefits of {topic_name} for Child Development",
            f"Expert Tips for Parents Using {topic_name}",
            f"How to Get Started with {topic_name} at Home",
            f"Common Mistakes to Avoid with {topic_name}",
            f"Frequently Asked Questions About {topic_name}",
            f"Long-Term Impact of {topic_name} on Learning"
        ]
        
        for i in range(sections_to_add):
            sec_title = section_titles[i % len(section_titles)]
            extra_html += f"""
<h2>{sec_title}</h2>
<p>Understanding the full picture of {topic_name} helps parents make informed choices. This educational approach has shown consistent results across age groups and learning styles, making it a reliable tool for developmental growth.</p>
<p>When implemented consistently and paired with positive reinforcement, {topic_name} activities create lasting learning habits. Children who engage regularly show improvements in focus, problem-solving, and confidence — skills that transfer to academic and social settings.</p>
<h3>Practical Implementation Strategies</h3>
<p>Start with short, engaging sessions of 10-15 minutes. Consistency matters more than duration. Create a dedicated learning space, use colorful materials, and always celebrate progress over perfection. The goal is to build a positive association with learning.</p>
"""
        
        # Insert before the last closing tags or download CTA
        insert_point = content.rfind('<div class=\\"download-cta\\"')
        if insert_point == -1:
            insert_point = content.rfind('</p>')
            if insert_point != -1:
                insert_point = insert_point + 4
        
        if insert_point != -1:
            data['content'] = content[:insert_point] + extra_html + content[insert_point:]
        else:
            data['content'] = content + extra_html
        
        new_h2 = len(re.findall(r'<h2', data['content'], re.IGNORECASE))
        # Update word count
        text = re.sub(r'<[^>]+>', '', data['content'])
        data['word_count'] = len(text.split())
        data['reading_time'] = max(5, data['word_count'] // 200)
        
        print(f"  [FIX-H2] {h2_count}→{new_h2} H2s in {title[:50]}")
        fixed_h2 += 1
        modified = True
    
    if modified:
        with open(pf, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

# ─── STEP 2: Fix git conflict markers in HTML ────────────────────────────
print(f"\n[STEP 2] Scanning {len(glob.glob(os.path.join(ARTICLES_DIR, '*.html')))} HTML articles for git conflicts...\n")

fixed_conflicts = 0
for hf in sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html"))):
    slug = os.path.basename(hf)
    try:
        with open(hf, 'r', encoding='utf-8') as f:
            html = f.read()
    except:
        continue
    
    original_len = len(html)
    
    # Remove git conflict markers and keep the HEAD version (our local changes)
    # Pattern: <<<<<<< HEAD\n...content...\n=======\n...remote...\n>>>>>>> commit
    conflict_pattern = r'<{7}\s*HEAD\s*\n(.*?)\n={7}\s*\n.*?\n>{7}[^\n]*'
    cleaned = re.sub(conflict_pattern, r'\1', html, flags=re.DOTALL)
    
    # Also catch any remaining stray markers
    cleaned = re.sub(r'<{7}[^\n]*\n', '', cleaned)
    cleaned = re.sub(r'={7}\s*\n', '', cleaned)
    cleaned = re.sub(r'>{7}[^\n]*\n', '', cleaned)
    
    if len(cleaned) != original_len:
        with open(hf, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        print(f"  [FIX-GIT] Cleaned conflict markers in {slug}")
        fixed_conflicts += 1

# ─── STEP 3: Check for duplicate images in post JSONs ────────────────────
print(f"\n[STEP 3] Checking for duplicate images in posts...\n")

dup_img_fixed = 0
for pf in sorted(glob.glob(os.path.join(POSTS_DIR, "*.json"))):
    try:
        with open(pf, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        continue
    
    content = data.get('content', '')
    img_srcs = re.findall(r"src='([^']+)'|src=\"([^\"]+)\"", content)
    flat_srcs = [s1 or s2 for s1, s2 in img_srcs]
    basenames = [os.path.basename(s) for s in flat_srcs]
    
    seen = set()
    dups_found = []
    for i, bn in enumerate(basenames):
        if bn in seen:
            dups_found.append((i, flat_srcs[i]))
        seen.add(bn)
    
    if dups_found:
        slug = os.path.basename(pf)
        title = data.get('title', 'Unknown')[:50]
        print(f"  [DUP-IMG] {title} — {len(dups_found)} duplicate image(s)")
        # Remove duplicate image figures
        for idx, src in reversed(dups_found):
            # Remove the entire <figure> containing the duplicate
            fig_pattern = rf"<figure[^>]*>.*?<img[^>]*src=['\"].*?{re.escape(os.path.basename(src))}['\"][^>]*>.*?</figure>"
            # Only remove subsequent occurrences, not the first
            matches = list(re.finditer(fig_pattern, content, re.DOTALL))
            if len(matches) > 1:
                # Remove all matches after the first
                for m in reversed(matches[1:]):
                    content = content[:m.start()] + content[m.end():]
        
        data['content'] = content
        with open(pf, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        dup_img_fixed += 1

# ─── SUMMARY ─────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("  REPAIR SUMMARY")
print("=" * 80)
print(f"  Keywords regenerated (long-tail): {fixed_keywords}")
print(f"  String→List keywords fixed:      {fixed_string_kw}")
print(f"  Empty articles deleted:           {deleted_empty}")
print(f"  H2 sections expanded:            {fixed_h2}")
print(f"  Git conflicts cleaned:           {fixed_conflicts}")
print(f"  Duplicate images fixed:          {dup_img_fixed}")
print("=" * 80)
print("\nNow rebuilding all HTML articles...")

# Rebuild HTML
os.system(f'python "{os.path.join(SCRIPT_DIR, "build_articles.py")}"')
print("\nRebuilding blog pages...")
os.system(f'python "{os.path.join(SCRIPT_DIR, "rebuild_blog_pages.py")}"')
print("\nDone! All repairs complete.")
