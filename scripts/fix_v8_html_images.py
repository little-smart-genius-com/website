import os
import glob
import re

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    articles_dir = os.path.join(base_dir, "articles")
    images_dir = os.path.join(base_dir, "images")
    
    html_files = glob.glob(os.path.join(articles_dir, "*.html"))
    
    # We also need to map slugs to their V8 images
    v8_images = {}
    for img_path in glob.glob(os.path.join(images_dir, "*-img*-*.webp")):
        img_name = os.path.basename(img_path)
        m = re.match(r"(.*)-img([1-5])-\d+\.webp", img_name)
        if m:
            slug = m.group(1)
            idx = int(m.group(2))
            if slug not in v8_images:
                v8_images[slug] = {}
            v8_images[slug][idx] = img_name

    fixed_count = 0

    for fp in html_files:
        slug = os.path.basename(fp).replace(".html", "")
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()

        slug_imgs = v8_images.get(slug, {})
        
        # In files that have naked <img ...> tags for inline images, we want to replace them too.
        # But we only want to replace inline images, not the cover. The cover has fetchpriority="high".
        # Let's find all <img src="../images/..." > that DO NOT have fetchpriority="high"
        # and are NOT inside an <a> tag pointing to related articles.
        # Wait, the inline images have loading='lazy' width='1200' height='675'
        
        # Regex to find naked inline images that weren't wrapped in the <figure> div block
        # We look for <img src='../images/[^']*' ...> or src="../images/[^"]*" which contains "loading" and doesn't contain "fetchpriority"
        
        matches = list(re.finditer(r'<img\s+src=[\'"]\.\./images/[^\'"]+[\'"][^>]+>', content))
        
        if not matches:
            continue
            
        new_content = ""
        last_end = 0
        img_counter = 1
        replaced_num = 0
        
        for match in matches:
            tag = match.group(0)
            
            # Skip cover images
            if 'fetchpriority="high"' in tag:
                new_content += content[last_end:match.end()]
                last_end = match.end()
                continue
                
            # Skip related article thumbs (they match .../thumbs/...)
            if '/thumbs/' in tag:
                new_content += content[last_end:match.end()]
                last_end = match.end()
                continue
                
            # This is an inline image!
            if img_counter > 5:
                # keep as is or delete?
                new_content += content[last_end:match.start()]
                last_end = match.end()
                continue
                
            new_img_fn = slug_imgs.get(img_counter)
            if not new_img_fn:
                new_content += content[last_end:match.end()]
                last_end = match.end()
                img_counter += 1
                continue
                
            new_figure = (
                f"<div style=\"margin: 2.5rem 0;\">"
                f"<figure class='my-8'><img src='../images/{new_img_fn}' alt='{slug}-img{img_counter}' "
                f"loading='lazy' width='1200' height='675' class='w-full rounded-xl shadow-md' "
                f"style=\"background: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy5wMy5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9IiNlMmU4ZjAiLz48L3N2Zz4=') center/cover; background-color: var(--bord);\"></figure>"
                f"</div>"
            )
            
            # Since the original tag might be wrapped in <p> or just naked, replacing it with a block-level div
            # is absolutely fine in HTML5.
            new_content += content[last_end:match.start()] + new_figure
            last_end = match.end()
            img_counter += 1
            replaced_num += 1
            
        new_content += content[last_end:]

        if content != new_content:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(new_content)
            fixed_count += 1
            print(f"Fixed {replaced_num} naked images for {slug}")

    print(f"Done. Fixed {fixed_count} HTML files.")

if __name__ == "__main__":
    main()
