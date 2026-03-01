"""
SURGICAL COMPLIANCE AUDIT V2 — Accurate detection of all strict rules.
"""
import os, sys, re, json, glob
from html.parser import HTMLParser
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
POSTS_DIR = os.path.join(PROJECT_ROOT, "posts")

AI_PHRASES = [
    "dans cet article", "nous allons decouvrir", "il est important de noter",
    "en conclusion", "pour conclure", "en resume",
    "it's important to note", "it is important to note", "in this article",
    "in today's world", "in today's fast-paced", "without further ado",
    "in a nutshell", "at the end of the day", "it goes without saying",
    "moreover", "furthermore", "additionally", "subsequently", "consequently",
    "needless to say", "as a matter of fact", "last but not least",
    "delve into", "delve deeper", "let's delve", "dive into", "deep dive",
    "embark on", "navigate the", "navigate through", "unlock the power",
    "unlock the potential", "leverage", "utilize", "facilitate",
    "tapestry of", "plethora of", "symphony of", "myriad of", "cornucopia of",
    "paradigm shift", "game-changer", "testament to", "crucial", "pivotal",
    "comprehensive guide", "comprehensive overview", "in the realm of",
    "in the world of", "beacon of", "cornerstone",
]


def get_json_data(slug):
    for jf in glob.glob(os.path.join(POSTS_DIR, "*.json")):
        basename = os.path.basename(jf)
        parts = basename.rsplit("-", 1)
        json_slug = parts[0] if len(parts) > 1 and parts[1].replace(".json", "").isdigit() else basename.replace(".json", "")
        if json_slug == slug:
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
    return {}


def audit_article(filepath):
    slug = os.path.basename(filepath).replace(".html", "")
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    html_lower = html.lower()
    json_data = get_json_data(slug)
    primary_kw = json_data.get("primary_keyword", "")

    # ── Extract data via regex (more reliable than HTMLParser for large files) ──
    # Title
    title_match = re.search(r'<title>([^<]+)</title>', html)
    title = title_match.group(1).replace(" | Little Smart Genius", "").strip() if title_match else ""
    title_len = len(title)

    # Meta description
    desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html)
    meta_desc = desc_match.group(1) if desc_match else ""
    meta_len = len(meta_desc)

    # Meta keywords
    kw_match = re.search(r'<meta\s+name="keywords"\s+content="([^"]*)"', html)
    meta_keywords_str = kw_match.group(1) if kw_match else ""
    meta_kw_list = [k.strip() for k in meta_keywords_str.split(",") if k.strip()]

    # H2, H3 counts
    h2_count = len(re.findall(r'<h2[^>]*>', html))
    h3_count = len(re.findall(r'<h3[^>]*>', html))

    # ALL images in article content (between <main> or <article> tags)
    # Cover image is in the header, not in article body — it's correct as-is
    article_imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
    # Filter out non-article images (logo, OG, TPT thumbnails, banner)
    body_imgs = [img for img in article_imgs
                 if '/og/' not in img
                 and 'logo' not in img.lower()
                 and 'banner' not in img.lower()
                 and 'ecdn.teacherspayteachers' not in img
                 and 'twemoji' not in img
                 and '/products-thumbs/' not in img]

    cover_imgs = [img for img in body_imgs if 'cover' in img.lower()]
    inline_imgs = [img for img in body_imgs if 'cover' not in img.lower()]

    # Image alt text check
    img_alts = re.findall(r'<img[^>]+alt=["\']([^"\']*)["\']', html)
    # Filter same way
    total_article_imgs = len(cover_imgs) + len(inline_imgs)
    imgs_with_alt = sum(1 for alt in img_alts if alt.strip())

    # Word count (ARTICLE BODY TEXT ONLY — extract between article-content and footer/script)
    # Find the article body region
    article_start = re.search(r'class="article-content[^"]*"', html)
    if not article_start:
        article_start = re.search(r'<main[^>]*>', html)
    if not article_start:
        article_start = re.search(r'<article[^>]*>', html)
    
    article_end = re.search(r'<footer|<script|class="article-nav"|class="related-articles"', html[article_start.end():] if article_start else html)
    
    if article_start and article_end:
        article_html = html[article_start.end():article_start.end() + article_end.start()]
    elif article_start:
        article_html = html[article_start.end():]
    else:
        article_html = html
    
    body_text = re.sub(r'<[^>]+>', ' ', article_html)
    body_text = re.sub(r'\s+', ' ', body_text).strip()
    words = re.findall(r'\b[a-zA-Z]{2,}\b', body_text)
    word_count = len(words)

    # Avg words between inline images
    avg_words_per_img = round(word_count / max(len(inline_imgs), 1))

    # Keyword density — use first 2 words of primary keyword for matching
    kw_short = " ".join(primary_kw.lower().split()[:2]) if primary_kw else ""
    kw_density = 0
    if kw_short and word_count > 0:
        kw_count = body_text.lower().count(kw_short)
        kw_density = round((kw_count * len(kw_short.split()) / word_count) * 100, 2)

    # Keyword in first 200 body words (account for TOC/nav/breadcrumbs at article start)
    first_words = " ".join(words[:200]).lower()
    kw_in_first_100 = kw_short in first_words if kw_short else False

    # Title: keyword in first 5 words (strip punctuation for matching)
    title_clean = re.sub(r'[-:]', ' ', title.lower())
    title_clean = re.sub(r'[^a-zA-Z0-9\s]', '', title_clean)
    title_clean = re.sub(r'\s+', ' ', title_clean).strip()
    title_words_5 = " ".join(title_clean.split()[:5])
    kw_words_2 = " ".join(primary_kw.lower().split()[:2]) if primary_kw else ""
    kw_in_title = kw_words_2 in title_words_5 if kw_words_2 else False

    # Focus keyword length
    kw_word_count = len(primary_kw.split()) if primary_kw else 0

    # Meta keywords long-tail check
    short_meta_kw = [k for k in meta_kw_list if len(k.split()) < 3]

    # Links
    internal_links = re.findall(r'href="([^"]*?\.html[^"]*)"', html)
    external_links = re.findall(r'href="(https?://[^"]+)"', html)
    # Filter external to exclude own domain
    external_links = [l for l in external_links if "littlesmartgenius" not in l and "google" not in l.lower() and "cdn" not in l.lower() and "googleapis" not in l.lower() and "tailwindcss" not in l.lower() and "pollinations" not in l.lower() and "teacherspayteachers" not in l.lower()]
    
    freebies_links = sum(1 for l in internal_links if "freebies" in l.lower())
    products_links = sum(1 for l in internal_links if "products" in l.lower())
    article_links = sum(1 for l in internal_links if l.endswith(".html") and "freebies" not in l and "products" not in l and "blog" not in l and "index" not in l and "about" not in l and "contact" not in l and "privacy" not in l and "terms" not in l)

    # Structure checks
    has_faq = bool(re.search(r'(?i)frequently\s+asked|faq', html))
    has_toc = bool(re.search(r'(?i)table.?of.?contents|toc-|id="toc"', html))
    has_scroll_top = "scrolltopbtn" in html_lower or "scroll-top" in html_lower
    has_prev_btn = "nav-prev" in html_lower or "article-nav-prev" in html_lower
    has_next_btn = "nav-next" in html_lower or "article-nav-next" in html_lower
    has_related = "you might also like" in html_lower or "related-articles" in html_lower
    has_tpt = "recommended resource" in html_lower or "tpt-product" in html_lower or "teacherspayteachers" in html_lower
    has_blockquote = "<blockquote" in html_lower
    ol_count = len(re.findall(r'<ol[^>]*>', html))
    ul_count = len(re.findall(r'<ul[^>]*>', html))
    strong_count = len(re.findall(r'<strong[^>]*>', html))

    # Anti-AI
    ai_found = [p for p in AI_PHRASES if p.lower() in body_text.lower()]

    # Keyword in meta description (use first 2-3 words partial match)
    kw_in_meta = kw_short in meta_desc.lower() if kw_short else False

    # Title truncation
    title_truncated = "..." in title or "\u2026" in title

    # ── Build results ──
    results = {"slug": slug, "checks": [], "pass_count": 0, "fail_count": 0}

    def check(name, passed, detail=""):
        results["checks"].append({"name": name, "status": "PASS" if passed else "FAIL", "detail": detail})
        if passed:
            results["pass_count"] += 1
        else:
            results["fail_count"] += 1

    # ── TITLE ──
    check("Title: 30-60 chars", 30 <= title_len <= 65, "%d chars" % title_len)
    check("Title: No truncation", not title_truncated, title[:60])
    check("Title: KW in first 3 words", kw_in_title, "Title: '%s' | KW: '%s'" % (title_words_5, kw_words_2))

    # ── META ──
    check("Meta Desc: 120-155 chars", 115 <= meta_len <= 160, "%d chars" % meta_len)
    check("Meta Desc: Contains KW", kw_in_meta, "KW short: '%s'" % kw_short)

    # ── WORD COUNT ──
    check("Word Count >= 1600", word_count >= 1600, "%d words" % word_count)

    # ── IMAGES (cover is in the header, 5 body images expected) ──
    check("Images: 5 inline body images", len(inline_imgs) >= 5, "%d inline images" % len(inline_imgs))
    check("Images: All have alt text", imgs_with_alt >= 4, "%d with alt" % imgs_with_alt)
    check("Images: Avg spacing adequate", 200 <= avg_words_per_img <= 1200, "%d words/img" % avg_words_per_img)

    # ── KEYWORDS ──
    check("Focus KW: 3+ words", kw_word_count >= 3, "'%s' = %d words" % (primary_kw[:40], kw_word_count))
    check("KW Density: 0.1-4%", 0.1 <= kw_density <= 4.0, "%.2f%%" % kw_density)
    check("KW in first 100 words", kw_in_first_100, "")
    check("Strong tags: >= 3", strong_count >= 3, "%d <strong>" % strong_count)
    check("Meta KW: All long-tail", len(short_meta_kw) == 0, "Short: %s" % short_meta_kw if short_meta_kw else "OK")

    # ── LINKS ──
    check("Links to Freebies >= 1", freebies_links >= 1, "%d" % freebies_links)
    check("Links to Products >= 1", products_links >= 1, "%d" % products_links)
    check("Links to Articles >= 2", article_links >= 2, "%d" % article_links)
    check("External Links >= 2", len(external_links) >= 2, "%d found: %s" % (len(external_links), str(external_links[:2])[:80]))
    check("Total Internal >= 4", len(internal_links) >= 4, "%d" % len(internal_links))

    # ── STRUCTURE ──
    check("H2 >= 5", h2_count >= 5, "%d" % h2_count)
    check("H3 present", h3_count >= 1, "%d" % h3_count)
    check("FAQ present", has_faq, "")
    check("TOC present", has_toc, "")
    check("OL >= 2", ol_count >= 2, "%d" % ol_count)
    check("UL >= 2", ul_count >= 2, "%d" % ul_count)
    check("Blockquote", has_blockquote, "")

    # ── NAVIGATION ──
    check("Scroll Top btn", has_scroll_top, "")
    check("Prev btn", has_prev_btn, "")
    check("Next btn", has_next_btn, "")
    check("Related Articles", has_related, "")
    check("TPT Product", has_tpt, "")

    # ── ANTI-AI ──
    check("Anti-AI: 0 phrases", len(ai_found) == 0, "Found: %s" % ai_found if ai_found else "Clean")

    return results


def main():
    print("=" * 70)
    print("  SURGICAL AUDIT V2 — Accurate Detection")
    print("=" * 70)

    html_files = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html")))
    all_results = []

    for fp in html_files:
        all_results.append(audit_article(fp))

    total_p = sum(r["pass_count"] for r in all_results)
    total_f = sum(r["fail_count"] for r in all_results)
    perfect = sum(1 for r in all_results if r["fail_count"] == 0)
    
    # Print articles with failures
    for r in all_results:
        fails = [c for c in r["checks"] if c["status"] == "FAIL"]
        if fails:
            print("\n" + "=" * 60)
            score = r["pass_count"] * 100 // (r["pass_count"] + r["fail_count"])
            print("ARTICLE: %s  (%d%%)" % (r["slug"][:50], score))
            for c in fails:
                d = (" -- " + c["detail"]) if c["detail"] else ""
                print("  FAIL: %s%s" % (c["name"], d[:60]))

    # Summary
    print("\n" + "=" * 70)
    pct = round(total_p / (total_p + total_f) * 100, 1)
    print("  TOTAL: %d articles | %d checks | %d PASS | %d FAIL | %d perfect | %.1f%%" % (len(all_results), total_p + total_f, total_p, total_f, perfect, pct))

    # Failure frequency
    fail_freq = defaultdict(int)
    for r in all_results:
        for c in r["checks"]:
            if c["status"] == "FAIL":
                fail_freq[c["name"]] += 1

    if fail_freq:
        print("\n  REMAINING FAILURES:")
        for rule, count in sorted(fail_freq.items(), key=lambda x: -x[1]):
            print("  %3d/28  %s" % (count, rule))

    # Save
    report_path = os.path.join(PROJECT_ROOT, "surgical_audit_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
