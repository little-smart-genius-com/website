import os
import glob
from bs4 import BeautifulSoup

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return

    soup = BeautifulSoup(content, 'html.parser')
    modified = False

    # 1. H1 Management: Keep first H1, change others to H2
    h1_tags = soup.find_all('h1')
    if len(h1_tags) > 1:
        for tag in h1_tags[1:]:
            tag.name = 'h2'
        modified = True
        print(f"[{os.path.basename(filepath)}] Changed {len(h1_tags)-1} extra H1 tags to H2.")

    # 2. Title length optimization (max 65 chars)
    title_tag = soup.find('title')
    if title_tag and title_tag.string:
        original_title = title_tag.string.strip()
        if len(original_title) > 65:
            # Truncate to 62 chars and add "..."
            new_title = original_title[:62].rsplit(' ', 1)[0] + "..."
            title_tag.string = new_title
            modified = True
            print(f"[{os.path.basename(filepath)}] Truncated title from {len(original_title)} to {len(new_title)} chars.")

    # 3. Dynamic Meta Description from first <p>
    first_p = soup.find('p')
    if first_p:
        text = first_p.get_text(strip=True)
        # Ensure it's not a tiny nav text
        if len(text) > 20: 
            # Trim/Pad to 110-155 characters
            if len(text) > 155:
                desc = text[:152].rsplit(' ', 1)[0] + "..."
            elif len(text) < 110:
                # If too short, just use it, or append generic text? 
                desc = text
            else:
                desc = text
            
            # Find existing meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                if meta_desc.get('content') != desc:
                    meta_desc['content'] = desc
                    modified = True
                    print(f"[{os.path.basename(filepath)}] Updated existing meta description.")
            else:
                # Create new meta description tag
                new_meta = soup.new_tag('meta', attrs={'name': 'description', 'content': desc})
                if soup.head:
                    soup.head.append(new_meta)
                    modified = True
                    print(f"[{os.path.basename(filepath)}] Added new meta description.")
                else:
                    print(f"[{os.path.basename(filepath)}] WARNING: No <head> tag found to inject meta description.")

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(soup))

if __name__ == '__main__':
    articles_dir = 'articles'
    html_files = glob.glob(os.path.join(articles_dir, '*.html'))
    root_html_files = glob.glob('*.html')
    
    # Exclude system/admin files
    excludes = ['admin.html', 'old_admin.html', '404.html']
    root_html_files = [f for f in root_html_files if os.path.basename(f) not in excludes]
    
    all_files = html_files + root_html_files
    print(f"Found {len(all_files)} articles and root files to process.")
    
    for file in all_files:
        process_file(file)
        
    print("SEO Ultime fix completed on all elements.")
