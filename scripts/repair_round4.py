"""
ROUND 4 — FORCE ALIGN all keywords. No conditions, just fix everything.
"""
import os, re, json, glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
POSTS_DIR = os.path.join(PROJECT_ROOT, "posts")

STOP_WORDS = {"the", "a", "an", "and", "or", "for", "to", "of", "in", "on", "at",
              "by", "is", "it", "its", "with", "your", "this", "that", "s"}


def extract_title(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()
    m = re.search(r'<title>([^<]+)</title>', html)
    return m.group(1).replace(" | Little Smart Genius", "").strip() if m else ""


def title_to_keyword(title):
    """Force-derive 3-5 word keyword from the first meaningful words of the title."""
    # Clean title
    clean = title.strip()
    # Remove subtitle after : or - or |
    clean = re.sub(r'\s*[:\-|]\s*[A-Z].*$', '', clean)
    words = clean.split()
    
    # Filter to meaningful words, keeping word order
    meaningful = []
    for w in words:
        if w.lower() not in STOP_WORDS:
            meaningful.append(w.lower())
        elif meaningful:  # Keep stop words between meaningful words
            meaningful.append(w.lower())
    
    # Trim trailing stop words
    while meaningful and meaningful[-1] in STOP_WORDS:
        meaningful.pop()
    
    # Take 3-5 words
    if len(meaningful) > 5:
        return " ".join(meaningful[:5])
    elif len(meaningful) >= 3:
        return " ".join(meaningful)
    else:
        # Fallback: just use first 4 title words
        return " ".join(words[:4]).lower()


def get_json(slug):
    for jf in glob.glob(os.path.join(POSTS_DIR, "*.json")):
        bn = os.path.basename(jf)
        parts = bn.rsplit("-", 1)
        js = parts[0] if len(parts) > 1 and parts[1].replace(".json", "").isdigit() else bn.replace(".json", "")
        if js == slug:
            return jf
    return None


def gen_longtail_kws(kw, title):
    kws = set()
    kws.add(kw)
    tw = title.lower().split()
    for i in range(len(tw) - 2):
        p = " ".join(tw[i:i+3])
        if not all(w in STOP_WORDS for w in p.split()):
            kws.add(p)
        if i + 4 <= len(tw):
            kws.add(" ".join(tw[i:i+4]))
    b = kw.split()[:2]
    bs = " ".join(b)
    for e in ["printable %s worksheets" % bs, "free %s activities" % bs, 
              "best %s for kids" % bs, "%s learning resources" % bs]:
        if len(e.split()) >= 3:
            kws.add(e)
    return [k for k in kws if len(k.split()) >= 3][:10]


def main():
    print("=" * 60)
    print("  ROUND 4 — FORCE ALIGN ALL KEYWORDS")
    print("=" * 60)
    
    fixes = 0
    for fp in sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html"))):
        slug = os.path.basename(fp).replace(".html", "")
        title = extract_title(fp)
        jp = get_json(slug)
        
        if not jp:
            print("  [SKIP] %s — no JSON" % slug[:40])
            continue
        
        with open(jp, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # FORCE derive keyword from title
        new_kw = title_to_keyword(title)
        kw_short = " ".join(new_kw.split()[:2])
        
        # Check if current keyword's first 2 words appear in title's first 3 words
        title_first3 = " ".join(title.lower().split()[:3])
        old_kw = data.get("primary_keyword", "")
        old_short = " ".join(old_kw.lower().split()[:2]) if old_kw else ""
        
        json_changed = False
        html_changed = False
        
        if not old_short or old_short not in title_first3:
            data["primary_keyword"] = new_kw
            json_changed = True
        
        # Update keywords to long-tail
        kw_str = data.get("keywords", "")
        if isinstance(kw_str, list):
            kw_str = ", ".join([str(k) for k in kw_str])
        kw_list = [k.strip() for k in kw_str.split(",") if k.strip()]
        short_kws = [k for k in kw_list if len(k.split()) < 3]
        if short_kws or not kw_list:
            data["keywords"] = ", ".join(gen_longtail_kws(data["primary_keyword"], title))
            json_changed = True
        
        if json_changed:
            with open(jp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Fix HTML meta
        with open(fp, "r", encoding="utf-8") as f:
            html = f.read()
        orig = html
        
        pk = data["primary_keyword"]
        kw_s = " ".join(pk.split()[:3])
        
        # Fix meta keywords
        new_meta_kws = gen_longtail_kws(pk, title)
        if new_meta_kws:
            m = re.search(r'<meta\s+name="keywords"\s+content="[^"]*"', html)
            if m:
                html = html[:m.start()] + '<meta name="keywords" content="%s"' % ", ".join(new_meta_kws) + html[m.end():]
        
        # Fix meta description — ensure kw_s is in it
        dm = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html)
        if dm and kw_s.lower() not in dm.group(1).lower():
            od = dm.group(1)
            # Try to naturally weave in
            nd = "Discover %s: %s" % (kw_s.title(), od)
            if len(nd) > 155:
                nd = nd[:152] + "..."
            html = html.replace(dm.group(0), '<meta name="description" content="%s"' % nd, 1)
        
        if html != orig:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(html)
            html_changed = True
        
        if json_changed or html_changed:
            fixes += 1
            print("  [FIX] %s -> KW: '%s'" % (slug[:40], pk[:30]))
    
    print("\n  ROUND 4 COMPLETE: %d articles updated" % fixes)


if __name__ == "__main__":
    main()
