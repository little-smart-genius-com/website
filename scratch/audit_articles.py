import os
import json

ARCHIVE_DIR = "data/archive_posts"

def audit():
    total = 0
    missing_cover = 0
    missing_section_images = 0
    damaged_image_paths = 0

    for fname in os.listdir(ARCHIVE_DIR):
        if not fname.endswith(".json"): continue
        total += 1
        path = os.path.join(ARCHIVE_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            cover = data.get("image")
            if not cover or len(cover.strip()) == 0:
                missing_cover += 1
            elif " an alt that reads " in cover:
                damaged_image_paths += 1
                
            for sec in data.get("sections", []):
                sec_img = sec.get("image")
                if not sec_img or len(sec_img.strip()) == 0:
                    missing_section_images += 1
                elif " an alt that reads " in sec_img:
                    damaged_image_paths += 1
                    
        except Exception as e:
            print(f"Error parsing {fname}: {e}")
            
    print(f"Total articles audited: {total}")
    print(f"Articles missing cover: {missing_cover}")
    print(f"Sections missing images: {missing_section_images}")
    print(f"Damaged image paths (e.g. alt text mixed in): {damaged_image_paths}")

if __name__ == "__main__":
    audit()
