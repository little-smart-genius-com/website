import json, glob, os, re

# This script cleans up duplicate sections embedded directly in the post JSON contents.
# This prevents the blog builder from rendering them twice (since build_articles.py also appends them).

def clean_html(content):
    original = content
    
    # 1. Remove hardcoded CTA boxes (e.g. "Love Learning Activities?")
    content = re.sub(r'<div class="cta-box".*?</div>\s*</div>', '', content, flags=re.DOTALL)
    
    # 2. Remove hardcoded FAQ sections (class="faq-section")
    content = re.sub(r'<div class="faq-section[^>]*>.*?</div>\s*</div>', '', content, flags=re.DOTALL)
    
    # 3. Remove raw HTML FAQ sections that don't use the div container
    # Matches <h2> or <h3> Frequently Asked Questions or FAQ followed by various question/answer formats
    content = re.sub(
        r'<h[23]>(?:Frequently Asked Questions(?:\s*\(FAQ\))?|FAQ)</h[23]>(?:\s*<h3>.*?</h3>\s*<p>.*?</p>)+', 
        '', 
        content, 
        flags=re.DOTALL | re.IGNORECASE
    )
    
    # Matches 'Q:' and 'A:' paragraph style or <strong>...</strong><br> style
    content = re.sub(
        r'<h[23]>(?:Frequently Asked Questions(?:\s*\(FAQ\))?|FAQ)</h[23]>(?:\s*<p><strong>.*?</strong><br>\s*.*?</p>)+',
        '',
        content,
        flags=re.DOTALL | re.IGNORECASE
    )
    
    # 3.5 Remove Markdown format FAQ sections
    content = re.sub(
        r'(?:###?|##)\s*(?:FAQ|Frequently Asked Questions)[\s\S]*?(?=(?:##|<p><em>According to)|$)',
        '',
        content,
        flags=re.IGNORECASE
    )
    
    # 4. Remove standalone <h2>Frequently Asked Questions (FAQ)</h2> if left behind
    content = re.sub(r'<h2>Frequently Asked Questions(?:\s*\(FAQ\))?</h2>', '', content, flags=re.IGNORECASE)

    # 5. Remove 'You Might Also Like' or 'You May Also Like' blocks embedded in content
    # Matches from the related <h3> until the next <h2>, EOF, or another specific block
    content = re.sub(
        r'<h3[^>]*>You M(?:ight|ay) Also Like</h3>.*?(?=<h2>|$)', 
        '', 
        content, 
        flags=re.DOTALL | re.IGNORECASE
    )

    return content.strip(), (original != content.strip())

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    posts_dir = os.path.join(project_root, 'posts')
    
    count = 0
    for file_path in glob.glob(os.path.join(posts_dir, '*.json')):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        old_content = data.get('content', '')
        new_content, changed = clean_html(old_content)
        
        if changed:
            data['content'] = new_content
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Cleaned: {os.path.basename(file_path)}")
            count += 1
            
    print(f"Total files cleaned: {count}")

if __name__ == "__main__":
    main()
