"""
TOPIC SELECTOR — V4.0
Manages topic selection across 3 slots (keyword, product, freebie).
Tracks used topics to avoid repetition.
"""

import os
import json
import random
from datetime import datetime
from typing import Dict, Optional

from data_parsers import parse_products_tpt, parse_download_links

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BASE_DIR = PROJECT_ROOT
USED_TOPICS_FILE = os.path.join(PROJECT_ROOT, "data", "used_topics.json")
KEYWORDS_FILE = os.path.join(PROJECT_ROOT, "data", "keywords.txt")

# Category mapping: maps freebie names to broader categories for prompt context
FREEBIE_CATEGORIES = {
    # Logic
    "Tic Tac Toe": "Critical Thinking", "Shikaku": "Critical Thinking",
    "Hitori": "Critical Thinking", "Four In A Row": "Critical Thinking",
    "Skyscraper": "Critical Thinking",
    # Words
    "ABC Path": "Language Arts", "Hangman": "Language Arts",
    "Word Search": "Language Arts", "Spot Correct Spelling": "Language Arts",
    "Cryptogram": "Language Arts", "Complete the Word": "Language Arts",
    "Word Pack": "Language Arts",
    # Math
    "Sudoku": "Math Skills", "Kids Math Equations": "Math Skills",
    "Counting Numbers": "Math Skills", "Range Puzzle": "Math Skills",
    "Number Crossword": "Math Skills",
    # Creative / Visual
    "Coloring Page (Kids)": "Creative Arts", "Coloring Page (Adult)": "Creative Arts",
    "Spot the Difference": "Visual Skills", "Shadow Matching": "Visual Skills",
    "Maze for Kids": "Problem Solving", "Connect the Dots": "Fine Motor Skills",
    "Cookbook for Kids": "Creative Arts", "Stickers Pack": "Creative Arts",
}


class TopicSelector:
    """
    Selects the next topic for each slot (keyword, product, freebie),
    avoiding previously used topics.
    """

    def __init__(self):
        self.used = self._load_used()
        self.keywords = self._load_keywords()
        self.products = parse_products_tpt()
        self.freebies = parse_download_links()

    def _load_used(self) -> Dict:
        """Load used_topics.json or create default."""
        if os.path.exists(USED_TOPICS_FILE):
            with open(USED_TOPICS_FILE, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    pass
        return {"keyword": [], "product": [], "freebie": [], "daily_log": []}

    def _save_used(self):
        """Save used_topics.json."""
        with open(USED_TOPICS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.used, f, indent=2, ensure_ascii=False)

    def _load_keywords(self):
        """Load keywords.txt, filtering comments and blanks."""
        keywords = []
        if os.path.exists(KEYWORDS_FILE):
            with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        keywords.append(line)
        return keywords

    def get_next_topic(self, slot: str) -> Optional[Dict]:
        """
        Get the next unused topic for a given slot.
        
        Args:
            slot: "keyword", "product", or "freebie"
        
        Returns:
            Dict with keys: slot, topic_name, category, keywords, product_data (optional)
            None if all topics in this slot have been used.
        """
        if slot == "keyword":
            return self._get_keyword_topic()
        elif slot == "product":
            return self._get_product_topic()
        elif slot == "freebie":
            return self._get_freebie_topic()
        else:
            raise ValueError(f"Unknown slot: {slot}. Use 'keyword', 'product', or 'freebie'.")

    def _get_keyword_topic(self) -> Optional[Dict]:
        """Pick an unused keyword from keywords.txt."""
        used_kw = set(self.used.get("keyword", []))
        available = [k for k in self.keywords if k not in used_kw]

        if not available:
            print(f"[TopicSelector] All {len(self.keywords)} keywords used! Resetting...")
            self.used["keyword"] = []
            available = self.keywords.copy()

        if not available:
            return None

        keyword = random.choice(available)

        # Derive category from keyword content
        kw_lower = keyword.lower()
        if any(w in kw_lower for w in ["math", "number", "count", "sudoku"]):
            category = "Math Skills"
        elif any(w in kw_lower for w in ["word", "spell", "vocabulary", "alphabet", "letter"]):
            category = "Language Arts"
        elif any(w in kw_lower for w in ["logic", "brain", "critical", "problem"]):
            category = "Critical Thinking"
        elif any(w in kw_lower for w in ["color", "creative", "art", "motor"]):
            category = "Creative Arts"
        elif any(w in kw_lower for w in ["spot", "visual", "maze", "shadow", "picture"]):
            category = "Visual Skills"
        else:
            category = "Education"

        return {
            "slot": "keyword",
            "topic_name": keyword,
            "category": category,
            "keywords": keyword,
            "product_data": None
        }

    def _get_product_topic(self) -> Optional[Dict]:
        """Pick an unused product from products_tpt.js."""
        used_names = set(self.used.get("product", []))
        available = [p for p in self.products if p["name"] not in used_names]

        if not available:
            print(f"[TopicSelector] All {len(self.products)} products used! Resetting...")
            self.used["product"] = []
            available = self.products.copy()

        if not available:
            return None

        product = random.choice(available)

        # Extract keywords from product name
        name_words = product["name"].lower()
        keywords_parts = []
        if "spot" in name_words and "difference" in name_words:
            keywords_parts = ["spot the difference", "visual perception", "picture puzzles"]
        elif "word search" in name_words:
            keywords_parts = ["word search", "vocabulary", "spelling practice"]
        elif "coloring" in name_words:
            keywords_parts = ["coloring pages", "creative activities", "fine motor skills"]
        else:
            keywords_parts = [w for w in product["name"].split("|")[0].strip().lower().split() if len(w) > 3]

        return {
            "slot": "product",
            "topic_name": product["name"],
            "category": product["category"],
            "keywords": ", ".join(keywords_parts[:5]),
            "product_data": product
        }

    def _get_freebie_topic(self) -> Optional[Dict]:
        """Pick an unused freebie from download_links.js."""
        used_names = set(self.used.get("freebie", []))
        available = [name for name in self.freebies.keys() if name not in used_names]

        if not available:
            print(f"[TopicSelector] All {len(self.freebies)} freebies used! Resetting...")
            self.used["freebie"] = []
            available = list(self.freebies.keys())

        if not available:
            return None

        freebie_name = random.choice(available)
        freebie_data = self.freebies[freebie_name]
        category = FREEBIE_CATEGORIES.get(freebie_name, "Education")

        # Build keywords from name + description
        desc_words = freebie_data["desc"].lower().split()
        keywords_parts = [freebie_name.lower()]
        keywords_parts.extend([w for w in desc_words if len(w) > 4][:4])

        return {
            "slot": "freebie",
            "topic_name": freebie_name,
            "category": category,
            "keywords": ", ".join(keywords_parts[:5]),
            "product_data": {
                "name": freebie_name,
                "url": freebie_data["link"],
                "desc": freebie_data["desc"],
                "price": "FREE"
            }
        }

    def mark_used(self, slot: str, topic_name: str):
        """Mark a topic as used after successful article generation."""
        if slot not in self.used:
            self.used[slot] = []
        if topic_name not in self.used[slot]:
            self.used[slot].append(topic_name)

        # Log to daily_log
        self.used["daily_log"].append({
            "slot": slot,
            "topic": topic_name,
            "date": datetime.now().isoformat(),
        })

        self._save_used()

    def get_stats(self) -> Dict:
        """Return usage statistics."""
        return {
            "keywords_total": len(self.keywords),
            "keywords_used": len(self.used.get("keyword", [])),
            "keywords_remaining": len(self.keywords) - len(self.used.get("keyword", [])),
            "products_total": len(self.products),
            "products_used": len(self.used.get("product", [])),
            "products_remaining": len(self.products) - len(self.used.get("product", [])),
            "freebies_total": len(self.freebies),
            "freebies_used": len(self.used.get("freebie", [])),
            "freebies_remaining": len(self.freebies) - len(self.used.get("freebie", [])),
            "total_articles": len(self.used.get("daily_log", [])),
        }


# --- Self-test ---
if __name__ == "__main__":
    print("=" * 60)
    print("TOPIC SELECTOR — Self Test")
    print("=" * 60)

    ts = TopicSelector()
    stats = ts.get_stats()
    print(f"\nStats: {json.dumps(stats, indent=2)}")

    for slot in ["keyword", "product", "freebie"]:
        topic = ts.get_next_topic(slot)
        if topic:
            print(f"\n[{slot.upper()}] Next topic:")
            print(f"  Name: {topic['topic_name'][:60]}")
            print(f"  Category: {topic['category']}")
            print(f"  Keywords: {topic['keywords'][:60]}")
        else:
            print(f"\n[{slot.upper()}] No topics available!")

    print("\nAll tests passed!")
