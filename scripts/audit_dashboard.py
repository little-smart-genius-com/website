import os
import re
import json
from collections import defaultdict
from typing import Dict, List, Any
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("BeautifulSoup4 is required. Please run: pip install beautifulsoup4")
    import sys
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
OUTPUT_HTML = os.path.join(PROJECT_ROOT, "audit_dashboard.html")

def extract_text_from_html(soup: BeautifulSoup) -> str:
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text(separator=' ')
    return re.sub(r'\s+', ' ', text).strip()

def analyze_article(filepath: str) -> Dict[str, Any]:
    with open(filepath, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    filename = os.path.basename(filepath)
    slug = filename.replace('.html', '')
    
    errors = []
    
    # Title
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else "N/A"
    if '...' in title:
        errors.append("Truncated Title")

    # Keywords
    meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
    keywords = meta_keywords['content'] if meta_keywords and meta_keywords.has_attr('content') else ""
    keyword_count = len([k for k in keywords.split(',') if k.strip()]) if keywords else 0
    focus_keyword = keywords.split(',')[0].strip() if keywords else ""
    
    fk_words = [w for w in re.split(r'\s+', focus_keyword) if w]
    if len(fk_words) < 2 and focus_keyword:
        errors.append("Short Focus Keyword")
    elif not focus_keyword:
        errors.append("Missing Focus Keyword")

    # Word Count
    article_content_div = soup.find('div', class_='article-content')
    if article_content_div:
        text_content = extract_text_from_html(article_content_div)
    else:
        text_content = extract_text_from_html(soup.find('body') or soup)
    words = [w for w in re.findall(r'\b\w+\b', text_content)]
    word_count = len(words)

    # Images
    main_block = soup.find('main')
    total_images = len(main_block.find_all('img')) if main_block else 0
    if total_images != 6:
        errors.append(f"Invalid Image Count ({total_images}/6)")
    
    avg_words_between_images = word_count // (total_images + 1) if total_images > 0 else word_count

    # Links
    all_links = soup.find_all('a', href=True)
    internal_links = 0
    external_links = 0
    links_to_other_articles = 0
    links_to_freebies = 0
    links_to_paid_products = 0
    
    related_tags = []
    short_tags = False

    for link in all_links:
        href = link['href'].lower()
        text = link.get_text(strip=True)
        if text.startswith('#'):
            clean_tag = text.lstrip('#')
            related_tags.append(clean_tag)
            if len([w for w in re.split(r'\s+|-', clean_tag) if w]) < 2:
                short_tags = True
                
        if href.startswith('http') and 'littlesmartgenius.com' not in href:
            external_links += 1
            if 'teacherspayteachers.com' in href:
                links_to_paid_products += 1
        else:
            internal_links += 1
            if 'articles/' in href or href.endswith('.html') and 'blog' not in href and 'products' not in href and 'freebies' not in href and href != 'index.html':
                links_to_other_articles += 1
            if 'freebies' in href:
                links_to_freebies += 1
            if 'products' in href:
                links_to_paid_products += 1
                
    if short_tags:
        errors.append("Short Related Tags")

    # Headings
    h2_count = len(soup.find_all('h2'))
    h3_count = len(soup.find_all('h3'))

    # Features
    has_faq = "Yes" if soup.find('details') or soup.find(lambda tag: tag.name == "h2" and "frequently asked questions" in tag.text.lower()) else "No"
    if has_faq == "No": errors.append("Missing FAQ")
    
    tpt_resource_span = soup.find(lambda tag: tag.name == "span" and "Recommended Resource" in tag.text)
    suggested_premium = "Yes" if tpt_resource_span else "No"
    if suggested_premium == "No": errors.append("Missing TPT Block")
    
    toc_container = soup.find(class_="toc-container")
    if not toc_container: errors.append("Missing TOC")

    scroll_to_top = "Yes" if soup.find(id="scrollTopBtn") else "No"
    prev_button = "Yes" if soup.find(id="prevArticleNav") or soup.find(class_="article-nav-prev") else "No"
    next_button = "Yes" if soup.find(id="nextArticleNav") or soup.find(class_="article-nav-next") else "No"
    
    # related articles
    related_articles_div = soup.find(class_="related-articles")
    has_related_articles = "Yes" if related_articles_div else "No"

    return {
        "Slug": slug,
        "Filename": filename,
        "Title": title,
        "Focus Keyword": focus_keyword,
        "Total Meta Keywords": keyword_count,
        "Word Count": word_count,
        "Images": total_images,
        "Avg Words/Img": avg_words_between_images,
        "Internal Links": internal_links,
        "External Links": external_links,
        "Other Articles": links_to_other_articles,
        "Freebies Linking": links_to_freebies,
        "Products Linking": links_to_paid_products,
        "Tags Count": len(related_tags),
        "H2": h2_count,
        "H3": h3_count,
        "FAQ": has_faq,
        "Suggested Articles": has_related_articles,
        "Suggested Premium Products": suggested_premium,
        "Scroll To Top Button": scroll_to_top,
        "Prev Button": prev_button,
        "Next Button": next_button,
        "TOC": "Yes" if toc_container else "No",
        "Errors": errors
    }

def build_dashboard(results: List[Dict]):
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blog Health Check Dashboard (Ultra Detailed)</title>
    <style>
        :root { --bg: #f8fafc; --card: #ffffff; --text: #0f172a; --border: #e2e8f0; --brand: #F48C06; --error: #ef4444; --success: #10b981; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); padding: 40px; margin: 0; }
        h1 { display: flex; align-items: center; justify-content: space-between; gap: 15px; font-size: 2.2rem; margin-bottom: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: var(--card); padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid var(--border); }
        .stat-card h3 { margin: 0 0 10px 0; color: #64748B; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; }
        .stat-card .val { font-size: 2.5rem; font-weight: 800; color: var(--text); }
        
        .bulk-btn { background: var(--brand); color: white; padding: 12px 24px; border: none; border-radius: 8px; font-weight: bold; font-size: 1rem; cursor: pointer; box-shadow: 0 4px 10px rgba(0,0,0,0.1); transition: 0.2s; }
        .bulk-btn:hover { background: #e07f04; transform: translateY(-2px); }
        .bulk-btn:disabled { background: #cbd5e1; cursor: not-allowed; transform: none; box-shadow: none; }
        
        .scan-btn { background: #3b82f6; }
        .scan-btn:hover { background: #2563eb; }
        
        .table-container { background: var(--card); border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid var(--border); overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; text-align: left; }
        th, td { padding: 12px 15px; border-bottom: 1px solid var(--border); font-size:0.85rem; white-space: nowrap; }
        th { background: #f1f5f9; font-weight: 700; color: #475569; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.5px; }
        tr:last-child td { border-bottom: none; }
        tr:hover { background: #f8fafc; }
        
        .status-badge { display: inline-flex; padding: 4px 10px; border-radius: 999px; font-size: 0.75rem; font-weight: bold; }
        .status-ok { background: #d1fae5; color: #047857; }
        .status-err { background: #fee2e2; color: #b91c1c; }
        .error-list { margin: 0; padding: 0; list-style: none; font-size: 0.8rem; color: var(--error); }
        .error-list li { margin-bottom: 8px; display: flex; flex-direction: column; gap: 4px; }
        
        .action-btn { background: #1e293b; color: #38bdf8; padding: 5px 10px; border-radius: 6px; font-weight: bold; font-size: 0.75rem; cursor: pointer; border: 1px solid #334155; text-align: center; }
        .action-btn:hover { background: #0f172a; border-color: #38bdf8; }
        .action-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        
        #log-console { margin-top: 30px; background: #0f172a; color: #10b981; padding: 20px; border-radius: 8px; font-family: monospace; height: 200px; overflow-y: auto; font-size: 0.85rem; display: none; }
        
        /* Specific column formatting */
        .col-filename { max-width: 250px; overflow: hidden; text-overflow: ellipsis; }
        .text-center { text-align: center; }
    </style>
    <script>
        function logMsg(msg) {
            const con = document.getElementById('log-console');
            con.style.display = 'block';
            con.innerHTML += `<div>[${new Date().toLocaleTimeString()}] ${msg}</div>`;
            con.scrollTop = con.scrollHeight;
        }

        async function repair(slug, action, btnElement) {
            btnElement.disabled = true;
            btnElement.innerText = "⏳ Fixing...";
            logMsg(`Starting repair for ${slug}: ${action}`);
            
            try {
                const res = await fetch('/api/repair', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ slug, action })
                });
                const data = await res.json();
                if(data.success) {
                    btnElement.style.background = 'var(--success)';
                    btnElement.style.color = 'white';
                    btnElement.innerText = "✅ Fixed";
                    logMsg(`Successfully repaired ${slug}.\\n${data.logs || ""}`);
                } else {
                    btnElement.innerText = "❌ Failed";
                    logMsg(`Failed fixing ${slug}.\\n${data.logs || ""}`);
                }
            } catch(e) {
                btnElement.innerText = "❌ Error";
                logMsg(`Network error: ${e.message}`);
            }
        }

        async function bulkRepair() {
            const btn = document.getElementById('bulk-btn');
            btn.disabled = true;
            btn.innerText = "⏳ Bulk Repair in Progress (See Console)...";
            logMsg("Starting Bulk Repair. This may take a while...");
            
            try {
                const res = await fetch('/api/repair_bulk', { method: 'POST' });
                const data = await res.json();
                if(data.success) {
                    btn.innerText = "✅ Bulk Repair Complete!";
                    logMsg(`Bulk repair completed successfully! Auto-reloading...\\n${data.logs || ""}`);
                    setTimeout(() => window.location.reload(), 3000);
                } else {
                    btn.innerText = "❌ Bulk Repair Failed";
                    btn.disabled = false;
                    logMsg(`Bulk repair encounted an error.\\n${data.logs || ""}`);
                }
            } catch(e) {
                btn.innerText = "❌ Network Error";
                btn.disabled = false;
                logMsg(`Network error during bulk repair: ${e.message}`);
            }
        }
        
        async function scanAll() {
            const btn = document.getElementById('scan-btn');
            btn.disabled = true;
            btn.innerText = "⏳ Scanning...";
            logMsg("Starting full scan of all articles...");
            try {
                const res = await fetch('/api/scan', { method: 'POST' });
                const data = await res.json();
                if(data.success) {
                    btn.innerText = "✅ Scan Complete!";
                    logMsg(`Scan completed successfully! Auto-reloading...\\n${data.logs || ""}`);
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    btn.innerText = "❌ Scan Failed";
                    btn.disabled = false;
                    logMsg(`Scan logic encountered an error.\\n${data.logs || ""}`);
                }
            } catch(e) {
                btn.innerText = "❌ Network Error";
                btn.disabled = false;
                logMsg(`Network error during scan: ${e.message}`);
            }
        }
    </script>
</head>
<body>
    <h1>
        <span>🩺 Advanced Blog Health Dashboard</span>
        <div style="display:flex; gap:10px;">
            <button id="scan-btn" class="bulk-btn scan-btn" onclick="scanAll()">⚡ Scan All Articles</button>
            <button id="bulk-btn" class="bulk-btn" onclick="bulkRepair()">🚀 Bulk Repair All Issues</button>
        </div>
    </h1>
    <div id="log-console"></div>
"""

    total_articles = len(results)
    perfect_articles = len([r for r in results if not r['Errors']])
    total_errors = sum(1 for r in results for e in r['Errors'])
    
    html += f"""    <br>
    <div class="summary">
        <div class="stat-card"><h3>Total Articles</h3><div class="val">{total_articles}</div></div>
        <div class="stat-card"><h3>Perfect Score</h3><div class="val" style="color:var(--success)">{perfect_articles}</div></div>
        <div class="stat-card"><h3>Errors Found</h3><div class="val" style="color:var(--error)">{total_errors}</div></div>
    </div>
    
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>Filename</th>
                    <th>Title</th>
                    <th>Status / Actions</th>
                    <th>Focus Keyword</th>
                    <th>Word Count</th>
                    <th>Images</th>
                    <th>Avg Words/Img</th>
                    <th>Total Keywords</th>
                    <th>Int Links</th>
                    <th>Ext Links</th>
                    <th>Tags Count</th>
                    <th>Links to Arts</th>
                    <th>Freebies</th>
                    <th>Paid Prods</th>
                    <th>H2</th>
                    <th>H3</th>
                    <th>FAQ</th>
                    <th>Sugg Arts</th>
                    <th>Sugg Prem</th>
                    <th>Top Btn</th>
                    <th>Prev Btn</th>
                    <th>Next Btn</th>
                    <th>TOC</th>
                </tr>
            </thead>
            <tbody>
"""
            
    for row in results:
        title = row['Title']
        slug = row['Slug']
        imgs = row['Images']
        errs = row['Errors']
        
        if not errs:
            status_td = '<span class="status-badge status-ok">Perfect</span>'
        else:
            err_li = ""
            for e in errs:
                err_li += f"<li>{e} <button class='action-btn' onclick=\"repair('{slug}', '{e}', this)\">Fix Issue</button></li>"
            status_td = f"<span class='status-badge status-err'>{len(errs)} Issues</span><ul class='error-list'>{err_li}</ul>"
            
        html += f"""
                <tr>
                    <td class="col-filename" title="{slug}.html"><strong>{slug}.html</strong></td>
                    <td>{title}</td>
                    <td>{status_td}</td>
                    <td>{row['Focus Keyword']}</td>
                    <td class="text-center">{row['Word Count']}</td>
                    <td class="text-center" style="color:{'var(--success)' if imgs==6 else 'var(--error)'}; font-weight:bold;">{imgs} / 6</td>
                    <td class="text-center">{row['Avg Words/Img']}</td>
                    <td class="text-center">{row['Total Meta Keywords']}</td>
                    <td class="text-center">{row['Internal Links']}</td>
                    <td class="text-center">{row['External Links']}</td>
                    <td class="text-center">{row['Tags Count']}</td>
                    <td class="text-center">{row['Other Articles']}</td>
                    <td class="text-center">{row['Freebies Linking']}</td>
                    <td class="text-center">{row['Products Linking']}</td>
                    <td class="text-center">{row['H2']}</td>
                    <td class="text-center">{row['H3']}</td>
                    <td class="text-center">{row['FAQ']}</td>
                    <td class="text-center">{row['Suggested Articles']}</td>
                    <td class="text-center">{row['Suggested Premium Products']}</td>
                    <td class="text-center">{row['Scroll To Top Button']}</td>
                    <td class="text-center">{row['Prev Button']}</td>
                    <td class="text-center">{row['Next Button']}</td>
                    <td class="text-center">{row['TOC']}</td>
                </tr>
"""

    html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    return OUTPUT_HTML

def main():
    if not os.path.exists(ARTICLES_DIR):
        print(f"Error: Directory {ARTICLES_DIR} not found.")
        sys.exit(1)

    html_files = [f for f in os.listdir(ARTICLES_DIR) if f.endswith('.html')]
    results = []
    
    for filename in html_files:
        filepath = os.path.join(ARTICLES_DIR, filename)
        try:
            stats = analyze_article(filepath)
            results.append(stats)
        except Exception as e:
            print(f"ERROR on {filename}: {e}")

    out_path = build_dashboard(results)
    print("="*60)
    print(f"[OK] Interactive Dashboard generated successfully!")
    print(f"File: {out_path}")
    print("To make buttons functional, run: python scripts/dashboard_server.py")
    print("="*60)

if __name__ == "__main__":
    main()
