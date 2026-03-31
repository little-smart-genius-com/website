"""
T5, T7, T10 FIX SCRIPT
Applies fixes to build_articles.py for SEO Alt text, Twitter Cards, and Favicon.
"""
import re
import os
import urllib.request

SCRIPT_DIR = r"c:\Users\Omar\Desktop\little-smart-genius-site\Nouveau dossier\online\Little_Smart_Genius\scripts"
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# 1. Favicon (T10)
favicon_url = "https://ecdn.teacherspayteachers.com/thumbuserhome/Little-Smart-Genius-1746813476/23416711.jpg"
favicon_path = os.path.join(PROJECT_ROOT, "favicon.ico")
try:
    urllib.request.urlretrieve(favicon_url, favicon_path)
    print(f"✅ T10: Favicon saved to {favicon_path}")
except Exception as e:
    print(f"❌ Failed to download favicon: {e}")

# 2. Patch build_articles.py
path = os.path.join(SCRIPT_DIR, "build_articles.py")
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

changes = 0

# T7: Twitter Cards
twitter_tags = """    <!-- Open Graph -->
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{excerpt}">
    <meta property="og:image" content="{og_image}">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:type" content="article">
    <meta property="article:published_time" content="{iso_date}">
    <meta property="article:author" content="{author_name}">

    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{excerpt}">
    <meta name="twitter:image" content="{og_image}">"""

old_og = """    <!-- Open Graph -->
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{excerpt}">
    <meta property="og:image" content="{og_image}">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:type" content="article">
    <meta property="article:published_time" content="{iso_date}">
    <meta property="article:author" content="{author_name}">"""

if old_og in content and "twitter:card" not in content:
    content = content.replace(old_og, twitter_tags)
    changes += 1
    print("✅ T7: Added Twitter Cards to ARTICLE_TEMPLATE")


# T5: Clean Alt text logic
old_def = "def fix_image_paths(content: str) -> str:"
new_def = "def fix_image_paths(content: str, article_title: str = \"\") -> str:"
if old_def in content:
    content = content.replace(old_def, new_def)
    changes += 1
    print("✅ T5: Updated fix_image_paths signature")

# Inject alt fix into enhance_img
old_enhance = """        # Assume it's an auto-generated body image without dimensions
        if "data:image/svg+xml" in img_tag:
            return img_tag"""
new_enhance = """        # Assume it's an auto-generated body image without dimensions
        if "data:image/svg+xml" in img_tag:
            return img_tag
            
        alt_match = re.search(r'alt="([^"]+)"', img_tag)
        if alt_match:
            alt_text = alt_match.group(1)
            # If it's a long AI prompt or empty
            if len(alt_text) > 80 or any(x in alt_text.lower() for x in ['pristine', 'cgi', 'render', 'illustration', '8k']):
                clean_alt = f"{article_title} illustration" if article_title else "Educational illustration"
                img_tag = img_tag.replace(f'alt="{alt_text}"', f'alt="{clean_alt}"')"""

if old_enhance in content and "alt_match =" not in content:
    content = content.replace(old_enhance, new_enhance)
    changes += 1
    print("✅ T5: Added Alt text cleanup logic in enhance_img")

# Update caller
# Looking for: content = fix_image_paths(content)
# We want to replace carefully because there could be multiple instances.
# In generate_article_html, we want: content = fix_image_paths(content, post.get('title', ''))

caller_target = "    content = fix_image_paths(content)"
caller_replacement = "    content = fix_image_paths(content, post.get('title', ''))"

count = content.count(caller_target)
if count > 0:
    content = content.replace(caller_target, caller_replacement)
    changes += count
    print(f"✅ T5: Updated caller of fix_image_paths ({count} occurrences)")


if changes > 0:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved {changes} changes to build_articles.py")
else:
    print("No changes needed or matching failed.")
