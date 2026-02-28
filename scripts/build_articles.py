"""
BUILD ARTICLES — Converts post JSONs into HTML pages + rebuilds indexes
Reads all posts/*.json, generates articles/*.html, search_index.json,
articles.json, and sitemap.xml.
"""
import os
import traceback
import sys
import io
import json
import re
import glob
import urllib.parse
from datetime import datetime

# Fix Windows terminal encoding
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
BASE_DIR = PROJECT_ROOT
POSTS_DIR = os.path.join(PROJECT_ROOT, "posts")
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
SITE_URL = "https://littlesmartgenius.com"

os.makedirs(ARTICLES_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# ARTICLE HTML TEMPLATE — matches index.html design system
# ═══════════════════════════════════════════════════════════════

def normalize_image_path(path):
    """Convert absolute server paths to relative web paths and enforce .webp format."""
    if not path or path.startswith('http'):
        return path
    # Extract just the filename from any absolute path
    basename = os.path.basename(path)
    if basename:
        # Enforce .webp extension for all images
        if basename.lower().endswith('.jpg') or basename.lower().endswith('.jpeg'):
            basename = basename.rsplit('.', 1)[0] + '.webp'
        elif basename.lower().endswith('.png'):
            basename = basename.rsplit('.', 1)[0] + '.webp'
        return f"images/{basename}"
    return path

ARTICLE_TEMPLATE = """<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | Little Smart Genius</title>
    <meta name="description" content="{excerpt}">
    <meta name="keywords" content="{keywords}">
    <link rel="canonical" href="{canonical_url}">
    <link rel="icon" href="https://ecdn.teacherspayteachers.com/thumbuserhome/Little-Smart-Genius-1746813476/23416711.jpg" type="image/jpeg">

    <!-- Open Graph -->
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{excerpt}">
    <meta property="og:image" content="{og_image}">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:type" content="article">
    <meta property="article:published_time" content="{iso_date}">
    <meta property="article:author" content="{author_name}">

    <!-- Tailwind -->
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Source+Serif+4:ital,opsz,wght@0,8..60,300;0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">

    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{ extend: {{ colors: {{ brand: '#F48C06' }} }} }}
        }}
    </script>

    <style>
        :root {{
            --bg: #FAFAFA;
            --text: #1E293B;
            --card: #FFFFFF;
            --head: rgba(255, 255, 255, 0.95);
            --bord: #E2E8F0;
        }}

        .dark {{
            --bg: #0F172A;
            --text: #F8FAFC;
            --card: #1E293B;
            --head: rgba(15, 23, 42, 0.95);
            --bord: #334155;
        }}

        body {{
            font-family: 'Outfit', sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            transition: 0.3s;
        }}

        /* HEADER - IDENTIQUE A INDEX.HTML (80px) */
        .top-header {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 80px;
            background: var(--head);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--bord);
            z-index: 50;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            transition: 0.3s;
        }}

        /* LOGO - STYLE IDENTIQUE */
        .logo-img {{
            width: 45px;
            height: 45px;
            border-radius: 50%;
            border: 2px solid #F48C06;
            object-fit: cover;
        }}

        /* NAV LINK - STYLE IDENTIQUE */
        .nav-link {{
            font-weight: 700;
            color: #64748B;
            text-decoration: none;
            transition: 0.2s;
        }}

        .nav-link:hover,
        .nav-link.active {{
            color: #F48C06;
        }}

        /* MOBILE MENU - TOP 80px */
        #mobile-menu {{
            display: none;
            position: fixed;
            top: 80px;
            left: 0;
            right: 0;
            background: var(--card);
            border-bottom: 1px solid var(--bord);
            flex-direction: column;
            padding: 20px;
            z-index: 49;
        }}

        /* HERO TITLE GRADIENT */
        .hero-title {{
            background: linear-gradient(135deg, #1E293B 0%, #F48C06 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .dark .hero-title {{
            background: linear-gradient(135deg, #FFFFFF 0%, #F48C06 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        /* ARTICLE CONTENT STYLES — airy, elegant, uniform */
        .article-content {{
            font-family: 'Source Serif 4', Georgia, 'Times New Roman', serif;
            font-size: 1.125rem;
            line-height: 1.9;
            color: var(--text);
            word-spacing: 0.02em;
            letter-spacing: 0.01em;
        }}
        .article-content h2 {{ font-family: 'Outfit', sans-serif; font-size: 1.75rem; font-weight: 900; margin-top: 3rem; margin-bottom: 1.25rem; color: var(--text); border-left: 4px solid #F48C06; padding-left: 1rem; line-height: 1.3; letter-spacing: -0.01em; }}
        .article-content h3 {{ font-family: 'Outfit', sans-serif; font-size: 1.25rem; font-weight: 800; margin-top: 2.25rem; margin-bottom: 1rem; color: var(--text); line-height: 1.4; letter-spacing: 0; }}
        .article-content p {{ margin-top: 0; margin-bottom: 1.75rem; }}
        .article-content ul {{ list-style-type: disc; padding-left: 2rem; margin-bottom: 1.75rem; }}
        .article-content ol {{ padding-left: 2rem; margin-bottom: 1.75rem; }}
        .article-content li {{ margin-bottom: 0.6rem; }}
        .article-content strong {{ color: #F48C06; font-weight: 700; }}
        .article-content a {{ color: #F48C06; text-decoration: underline; text-underline-offset: 3px; transition: 0.2s; }}
        .article-content a:hover {{ color: #E07B00; }}
        .article-content a.internal-link {{ text-decoration-style: dotted; }}
        .article-content a.internal-link:hover {{ text-decoration-style: solid; }}
        .article-content img {{ border-radius: 12px; margin: 2.5rem 0; width: 100%; box-shadow: 0 10px 30px -10px rgba(0,0,0,0.15); }}
        .article-content figure {{ margin: 2.5rem 0; }}
        .article-content figure img {{ margin: 0; }}
        .article-content figcaption {{ text-align: center; font-size: 0.875rem; color: #94A3B8; margin-top: 0.75rem; font-style: italic; }}
        .article-content blockquote {{ border-left: 4px solid #F48C06; background: rgba(244, 140, 6, 0.08); padding: 1.5rem 1.75rem; margin: 2rem 0; border-radius: 0 12px 12px 0; font-style: italic; }}

        .reading-time {{ display: inline-block; padding: 0.5rem 1rem; background: rgba(244, 140, 6, 0.1); border-radius: 20px; font-size: 0.875rem; font-weight: 600; color: #F48C06; }}

        /* SCROLL-TO-TOP BUTTON */
        #scrollTopBtn {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 55;
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: linear-gradient(135deg, #F48C06, #E07B00);
            color: #FFF;
            border: none;
            cursor: pointer;
            font-size: 20px;
            box-shadow: 0 4px 15px rgba(244, 140, 6, 0.4);
            opacity: 0;
            visibility: hidden;
            transform: translateY(20px);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        #scrollTopBtn.visible {{
            opacity: 1;
            visibility: visible;
            transform: translateY(0);
        }}
        #scrollTopBtn:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(244, 140, 6, 0.5);
        }}

        /* PREV / NEXT ARTICLE NAV */
        .article-nav {{
            position: fixed;
            top: 50%;
            transform: translateY(-50%);
            z-index: 50;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
        }}
        .article-nav.visible {{
            opacity: 1;
            visibility: visible;
        }}
        .article-nav a {{
            display: flex;
            align-items: center;
            justify-content: center;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: var(--card);
            border: 2px solid var(--bord);
            color: var(--text);
            font-size: 18px;
            text-decoration: none;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }}
        .article-nav a:hover {{
            background: #F48C06;
            color: #fff;
            border-color: #F48C06;
            transform: scale(1.1);
            box-shadow: 0 6px 20px rgba(244, 140, 6, 0.4);
        }}
        .article-nav-prev {{ left: 15px; }}
        .article-nav-next {{ right: 15px; }}
        .article-nav .nav-title {{
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            background: var(--card);
            border: 1px solid var(--bord);
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 700;
            color: var(--text);
            white-space: nowrap;
            max-width: 180px;
            overflow: hidden;
            text-overflow: ellipsis;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            opacity: 0;
            transition: opacity 0.2s;
            pointer-events: none;
        }}
        .article-nav-prev .nav-title {{ left: 56px; }}
        .article-nav-next .nav-title {{ right: 56px; }}
        .article-nav a:hover + .nav-title,
        .article-nav a:hover ~ .nav-title {{ opacity: 1; }}
        @media (max-width: 1280px) {{
            .article-nav .nav-title {{ display: none; }}
        }}
        @media (max-width: 768px) {{
            .article-nav a {{ width: 36px; height: 36px; font-size: 14px; }}
            .article-nav-prev {{ left: 8px; }}
            .article-nav-next {{ right: 8px; }}
        }}

        /* SHARE BUTTONS */
        .share-bar {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin-top: 1.5rem;
            flex-wrap: wrap;
        }}
        .share-bar span {{
            font-size: 0.8rem;
            font-weight: 700;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .share-btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            text-decoration: none;
            transition: all 0.3s ease;
            border: 1px solid var(--bord);
            background: var(--card);
        }}
        .share-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }}
        .share-btn svg {{
            width: 18px;
            height: 18px;
        }}
        .share-btn.fb {{ color: #1877F2; }}
        .share-btn.fb:hover {{ background: #1877F2; color: #fff; border-color: #1877F2; }}
        .share-btn.ig {{ color: #E4405F; }}
        .share-btn.ig:hover {{ background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); color: #fff; border-color: #E4405F; }}
        .share-btn.tw {{ color: #000; }} .dark .share-btn.tw {{ color: #fff; }}
        .share-btn.tw:hover {{ background: #000; color: #fff; border-color: #000; }}
        .share-btn.pi {{ color: #E60023; }}
        .share-btn.pi:hover {{ background: #E60023; color: #fff; border-color: #E60023; }}
        .share-btn.wa {{ color: #25D366; }}
        .share-btn.wa:hover {{ background: #25D366; color: #fff; border-color: #25D366; }}
        .share-btn.cp {{ color: #64748B; }}
        .share-btn.cp:hover {{ background: #64748B; color: #fff; border-color: #64748B; }}

        /* SOCIAL FOOTER ICONS */
        .social-footer-bar {{ display: flex; justify-content: center; gap: 16px; padding: 20px 0 10px; }}
        .social-footer-bar a {{
            width: 40px; height: 40px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            background: rgba(244, 140, 6, 0.1); color: #F48C06;
            transition: all 0.3s; text-decoration: none;
        }}
        .social-footer-bar a:hover {{ background: #F48C06; color: #fff; transform: translateY(-2px); }}
        .social-footer-bar svg {{ width: 20px; height: 20px; }}

        /* SITE FOOTER TEXT */
        .site-footer {{
            text-align: center;
            padding: 15px 20px 25px;
            color: #94A3B8;
            font-size: 0.75rem;
        }}
        .site-footer a {{ color: #94A3B8; text-decoration: none; transition: 0.2s; }}
        .site-footer a:hover {{ color: #F48C06; }}

        @media (max-width: 1024px) {{
            .top-header {{
                padding: 0 20px;
            }}
        }}

        @media (min-width: 1024px) {{
            .top-header {{
                padding: 0 40px;
            }}
        }}
    </style>
    <!-- Google Analytics GA4 -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-1S8G205JX2"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', 'G-1S8G205JX2');
    </script>
</head>
<body>

    <header class="top-header px-5 md:px-10">
        <a href="../index.html" class="flex items-center gap-3 no-underline">
            <img src="https://ecdn.teacherspayteachers.com/thumbuserhome/Little-Smart-Genius-1746813476/23416711.jpg"
                class="logo-img" alt="Logo">
            <span class="text-lg md:text-xl font-extrabold block" style="color:var(--text)">Little Smart Genius<span
                    class="text-brand">.</span></span>
        </a>

        <nav class="hidden lg:flex gap-8">
            <a href="../index.html" class="nav-link">Home</a>
            <a href="../products.html" class="nav-link">Store</a>
            <a href="../freebies.html" class="nav-link">Freebies</a>
            <a href="../blog.html" class="nav-link active">Blog</a>
            <a href="../about.html" class="nav-link">About</a>
            <a href="../contact.html" class="nav-link">Contact</a>
        </nav>

        <div class="flex items-center gap-4">
            <div class="hidden lg:flex items-center gap-2 mr-3">
                <a href="https://www.instagram.com/littlesmartgenius_com/" target="_blank" rel="noopener" title="Instagram" class="w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:text-white hover:bg-gradient-to-br hover:from-purple-500 hover:to-pink-500 transition-all duration-300">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>
                </a>
                <a href="https://www.pinterest.com/littlesmartgenius_com/" target="_blank" rel="noopener" title="Pinterest" class="w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:text-white hover:bg-red-500 transition-all duration-300">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.174.271-.401.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.607 0 11.985-5.365 11.985-11.987C23.97 5.39 18.592.026 11.985.026L12.017 0z"/></svg>
                </a>
                <a href="https://medium.com/@littlesmartgenius-com" target="_blank" rel="noopener" title="Medium" class="w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 transition-all duration-300">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M13.54 12a6.8 6.8 0 01-6.77 6.82A6.8 6.8 0 010 12a6.8 6.8 0 016.77-6.82A6.8 6.8 0 0113.54 12zM20.96 12c0 3.54-1.51 6.42-3.38 6.42-1.87 0-3.39-2.88-3.39-6.42s1.52-6.42 3.39-6.42 3.38 2.88 3.38 6.42M24 12c0 3.17-.53 5.75-1.19 5.75-.66 0-1.19-2.58-1.19-5.75s.53-5.75 1.19-5.75C23.47 6.25 24 8.83 24 12z"/></svg>
                </a>
            </div>
            <a href="https://www.teacherspayteachers.com/store/little-smart-genius" target="_blank"
                class="hidden lg:block px-5 py-2.5 bg-slate-900 text-white font-bold rounded-full text-xs hover:bg-brand transition">TpT
                Store</a>
            <div class="w-10 h-10 rounded-full flex items-center justify-center cursor-pointer bg-slate-100 dark:bg-slate-700 transition"
                onclick="toggleTheme()"><span id="theme-icon">&#127769;</span></div>
            <button class="block lg:hidden text-2xl" style="color:var(--text)" onclick="toggleMobileMenu()">&#9776;</button>
        </div>
    </header>

    <div id="mobile-menu">
        <a href="../index.html" class="py-3 border-b border-gray-200 font-bold" style="color:var(--text)">Home</a>
        <a href="../products.html" class="py-3 border-b border-gray-200 font-bold" style="color:var(--text)">Store</a>
        <a href="../freebies.html" class="py-3 border-b border-gray-200 font-bold" style="color:var(--text)">Freebies</a>
        <a href="../blog.html" class="py-3 border-b border-gray-200 font-bold text-brand">Blog</a>
        <a href="../about.html" class="py-3 border-b border-gray-200 font-bold" style="color:var(--text)">About</a>
        <a href="../contact.html" class="py-3 font-bold" style="color:var(--text)">Contact</a>
        <a href="https://www.teacherspayteachers.com/store/little-smart-genius" target="_blank"
            class="py-3 mt-2 text-center bg-slate-900 text-white font-bold rounded-lg hover:bg-brand transition">Visit
            TpT Store</a>
    </div>

    <main class="pt-[100px] pb-20 px-5 md:px-10">

        <div class="max-w-4xl mx-auto mb-8">
            {breadcrumb_html}
        </div>

        <article class="max-w-4xl mx-auto">

            <div class="text-center mb-10">
                <div class="mb-4">
                    <span class="reading-time">&#128214; {reading_time} min read</span>
                </div>
                <h1 class="text-4xl md:text-5xl font-extrabold mb-6 leading-tight hero-title">
                    {title}
                </h1>
                <div class="flex items-center justify-center gap-4 text-sm font-bold" style="color: #64748B;">
                    <span>{author_display}</span>
                    <span>&bull;</span>
                    <span>{date}</span>
                    {category_display}
                </div>

                <!-- SHARE BUTTONS -->
                <div class="share-bar">
                    <span>Share</span>
                    <a href="https://www.facebook.com/sharer/sharer.php?u={canonical_url}" target="_blank" rel="noopener" class="share-btn fb" title="Share on Facebook">
                        <svg fill="currentColor" viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
                    </a>
                    <a href="https://www.instagram.com/littlesmartgenius_com/" target="_blank" rel="noopener" class="share-btn ig" title="Share on Instagram">
                        <svg fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>
                    </a>
                    <a href="https://twitter.com/intent/tweet?url={canonical_url}&text={title}" target="_blank" rel="noopener" class="share-btn tw" title="Share on X">
                        <svg fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                    </a>
                    <a href="https://pinterest.com/pin/create/button/?url={canonical_url}&description={title}" target="_blank" rel="noopener" class="share-btn pi" title="Pin on Pinterest">
                        <svg fill="currentColor" viewBox="0 0 24 24"><path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.174.271-.401.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.607 0 11.985-5.365 11.985-11.987C23.97 5.39 18.592.026 11.985.026L12.017 0z"/></svg>
                    </a>
                    <a href="https://api.whatsapp.com/send?text={title}%20{canonical_url}" target="_blank" rel="noopener" class="share-btn wa" title="Share on WhatsApp">
                        <svg fill="currentColor" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
                    </a>
                    <button onclick="copyArticleUrl()" class="share-btn cp" title="Copy link">
                        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/></svg>
                    </button>
                </div>
            </div>

            <div class="rounded-2xl overflow-hidden shadow-2xl mb-12 border" style="border-color: var(--bord); aspect-ratio: 1200/630;">
                <img
                    src="../{image}"
                    srcset="../{thumb_image} 480w, ../{image} 1200w"
                    sizes="(max-width: 768px) 480px, 1200px"
                    alt="{title}"
                    class="w-full h-auto object-cover"
                    fetchpriority="high"
                    width="1200" height="630"
                    style="background: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9IiNlMmU4ZjAiLz48L3N2Zz4=') center/cover; background-color: var(--bord);"
                >
            </div>

            <div class="article-content">
                {content}
            </div>

            <!-- CTA SECTION -->
            <div class="mt-16 pt-10 border-t" style="border-color: var(--bord);">
                <div class="rounded-2xl p-8 text-center" style="background: var(--card); border: 1px solid var(--bord);">
                    <h3 class="font-extrabold text-xl mb-3" style="color: var(--text);">&#128218; Loved this article?</h3>
                    <p class="text-slate-500 dark:text-slate-400 mb-6">
                        Explore our free educational resources and premium printables.
                    </p>
                    <div class="flex gap-4 justify-center flex-wrap">
                        <a href="../freebies.html" class="inline-block px-8 py-3.5 font-bold rounded-xl shadow-lg transition" style="background: #F48C06; color: #FFFFFF;">
                            Browse Free Resources
                        </a>
                        <a href="../products.html" class="inline-block px-8 py-3.5 bg-slate-900 text-white font-bold rounded-xl hover:bg-slate-800 transition">
                            Visit Store
                        </a>
                    </div>
                </div>
            </div>

            <!-- RELATED ARTICLES — injected by _post_process.py only -->

        </article>
    </main>

    <!-- Cookie Banner -->
    <div id="cookie-banner"
        class="hidden fixed bottom-4 right-4 md:bottom-6 md:right-6 max-w-sm w-full bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700 z-[60] transition-all duration-500 translate-y-20 opacity-0">
        <div class="flex items-start gap-4">
            <div class="text-3xl">&#127850;</div>
            <div>
                <h3 class="font-bold text-slate-900 dark:text-white mb-1">Cookie Policy</h3>
                <p class="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-4">
                    We use cookies to analyze traffic and show you personalized content. By using our site, you agree to
                    our <a href="../privacy.html" class="text-brand font-bold hover:underline">Privacy Policy</a>.
                </p>
                <div class="flex gap-3">
                    <button onclick="acceptCookies()"
                        class="flex-1 px-4 py-2 bg-brand text-white text-xs font-bold rounded-lg hover:bg-orange-600 transition shadow-md">
                        Accept
                    </button>
                    <button onclick="closeCookies()"
                        class="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-xs font-bold rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition">
                        Decline
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // --- THEME & MENU ---
        function initTheme() {{
            if (localStorage.getItem('theme') === 'dark') {{
                document.documentElement.classList.add('dark');
                document.getElementById('theme-icon').innerHTML = '&#9728;&#65039;';
            }} else {{
                document.documentElement.classList.remove('dark');
                document.getElementById('theme-icon').innerHTML = '&#127769;';
            }}
        }}

        function toggleTheme() {{
            const html = document.documentElement;
            html.classList.toggle('dark');
            const isDark = html.classList.contains('dark');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
            document.getElementById('theme-icon').innerHTML = isDark ? '&#9728;&#65039;' : '&#127769;';
        }}

        function toggleMobileMenu() {{
            const m = document.getElementById('mobile-menu');
            m.style.display = (m.style.display === 'flex') ? 'none' : 'flex';
        }}

        // --- COOKIES ---
        function acceptCookies() {{ localStorage.setItem('cookieConsent', 'true'); hideBanner(); }}
        function closeCookies() {{ hideBanner(); }}
        function hideBanner() {{
            const banner = document.getElementById('cookie-banner');
            banner.classList.add('translate-y-20', 'opacity-0');
            setTimeout(() => banner.classList.add('hidden'), 500);
        }}

        // --- COPY LINK ---
        function copyArticleUrl() {{
            navigator.clipboard.writeText(window.location.href).then(() => {{
                const btn = document.querySelector('.share-btn.cp');
                const orig = btn.innerHTML;
                btn.innerHTML = '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>';
                btn.style.background = '#10B981';
                btn.style.color = '#fff';
                btn.style.borderColor = '#10B981';
                setTimeout(() => {{ btn.innerHTML = orig; btn.style.background = ''; btn.style.color = ''; btn.style.borderColor = ''; }}, 2000);
            }});
        }}

        // --- SCROLL TO TOP ---
        function scrollToTop() {{
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}

        // --- INIT ---
        window.onload = function () {{
            initTheme();
            // Scroll-to-top listener
            const scrollBtn = document.getElementById('scrollTopBtn');
            const prevNav = document.getElementById('prevArticleNav');
            const nextNav = document.getElementById('nextArticleNav');
            if (scrollBtn) {{
                window.addEventListener('scroll', () => {{
                    const show = window.scrollY > 400;
                    scrollBtn.classList.toggle('visible', show);
                    if (prevNav) prevNav.classList.toggle('visible', show);
                    if (nextNav) nextNav.classList.toggle('visible', show);
                }});
            }}
            // Cookie banner
            if (!localStorage.getItem('cookieConsent')) {{
                const banner = document.getElementById('cookie-banner');
                banner.classList.remove('hidden');
                setTimeout(() => banner.classList.remove('translate-y-20', 'opacity-0'), 100);
            }}
        }};
    </script>

    <!-- PREV / NEXT ARTICLE NAV -->
    {prev_nav_html}
    {next_nav_html}

    <!-- SCROLL TO TOP BUTTON -->
    <button id="scrollTopBtn" onclick="scrollToTop()" aria-label="Scroll to top">
        &#8593;
    </button>
    
    <!-- SOCIAL MEDIA & FOOTER -->
    <div class="dark:border-slate-700" style="border-top: 1px solid var(--bord, #E2E8F0); margin-top: 40px;">
        <div class="social-footer-bar">
            <a href="https://www.instagram.com/littlesmartgenius_com/" rel="noopener" target="_blank" title="Instagram">
                <svg fill="currentColor" viewBox="0 0 24 24">
                    <path
                        d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z">
                    </path>
                </svg>
            </a>
            <a href="https://www.pinterest.com/littlesmartgenius_com/" rel="noopener" target="_blank" title="Pinterest">
                <svg fill="currentColor" viewBox="0 0 24 24">
                    <path
                        d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.174.271-.401.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.607 0 11.985-5.365 11.985-11.987C23.97 5.39 18.592.026 11.985.026L12.017 0z">
                    </path>
                </svg>
            </a>
            <a href="https://medium.com/@littlesmartgenius-com" rel="noopener" target="_blank" title="Medium">
                <svg fill="currentColor" viewBox="0 0 24 24">
                    <path
                        d="M13.54 12a6.8 6.8 0 01-6.77 6.82A6.8 6.8 0 010 12a6.8 6.8 0 016.77-6.82A6.8 6.8 0 0113.54 12zM20.96 12c0 3.54-1.51 6.42-3.38 6.42-1.87 0-3.39-2.88-3.39-6.42s1.52-6.42 3.39-6.42 3.38 2.88 3.38 6.42M24 12c0 3.17-.53 5.75-1.19 5.75-.66 0-1.19-2.58-1.19-5.75s.53-5.75 1.19-5.75C23.47 6.25 24 8.83 24 12z">
                    </path>
                </svg>
            </a>
        </div>
        <div class="site-footer">
            <div style="margin-bottom: 6px;">
                <a href="../terms.html">Terms of Service</a>
                <span style="margin: 0 8px;">•</span>
                <a href="../privacy.html">Privacy Policy</a>
            </div>
            © 2026 Little Smart Genius. All rights reserved.
        </div>
    </div>

    {lead_magnet_html}

<script src="../exit-intent.js"></script>
</body>
</html>
"""


def sanitize_html(content: str) -> str:
    """Basic HTML sanitization."""
    # Remove script tags
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    return content


def convert_markdown_to_html(content: str) -> str:
    """Convert any remaining Markdown syntax in content to proper HTML.
    
    Some articles are generated with mixed HTML + Markdown. This converts:
    - ### Heading -> <h3>Heading</h3>
    - ## Heading -> <h2>Heading</h2>
    - **bold** -> <strong>bold</strong>
    - *italic* -> <em>italic</em>
    - * list item / - list item -> <ul><li>...</li></ul>
    - 1. numbered item -> <ol><li>...</li></ol>
    - Bare text lines -> wrapped in <p>
    """
    # Check if content has significant markdown
    md_headings = len(re.findall(r'^#{1,4}\s+\S', content, re.MULTILINE))
    md_bold = len(re.findall(r'\*\*[^*]+\*\*', content))
    if md_headings < 2 and md_bold < 5:
        return content  # Not enough markdown to bother
    
    lines = content.split('\n')
    result = []
    in_ul = False
    in_ol = False
    
    def close_lists():
        nonlocal in_ul, in_ol
        parts = []
        if in_ul:
            parts.append('</ul>')
            in_ul = False
        if in_ol:
            parts.append('</ol>')
            in_ol = False
        return parts
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            result.extend(close_lists())
            continue
        
        # Skip lines that are already HTML block elements
        if re.match(r'<(h[1-6]|div|figure|blockquote|ul|ol|li|table|section|article|header|footer|nav|aside|p)\b', stripped, re.IGNORECASE):
            result.extend(close_lists())
            result.append(line)
            continue
        
        # Also skip closing tags and self-contained HTML
        if re.match(r'</(h[1-6]|div|figure|blockquote|ul|ol|table|section|article)\b', stripped, re.IGNORECASE):
            result.append(line)
            continue
        
        # Headings: #### -> h4, ### -> h3, ## -> h2
        heading_match = re.match(r'^(#{2,4})\s+(.+)$', stripped)
        if heading_match:
            result.extend(close_lists())
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            # Convert inline markdown in heading text
            text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
            text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
            result.append(f'<h{level}>{text}</h{level}>')
            continue
        
        # Unordered list items: * item or - item (but not ** bold **)
        ul_match = re.match(r'^[\*\-]\s+(.+)$', stripped)
        if ul_match and not stripped.startswith('**'):
            if not in_ul:
                result.extend(close_lists())
                result.append('<ul>')
                in_ul = True
            item_text = ul_match.group(1)
            item_text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', item_text)
            item_text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', item_text)
            result.append(f'<li>{item_text}</li>')
            continue
        
        # Ordered list items: 1. item
        ol_match = re.match(r'^\d+\.\s+(.+)$', stripped)
        if ol_match:
            if not in_ol:
                result.extend(close_lists())
                result.append('<ol>')
                in_ol = True
            item_text = ol_match.group(1)
            item_text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', item_text)
            item_text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', item_text)
            result.append(f'<li>{item_text}</li>')
            continue
        
        # Regular text line — close any open lists, convert inline md, wrap in <p>
        result.extend(close_lists())
        
        # Convert inline **bold** and *italic*
        text = stripped
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
        
        # Only wrap in <p> if not already wrapped
        if not re.match(r'<(p|h[1-6]|div|figure|blockquote|ul|ol|li|table)\b', text, re.IGNORECASE):
            text = f'<p>{text}</p>'
        
        result.append(text)
    
    # Close any remaining open lists
    result.extend(close_lists())
    
    return '\n'.join(result)


def fix_image_paths(content: str) -> str:
    """Fix image paths to use ../ prefix for articles/ directory."""
    # Fix absolute server paths: src="..//home/runner/.../images/xxx.webp" → src="../images/xxx.webp"
    content = re.sub(r'src="\.\./(/.+?/images/([^"]+))"', r'src="../images/\2"', content)
    # Fix absolute paths without ../ prefix: src="/home/runner/.../images/xxx.webp"
    content = re.sub(r'src="(/[^"]*?/images/([^"]+))"', r'src="../images/\2"', content)
    # Fix src="images/..." to src="../images/..."
    content = re.sub(r'src="images/', 'src="../images/', content)
    # Fix src="/images/..." to src="../images/..."
    content = re.sub(r'src="/images/', 'src="../images/', content)
    
    # ── LCP Optimization: Add Base64 placeholder and dimensions to body images ──
    b64_placeholder = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy5wMy5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9IiNlMmU4ZjAiLz48L3N2Zz4="
    
    def enhance_img(match):
        img_tag = match.group(0)
        
        # Assume it's an auto-generated body image without dimensions
        if "data:image/svg+xml" in img_tag:
            return img_tag
            
        enhancements = []
        if 'loading=' not in img_tag:
            enhancements.append('loading="lazy"')
        if 'width=' not in img_tag:
            enhancements.append('width="800"')
        if 'height=' not in img_tag:
            enhancements.append('height="450"')
        if 'style=' not in img_tag:
            enhancements.append(f'style="background: url(\'{b64_placeholder}\') center/cover; background-color: var(--bord);"')
            
        if enhancements:
            # Inject right before the closing >
            close_idx = img_tag.rfind('/>')
            if close_idx != -1:
                return img_tag[:close_idx] + " " + " ".join(enhancements) + " " + img_tag[close_idx:]
            close_idx = img_tag.rfind('>')
            if close_idx != -1:
                return img_tag[:close_idx] + " " + " ".join(enhancements) + img_tag[close_idx:]
        
        return img_tag
        
    content = re.sub(r'<img\b[^>]*>', enhance_img, content, flags=re.IGNORECASE)
    
    return content


def fix_domain_urls(content: str) -> str:
    """Convert absolute domain URLs to relative paths.
    
    Converts:
      https://littlesmartgenius.com/freebies.html  → ../freebies.html
      https://littlesmartgenius.com/products.html   → ../products.html
      https://littlesmartgenius.com/articles/slug   → slug  (same directory)
      https://littlesmartgenius.com/blog.html       → ../blog.html
    
    Works both locally and in production. Google resolves relative URLs
    identically for SEO — zero penalty.
    """
    # Convert article links (same directory — articles/ → articles/)
    content = re.sub(
        r'https?://(?:www\.)?littlesmartgenius\.com/articles/([^"\'>\s]+)',
        r'\1',
        content,
        flags=re.IGNORECASE
    )
    
    # Convert all other domain links to ../path
    content = re.sub(
        r'https?://(?:www\.)?littlesmartgenius\.com/([^"\'>\s]*)',
        r'../\1',
        content,
        flags=re.IGNORECASE
    )
    
    # Edge case: root domain with no path → ../index.html
    content = re.sub(
        r'https?://(?:www\.)?littlesmartgenius\.com/?(["\'])',
        r'../index.html\1',
        content,
        flags=re.IGNORECASE
    )
    
    return content

# ═══════════════════════════════════════════════════════════════════════════════
# CONTENT POST-PROCESSORS
# ═══════════════════════════════════════════════════════════════════════════════

def fix_nested_blocks(content: str) -> str:
    """Fix malformed HTML where block elements are nested inside <p> tags.
    
    AI-generated content often produces:
      <p>Some text <ul><li>item</li></ul> more text</p>
    
    This converts it to:
      <p>Some text</p>
      <ul><li>item</li></ul>
      <p>more text</p>
    """
    # Pattern: find <p> that contain block elements
    block_tags = r'(<(?:ul|ol|blockquote|figure|div|table|h[1-6])\b[^>]*>.*?</(?:ul|ol|blockquote|figure|div|table|h[1-6])>)'
    
    def _fix_p(match):
        inner = match.group(1)
        # Check if this <p> contains block elements
        if not re.search(r'<(ul|ol|blockquote|figure|div|table|h[1-6])\b', inner, re.IGNORECASE):
            return match.group(0)
        
        # Split the inner content around block elements
        parts = re.split(block_tags, inner, flags=re.DOTALL | re.IGNORECASE)
        
        result_parts = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            # If it's a block element, add it directly
            if re.match(r'<(ul|ol|blockquote|figure|div|table|h[1-6])\b', part, re.IGNORECASE):
                result_parts.append(part)
            else:
                # It's inline text, wrap in <p> if substantial
                clean = re.sub(r'<[^>]+>', '', part).strip()
                if len(clean) > 3:
                    result_parts.append(f'<p>{part}</p>')
        
        return '\n'.join(result_parts)
    
    content = re.sub(r'<p>(.*?)</p>', _fix_p, content, flags=re.DOTALL)
    
    # Clean up empty paragraphs
    content = re.sub(r'<p>\s*</p>', '', content)
    
    return content

def split_long_paragraphs(content: str, max_words: int = 80) -> str:
    """Split <p> paragraphs that exceed max_words into multiple smaller paragraphs.
    
    Uses a plain-text first approach: strips tags, finds sentence boundaries
    on clean text, then maps split points back to the original HTML.
    """
    
    def _select_splits(boundaries, target, mode='primary'):
        """Select split positions from boundary list."""
        filtered = [(pos, wc) for pos, wc, btype in boundaries 
                     if mode == 'all' or btype == mode]
        if not filtered:
            return []
        points = []
        last_wc = 0
        for pos, wc in filtered:
            if wc - last_wc >= target:
                points.append(pos)
                last_wc = wc
        return points
    
    def _split_p(match):
        inner = match.group(1).strip()
        if not inner:
            return match.group(0)
        
        # Don't touch if it contains block-level elements
        if re.search(r'<(div|ul|ol|table|blockquote|h[1-6]|figure|img)', inner, re.IGNORECASE):
            return match.group(0)
        
        # Get plain text and count words
        plain = re.sub(r'<[^>]+>', '', inner)
        words = plain.split()
        if len(words) <= max_words:
            return match.group(0)
        
        # Build a character position map: for each char in 'plain',
        # what is the corresponding position in 'inner'?
        char_map = []
        inner_idx = 0
        for plain_idx in range(len(plain)):
            while inner_idx < len(inner) and inner[inner_idx] == '<':
                close = inner.find('>', inner_idx)
                if close == -1:
                    break
                inner_idx = close + 1
            char_map.append(inner_idx)
            inner_idx += 1
        
        # Find sentence boundaries in the plain text
        # Primary: . ! ? followed by whitespace
        # Secondary: em-dash (—), semicolon (;), colon (:) followed by whitespace
        boundaries = []
        word_count = 0
        for i in range(1, len(plain)):
            if plain[i] in ' \t\n\r':
                if i > 0 and plain[i-1] in '.!?':
                    word_count = len(plain[:i].split())
                    boundaries.append((i, word_count, 'primary'))
                elif i > 0 and plain[i-1] in '—;:':
                    word_count = len(plain[:i].split())
                    boundaries.append((i, word_count, 'secondary'))
            # Also detect em-dash without space (text—text)
            elif plain[i] == '—' and i > 1:
                word_count = len(plain[:i].split())
                boundaries.append((i, word_count, 'secondary'))
        
        if not boundaries:
            return match.group(0)
        
        # Select split points: first try primary boundaries only
        target = int(max_words * 0.65)
        split_points = _select_splits(boundaries, target, 'primary')
        
        # If no split points found or chunks still too long, use all boundaries
        if not split_points:
            split_points = _select_splits(boundaries, target, 'all')
        
        if not split_points:
            return match.group(0)
        
        # Map split points back to positions in 'inner'
        chunks = []
        last_inner_pos = 0
        for sp in split_points:
            if sp < len(char_map):
                inner_split = char_map[sp]
                # Walk forward in inner to include any closing tags at this position
                while inner_split < len(inner) and inner[inner_split] == '<':
                    close = inner.find('>', inner_split)
                    if close == -1:
                        break
                    # Check if it's a closing inline tag
                    tag_content = inner[inner_split:close+1]
                    if re.match(r'</(strong|em|b|i|a|span)>', tag_content, re.IGNORECASE):
                        inner_split = close + 1
                    else:
                        break
                # Skip whitespace
                while inner_split < len(inner) and inner[inner_split] in ' \t\n\r':
                    inner_split += 1
                chunk = inner[last_inner_pos:inner_split].strip()
                if chunk:
                    chunks.append(chunk)
                last_inner_pos = inner_split
        
        # Add the final chunk
        final = inner[last_inner_pos:].strip()
        if final:
            final_words = len(re.sub(r'<[^>]+>', '', final).split())
            if chunks and final_words < 15:
                chunks[-1] += ' ' + final
            else:
                chunks.append(final)
        
        if len(chunks) <= 1:
            return match.group(0)
        
        return '\n'.join(f'<p>{c}</p>' for c in chunks)
    
    content = re.sub(r'<p>(.*?)</p>', _split_p, content, flags=re.DOTALL)
    return content


def improve_text_spacing(content: str) -> str:
    """Add breathing room between paragraphs, headings, lists, and images.
    
    Strategy:
    - Wrap consecutive text in well-spaced containers
    - Add spacer divs between major content blocks
    - Ensure paragraphs have generous margins
    """
    # Add spacer after each heading (h2, h3)
    content = re.sub(
        r'(</h2>)\s*(<p)',
        r'\1\n<div style="height: 0.5rem;"></div>\n\2',
        content
    )
    content = re.sub(
        r'(</h3>)\s*(<p)',
        r'\1\n<div style="height: 0.25rem;"></div>\n\2',
        content
    )
    
    # Add spacer between list end and next paragraph
    content = re.sub(
        r'(</ul>)\s*(<p)',
        r'\1\n<div style="height: 1rem;"></div>\n\2',
        content
    )
    content = re.sub(
        r'(</ol>)\s*(<p)',
        r'\1\n<div style="height: 1rem;"></div>\n\2',
        content
    )
    
    # Add spacer after blockquote
    content = re.sub(
        r'(</blockquote>)\s*(<[ph])',
        r'\1\n<div style="height: 1.5rem;"></div>\n\2',
        content
    )
    
    # Add spacer after figure/img blocks before next paragraph
    content = re.sub(
        r'(</figure>)\s*(<p)',
        r'\1\n<div style="height: 1.5rem;"></div>\n\2',
        content
    )
    
    return content


def redistribute_images(content: str) -> str:
    """Redistribute images evenly throughout article content.
    
    Uses a simple, robust approach:
    1. Extract all images from content
    2. Split remaining content into lines
    3. Re-insert images at evenly spaced word-count positions
    """
    # Find all image/figure tags
    img_pattern = re.compile(r'(<figure[^>]*>.*?</figure>|<img[^>]*(?:/>|>(?:</img>)?))', re.DOTALL)
    
    images_found = img_pattern.findall(content)
    if len(images_found) < 2:
        return content
    
    # Remove all images from content
    text_only_content = img_pattern.sub('', content)
    
    # Split into lines (preserving HTML structure)
    lines = text_only_content.split('\n')
    lines = [l for l in lines if l.strip()]  # Remove empty lines
    
    if not lines:
        return content
    
    # Calculate total word count
    full_plain = re.sub(r'<[^>]+>', '', text_only_content)
    total_words = len(full_plain.split())
    
    if total_words < 200:
        return content
    
    # Calculate ideal gap between images
    n_images = len(images_found)
    ideal_gap = total_words // (n_images + 1)
    ideal_gap = max(ideal_gap, 80)
    
    # Track cumulative word count and insert images at thresholds
    result = []
    cumulative_words = 0
    img_idx = 0
    next_target = ideal_gap
    
    for line in lines:
        result.append(line)
        
        # Count words in this line (text only, no html tags)
        line_plain = re.sub(r'<[^>]+>', '', line).strip()
        word_count = len(line_plain.split()) if line_plain else 0
        cumulative_words += word_count
        
        # Insert image if we've reached the target word count
        if img_idx < n_images and cumulative_words >= next_target and word_count > 0:
            img_html = f'\n<div style="margin: 2.5rem 0;">{images_found[img_idx]}</div>\n'
            result.append(img_html)
            img_idx += 1
            next_target = cumulative_words + ideal_gap
    
    # Append any remaining images near the end
    while img_idx < n_images:
        result.append(f'\n<div style="margin: 2.5rem 0;">{images_found[img_idx]}</div>\n')
        img_idx += 1
    
    return '\n'.join(result)


def load_tpt_products() -> list:
    """Parse products_tpt.js and extract product data for internal linking."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "products_tpt.js")
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        match = re.search(r'window\.tptProducts\s*=\s*(\[.+?\]);', content, re.DOTALL)
        if match:
            products = json.loads(match.group(1))
            return [{"title": p[0], "url": p[1]} for p in products if len(p) >= 2]
    except Exception as e:
        print(f"Warning: Could not load TPT products: {e}")
    return []

def load_freebies() -> list:
    """Parse freebies.html to extract freebie names and data for internal linking and lead magnets."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "freebies.html")
    freebies = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Regex to extract the JS objects in freebies.html
        pattern = r'\{\s*name:\s*"(.*?)",\s*icon:\s*"(.*?)",\s*category:\s*"(.*?)"\s*\}'
        matches = re.findall(pattern, content)
        
        for m in matches:
            name = m[0]
            icon = m[1]
            cat = m[2]
            encoded_fname = urllib.parse.quote(name)
            url = f"../freebies.html?dl={encoded_fname}"
            
            freebies.append({
                "title": name,
                "image": icon,
                "category": cat,
                "url": url
            })
    except Exception as e:
        print(f"Warning: Could not load freebies: {e}")
    return freebies


def build_lead_magnet_html(category: str, freebies: list) -> str:
    """Generate a slide-in Contextual Lead Magnet pop-up."""
    if not freebies:
        return ""
    
    import hashlib
    
    cat_lower = category.lower() if category else ""
    
    # Map article categories to freebie categories
    # Freebie categories in freebies.html: "logic", "math", "word", "creative"
    CATEGORY_MAP = {
        'critical thinking': 'logic',
        'problem solving': 'logic',
        'math skills': 'math',
        'language arts': 'word',
        'word search activity worksheet': 'word',
        'creative arts': 'creative',
        'coloring book': 'creative',
        'visual skills': 'logic',
        'spot the difference (photorealistic)': 'logic',
        'education': None,  # general — pick random
    }
    
    # Find the mapped freebie category
    mapped_cat = None
    for art_cat, fb_cat in CATEGORY_MAP.items():
        if art_cat in cat_lower:
            mapped_cat = fb_cat
            break
    
    # Collect matching freebies
    candidates = []
    if mapped_cat:
        candidates = [fb for fb in freebies if fb.get('category', '').lower() == mapped_cat]
    
    # If no category match, use ALL freebies as candidates
    if not candidates:
        candidates = freebies
    
    # Pick a deterministic-but-varied freebie based on the category string
    # (using hash so the same category always gets the same freebie, but different categories get different ones)
    hash_val = int(hashlib.md5(cat_lower.encode()).hexdigest(), 16)
    target = candidates[hash_val % len(candidates)]
        
    title = target.get('title', 'Free Educational Resource')
    url = target.get('url', '../freebies.html')
    image = target.get('image', '')
    
    if image and not image.startswith('http') and not image.startswith('../'):
        # Check if it's an actual image path (contains . or /) or just an emoji
        if '/' in image or '.' in image:
            image = f"../{image}"
        else:
            # It's an emoji, not a file path — use it as text
            pass
        
    # Determine if image is a file path or an emoji
    is_image_file = image and ('/' in image or '.' in image)
    if is_image_file:
        img_html = f'<img src="{image}" alt="{title}" class="w-16 h-16 object-cover rounded shadow-sm border border-slate-200">'
    elif image:
        # It's an emoji icon — render as styled text
        img_html = f'<div class="w-16 h-16 rounded shadow-sm border border-slate-200 flex items-center justify-center text-3xl" style="background: rgba(244,140,6,0.08);">{image}</div>'
    else:
        img_html = '<div class="w-16 h-16 rounded shadow-sm border border-slate-200 flex items-center justify-center text-3xl" style="background: rgba(244,140,6,0.08);">🎁</div>'
    
    # Escape title for JS string
    title_js = title.replace("'", "\\'").replace('"', '\\"')
    
    return f"""
    <!-- ═══ CONTEXTUAL LEAD MAGNET ═══ -->
    <div id="lead-magnet-popup" class="fixed bottom-4 left-4 md:bottom-6 md:left-6 max-w-[320px] w-full bg-white dark:bg-slate-800 p-4 rounded-2xl shadow-[0_10px_40px_rgba(0,0,0,0.2)] border border-[#F48C06]/30 z-[50] transition-all duration-700 translate-y-[150%] opacity-0 flex gap-4 items-center group cursor-pointer hover:border-[#F48C06]" onclick="openLeadMagnetModal()">
        
        <button onclick="event.stopPropagation(); document.getElementById('lead-magnet-popup').remove();" class="absolute -top-2 -right-2 w-7 h-7 bg-slate-100 dark:bg-slate-700 hover:bg-red-500 hover:text-white rounded-full flex items-center justify-center text-sm font-bold transition shadow-md z-10 text-slate-500 dark:text-slate-300" aria-label="Close">
            &times;
        </button>
        
        <div class="flex-shrink-0">
            {img_html}
        </div>
        
        <div class="flex-1">
            <h4 class="text-[10px] uppercase tracking-widest font-extrabold text-[#F48C06] mb-1">🎁 Free Download</h4>
            <p class="text-sm font-bold text-slate-800 dark:text-white leading-tight mb-2 group-hover:text-[#F48C06] transition">{title}</p>
            <span class="inline-flex items-center text-[#F48C06] text-xs font-bold font-mono uppercase tracking-wider group-hover:underline">Get it now &rarr;</span>
        </div>
    </div>
    
    <!-- ═══ INLINE DOWNLOAD MODAL (stays on page) ═══ -->
    <div id="lm-download-modal" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.5); backdrop-filter:blur(4px); z-index:9998; align-items:center; justify-content:center;">
        <div class="bg-white dark:bg-slate-800 p-8 rounded-3xl max-w-md w-full mx-4 shadow-2xl relative border border-slate-200 dark:border-slate-700">
            <button class="absolute top-4 right-4 text-slate-400 hover:text-red-500 text-2xl font-bold" onclick="closeLeadMagnetModal()">&times;</button>
            
            <!-- NEW USER VIEW -->
            <div class="text-center" id="lm-new-user">
                <div class="text-4xl mb-4">📧</div>
                <h3 class="text-xl font-bold mb-2" style="color:var(--text)">Where should we send it?</h3>
                <p class="text-sm font-bold text-[#F48C06] mb-2 bg-orange-50 dark:bg-slate-700 py-1 px-3 rounded-lg inline-block">{title}</p>
                <p class="text-xs text-slate-500 italic mb-4 max-w-xs mx-auto">Unlock this exclusive content by confirming your email.</p>
                <input autocomplete="off" style="position:absolute;left:-9999px;" id="lm-honeypot" tabindex="-1" type="text" />
                <input class="w-full p-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-600 outline-none focus:border-[#F48C06] mb-4 transition" id="lm-email" placeholder="your@email.com" type="email" />
                <div class="flex items-start gap-3 mb-6 text-left px-1">
                    <input class="mt-1" id="lm-consent" type="checkbox" style="accent-color:#F48C06;" />
                    <label class="text-[10px] text-slate-500 leading-snug cursor-pointer" for="lm-consent">
                        By checking this box, I confirm I am the authorized owner of this email address. I agree to the
                        <a class="text-[#F48C06] underline" href="../terms.html" target="_blank">Terms &amp; Conditions</a>,
                        and I accept to join the email database to receive this freebie and occasional educational updates.
                    </label>
                </div>
                <button class="w-full py-3 bg-[#F48C06] text-white font-bold rounded-xl hover:shadow-lg hover:brightness-110 transition" onclick="lmSubmitEmail()">Send it to me!</button>
            </div>
            
            <!-- RETURNING USER VIEW -->
            <div class="text-center hidden" id="lm-returning-user">
                <div class="text-4xl mb-4">👋</div>
                <h3 class="text-xl font-bold mb-1" style="color:var(--text)">Welcome Back!</h3>
                <p class="text-xs text-slate-400 mb-2">Your freebie:</p>
                <p class="text-sm font-bold text-[#F48C06] mb-1 bg-orange-50 dark:bg-slate-700 py-1 px-3 rounded-lg inline-block">{title}</p>
                <p class="text-xs text-slate-500 italic mb-6 max-w-xs mx-auto">Unlock this exclusive content by confirming your email.</p>
                <button class="w-full py-3 bg-[#F48C06] text-white font-bold rounded-xl hover:shadow-lg hover:brightness-110 transition mb-3 flex items-center justify-center gap-2" onclick="lmDirectDownload()">
                    <span>📥</span> Download Directly
                </button>
                <p class="text-xs text-slate-400 mb-3">&mdash; or &mdash;</p>
                <button class="text-xs text-slate-500 hover:text-[#F48C06] underline decoration-dotted transition" onclick="lmSendEmail()">
                    📧 Send to my email (<span id="lm-saved-email">user@example.com</span>)
                </button>
                <div class="mt-3">
                    <button class="text-[10px] text-slate-400 hover:text-red-500 underline decoration-dotted" onclick="lmResetEmail()">Change Email</button>
                </div>
            </div>
            
            <!-- SUCCESS VIEW -->
            <div class="text-center hidden" id="lm-success">
                <div class="text-4xl mb-4">🚀</div>
                <h3 class="text-xl font-bold mb-2" style="color:var(--text)">Sent!</h3>
                <p class="text-sm text-slate-500 mb-6">Check your inbox. Your freebie is on the way.</p>
                <div>
                    <button class="text-xs font-bold text-slate-400 hover:text-[#F48C06] underline decoration-dotted transition" id="lm-resend-btn" onclick="lmHandleResend()">
                        Didn't receive it? Click to resend.
                    </button>
                </div>
                <div class="hidden mt-6 pt-6 border-t border-slate-100 dark:border-slate-700" id="lm-direct-dl-container">
                    <p class="text-xs text-orange-500 mb-2 font-bold">⚠️ Due to high demand, email delivery is slower than usual. Please use this direct link:</p>
                    <a class="w-full block py-2 border-2 border-[#F48C06] text-[#F48C06] font-bold rounded-xl hover:bg-[#F48C06] hover:text-white transition text-sm" href="#" id="lm-direct-dl-link" target="_blank">
                        Direct Download
                    </a>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        (function() {{
            var LM_PRODUCT = "{title_js}";
            var LM_WORKER = "https://freebie-email.littlesmartgenius.com";
            var lmResendCount = 0;
            var lmLastLink = "#";
            var EXPIRY_DAYS = 30;
            
            function getStored() {{
                var d = localStorage.getItem('lsg_user_data');
                if (!d) return null;
                try {{
                    var o = JSON.parse(d);
                    if (new Date().getTime() > o.expiry) {{ localStorage.removeItem('lsg_user_data'); return null; }}
                    return o.email;
                }} catch(e) {{ return null; }}
            }}
            function setStored(email) {{
                var exp = new Date().getTime() + (EXPIRY_DAYS*24*60*60*1000);
                localStorage.setItem('lsg_user_data', JSON.stringify({{email:email, expiry:exp}}));
            }}
            
            window.openLeadMagnetModal = function() {{
                var m = document.getElementById('lm-download-modal');
                lmResendCount = 0;
                document.getElementById('lm-direct-dl-container').classList.add('hidden');
                var rb = document.getElementById('lm-resend-btn');
                rb.innerText = "Didn't receive it? Click to resend.";
                rb.style.display = "inline-block";
                document.getElementById('lm-success').classList.add('hidden');
                
                var saved = getStored();
                if (saved) {{
                    document.getElementById('lm-saved-email').textContent = saved;
                    document.getElementById('lm-new-user').classList.add('hidden');
                    document.getElementById('lm-returning-user').classList.remove('hidden');
                }} else {{
                    document.getElementById('lm-new-user').classList.remove('hidden');
                    document.getElementById('lm-returning-user').classList.add('hidden');
                }}
                m.style.display = 'flex';
                if (typeof gtag === 'function') {{
                    gtag('event', 'lead_magnet_click', {{'event_category':'freebies','event_label':LM_PRODUCT}});
                }}
            }};
            
            window.closeLeadMagnetModal = function() {{
                document.getElementById('lm-download-modal').style.display = 'none';
            }};
            document.getElementById('lm-download-modal').addEventListener('click', function(e) {{
                if (e.target === this) closeLeadMagnetModal();
            }});
            
            function showSuccess() {{
                document.getElementById('lm-new-user').classList.add('hidden');
                document.getElementById('lm-returning-user').classList.add('hidden');
                document.getElementById('lm-success').classList.remove('hidden');
            }}
            
            async function callAPI(email) {{
                showSuccess();
                var rb = document.getElementById('lm-resend-btn');
                rb.innerText = "Sending...";
                try {{
                    var resp = await fetch(LM_WORKER, {{
                        method:"POST", headers:{{"Content-Type":"application/json"}},
                        body: JSON.stringify({{email:email, productName:LM_PRODUCT}})
                    }});
                    var data = await resp.json();
                    if (data.success) {{
                        rb.innerText = "📧 Email sent! Check your inbox.";
                        if (data.downloadLink) lmLastLink = data.downloadLink;
                    }} else {{
                        rb.innerText = "Oops! Something went wrong.";
                        if (data.downloadLink) lmLastLink = data.downloadLink;
                    }}
                }} catch(err) {{
                    lmResendCount++;
                    if (lmResendCount >= 2) showDirectDL();
                    else rb.innerText = "Network error. Try resending.";
                }}
            }}
            
            function showDirectDL() {{
                document.getElementById('lm-resend-btn').style.display = 'none';
                document.getElementById('lm-direct-dl-container').classList.remove('hidden');
                document.getElementById('lm-direct-dl-link').href = lmLastLink;
            }}
            
            window.lmSubmitEmail = function() {{
                var hp = document.getElementById('lm-honeypot').value;
                if (hp) return;
                var c = document.getElementById('lm-consent').checked;
                if (!c) {{ alert("Please check the box to confirm you agree to our Terms & Conditions."); return; }}
                var email = document.getElementById('lm-email').value.trim();
                if (/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email)) {{
                    setStored(email);
                    callAPI(email);
                    if (typeof gtag === 'function') {{
                        gtag('event', 'lead_magnet_email_submit', {{'event_category':'freebies','event_label':LM_PRODUCT}});
                    }}
                }} else {{
                    document.getElementById('lm-email').style.borderColor = '#EF4444';
                }}
            }};
            
            window.lmDirectDownload = async function() {{
                var email = getStored();
                if (!email) {{ lmResetEmail(); return; }}
                try {{
                    var resp = await fetch(LM_WORKER, {{
                        method:"POST", headers:{{"Content-Type":"application/json"}},
                        body: JSON.stringify({{email:email, productName:LM_PRODUCT, directOnly:true}})
                    }});
                    var data = await resp.json();
                    if (data.downloadLink) {{
                        var a = document.createElement('a');
                        a.href = data.downloadLink; a.style.display='none';
                        document.body.appendChild(a); a.click(); document.body.removeChild(a);
                        closeLeadMagnetModal();
                    }} else {{
                        lmSendEmail();
                    }}
                }} catch(err) {{
                    lmSendEmail();
                }}
            }};
            
            window.lmSendEmail = function() {{
                var email = getStored();
                if (email) callAPI(email);
            }};
            
            window.lmHandleResend = function() {{
                lmResendCount++;
                if (lmResendCount >= 2) showDirectDL();
                else lmSendEmail();
            }};
            
            window.lmResetEmail = function() {{
                localStorage.removeItem('lsg_user_data');
                document.getElementById('lm-returning-user').classList.add('hidden');
                document.getElementById('lm-success').classList.add('hidden');
                document.getElementById('lm-new-user').classList.remove('hidden');
            }};
            
            // ── Scroll trigger: show lead magnet at 50% scroll ──
            var popup = document.getElementById("lead-magnet-popup");
            if (popup) {{
                var triggered = false;
                window.addEventListener("scroll", function() {{
                    if (triggered) return;
                    var scrollPos = window.scrollY;
                    var docHeight = document.documentElement.scrollHeight - window.innerHeight;
                    if (docHeight > 0 && (scrollPos / docHeight) > 0.5) {{
                        popup.classList.remove('translate-y-[150%]', 'opacity-0');
                        triggered = true;
                    }}
                }});
            }}
        }})();
    </script>
"""

def build_link_targets(all_articles, current_slug='', tpt_products=None, freebies=None):
    """Build a dictionary of linkable phrases and their target URLs.
    
    Returns list of (phrase, url, priority) sorted by phrase length (longest first)
    to avoid partial matches.
    """
    targets = []
    
    # 1. Link to other articles by title
    for art in all_articles:
        if art.get('slug') == current_slug:
            continue
        title = art.get('title', '')
        url = f"../{art.get('url', '')}"
        if title:
            targets.append((title, url, 10))
            # Also add shorter variations (remove "How to Use" prefix etc.)
            short = re.sub(r'^(How to Use |Best |Ultimate |Essential |How )', '', title)
            if short != title and len(short) > 20:
                targets.append((short, url, 5))
    
    # 1b. Link article keywords to their articles (cross-linking)
    for art in all_articles:
        if art.get('slug') == current_slug:
            continue
        url = f"../{art.get('url', '')}"
        keywords = art.get('keywords', [])
        for kw in keywords:
            # Link keywords of 2 or more words directly to this specific article
            if len(kw.split()) >= 2 and len(kw) > 8:
                targets.append((kw, url, 4))
    
    # 2. Link to category-filtered blog pages
    category_map = {}
    for art in all_articles:
        cat = art.get('category', '')
        if cat and cat not in category_map:
            cat_slug = re.sub(r'[^a-z0-9]+', '-', cat.lower()).strip('-')
            if cat_slug:
                category_map[cat] = f"../blog-{cat_slug}.html"
    
    for cat, url in category_map.items():
        targets.append((cat, url, 8))
        # Also add common variations
        cat_lower = cat.lower()
        if 'spot the difference' in cat_lower:
            targets.append(('spot the difference activities', url, 7))
            targets.append(('spot the difference puzzles', url, 7))
            targets.append(('spot the difference worksheets', url, 7))
            targets.append(('photorealistic spot the difference', url, 7))
            targets.append(('photorealistic spot the difference activities for kids', url, 7))
            targets.append(('spot the difference', url, 6))
        elif 'coloring' in cat_lower:
            targets.append(('coloring activities', url, 7))
            targets.append(('coloring worksheets', url, 7))
            targets.append(('coloring pages', url, 7))
            targets.append(('coloring books', url, 6))
        elif 'math' in cat_lower:
            targets.append(('math worksheets', url, 7))
            targets.append(('math activities', url, 7))
            targets.append(('math exercises', url, 7))
            targets.append(('math skills', url, 6))
        elif 'word search' in cat_lower:
            targets.append(('word search activities', url, 7))
            targets.append(('word search worksheets', url, 7))
            targets.append(('word search puzzles', url, 7))
        elif 'critical thinking' in cat_lower:
            targets.append(('critical thinking activities', url, 7))
            targets.append(('critical thinking worksheets', url, 7))
            targets.append(('critical thinking skills', url, 6))
        elif 'problem solving' in cat_lower:
            targets.append(('problem-solving activities', url, 7))
            targets.append(('problem solving worksheets', url, 7))
            targets.append(('maze activities', url, 7))
            targets.append(('maze worksheets', url, 7))
            targets.append(('problem-solving skills', url, 6))
        elif 'visual' in cat_lower:
            targets.append(('shadow matching worksheets', url, 7))
            targets.append(('shadow matching activities', url, 7))
            targets.append(('visual perception worksheets', url, 7))
            targets.append(('visual skills activities', url, 6))
        elif 'creative' in cat_lower:
            targets.append(('fine motor skills worksheets', url, 7))
            targets.append(('fine motor activities', url, 7))
            targets.append(('clip art activities', url, 7))
            targets.append(('fine motor skills', url, 6))
    
    # 3. Link to key site pages
    targets.append(('free printables', '../freebies.html', 6))
    targets.append(('free worksheets', '../freebies.html', 6))
    targets.append(('free resources', '../freebies.html', 6))
    targets.append(('free educational resources', '../freebies.html', 6))
    targets.append(('printable worksheets', '../freebies.html', 6))
    targets.append(('printable activities', '../freebies.html', 6))
    targets.append(('free printable worksheets', '../freebies.html', 6))
    targets.append(('downloadable worksheets', '../freebies.html', 6))
    targets.append(('premium resources', '../products.html', 6))
    targets.append(('premium worksheets', '../products.html', 6))
    targets.append(('our store', '../products.html', 6))
    targets.append(('educational resources', '../products.html', 5))
    targets.append(('activity book', '../products.html', 5))
    targets.append(('counting exercises', '../products.html', 5))
    targets.append(('educational printables', '../products.html', 5))
    targets.append(('learning resources', '../products.html', 5))
    targets.append(('classroom resources', '../products.html', 5))
    targets.append(('teachers pay teachers', 'https://www.teacherspayteachers.com/store/little-smart-genius', 4))
    targets.append(('TpT store', 'https://www.teacherspayteachers.com/store/little-smart-genius', 4))
    
    # 4. Cross-topic educational phrases -> blog
    targets.append(('cognitive development', '../blog.html', 4))
    targets.append(('brain development activities', '../blog.html', 4))
    targets.append(('executive function skills', '../blog.html', 4))
    targets.append(('observation skills', '../blog.html', 4))
    targets.append(('early childhood education', '../blog.html', 4))
    targets.append(('preschool learning activities', '../blog.html', 4))
    targets.append(('kindergarten activities', '../blog.html', 4))
    
    # 5. Link to Specific TPT Products
    if tpt_products:
        for product in tpt_products:
            title = product.get('title', '')
            if title:
                encoded_title = urllib.parse.quote(title)
                url = f"../products.html?product={encoded_title}"
                # Full title match (High priority)
                targets.append((title, url, 9))
                # Short title match (e.g. up to the first pipe)
                parts = title.split('|')
                if len(parts) > 1:
                    short_title = parts[0].strip()
                    if short_title and len(short_title) > 10:
                        targets.append((short_title, url, 6))
                        
    # 6. Link to Specific Freebies
    if freebies:
        for fb in freebies:
            fname = fb.get('title') if isinstance(fb, dict) else fb
            if not fname: continue
            
            encoded_fname = urllib.parse.quote(fname)
            url = f"../freebies.html?dl={encoded_fname}"
            targets.append((fname, url, 9))
    
    # Sort by phrase length (longest first) to prevent partial matches
    targets.sort(key=lambda x: (-len(x[0]), -x[2]))
    
    return targets


def inject_internal_links(content: str, link_targets: list, max_links=12) -> str:
    """Inject internal hyperlinks into article content.
    
    Rules:
    - Only link the FIRST occurrence of each phrase
    - Don't link text that's already inside an <a> tag
    - Don't link text that's inside an <h1>/<h2>/<h3> tag
    - Maximum 12 internal links per article
    - Case-insensitive matching
    """
    links_added = 0
    url_counts = {}  # Allow up to 2 links per URL
    linked_phrases = set()  # Track what we've already linked
    
    for phrase, url, priority in link_targets:
        if links_added >= max_links:
            break
        
        # Allow max 2 links per unique URL
        if url_counts.get(url, 0) >= 2:
            continue
        
        # Build a regex that matches the phrase case-insensitively
        # but NOT inside existing <a>...</a> tags or headings
        escaped = re.escape(phrase)
        
        # Match the phrase with word boundaries
        pattern = re.compile(
            r'(?<!["\'>])(?<!/)\b(' + escaped + r')\b(?!["\'])',
            re.IGNORECASE
        )
        
        # Find all matches
        matches = list(pattern.finditer(content))
        
        for match in matches:
            # Check if this match is inside an <a> tag or heading
            start = match.start()
            
            # Look backward for unclosed <a> tag
            before = content[:start]
            a_opens = len(re.findall(r'<a\b', before, re.IGNORECASE))
            a_closes = len(re.findall(r'</a>', before, re.IGNORECASE))
            if a_opens > a_closes:
                continue  # Inside an <a> tag
            
            # Check if inside heading
            h_opens = len(re.findall(r'<h[1-3]\b', before, re.IGNORECASE))
            h_closes = len(re.findall(r'</h[1-3]>', before, re.IGNORECASE))
            if h_opens > h_closes:
                continue  # Inside a heading
            
            # Check if inside <strong> already linked (we want to keep bold + add link)
            # Build the replacement
            matched_text = match.group()
            replacement = f'<a href="{url}" class="internal-link" style="color: #F48C06; text-decoration: underline; font-weight: 600;">{matched_text}</a>'
            
            content = content[:start] + replacement + content[start + len(matched_text):]
            links_added += 1
            url_counts[url] = url_counts.get(url, 0) + 1
            linked_phrases.add(phrase.lower())
            break  # Only first occurrence
    
    return content


def build_faq_html(faq_schema):
    """Build FAQ accordion HTML from FAQ schema."""
    if not faq_schema:
        return ""
    
    faq_items = ""
    for item in faq_schema:
        q = item.get('q', '')
        a = item.get('a', '')
        faq_items += f"""
        <details class="border rounded-xl p-4 mb-3" style="border-color: var(--bord);">
            <summary class="font-bold cursor-pointer" style="color: var(--text);">{q}</summary>
            <p class="mt-3 text-slate-600 dark:text-slate-400">{a}</p>
        </details>"""
    
    return f"""
    <div class="mt-12 pt-8 border-t" style="border-color: var(--bord);">
        <h2 class="text-2xl font-extrabold mb-6" style="color: var(--text);">Frequently Asked Questions</h2>
        {faq_items}
    </div>"""

def add_table_of_contents(content: str) -> str:
    """Finds all H2 tags, assigns IDs, and injects a Table of Contents right before the first H2."""
    h2_pattern = re.compile(r'<h2(.*?)>(.*?)</h2>', re.IGNORECASE | re.DOTALL)
    
    toc_items = []
    seen_ids = set()
    
    def h2_repl_func(match):
        attrs = match.group(1)
        inner_html = match.group(2)
        inner_text = re.sub(r'<[^>]+>', '', inner_html).strip()
        
        # Check if already has id
        id_match = re.search(r'id=["\']([^"\']+)["\']', attrs, re.IGNORECASE)
        if id_match:
            h2_id = id_match.group(1)
        else:
            # Generate ID
            h2_id = re.sub(r'[^a-z0-9]+', '-', inner_text.lower()).strip('-')
            if not h2_id:
                h2_id = "section"
            
            # Ensure uniqueness
            base_id = h2_id
            counter = 1
            while h2_id in seen_ids:
                h2_id = f"{base_id}-{counter}"
                counter += 1
                
            attrs = f' id="{h2_id}"{attrs}'
            
        seen_ids.add(h2_id)
        toc_items.append((h2_id, inner_text))
        
        return f'<h2{attrs}>{inner_html}</h2>'

    # First pass: replace H2s and collect TOC items
    content_with_ids = h2_pattern.sub(h2_repl_func, content)
    
    # If there are fewer than 2 H2 headers, a TOC isn't very useful
    if len(toc_items) < 2:
        return content_with_ids
        
    # Build TOC HTML
    lis = []
    for h2_id, text in toc_items:
        lis.append(f'<li class="py-1"><a href="#{h2_id}" class="text-brand hover:text-orange-600 transition font-bold text-sm" style="text-decoration: none;">{text}</a></li>')
        
    toc_html = f"""
    <div class="toc-container rounded-xl p-6 my-8 border shadow-sm" style="background: var(--card); border-color: var(--bord);">
        <h3 class="font-extrabold text-lg mb-4 flex items-center gap-2" style="color: var(--text);">
            <span>📑</span> Table of Contents
        </h3>
        <ul class="space-y-1 list-none p-0 m-0">
            {''.join(lis)}
        </ul>
    </div>
    """
    
    # Inject TOC before the first <h2>
    first_h2_idx = content_with_ids.lower().find("<h2")
    if first_h2_idx != -1:
        content_with_ids = content_with_ids[:first_h2_idx] + toc_html + content_with_ids[first_h2_idx:]
        
    return content_with_ids


def build_faq_schema_json(faq_schema, title, canonical_url):
    """Build JSON-LD FAQ schema."""
    if not faq_schema:
        return ""
    
    entities = []
    for item in faq_schema:
        entities.append({
            "@type": "Question",
            "name": item.get('q', ''),
            "acceptedAnswer": {
                "@type": "Answer",
                "text": item.get('a', '')
            }
        })
    
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": entities
    }
    
    return f'\n<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>'


def build_related_articles_html(current_slug, current_category, current_keywords, all_articles, max_related=3):
    """Build related articles HTML section based on category and keyword matching."""
    if not all_articles:
        return ""
    
    current_kw_set = set(k.lower() for k in current_keywords) if current_keywords else set()
    
    scored = []
    for art in all_articles:
        if art.get('slug') == current_slug:
            continue
        score = 0
        # Category match = 3 points
        if art.get('category', '').lower() == (current_category or '').lower() and current_category:
            score += 3
        # Keyword overlap
        art_kw = set(k.lower() for k in art.get('keywords', []))
        overlap = current_kw_set & art_kw
        score += len(overlap)
        if score > 0:
            scored.append((score, art))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    related = [s[1] for s in scored[:max_related]]
    
    # If not enough related, fill with recent articles
    if len(related) < max_related:
        for art in all_articles:
            if art.get('slug') == current_slug or art in related:
                continue
            related.append(art)
            if len(related) >= max_related:
                break
    
    if not related:
        return ""
    
    cards = []
    for art in related:
        title = art.get('title', 'Untitled')
        url = art.get('url', '#')
        image = art.get('image', '')
        # Thumbnail path for srcset (mobile)
        thumb_image = image.replace('images/', 'images/thumbs/', 1) if image.startswith('images/') else image
        category = art.get('category', '')
        reading_time = art.get('reading_time', 5)
        date = art.get('date', '')
        excerpt = art.get('excerpt', '')[:120]
        if len(art.get('excerpt', '')) > 120:
            excerpt += '...'
        
        cards.append(f'''<article class="rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 border" style="background: var(--card); border-color: var(--bord);">
                <a href="../{url}" class="block">
                    <div class="aspect-video overflow-hidden">
                        <img
                            src="../{image}"
                            srcset="../{thumb_image} 480w, ../{image} 1200w"
                            sizes="(max-width: 768px) 480px, 800px"
                            alt="{title}"
                            class="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
                            loading="lazy"
                        >
                    </div>
                    <div class="p-5">
                        <div class="flex items-center gap-2 mb-2">
                            <span class="text-xs font-bold uppercase tracking-wider" style="color: #F48C06;">{category}</span>
                            <span class="text-xs text-slate-500">&#128214; {reading_time} min</span>
                        </div>
                        <h3 class="text-lg font-extrabold mb-2 hover:text-brand transition" style="color: var(--text);">{title}</h3>
                        <p class="text-sm text-slate-600 dark:text-slate-400 line-clamp-2">{excerpt}</p>
                    </div>
                </a>
            </article>''')
    
    return f'''
            <!-- RELATED ARTICLES -->
            <div class="mt-16 pt-10 border-t" style="border-color: var(--bord);">
                <h2 class="text-2xl font-extrabold mb-8" style="color: var(--text);">&#128240; You May Also Like</h2>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {''.join(cards)}
                </div>
            </div>'''


def build_breadcrumb_schema(title: str, category: str, canonical_url: str) -> str:
    """Generate JSON-LD schema for BreadcrumbList."""
    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": f"{SITE_URL}/index.html"
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "Blog",
                "item": f"{SITE_URL}/blog.html"
            }
        ]
    }
    
    pos = 3
    if category:
        cat_slug = re.sub(r'[^a-z0-9]+', '-', category.lower()).strip('-')
        cat_url = f"{SITE_URL}/blog-{cat_slug}.html" if cat_slug else f"{SITE_URL}/blog.html"
        schema["itemListElement"].append({
            "@type": "ListItem",
            "position": pos,
            "name": category,
            "item": cat_url
        })
        pos += 1
        
    schema["itemListElement"].append({
        "@type": "ListItem",
        "position": pos,
        "name": title,
        "item": canonical_url
    })
    
    return f'\n<script type="application/ld+json">\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n</script>\n'


def generate_article_html(json_data: dict, slug: str, all_articles=None, prev_article=None, next_article=None, tpt_products=None, freebies=None) -> str:
    """Generate full HTML page for an article."""
    title = json_data.get('title', 'Untitled Article')
    content = json_data.get('content', '<p>No content available.</p>')
    
    # === RETROACTIVE V6 CLEANUP ===
    # 1. Strip full HTML document wrappers accidentally generated by AI
    content = re.sub(r'<!DOCTYPE[^>]*>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</?html[^>]*>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'<head[^>]*>.*?</head>', '', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'</?body[^>]*>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.IGNORECASE | re.DOTALL)
    
    # 2. Strip duplicate plain-text FAQ blocks generated by older V6 scripts
    content = re.sub(r'<div class="faq-section[^>]*>\s*<h2[^>]*>Frequently\s+Asked\s+Questions</h2>.*', '', content, flags=re.IGNORECASE | re.DOTALL)
    
    # Sanitize and fix paths
    content = sanitize_html(content)
    content = fix_image_paths(content)
    content = fix_domain_urls(content)
    
    # Strip embedded "You Might Also Like" / "You May Also Like" sections
    # (the template already adds a proper image-card version)
    content = re.sub(
        r'<div[^>]*>\s*<h3[^>]*>You M(?:ight|ay) Also Like</h3>.*?</div>\s*(?:</div>)?',
        '',
        content,
        flags=re.DOTALL | re.IGNORECASE
    )
    content = re.sub(
        r'<h3[^>]*>You M(?:ight|ay) Also Like</h3>\s*(?:<(?:a|p|div|hr|br)[^>]*>.*?</(?:a|p|div)>\s*(?:<hr[^>]*/?>\s*)*)*',
        '',
        content,
        flags=re.DOTALL | re.IGNORECASE
    )
    
    # ── SAFETY: Strip ALL Google Drive links ──
    # Drive links must NEVER appear in articles; downloads go through freebies.html only.
    # Remove entire download-cta div blocks
    content = re.sub(
        r'<div\s+class="download-cta"[^>]*>.*?</div>',
        '',
        content,
        flags=re.DOTALL
    )
    # Remove <a> tags linking to Drive, keep inner text
    content = re.sub(
        r'<a\s+href="https?://drive\.google\.com/[^"]*"[^>]*>(.*?)</a>',
        r'\1',
        content,
        flags=re.DOTALL
    )
    # Remove markdown drive links
    content = re.sub(
        r'\[([^\]]*)\]\(https?://drive\.google\.com/[^)]*\)',
        '',
        content
    )
    # Remove any remaining bare Drive URLs
    content = re.sub(
        r'https?://drive\.google\.com/[^\s<>"\')\]]*',
        '../freebies.html',
        content
    )
    
    # ── Content post-processing ──
    # 0. Convert any raw Markdown to proper HTML (some articles have mixed md+html content)
    content = convert_markdown_to_html(content)
    
    # 1. Redistribute images evenly (before link injection)
    content = redistribute_images(content)
    
    # 1.5. Fix malformed HTML: extract block elements from inside <p> tags
    content = fix_nested_blocks(content)
    
    # 2. Split long paragraphs for comfortable reading
    content = split_long_paragraphs(content, max_words=80)
    
    # 3. Improve text spacing
    content = improve_text_spacing(content)
    
    # 4. Inject smart internal links (SEO backlinks)
    if all_articles:
        link_targets = build_link_targets(all_articles, current_slug=slug, tpt_products=tpt_products, freebies=freebies)
        content = inject_internal_links(content, link_targets, max_links=20)
        
    # 5. Add Table of Contents
    content = add_table_of_contents(content)
    
    # Add Tags section
    keywords = json_data.get('keywords', [])
    if keywords:
        tags_list = []
        for kw in keywords:
            encoded_kw = urllib.parse.quote(kw.strip())
            tags_list.append(f'<a href="../blog.html" class="inline-block px-3 py-1 bg-slate-100 dark:bg-slate-800 text-xs font-bold text-slate-500 hover:text-brand hover:bg-orange-50 transition rounded-full mb-2 mr-2" style="border: 1px solid var(--bord); text-decoration: none;">#{kw.strip()}</a>')
        
        tags_html = f"""
    <div class="mt-8 pt-6 border-t" style="border-color: var(--bord);">
        <h3 class="font-bold text-sm uppercase tracking-wider text-slate-500 mb-3">🏷️ Related Tags</h3>
        <div class="flex flex-wrap">
            {''.join(tags_list)}
        </div>
    </div>"""
        content += tags_html
    
    # Add FAQ section (accordion HTML + Schema JSON-LD)
    faq_schema = json_data.get('faq_schema', [])
    faq_html = build_faq_html(faq_schema) 
    
    # Check if the AI accidentally left a plain-text FAQ at the bottom; if so, we just append the accordion anyway.
    # The accordion looks much better.
    content += faq_html
    
    # Excerpt
    excerpt = json_data.get('excerpt') or json_data.get('meta_description', '')
    if not excerpt:
        text = re.sub(r'<[^>]+>', '', content)
        excerpt = text[:155].strip() + "..." if len(text) > 155 else text
    
    # Author
    author_name = json_data.get('author_name', 'Little Smart Genius')
    author_display = author_name if author_name != 'Little Smart Genius' else 'Little Smart Genius Team'
    
    # Date & Time (Task 4.2)
    iso_date_str = json_data.get('iso_date', datetime.now().isoformat())
    iso_date = iso_date_str
    
    try:
        # Parse the ISO date string to a datetime object
        dt = datetime.fromisoformat(iso_date_str.replace('Z', '+00:00'))
        # Format as "Month DD, YYYY at HH:MM AM/PM"
        date_str = dt.strftime("%B %d, %Y at %I:%M %p")
    except ValueError:
        # Fallback if parsing fails
        date_str = json_data.get('date', datetime.now().strftime("%B %d, %Y at %I:%M %p"))
    
    # Category
    category = json_data.get('category', '')
    category_display = f'<span>&bull;</span><span>{category}</span>' if category else ''
    
    # Image
    image = normalize_image_path(json_data.get('image', 'images/placeholder.webp'))
    # Thumbnail path for srcset (mobile-optimised, ~14KB vs ~80KB)
    thumb_image = image.replace('images/', 'images/thumbs/', 1) if image.startswith('images/') else image
    
    # Custom OpenGraph image
    og_image = f"{SITE_URL}/images/og/{slug}.jpg"
    
    # Keywords
    keywords = ', '.join(json_data.get('keywords', []))
    
    # Reading time
    reading_time = json_data.get('reading_time', 5)
    
    # Canonical URL
    canonical_url = f"{SITE_URL}/articles/{slug}.html"
    
    # Related articles are handled exclusively by _post_process.py
    # (removed from build to avoid duplication)
    
    # Build prev/next navigation HTML
    prev_html = ''
    next_html = ''
    if prev_article:
        prev_url = prev_article['slug'] + '.html'
        prev_title = prev_article.get('title', 'Previous Article')[:45]
        prev_html = f'<div id="prevArticleNav" class="article-nav article-nav-prev"><a href="{prev_url}" title="{prev_title}">&#8592;</a><span class="nav-title">{prev_title}</span></div>'
    if next_article:
        next_url = next_article['slug'] + '.html'
        next_title = next_article.get('title', 'Next Article')[:45]
        next_html = f'<div id="nextArticleNav" class="article-nav article-nav-next"><a href="{next_url}" title="{next_title}">&#8594;</a><span class="nav-title">{next_title}</span></div>'
    
    # Build Breadcrumb UI HTML
    cat_slug = re.sub(r'[^a-z0-9]+', '-', category.lower()).strip('-') if category else ''
    cat_url = f"../blog-{cat_slug}.html" if cat_slug else "../blog.html"
    
    breadcrumb_html = f"""
        <nav aria-label="Breadcrumb" class="overflow-x-auto whitespace-nowrap pb-2">
            <ol class="flex items-center space-x-2 text-xs md:text-sm font-bold text-slate-500">
                <li><a href="../index.html" class="hover:text-brand transition flex items-center gap-1"><svg class="w-3 h-3 md:w-4 md:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"></path></svg>Home</a></li>
                <li><span class="text-slate-300">/</span></li>
                <li><a href="../blog.html" class="hover:text-brand transition">Blog</a></li>
"""
    if category:
        breadcrumb_html += f"""
                <li><span class="text-slate-300">/</span></li>
                <li><a href="{cat_url}" class="hover:text-brand transition">{category}</a></li>
"""
    breadcrumb_html += f"""
                <li><span class="text-slate-300">/</span></li>
                <li class="text-slate-400 truncate max-w-[200px] md:max-w-[400px]" aria-current="page" title="{title}">{title}</li>
            </ol>
        </nav>
"""
    
    # Contextual Lead Magnet
    lead_magnet_html = build_lead_magnet_html(category, freebies)
    
    html = ARTICLE_TEMPLATE.format(
        title=title,
        excerpt=excerpt,
        keywords=keywords,
        canonical_url=canonical_url,
        og_image=og_image,
        iso_date=iso_date,
        author_name=author_name,
        reading_time=reading_time,
        author_display=author_display,
        date=date_str,
        category_display=category_display,
        image=image,
        thumb_image=thumb_image,
        content=content,

        prev_nav_html=prev_html,
        next_nav_html=next_html,
        breadcrumb_html=breadcrumb_html,
        lead_magnet_html=lead_magnet_html
    )
    
    # ── Breadcrumb Schema ──
    breadcrumb_schema_json = build_breadcrumb_schema(title, category, canonical_url)
    
    # Add schemas before </head>
    faq_schema_json = build_faq_schema_json(faq_schema, title, canonical_url)
    all_schemas = breadcrumb_schema_json + (faq_schema_json if faq_schema_json else "")
    if all_schemas:
        html = html.replace('</head>', f'{all_schemas}\n</head>')
    
    return html


def build_all():
    """Build all HTML articles and index files from post JSONs."""
    
    print("=" * 80)
    print("  BUILD ARTICLES — Converting post JSONs to HTML + indexes")
    print("=" * 80)
    
    # Load all post JSONs
    post_files = sorted(glob.glob(os.path.join(POSTS_DIR, "*.json")))
    print(f"\n  Found {len(post_files)} post JSONs in posts/")
    
    all_articles = []
    all_post_data = []  # Store raw data for second pass
    errors = []
    
    # ── PASS 1: Collect all metadata (for related articles) ──
    print("\n  Pass 1: Collecting article metadata...")
    for i, pf in enumerate(post_files, 1):
        try:
            with open(pf, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            slug = data.get('slug', os.path.basename(pf).replace('.json', ''))
            title = data.get('title', 'Untitled')
            
            # Build article metadata for index
            article_meta = {
                "title": data.get('title', 'Untitled'),
                "slug": slug,
                "date": data.get('date', ''),
                "iso_date": data.get('iso_date', ''),
                "category": data.get('category', ''),
                "excerpt": (data.get('excerpt') or data.get('meta_description', ''))[:200],
                "image": normalize_image_path(data.get('image', '')),
                "reading_time": data.get('reading_time', 5),
                "url": f"articles/{slug}.html",
                "keywords": data.get('keywords', []),
                "word_count": data.get('word_count', 0),
                "slot": data.get('slot', ''),
            }
            all_articles.append(article_meta)
            all_post_data.append((data, slug))
            
        except Exception as e:
            errors.append((pf, str(e)))
            print(f"  [{i:>2}] ERR {os.path.basename(pf)}: {str(e)[:60]}")
    
    # Sort articles by date (newest first)
    all_articles.sort(key=lambda a: a.get('iso_date', ''), reverse=True)
    
    tpt_products = load_tpt_products()
    freebies = load_freebies()
    
    # ── PASS 2: Generate HTML with related articles + prev/next nav ──
    # Build a slug-to-index mapping in sorted order for prev/next
    slug_to_sorted_idx = {a['slug']: idx for idx, a in enumerate(all_articles)}
    
    print(f"  Pass 2: Generating {len(all_post_data)} HTML pages with related articles...")
    for i, (data, slug) in enumerate(all_post_data, 1):
        try:
            title = data.get('title', 'Untitled')
            
            # Determine prev/next articles in date-sorted order
            sorted_idx = slug_to_sorted_idx.get(slug)
            prev_art = all_articles[sorted_idx - 1] if sorted_idx is not None and sorted_idx > 0 else None
            next_art = all_articles[sorted_idx + 1] if sorted_idx is not None and sorted_idx < len(all_articles) - 1 else None
            
            # Generate HTML (now with related articles + prev/next nav)
            html = generate_article_html(data, slug, all_articles=all_articles, prev_article=prev_art, next_article=next_art, tpt_products=tpt_products, freebies=freebies)
            
            # Save HTML file
            html_path = os.path.join(ARTICLES_DIR, f"{slug}.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            html_size = os.path.getsize(html_path) // 1024
            
            print(f"  [{i:>2}] OK  {html_size:>3}KB  {title[:60]}")
            
        except Exception as e:
            errors.append((slug, str(e)))
            print(f"  [{i:>2}] ERR {slug}: {str(e)[:60]}")
            traceback.print_exc()
    
    # Build search_index.json
    index_data = {
        "generated_at": datetime.now().isoformat(),
        "total_articles": len(all_articles),
        "articles": all_articles
    }
    
    search_index_path = os.path.join(BASE_DIR, "search_index.json")
    with open(search_index_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)
    print(f"\n  search_index.json: {len(all_articles)} articles")
    
    # Build articles.json (backward compat)
    articles_json_path = os.path.join(BASE_DIR, "articles.json")
    with open(articles_json_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)
    print(f"  articles.json: {len(all_articles)} articles")
    
    # Build sitemap.xml
    sitemap_entries = []
    
    static_pages = [
        ('index.html', '1.0', 'daily'),
        ('blog.html', '0.9', 'daily'),
        ('products.html', '0.8', 'weekly'),
        ('freebies.html', '0.8', 'weekly'),
        ('about.html', '0.7', 'monthly'),
        ('contact.html', '0.7', 'monthly'),
    ]
    
    for page, priority, changefreq in static_pages:
        sitemap_entries.append(f"""  <url>
    <loc>{SITE_URL}/{page}</loc>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>""")
    
    for article in all_articles:
        url = article.get('url', '')
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
    
    sitemap_path = os.path.join(BASE_DIR, "sitemap.xml")
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write(sitemap_xml)
    print(f"  sitemap.xml: {len(sitemap_entries)} URLs")
    
    # Summary
    print(f"\n{'=' * 80}")
    print(f"  BUILD COMPLETE")
    print(f"{'=' * 80}")
    print(f"  HTML articles: {len(all_articles)} in articles/")
    print(f"  Indexes: search_index.json + articles.json")
    print(f"  Sitemap: {len(sitemap_entries)} URLs")
    if errors:
        print(f"  ERRORS: {len(errors)}")
        for pf, err in errors:
            print(f"    {os.path.basename(pf)}: {err}")
    else:
        print(f"  No errors!")
        
    print(f"\n{'=' * 80}")
    print(f"  RUNNING POST-PROCESSOR (Related Articles & TPT Products)")
    print(f"{'=' * 80}")
    import subprocess
    post_process_script = os.path.join(BASE_DIR, "scripts", "_post_process.py")
    if os.path.exists(post_process_script):
        subprocess.run([sys.executable, post_process_script])
    else:
        print(f"  [!] _post_process.py not found at {post_process_script}")


if __name__ == "__main__":
    build_all()
