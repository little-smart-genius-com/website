"""
GENERATE AUTHOR PROFILE PAGES
Creates /authors/ directory with individual profile pages for each team member.
Each page includes:
- Person structured data (JSON-LD)
- Author bio, expertise, and credentials
- List of published articles (from articles.json)
- Internal links back to the author's articles
"""
import os, json, re
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
SITE_URL = "https://littlesmartgenius.com"

# ── Team Directory (from about.html) ──
AUTHORS = [
    {
        "slug": "little-smart-genius",
        "name": "Little Smart Genius",
        "display_name": "Little Smart Genius Team",
        "role": "Founder & Lead Editor",
        "real_name": "Richard Dubois",
        "emoji": "🧠",
        "color": "orange",
        "expertise": ["Curriculum Design", "Educational Publishing", "Activity Books", "Printable Resources"],
        "bio": "The creative engine behind Little Smart Genius. With a passion for curriculum design and educational publishing, our founder curates every resource to ensure it sparks curiosity and builds real skills in young learners.",
        "extended_bio": "With over 18 years of classroom experience and a degree from Stanford University, Richard Dubois created Little Smart Genius to bridge the gap between fun and learning. Every worksheet, puzzle, and activity in our catalog is designed to make children think critically, build confidence, and discover that learning can be an adventure.",
        "credentials": ["B.A. English Literature, Stanford University", "18+ years classroom experience", "Educator of the Year Award"],
        "is_primary": True,
    },
    {
        "slug": "sarah-mitchell",
        "name": "Sarah Mitchell",
        "display_name": "Sarah Mitchell",
        "role": "Senior Content Creator — Elementary Teacher (15 years)",
        "emoji": "👩‍🏫",
        "color": "blue",
        "expertise": ["Differentiated Instruction", "Literacy", "Math for Reluctant Learners", "K-5 Education"],
        "bio": "After 15 years in K-5 classrooms, Sarah brings real-world teaching experience into every worksheet and guide. She specializes in differentiated instruction, literacy, and making math fun for reluctant learners.",
        "extended_bio": "Sarah Mitchell spent 15 years teaching elementary school before joining Little Smart Genius as Senior Content Creator. Her deep understanding of how young children learn — and struggle — informs every resource she develops. Sarah's worksheets are known for their scaffolded approach, making complex concepts accessible to learners of all levels.",
        "credentials": ["15 years K-5 teaching experience", "Differentiated Instruction Specialist", "Literacy & Math Curriculum Designer"],
    },
    {
        "slug": "dr-emily-carter",
        "name": "Dr. Emily Carter",
        "display_name": "Dr. Emily Carter",
        "role": "Child Development Advisor — PhD in Developmental Psychology",
        "emoji": "🧬",
        "color": "purple",
        "expertise": ["Cognitive Science", "Child Development", "Evidence-Based Learning", "Brain-Based Teaching"],
        "bio": "Dr. Carter translates the latest cognitive science research into parent-friendly language. She ensures our activities are backed by evidence and aligned with how children's brains actually learn.",
        "extended_bio": "With a PhD in Developmental Psychology, Dr. Emily Carter bridges the gap between academic research and practical parenting. She reviews every Little Smart Genius resource to ensure it aligns with current cognitive science — from attention span research to executive function development. Her articles translate complex studies into actionable advice that parents and teachers can use today.",
        "credentials": ["PhD in Developmental Psychology", "Published Researcher in Child Cognition", "Science Advisory Board Member"],
    },
    {
        "slug": "rachel-nguyen",
        "name": "Rachel Nguyen",
        "display_name": "Rachel Nguyen",
        "role": "Parenting & Montessori Specialist",
        "emoji": "🌱",
        "color": "green",
        "expertise": ["Montessori Methods", "Sensory Activities", "Nature Play", "Homeschooling"],
        "bio": "A Montessori mom who lives and breathes child-led learning. Rachel writes from the trenches of parenting — sharing hands-on sensory activities, nature play ideas, and practical tips that work in real homes with real kids.",
        "extended_bio": "Rachel Nguyen is a certified Montessori educator and mother of three. Her approach combines Montessori principles with the chaos of real family life — messy sensory bins, nature walks that turn into bug hunts, and learning moments that happen between dinner and bedtime. Her content resonates with parents who want evidence-based methods without the perfection pressure.",
        "credentials": ["Certified Montessori Educator", "Homeschool Parent (3 children)", "Nature-Based Learning Advocate"],
    },
    {
        "slug": "david-moreau",
        "name": "David Moreau",
        "display_name": "David Moreau",
        "role": "Education & Pedagogy Specialist — M.Ed. (12 years)",
        "emoji": "📐",
        "color": "indigo",
        "expertise": ["Instructional Design", "Formative Assessment", "Project-Based Learning", "Math & Logic"],
        "bio": "With a Master's in Education and 12 years of instructional design experience, David crafts structured, methodical learning strategies. He focuses on formative assessment, project-based learning, and making complex concepts accessible.",
        "extended_bio": "David Moreau holds a Master's in Education and has spent 12 years designing curriculum for schools and educational publishers. His structured, methodical approach ensures that every learning pathway has clear objectives, measurable outcomes, and engaging activities. David specializes in making abstract math and logic concepts tangible for young learners.",
        "credentials": ["M.Ed. in Curriculum & Instruction", "12 years Instructional Design", "Project-Based Learning Specialist"],
    },
    {
        "slug": "lina-bautista",
        "name": "Lina Bautista",
        "display_name": "Lina Bautista",
        "role": "Educational Designer & Visual Learning Expert",
        "emoji": "🎨",
        "color": "pink",
        "expertise": ["Graphic Design", "Color Psychology", "Visual Scaffolding", "Gamification"],
        "bio": "Lina combines graphic design expertise with educational theory. She designs every worksheet with color psychology, visual scaffolding, and gamification — because great learning materials need to look great too.",
        "extended_bio": "Lina Bautista is a graphic designer with a specialization in educational materials. She understands that children engage more deeply with visually appealing content — so every worksheet, coloring page, and activity book she creates uses intentional color palettes, clear visual hierarchies, and gamification elements that make learning feel like play.",
        "credentials": ["B.F.A. in Graphic Design", "Educational Materials Specialist", "Visual Learning & Gamification Expert"],
    },
]

COLOR_MAP = {
    "orange": {"bg": "bg-orange-100", "text": "text-brand", "border": "border-brand"},
    "blue": {"bg": "bg-blue-100", "text": "text-blue-600", "border": "border-blue-500"},
    "purple": {"bg": "bg-purple-100", "text": "text-purple-600", "border": "border-purple-500"},
    "green": {"bg": "bg-green-100", "text": "text-green-600", "border": "border-green-500"},
    "indigo": {"bg": "bg-indigo-100", "text": "text-indigo-600", "border": "border-indigo-500"},
    "pink": {"bg": "bg-pink-100", "text": "text-pink-600", "border": "border-pink-500"},
}

def build_person_schema(author, articles):
    """Generate Person JSON-LD schema."""
    schema = {
        "@context": "https://schema.org",
        "@type": "ProfilePage",
        "mainEntity": {
            "@type": "Person",
            "name": author["name"],
            "jobTitle": author["role"],
            "url": f"{SITE_URL}/authors/{author['slug']}.html",
            "worksFor": {
                "@type": "Organization",
                "name": "Little Smart Genius",
                "url": SITE_URL,
            },
            "knowsAbout": author["expertise"],
            "description": author["bio"],
        },
    }
    if author.get("credentials"):
        schema["mainEntity"]["hasCredential"] = [
            {"@type": "EducationalOccupationalCredential", "credentialCategory": c}
            for c in author["credentials"]
        ]
    return json.dumps(schema, indent=2, ensure_ascii=False)


def build_author_page(author, articles_list):
    """Generate a full author profile HTML page."""
    colors = COLOR_MAP.get(author["color"], COLOR_MAP["orange"])
    canonical = f"{SITE_URL}/authors/{author['slug']}.html"
    
    # Build article cards
    article_cards = ""
    for a in articles_list[:12]:  # Show up to 12 articles
        cat = a.get("category", "")
        time = a.get("reading_time", 5)
        excerpt = (a.get("excerpt", "")[:120] + "...") if len(a.get("excerpt", "")) > 120 else a.get("excerpt", "")
        article_cards += f'''
            <a href="/articles/{a['slug']}.html" class="rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 border block" style="background: var(--card); border-color: var(--bord);">
                <div class="p-5">
                    <div class="flex items-center gap-2 mb-2">
                        <span class="text-xs font-bold uppercase tracking-wider {colors['text']} bg-orange-50 dark:bg-slate-800 px-2 py-0.5 rounded-full">{cat}</span>
                        <span class="text-xs text-slate-500">📖 {time} min</span>
                    </div>
                    <h3 class="text-base font-extrabold mb-2 leading-snug" style="color: var(--text);">{a['title']}</h3>
                    <p class="text-sm text-slate-500 dark:text-slate-400 line-clamp-2">{excerpt}</p>
                </div>
            </a>'''
    
    total_articles = len(articles_list)
    
    return f'''<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{author['name']} — Author Profile | Little Smart Genius</title>
    <meta name="description" content="{author['bio'][:155]}">
    <link rel="canonical" href="{canonical}">
    <link rel="icon" type="image/x-icon" href="/favicon.ico">
    <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
    <!-- Open Graph -->
    <meta property="og:title" content="{author['name']} — Author Profile | Little Smart Genius">
    <meta property="og:description" content="{author['bio'][:200]}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:type" content="profile">
    <!-- Tailwind (Production Build) -->
    <link rel="stylesheet" href="/styles/tailwind.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <!-- Person Schema -->
    <script type="application/ld+json">
{build_person_schema(author, articles_list)}
    </script>
    <style>
        :root {{ --bg: #FAFAFA; --text: #1E293B; --card: #FFFFFF; --head: rgba(255,255,255,0.95); --bord: #E2E8F0; }}
        .dark {{ --bg: #0F172A; --text: #F8FAFC; --card: #1E293B; --head: rgba(15,23,42,0.95); --bord: #334155; }}
        body {{ font-family: 'Outfit', sans-serif; background: var(--bg); color: var(--text); margin: 0; transition: 0.3s; }}
        .top-header {{ position: fixed; top: 0; left: 0; right: 0; height: 80px; background: var(--head); backdrop-filter: blur(10px); border-bottom: 1px solid var(--bord); z-index: 50; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; transition: 0.3s; }}
        .logo-img {{ width: 45px; height: 45px; border-radius: 50%; border: 2px solid #F48C06; object-fit: cover; }}
        .nav-link {{ font-weight: 700; color: #64748B; text-decoration: none; transition: 0.2s; }}
        .nav-link:hover {{ color: #F48C06; }}
        #mobile-menu {{ display: none; position: fixed; top: 80px; left: 0; right: 0; background: var(--card); border-bottom: 1px solid var(--bord); flex-direction: column; padding: 20px; z-index: 49; }}
        .hero-title {{ background: linear-gradient(135deg, #1E293B 0%, #F48C06 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .dark .hero-title {{ background: linear-gradient(135deg, #FFFFFF 0%, #F48C06 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .social-footer-bar {{ display: flex; justify-content: center; gap: 16px; padding: 5px 0; }}
        .social-footer-bar a {{ width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: rgba(244,140,6,0.1); color: #F48C06; transition: all 0.3s; text-decoration: none; }}
        .social-footer-bar a:hover {{ background: #F48C06; color: #fff; transform: translateY(-2px); }}
        .social-footer-bar svg {{ width: 20px; height: 20px; }}
        .site-footer {{ text-align: center; padding: 5px 0; color: #94A3B8; font-size: 0.75rem; }}
        .site-footer a {{ color: #94A3B8; text-decoration: none; transition: 0.2s; }}
        .site-footer a:hover {{ color: #F48C06; }}
        .fade-in {{ animation: fadeIn 0.8s ease-out; }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    </style>
    <!-- GA4 -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-1S8G205JX2"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-1S8G205JX2');</script>
</head>
<body>
    <header class="top-header px-5 md:px-10">
        <a class="flex items-center gap-3 no-underline" href="/">
            <img alt="Logo" class="logo-img" src="https://ecdn.teacherspayteachers.com/thumbuserhome/Little-Smart-Genius-1746813476/23416711.jpg">
            <span class="text-lg md:text-xl font-extrabold block" style="color:var(--text)">Little Smart Genius<span class="text-brand">.</span></span>
        </a>
        <nav class="hidden lg:flex gap-8">
            <a class="nav-link" href="/">Home</a>
            <a class="nav-link" href="/products.html">Store</a>
            <a class="nav-link" href="/freebies.html">Freebies</a>
            <a class="nav-link" href="/blog/">Blog</a>
            <a class="nav-link" href="/about.html">About</a>
            <a class="nav-link" href="/contact.html">Contact</a>
        </nav>
        <div class="flex items-center gap-4">
            <div class="w-10 h-10 rounded-full flex items-center justify-center cursor-pointer bg-slate-100 dark:bg-slate-700 transition" onclick="toggleTheme()"><span id="theme-icon">🌙</span></div>
            <button class="block lg:hidden text-2xl" onclick="toggleMobileMenu()" style="color:var(--text)">☰</button>
        </div>
    </header>
    <div id="mobile-menu">
        <a class="py-3 border-b border-gray-200 font-bold" href="/" style="color:var(--text)">Home</a>
        <a class="py-3 border-b border-gray-200 font-bold" href="/products.html" style="color:var(--text)">Store</a>
        <a class="py-3 border-b border-gray-200 font-bold" href="/freebies.html" style="color:var(--text)">Freebies</a>
        <a class="py-3 border-b border-gray-200 font-bold" href="/blog/" style="color:var(--text)">Blog</a>
        <a class="py-3 border-b border-gray-200 font-bold" href="/about.html" style="color:var(--text)">About</a>
        <a class="py-3 border-b border-gray-200 font-bold" href="/contact.html" style="color:var(--text)">Contact</a>
    </div>

    <!-- BREADCRUMB -->
    <div class="pt-24 px-6 max-w-5xl mx-auto">
        <nav class="text-sm text-slate-500 mb-6 fade-in" aria-label="Breadcrumb">
            <a href="/" class="hover:text-brand transition">Home</a>
            <span class="mx-2">›</span>
            <a href="/about.html" class="hover:text-brand transition">About</a>
            <span class="mx-2">›</span>
            <span style="color: var(--text); font-weight: 700;">{author['name']}</span>
        </nav>
    </div>

    <!-- AUTHOR PROFILE -->
    <div class="px-6 max-w-5xl mx-auto pb-12 fade-in">
        <div class="flex flex-col md:flex-row gap-8 items-start mb-12">
            <!-- Avatar + Info -->
            <div class="flex-shrink-0">
                <div class="w-28 h-28 rounded-full {colors['bg']} flex items-center justify-center text-6xl border-4 {colors['border']} shadow-lg">
                    {author['emoji']}
                </div>
            </div>
            <div class="flex-1">
                <h1 class="text-3xl md:text-4xl font-extrabold mb-2 hero-title">{author['name']}</h1>
                <p class="{colors['text']} font-bold text-lg mb-1">{author['role']}</p>
                {"<p class='text-slate-400 text-sm italic mb-3'>" + author['real_name'] + "</p>" if author.get('real_name') else ""}
                <p class="text-slate-600 dark:text-slate-300 leading-relaxed mb-4">{author.get('extended_bio', author['bio'])}</p>
                <!-- Expertise tags -->
                <div class="flex flex-wrap gap-2 mb-4">
                    {"".join(f'<span class="text-xs font-bold px-3 py-1 rounded-full {colors["bg"]} {colors["text"]}">{e}</span>' for e in author['expertise'])}
                </div>
                <!-- Credentials -->
                <div class="space-y-1">
                    {"".join(f'<div class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400"><span class="text-brand">✓</span> {c}</div>' for c in author.get('credentials', []))}
                </div>
            </div>
        </div>

        <!-- PUBLISHED ARTICLES -->
        <div class="mb-12">
            <h2 class="text-2xl font-extrabold mb-6" style="color: var(--text);">
                Articles by {author['name']}
                <span class="text-sm font-normal text-slate-500 ml-2">({total_articles} article{"s" if total_articles != 1 else ""})</span>
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {article_cards}
            </div>
            {"<div class='text-center mt-8'><a href='/blog/' class='inline-block px-8 py-3 bg-brand text-white font-bold rounded-xl hover:shadow-lg transition'>Browse All Articles →</a></div>" if total_articles > 12 else ""}
        </div>

        <!-- BACK TO TEAM -->
        <div class="text-center">
            <a href="/about.html" class="inline-flex items-center gap-2 px-6 py-3 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold rounded-xl hover:bg-slate-200 dark:hover:bg-slate-700 transition">
                ← Meet the Full Team
            </a>
        </div>
    </div>

    <!-- FOOTER -->
    <div class="dark:border-slate-700" style="border-top: 1px solid var(--bord, #E2E8F0);">
        <div class="social-footer-bar">
            <a href="https://www.instagram.com/littlesmartgenius_com/" rel="noopener" target="_blank" title="Instagram">
                <svg fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"></path></svg>
            </a>
            <a href="https://www.pinterest.com/littlesmartgenius_com/" rel="noopener" target="_blank" title="Pinterest">
                <svg fill="currentColor" viewBox="0 0 24 24"><path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.174.271-.401.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.607 0 11.985-5.365 11.985-11.987C23.97 5.39 18.592.026 11.985.026L12.017 0z"></path></svg>
            </a>
            <a href="https://medium.com/@littlesmartgenius-com" rel="noopener" target="_blank" title="Medium">
                <svg fill="currentColor" viewBox="0 0 24 24"><path d="M13.54 12a6.8 6.8 0 01-6.77 6.82A6.8 6.8 0 010 12a6.8 6.8 0 016.77-6.82A6.8 6.8 0 0113.54 12zM20.96 12c0 3.54-1.51 6.42-3.38 6.42-1.87 0-3.39-2.88-3.39-6.42s1.52-6.42 3.39-6.42 3.38 2.88 3.38 6.42M24 12c0 3.17-.53 5.75-1.19 5.75-.66 0-1.19-2.58-1.19-5.75s.53-5.75 1.19-5.75C23.47 6.25 24 8.83 24 12z"></path></svg>
            </a>
        </div>
        <div class="site-footer">
            <div style="margin-bottom: 6px;">
                <a href="/terms.html">Terms of Service</a>
                <span style="margin: 0 8px;">•</span>
                <a href="/privacy.html">Privacy Policy</a>
                <span style="margin: 0 8px;">•</span>
                <a href="/education.html">Education</a>
                <span style="margin: 0 8px;">•</span>
                <a href="/legal.html">Legal</a>
            </div>
            © 2026 Little Smart Genius. All rights reserved.
        </div>
    </div>
    <script>
        function initTheme(){{if(localStorage.getItem('theme')==='dark'){{document.documentElement.classList.add('dark');document.getElementById('theme-icon').innerHTML='☀️';}}else{{document.documentElement.classList.remove('dark');document.getElementById('theme-icon').innerHTML='🌙';}}}}
        function toggleTheme(){{const h=document.documentElement;h.classList.toggle('dark');const d=h.classList.contains('dark');localStorage.setItem('theme',d?'dark':'light');document.getElementById('theme-icon').innerHTML=d?'☀️':'🌙';}}
        function toggleMobileMenu(){{const m=document.getElementById('mobile-menu');m.style.display=(m.style.display==='flex')?'none':'flex';}}
        initTheme();
    </script>
</body>
</html>'''


def main():
    # Load articles
    articles_path = os.path.join(PROJECT_ROOT, "articles.json")
    with open(articles_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    all_articles = data.get("articles", [])
    
    # Create authors directory
    authors_dir = os.path.join(PROJECT_ROOT, "authors")
    os.makedirs(authors_dir, exist_ok=True)
    
    # Map article authors to their team slug
    author_articles = {a["slug"]: [] for a in AUTHORS}
    
    # Assign articles based on their author field
    for art in all_articles:
        # Assuming art["author"] holds the persona ID like "LSG_Admin", "Sarah_Mitchell", etc.
        # We need to map those to the slugs defined in AUTHORS.
        # LSG_Admin -> "little-smart-genius"
        author_id = art.get("author", "LSG_Admin")
        
        # Mappings based on the personas IDs in auto_blog_v6_ultimate
        slug_map = {
            "LSG_Admin": "little-smart-genius",
            "Sarah_Mitchell": "sarah-mitchell",
            "Dr_Emily_Carter": "dr-emily-carter",
            "Rachel_Nguyen": "rachel-nguyen",
            "David_Moreau": "david-moreau",
            "Lina_Bautista": "lina-bautista"
        }
        
        author_slug = slug_map.get(author_id, "little-smart-genius")
        if author_slug in author_articles:
            author_articles[author_slug].append(art)
        else:
            author_articles["little-smart-genius"].append(art)
    
    # Generate pages
    for author in AUTHORS:
        articles = author_articles.get(author["slug"], [])
        html = build_author_page(author, articles)
        filepath = os.path.join(authors_dir, f"{author['slug']}.html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  ✓ {author['slug']}.html ({len(articles)} articles)")
    
    # Generate authors index page
    build_authors_index(authors_dir, author_articles)
    
    # Add to sitemap
    add_to_sitemap(authors_dir)
    
    print(f"\n  Generated {len(AUTHORS)} author pages + index in /authors/")


def build_authors_index(authors_dir, author_articles):
    """Generate the /authors/index.html listing page."""
    cards = ""
    for a in AUTHORS:
        count = len(author_articles.get(a["slug"], []))
        colors = COLOR_MAP.get(a["color"], COLOR_MAP["orange"])
        cards += f'''
        <a href="/authors/{a['slug']}.html" class="p-6 rounded-2xl border shadow-lg hover:shadow-2xl transition-all duration-300 block" style="background: var(--card); border-color: var(--bord);">
            <div class="flex items-center gap-4 mb-3">
                <div class="w-16 h-16 rounded-full {colors['bg']} flex items-center justify-center text-3xl border-2 {colors['border']}">{a['emoji']}</div>
                <div>
                    <h2 class="text-lg font-extrabold" style="color: var(--text);">{a['name']}</h2>
                    <p class="{colors['text']} text-sm font-bold">{a['role'].split('—')[0].strip()}</p>
                </div>
            </div>
            <p class="text-sm text-slate-500 dark:text-slate-400 leading-relaxed mb-3">{a['bio'][:150]}...</p>
            <div class="flex items-center gap-2">
                <span class="text-xs font-bold text-brand">📝 {count} article{"s" if count != 1 else ""}</span>
                <span class="text-xs text-slate-400">• View profile →</span>
            </div>
        </a>'''

    index_html = f'''<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Our Authors & Experts | Little Smart Genius</title>
    <meta name="description" content="Meet the educators, child psychologists, and design experts behind Little Smart Genius. Our team creates evidence-based learning resources for children ages 3-12.">
    <link rel="canonical" href="{SITE_URL}/authors/">
    <link rel="icon" type="image/x-icon" href="/favicon.ico">
    <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
    <meta property="og:title" content="Our Authors & Experts | Little Smart Genius">
    <meta property="og:description" content="Meet the educators and experts behind Little Smart Genius learning resources.">
    <meta property="og:url" content="{SITE_URL}/authors/">
    <meta property="og:type" content="website">
    <link rel="stylesheet" href="/styles/tailwind.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {{ --bg: #FAFAFA; --text: #1E293B; --card: #FFFFFF; --head: rgba(255,255,255,0.95); --bord: #E2E8F0; }}
        .dark {{ --bg: #0F172A; --text: #F8FAFC; --card: #1E293B; --head: rgba(15,23,42,0.95); --bord: #334155; }}
        body {{ font-family: 'Outfit', sans-serif; background: var(--bg); color: var(--text); margin: 0; transition: 0.3s; }}
        .top-header {{ position: fixed; top: 0; left: 0; right: 0; height: 80px; background: var(--head); backdrop-filter: blur(10px); border-bottom: 1px solid var(--bord); z-index: 50; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; transition: 0.3s; }}
        .logo-img {{ width: 45px; height: 45px; border-radius: 50%; border: 2px solid #F48C06; object-fit: cover; }}
        .nav-link {{ font-weight: 700; color: #64748B; text-decoration: none; transition: 0.2s; }}
        .nav-link:hover {{ color: #F48C06; }}
        #mobile-menu {{ display: none; position: fixed; top: 80px; left: 0; right: 0; background: var(--card); border-bottom: 1px solid var(--bord); flex-direction: column; padding: 20px; z-index: 49; }}
        .hero-title {{ background: linear-gradient(135deg, #1E293B 0%, #F48C06 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .dark .hero-title {{ background: linear-gradient(135deg, #FFFFFF 0%, #F48C06 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .social-footer-bar {{ display: flex; justify-content: center; gap: 16px; padding: 5px 0; }}
        .social-footer-bar a {{ width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: rgba(244,140,6,0.1); color: #F48C06; transition: all 0.3s; text-decoration: none; }}
        .social-footer-bar a:hover {{ background: #F48C06; color: #fff; transform: translateY(-2px); }}
        .social-footer-bar svg {{ width: 20px; height: 20px; }}
        .site-footer {{ text-align: center; padding: 5px 0; color: #94A3B8; font-size: 0.75rem; }}
        .site-footer a {{ color: #94A3B8; text-decoration: none; transition: 0.2s; }}
        .site-footer a:hover {{ color: #F48C06; }}
    </style>
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-1S8G205JX2"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-1S8G205JX2');</script>
</head>
<body>
    <header class="top-header px-5 md:px-10">
        <a class="flex items-center gap-3 no-underline" href="/">
            <img alt="Logo" class="logo-img" src="https://ecdn.teacherspayteachers.com/thumbuserhome/Little-Smart-Genius-1746813476/23416711.jpg">
            <span class="text-lg md:text-xl font-extrabold block" style="color:var(--text)">Little Smart Genius<span class="text-brand">.</span></span>
        </a>
        <nav class="hidden lg:flex gap-8">
            <a class="nav-link" href="/">Home</a>
            <a class="nav-link" href="/products.html">Store</a>
            <a class="nav-link" href="/freebies.html">Freebies</a>
            <a class="nav-link" href="/blog/">Blog</a>
            <a class="nav-link" href="/about.html">About</a>
            <a class="nav-link" href="/contact.html">Contact</a>
        </nav>
        <div class="flex items-center gap-4">
            <div class="w-10 h-10 rounded-full flex items-center justify-center cursor-pointer bg-slate-100 dark:bg-slate-700 transition" onclick="toggleTheme()"><span id="theme-icon">🌙</span></div>
            <button class="block lg:hidden text-2xl" onclick="toggleMobileMenu()" style="color:var(--text)">☰</button>
        </div>
    </header>
    <div id="mobile-menu">
        <a class="py-3 border-b border-gray-200 font-bold" href="/" style="color:var(--text)">Home</a>
        <a class="py-3 border-b border-gray-200 font-bold" href="/products.html" style="color:var(--text)">Store</a>
        <a class="py-3 border-b border-gray-200 font-bold" href="/freebies.html" style="color:var(--text)">Freebies</a>
        <a class="py-3 border-b border-gray-200 font-bold" href="/blog/" style="color:var(--text)">Blog</a>
        <a class="py-3 border-b border-gray-200 font-bold" href="/about.html" style="color:var(--text)">About</a>
        <a class="py-3 border-b border-gray-200 font-bold" href="/contact.html" style="color:var(--text)">Contact</a>
    </div>

    <div class="pt-28 px-6 max-w-5xl mx-auto pb-16">
        <div class="text-center mb-12">
            <h1 class="text-3xl md:text-4xl font-extrabold mb-4 hero-title">Our Authors & Experts</h1>
            <p class="text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
                Meet the educators, child psychologists, and design experts who create every Little Smart Genius resource. Each team member brings unique expertise to help your child learn and grow.
            </p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {cards}
        </div>
    </div>

    <div class="dark:border-slate-700" style="border-top: 1px solid var(--bord, #E2E8F0);">
        <div class="social-footer-bar">
            <a href="https://www.instagram.com/littlesmartgenius_com/" rel="noopener" target="_blank" title="Instagram"><svg fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"></path></svg></a>
            <a href="https://www.pinterest.com/littlesmartgenius_com/" rel="noopener" target="_blank" title="Pinterest"><svg fill="currentColor" viewBox="0 0 24 24"><path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.174.271-.401.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.607 0 11.985-5.365 11.985-11.987C23.97 5.39 18.592.026 11.985.026L12.017 0z"></path></svg></a>
            <a href="https://medium.com/@littlesmartgenius-com" rel="noopener" target="_blank" title="Medium"><svg fill="currentColor" viewBox="0 0 24 24"><path d="M13.54 12a6.8 6.8 0 01-6.77 6.82A6.8 6.8 0 010 12a6.8 6.8 0 016.77-6.82A6.8 6.8 0 0113.54 12zM20.96 12c0 3.54-1.51 6.42-3.38 6.42-1.87 0-3.39-2.88-3.39-6.42s1.52-6.42 3.39-6.42 3.38 2.88 3.38 6.42M24 12c0 3.17-.53 5.75-1.19 5.75-.66 0-1.19-2.58-1.19-5.75s.53-5.75 1.19-5.75C23.47 6.25 24 8.83 24 12z"></path></svg></a>
        </div>
        <div class="site-footer">
            <div style="margin-bottom: 6px;">
                <a href="/terms.html">Terms</a> <span style="margin: 0 8px;">•</span>
                <a href="/privacy.html">Privacy</a> <span style="margin: 0 8px;">•</span>
                <a href="/education.html">Education</a> <span style="margin: 0 8px;">•</span>
                <a href="/legal.html">Legal</a>
            </div>
            © 2026 Little Smart Genius. All rights reserved.
        </div>
    </div>
    <script>
        function initTheme(){{if(localStorage.getItem('theme')==='dark'){{document.documentElement.classList.add('dark');document.getElementById('theme-icon').innerHTML='☀️';}}else{{document.documentElement.classList.remove('dark');document.getElementById('theme-icon').innerHTML='🌙';}}}}
        function toggleTheme(){{const h=document.documentElement;h.classList.toggle('dark');const d=h.classList.contains('dark');localStorage.setItem('theme',d?'dark':'light');document.getElementById('theme-icon').innerHTML=d?'☀️':'🌙';}}
        function toggleMobileMenu(){{const m=document.getElementById('mobile-menu');m.style.display=(m.style.display==='flex')?'none':'flex';}}
        initTheme();
    </script>
</body>
</html>'''
    
    filepath = os.path.join(authors_dir, "index.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"  ✓ index.html (authors listing)")


def add_to_sitemap(authors_dir):
    """Add author pages to the sitemap."""
    sitemap_path = os.path.join(PROJECT_ROOT, "sitemap.xml")
    with open(sitemap_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    today = datetime.now().strftime("%Y-%m-%d")
    new_urls = ""
    
    # Index page
    new_urls += f"""
    <url>
        <loc>{SITE_URL}/authors/</loc>
        <lastmod>{today}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>"""
    
    # Individual author pages
    for author in AUTHORS:
        new_urls += f"""
    <url>
        <loc>{SITE_URL}/authors/{author['slug']}.html</loc>
        <lastmod>{today}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.6</priority>
    </url>"""
    
    # Insert before </urlset>
    content = content.replace("</urlset>", f"{new_urls}\n</urlset>")
    
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"  ✓ Added {len(AUTHORS) + 1} URLs to sitemap.xml")


if __name__ == "__main__":
    main()
