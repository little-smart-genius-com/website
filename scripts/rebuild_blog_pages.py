"""
REBUILD BLOG PAGES — Regenerates blog.html, blog-2.html, etc.
Uses the existing blog.html as a template and repopulates with current articles.json data.
"""
import os, json, re, math, html

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

ARTICLES_PER_PAGE = 9

def esc(text):
    """HTML-escape text."""
    return html.escape(text or "", quote=True)


def generate_article_card(article):
    """Generate a single article card HTML."""
    title = esc(article.get("title", "Untitled"))
    slug = article.get("slug", "")
    url = f'articles/{slug}.html'
    image = esc(article.get("image", ""))
    category = esc(article.get("category", ""))
    excerpt = esc(article.get("excerpt", ""))
    reading_time = article.get("reading_time", 5)
    
    # Date & Time (Task 4.2)
    iso_date_str = article.get("iso_date", "")
    if iso_date_str:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(iso_date_str.replace('Z', '+00:00'))
            date = dt.strftime("%B %d, %Y at %I:%M %p")
        except:
            date = esc(article.get("date", ""))
    else:
        date = esc(article.get("date", ""))

    return f"""        <article class="rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 border" style="background: var(--card); border-color: var(--bord);">
            <a href="{url}" class="block">
                <div class="aspect-video overflow-hidden rounded-t-2xl">
                    <img src="{image}" alt="{title}" class="w-full h-full object-cover hover:scale-105 transition-transform duration-300" loading="lazy">
                </div>
                <div class="p-6">
                    <div class="flex items-center gap-2 mb-3">
                        <span class="text-xs font-bold uppercase tracking-wider text-brand bg-orange-50 dark:bg-slate-800 px-2 py-1 rounded-full">{category}</span>
                        <span class="text-xs text-slate-500">\U0001f4d6 {reading_time} min</span>
                    </div>
                    <h3 class="text-lg font-extrabold mb-3 hover:text-brand transition leading-snug" style="color: var(--text);">
                        {title}
                    </h3>
                    <p class="text-sm text-slate-600 dark:text-slate-400 mb-4 line-clamp-3">
                        {excerpt}
                    </p>
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold text-slate-500">{date}</span>
                        <span class="text-brand font-bold text-sm">Read More \u2192</span>
                    </div>
                </div>
            </a>
        </article>"""


def generate_pagination(current_page, total_pages, base_name="blog"):
    """Generate pagination navigation HTML."""
    if total_pages <= 1:
        return ''
        
    parts = []
    
    # Previous button
    if current_page == 1:
        parts.append('<span class="px-5 py-3 rounded-xl font-bold text-sm bg-slate-50 dark:bg-slate-800 text-slate-300 dark:text-slate-600 cursor-default">&larr; Previous</span>')
    else:
        prev_file = f"{base_name}.html" if current_page == 2 else f"{base_name}-{current_page - 1}.html"
        parts.append(f'<a href="{prev_file}" class="px-5 py-3 rounded-xl font-bold text-sm transition bg-slate-100 dark:bg-slate-700 hover:bg-brand hover:text-white" style="color:var(--text)">&larr; Previous</a>')
    
    # Page numbers
    for p in range(1, total_pages + 1):
        page_file = f"{base_name}.html" if p == 1 else f"{base_name}-{p}.html"
        if p == current_page:
            parts.append(f'<span class="px-4 py-3 rounded-xl font-bold text-sm bg-brand text-white">{p}</span>')
        else:
            parts.append(f'<a href="{page_file}" class="px-4 py-3 rounded-xl font-bold text-sm bg-slate-100 dark:bg-slate-700 hover:bg-brand hover:text-white transition" style="color:var(--text)">{p}</a>')
    
    # Next button
    if current_page == total_pages:
        parts.append('<span class="px-5 py-3 rounded-xl font-bold text-sm bg-slate-50 dark:bg-slate-800 text-slate-300 dark:text-slate-600 cursor-default">Next &rarr;</span>')
    else:
        next_file = f"{base_name}-{current_page + 1}.html"
        parts.append(f'<a href="{next_file}" class="px-5 py-3 rounded-xl font-bold text-sm transition bg-slate-100 dark:bg-slate-700 hover:bg-brand hover:text-white" style="color:var(--text)">Next &rarr;</a>')
    
    return '<div class="flex items-center justify-center gap-2 mt-12 mb-8 flex-wrap">' + ''.join(parts) + '</div>'



def rebuild_blog_pages():
    """Main function to rebuild blog listing pages."""
    
    # Load articles
    articles_path = os.path.join(PROJECT_ROOT, "articles.json")
    with open(articles_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    articles = data.get("articles", [])
    total_articles = len(articles)
    total_pages = max(1, math.ceil(total_articles / ARTICLES_PER_PAGE))
    
    print("=" * 70)
    print("  REBUILD BLOG PAGES")
    print("=" * 70)
    print(f"\n  Articles: {total_articles}")
    print(f"  Pages: {total_pages} ({ARTICLES_PER_PAGE} per page)")
    
    # Read the existing blog.html as template
    blog_template_path = os.path.join(PROJECT_ROOT, "blog.html")
    with open(blog_template_path, "r", encoding="utf-8") as f:
        template = f.read()
    
    # Extract HEAD section (everything up to and including </head>)
    head_match = re.search(r'(<!DOCTYPE html>.*?</head>)', template, re.DOTALL)
    if not head_match:
        print("  [ERROR] Could not find <head> section in blog.html")
        return
    head_section = head_match.group(1)
    
    # Extract BODY opening up to the article grid start
    body_before_match = re.search(r'(<body>.*?)<!-- STATIC GRID', template, re.DOTALL)
    if not body_before_match:
        print("  [ERROR] Could not find body/grid section")
        return
    body_before = body_before_match.group(1)
    
    # Extract BODY after pagination (footer, cookie banner, scripts — but NOT the inline search data)
    # We want EVERYTHING from </main> onwards, but we need to remove the existing <div class="dark:border-slate-700"... > footer
    footer_match = re.search(r'(</main>.*?)(<div class="dark:border-slate-700".*?)(<script src="exit-intent\.js"></script>|\s*</body>)', template, re.DOTALL)
    
    search_inline = "" # Initialize search_inline
    if footer_match:
        # body_after is everything between </main> and the footer
        body_after = footer_match.group(1)
        search_match = re.search(r'(<script>window\.__SEARCH_INDEX__.*?</script>)', body_after, re.DOTALL)
        if search_match:
            search_inline = search_match.group(1)
            body_after = body_after.replace(search_inline, '')
    else:
        # Fallback if the footer regex fails
        footer_fallback = re.search(r'(</main>.*)</html>', template, re.DOTALL)
        body_after = footer_fallback.group(1) if footer_fallback else '</main></body>'
    
    # Build search index inline data
    search_index_path = os.path.join(PROJECT_ROOT, "search_index.json")
    if os.path.exists(search_index_path):
        with open(search_index_path, "r", encoding="utf-8") as f:
            search_data = json.load(f)
        search_inline = f'    <script>window.__SEARCH_INDEX__={json.dumps(search_data, ensure_ascii=False)};</script>\n'
    
    # Generate each page (Main Blog)
    def create_pages(articles_list, base_name, category_title=None):
        cat_total_pages = max(1, math.ceil(len(articles_list) / ARTICLES_PER_PAGE))
        for page_num in range(1, cat_total_pages + 1):
            start_idx = (page_num - 1) * ARTICLES_PER_PAGE
            end_idx = start_idx + ARTICLES_PER_PAGE
            page_articles = articles_list[start_idx:end_idx]
            
            # Build article cards
            cards_html = "\n".join(generate_article_card(a) for a in page_articles)
            
            # Build pagination
            pagination_html = generate_pagination(page_num, cat_total_pages, base_name)
            
            # Update header info
            page_head = head_section
            
            # Adjust meta title and canonical for category pages
            if category_title:
                page_head = re.sub(r'<title>.*?</title>', f'<title>{category_title} Articles | Little Smart Genius</title>', page_head)
                page_head = re.sub(r'<meta property="og:title" content=".*?">', f'<meta property="og:title" content="{category_title} Articles | Little Smart Genius">', page_head)
            
            page_body_before = body_before
            
            # Adjust the main H1 for category pages
            if category_title:
                page_body_before = re.sub(
                    r'<h1 class="text-4xl md:text-5xl font-extrabold mb-4 hero-title">Our Blog</h1>',
                    f'<h1 class="text-4xl md:text-5xl font-extrabold mb-4 hero-title">{category_title}</h1>',
                    page_body_before
                )
                page_body_before = re.sub(
                    r'<p class="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">.*?</p>',
                    f'<p class="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">Browse all articles related to {category_title}.</p>',
                    page_body_before
                )
            
            # Fix the page info line
            page_body_before = re.sub(
                r'<p class="text-sm text-slate-500 mt-2">.*?</p>',
                f'<p class="text-sm text-slate-500 mt-2">{len(articles_list)} articles \u2022 Page {page_num}/{cat_total_pages}</p>',
                page_body_before
            )
            
            # Assemble full page
            full_html = page_head + "\n\n"
            full_html += page_body_before
            full_html += '<!-- STATIC GRID (server-rendered, visible by default) -->\n'
            full_html += f'        <div id="blog-static-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">\n'
            full_html += cards_html + "\n"
            full_html += '        </div>\n\n'
            full_html += '        <!-- DYNAMIC GRID (JS-rendered, hidden by default) -->\n'
            full_html += '        <div id="blog-dynamic-grid" class="hidden grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"></div>\n\n'
            full_html += '        <!-- INFINITE SCROLL SENTINEL -->\n'
            full_html += '        <div id="blog-scroll-sentinel" class="hidden h-10"></div>\n\n'
            full_html += '        <!-- PAGINATION NAV -->\n'
            full_html += f'        <div id="blog-pagination-nav">\n{pagination_html}\n</div>\n\n'
            full_html += '    </main>\n\n'
            full_html += body_after.replace('</main>', '').strip() + '\n\n'
            full_html += search_inline
            
            # Force script to pre-select category on load so users see it in the dropdown
            script_add = ""
            if category_title:
                script_add = f"""
    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            setTimeout(() => {{
                var select = document.getElementById('blog-category-select');
                if(select) select.value = "{category_title}";
            }}, 100);
        }});
    </script>
"""
            full_html += '    <script src="blog-search.js" defer></script>\n' + script_add
            
            # ADD STANDARD FOOTER
            full_html += """    <!-- SOCIAL MEDIA & FOOTER -->
    <div class="dark:border-slate-700" style="border-top: 1px solid var(--bord, #E2E8F0);">
        <div class="social-footer-bar">
            <a href="https://www.instagram.com/littlesmartgenius_com/" rel="noopener" target="_blank" title="Instagram">
                <svg fill="currentColor" viewbox="0 0 24 24">
                    <path
                        d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z">
                    </path>
                </svg>
            </a>
            <a href="https://www.pinterest.com/littlesmartgenius_com/" rel="noopener" target="_blank" title="Pinterest">
                <svg fill="currentColor" viewbox="0 0 24 24">
                    <path
                        d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.174.271-.401.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.607 0 11.985-5.365 11.985-11.987C23.97 5.39 18.592.026 11.985.026L12.017 0z">
                    </path>
                </svg>
            </a>
            <a href="https://medium.com/@littlesmartgenius-com" rel="noopener" target="_blank" title="Medium">
                <svg fill="currentColor" viewbox="0 0 24 24">
                    <path
                        d="M13.54 12a6.8 6.8 0 01-6.77 6.82A6.8 6.8 0 010 12a6.8 6.8 0 016.77-6.82A6.8 6.8 0 0113.54 12zM20.96 12c0 3.54-1.51 6.42-3.38 6.42-1.87 0-3.39-2.88-3.39-6.42s1.52-6.42 3.39-6.42 3.38 2.88 3.38 6.42M24 12c0 3.17-.53 5.75-1.19 5.75-.66 0-1.19-2.58-1.19-5.75s.53-5.75 1.19-5.75C23.47 6.25 24 8.83 24 12z">
                    </path>
                </svg>
            </a>
        </div>
        <div class="site-footer" style="text-align: center;">
            <div style="margin-bottom: 6px;">
                <a href="terms.html">Terms of Service</a>
                <span style="margin: 0 8px;">•</span>
                <a href="privacy.html">Privacy Policy</a>
            </div>
            © 2026 Little Smart Genius. All rights reserved.
        </div>
    </div>
"""
            full_html += '<script src="exit-intent.js"></script>\n</body>\n\n</html>'
            
            output_file = os.path.join(PROJECT_ROOT, f"{base_name}.html") if page_num == 1 else os.path.join(PROJECT_ROOT, f"{base_name}-{page_num}.html")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(full_html)
            
            file_size = os.path.getsize(output_file) // 1024
            print(f"  [{page_num}/{cat_total_pages}] OK  {file_size}KB  {os.path.basename(output_file)} ({len(page_articles)} articles)")

    # 1. Create main blog pages
    print("\n  Generating Main Blog Pages...")
    create_pages(articles, "blog")
    
    # Clean up old blog pages (if any exist beyond current total)
    for old_page in range(total_pages + 1, 10):
        old_file = os.path.join(PROJECT_ROOT, f"blog-{old_page}.html")
        if os.path.exists(old_file):
            os.remove(old_file)
            print(f"  [CLEANUP] Removed {os.path.basename(old_file)}")
            
    # 2. Extract unique categories and create Pillar Pages
    print("\n  Generating Category Pillar Pages (Semantic Silos)...")
    category_map = {}
    for a in articles:
        cat = a.get('category', '')
        if cat:
            if cat not in category_map:
                category_map[cat] = []
            category_map[cat].append(a)
            
    for cat, cat_articles in category_map.items():
        # URL safe slug for category
        cat_slug = re.sub(r'[^a-z0-9]+', '-', cat.lower()).strip('-')
        if cat_slug:
            base_name = f"blog-{cat_slug}"
            print(f"  >> Category: {cat} (slug: {base_name})")
            create_pages(cat_articles, base_name, category_title=cat)

    print(f"\n  DONE! Main blog and {len(category_map)} category pillar pages generated.")


if __name__ == "__main__":
    rebuild_blog_pages()
