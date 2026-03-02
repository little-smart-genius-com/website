import os
import glob
import re

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    articles_dir = os.path.join(base_dir, "articles")
    images_dir = os.path.join(base_dir, "images")
    
    html_files = glob.glob(os.path.join(articles_dir, "*.html"))
    
    # Map slugs to their V8 cover images
    v8_covers = {}
    for img_path in glob.glob(os.path.join(images_dir, "*-cover-*.webp")):
        img_name = os.path.basename(img_path)
        # e.g best-printable-logic-puzzles-for-kids-6-10-cover-1772427658.webp
        m = re.match(r"(.*)-cover-\d+\.webp", img_name)
        if m:
            slug = m.group(1)
            v8_covers[slug] = img_name

    fixed_count = 0

    for fp in html_files:
        slug = os.path.basename(fp).replace(".html", "")
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()

        cover_fn = v8_covers.get(slug)
        if not cover_fn:
            continue
            
        thumb_fn = cover_fn # Same naming in thumbs folder
        
        # The cover image is inside a rounded-2xl div
        # We can find the <img ... fetchpriority="high" ... > tag and replace its src and srcset directly
        
        # Regex to find the <img ...> tag that has fetchpriority="high"
        # We will extract the full tag, replace src=..., replace srcset=..., then substitute back
        
        def replacer(match):
            tag = match.group(0)
            tag = re.sub(r'src="[^"]+"', f'src="../images/{cover_fn}"', tag)
            tag = re.sub(r'src=\'[^\']+\'', f'src="../images/{cover_fn}"', tag)
            tag = re.sub(r'srcset="[^"]+"', f'srcset="../images/thumbs/{thumb_fn} 480w, ../images/{cover_fn} 1200w"', tag)
            tag = re.sub(r'srcset=\'[^\']+\'', f'srcset="../images/thumbs/{thumb_fn} 480w, ../images/{cover_fn} 1200w"', tag)
            return tag
            
        new_content = re.sub(r'<img[^>]+fetchpriority="high"[^>]+>', replacer, content)
        
        # Fix any placeholder.webp references remaining anywhere in the file (just replace with cover)
        new_content = new_content.replace("../images/placeholder.webp", f"../images/{cover_fn}")

        if content != new_content:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(new_content)
            fixed_count += 1
            print(f"Fixed cover image for {slug}")

    print(f"Done. Fixed {fixed_count} HTML covers.")

if __name__ == "__main__":
    main()
