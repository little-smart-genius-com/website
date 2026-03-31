"""Scan all articles for broken link patterns — write to file."""
import re, os, glob

articles_dir = "articles"
issues = []
existing_slugs = set()

for f in glob.glob(os.path.join(articles_dir, "*.html")):
    existing_slugs.add(os.path.basename(f))

for f in sorted(glob.glob(os.path.join(articles_dir, "*.html"))):
    with open(f, "r", encoding="utf-8") as fh:
        html = fh.read()
    name = os.path.basename(f)
    
    for m in re.finditer(r'href="([^"#][^"]*?)"', html):
        href = m.group(1)
        if href.startswith("http") or href.startswith("mailto") or href.startswith("tel") or href.startswith("javascript"):
            continue
        if href.startswith("/"):
            continue  # Absolute paths are OK
        
        if "../../" in href:
            issues.append((name, f"Deep relative: {href}"))
            continue
        
        if href.startswith("../"):
            target = href.split("?")[0].split("#")[0].replace("../", "")
            valid_roots = {"freebies.html", "products.html", "about.html", "contact.html",
                          "terms.html", "privacy.html", "education.html", "legal.html",
                          "index.html", "exit-intent.js", ""}
            if target in valid_roots or target.startswith("blog/") or target.startswith("images/") or target.startswith("articles/"):
                continue
            issues.append((name, f"Unknown ../target: {href}"))
            continue
        
        if href == "another-topic.html":
            issues.append((name, f"Placeholder: {href}"))
        elif re.match(r"^[a-z].*\.html$", href) and "/" not in href:
            if href not in existing_slugs:
                issues.append((name, f"Missing sibling: {href}"))

with open("_broken_links_report.txt", "w", encoding="utf-8") as out:
    out.write(f"Scanned {len(existing_slugs)} articles\n")
    out.write(f"Found {len(issues)} broken links\n\n")
    for name, issue in sorted(issues):
        out.write(f"  {name}: {issue}\n")

print(f"Scanned {len(existing_slugs)} articles, found {len(issues)} broken links")
print("Report written to _broken_links_report.txt")
