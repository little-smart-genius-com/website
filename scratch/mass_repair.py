import os
import json
import glob
import re

def main():
    print("Starting mass repair audit...")
    files = glob.glob("data/archive_posts/*.json") + glob.glob("data/pending_posts/*.json")
    
    corrupted_count = 0
    fixed_count = 0
    
    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"Error decoding JSON in {filepath}")
                continue
                
        needs_save = False
        content = data.get("content_html", "")
        
        idx = 0
        while True:
            idx = content.find("<img", idx)
            if idx == -1:
                break
                
            end_idx = content.find(">", idx)
            next_tag_idx = content.find("<", idx + 1)
            
            if end_idx == -1 or (next_tag_idx != -1 and next_tag_idx < end_idx):
                print(f"Malformed img tag found in {filepath}")
                corrupted_count += 1
                
                if next_tag_idx != -1:
                    broken_tag = content[idx:next_tag_idx]
                    if 'src="' in broken_tag:
                        fixed_tag = broken_tag.strip()
                        if not fixed_tag.endswith('"'):
                            src_match = re.search(r'src="([^"]+)"', broken_tag)
                            alt_match = re.search(r'alt="([^"]+)"', broken_tag)
                            if src_match:
                                src = src_match.group(1)
                                alt = alt_match.group(1) if alt_match else "image"
                                fixed_tag = f'<img src="{src}" alt="{alt}" class="w-full h-auto rounded-lg shadow-md my-8" />'
                            else:
                                fixed_tag = fixed_tag + ' />'
                        else:
                            fixed_tag = fixed_tag + ' />'
                        
                        content = content[:idx] + fixed_tag + content[next_tag_idx:]
                        needs_save = True
                        fixed_count += 1
                        print(f"  -> Fixed tag!")
                    else:
                        print(f"  -> Could not auto-fix tag: {broken_tag}")
                        idx = next_tag_idx
                else:
                    idx += 4
            else:
                idx = end_idx + 1

        if needs_save:
            data["content_html"] = content
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                
    print(f"\nAudit complete. Found {corrupted_count} corrupted images. Fixed {fixed_count}.")

if __name__ == "__main__":
    main()
