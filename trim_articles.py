import json
import os

article_path = r'c:\Users\Omar\Desktop\little-smart-genius-site\Nouveau dossier\online\Little_Smart_Genius\articles.json'
with open(article_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Group by slot
slots = {'freebie': [], 'product': [], 'keyword': []}
for a in data.get('articles', []):
    slot = a.get('slot')
    if slot in slots:
        slots[slot].append(a)
    else:
        # Keep unknown slots as is? Or just ignore
        pass

# Ensure we have EXACTLY 8 for each slot, taking the newest ones (which are at the end, or sort by id which ends in timestamp)
def sort_by_timestamp(article):
    # Extract timestamp from id, e.g., 'how-spot-the-difference-puzzles-build-focus-1773062023'
    id_str = article.get('id', '')
    parts = id_str.split('-')
    if parts and parts[-1].isdigit():
        return int(parts[-1])
    return 0

for s in slots:
    slots[s].sort(key=sort_by_timestamp, reverse=True)
    # limit to 8
    slots[s] = slots[s][:8]

# Recombine
final_articles = []
for s in ['product', 'freebie', 'keyword']:
    final_articles.extend(slots[s])

data['articles'] = final_articles

with open(article_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4)

print(f"Total articles now: {len(data['articles'])}")
for s in ['product', 'freebie', 'keyword']:
    print(f"{s}: {len(slots[s])}")
