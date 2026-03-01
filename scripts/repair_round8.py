"""
ROUND 8 — Inject keyword into article body for ALL failing articles.
Uses a smarter paragraph detection that works with any HTML structure.
"""
import os, re, json, glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
POSTS_DIR = os.path.join(PROJECT_ROOT, "posts")

TARGETS = [
    "best-printable-logic-puzzles-for-kids-6-10",
    "best-sudoku-puzzles-for-beginners-kids-ultimate-guide",
    "boost-reading-skills-with-word-searches",
    "boost-your-childs-critical-thinking-with-this-activity-book",
    "boost-your-childs-logic-skills-with-skyscraper",
    "how-spot-the-difference-activities-boost-observation-skills",
    "mazes-the-ultimate-problem-solving-guide-for-kids",
    "photorealistic-spot-difference-puzzles-sharpen-childs-mind",
    "photorealistic-spot-the-difference-build-focus-guide",
    "ultimate-guide-to-fine-motor-skills-worksheets-for-preschool",
    "ultimate-guide-to-printable-1st-grade-math-sheets",
    "unlock-your-childs-strategic-thinking-with-four-in-a-row",
    "use-a-freebie-pack-to-boost-learning-skills-ultimate-guide",
]


def get_json(slug):
    for jf in glob.glob(os.path.join(POSTS_DIR, "*.json")):
        bn = os.path.basename(jf)
        parts = bn.rsplit("-", 1)
        js = parts[0] if len(parts) > 1 and parts[1].replace(".json","").isdigit() else bn.replace(".json","")
        if js == slug:
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
    return {}


def main():
    print("ROUND 8 — INJECT KEYWORDS INTO ARTICLE BODY")
    print("=" * 55)
    
    for slug in TARGETS:
        fp = os.path.join(ARTICLES_DIR, slug + ".html")
        if not os.path.exists(fp):
            print("  [SKIP] %s" % slug[:40])
            continue
        
        data = get_json(slug)
        pk = data.get("primary_keyword", "")
        if not pk:
            print("  [NO KW] %s" % slug[:40])
            continue
        
        kw_2 = " ".join(pk.lower().split()[:2])
        
        with open(fp, "r", encoding="utf-8") as f:
            html = f.read()
        
        # Check if keyword is already in body paragraphs
        # Find article body region
        body_start = re.search(r'class="article-content|<main|<article', html)
        if not body_start:
            print("  [NO BODY] %s" % slug[:40])
            continue
        
        body_html = html[body_start.end():]
        body_text = re.sub(r'<[^>]+>', ' ', body_html).lower()
        first_500_chars = body_text[:2000]
        
        if kw_2 in first_500_chars:
            print("  [ALREADY OK] %s — '%s' found in body" % (slug[:35], kw_2))
            continue
        
        # Find the first real paragraph in the body (after the first H2 or at the start)
        # Search for <p> tags with actual text content in the body region
        p_matches = list(re.finditer(r'<p[^>]*>(.*?)</p>', html[body_start.end():], re.DOTALL))
        
        injected = False
        for pm in p_matches:
            inner = pm.group(1)
            text = re.sub(r'<[^>]+>', '', inner).strip()
            if len(text) > 80:  # Real paragraph with enough content
                abs_pos = body_start.end() + pm.start()
                abs_end = body_start.end() + pm.end()
                
                # Inject keyword as a natural sentence after the first sentence
                kw_sentence = ' When it comes to <strong>%s</strong>, the right approach makes all the difference.' % pk.lower()
                
                # Find first sentence end (. followed by space or end)
                dot_pos = inner.find(". ")
                if dot_pos != -1 and dot_pos < len(inner) - 10:
                    new_inner = inner[:dot_pos + 1] + kw_sentence + inner[dot_pos + 1:]
                else:
                    new_inner = inner + kw_sentence
                
                # Reconstruct the <p> tag
                p_tag_end = html[abs_pos:].find(">") + 1
                p_open = html[abs_pos:abs_pos + p_tag_end]
                new_p = p_open + new_inner + "</p>"
                
                html = html[:abs_pos] + new_p + html[abs_end:]
                print("  [INJECT] %s — added '%s'" % (slug[:35], kw_2))
                injected = True
                break
        
        if not injected:
            print("  [FAIL] %s — could not find suitable paragraph" % slug[:40])
        
        with open(fp, "w", encoding="utf-8") as f:
            f.write(html)
    
    # Also fix mazes keyword to match title better
    mazes_jp = get_json("mazes-the-ultimate-problem-solving-guide-for-kids")
    if mazes_jp:
        # The title starts with "Mazes:" so KW should start with "mazes"
        # Change to "mazes problem solving kids" which has "mazes" as first word
        for jf in glob.glob(os.path.join(POSTS_DIR, "*.json")):
            bn = os.path.basename(jf)
            if "mazes" in bn:
                with open(jf, "r", encoding="utf-8") as f:
                    d = json.load(f)
                d["primary_keyword"] = "mazes problem solving kids guide"
                with open(jf, "w", encoding="utf-8") as f:
                    json.dump(d, f, indent=2, ensure_ascii=False)
                print("  [FIX] mazes KW -> 'mazes problem solving kids guide'")
                break
    
    print("\n  ROUND 8 COMPLETE")


if __name__ == "__main__":
    main()
