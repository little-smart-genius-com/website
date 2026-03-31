import os
import re

html_files = []
for directory in ['.', 'articles', 'blog']:
    if os.path.exists(directory):
        html_files.extend([os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.html')])

# Match single or double quotes for href, and allow any internal spacing
favicon_pattern = re.compile(
    r'<link[^>]*https://ecdn\.teacherspayteachers\.com/thumbuserhome/Little-Smart-Genius[^>]*>', 
    re.IGNORECASE
)
new_favicon = '<link rel="icon" type="image/x-icon" href="/favicon.ico">'

schema = """
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "WebSite",
      "name": "Little Smart Genius",
      "url": "https://littlesmartgenius.com/",
      "potentialAction": {
        "@type": "SearchAction",
        "target": "https://littlesmartgenius.com/blog/?q={search_term_string}",
        "query-input": "required name=search_term_string"
      }
    }
    </script>
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "Organization",
      "name": "Little Smart Genius",
      "url": "https://littlesmartgenius.com/",
      "logo": "https://littlesmartgenius.com/favicon.ico",
      "sameAs": [
        "https://www.instagram.com/littlesmartgenius_com/",
        "https://www.pinterest.com/littlesmartgenius_com/"
      ]
    }
    </script>
"""

count = 0
for hf in html_files:
    with open(hf, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    # Try replacing the ecdn tag
    if favicon_pattern.search(content):
        content = favicon_pattern.sub(new_favicon, content)
        modified = True
        
    if hf == 'index.html' and '@type": "Organization"' not in content:
        content = content.replace('</head>', f'{schema}\n</head>')
        modified = True
            
    if modified:
        with open(hf, 'w', encoding='utf-8') as f:
            f.write(content)
        count += 1

print(f"Updated {count} root HTMLs")
