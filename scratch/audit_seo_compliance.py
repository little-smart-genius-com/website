import json
import glob
import re

def audit():
    files = glob.glob("data/archive_posts/*.json") + glob.glob("data/pending_posts/*.json")
    
    report = {
        "short_title": [],
        "long_title": [],
        "missing_excerpt": [],
        "short_excerpt": [],
        "long_excerpt": [],
        "no_images": [],
        "missing_alt": []
    }
    
    total = len(files)
    
    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                continue
                
        title = data.get("title", "")
        excerpt = data.get("excerpt", "")
        content = data.get("content", "")
        
        # 1. Title Length (SEO best practice: 40-70 chars)
        if len(title) < 30:
            report["short_title"].append(filepath)
        elif len(title) > 80:
            report["long_title"].append(filepath)
            
        # 2. Excerpt / Meta Description (SEO best practice: 120-160 chars)
        if not excerpt:
            report["missing_excerpt"].append(filepath)
        elif len(excerpt) < 50:
            report["short_excerpt"].append(filepath)
        elif len(excerpt) > 180:
            report["long_excerpt"].append(filepath)
            
        # 3. Image Count (at least 1 in content)
        img_tags = re.findall(r'<img[^>]+>', content)
        if len(img_tags) == 0:
            report["no_images"].append(filepath)
            
        # 4. Missing ALT text
        missing_alt = False
        for img in img_tags:
            if 'alt=""' in img or 'alt=' not in img:
                missing_alt = True
                
        if missing_alt:
            report["missing_alt"].append(filepath)
            
    print("=== SEO & COMPLIANCE AUDIT ===")
    print(f"Total articles audited: {total}")
    print(f"Short Titles (<30 chars): {len(report['short_title'])}")
    print(f"Long Titles (>80 chars): {len(report['long_title'])}")
    print(f"Missing Excerpts: {len(report['missing_excerpt'])}")
    print(f"Short Excerpts (<50 chars): {len(report['short_excerpt'])}")
    print(f"Long Excerpts (>180 chars): {len(report['long_excerpt'])}")
    print(f"Articles with NO images in content: {len(report['no_images'])}")
    print(f"Images missing ALT text: {len(report['missing_alt'])}")
    
if __name__ == "__main__":
    audit()
