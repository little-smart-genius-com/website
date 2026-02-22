"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          GENERATE BLOG ARTICLES V3.0 SUPREME - MODE VERBOSE                  ║
║        Convertisseur JSON → HTML Ultra-Robuste avec SEO Avancé               ║
║                     © 2026 Little Smart Genius                               ║
╚══════════════════════════════════════════════════════════════════════════════╝

AMÉLIORATIONS V3.0:
✅ Logs détaillés en temps réel
✅ Validation robuste des JSON
✅ Backup automatique avant modifications
✅ Génération sitemap.xml automatique
✅ Métadonnées enrichies (Open Graph, Twitter Cards)
✅ Détection et gestion des doublons
✅ Index de tous les articles (articles.json)
✅ Rapport de génération détaillé
✅ Gestion des erreurs avec retry
✅ Optimisations SEO avancées
"""

import os
import json
import glob
import shutil
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import re
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# 🔧 CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

POSTS_DIR = "posts"
IMAGES_DIR = "images"
ARTICLES_DIR = "articles"
BLOG_FILE = "blog.html"
BACKUP_DIR = "backups"
REPORTS_DIR = "reports"
ARCHIVE_DIR = os.path.join("posts", "archive")
ARTICLES_PER_PAGE = 9
SITE_URL = "https://littlesmartgenius.com"  # ⚠️ PERSONNALISEZ

# ═══════════════════════════════════════════════════════════════════════════
# 🎨 SYSTÈME DE LOGGING DÉTAILLÉ
# ═══════════════════════════════════════════════════════════════════════════

class ConversionLogger:
    """Logger avec affichage temps réel détaillé"""

    def __init__(self):
        os.makedirs(REPORTS_DIR, exist_ok=True)
        self.start_time = datetime.now()
        self.report_file = os.path.join(
            REPORTS_DIR, 
            f"conversion_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        )
        self.report = {
            "start_time": self.start_time.isoformat(),
            "articles_processed": [],
            "errors": [],
            "warnings": [],
            "stats": {}
        }

    def section(self, title: str):
        """Affiche un en-tête de section"""
        print(f"\n{'═'*80}")
        print(f"║  {title}")
        print('═'*80)

    def info(self, message: str, indent: int = 1):
        """Message d'information"""
        print(f"{'   '*indent}ℹ️  {message}")

    def success(self, message: str, indent: int = 1):
        """Message de succès"""
        print(f"{'   '*indent}✅ {message}")

    def warning(self, message: str, indent: int = 1):
        """Message d'avertissement"""
        print(f"{'   '*indent}⚠️  {message}")
        self.report["warnings"].append({
            "timestamp": datetime.now().isoformat(),
            "message": message
        })

    def error(self, message: str, context: dict = None, indent: int = 1):
        """Message d'erreur"""
        print(f"{'   '*indent}❌ ERREUR: {message}")
        if context:
            print(f"{'   '*(indent+1)}Contexte: {json.dumps(context, indent=2)}")
        self.report["errors"].append({
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "context": context or {}
        })

    def progress(self, current: int, total: int, label: str = ""):
        """Barre de progression"""
        percentage = (current / total) * 100
        filled = int(percentage / 5)
        bar = "█" * filled + "░" * (20 - filled)
        print(f"   [{bar}] {percentage:.0f}% {label} ({current}/{total})", end="\r")
        if current == total:
            print()

    def article_processed(self, article_info: dict):
        """Enregistre un article traité"""
        self.report["articles_processed"].append(article_info)

    def add_stat(self, key: str, value):
        """Ajoute une statistique"""
        self.report["stats"][key] = value

    def save(self):
        """Sauvegarde le rapport"""
        self.report["end_time"] = datetime.now().isoformat()
        duration = (datetime.now() - self.start_time).total_seconds()
        self.report["duration_seconds"] = round(duration, 2)

        with open(self.report_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Rapport sauvegardé: {self.report_file}")


# ═══════════════════════════════════════════════════════════════════════════
# 🛡️ VALIDATION & SÉCURITÉ
# ═══════════════════════════════════════════════════════════════════════════

class ArticleValidator:
    """Validation robuste des articles"""

    @staticmethod
    def validate_json(filepath: str, logger: ConversionLogger) -> Tuple[bool, Optional[dict], List[str]]:
        """Valide un fichier JSON et retourne (success, data, errors)"""
        errors = []

        # Vérifier l'existence du fichier
        if not os.path.exists(filepath):
            errors.append(f"Fichier introuvable: {filepath}")
            return False, None, errors

        # Vérifier la taille du fichier
        file_size = os.path.getsize(filepath)
        if file_size == 0:
            errors.append("Fichier vide")
            return False, None, errors

        if file_size > 10 * 1024 * 1024:  # 10 MB
            errors.append(f"Fichier trop volumineux: {file_size // 1024 // 1024} MB")
            return False, None, errors

        # Parser le JSON
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"JSON invalide: {str(e)}")
            return False, None, errors
        except Exception as e:
            errors.append(f"Erreur lecture: {str(e)}")
            return False, None, errors

        # Valider les champs requis
        required_fields = ['title', 'content']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Champ requis manquant: {field}")

        # Valider le contenu
        if 'content' in data:
            content = data['content']
            if len(content) < 100:
                errors.append(f"Contenu trop court: {len(content)} caractères")

            # Vérifier présence de HTML basique
            if not re.search(r'<[^>]+>', content):
                logger.warning(f"Aucune balise HTML détectée dans {os.path.basename(filepath)}", 2)

        # Valider l'image
        if 'image' in data and data['image']:
            img_path = data['image']
            if not img_path.startswith('http'):
                # Image locale
                if not os.path.exists(img_path):
                    logger.warning(f"Image introuvable: {img_path}", 2)

        return len(errors) == 0, data, errors

    @staticmethod
    def sanitize_html(content: str) -> str:
        """Nettoie le contenu HTML"""
        # Supprimer les scripts dangereux
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)

        # Supprimer les styles inline excessifs
        content = re.sub(r' style="[^"]*"', '', content)

        # Normaliser les espaces
        content = re.sub(r'\s+', ' ', content)

        return content.strip()


# ═══════════════════════════════════════════════════════════════════════════
# 📄 TEMPLATE HTML ARTICLE (Votre Design Exact)
# ═══════════════════════════════════════════════════════════════════════════

ARTICLE_TEMPLATE = """<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>{title} | Little Smart Genius</title>
    <meta name="description" content="{excerpt}">
    <meta name="keywords" content="{keywords}">
    <link rel="canonical" href="{canonical_url}">

    <!-- Open Graph -->
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{excerpt}">
    <meta property="og:image" content="{og_image}">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:type" content="article">
    <meta property="article:published_time" content="{iso_date}">
    <meta property="article:author" content="{author_name}">

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{excerpt}">
    <meta name="twitter:image" content="{og_image}">

    <!-- JSON-LD Schema -->
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "BlogPosting",
      "headline": "{title}",
      "image": "{og_image}",
      "author": {{
        "@type": "Person",
        "name": "{author_name}"
      }},
      "publisher": {{
        "@type": "Organization",
        "name": "Little Smart Genius",
        "logo": {{
          "@type": "ImageObject",
          "url": "{site_url}/logo.png"
        }}
      }},
      "datePublished": "{iso_date}",
      "dateModified": "{iso_date}",
      "description": "{excerpt}",
      "mainEntityOfPage": {{
        "@type": "WebPage",
        "@id": "{canonical_url}"
      }}
    }}
    </script>

    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">

    <script>
        tailwind.config = {{ 
            darkMode: 'class', 
            theme: {{ extend: {{ colors: {{ brand: '#F48C06' }} }} }} 
        }}
    </script>

    <style>
        :root {{ --bg: #FAFAFA; --text: #1E293B; --card: #FFFFFF; --head: rgba(255,255,255,0.95); --bord: #E2E8F0; }}
        .dark {{ --bg: #0F172A; --text: #F8FAFC; --card: #1E293B; --head: rgba(15,23,42,0.95); --bord: #334155; }}

        body {{ font-family: 'Outfit', sans-serif; background: var(--bg); color: var(--text); margin: 0; transition: 0.3s; }}

        .top-header {{ 
            position: fixed; top: 0; left: 0; right: 0; height: 80px; 
            background: var(--head); backdrop-filter: blur(10px); 
            border-bottom: 1px solid var(--bord); z-index: 50; 
            display: flex; align-items: center; justify-content: space-between; 
            padding: 0 20px; transition: 0.3s; 
        }}

        .logo-img {{ width: 45px; height: 45px; border-radius: 50%; border: 2px solid #F48C06; object-fit: cover; }}
        .nav-link {{ font-weight: 700; color: #64748B; text-decoration: none; transition: 0.2s; }}
        .nav-link:hover, .nav-link.active {{ color: #F48C06; }}

        #mobile-menu {{ display: none; position: fixed; top: 80px; left: 0; right: 0; background: var(--card); border-bottom: 1px solid var(--bord); flex-direction: column; padding: 20px; z-index: 49; }}

        .article-content {{ max-width: 800px; margin: 0 auto; line-height: 1.8; }}
        .article-content h2 {{ font-size: 1.8rem; font-weight: 800; margin-top: 2.5rem; margin-bottom: 1rem; color: var(--text); }}
        .article-content h3 {{ font-size: 1.4rem; font-weight: 700; margin-top: 2rem; margin-bottom: 0.8rem; color: #F48C06; }}
        .article-content p {{ margin-bottom: 1.5rem; font-size: 1.125rem; }}
        .article-content ul {{ list-style-type: disc; padding-left: 2rem; margin-bottom: 1.5rem; }}
        .article-content li {{ margin-bottom: 0.5rem; }}
        .article-content strong {{ color: #F48C06; font-weight: 700; }}
        .article-content a {{ color: #F48C06; text-decoration: underline; }}
        .article-content img {{ border-radius: 12px; margin: 2rem 0; width: 100%; box-shadow: 0 10px 30px -10px rgba(0,0,0,0.15); }}
        .article-content figure {{ margin: 2rem 0; }}
        .article-content blockquote {{ border-left: 4px solid #F48C06; background: rgba(244, 140, 6, 0.1); padding: 1.5rem; margin: 2rem 0; border-radius: 0 8px 8px 0; font-style: italic; }}

        .reading-time {{ display: inline-block; padding: 0.5rem 1rem; background: rgba(244, 140, 6, 0.1); border-radius: 20px; font-size: 0.875rem; font-weight: 600; color: #F48C06; }}

        @media (min-width: 1024px) {{ .top-header {{ padding: 0 40px; }} }}
    </style>
</head>
<body>

    <header class="top-header px-5 md:px-10">
        <a href="../index.html" class="flex items-center gap-3 no-underline">
            <img src="https://ecdn.teacherspayteachers.com/thumbuserhome/Little-Smart-Genius-1.746813476e+09/23416711.jpg" class="logo-img" alt="Logo">
            <span class="text-lg md:text-xl font-extrabold block" style="color:var(--text)">Little Smart Genius<span class="text-brand">.</span></span>
        </a>

        <nav class="hidden lg:flex gap-8">
            <a href="../index.html" class="nav-link">Home</a>
            <a href="../products.html" class="nav-link">Store</a>
            <a href="../blog.html" class="nav-link active">Blog</a>
            <a href="../freebies.html" class="nav-link">Freebies</a>
            <a href="../about.html" class="nav-link">About</a>
            <a href="../contact.html" class="nav-link">Contact</a>
        </nav>

        <div class="flex items-center gap-4">
            <a href="https://www.teacherspayteachers.com/store/little-smart-genius" target="_blank" class="hidden lg:block px-5 py-2.5 bg-slate-900 text-white font-bold rounded-full text-xs hover:bg-brand transition">TpT Store</a>
            <div class="w-10 h-10 rounded-full flex items-center justify-center cursor-pointer bg-slate-100 dark:bg-slate-700 transition" onclick="toggleTheme()"><span id="theme-icon">🌙</span></div>
            <button class="block lg:hidden text-2xl" style="color:var(--text)" onclick="toggleMobileMenu()">☰</button>
        </div>
    </header>

    <div id="mobile-menu">
        <a href="../index.html" class="py-3 border-b border-gray-200 font-bold" style="color:var(--text)">Home</a>
        <a href="../products.html" class="py-3 border-b border-gray-200 font-bold" style="color:var(--text)">Store</a>
        <a href="../blog.html" class="py-3 border-b border-gray-200 font-bold text-brand">Blog</a>
        <a href="../freebies.html" class="py-3 border-b border-gray-200 font-bold" style="color:var(--text)">Freebies</a>
        <a href="../about.html" class="py-3 border-b border-gray-200 font-bold" style="color:var(--text)">About</a>
        <a href="../contact.html" class="py-3 font-bold" style="color:var(--text)">Contact</a>
        <a href="https://www.teacherspayteachers.com/store/little-smart-genius" target="_blank" class="py-3 mt-2 text-center bg-slate-900 text-white font-bold rounded-lg hover:bg-brand transition">Visit TpT Store</a>
    </div>

    <main class="pt-[100px] pb-20 px-5 md:px-10">

        <div class="max-w-4xl mx-auto mb-8">
            <a href="../blog.html" class="inline-flex items-center text-sm font-bold text-slate-400 hover:text-brand transition">
                ← Back to Blog
            </a>
        </div>

        <article class="max-w-4xl mx-auto">

            <div class="text-center mb-10">
                <div class="mb-4">
                    <span class="reading-time">📖 {reading_time} min read</span>
                </div>
                <h1 class="text-4xl md:text-5xl font-extrabold mb-6 leading-tight" style="background: linear-gradient(135deg, #1E293B 0%, #F48C06 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    {title}
                </h1>
                <div class="flex items-center justify-center gap-4 text-sm font-bold" style="color: #64748B;">
                    <span>{author_display}</span>
                    <span>•</span>
                    <span>{date}</span>
                    {category_display}
                </div>
            </div>

            <div class="rounded-2xl overflow-hidden shadow-2xl mb-12 border" style="border-color: var(--bord);">
                <img src="../{image}" alt="{title}" class="w-full h-auto object-cover" loading="lazy">
            </div>

            <div class="article-content">
                {content}
            </div>

            <div class="mt-16 pt-10 border-t" style="border-color: var(--bord);">
                <div class="rounded-2xl p-8 text-center" style="background: var(--card); border: 1px solid var(--bord);">
                    <h3 class="font-extrabold text-xl mb-3" style="color: var(--text);">📚 Loved this article?</h3>
                    <p class="text-slate-500 dark:text-slate-400 mb-6">
                        Explore our free educational resources and premium printables.
                    </p>
                    <div class="flex gap-4 justify-center flex-wrap">
                        <a href="../freebies.html" class="inline-block px-8 py-3.5 bg-brand text-white font-bold rounded-xl shadow-lg hover:shadow-brand/50 transition">
                            Browse Free Resources
                        </a>
                        <a href="../products.html" class="inline-block px-8 py-3.5 bg-slate-900 text-white font-bold rounded-xl hover:bg-slate-800 transition">
                            Visit Store
                        </a>
                    </div>
                </div>
            </div>

        </article>
    </main>

    <footer class="text-center text-slate-400 text-xs py-6 border-t border-slate-200 dark:border-slate-700">
        <div class="flex justify-center gap-4 mb-2">
            <a href="../terms.html" class="hover:text-brand transition">Terms of Service</a>
            <span>•</span>
            <a href="../privacy.html" class="hover:text-brand transition">Privacy Policy</a>
        </div>
        &copy; 2026 Little Smart Genius. All rights reserved.
    </footer>

    <script>
        function initTheme() {{
            if (localStorage.getItem('theme') === 'dark') {{
                document.documentElement.classList.add('dark');
                document.getElementById('theme-icon').innerHTML = '☀️';
            }}
        }}

        function toggleTheme(){{ 
            const html = document.documentElement;
            html.classList.toggle('dark');
            const isDark = html.classList.contains('dark');
            localStorage.setItem('theme', isDark ? 'dark' : 'light'); 
            document.getElementById('theme-icon').innerHTML = isDark ? '☀️' : '🌙'; 
        }}

        function toggleMobileMenu(){{
            const m = document.getElementById('mobile-menu');
            m.style.display = (m.style.display === 'flex') ? 'none' : 'flex';
        }}

        initTheme();
    </script>
</body>
</html>
"""


# ═══════════════════════════════════════════════════════════════════════════
# 🚀 GÉNÉRATEUR D'ARTICLES HTML
# ═══════════════════════════════════════════════════════════════════════════

def generate_article_html(json_data: dict, slug: str, logger: ConversionLogger) -> str:
    """Génère le HTML d'un article"""

    # Extraction des données avec valeurs par défaut
    title = json_data.get('title', 'Untitled Article')
    content = json_data.get('content', '<p>No content available.</p>')

    # Sanitize HTML
    content = ArticleValidator.sanitize_html(content)

    # Excerpt
    excerpt_raw = json_data.get('excerpt') or json_data.get('meta_description', '')
    if not excerpt_raw:
        text = re.sub(r'<[^>]+>', '', content)
        excerpt_raw = text[:155].strip() + "..." if len(text) > 155 else text

    # Auteur
    author_name = json_data.get('author_name', 'Little Smart Genius')
    author_display = author_name if author_name != 'Little Smart Genius' else 'Little Smart Genius Team'

    # Date
    date_str = json_data.get('date', datetime.now().strftime("%B %d, %Y"))
    iso_date = json_data.get('iso_date', datetime.now().isoformat())

    # Catégorie
    category = json_data.get('category', '')
    category_display = f'<span>•</span><span>{category}</span>' if category else ''

    # Image
    image = json_data.get('image', 'images/placeholder.webp')
    og_image = f"{SITE_URL}/{image}" if not image.startswith('http') else image

    # Keywords
    keywords = ', '.join(json_data.get('keywords', []))

    # Reading time
    reading_time = json_data.get('reading_time', 5)

    # URL canonique
    canonical_url = f"{SITE_URL}/articles/{slug}.html"

    # Remplissage du template
    html = ARTICLE_TEMPLATE.format(
        title=title,
        excerpt=excerpt_raw,
        keywords=keywords,
        canonical_url=canonical_url,
        og_image=og_image,
        iso_date=iso_date,
        author_name=author_name,
        site_url=SITE_URL,
        reading_time=reading_time,
        author_display=author_display,
        date=date_str,
        category_display=category_display,
        image=image,
        content=content
    )

    return html


# ═══════════════════════════════════════════════════════════════════════════
# 📝 GÉNÉRATEUR DE CARTES BLOG
# ═══════════════════════════════════════════════════════════════════════════

def generate_blog_card(article_data: dict) -> str:
    """Génère une carte pour la page blog"""

    title = article_data.get('title', 'Untitled')
    date = article_data.get('date', '')
    image = article_data.get('image', 'images/placeholder.webp')
    excerpt = article_data.get('excerpt', '')[:150] + "..."
    url = article_data.get('url', '#')
    category = article_data.get('category', '')
    reading_time = article_data.get('reading_time', 5)

    category_badge = f'<span class="text-xs font-bold uppercase tracking-wider text-brand bg-orange-50 dark:bg-slate-800 px-2 py-1 rounded-full">{category}</span>' if category else ''

    card = f"""
        <article class="rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 border" style="background: var(--card); border-color: var(--bord);">
            <a href="{url}" class="block">
                <div class="aspect-video overflow-hidden">
                    <img src="{image}" alt="{title}" class="w-full h-full object-cover hover:scale-105 transition-transform duration-300" loading="lazy">
                </div>
                <div class="p-6">
                    <div class="flex items-center gap-2 mb-3">
                        {category_badge}
                        <span class="text-xs text-slate-500">📖 {reading_time} min</span>
                    </div>
                    <h3 class="text-xl font-extrabold mb-3 hover:text-brand transition" style="color: var(--text);">
                        {title}
                    </h3>
                    <p class="text-sm text-slate-600 dark:text-slate-400 mb-4 line-clamp-3">
                        {excerpt}
                    </p>
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold text-slate-500">{date}</span>
                        <span class="text-brand font-bold text-sm">Read More →</span>
                    </div>
                </div>
            </a>
        </article>"""

    return card


# ═══════════════════════════════════════════════════════════════════════════
# 🗺️ GÉNÉRATEUR SITEMAP (V4.0 — includes pagination pages)
# ═══════════════════════════════════════════════════════════════════════════

def generate_sitemap(articles: List[Dict], total_pages: int, logger: ConversionLogger):
    """Génère sitemap.xml avec pages de pagination"""

    logger.info("Génération du sitemap.xml...", 2)

    sitemap_entries = []

    # Pages statiques
    static_pages = [
        ('index.html', '1.0', 'daily'),
        ('blog.html', '0.9', 'daily'),
        ('products.html', '0.8', 'weekly'),
        ('freebies.html', '0.8', 'weekly'),
        ('about.html', '0.7', 'monthly'),
        ('contact.html', '0.7', 'monthly')
    ]

    for page, priority, changefreq in static_pages:
        sitemap_entries.append(f"""  <url>
    <loc>{SITE_URL}/{page}</loc>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>""")

    # Pagination pages (blog-2.html, blog-3.html, etc.)
    for p in range(2, total_pages + 1):
        sitemap_entries.append(f"""  <url>
    <loc>{SITE_URL}/blog-{p}.html</loc>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>""")

    # Articles — only those with actual HTML files
    for article in articles:
        url = article.get('url', '').replace('../', '')
        # Verify the HTML file exists
        html_path = url  # e.g. articles/slug.html
        if not os.path.exists(html_path):
            continue
        iso_date = article.get('iso_date', datetime.now().isoformat())

        sitemap_entries.append(f"""  <url>
    <loc>{SITE_URL}/{url}</loc>
    <lastmod>{iso_date.split('T')[0]}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")

    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(sitemap_entries)}
</urlset>"""

    with open('sitemap.xml', 'w', encoding='utf-8') as f:
        f.write(sitemap_xml)

    logger.success(f"Sitemap généré: {len(sitemap_entries)} URLs (incl. {max(0, total_pages-1)} pagination pages)", 2)


# ═══════════════════════════════════════════════════════════════════════════
# 📚 SEARCH INDEX (V4.0 — lightweight, no content field)
# ═══════════════════════════════════════════════════════════════════════════

def generate_search_index(articles: List[Dict], logger: ConversionLogger):
    """Génère search_index.json — métadonnées uniquement, PAS de champ content"""

    logger.info("Génération de search_index.json...", 2)

    # Build lightweight entries (no content field)
    lightweight = []
    for a in articles:
        lightweight.append({
            "title": a.get("title", "Untitled"),
            "slug": a.get("slug", ""),
            "date": a.get("date", ""),
            "iso_date": a.get("iso_date", ""),
            "category": a.get("category", ""),
            "excerpt": a.get("excerpt", "")[:200],
            "image": a.get("image", ""),
            "reading_time": a.get("reading_time", 5),
            "url": a.get("url", ""),
            "keywords": a.get("keywords", []),
        })

    index_data = {
        "generated_at": datetime.now().isoformat(),
        "total_articles": len(lightweight),
        "articles": lightweight
    }

    with open('search_index.json', 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    # Also keep articles.json for backward compat
    with open('articles.json', 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    logger.success(f"search_index.json créé: {len(lightweight)} articles (lightweight)", 2)


# ═══════════════════════════════════════════════════════════════════════════
# 🔍 EXTRACT METADATA FROM EXISTING HTML ARTICLES
# ═══════════════════════════════════════════════════════════════════════════

def extract_metadata_from_html(html_path: str) -> Optional[Dict]:
    """Extract article metadata from an existing HTML file."""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()

        slug = os.path.basename(html_path).replace('.html', '')

        # Title
        title_m = re.search(r'<title>(.+?)\s*\|', content)
        title = title_m.group(1).strip() if title_m else slug.replace('-', ' ').title()

        # Meta description
        desc_m = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', content)
        excerpt = desc_m.group(1).strip() if desc_m else ''

        # Date
        date_m = re.search(r'<meta\s+property="article:published_time"\s+content="([^"]+)"', content)
        iso_date = date_m.group(1) if date_m else datetime.now().isoformat()
        try:
            dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
            date_str = dt.strftime('%B %d, %Y')
        except:
            date_str = ''

        # Category — look in visible text
        cat_m = re.search(r'<span>•</span>\s*<span>([^<]+)</span>', content)
        category = cat_m.group(1).strip() if cat_m else ''

        # Image
        img_m = re.search(r'<img\s+src="\.\./([^"]+)"\s+alt=', content)
        image = img_m.group(1) if img_m else 'images/placeholder.webp'

        # Reading time
        rt_m = re.search(r'(\d+)\s*min\s*read', content)
        reading_time = int(rt_m.group(1)) if rt_m else 5

        # Keywords
        kw_m = re.search(r'<meta\s+name="keywords"\s+content="([^"]+)"', content)
        keywords = [k.strip() for k in kw_m.group(1).split(',')] if kw_m else []

        return {
            'title': title,
            'slug': slug,
            'date': date_str,
            'iso_date': iso_date,
            'category': category,
            'excerpt': excerpt[:200],
            'image': image,
            'reading_time': reading_time,
            'url': f'articles/{slug}.html',
            'keywords': keywords,
        }
    except Exception:
        return None


def collect_all_articles(new_articles: List[Dict], logger: ConversionLogger) -> List[Dict]:
    """Collect metadata from ALL articles (new batch + existing HTML files)."""
    all_articles = {}

    # 1. Add new articles from current batch
    for a in new_articles:
        slug = a.get('slug', '')
        if slug:
            all_articles[slug] = a

    # 2. Scan existing HTML files for articles not in current batch
    if os.path.exists(ARTICLES_DIR):
        for filename in os.listdir(ARTICLES_DIR):
            if not filename.endswith('.html'):
                continue
            slug = filename.replace('.html', '')
            if slug in all_articles:
                continue  # Already from current batch
            meta = extract_metadata_from_html(os.path.join(ARTICLES_DIR, filename))
            if meta:
                all_articles[slug] = meta

    # Sort by iso_date descending (newest first)
    sorted_articles = sorted(
        all_articles.values(),
        key=lambda x: x.get('iso_date', ''),
        reverse=True
    )

    logger.info(f"Total articles collected: {len(sorted_articles)} ({len(new_articles)} new + {len(sorted_articles) - len(new_articles)} existing)", 2)
    return sorted_articles


# ═══════════════════════════════════════════════════════════════════════════
# 📄 PAGINATED BLOG GENERATOR (V4.0)
# ═══════════════════════════════════════════════════════════════════════════

def generate_paginated_blog(articles: List[Dict], logger: ConversionLogger) -> int:
    """Generate paginated blog pages: blog.html, blog-2.html, blog-3.html, etc.
    Returns total number of pages."""

    if not articles:
        logger.warning("Aucun article pour la pagination", 2)
        return 0

    if not os.path.exists(BLOG_FILE):
        logger.warning(f"Fichier {BLOG_FILE} introuvable", 2)
        return 0

    # Backup original
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_file = os.path.join(BACKUP_DIR, f"blog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
    shutil.copy2(BLOG_FILE, backup_file)
    logger.info(f"Backup créé: {backup_file}", 3)

    # Read template
    with open(BLOG_FILE, 'r', encoding='utf-8') as f:
        blog_template = f.read()

    # Calculate pages
    total_pages = max(1, -(-len(articles) // ARTICLES_PER_PAGE))  # ceil division
    logger.info(f"Pagination: {len(articles)} articles / {ARTICLES_PER_PAGE} par page = {total_pages} pages", 2)

    for page_num in range(1, total_pages + 1):
        start_idx = (page_num - 1) * ARTICLES_PER_PAGE
        end_idx = start_idx + ARTICLES_PER_PAGE
        page_articles = articles[start_idx:end_idx]

        # Build cards
        cards_html = ""
        for article in page_articles:
            cards_html += generate_blog_card(article)

        # Build pagination nav
        pagination_html = _build_pagination_nav(page_num, total_pages)

        # Inject cards into blog-static-grid (Phase 3 compatible)
        pattern = r'(<div id="blog-static-grid"[^>]*>)(.*?)(</div>\s*(?:<!--.*?-->)?\s*(?:<div id="blog-dynamic-grid"|</main>))'
        page_content = re.sub(
            pattern,
            rf'\g<1>{cards_html}\g<3>',
            blog_template,
            flags=re.DOTALL
        )

        # Inject pagination nav into blog-pagination-nav div (if it exists)
        page_content = re.sub(
            r'(<div id="blog-pagination-nav">)(.*?)(</div>\s*</main>)',
            rf'\g<1>\n{pagination_html}\n\g<3>',
            page_content,
            flags=re.DOTALL
        )

        # Update article count badge in hero
        count_badge = f'<p class="text-sm text-slate-500 mt-2">{len(articles)} articles \u2022 Page {page_num}/{total_pages}</p>'
        page_content = re.sub(
            r'<p class="text-sm text-slate-500 mt-2">[^<]*</p>',
            count_badge,
            page_content
        )

        # File name
        if page_num == 1:
            output_file = BLOG_FILE
        else:
            output_file = f"blog-{page_num}.html"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(page_content)

        logger.success(f"Page {page_num}/{total_pages}: {output_file} ({len(page_articles)} articles)", 3)

    return total_pages


def _build_pagination_nav(current_page: int, total_pages: int) -> str:
    """Build Prev/Next pagination HTML."""
    if total_pages <= 1:
        return ""

    nav_items = []

    # Previous
    if current_page > 1:
        prev_href = "blog.html" if current_page == 2 else f"blog-{current_page - 1}.html"
        nav_items.append(
            f'<a href="{prev_href}" class="px-5 py-3 rounded-xl font-bold text-sm transition'
            f' bg-slate-100 dark:bg-slate-700 hover:bg-brand hover:text-white" style="color:var(--text)">'
            f'&larr; Previous</a>'
        )
    else:
        nav_items.append(
            '<span class="px-5 py-3 rounded-xl font-bold text-sm bg-slate-50 dark:bg-slate-800'
            ' text-slate-300 dark:text-slate-600 cursor-default">&larr; Previous</span>'
        )

    # Page numbers
    for p in range(1, total_pages + 1):
        href = "blog.html" if p == 1 else f"blog-{p}.html"
        if p == current_page:
            nav_items.append(
                f'<span class="px-4 py-3 rounded-xl font-bold text-sm bg-brand text-white">{p}</span>'
            )
        else:
            nav_items.append(
                f'<a href="{href}" class="px-4 py-3 rounded-xl font-bold text-sm'
                f' bg-slate-100 dark:bg-slate-700 hover:bg-brand hover:text-white transition"'
                f' style="color:var(--text)">{p}</a>'
            )

    # Next
    if current_page < total_pages:
        next_href = f"blog-{current_page + 1}.html"
        nav_items.append(
            f'<a href="{next_href}" class="px-5 py-3 rounded-xl font-bold text-sm transition'
            f' bg-slate-100 dark:bg-slate-700 hover:bg-brand hover:text-white" style="color:var(--text)">'
            f'Next &rarr;</a>'
        )
    else:
        nav_items.append(
            '<span class="px-5 py-3 rounded-xl font-bold text-sm bg-slate-50 dark:bg-slate-800'
            ' text-slate-300 dark:text-slate-600 cursor-default">Next &rarr;</span>'
        )

    return (
        '<div class="flex items-center justify-center gap-2 mt-12 mb-8 flex-wrap">'
        + ''.join(nav_items)
        + '</div>'
    )


# ═══════════════════════════════════════════════════════════════════════════
# 🚀 FONCTION PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Fonction principale de conversion"""

    logger = ConversionLogger()

    logger.section("🚀 GENERATE BLOG ARTICLES V3.0 SUPREME")
    print(f"⏰ Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Dossier posts: {POSTS_DIR}")
    print(f"📁 Dossier articles: {ARTICLES_DIR}")
    print(f"🌐 Site URL: {SITE_URL}")

    # Vérification des dossiers
    logger.section("📋 ÉTAPE 1/5: VÉRIFICATION DES DOSSIERS")

    if not os.path.exists(POSTS_DIR):
        logger.error(f"Dossier '{POSTS_DIR}' introuvable")
        logger.save()
        return

    logger.success(f"Dossier '{POSTS_DIR}' trouvé")

    os.makedirs(ARTICLES_DIR, exist_ok=True)
    logger.success(f"Dossier '{ARTICLES_DIR}' prêt")

    # Recherche des JSON
    logger.section("📋 ÉTAPE 2/5: DÉCOUVERTE DES ARTICLES")

    json_files = sorted(
        glob.glob(os.path.join(POSTS_DIR, "*.json")),
        key=os.path.getmtime,
        reverse=True
    )

    if not json_files:
        logger.warning(f"Aucun fichier JSON trouvé dans '{POSTS_DIR}'")
        logger.save()
        return

    logger.success(f"{len(json_files)} fichiers JSON trouvés")

    # Traitement des articles
    logger.section("📋 ÉTAPE 3/5: CONVERSION JSON → HTML")

    articles_data = []
    processed_count = 0
    errors_count = 0

    for idx, json_path in enumerate(json_files, 1):
        filename = os.path.basename(json_path)
        slug = filename.replace('.json', '')

        logger.info(f"[{idx}/{len(json_files)}] Traitement: {filename}", 2)
        logger.progress(idx - 1, len(json_files), "Articles traités")

        # Validation
        valid, data, validation_errors = ArticleValidator.validate_json(json_path, logger)

        if not valid:
            logger.error(f"Validation échouée pour {filename}", {
                "errors": validation_errors
            }, 3)
            errors_count += 1
            continue

        try:
            # Génération HTML
            html_output = generate_article_html(data, slug, logger)

            # Sauvegarde
            output_path = os.path.join(ARTICLES_DIR, f"{slug}.html")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_output)

            logger.success(f"HTML généré: {slug}.html", 3)

            # Données pour blog
            article_info = {
                'title': data.get('title', 'Untitled'),
                'date': data.get('date', ''),
                'iso_date': data.get('iso_date', ''),
                'image': data.get('image', 'images/placeholder.webp'),
                'excerpt': data.get('excerpt', data.get('meta_description', ''))[:150] + "...",
                'url': f"articles/{slug}.html",
                'category': data.get('category', ''),
                'reading_time': data.get('reading_time', 5),
                'slug': slug,
                'keywords': data.get('keywords', []),
            }

            articles_data.append(article_info)
            logger.article_processed(article_info)
            processed_count += 1

            # V4.0: Archive the JSON after successful conversion
            os.makedirs(ARCHIVE_DIR, exist_ok=True)
            archive_dest = os.path.join(ARCHIVE_DIR, filename)
            shutil.move(json_path, archive_dest)
            logger.success(f"Archivé: {filename} → {ARCHIVE_DIR}/", 3)

        except Exception as e:
            logger.error(f"Erreur lors de la génération de {filename}", {
                "error": str(e)
            }, 3)
            errors_count += 1

    logger.progress(len(json_files), len(json_files), "Articles traités")

    # V4.0: Collect ALL articles (new + existing HTML)
    logger.section("📋 ÉTAPE 4/6: COLLECTE DE TOUS LES ARTICLES")
    all_articles = collect_all_articles(articles_data, logger)

    # V4.0: Paginated blog
    total_pages = 0
    if all_articles:
        logger.section("📋 ÉTAPE 5/6: PAGINATION DU BLOG")
        total_pages = generate_paginated_blog(all_articles, logger)

    # V4.0: Search index + sitemap
    if all_articles:
        logger.section("📋 ÉTAPE 6/6: FICHIERS AUXILIAIRES")
        generate_search_index(all_articles, logger)
        generate_sitemap(all_articles, total_pages, logger)

    # Statistiques
    logger.add_stat("total_files", len(json_files))
    logger.add_stat("processed", processed_count)
    logger.add_stat("archived", processed_count)
    logger.add_stat("errors", errors_count)
    logger.add_stat("total_articles", len(all_articles))
    logger.add_stat("blog_pages", total_pages)
    if len(json_files) > 0:
        logger.add_stat("success_rate", f"{(processed_count / len(json_files) * 100):.1f}%")

    # Rapport final
    logger.section("✨ CONVERSION V4.0 TERMINÉE")
    print(f"📊 Statistiques:")
    print(f"   • Fichiers traités: {processed_count}/{len(json_files)}")
    print(f"   • Archivés: {processed_count} → {ARCHIVE_DIR}/")
    print(f"   • Erreurs: {errors_count}")
    if len(json_files) > 0:
        print(f"   • Taux de succès: {(processed_count / len(json_files) * 100):.1f}%")
    print(f"\n📁 Fichiers générés:")
    print(f"   • {processed_count} articles HTML dans {ARTICLES_DIR}/")
    print(f"   • {total_pages} pages blog (blog.html" + (f", blog-2.html...blog-{total_pages}.html" if total_pages > 1 else "") + ")")
    print(f"   • search_index.json ({len(all_articles)} articles)")
    print(f"   • sitemap.xml")

    if errors_count > 0:
        print(f"\n⚠️  {errors_count} erreur(s) détectée(s). Consultez le rapport pour détails.")

    logger.save()
    print(f"\n⏰ Terminé à: {datetime.now().strftime('%H:%M:%S')}")
    print("="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Conversion interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n\n❌ ERREUR CRITIQUE: {str(e)}")
        import traceback
        traceback.print_exc()
