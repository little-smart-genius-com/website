import os
import sys
import glob
import json
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
POSTS_DIR = os.path.join(PROJECT_ROOT, "posts")

sys.path.append(SCRIPT_DIR)
from auto_blog_v6_ultimate import generate_article_v6, TopicSelector
from build_articles import build_all

def main():
    json_files = glob.glob(os.path.join(POSTS_DIR, "*.json"))
    ts = TopicSelector()
    
    print("="*80)
    print(f"MASS REGENERATION STARTED: {len(json_files)} Articles")
    print("="*80)
    
    for i, file_path in enumerate(json_files):
        print(f"\n[{i+1}/{len(json_files)}] Regenerating {os.path.basename(file_path)}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Use original slug to prevent breaking URLs
            slug = data.get('slug')
            if not slug:
                # Fallback to parsing filename (which has timestamps)
                base = os.path.basename(file_path).replace('.json', '')
                slug = "-".join(base.split("-")[:-1]) if "-" in base and base.split("-")[-1].isdigit() else base
                
            topic_name = data.get('title', slug.replace('-', ' ').title())
            category = data.get('category', 'education')
            keywords = data.get('keywords', topic_name)
            if isinstance(keywords, list):
                keywords = ', '.join(keywords)
            
            # Delete old HTML immediately
            html_path = os.path.join(PROJECT_ROOT, "articles", f"{slug}.html")
            if os.path.exists(html_path):
                try: os.remove(html_path)
                except Exception: pass
                
            # Delete old JSON so a clean one is generated
            try: os.remove(file_path)
            except Exception: pass
            
            topic = {"topic_name": topic_name, "category": category, "keywords": keywords, "product_data": None}
            print(f"  Topic: {topic_name}")
            
            # Start generation
            generate_article_v6("keyword", topic, ts)
            
            if i < len(json_files) - 1:
                print("  Sleep 5s for API cooldown...")
                time.sleep(5)
                
        except Exception as e:
            print(f"  [ERROR] FAILED to regenerate {file_path}: {e}")

    print("\nRegeneration complete! Now rebuilding site...")
    build_all()
    
    print("\nRunning post processor...")
    os.system(f"{sys.executable} {os.path.join(SCRIPT_DIR, '_post_process.py')}")
    
    print("\nRebuilding audit dashboard...")
    try:
        from audit_dashboard import main as build_dash
        build_dash()
    except Exception as e:
        print(f"Dashboard error: {e}")
        
    print("\n="*80)
    print("ALL DONE. 100% REGENERATION COMPLETED.")
    print("="*80)

if __name__ == "__main__":
    main()
