import os
import glob
import json
from datetime import datetime
from bs4 import BeautifulSoup
import math
import re

ARTICLES_DIR = 'articles'
IMAGES_DIR = 'images'
ARTICLES_PER_PAGE = 9

def get_articles():
    articles = []
    html_files = glob.glob(os.path.join(ARTICLES_DIR, '*.html'))
    
    for filepath in html_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Extract Meta Data
            title_tag = soup.find('meta', property='og:title')
            title = title_tag['content'] if title_tag else soup.find('title').string
            
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            desc = desc_tag['content'] if desc_tag else ""
            
            img_tag = soup.find('meta', property='og:image')
            img_full = img_tag['content'] if img_tag else ""
            # Convert full URL to relative path
            img = 'images/' + os.path.basename(img_full) if img_full else ""
            
            date_tag = soup.find('meta', property='article:published_time')
            iso_date = date_tag['content'] if date_tag else datetime.now().isoformat()
            
            # Parse Date for UI display
            try:
                dt = datetime.fromisoformat(iso_date)
                formatted_date = dt.strftime("%B %d, %Y").replace(" 0", " ") # Remove leading zero
            except:
                formatted_date = iso_date
                
            # Category
            cat_elem = soup.find('div', class_='flex items-center justify-center gap-4 text-sm font-bold')
            category = "Education"
            if cat_elem:
                spans = cat_elem.find_all('span')
                if len(spans) >= 5:
                    category = spans[4].text.strip()
                    
            # Reading Time
            rt_elem = soup.find('span', class_='reading-time')
            reading_time_str = rt_elem.text if rt_elem else "10"
            rt_match = re.search(r'(\d+)', reading_time_str)
            reading_time = int(rt_match.group(1)) if rt_match else 10
            
            # Count words
            text_content = soup.find('div', class_='article-content')
            word_count = len(text_content.text.split()) if text_content else 1000
            
            # Extract keywords
            kw_tag = soup.find('meta', attrs={'name': 'keywords'})
            keywords = [k.strip() for k in kw_tag['content'].split(',')] if kw_tag else []

            # Slot (simulated from what we see, mostly "freebie", "keyword" or "product")
            slot = "keyword"
            
            path_url = filepath.replace('\\', '/')
            
            articles.append({
                "title": title,
                "slug": os.path.basename(filepath).replace('.html', ''),
                "date": formatted_date,
                "iso_date": iso_date,
                "category": category,
                "excerpt": desc,
                "image": img,
                "reading_time": reading_time,
                "url": path_url,
                "keywords": keywords,
                "word_count": word_count,
                "slot": slot
            })
            
    # Sort by date descending
    articles.sort(key=lambda x: x['iso_date'], reverse=True)
    return articles

def generate_article_card(article, in_subfolder=False):
    prefix = '../' if in_subfolder else ''
    url = f"{prefix}{article['url']}"
    img = f"{prefix}{article['image']}"
    
    return f'''<article class="rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 border" style="background: var(--card); border-color: var(--bord);">
<a class="block" href="{url}">
<div class="aspect-video overflow-hidden rounded-t-2xl">
<img alt="{article['title']}" class="w-full h-full object-cover hover:scale-105 transition-transform duration-300" loading="lazy" src="{img}"/>
</div>
<div class="p-6">
<div class="flex items-center gap-2 mb-3">
<span class="text-xs font-bold uppercase tracking-wider text-brand bg-orange-50 dark:bg-slate-800 px-2 py-1 rounded-full">{article['category']}</span>
<span class="text-xs text-slate-500">📖 {article['reading_time']} min</span>
</div>
<h3 class="text-lg font-extrabold mb-3 hover:text-brand transition leading-snug" style="color: var(--text);">
                        {article['title']}
                    </h3>
<p class="text-sm text-slate-600 dark:text-slate-400 mb-4 line-clamp-3">
                        {article['excerpt']}
                    </p>
<div class="flex items-center justify-between">
<span class="text-xs font-bold text-slate-500">{article['date']}</span>
<span class="text-brand font-bold text-sm">Read More →</span>
</div>
</div>
</a>
</article>'''

def generate_sidebar_card(article):
    url = f"../{article['url']}"
    img = f"../{article['image']}"
    
    return f'''<a class="block rounded-xl overflow-hidden border hover:shadow-xl transition-all duration-300 group" href="{url}" style="background: var(--card); border-color: var(--bord);">
<div class="aspect-video overflow-hidden">
<img alt="{article['title']}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" loading="lazy" src="{img}"/>
</div>
<div class="p-4">
<div class="flex items-center gap-2 mb-2">
<span class="text-xs font-bold uppercase tracking-wider text-brand bg-orange-50 dark:bg-slate-800 px-2 py-0.5 rounded-full">{article['category']}</span>
<span class="text-xs text-slate-500">📖 {article['reading_time']} min</span>
</div>
<h4 class="font-bold text-sm group-hover:text-brand transition" style="color: var(--text);">{article['title']}</h4>
</div>
</a>'''

def rebuild_home(articles):
    with open('index.html', 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        
    # Find the "Latest Articles" grid. It is the grid exactly after the H2 "Latest Articles"
    h2_tags = soup.find_all('h2')
    latest_h2 = next((h2 for h2 in h2_tags if 'Latest Articles' in h2.text), None)
    
    if latest_h2:
        grid = latest_h2.find_next_sibling('div', class_='grid')
        if grid:
            grid.clear()
            for art in articles[:3]:
                card_html = generate_article_card(art)
                card_soup = BeautifulSoup(card_html, 'html.parser')
                grid.append(card_soup)
                
            with open('index.html', 'w', encoding='utf-8') as f:
                f.write(str(soup))
            print("index.html updated.")

def rebuild_blog_pages(articles):
    total_pages = math.ceil(len(articles) / ARTICLES_PER_PAGE)
    
    # Read the base template from blog.html
    with open('blog.html', 'r', encoding='utf-8') as f:
        base_soup = BeautifulSoup(f.read(), 'html.parser')
        
    # Update search index in base_soup (we'll reuse this updated soup)
    script_tags = base_soup.find_all('script')
    for script in script_tags:
        if script.string and 'window.__SEARCH_INDEX__' in script.string:
            search_data = {
                "generated_at": datetime.now().isoformat(),
                "total_articles": len(articles),
                "articles": articles
            }
            script.string = f'window.__SEARCH_INDEX__={json.dumps(search_data)};'
            break
            
    for page in range(1, total_pages + 1):
        filename = 'blog.html' if page == 1 else f'blog-{page}.html'
        
        # Clone soup
        soup = BeautifulSoup(str(base_soup), 'html.parser')
        
        # Update meta title and description
        if page > 1:
            soup.find('title').string = f"Blog - Page {page} | Little Smart Genius"
        
        # Update Header text (Page X/Y)
        page_info = soup.find('p', text=re.compile(r'\d+ articles • Page \d+/\d+'))
        if page_info:
            page_info.string = f"{len(articles)} articles • Page {page}/{total_pages}"
            
        # Update Grid
        grid = soup.find('div', id='blog-static-grid')
        if grid:
            grid.clear()
            start_idx = (page - 1) * ARTICLES_PER_PAGE
            end_idx = start_idx + ARTICLES_PER_PAGE
            for art in articles[start_idx:end_idx]:
                card_html = generate_article_card(art)
                grid.append(BeautifulSoup(card_html, 'html.parser'))
                
        # Update Pagination
        nav = soup.find('div', id='blog-pagination-nav')
        if nav:
            pagination_container = nav.find('div')
            pagination_container.clear()
            
            # Prev Button
            if page == 1:
                pagination_container.append(BeautifulSoup('<span class="px-5 py-3 rounded-xl font-bold text-sm bg-slate-50 dark:bg-slate-800 text-slate-300 dark:text-slate-600 cursor-default">← Previous</span>', 'html.parser'))
            else:
                prev_link = 'blog.html' if page == 2 else f'blog-{page-1}.html'
                pagination_container.append(BeautifulSoup(f'<a class="px-5 py-3 rounded-xl font-bold text-sm bg-slate-100 dark:bg-slate-700 hover:bg-brand hover:text-white transition" href="{prev_link}" style="color:var(--text)">← Previous</a>', 'html.parser'))
                
            # Numbers
            for p in range(1, total_pages + 1):
                if p == page:
                    pagination_container.append(BeautifulSoup(f'<span class="px-4 py-3 rounded-xl font-bold text-sm bg-brand text-white">{p}</span>', 'html.parser'))
                else:
                    plink = 'blog.html' if p == 1 else f'blog-{p}.html'
                    pagination_container.append(BeautifulSoup(f'<a class="px-4 py-3 rounded-xl font-bold text-sm bg-slate-100 dark:bg-slate-700 hover:bg-brand hover:text-white transition" href="{plink}" style="color:var(--text)">{p}</a>', 'html.parser'))
                    
            # Next Button
            if page == total_pages:
                pagination_container.append(BeautifulSoup('<span class="px-5 py-3 rounded-xl font-bold text-sm bg-slate-50 dark:bg-slate-800 text-slate-300 dark:text-slate-600 cursor-default">Next →</span>', 'html.parser'))
            else:
                next_link = f'blog-{page+1}.html'
                pagination_container.append(BeautifulSoup(f'<a class="px-5 py-3 rounded-xl font-bold text-sm bg-slate-100 dark:bg-slate-700 hover:bg-brand hover:text-white transition" href="{next_link}" style="color:var(--text)">Next →</a>', 'html.parser'))
                
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print(f"{filename} updated.")

def rebuild_articles_sidebar(articles):
    # Update the "You Might Also Like" section inside each article.
    html_files = glob.glob(os.path.join(ARTICLES_DIR, '*.html'))
    for filepath in html_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
        h3_tags = soup.find_all(['h3', 'h4'])
        like_heading = next((h for h in h3_tags if 'You Might Also Like' in h.text), None)
        
        if like_heading:
            # Reconstruct the grid
            grid = like_heading.parent.find_next_sibling('div', class_='grid')
            if grid:
                grid.clear()
                
                # Find current slug to avoid recommending itself
                current_slug = os.path.basename(filepath).replace('.html', '')
                curr_category = next((a['category'] for a in articles if a['slug'] == current_slug), None)
                
                # Recommend 3 items from same category, fallback to latest
                recommendations = [a for a in articles if a['category'] == curr_category and a['slug'] != current_slug]
                if len(recommendations) < 3:
                    recommendations += [a for a in articles if a['slug'] != current_slug and a['slug'] not in [r['slug'] for r in recommendations]]
                
                for art in recommendations[:3]:
                    card_html = generate_sidebar_card(art)
                    grid.append(BeautifulSoup(card_html, 'html.parser'))
                    
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
    print("Article sidebars updated.")
    
def rebuild_sitemap(articles):
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\\n'
    
    # Static pages
    static_pages = ['', 'products.html', 'freebies.html', 'blog.html', 'about.html', 'contact.html']
    for page in static_pages:
        sitemap += f'  <url>\\n    <loc>https://littlesmartgenius.com/{page}</loc>\\n    <changefreq>weekly</changefreq>\\n    <priority>{"1.0" if page == "" else "0.8"}</priority>\\n  </url>\\n'
        
    for art in articles:
        # Date format YYYY-MM-DD for sitemap
        iso_str = art['iso_date'].split('T')[0]
        sitemap += f'  <url>\\n    <loc>https://littlesmartgenius.com/{art["url"]}</loc>\\n    <lastmod>{iso_str}</lastmod>\\n    <changefreq>monthly</changefreq>\\n    <priority>0.6</priority>\\n  </url>\\n'
        
    sitemap += '</urlset>'
    
    with open('sitemap.xml', 'w', encoding='utf-8') as f:
        f.write(sitemap)
    print("sitemap.xml updated.")


if __name__ == '__main__':
    print("Starting Little Smart Genius REBUILD...")
    articles = get_articles()
    print(f"Loaded {len(articles)} articles.")
    
    rebuild_home(articles)
    rebuild_blog_pages(articles)
    rebuild_articles_sidebar(articles)
    rebuild_sitemap(articles)
    
    print("Rebuild COMPLETE ✅")
