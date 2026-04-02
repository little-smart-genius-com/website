"""
MEDIUM ARTICLE SUMMARIZER — Abstract Generator for Medium
Uses the same DeepSeek API infrastructure as auto_blog_v6_ultimate.py.

Reads published articles from articles/*.html, extracts H2 sections,
generates an engaging abstract via DeepSeek, and outputs Medium-ready
Markdown files with backlinks to the original article, blog, freebies,
and premium products.

Usage:
  python medium_publisher.py                     # Process all unprocessed articles
  python medium_publisher.py --slug SLUG         # Process a specific article by slug
  python medium_publisher.py --last N            # Process the last N articles
  python medium_publisher.py --list              # List all articles and their status
  python medium_publisher.py --force             # Reprocess already-processed articles

(c) 2026 Little Smart Genius
"""

import os
import sys
import re
import json
import glob
import time
import argparse
import requests
from datetime import datetime
from typing import Dict, List, Optional
from html.parser import HTMLParser

from dotenv import load_dotenv

# ─── PATH RESOLUTION ────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# ─── CONFIG ─────────────────────────────────────────────────────────
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL_CHAT = "deepseek-chat"

# Load all DeepSeek keys for parallel processing
DEEPSEEK_KEYS = []
for i in range(1, 8):
    key = os.getenv(f"DEEPSEEK_API_KEY_{i}")
    if key:
        DEEPSEEK_KEYS.append(key)
if not DEEPSEEK_KEYS:
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if key:
        DEEPSEEK_KEYS.append(key)

# Medium Integration Token (optional — for future API publishing)
MEDIUM_TOKEN = os.getenv("MEDIUM_INTEGRATION_TOKEN", "")

# Directories
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs", "medium")
TRACKER_FILE = os.path.join(OUTPUT_DIR, "_processed.json")

# Site URLs
SITE_BASE = "https://littlesmartgenius.com"
BLOG_URL = f"{SITE_BASE}/blog/"
FREEBIES_URL = f"{SITE_BASE}/freebies.html"
PRODUCTS_URL = f"{SITE_BASE}/products.html"


# ─── HTML CONTENT EXTRACTOR ─────────────────────────────────────────

class ArticleExtractor(HTMLParser):
    """Extracts title, meta description, H2 headings, author, and
    first paragraphs from an article HTML file."""

    def __init__(self):
        super().__init__()
        self._tag_stack = []
        self._capture = None
        self._buffer = ""

        self.title = ""
        self.meta_description = ""
        self.author = ""
        self.h2_sections: List[str] = []
        self.first_paragraphs: List[str] = []  # first <p> after each <h2>
        self.og_image = ""
        self._awaiting_first_p = False
        self._p_count_after_h2 = 0

    def handle_starttag(self, tag, attrs):
        self._tag_stack.append(tag)
        attrs_dict = dict(attrs)

        if tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            content = attrs_dict.get("content", "")
            if name == "description":
                self.meta_description = content
            elif prop == "article:author":
                self.author = content
            elif prop == "og:image":
                self.og_image = content

        if tag == "title":
            self._capture = "title"
            self._buffer = ""
        elif tag == "h2":
            self._capture = "h2"
            self._buffer = ""
        elif tag == "p" and self._awaiting_first_p and self._p_count_after_h2 < 2:
            self._capture = "p"
            self._buffer = ""

    def handle_endtag(self, tag):
        if self._capture == "title" and tag == "title":
            self.title = self._buffer.strip()
            # Remove " | Little Smart Genius" suffix
            self.title = re.sub(r'\s*\|\s*Little Smart Genius\s*$', '', self.title)
            self._capture = None
        elif self._capture == "h2" and tag == "h2":
            h2_text = re.sub(r'<[^>]+>', '', self._buffer).strip()
            if h2_text and "FAQ" not in h2_text and "Frequently Asked" not in h2_text:
                self.h2_sections.append(h2_text)
                self._awaiting_first_p = True
                self._p_count_after_h2 = 0
            self._capture = None
        elif self._capture == "p" and tag == "p":
            p_text = re.sub(r'<[^>]+>', '', self._buffer).strip()
            if p_text and len(p_text) > 40:
                self.first_paragraphs.append(p_text)
                self._p_count_after_h2 += 1
                if self._p_count_after_h2 >= 2:
                    self._awaiting_first_p = False
            self._capture = None

        if self._tag_stack and self._tag_stack[-1] == tag:
            self._tag_stack.pop()

    def handle_data(self, data):
        if self._capture:
            self._buffer += data


def extract_article_data(html_path: str) -> Dict:
    """Extract structured data from an article HTML file."""
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    extractor = ArticleExtractor()
    extractor.feed(html_content)

    slug = os.path.splitext(os.path.basename(html_path))[0]

    return {
        "slug": slug,
        "title": extractor.title,
        "meta_description": extractor.meta_description,
        "author": extractor.author or "Little Smart Genius",
        "h2_sections": extractor.h2_sections,
        "first_paragraphs": extractor.first_paragraphs,
        "og_image": extractor.og_image,
        "article_url": f"{SITE_BASE}/articles/{slug}.html",
        "file_path": html_path,
    }


# ─── DEEPSEEK API (same pattern as autoblog v6) ─────────────────────

def call_deepseek(system_prompt: str, user_prompt: str,
                  temperature: float = 0.7, api_key: str = None) -> Optional[str]:
    """Synchronous DeepSeek API call with parallel key support."""
    if not api_key and DEEPSEEK_KEYS:
        api_key = DEEPSEEK_KEYS[0]
        
    if not api_key:
        print("  [ERROR] No DeepSeek API key configured")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_CHAT,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": 4096
    }

    try:
        resp = requests.post(DEEPSEEK_API_URL, headers=headers,
                             json=payload, timeout=120)
        if resp.status_code == 200:
            data = resp.json()
            content = data['choices'][0]['message'].get('content', '')
            return content.strip()
        else:
            print(f"  [API ERROR] HTTP {resp.status_code}: {resp.text[:150]}")
            return None
    except Exception as e:
        print(f"  [API ERROR] {str(e)[:100]}")
        return None


# ─── ABSTRACT GENERATION PROMPT ─────────────────────────────────────

SYSTEM_PROMPT = """You are a professional content writer for Medium.
You specialize in writing engaging, concise article abstracts
for an educational brand called "Little Smart Genius" that creates
printable worksheets and activities for children aged 3-10.

Your writing style:
- Warm, conversational, parent-friendly tone
- NO AI-detectable phrases (avoid: "In today's world", "It's important to note",
  "Let's dive in", "In conclusion", "Game-changer", "Navigating", "Fostering")
- Short paragraphs (2-4 sentences max)
- Use natural, human transitions
- Write like a knowledgeable parent sharing tips with a friend
- Include actionable takeaways
- Keep it between 400-500 words (excluding the links section)

Output format: Write ONLY the article body in clean Markdown.
Do NOT include the title (it will be added separately).
Do NOT include any code blocks or fences around the output."""


def build_user_prompt(article_data: Dict) -> str:
    """Build the user prompt from extracted article data."""
    h2_list = "\n".join(f"  - {h2}" for h2 in article_data['h2_sections'])
    
    # Include first paragraph snippets for context
    context_snippets = ""
    for i, p in enumerate(article_data['first_paragraphs'][:6]):
        context_snippets += f"\n[Section {i+1} excerpt]: {p[:200]}..."

    return f"""Write an engaging Medium abstract for this article:

TITLE: {article_data['title']}
AUTHOR: {article_data['author']}
META DESCRIPTION: {article_data['meta_description']}

H2 SECTIONS (the article's main topics):
{h2_list}

CONTEXT FROM ARTICLE:
{context_snippets}

INSTRUCTIONS:
1. Summarize the key insights from each H2 section in a flowing, engaging narrative
2. Make parents WANT to click through to the full article 
3. Highlight 2-3 specific actionable tips from the content
4. End with a compelling reason to read the full article
5. Write in Markdown format (use **bold** for emphasis, no headers)
6. MUST be at least 400-500 words (strictly respected)
7. Do NOT include the title — it will be added separately
8. Do NOT wrap your output in code fences"""


# ─── MEDIUM MARKDOWN BUILDER ────────────────────────────────────────

def build_medium_markdown(article_data: Dict, abstract: str) -> str:
    """Assemble the final Medium-ready Markdown with backlinks and featured image."""
    
    article_url = article_data['article_url']
    og_image = article_data.get('og_image', '')
    
    # Prepend image if it exists
    image_md = f"![Featured Image]({og_image})\n\n" if og_image else ""
    
    md = f"""# {article_data['title']}

*By {article_data['author']} · Little Smart Genius*

---

{image_md}{abstract}

---

## 📖 Read the Full Article

Want the complete guide with printable resources, step-by-step activities, and expert tips?

**👉 [Read the full article on Little Smart Genius]({article_url})**

---

## 🎓 Explore More from Little Smart Genius

| Resource | Link |
|----------|------|
| 📚 **Education Blog** — 100+ expert articles on child development | [Visit the Blog]({BLOG_URL}) |
| 🎁 **Free Resources** — Download printable worksheets and activities | [Get Freebies]({FREEBIES_URL}) |
| ⭐ **Premium Products** — Full activity books and curriculum bundles | [Browse Products]({PRODUCTS_URL}) |
| 🌐 **Website** — Your one-stop shop for early learning resources | [littlesmartgenius.com]({SITE_BASE}) |

---

*Little Smart Genius creates printable educational resources — worksheets, puzzles, and activity books — designed to make learning fun for children aged 3–10. All resources are crafted by experienced educators and child development specialists.*

*Originally published on [littlesmartgenius.com]({SITE_BASE})*
"""
    return md


# ─── TRACKER (avoid reprocessing) ───────────────────────────────────

def load_tracker() -> Dict:
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"processed": {}}


def save_tracker(tracker: Dict):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(TRACKER_FILE, 'w', encoding='utf-8') as f:
        json.dump(tracker, f, indent=2, ensure_ascii=False)


def is_processed(tracker: Dict, slug: str) -> bool:
    return slug in tracker.get("processed", {})


def mark_processed(tracker: Dict, slug: str, output_path: str):
    tracker.setdefault("processed", {})[slug] = {
        "date": datetime.now().isoformat(),
        "output": output_path
    }


# ─── CORE PROCESSING ────────────────────────────────────────────────

import threading
import concurrent.futures

# Lock for writing to the tracker json file to prevent corruption
tracker_lock = threading.Lock()

def process_article(args) -> Optional[str]:
    """Process a single article: extract → summarize → save Markdown."""
    html_path, tracker, force, api_key = args
    
    # 1. Extract article data
    article_data = extract_article_data(html_path)
    slug = article_data['slug']
    
    with tracker_lock:
        already_processed = is_processed(tracker, slug)
        
    if not force and already_processed:
        print(f"  [SKIP] Already processed: {slug}")
        return None
    
    if len(article_data['h2_sections']) < 2:
        print(f"  [SKIP] Not enough H2 sections ({len(article_data['h2_sections'])}): {slug}")
        return None
    
    print(f"\n  📝 Processing: {article_data['title'][:60]}")

    # 2. Generate abstract via DeepSeek
    t0 = time.time()
    
    abstract = call_deepseek(SYSTEM_PROMPT, build_user_prompt(article_data), api_key=api_key)
    
    if not abstract:
        print(f"  [ERROR] Failed to generate abstract for {slug}")
        return None

    elapsed = round(time.time() - t0, 1)
    word_count = len(abstract.split())
    print(f"  [OK] Abstract generated for {slug}: {word_count} words ({elapsed}s)")
    
    # Clean up any code fences the model might have added
    abstract = re.sub(r'^```(?:markdown|md)?\s*\n?', '', abstract)
    abstract = re.sub(r'\n?```\s*$', '', abstract)

    # 3. Build final Markdown
    markdown = build_medium_markdown(article_data, abstract)
    
    # 4. Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{slug}.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    # 5. Track
    with tracker_lock:
        mark_processed(tracker, slug, output_path)
        save_tracker(tracker)
    
    return output_path


# ─── CLI ─────────────────────────────────────────────────────────────

def get_all_articles() -> List[str]:
    """Get all article HTML files sorted by modification time (newest first)."""
    pattern = os.path.join(ARTICLES_DIR, "*.html")
    files = glob.glob(pattern)
    files.sort(key=os.path.getmtime, reverse=True)
    return files


def main():
    parser = argparse.ArgumentParser(
        description="Medium Article Summarizer — Generate abstracts from blog articles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python medium_publisher.py                  # Process all unprocessed articles
  python medium_publisher.py --slug SLUG      # Process a specific article
  python medium_publisher.py --last 5         # Process the 5 most recent articles
  python medium_publisher.py --list           # Show all articles and processing status
  python medium_publisher.py --force          # Reprocess already-processed articles
"""
    )
    parser.add_argument("--slug", metavar="SLUG", help="Process a specific article by slug")
    parser.add_argument("--last", type=int, metavar="N", help="Process the last N articles")
    parser.add_argument("--list", action="store_true", help="List all articles and their status")
    parser.add_argument("--force", action="store_true", help="Force reprocess already-processed articles")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed without calling API")

    args = parser.parse_args()
    tracker = load_tracker()

    print("\n" + "=" * 60)
    print("  MEDIUM ARTICLE SUMMARIZER")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_articles = get_all_articles()
    print(f"\n  Total articles found: {len(all_articles)}")
    processed_count = len(tracker.get("processed", {}))
    print(f"  Already processed: {processed_count}")

    # ─── LIST MODE ───────────────────────────────────────────
    if args.list:
        print(f"\n{'─'*60}")
        for f in all_articles:
            slug = os.path.splitext(os.path.basename(f))[0]
            status = "✅" if is_processed(tracker, slug) else "⬜"
            mtime = datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y-%m-%d")
            print(f"  {status} [{mtime}] {slug}")
        return

    # ─── DETERMINE ARTICLES TO PROCESS ───────────────────────
    if args.slug:
        target_path = os.path.join(ARTICLES_DIR, f"{args.slug}.html")
        if not os.path.exists(target_path):
            print(f"\n  [ERROR] Article not found: {target_path}")
            return
        to_process = [target_path]
    elif args.last:
        to_process = all_articles[:args.last]
    else:
        to_process = all_articles

    # Filter already processed (unless --force)
    if not args.force:
        to_process = [f for f in to_process
                      if not is_processed(tracker, os.path.splitext(os.path.basename(f))[0])]

    print(f"\n  Articles to process: {len(to_process)}")

    if args.dry_run:
        print("\n  [DRY RUN] Would process:")
        for f in to_process:
            slug = os.path.splitext(os.path.basename(f))[0]
            print(f"    → {slug}")
        return

    if not to_process:
        print("\n  Nothing to process. Use --force to reprocess, or --last N.")
        return

    # ─── PROCESS ARTICLES ────────────────────────────────────
    results = []
    
    # Assign API keys rotationally to jobs
    jobs = []
    for i, html_path in enumerate(to_process):
        api_key = DEEPSEEK_KEYS[i % len(DEEPSEEK_KEYS)]
        jobs.append((html_path, tracker, args.force, api_key))
        
    print(f"\n  Running with {len(DEEPSEEK_KEYS)} parallel threads...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(DEEPSEEK_KEYS)) as executor:
        futures = {executor.submit(process_article, job): job for job in jobs}
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            try:
                output = future.result()
                if output:
                    results.append(output)
            except Exception as e:
                print(f"  [THREAD ERROR] Exception: {str(e)}")

    # ─── SUMMARY ─────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  COMPLETE: {len(results)}/{len(to_process)} abstracts generated")
    print(f"  Output directory: {OUTPUT_DIR}")
    print(f"{'='*60}")
    for r in results:
        print(f"  ✅ {os.path.basename(r)}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nCRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
