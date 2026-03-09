import os
import json
import glob
import re
from datetime import datetime

base_dir = r'C:\Users\Omar\Desktop\little-smart-genius-site\Nouveau dossier\online\Little_Smart_Genius'
backup_dir = r'C:\Users\Omar\Desktop\tmp_archive_posts'

# 1. Rebuild articles.json
all_articles = []
for file_path in glob.glob(os.path.join(backup_dir, '*.json')):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            article = json.load(f)
            if 'title' in article and 'slot' in article:
                all_articles.append(article)
    except Exception as e:
        print(f"Skipping {file_path}: {e}")

# Group and sort by timestamp (newest first)
def get_ts(a):
    try:
        d = a.get('iso_date')
        if d:
            return datetime.fromisoformat(d).timestamp()
    except:
        pass
    return 0

slots = {'product': [], 'keyword': [], 'freebie': []}
for a in all_articles:
    slot = a.get('slot')
    if slot in slots:
        slots[slot].append(a)

final_list = []
for s in slots:
    slots[s].sort(key=get_ts, reverse=True)
    # Take exactly newest 8
    slots[s] = slots[s][:8]
    final_list.extend(slots[s])

articles_db = {
    "generated_at": datetime.utcnow().isoformat(),
    "total_articles": len(final_list),
    "articles": final_list
}
with open(os.path.join(base_dir, 'articles.json'), 'w', encoding='utf-8') as f:
    json.dump(articles_db, f, indent=4)
print(f"Rebuilt articles.json with {len(final_list)} articles.")

# 2. Rebuild used_topics.json
used_topics = {"keyword": [], "product": [], "freebie": [], "daily_log": []}
for a in final_list:
    used_topics[a['slot']].append(a['title'])
    # Optional: could also build daily_log entries, but let's just make it simple
    used_topics["daily_log"].append({
        "slot": a['slot'],
        "topic": a['title'],
        "date": a.get("iso_date", datetime.utcnow().isoformat())
    })

with open(os.path.join(base_dir, 'data', 'used_topics.json'), 'w', encoding='utf-8') as f:
    json.dump(used_topics, f, indent=4)
print("Rebuilt used_topics.json.")

# 3. Clean instagram/posted_log.json using regex
posted_log_path = os.path.join(base_dir, 'instagram', 'posted_log.json')
try:
    with open(posted_log_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Extract valid entries out of the corrupted JSON text
    # Pattern looks for: "key": {"posted_at": float, "posted_at_human": string, "delete_after": string}
    pattern = r'"([a-z0-9-]+)":\s*\{\s*"posted_at":\s*([\d\.]+),\s*"posted_at_human":\s*"([^"]+)",\s*"delete_after":\s*"([^"]+)"\s*\}'
    matches = re.finditer(pattern, text)
    
    clean_log = {}
    for match in matches:
        key = match.group(1)
        clean_log[key] = {
            "posted_at": float(match.group(2)),
            "posted_at_human": match.group(3),
            "delete_after": match.group(4)
        }
        
    with open(posted_log_path, 'w', encoding='utf-8') as f:
        json.dump(clean_log, f, indent=2)
    print(f"Cleaned posted_log.json. Recovered {len(clean_log)} entries.")
except Exception as e:
    print(f"Failed to clean posted_log.json: {e}")
