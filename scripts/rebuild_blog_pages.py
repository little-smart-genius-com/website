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


def generate_pagination(current_page, total_pages):
    """Generate pagination navigation HTML."""
    parts = []
    
    # Previous button
    if current_page == 1:
        parts.append('<span class="px-5 py-3 rounded-xl font-bold text-sm bg-slate-50 dark:bg-slate-800 text-slate-300 dark:text-slate-600 cursor-default">&larr; Previous</span>')
    else:
        prev_file = "blog.html" if current_page == 2 else f"blog-{current_page - 1}.html"
        parts.append(f'<a href="{prev_file}" class="px-5 py-3 rounded-xl font-bold text-sm transition bg-slate-100 dark:bg-slate-700 hover:bg-brand hover:text-white" style="color:var(--text)">&larr; Previous</a>')
    
    # Page numbers
    for p in range(1, total_pages + 1):
        page_file = "blog.html" if p == 1 else f"blog-{p}.html"
        if p == current_page:
            parts.append(f'<span class="px-4 py-3 rounded-xl font-bold text-sm bg-brand text-white">{p}</span>')
        else:
            parts.append(f'<a href="{page_file}" class="px-4 py-3 rounded-xl font-bold text-sm bg-slate-100 dark:bg-slate-700 hover:bg-brand hover:text-white transition" style="color:var(--text)">{p}</a>')
    
    # Next button
    if current_page == total_pages:
        parts.append('<span class="px-5 py-3 rounded-xl font-bold text-sm bg-slate-50 dark:bg-slate-800 text-slate-300 dark:text-slate-600 cursor-default">Next &rarr;</span>')
    else:
        next_file = f"blog-{current_page + 1}.html"
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
    footer_match = re.search(r'(</main>.*?)(    <script>window\.__SEARCH_INDEX__.*?</script>)?\s*(<script src="blog-search.js" defer></script>\s*</body>\s*</html>)', template, re.DOTALL)
    if not footer_match:
        # Fallback: find from </main> to end
        footer_match = re.search(r'(</main>.*)</html>', template, re.DOTALL)
        body_after = footer_match.group(1) + '</html>' if footer_match else '</main></body></html>'
        search_script_tag = ''
    else:
        body_after = footer_match.group(1)
        search_script_tag = footer_match.group(3)
    
    # Build search index inline data
    search_index_path = os.path.join(PROJECT_ROOT, "search_index.json")
    search_inline = ""
    if os.path.exists(search_index_path):
        with open(search_index_path, "r", encoding="utf-8") as f:
            search_data = json.load(f)
        search_inline = f'    <script>window.__SEARCH_INDEX__={json.dumps(search_data, ensure_ascii=False)};</script>\n'
    
    # Generate each page
    for page_num in range(1, total_pages + 1):
        start_idx = (page_num - 1) * ARTICLES_PER_PAGE
        end_idx = start_idx + ARTICLES_PER_PAGE
        page_articles = articles[start_idx:end_idx]
        
        # Build article cards
        cards_html = "\n".join(generate_article_card(a) for a in page_articles)
        
        # Build pagination
        pagination_html = generate_pagination(page_num, total_pages)
        
        # Update header info
        page_head = head_section
        page_body_before = body_before
        
        # Fix the page info line
        page_body_before = re.sub(
            r'<p class="text-sm text-slate-500 mt-2">.*?</p>',
            f'<p class="text-sm text-slate-500 mt-2">{total_articles} articles \u2022 Page {page_num}/{total_pages}</p>',
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
        full_html += '    <script src="blog-search.js" defer></script>\n'
        full_html += '</body>\n\n</html>'
        
        # Write the file
        if page_num == 1:
            output_file = os.path.join(PROJECT_ROOT, "blog.html")
        else:
            output_file = os.path.join(PROJECT_ROOT, f"blog-{page_num}.html")
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_html)
        
        file_size = os.path.getsize(output_file) // 1024
        print(f"  [{page_num}/{total_pages}] OK  {file_size}KB  {os.path.basename(output_file)} ({len(page_articles)} articles)")
    
    # Clean up old blog pages that are no longer needed
    for old_page in range(total_pages + 1, 10):  # Clean up up to blog-9.html
        old_file = os.path.join(PROJECT_ROOT, f"blog-{old_page}.html")
        if os.path.exists(old_file):
            os.remove(old_file)
            print(f"  [CLEANUP] Removed {os.path.basename(old_file)} (no longer needed)")
    
    print(f"\n  DONE! {total_pages} blog pages generated.")


if __name__ == "__main__":
    rebuild_blog_pages()
