import os
import re
import glob

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    html_files = glob.glob(os.path.join(base_dir, "*.html"))
    html_files.extend(glob.glob(os.path.join(base_dir, "articles", "*.html")))
    
    img_regex = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
    source_regex = re.compile(r'<source[^>]+srcset=["\']([^"\'\s]+)', re.IGNORECASE)
    og_regex = re.compile(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', re.IGNORECASE)
    twitter_regex = re.compile(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', re.IGNORECASE)
    
    missing_files = []
    checked_count = 0
    missing_unique = set()
    
    for file_path in html_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            links = []
            links.extend(img_regex.findall(content))
            links.extend(source_regex.findall(content))
            links.extend(og_regex.findall(content))
            links.extend(twitter_regex.findall(content))
            
            for link in links:
                # ignore external links
                if link.startswith("http") and "littlesmartgenius.com" not in link:
                    continue
                if link.startswith("data:"):
                    continue
                if link.startswith("${"):
                    continue
                
                # normalize local paths
                local_path = link.replace("https://littlesmartgenius.com/", "")
                local_path = local_path.lstrip("../")
                local_path = local_path.lstrip("./")
                local_path = local_path.lstrip("/")
                
                # Build absolute local path
                abs_path = os.path.join(base_dir, os.path.normpath(local_path))
                
                checked_count += 1
                if not os.path.exists(abs_path):
                    missing_unique.add(local_path)
                    missing_files.append((file_path, local_path))
                    
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    print(f"Scanned {len(html_files)} HTML files.")
    print(f"Checked {checked_count} image references.")
    
    if len(missing_files) == 0:
        print("SUCCESS: No broken image links found! All referenced images exist locally.")
    else:
        print(f"ERROR: Found {len(missing_files)} broken image references (total {len(missing_unique)} unique missing files):")
        for f in missing_unique:
            print(f"  - {f}")
            
        print("\nLocations of broken links (First 10):")
        for i, (html_file, img_link) in enumerate(missing_files[:10]):
            print(f"  - In {html_file}: {img_link}")

if __name__ == "__main__":
    main()
