import requests
from bs4 import BeautifulSoup
import time
import random
import re
import json
import os
import sys
import io

# --- 0. FIX ENCODAGE ---
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
except:
    pass

# Resolve project root (parent of scripts/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# ==========================================
# CONFIGURATION GLOBALE
# ==========================================
STORE_URL = "https://www.teacherspayteachers.com/store/little-smart-genius"
LOCAL_TEST_FILE = os.path.join(PROJECT_ROOT, "page.html") # Pour tests locaux

# Fichiers de sortie
FILE_JS_HOMEPAGE = os.path.join(PROJECT_ROOT, "featured_products.js") # Pour index.html
FILE_JS_STORE = os.path.join(PROJECT_ROOT, "products_tpt.js")         # Pour products.html

# Fichier source pour les freebies
SOURCE_FREEBIES = os.path.join(PROJECT_ROOT, "freebies.html")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com/',
}

# ==========================================
# 1. UTILITAIRES (Communs aux deux logiques)
# ==========================================

def determine_category(title):
    t = title.lower()
    if "visual perception" in t: return "Spot the Difference (Photorealistic)"
    if "brain games" in t: return "Spot the Difference for Kids"
    if "word search" in t: return "Word Search Activity Worksheet"
    if "coloring" in t: return "Coloring Book"
    if "spot the difference" in t: return "Spot the Difference for Kids"
    return "Other Resources"

def clean_image_url(url):
    if not url: return ""
    try:
        if "cdn-cgi" in url or "/thumbitem/" in url:
            parts = url.split("/thumbitem/")
            if len(parts) > 1: return parts[1]
    except: pass
    return url

def extract_single_best_price(card):
    full_text = card.get_text(" ", strip=True)
    if "FREE" in full_text.upper() or "Free" in full_text: return "FREE"
    found_prices = re.findall(r'\$\d+\.\d{2}', full_text)
    if found_prices:
        try:
            values = sorted(list(set([float(p.replace("$", "")) for p in found_prices])))
            return f"${values[0]:.2f}"
        except: return found_prices[0]
    return "$?.??"

def get_preview_data(product_link):
    try:
        if "/Product/" not in product_link: return ""
        parts = product_link.split("/Product/")
        slug = parts[1].split("?")[0].replace("-", "")
        return f"https://www.teacherspayteachers.com/Preview/{parts[1].split('?')[0]}?fn=demo{slug}.pdf"
    except: return ""

# ==========================================
# 2. LE GRAND SCANNER (TpT)
# ==========================================
def scan_whole_store():
    print("🚀 Démarrage du SCAN UNIQUE de la boutique...")
    mode = "WEB"
    if os.path.exists(LOCAL_TEST_FILE):
        print(f"   📂 Mode local activé ({LOCAL_TEST_FILE}).")
        with open(LOCAL_TEST_FILE, "r", encoding="utf-8") as f: content = f.read()
        mode = "LOCAL"
        soup = BeautifulSoup(content, 'html.parser')
        cards = soup.find_all("div", attrs={"data-testid": "ProductRow"})
        if not cards: cards = soup.find_all("div", class_=lambda x: x and "ProductRowCard" in x)
    else:
        print("   🌐 Mode Web activé.")
    
    all_products = []
    categories_found = set()
    page = 1
    
    while True:
        if mode == "WEB":
            print(f"   ⮑ Analyse de la Page {page}...")
            try:
                time.sleep(random.uniform(1.0, 2.0)) # Pause polie
                response = requests.get(f"{STORE_URL}?page={page}", headers=HEADERS, timeout=20)
                if response.status_code != 200: break
                soup = BeautifulSoup(response.content, 'html.parser')
                cards = soup.find_all("div", attrs={"data-testid": "ProductRow"})
                if not cards: cards = soup.find_all("div", class_=lambda x: x and "ProductRowCard" in x)
                if not cards: break
            except Exception as e: 
                print(f"   ❌ Erreur: {e}")
                break
        
        if mode == "LOCAL" and page > 1: break

        for card in cards:
            try:
                # Titre & Lien
                title_link = None
                links = card.find_all("a", href=True)
                for l in links:
                    if "/Product/" in l['href'] and len(l.text.strip()) > 5:
                        title_link = l; break
                
                if not title_link: continue
                href = title_link['href']
                if not href.startswith("http"): href = "https://www.teacherspayteachers.com" + href
                title = title_link.text.strip()
                
                # Anti-Doublon global
                if any(p['url'] == href for p in all_products): continue

                # Image
                img_src = ""
                source_tag = card.find("source", attrs={"type": "image/avif"})
                if source_tag and "srcset" in source_tag.attrs: img_src = source_tag['srcset'].split(" ")[0]
                else:
                    img_tag = card.find("img")
                    if img_tag: img_src = img_tag.get('src')
                clean_path = clean_image_url(img_src)
                if not clean_path: continue

                # Données
                price = extract_single_best_price(card)
                cat = determine_category(title)
                categories_found.add(cat)
                
                # Rating & Review (Pour Store Page)
                rating = "New"; reviews = ""
                rating_div = card.find("div", class_=lambda x: x and "Ratings-module__starContainer" in x)
                if rating_div:
                    sr = rating_div.find("span", class_=lambda x: x and "srOnly" in x)
                    if sr:
                        txt = sr.text
                        r_match = re.search(r'Rated ([\d\.]+) out', txt)
                        c_match = re.search(r'based on (\d+) reviews', txt)
                        if r_match: rating = r_match.group(1); reviews = c_match.group(1)
                
                # PDF Preview (Pour Store Page)
                pdf = get_preview_data(href)

                # On stocke un objet dictionnaire propre (plus facile à manipuler)
                product_obj = {
                    "name": title,
                    "url": href,
                    "img_clean": clean_path,
                    "price": price,
                    "category": cat,
                    "rating": rating,
                    "reviews": reviews,
                    "pdf": pdf
                }
                all_products.append(product_obj)
            except: continue

        if mode == "LOCAL": break
        if mode == "WEB" and not cards: break
        page += 1
    
    return all_products, sorted(list(categories_found))

# ==========================================
# 3. SCANNER FREEBIES (Local)
# ==========================================
def process_local_freebies():
    print(f"🔍 Extraction des Freebies depuis {SOURCE_FREEBIES}...")
    if not os.path.exists(SOURCE_FREEBIES):
        print("   ❌ Fichier introuvable.")
        return []

    with open(SOURCE_FREEBIES, "r", encoding="utf-8") as f: content = f.read()
    
    # Regex pour extraire les objets JS
    pattern = r'\{\s*name:\s*"(.*?)",\s*icon:\s*"(.*?)",\s*category:\s*"(.*?)"\s*\}'
    matches = re.findall(pattern, content)
    
    raw_freebies = [{"name": m[0], "icon": m[1], "category": m[2]} for m in matches]
    
    # Logique de tri intelligent (2 Sticky + 8 Randoms équilibrés)
    target_sticky = ["Spot the Difference", "Cookbook for Kids"]
    cats = {"logic": [], "math": [], "word": [], "creative": []}
    
    sticky_items = []
    pool = []
    
    for item in raw_freebies:
        if item["name"] in target_sticky:
            # On les garde de côté pour les mettre en premier
            pass
        else:
            if item["category"] in cats: cats[item["category"]].append(item)
    
    # Récupérer les sticky
    s1 = next((x for x in raw_freebies if x["name"] == target_sticky[0]), None)
    s2 = next((x for x in raw_freebies if x["name"] == target_sticky[1]), None)
    
    final_list = []
    if s1: final_list.append(s1)
    if s2: final_list.append(s2)
    
    # Prendre 2 de chaque catégorie restante
    for cat_name in ["logic", "math", "word", "creative"]:
        available = cats[cat_name]
        random.shuffle(available)
        final_list.extend(available[:2])
        
    print(f"   📦 {len(final_list)} freebies sélectionnés.")
    return final_list

# ==========================================
# 4. GÉNÉRATEURS DE FICHIERS JS
# ==========================================

def generate_homepage_js(all_products, freebies):
    """Génère featured_products.js pour l'accueil (Données légères)"""
    print(f"✨ Génération {FILE_JS_HOMEPAGE} (Accueil)...")
    
    # On prend uniquement les produits payants pour la vitrine "Premium Picks"
    paid_products = [p for p in all_products if p["price"] != "FREE"]
    
    # On mélange et on en prend 8
    random.shuffle(paid_products)
    selection = paid_products[:8]
    
    # Formatage léger (juste ce dont l'index a besoin)
    js_products = []
    for p in selection:
        full_img = f"https://ecdn.teacherspayteachers.com/thumbitem/{p['img_clean']}"
        js_products.append({
            "name": p["name"],
            "url": p["url"],
            "img": full_img,
            "price": p["price"],
            "category": p["category"]
        })
    
    content = f"window.importedProducts = {json.dumps(js_products, ensure_ascii=False, indent=4)};\n\n"
    content += f"window.importedFreebies = {json.dumps(freebies, ensure_ascii=False, indent=4)};"
    
    with open(FILE_JS_HOMEPAGE, "w", encoding="utf-8") as f:
        f.write(content)

def generate_storepage_js(all_products, categories):
    """Génère products_tpt.js pour la boutique (Données complètes)"""
    print(f"✨ Génération {FILE_JS_STORE} (Boutique)...")
    
    # Tri des catégories
    desired_order = ["Spot the Difference (Photorealistic)", "Spot the Difference for Kids", "Word Search Activity Worksheet", "Coloring Book"]
    final_cats = [c for c in desired_order if c in categories]
    for c in categories:
        if c not in final_cats: final_cats.append(c)
    
    # Formatage Matrice (Liste de listes) pour réduire la taille du fichier
    # Ordre: [Title, URL, CleanPath, Price, Cat, Rating, Reviews, PdfLink]
    matrix_products = []
    for p in all_products:
        matrix_products.append([
            p["name"],
            p["url"],
            p["img_clean"],
            p["price"],
            p["category"],
            p["rating"],
            p["reviews"],
            p["pdf"]
        ])
    
    content = f"// DONNÉES AUTOMATIQUES GÉNÉRÉES\n"
    content += f"window.tptProducts = {json.dumps(matrix_products, ensure_ascii=False)};\n"
    content += f"window.tptCategories = {json.dumps(final_cats, ensure_ascii=False)};"
    
    with open(FILE_JS_STORE, "w", encoding="utf-8") as f:
        f.write(content)

# ==========================================
# 5. PRODUCT THUMBNAIL SYNC (WebP local)
# ==========================================
def ensure_product_thumbs(all_products):
    """
    After each scan, ensure every product has a local WebP thumbnail in
    images/products-thumbs/<product_id>.webp.
    Downloads and converts any missing ones from the TPT CDN.
    """
    try:
        from PIL import Image
        from io import BytesIO
        import urllib.request as ureq
    except ImportError:
        print("   [thumbs] Pillow not installed — skipping thumbnail sync (pip install Pillow)")
        return

    thumbs_dir = os.path.join(PROJECT_ROOT, "images", "products-thumbs")
    os.makedirs(thumbs_dir, exist_ok=True)
    local_files = set(os.listdir(thumbs_dir))

    missing = []
    for p in all_products:
        img_path = p["img_clean"]
        pid_match = re.search(r"-(\d{7,})-", img_path)
        if not pid_match:
            continue
        pid = pid_match.group(1)
        if f"{pid}.webp" not in local_files:
            missing.append((pid, img_path, p["name"]))

    if not missing:
        print(f"   [thumbs] All {len(all_products)} product thumbnails already present locally. OK")
        return

    print(f"   [thumbs] {len(missing)} new thumbnail(s) to download...")
    downloaded = errors = 0
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for pid, img_path, name in missing:
        url = f"https://ecdn.teacherspayteachers.com/cdn-cgi/image/format=auto,width=480,quality=80/thumbitem/{img_path}"
        out_path = os.path.join(thumbs_dir, f"{pid}.webp")
        try:
            request = ureq.Request(url, headers=headers)
            with ureq.urlopen(request, timeout=15) as resp:
                data = resp.read()
            img = Image.open(BytesIO(data)).convert("RGB")
            img.thumbnail((480, 480), Image.LANCZOS)
            img.save(out_path, "WEBP", quality=80, method=6)
            size_kb = os.path.getsize(out_path) // 1024
            print(f"   [thumbs] OK [{pid}] {name[:45]:<45} -> {size_kb}KB")
            local_files.add(f"{pid}.webp")
            downloaded += 1
            time.sleep(0.2)
        except Exception as e:
            print(f"   [thumbs] ERR [{pid}] {name[:45]}: {e}")
            errors += 1

    print(f"   [thumbs] Done: {downloaded} downloaded, {errors} error(s).")


# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    start_time = time.time()

    # 1. SCANNER TOUT UNE FOIS
    products, categories = scan_whole_store()

    if products:
        print(f"OK Scan termine : {len(products)} produits trouves.")

        # 2. PREPARER FREEBIES
        freebies_list = process_local_freebies()

        # 3. GENERER SORTIE ACCUEIL (featured_products.js)
        generate_homepage_js(products, freebies_list)

        # 4. GENERER SORTIE BOUTIQUE (products_tpt.js)
        generate_storepage_js(products, categories)

        # 5. SYNC MINIATURES WEBP (auto-complete les manquantes)
        print("\nVerification des miniatures produits locales...")
        ensure_product_thumbs(products)

        print(f"TERMINE en {round(time.time() - start_time, 2)} secondes.")
    else:
        print("Erreur critique : Aucun produit trouve.")