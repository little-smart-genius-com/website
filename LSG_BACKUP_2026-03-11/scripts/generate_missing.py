import sys, os, asyncio
sys.path.insert(0, r'c:\Users\Omar\Desktop\little-smart-genius-site\Nouveau dossier\online\Little_Smart_Genius\scripts')
os.chdir(r'c:\Users\Omar\Desktop\little-smart-genius-site\Nouveau dossier\online\Little_Smart_Genius\scripts')

from topic_selector import TopicSelector
from auto_blog_v6_ultimate import generate_article_v6

def main():
    ts = TopicSelector()
    
    # Check how many are missing
    import json
    article_path = r'c:\Users\Omar\Desktop\little-smart-genius-site\Nouveau dossier\online\Little_Smart_Genius\articles.json'
    with open(article_path, 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    from collections import Counter
    slots = Counter(a.get('slot', 'unknown') for a in articles.get('articles', []))
    
    products_needed = 8 - slots.get('product', 0)
    keywords_needed = 8 - slots.get('keyword', 0)
    freebies_needed = 8 - slots.get('freebie', 0)
    
    print(f"Current slots: {dict(slots)}")
    print(f"Needed -> Products: {products_needed}, Keywords: {keywords_needed}, Freebies: {freebies_needed}")
    
    def generate_missing(slot_type, needed):
        print(f"\n--- GENERATING {needed} MISSING {slot_type.upper()} ARTICLES ---")
        for i in range(needed):
            print(f">>> Generating {slot_type} Article {i+1}/{needed} <<<")
            topic = ts.get_next_topic(slot_type)
            if not topic:
                print(f"No more {slot_type} topics available!")
                break
            
            result = generate_article_v6(slot_type, topic, ts)
            if result:
                print(f"Successfully generated: {result.get('title', '')}")
            else:
                print("Failed to generate article")

    if products_needed > 0: generate_missing('product', products_needed)
    if keywords_needed > 0: generate_missing('keyword', keywords_needed)
    if freebies_needed > 0: generate_missing('freebie', freebies_needed)
    
    print("DONE generating missing articles.")

if __name__ == '__main__':
    main()
