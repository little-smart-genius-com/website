import os
import re
import csv
import json
from collections import defaultdict
from typing import Dict, List, Any

# Ensure BeautifulSoup is installed for robust HTML parsing
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("BeautifulSoup4 is required. Please run: pip install beautifulsoup4")
    import sys
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
OUTPUT_CSV = os.path.join(PROJECT_ROOT, "blog_health_report.csv")

def extract_text_from_html(soup: BeautifulSoup) -> str:
    # Remove script, style, and comments
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text(separator=' ')
    # Breakdown into words
    return re.sub(r'\s+', ' ', text).strip()

def analyze_article(filepath: str) -> Dict[str, Any]:
    with open(filepath, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    filename = os.path.basename(filepath)
    
    # 1. Main Elements
    # Title
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else "N/A"
    
    # Meta Keywords (Often used as focus keyword)
    meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
    keywords = meta_keywords['content'] if meta_keywords and meta_keywords.has_attr('content') else ""
    keyword_count = len([k for k in keywords.split(',') if k.strip()]) if keywords else 0
    focus_keyword = keywords.split(',')[0].strip() if keywords else "N/A"

    # Article Content specific extraction
    article_content_div = soup.find('div', class_='article-content')
    
    # 2. Word Count
    # We count words mainly in the article content if available, else the whole body
    if article_content_div:
        text_content = extract_text_from_html(article_content_div)
    else:
        text_content = extract_text_from_html(soup.find('body') or soup)
    words = [w for w in re.findall(r'\b\w+\b', text_content)]
    word_count = len(words)

    # 3. Images and Spacing
    # Target images inside the article content to analyze spacing
    images = article_content_div.find_all('img') if article_content_div else soup.find_all('img')
    image_count = len(images)
    
    # Calculate spacing between images (average words)
    avg_words_between_images = word_count // (image_count + 1) if image_count > 0 else word_count

    # 4. Links Analysis
    # We find all <a> tags
    all_links = soup.find_all('a', href=True)
    internal_links = 0
    external_links = 0
    links_to_other_articles = 0
    links_to_freebies = 0
    links_to_paid_products = 0
    
    for link in all_links:
        href = link['href'].lower()
        if href.startswith('http') and 'littlesmartgenius.com' not in href:
            if 'teacherspayteachers.com' in href:
                links_to_paid_products += 1
                external_links += 1
            else:
                external_links += 1
        else:
            internal_links += 1
            if 'articles/' in href or href.endswith('.html') and href != 'index.html' and 'blog' not in href and 'products' not in href and 'freebies' not in href:
                # Basic heuristic for other articles
                links_to_other_articles += 1
            if 'freebies.html' in href or '/freebies' in href:
                links_to_freebies += 1
            if 'products.html' in href or '/products' in href:
                links_to_paid_products += 1

    # 5. Related Tags
    # Usually found at the bottom with #
    related_tags = []
    for link in all_links:
        if link.get_text(strip=True).startswith('#'):
            related_tags.append(link.get_text(strip=True))
    related_tags_count = len(related_tags)

    # 6. Headings
    h2_count = len(soup.find_all('h2'))
    h3_count = len(soup.find_all('h3'))

    # 7. FAQ Presence
    # FAQs are usually inside <details> tags or an H2 named "Frequently Asked Questions"
    has_faq = "Yes" if soup.find('details') or soup.find(lambda tag: tag.name == "h2" and "frequently asked questions" in tag.text.lower()) else "No"

    # 8. Suggested Articles (You Might Also Like)
    # Check for the specific H3 or container
    related_articles_heading = soup.find(lambda tag: tag.name in ["h2", "h3"] and "You Might Also Like" in tag.text)
    suggested_articles_count = 0
    if related_articles_heading:
        parent_div = related_articles_heading.find_parent('div', class_='mt-16')
        if parent_div:
            # Count the blocks/links inside the related articles grid
            grid = parent_div.find('div', class_=re.compile(r'grid'))
            if grid:
                suggested_articles_count = len(grid.find_all('a'))
                
    # 9. Suggested Premium Products (TPT Card)
    # Check for "Recommended Resource" text
    tpt_resource_span = soup.find(lambda tag: tag.name == "span" and "Recommended Resource" in tag.text)
    suggested_premium_products_count = 1 if tpt_resource_span else 0

    # 10. Buttons & Navigation Elements
    scroll_to_top = "Yes" if soup.find(id="scrollTopBtn") else "No"
    prev_button = "Yes" if soup.find(id="prevArticleNav") or soup.find(class_="article-nav-prev") else "No"
    next_button = "Yes" if soup.find(id="nextArticleNav") or soup.find(class_="article-nav-next") else "No"
    
    # 11. Table of Contents
    toc_container = soup.find(class_="toc-container")
    table_of_contents = "Yes" if toc_container else "No"

    return {
        "Filename": filename,
        "Title": title,
        "Focus Keyword": focus_keyword,
        "Word Count": word_count,
        "Number of Images": image_count,
        "Avg Words Between Images": avg_words_between_images,
        "Total Meta Keywords": keyword_count,
        "Total Internal Links": internal_links,
        "Total External Links": external_links,
        "Related Tags Count": related_tags_count,
        "Links to Other Articles": links_to_other_articles,
        "Links to Freebies": links_to_freebies,
        "Links to Paid Products": links_to_paid_products,
        "H2 Count": h2_count,
        "H3 Count": h3_count,
        "Has FAQ": has_faq,
        "Suggested Articles": suggested_articles_count,
        "Suggested Premium Products": suggested_premium_products_count,
        "Scroll To Top Button": scroll_to_top,
        "Prev Button": prev_button,
        "Next Button": next_button,
        "Table of Contents": table_of_contents
    }

def main():
    print("="*60)
    print("    LITTLE SMART GENIUS - BLOG HEALTH CHECK")
    print("="*60)
    
    if not os.path.exists(ARTICLES_DIR):
        print(f"Error: Directory {ARTICLES_DIR} not found.")
        sys.exit(1)

    html_files = [f for f in os.listdir(ARTICLES_DIR) if f.endswith('.html')]
    print(f"Found {len(html_files)} articles to audit. Processing...\n")

    results = []
    for i, filename in enumerate(html_files, 1):
        filepath = os.path.join(ARTICLES_DIR, filename)
        try:
            stats = analyze_article(filepath)
            results.append(stats)
            # Print brief status
            print(f"[{i:02d}/{len(html_files)}] Audited: {filename}")
        except Exception as e:
            print(f"[{i:02d}/{len(html_files)}] ERROR on {filename}: {e}")

    if not results:
        print("\nNo results generated.")
        return

    # Write to CSV
    headers = list(results[0].keys())
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n============================================================")
    print(f"✅ Audit Complete! Report saved to: {OUTPUT_CSV}")
    print(f"============================================================")
    
    # Print a quick summary of potential issues
    print("\n--- Quick Diagnostic Summary ---")
    missing_faqs = [r["Filename"] for r in results if r["Has FAQ"] == "No"]
    missing_toc = [r["Filename"] for r in results if r["Table of Contents"] == "No"]
    missing_tpt = [r["Filename"] for r in results if r["Suggested Premium Products"] == 0]
    duplicate_related = [r["Filename"] for r in results if r["Suggested Articles"] > 3]
    missing_nav = [r["Filename"] for r in results if r["Prev Button"] == "No" or r["Next Button"] == "No"]
    
    if missing_faqs:
        print(f"Missing FAQ     : {len(missing_faqs)} articles")
    if missing_toc:
        print(f"Missing TOC     : {len(missing_toc)} articles")
    if missing_tpt:
        print(f"Missing Product : {len(missing_tpt)} articles")
    if duplicate_related:
        print(f"Duplicate 'You Might Also Like': {len(duplicate_related)} articles")
    if missing_nav:
        print(f"Missing Prev/Next Navigation   : {len(missing_nav)} articles")

    print("\nRun this script anytime to get a fresh health check of all articles.")

if __name__ == "__main__":
    main()
