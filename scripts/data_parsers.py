"""
DATA PARSERS — V4.0
Parse products_tpt.js and download_links.js to get live product/freebie data.
Eliminates hardcoded TPT_PRODUCTS_FULL and FREEBIES_CATEGORIES.
"""

import os
import re
import json
from typing import List, Dict

# Resolve paths relative to project root (parent of scripts/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)


def parse_products_tpt(filepath: str = None) -> List[Dict]:
    """
    Parse products_tpt.js → List of product dicts.
    
    products_tpt.js format:
        window.tptProducts = [[name, url, img, price, category, rating, reviews, preview], ...]
    
    Returns list of dicts with keys:
        name, url, image, price, category, rating, reviews, preview_url
    """
    if filepath is None:
        filepath = os.path.join(BASE_DIR, "products_tpt.js")
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract the JSON array from: window.tptProducts = [...];
    # The file has everything on one line, so we find the balanced brackets
    start_idx = content.find("window.tptProducts")
    if start_idx == -1:
        raise ValueError(f"Could not find window.tptProducts in {filepath}")
    
    # Find the opening bracket
    bracket_start = content.index("[", start_idx)
    
    # Find matching closing bracket by counting depth
    depth = 0
    bracket_end = bracket_start
    for i in range(bracket_start, len(content)):
        if content[i] == "[":
            depth += 1
        elif content[i] == "]":
            depth -= 1
            if depth == 0:
                bracket_end = i
                break
    
    json_str = content[bracket_start:bracket_end + 1]
    raw_array = json.loads(json_str)
    
    products = []
    for item in raw_array:
        if len(item) < 5:
            continue
        products.append({
            "name": item[0],
            "url": item[1],
            "image": f"https://ecdn.teacherspayteachers.com/thumbitem/{item[2]}" if item[2] else "",
            "price": item[3],
            "category": item[4],
            "rating": item[5] if len(item) > 5 else "",
            "reviews": item[6] if len(item) > 6 else "",
            "preview_url": item[7] if len(item) > 7 else ""
        })
    
    return products


def parse_download_links(filepath: str = None) -> Dict[str, Dict]:
    """
    Parse download_links.js → Dict of freebie name → {link, desc}.
    
    download_links.js format:
        const productData = { "Name": { link: "...", desc: "..." }, ... };
    
    Returns dict like:
        {"Tic Tac Toe": {"link": "https://...", "desc": "Strategy game..."}, ...}
    """
    if filepath is None:
        filepath = os.path.join(BASE_DIR, "download_links.js")
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract everything between the outer braces of productData = {...}
    match = re.search(r"const\s+productData\s*=\s*\{(.+)\};", content, re.DOTALL)
    if not match:
        raise ValueError(f"Could not find productData in {filepath}")
    
    inner = match.group(1)
    
    # Parse each entry: "Name": { link: "...", desc: "..." }
    freebies = {}
    entry_pattern = re.compile(
        r'"([^"]+)"\s*:\s*\{[^}]*link\s*:\s*"([^"]+)"[^}]*desc\s*:\s*"([^"]+)"[^}]*\}',
        re.DOTALL
    )
    
    for m in entry_pattern.finditer(inner):
        name = m.group(1)
        link = m.group(2)
        desc = m.group(3)
        freebies[name] = {"link": link, "desc": desc}
    
    return freebies


def get_product_categories() -> List[str]:
    """Get unique product categories from products_tpt.js."""
    products = parse_products_tpt()
    return list(set(p["category"] for p in products))


def get_freebie_names() -> List[str]:
    """Get all freebie names from download_links.js."""
    freebies = parse_download_links()
    return list(freebies.keys())


def get_products_by_category(category: str = None) -> Dict[str, List[Dict]]:
    """Group products by category. If category given, return only that category."""
    products = parse_products_tpt()
    grouped = {}
    for p in products:
        cat = p["category"]
        if category and cat != category:
            continue
        grouped.setdefault(cat, []).append(p)
    return grouped


# --- Self-test ---
if __name__ == "__main__":
    print("=" * 60)
    print("DATA PARSERS — Self Test")
    print("=" * 60)
    
    products = parse_products_tpt()
    print(f"\nProducts (products_tpt.js): {len(products)} items")
    cats = get_product_categories()
    print(f"Categories: {cats}")
    for p in products[:3]:
        print(f"  - {p['name'][:60]}... | {p['price']} | {p['category']}")
    
    freebies = parse_download_links()
    print(f"\nFreebies (download_links.js): {len(freebies)} items")
    for name in list(freebies.keys())[:5]:
        print(f"  - {name}: {freebies[name]['desc'][:60]}...")
    
    print("\nAll tests passed!")
