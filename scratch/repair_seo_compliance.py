import json
import glob
import re

def repair():
    files = glob.glob("data/archive_posts/*.json") + glob.glob("data/pending_posts/*.json")
    
    fixed_excerpts = 0
    fixed_no_images = 0
    fixed_alts = 0
    
    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                continue
                
        title = data.get("title", "")
        excerpt = data.get("excerpt", "")
        content = data.get("content", "")
        cover_image = data.get("image", "")
        needs_save = False
        
        # 1. Fix Long Excerpt
        if len(excerpt) > 180:
            # Truncate to ~155 chars
            short_excerpt = excerpt[:155]
            # Find the last space to not break a word
            last_space = short_excerpt.rfind(' ')
            if last_space > 0:
                short_excerpt = short_excerpt[:last_space]
            data["excerpt"] = short_excerpt + "..."
            needs_save = True
            fixed_excerpts += 1
            
        # 2. Fix No Images
        img_tags = re.findall(r'<img[^>]+>', content)
        if len(img_tags) == 0:
            if cover_image:
                img_html = f'<img src="{cover_image}" alt="{title}" class="w-full h-auto rounded-lg shadow-md my-8" />'
                # Insert at the beginning of the content or after the first paragraph
                first_p_end = content.find('</p>')
                if first_p_end != -1:
                    content = content[:first_p_end+4] + img_html + content[first_p_end+4:]
                else:
                    content = img_html + content
                data["content"] = content
                needs_save = True
                fixed_no_images += 1
                
        # 3. Fix Missing ALT text
        # Since content might have changed, refetch img tags
        img_tags = re.findall(r'<img[^>]+>', content)
        new_content = content
        for img in img_tags:
            if 'alt=""' in img:
                new_img = img.replace('alt=""', f'alt="{title}"')
                new_content = new_content.replace(img, new_img)
                fixed_alts += 1
                needs_save = True
            elif 'alt=' not in img:
                # Insert alt before class or src or at the end
                if 'class="' in img:
                    new_img = img.replace('class="', f'alt="{title}" class="')
                else:
                    new_img = img.replace('/>', f'alt="{title}" />').replace('>', f' alt="{title}">')
                new_content = new_content.replace(img, new_img)
                fixed_alts += 1
                needs_save = True
                
        if needs_save:
            data["content"] = new_content
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                
    print("=== SEO & COMPLIANCE REPAIR ===")
    print(f"Fixed Long Excerpts: {fixed_excerpts}")
    print(f"Fixed Articles with NO images: {fixed_no_images}")
    print(f"Fixed Images missing ALT text: {fixed_alts}")
    
if __name__ == "__main__":
    repair()
