import os
import glob
import requests
import json
import time
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.environ.get("MAKECOM_WEBHOOK_URL", "")
if not WEBHOOK_URL:
    print("Error: MAKECOM_WEBHOOK_URL not found in .env")
    exit(1)

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/little-smart-genius-com/website/main/instagram/"
IG_DIR = os.path.join(os.path.dirname(__file__), "..", "instagram")

# Find all .txt files
txt_files = glob.glob(os.path.join(IG_DIR, "*.txt"))
print(f"Found {len(txt_files)} Instagram posts to process.\n")

success_count = 0
for txt_path in txt_files:
    basename = os.path.basename(txt_path).replace(".txt", "")
    jpg_path = os.path.join(IG_DIR, f"{basename}.jpg")
    
    if not os.path.exists(jpg_path):
        print(f"Skipping {basename}: Missing .jpg file")
        continue
        
    # Read caption and hashtags
    with open(txt_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Split content (usually caption then blank line then hashtags)
    parts = content.split("\n\n")
    caption = parts[0].strip() if parts else ""
    hashtags = parts[-1].strip() if len(parts) > 1 else ""
    
    # Construct raw GitHub URL for the image
    image_url = f"{GITHUB_RAW_BASE}{basename}.jpg"
    
    # Try to derive article URL from filename (simplistic approach, mostly for logging)
    slug = basename.rsplit("-ig-", 1)[0]
    article_url = f"https://littlesmartgenius.com/articles/{slug}.html"
    
    payload = {
        "image_url": image_url,
        "image_filename": f"{basename}.jpg",
        "caption": caption,
        "hashtags": hashtags,
        "article_url": article_url,
        "brand": "Little Smart Genius",
        "timestamp": datetime.now().isoformat(),
    }
    
    print(f"Sending: {basename} ...")
    try:
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=30)
        if resp.status_code == 200:
            print("  -> OK")
            success_count += 1
            time.sleep(3) # Wait between requests so Make doesn't rate limit or drop parallel requests
        else:
            print(f"  -> Failed: HTTP {resp.status_code}")
    except Exception as e:
        print(f"  -> Error: {e}")

print(f"\nCompleted: {success_count} posts sent successfully to Make.com")
