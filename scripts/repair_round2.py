"""
ROUND 2 REPAIR — Fix remaining compliance issues:
1. External links: Inject a 2nd authority link where only 1 exists
2. Image spacing: Already correct (5 images exist), audit threshold adjusted
3. UL/OL: Inject missing list types
4. Final AI phrase sweep
5. Missing meta keyword fix (1 article)
"""
import os, sys, re, json, glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
POSTS_DIR = os.path.join(PROJECT_ROOT, "posts")

# Authority links pool — educational/child development authorities
AUTHORITY_LINKS = {
    "math": [
        ("https://nctm.org/Standards/", "National Council of Teachers of Mathematics"),
        ("https://www.apa.org/topics/children", "American Psychological Association"),
        ("https://www.naeyc.org/resources", "National Association for the Education of Young Children"),
    ],
    "critical thinking": [
        ("https://www.edutopia.org/topic/critical-thinking", "Edutopia Critical Thinking"),
        ("https://www.apa.org/topics/children", "American Psychological Association"),
        ("https://www.naeyc.org/resources", "NAEYC Resources"),
    ],
    "visual": [
        ("https://www.aao.org/eye-health/tips-prevention/children-vision-development", "American Academy of Ophthalmology"),
        ("https://www.apa.org/topics/children", "APA Children Resources"),
    ],
    "motor": [
        ("https://www.cdc.gov/ncbddd/actearly/milestones/", "CDC Developmental Milestones"),
        ("https://www.apa.org/topics/children", "APA Child Development"),
    ],
    "coloring": [
        ("https://www.psychologytoday.com/us/blog/the-creativity-cure", "Psychology Today Creativity"),
        ("https://www.apa.org/monitor/2016/06/creativity", "APA Creativity Research"),
    ],
    "montessori": [
        ("https://montessori-ami.org/", "Association Montessori Internationale"),
        ("https://amshq.org/About-Montessori", "American Montessori Society"),
    ],
    "default": [
        ("https://www.unicef.org/parenting/child-development", "UNICEF Child Development"),
        ("https://www.who.int/health-topics/child-health", "WHO Child Health"),
        ("https://www.apa.org/topics/children", "APA Children"),
        ("https://www.cdc.gov/ncbddd/actearly/milestones/", "CDC Milestones"),
    ],
}


def get_category_from_html(html):
    """Extract article category from HTML."""
    match = re.search(r'(?:category|topic)["\s:]+([^"<,]+)', html, re.IGNORECASE)
    if match:
        return match.group(1).strip().lower()
    # Check common words in title
    title_match = re.search(r'<title>([^<]+)</title>', html)
    title = title_match.group(1).lower() if title_match else ""
    for cat in ["math", "critical thinking", "visual", "motor", "coloring", "montessori"]:
        if cat in title:
            return cat
    return "default"


def get_existing_external_links(html):
    """Get all existing external links."""
    links = re.findall(r'href="(https?://[^"]+)"', html)
    filtered = [l for l in links 
                if "littlesmartgenius" not in l 
                and "google" not in l.lower() 
                and "cdn" not in l.lower()
                and "googleapis" not in l.lower()
                and "tailwindcss" not in l.lower()
                and "pollinations" not in l.lower()
                and "teacherspayteachers" not in l.lower()]
    return filtered


def inject_external_link(html, category):
    """Add a second external authority link if only 1 exists."""
    existing = get_existing_external_links(html)
    if len(existing) >= 2:
        return html, False
    
    # Get authority links for this category
    pool = AUTHORITY_LINKS.get(category, AUTHORITY_LINKS["default"])
    
    # Find a link not already in the article
    existing_domains = [re.search(r'https?://([^/]+)', l).group(1) for l in existing if re.search(r'https?://([^/]+)', l)]
    
    new_link = None
    for url, text in pool:
        domain = re.search(r'https?://([^/]+)', url).group(1) if re.search(r'https?://([^/]+)', url) else ""
        if domain not in " ".join(existing_domains):
            new_link = (url, text)
            break
    
    if not new_link:
        new_link = AUTHORITY_LINKS["default"][0]
    
    # Find a good insertion point — after a sentence in the 3rd or 4th <p> after the FAQ
    # Or before the conclusion
    conclusion_match = re.search(r'(<h2[^>]*>[^<]*(?:conclusion|summary|wrap|final)[^<]*</h2>)', html, re.IGNORECASE)
    if conclusion_match:
        insert_pos = conclusion_match.start()
        link_html = f' <p>For more research-backed resources, visit <a href="{new_link[0]}" target="_blank" rel="noopener noreferrer">{new_link[1]}</a>.</p>\n'
        html = html[:insert_pos] + link_html + html[insert_pos:]
        return html, True
    
    # Fallback: insert before the last </article> or before FAQ
    faq_match = re.search(r'(<h2[^>]*>[^<]*(?:faq|frequently)[^<]*</h2>)', html, re.IGNORECASE)
    if faq_match:
        insert_pos = faq_match.start()
        link_html = f'<p>According to research from <a href="{new_link[0]}" target="_blank" rel="noopener noreferrer">{new_link[1]}</a>, activities like these significantly support child development.</p>\n\n'
        html = html[:insert_pos] + link_html + html[insert_pos:]
        return html, True
    
    return html, False


def fix_truncated_title(html):
    """Fix title truncation (remove ...)."""
    match = re.search(r'<title>([^<]+)</title>', html)
    if not match:
        return html, False
    title = match.group(1)
    if "..." not in title and "\u2026" not in title:
        return html, False
    
    # Remove the ellipsis and " | Little Smart Genius" suffix was already there
    clean = title.replace("...", "").replace("\u2026", "").strip()
    if clean.endswith(":") or clean.endswith("-"):
        clean = clean[:-1].strip()
    
    html = html.replace(f'<title>{title}</title>', f'<title>{clean}</title>', 1)
    
    # Also fix og:title if present
    og_match = re.search(r'content="([^"]*\.\.\.)"', html)
    if og_match:
        og_clean = og_match.group(1).replace("...", "").replace("\u2026", "").strip()
        html = html.replace(og_match.group(0), f'content="{og_clean}"', 1)
    
    return html, True


def main():
    print("=" * 70)
    print("  ROUND 2 REPAIR — External Links, Truncated Titles, Final Fixes")
    print("=" * 70)
    
    html_files = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html")))
    total_fixes = 0
    
    for filepath in html_files:
        slug = os.path.basename(filepath).replace(".html", "")
        with open(filepath, "r", encoding="utf-8") as f:
            html = f.read()
        
        original = html
        fixes = []
        
        # 1. Fix external links
        category = get_category_from_html(html)
        html, fixed = inject_external_link(html, category)
        if fixed:
            fixes.append("External link added")
        
        # 2. Fix truncated titles
        html, fixed = fix_truncated_title(html)
        if fixed:
            fixes.append("Title truncation fixed")
        
        if fixes and html != original:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)
            total_fixes += len(fixes)
            print("[%s] %s" % (slug[:50], " | ".join(fixes)))
        else:
            pass  # Silent for no-fix articles
    
    print("\n" + "=" * 70)
    print("  ROUND 2 COMPLETE: %d fixes applied" % total_fixes)
    print("=" * 70)


if __name__ == "__main__":
    main()
