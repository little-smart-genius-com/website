import os
import json
import re
import requests
import time
from urllib.parse import quote
from dotenv import load_dotenv

os.chdir(r'c:\Users\Omar\Desktop\little-smart-genius-site\Nouveau dossier\online\Little_Smart_Genius')
load_dotenv('.env')

keys = []
for k, v in os.environ.items():
    if k.startswith("POLLINATIONS_API_KEY") and v and len(v) > 5:
        keys.append(v)
api_key = None
for key in keys:
    balance_url = "https://gen.pollinations.ai/account/balance"
    try:
        res = requests.get(balance_url, headers={"Authorization": f"Bearer {key}"}, timeout=10)
        if res.status_code == 200 and res.json().get("balance", 0) > 0:
            api_key = key
            break
    except Exception:
        continue

headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

post_file = r'posts\best-age-appropriate-painting-activities-for-preschoolers-1773223882.json'
with open(post_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

slug = data['slug']
content = data['content']
timestamp = str(int(time.time()))

def generate_image(prompt, filename):
    safe_prompt = quote(prompt)
    url = f"https://gen.pollinations.ai/image/{safe_prompt}?model=flux&width=1200&height=675&nologo=true"
    print(f"Generating image for prompt: {prompt[:50]}...")
    try:
        res = requests.get(url, headers=headers, timeout=30)
        if res.status_code == 200 and len(res.content) > 1024:
            with open(os.path.join('images', filename), "wb") as f:
                f.write(res.content)
            print(f"✅ Created {filename}")
            return f"images/{filename}"
    except Exception as e:
        print(f"Error: {e}")
    return None

# 1. Generate cover image
if "placehold.co" in data.get('image', ''):
    prompt_cover = f"A high quality illustration for {data['title']}, educational content for preschoolers, modern disney pixar style --aspect 16:9"
    cover_filename = f"{slug}-cover-{timestamp}.webp"
    cover_path = generate_image(prompt_cover, cover_filename)
    if cover_path:
        data['image'] = cover_path

# 2. Extract alt tags from content placeholders and generate images
img_pattern = re.compile(r"<img[^>]+src=['\"](\.\./)?https://placehold\.co[^'\"]+['\"][^>]+alt=['\"](.*?)['\"]", re.IGNORECASE)
matches = img_pattern.findall(content)

idx = 1
for match in set(matches):  # use set to avoid duplicates
    full_src = match[0] + "https://placehold.co/1200x675/F48C06/FFFFFF/png?text=Smart+Genius"
    alt_text = match[1]
    
    filename = f"{slug}-img{idx}-{timestamp}.webp"
    
    # Prompt is the alt text, cleaning it up if needed
    img_path = generate_image(alt_text, filename)
    if img_path:
        # replace the specific placeholder src with the new image path
        # content has src='../https://placehold.co...'
        old_src_pattern = f"\\.\\./https://placehold.co/1200x675/F48C06/FFFFFF/png\\?text=Smart\\+Genius"
        new_src = f"../{img_path}"
        content = re.sub(old_src_pattern, new_src, content, count=1)
    
    idx += 1

data['content'] = content

with open(post_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print("Finished updating images!")
