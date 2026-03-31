"""Batch fix broken links found in the report."""
import re, os, glob

articles_dir = "articles"
existing_slugs = {os.path.basename(f) for f in glob.glob(os.path.join(articles_dir, "*.html"))}

valid_roots = {"freebies.html", "products.html", "about.html", "contact.html",
                "terms.html", "privacy.html", "education.html", "legal.html", "index.html"}

fixed_files = 0
unwrapped_links = 0
root_fixed = 0

for f in sorted(glob.glob(os.path.join(articles_dir, "*.html"))):
    with open(f, "r", encoding="utf-8") as fh:
        html = fh.read()
    
    original_html = html
    name = os.path.basename(f)
    
    # We want to use a regex replacement function to process all links carefully
    def replacer(match):
        global unwrapped_links, root_fixed
        full_a_tag = match.group(0)
        href = match.group(1)
        inner_text = match.group(2)
        
        # Skip absolute and external links
        if href.startswith(("http", "mailto", "tel", "javascript", "/", "#")):
            return full_a_tag
            
        # Fix missing root slash for root pages (e.g., href="products.html")
        if target := href.split("?")[0].split("#")[0]:
            if target in valid_roots:
                root_fixed += 1
                return full_a_tag.replace(f'href="{href}"', f'href="/{href}"')
        
        # Check if it's a broken ../ link
        if href.startswith("../"):
            target = href.split("?")[0].split("#")[0].replace("../", "")
            if target not in valid_roots and not target.startswith("blog/") and not target.startswith("images/") and not target.startswith("articles/"):
                # It's an unknown ../ link like ../resources.html - unwrap it
                unwrapped_links += 1
                return inner_text
            return full_a_tag
            
        # Check if it's a sibling link but the sibling doesn't exist
        if re.match(r"^[a-z0-9-]+\.html$", target):
            if target not in existing_slugs and target not in valid_roots:
                # Missing sibling - unwrap
                unwrapped_links += 1
                return inner_text
                
        return full_a_tag

    # Find all <a> tags and replace using the replacer function
    # The regex needs to capture the href value and the inner text.
    # It must handle nested HTML within the <a> tag cautiously.
    html = re.sub(
        r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        replacer,
        html,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    if html != original_html:
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(html)
        fixed_files += 1

print(f"Fixed {fixed_files} files.")
print(f"  Unwrapped {unwrapped_links} hallucinated links")
print(f"  Fixed {root_fixed} root-level links missing slash")
