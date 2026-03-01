"""
ROUND 7 — LASER TARGETED: Fix exact articles with exact issues
"""
import os, re, json, glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
POSTS_DIR = os.path.join(PROJECT_ROOT, "posts")


def get_json(slug):
    for jf in glob.glob(os.path.join(POSTS_DIR, "*.json")):
        bn = os.path.basename(jf)
        parts = bn.rsplit("-", 1)
        js = parts[0] if len(parts) > 1 and parts[1].replace(".json","").isdigit() else bn.replace(".json","")
        if js == slug:
            return jf
    return None


# Articles that need KW in first 100 words
KW_INJECT = [
    "boost-your-childs-critical-thinking-with-this-activity-book",
    "boost-your-childs-logic-skills-with-skyscraper",
    "engaging-classroom-activities-ultimate-early-learner-ess",
    "how-coloring-builds-cognitive-skills-the-ultimate-guide",
    "mazes-the-ultimate-problem-solving-guide-for-kids",
    "unlock-your-childs-strategic-thinking-with-four-in-a-row",
    "use-a-freebie-pack-to-boost-learning-skills-ultimate-guide",
]


def main():
    print("ROUND 7 — LASER TARGETED FIXES")
    print("=" * 50)
    fixes = 0
    
    for slug in KW_INJECT:
        fp = os.path.join(ARTICLES_DIR, slug + ".html")
        if not os.path.exists(fp):
            print("  [SKIP] %s not found" % slug[:40])
            continue
        
        jp = get_json(slug)
        if not jp:
            print("  [SKIP] no JSON for %s" % slug[:40])
            continue
        
        with open(jp, "r", encoding="utf-8") as f:
            data = json.load(f)
        pk = data.get("primary_keyword", "")
        if not pk:
            continue
        
        kw_2 = " ".join(pk.lower().split()[:2])
        
        with open(fp, "r", encoding="utf-8") as f:
            html = f.read()
        
        # Check if KW already in first 100 words
        text = re.sub(r'<[^>]+>', ' ', html)
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text)
        first100 = " ".join(words[:100]).lower()
        
        if kw_2 in first100:
            print("  [OK] %s already has KW" % slug[:40])
            continue
        
        # Find the VERY FIRST <p> tag in the article (not in head/nav)
        # Search after the first <h1> or <h2> or article tag
        body_start = re.search(r'(?:<article|<main|<h1|<h2)', html)
        if not body_start:
            body_start = re.search(r'</header>', html)
        
        search_from = body_start.end() if body_start else 0
        
        # Find first <p> with actual text content (not empty, not just whitespace)
        p_iter = re.finditer(r'<p[^>]*>(.*?)</p>', html[search_from:], re.DOTALL)
        for pm in p_iter:
            p_text = re.sub(r'<[^>]+>', '', pm.group(1)).strip()
            if len(p_text) > 50:  # Has real content
                abs_start = search_from + pm.start()
                abs_end = search_from + pm.end()
                old_p = html[abs_start:abs_end]
                
                # Inject keyword naturally as the second sentence
                kw_sentence = ' When it comes to <strong>%s</strong>, getting started early makes all the difference.' % pk.lower()
                
                # Find first period in old_p content
                inner = pm.group(1)
                dot_pos = inner.find(". ")
                if dot_pos != -1:
                    new_inner = inner[:dot_pos+1] + kw_sentence + inner[dot_pos+1:]
                else:
                    new_inner = inner + kw_sentence
                
                new_p = '<p>' + new_inner + '</p>'  # Simplified but functional
                # We need to be careful with attributes on <p>
                p_open_end = old_p.find(">") + 1
                p_open_tag = old_p[:p_open_end]
                html = html[:abs_start] + p_open_tag + new_inner + '</p>' + html[abs_end:]
                
                print("  [INJECT] %s: KW '%s' added" % (slug[:35], kw_2))
                fixes += 1
                break
        
        with open(fp, "w", encoding="utf-8") as f:
            f.write(html)
    
    # ── Fix mazes article title/KW alignment ──
    mazes_fp = os.path.join(ARTICLES_DIR, "mazes-the-ultimate-problem-solving-guide-for-kids.html")
    mazes_jp = get_json("mazes-the-ultimate-problem-solving-guide-for-kids")
    if mazes_jp:
        with open(mazes_jp, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Change KW to match title "Mazes: The Ultimate..."
        data["primary_keyword"] = "mazes ultimate problem solving guide"
        with open(mazes_jp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("  [FIX KW] mazes -> 'mazes ultimate problem solving guide'")
    
    # ── Fix homeschool KW density ──
    hs_fp = os.path.join(ARTICLES_DIR, "homeschool-printables-ultimate-guide-for-parents-teachers.html")
    hs_jp = get_json("homeschool-printables-ultimate-guide-for-parents-teachers")
    if hs_jp:
        with open(hs_jp, "r", encoding="utf-8") as f:
            data = json.load(f)
        pk = data.get("primary_keyword", "")
        if pk:
            with open(hs_fp, "r", encoding="utf-8") as f:
                html = f.read()
            # Bold keyword a few times
            kw_lower = pk.lower()
            # Find occurrences of keyword in text (not already in <strong>)
            pattern = re.compile(r'(?<!<strong>)(' + re.escape(kw_lower) + r')(?!</strong>)', re.IGNORECASE)
            matches = list(pattern.finditer(html))
            boldified = 0
            for m in matches[:3]:
                if '<strong>' not in html[max(0, m.start()-20):m.start()]:
                    html = html[:m.start()] + '<strong>' + m.group(0) + '</strong>' + html[m.end():]
                    boldified += 1
            if boldified:
                with open(hs_fp, "w", encoding="utf-8") as f:
                    f.write(html)
                print("  [BOLD] homeschool: %d keyword mentions bolded" % boldified)
    
    print("\n  ROUND 7 COMPLETE: %d articles injected" % fixes)


if __name__ == "__main__":
    main()
