"""
AUTO BLOG ULTIMATE V3.2 - CONFIGURATION API SPECIALISEE
Generation + Real Images (Klein-Large) + SEO Correction + Internal/TPT Links
(c) 2026 Little Smart Genius

NOUVEAUTES V3.2:
- Configuration API specialisee par role (Plan, Contenu, Images, SEO)
- Model Flux Klein-Large via Pollinations (2 cles backup)
- Directeur artistique dedie pour optimisation prompts
- Toutes les fonctionnalites V3.1 preservees
"""

import os
import json
import random
import re
import time
import requests
# [V3.4] google.generativeai remplace par DeepSeek API (V3.2 Thinking Mode)
from datetime import datetime
import urllib.parse
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from typing import Dict, List, Optional, Tuple

load_dotenv()

# ===================================================================
# CONFIGURATION API SPECIALISEE V3.2
# ===================================================================

# TEXTE — DeepSeek-V3.2 Thinking Mode
DEEPSEEK_API_KEY    = os.environ.get("DEEPSEEK_API_KEY")        # Cle DeepSeek
DEEPSEEK_TEXT_MODEL = "deepseek-reasoner"                       # V3.2 Thinking Mode
DEEPSEEK_TEXT_URL   = "https://api.deepseek.com/v1/chat/completions"

# IMAGES — Pollinations Klein-Large (5 cles, inchange)
POLLINATIONS_KEY_1 = os.environ.get("POLLINATIONS_API_KEY_1")    # Cle image 1
POLLINATIONS_KEY_2 = os.environ.get("POLLINATIONS_API_KEY_2")    # Cle image 2
POLLINATIONS_KEY_3 = os.environ.get("POLLINATIONS_API_KEY_3")    # Cle image 3
POLLINATIONS_KEY_4 = os.environ.get("POLLINATIONS_API_KEY_4")    # Cle image 4
POLLINATIONS_KEY_5 = os.environ.get("POLLINATIONS_API_KEY_5")    # Cle image 5
POLLINATIONS_KEYS = [k for k in [
    POLLINATIONS_KEY_1, POLLINATIONS_KEY_2, POLLINATIONS_KEY_3,
    POLLINATIONS_KEY_4, POLLINATIONS_KEY_5
] if k]
POLLINATIONS_MODEL = "klein-large"                               # Images (inchange)

# Variables de compatibilite (roles tous geres par DeepSeek maintenant)
API_KEY_PLAN    = None          # Remplace par DeepSeek
API_KEY_DIR_ART = None          # Remplace par DeepSeek
API_KEY_SEO     = None          # Remplace par DeepSeek
CONTENT_KEYS    = [DEEPSEEK_API_KEY] if DEEPSEEK_API_KEY else []  # Compatibilite

# Configuration generale
POSTS_DIR = "posts"
IMAGES_DIR = "images"
LOGS_DIR = "logs"
TARGET_WORD_COUNT = 1800
MIN_WORD_COUNT = 1200
MAX_RETRIES = 3
IMAGE_RETRY_MAX = 3

NUM_CONTENT_IMAGES = 3
TOTAL_IMAGES = 4

SITE_BASE_URL = "https://littlesmartgenius.com"

session_api_config = {"key": None, "model": None}
MODELS_RANKING = MODELS_RANKING = [
    # Tier 1: Modeles stables et performants
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-exp-1206",
    
    # Tier 2: Modeles alias (toujours a jour)
    "gemini-pro-latest",
    "gemini-flash-latest",
    
    # Tier 3: Modeles versions specifiques
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    
    # Tier 4: Modeles lite (si quotas epuises)
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
    "gemini-flash-lite-latest",
    
    # Tier 5: Modeles preview (quotas separes potentiels)
    "gemini-3-pro-preview",
    "gemini-3-flash-preview",
    "gemini-2.5-flash-preview-09-2025",
]


# ===================================================================
# BASE DE DONNEES TPT COMPLETE (50+ produits)
# ===================================================================

TPT_PRODUCTS_FULL = {
    "spot_difference_photorealistic": [
        {"name": "Spot the Difference Streets Vol.4", "url": "https://www.teacherspayteachers.com/Product/Spot-the-Difference-Picture-Puzzle-Visual-Perception-Activity-Streets-Vol4-10478133", "price": "$3.00"},
        {"name": "Spot the Difference Rooms Vol.1", "url": "https://www.teacherspayteachers.com/Product/Spot-the-Difference-Picture-Puzzle-Visual-Perception-Activity-Rooms-Vol1-10561567", "price": "$3.00"},
        {"name": "Spot the Difference Animals Vol.1", "url": "https://www.teacherspayteachers.com/Product/Spot-the-Difference-Picture-Puzzle-Visual-Perception-Activity-Animals-Vol1-10436437", "price": "$3.00"},
        {"name": "Spot the Difference Animals Bundle", "url": "https://www.teacherspayteachers.com/Product/Spot-the-Difference-Picture-Puzzle-Visual-Perception-Activity-Animals-Bundle-14654622", "price": "$12.60"},
        {"name": "Spot the Difference Buildings Vol.1", "url": "https://www.teacherspayteachers.com/Product/Spot-the-Difference-Picture-Puzzle-Visual-Perception-Buildings-Vol1-10464350", "price": "$3.00"},
        {"name": "Spot the Difference Beach Vol.1", "url": "https://www.teacherspayteachers.com/Product/Spot-the-Difference-Picture-Puzzle-Visual-Perception-Activity-Beach-Vol1-10477574", "price": "$3.00"},
    ],
    "spot_difference_kids": [
        {"name": "Spot the Difference School Classroom Vol.8", "url": "https://www.teacherspayteachers.com/Product/Spot-the-Difference-Picture-Puzzles-Brain-Games-School-Classroom-Vol8-15413169", "price": "$3.00"},
        {"name": "Spot the Difference School Classroom Vol.7", "url": "https://www.teacherspayteachers.com/Product/Spot-the-Difference-Picture-Puzzles-Brain-Games-School-Classroom-Vol7-15413166", "price": "$3.00"},
        {"name": "Spot the Difference School Classroom Vol.6", "url": "https://www.teacherspayteachers.com/Product/Spot-the-Difference-Picture-Puzzles-Brain-Games-School-Classroom-Vol6-15413165", "price": "$3.00"},
    ],
    "word_search": [
        {"name": "Thanksgiving Word Search Bundle", "url": "https://www.teacherspayteachers.com/Product/Thanksgiving-Word-Search-Adventure-Fun-Activity-Worksheet-Collection-10534022", "price": "$12.00"},
        {"name": "Thanksgiving Word Search Vol.10", "url": "https://www.teacherspayteachers.com/Product/Thanksgiving-Word-Search-Adventure-Fun-Activity-Worksheet-Collection-Vol10-10522501", "price": "$2.00"},
        {"name": "Thanksgiving Word Search Vol.5", "url": "https://www.teacherspayteachers.com/Product/Thanksgiving-Word-Search-Adventure-Fun-Activity-Worksheet-Collection-Vol5-10520863", "price": "$2.00"},
    ],
    "coloring": [
        {"name": "Thanksgiving Coloring Turkey Vol.6", "url": "https://www.teacherspayteachers.com/Product/Happy-Thanksgiving-Coloring-Page-Coloring-Pages-Thanksgiving-Turkey-Vol6-10540764", "price": "$1.00"},
        {"name": "Thanksgiving Coloring Turkey Vol.5", "url": "https://www.teacherspayteachers.com/Product/Happy-Thanksgiving-Coloring-Page-Coloring-Pages-Thanksgiving-Turkey-Vol5-10540763", "price": "$1.00"},
    ],
    "free": [
        {"name": "Spot the Difference Animals Vol.D2 FREE", "url": "https://www.teacherspayteachers.com/Product/Spot-the-Difference-Picture-Puzzle-Visual-Perception-Activity-Animals-VolD2-10435775", "price": "FREE"},
        {"name": "Spot the Difference Buildings Vol.D2 FREE", "url": "https://www.teacherspayteachers.com/Product/Spot-the-Difference-Picture-Puzzle-Visual-Perception-Buildings-VolD2-10464345", "price": "FREE"},
    ]
}

FREEBIES_CATEGORIES = {
    "logic": ["Shikaku", "Hitori"],
    "math": ["Kids Math Equations", "Range Puzzle"],
    "word": ["Spot Correct Spelling", "Cryptogram"],
    "creative": ["Spot the Difference", "Cookbook for Kids", "Coloring Page", "Stickers Pack"]
}

INTERNAL_LINKS = {
    "freebies": f"{SITE_BASE_URL}/freebies.html",
    "products": f"{SITE_BASE_URL}/products.html",
    "blog": f"{SITE_BASE_URL}/blog.html",
    "about": f"{SITE_BASE_URL}/about.html"
}

PERSONAS = [
    {
        "id": "Sarah_Teacher",
        "role": "Elementary School Teacher (15 years experience)",
        "expertise": "Classroom management, differentiated instruction",
        "tone": "Warm, professional, evidence-based",
        "img_style": "bright classroom, educational setting, 3D Pixar style"
    },
    {
        "id": "Emma_Mom",
        "role": "Montessori Mom & Parenting Blogger",
        "expertise": "Child-led learning, hands-on activities",
        "tone": "Friendly, encouraging, practical",
        "img_style": "cozy home learning space, warm colors, 3D illustration"
    },
    {
        "id": "Dr_James",
        "role": "Child Development Psychologist (PhD)",
        "expertise": "Cognitive development, learning psychology",
        "tone": "Authoritative, research-based, accessible",
        "img_style": "modern office, professional setting, clean 3D"
    }
]

PRODUCTS = [
    {"name": "Logic Puzzles for Kids", "category": "Critical Thinking", "keywords": "logic puzzles, brain teasers, problem solving"},
    {"name": "Sudoku Worksheets", "category": "Math Skills", "keywords": "sudoku for kids, number puzzles, math games"},
    {"name": "Maze Activities", "category": "Problem Solving", "keywords": "printable mazes, spatial reasoning, fun activities"},
    {"name": "Math Worksheets", "category": "Mathematics", "keywords": "math practice, arithmetic, learning numbers"},
    {"name": "Word Search Puzzles", "category": "Language Arts", "keywords": "word search, vocabulary, spelling practice"},
    {"name": "Spot the Difference", "category": "Visual Skills", "keywords": "spot difference, visual perception, attention"}
]

def get_persona() -> dict:
    return random.choice(PERSONAS)

def get_random_product() -> dict:
    return random.choice(PRODUCTS)


# ===================================================================
# LOGGER ULTRA-DETAILLE (identique V3.1)
# ===================================================================

class DetailedLogger:
    def __init__(self, article_slug: str):
        os.makedirs(LOGS_DIR, exist_ok=True)
        self.slug = article_slug
        self.log_file = os.path.join(LOGS_DIR, f"{article_slug}_{int(time.time())}.json")
        self.logs = {
            "slug": article_slug,
            "start_time": datetime.now().isoformat(),
            "steps": [],
            "verifications": [],
            "corrections": [],
            "errors": [],
            "metrics": {},
            "api_calls": [],
            "prompts": [],
            "quality_scores": {},
            "images_generated": [],
            "api_config": {
                "text_provider":  "DeepSeek",
                "text_model":     DEEPSEEK_TEXT_MODEL,
                "text_endpoint":  DEEPSEEK_TEXT_URL,
                "image_provider": "Pollinations",
                "image_model":    POLLINATIONS_MODEL,
                "image_keys":     f"{len(POLLINATIONS_KEYS)}/5 cles actives"
            }
        }
        self.step_timers = {}
        self.current_step = None

    def banner(self, text: str, char: str = "="):
        print(f"\n{char*80}")
        print(f"  {text}")
        print(f"{char*80}")

    def step_start(self, step: str, description: str = ""):
        self.current_step = step
        self.step_timers[step] = time.time()
        self.banner(f"ETAPE: {step}", "-")
        if description:
            print(f"   {description}")
        print()

    def step_end(self, step: str, status: str = "success"):
        if step in self.step_timers:
            elapsed = time.time() - self.step_timers[step]
            icon = "[OK]" if status == "success" else "[ERREUR]" if status == "error" else "[WARN]"
            print(f"\n   {icon} {step} termine en {elapsed:.2f}s")
            print("   " + "-" * 76)

            self.logs["steps"].append({
                "timestamp": datetime.now().isoformat(),
                "step": step,
                "status": status,
                "duration_seconds": round(elapsed, 2)
            })

    def log(self, level: str, message: str, indent: int = 1):
        icons = {
            "info": "[INFO]",
            "success": "[OK]",
            "warning": "[WARN]",
            "error": "[ERR]",
            "debug": "[DEBUG]",
            "api": "[API]",
            "check": "[CHECK]",
            "fix": "[FIX]",
            "quality": "[QUALITY]"
        }
        icon = icons.get(level, "  ")
        prefix = "   " * indent
        print(f"{prefix}{icon} {message}")

    def info(self, msg: str, indent: int = 1): self.log("info", msg, indent)
    def success(self, msg: str, indent: int = 1): self.log("success", msg, indent)
    def warning(self, msg: str, indent: int = 1): self.log("warning", msg, indent)
    def error(self, msg: str, indent: int = 1): self.log("error", msg, indent)
    def debug(self, msg: str, indent: int = 1): self.log("debug", msg, indent)
    def check(self, msg: str, indent: int = 1): self.log("check", msg, indent)
    def fix(self, msg: str, indent: int = 1): self.log("fix", msg, indent)
    def quality(self, msg: str, indent: int = 1): self.log("quality", msg, indent)

    def show_prompt(self, prompt_type: str, prompt: str, max_length: int = 400):
        print(f"\n   [PROMPT] {prompt_type}")
        print("   " + "+" + "-" * 74 + "+")

        lines = prompt[:max_length].split("\n")
        for line in lines[:10]:
            truncated = line[:71] + "..." if len(line) > 71 else line
            print(f"   | {truncated:<71} |")

        if len(prompt) > max_length:
            remaining = len(prompt) - max_length
            print(f"   | ... [{remaining} caracteres supplementaires]")

        print("   " + "+" + "-" * 74 + "+")

        self.logs["prompts"].append({
            "type": prompt_type,
            "prompt": prompt,
            "timestamp": datetime.now().isoformat()
        })

    def show_response(self, response: str, max_length: int = 300):
        print(f"\n   [REPONSE] ({len(response)} caracteres)")
        print("   " + "+" + "-" * 74 + "+")

        preview = response[:max_length].replace("\n", " ")
        words = preview.split()
        line = ""
        for word in words:
            if len(line) + len(word) + 1 <= 71:
                line += word + " "
            else:
                print(f"   | {line:<71} |")
                line = word + " "
        if line:
            print(f"   | {line:<71} |")

        if len(response) > max_length:
            print(f"   | ... [reste: {len(response) - max_length} caracteres]")

        print("   " + "+" + "-" * 74 + "+")

    def api_call(self, model: str, account: str, success: bool, length: int = 0):
        icon = "[OK]" if success else "[FAIL]"
        status = "SUCCES" if success else "ECHEC"
        length_info = f" ({length} chars)" if success else ""
        print(f"   [API] {model} ({account}) -> {icon} {status}{length_info}")

        self.logs["api_calls"].append({
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "account": account,
            "success": success,
            "response_length": length
        })

    def progress(self, current: int, total: int, label: str = ""):
        percentage = (current / total) * 100
        filled = int(percentage / 5)
        bar = "#" * filled + "." * (20 - filled)
        print(f"   [{bar}] {percentage:.0f}% {label} ({current}/{total})", end="\r")
        if current == total:
            print()

    def metric(self, key: str, value, indent: int = 1):
        prefix = "   " * indent
        print(f"{prefix}[METRIC] {key}: {value}")
        self.logs["metrics"][key] = value

    def verification_result(self, check_name: str, passed: bool, details: str = ""):
        icon = "[PASS]" if passed else "[FAIL]"
        print(f"   {icon} {check_name}")
        if details:
            print(f"      -> {details}")

        self.logs["verifications"].append({
            "timestamp": datetime.now().isoformat(),
            "check": check_name,
            "passed": passed,
            "details": details
        })

    def correction_applied(self, issue: str, fix: str):
        print(f"   [FIX] CORRECTION: {issue}")
        print(f"      -> {fix}")

        self.logs["corrections"].append({
            "timestamp": datetime.now().isoformat(),
            "issue": issue,
            "fix": fix
        })

    def quality_score(self, category: str, score: int, max_score: int):
        percentage = (score / max_score) * 100
        icon = "[EXCELLENT]" if percentage >= 80 else "[OK]" if percentage >= 60 else "[FAIBLE]"
        print(f"   {icon} {category}: {score}/{max_score} ({percentage:.0f}%)")

        self.logs["quality_scores"][category] = {
            "score": score,
            "max": max_score,
            "percentage": round(percentage, 1)
        }

    def image_saved(self, filename: str, size_kb: int):
        self.logs["images_generated"].append({
            "filename": filename,
            "size_kb": size_kb,
            "timestamp": datetime.now().isoformat()
        })

    def save(self):
        self.logs["end_time"] = datetime.now().isoformat()
        duration = (datetime.fromisoformat(self.logs["end_time"]) - 
                   datetime.fromisoformat(self.logs["start_time"])).total_seconds()
        self.logs["total_duration_seconds"] = round(duration, 2)

        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, indent=2, ensure_ascii=False)

        print(f"\n[SAVE] Logs detailles sauvegardes: {self.log_file}")


# [PARTIE 2 SUIT...]

# ===================================================================
# GENERATION TEXTE AVEC CONFIGURATION SPECIALISEE V3.2
# ===================================================================

def generate_text_specialized(prompt: str, logger: DetailedLogger, prompt_type: str,
                              role: str = "content", max_retries: int = MAX_RETRIES) -> Optional[str]:
    """
    Generation texte avec cles API specialisees selon le role

    Roles:
    - "plan": Utilise API_KEY_PLAN uniquement (Chef d'orchestre)
    - "content": Utilise CONTENT_KEYS en rotation (Redacteurs pro)
    - "dir_art": Utilise API_KEY_DIR_ART (Directeur artistique)
    - "seo": Utilise API_KEY_SEO (Corrections SEO)
    """
    # [V3.4] DeepSeek-V3.2 Thinking Mode pour tous les roles
    role_labels = {
        "plan":    "Chef Orchestre",
        "content": "Redacteur Pro",
        "dir_art": "Directeur Artistique",
        "seo":     "SEO Corrector"
    }
    account_label = role_labels.get(role, "Generic")

    if not DEEPSEEK_API_KEY:
        logger.error("Aucune cle DEEPSEEK_API_KEY configuree dans .env", 2)
        return None

    logger.info(f"Generation: {prompt_type} (Role: {role}) via {DEEPSEEK_TEXT_MODEL}", 2)
    logger.show_prompt(prompt_type, prompt)

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type":  "application/json"
    }
    payload = {
        "model":    DEEPSEEK_TEXT_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }

    for attempt in range(max_retries):
        if attempt > 0:
            wait_time = 2 ** attempt
            logger.warning(f"Retry #{attempt} dans {wait_time}s...", 2)
            for i in range(wait_time):
                time.sleep(1)
                logger.progress(i + 1, wait_time, "Attente")

        try:
            logger.debug(f"Appel DeepSeek ({account_label}) — {DEEPSEEK_TEXT_MODEL}", 3)
            start_time = time.time()
            resp = requests.post(DEEPSEEK_TEXT_URL, headers=headers,
                                 json=payload, timeout=180)
            elapsed = time.time() - start_time

            if resp.status_code == 200:
                data = resp.json()
                # DeepSeek Thinking: reasoning_content (ignore) + content (utilise)
                msg  = data["choices"][0]["message"]
                text = msg.get("content") or msg.get("reasoning_content", "")
                if text and len(text) > 100:
                    logger.api_call(DEEPSEEK_TEXT_MODEL, account_label, True, len(text))
                    logger.success(f"Succes en {elapsed:.2f}s ({len(text)} chars)", 3)
                    logger.show_response(text)
                    return text
                else:
                    logger.api_call(DEEPSEEK_TEXT_MODEL, account_label, False)
                    logger.warning("Reponse vide ou trop courte", 4)

            elif resp.status_code == 429:
                logger.api_call(DEEPSEEK_TEXT_MODEL, account_label, False)
                logger.warning(f"Rate limit (429) — retry dans {2**attempt}s", 3)

            elif resp.status_code == 402:
                logger.api_call(DEEPSEEK_TEXT_MODEL, account_label, False)
                logger.error("Solde DeepSeek insuffisant (402) — verifier le compte", 3)
                return None

            else:
                logger.api_call(DEEPSEEK_TEXT_MODEL, account_label, False)
                logger.warning(f"HTTP {resp.status_code}", 3)

        except requests.exceptions.Timeout:
            logger.api_call(DEEPSEEK_TEXT_MODEL, account_label, False)
            logger.warning(f"Timeout 180s (attempt {attempt+1}/{max_retries})", 3)
        except Exception as e:
            logger.api_call(DEEPSEEK_TEXT_MODEL, account_label, False)
            logger.error(f"Erreur: {str(e)[:80]}", 3)

    logger.error(f"Echec apres {max_retries} tentatives", 2)
    return None


# Fonctions simplifiees par role
def generate_plan(prompt: str, logger: DetailedLogger) -> Optional[str]:
    """Generation du plan SEO avec cle dediee chef d'orchestre"""
    return generate_text_specialized(prompt, logger, "PLAN SEO", role="plan")

def generate_content(prompt: str, logger: DetailedLogger) -> Optional[str]:
    """Generation du contenu avec redacteurs pro en rotation"""
    return generate_text_specialized(prompt, logger, "CONTENU ARTICLE", role="content")

def optimize_image_prompt_dir_art(basic_prompt: str, context: str, logger: DetailedLogger) -> str:
    """Optimisation prompt image par directeur artistique dedie"""
    logger.info("Optimisation prompt avec Directeur Artistique dedie", 3)

    optimization_prompt = f"""You are an expert Art Director and Visual Designer with 20 years experience in educational content imagery.

Your task: Enhance this basic image concept into a detailed, professional prompt for AI image generation using Flux Klein-Large model.

BASIC CONCEPT: {basic_prompt}
CONTEXT: {context}
TARGET AUDIENCE: Parents and teachers of children aged 4-12
STYLE REQUIRED: 3D illustration, Pixar-like, warm colors, educational, friendly
MODEL: Flux Klein-Large (9B parameters, ultra-detailed output)

OUTPUT FORMAT (return ONLY the enhanced prompt, nothing else):
Enhanced prompt should be 1-2 sentences, include:
- Specific composition details (foreground, midground, background)
- Lighting description (warm, soft, natural)
- Color palette (specific colors, not just "bright")
- Emotional tone (inviting, encouraging, playful)
- Technical details optimized for Flux Klein-Large (depth of field, 3D render quality, ultra-detailed 8K)

Example:
Input: "Children solving puzzles in classroom"
Output: "Wide-angle shot of a bright, modern classroom with warm afternoon sunlight streaming through large windows, featuring 4 diverse children (ages 6-8) seated at a rounded wooden table covered with colorful jigsaw puzzles, markers, and educational worksheets, soft bokeh background showing cheerful wall decorations, 3D Pixar-style rendering with vibrant teal and orange color palette, depth of field focusing on excited child faces, professional studio lighting optimized for Flux Klein-Large, ultra-detailed 8K quality with sharp textures and realistic materials"

Now enhance this prompt for Flux Klein-Large:
{basic_prompt}"""

    enhanced = generate_text_specialized(
        optimization_prompt,
        logger,
        "OPTIMIZATION PROMPT (Directeur Artistique)",
        role="dir_art"
    )

    if enhanced and len(enhanced) > 50:
        enhanced_clean = enhanced.strip().strip('"').strip("'")
        logger.success(f"Prompt optimise: {len(enhanced_clean)} chars", 4)
        logger.debug(f"Prompt: {enhanced_clean[:100]}...", 4)
        return enhanced_clean
    else:
        logger.warning("Optimisation echouee, utilisation prompt basique", 4)
        return f"{basic_prompt}, {context}, 3D Pixar style, high quality, vibrant colors, educational, Flux Klein-Large optimized"


def correct_with_seo_specialist(prompt: str, logger: DetailedLogger, correction_type: str) -> Optional[str]:
    """Corrections SEO avec specialiste dedie"""
    return generate_text_specialized(
        prompt,
        logger,
        f"CORRECTION SEO: {correction_type}",
        role="seo"
    )


# ===================================================================
# GENERATION IMAGES AVEC POLLINATIONS KLEIN-LARGE (2 CLES)
# ===================================================================

def download_image_pollinations_klein(prompt: str, seed: int, logger: DetailedLogger) -> Optional[bytes]:
    """Telecharge image depuis Pollinations avec model Klein-Large et rotation 2 cles"""

    if not POLLINATIONS_KEYS:
        logger.error("Aucune cle Pollinations configuree", 5)
        return None

    for key_idx, api_key in enumerate(POLLINATIONS_KEYS, 1):
        try:
            safe_prompt = urllib.parse.quote(prompt)

            # URL Pollinations avec model Klein-Large
            url = f"https://gen.pollinations.ai/image/{safe_prompt}"

            params = {
                "width": 1200,
                "height": 675,
                "seed": seed,
                "model": POLLINATIONS_MODEL,  # klein-large
                "nologo": "true",
                "enhance": "true"
            }

            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            logger.debug(f"Pollinations Klein-Large (Cle #{key_idx})", 5)
            logger.debug(f"Model: {POLLINATIONS_MODEL}", 6)

            resp = requests.get(url, params=params, headers=headers, timeout=90)

            if resp.status_code == 200 and len(resp.content) > 1024:
                logger.success(f"Pollinations cle #{key_idx} OK: {len(resp.content)//1024} KB", 5)
                return resp.content
            else:
                logger.warning(f"Pollinations cle #{key_idx} FAIL: {resp.status_code}", 5)

                # Si 429 (quota), essayer cle suivante
                if resp.status_code == 429 and key_idx < len(POLLINATIONS_KEYS):
                    logger.info(f"Quota depasse, basculement vers cle #{key_idx + 1}", 5)
                    continue

        except Exception as e:
            logger.error(f"Pollinations cle #{key_idx} error: {str(e)[:50]}", 5)

            # Si erreur, essayer cle suivante
            if key_idx < len(POLLINATIONS_KEYS):
                logger.info(f"Erreur, tentative avec cle #{key_idx + 1}", 5)
                continue

    logger.error("Toutes les cles Pollinations ont echoue", 5)
    return None


def generate_seo_alt_text(concept: str, context: str) -> str:
    """Genere un alt text SEO"""
    alt = f"{concept} {context}"
    alt = re.sub(r'[^a-zA-Z0-9\s-]', '', alt)
    alt = re.sub(r'\s+', '-', alt)
    return alt.lower()[:125]


def download_and_optimize_image(prompt: str, filename: str, logger: DetailedLogger, 
                                alt_context: str = "") -> Tuple[str, str]:
    """
    Telecharge et optimise une image avec:
    - Optimisation prompt par Directeur Artistique dedie
    - Retry sur 2 cles Pollinations (Klein-Large)
    - Sauvegarde confirmee dans images/
    """
    logger.info(f"Image: {filename}", 3)

    # ETAPE 1: Optimiser le prompt avec Directeur Artistique
    optimized_prompt = optimize_image_prompt_dir_art(prompt, alt_context, logger)
    clean_prompt = re.sub(r'[^a-zA-Z0-9 ,.-]', '', optimized_prompt)

    # ETAPE 2: Tentatives de telechargement avec 2 cles Pollinations
    image_data = None

    for attempt in range(IMAGE_RETRY_MAX):
        seed = random.randint(0, 999999)

        logger.debug(f"Tentative {attempt + 1}/{IMAGE_RETRY_MAX}...", 4)

        # Essayer Pollinations Klein-Large avec rotation 2 cles
        image_data = download_image_pollinations_klein(clean_prompt, seed, logger)

        # Si succes, sortir de la boucle
        if image_data:
            break

        # Sinon, attendre avant retry
        if attempt < IMAGE_RETRY_MAX - 1:
            time.sleep(2)

    # ETAPE 3: Traitement et sauvegarde
    if image_data and len(image_data) > 1024:
        try:
            img = Image.open(BytesIO(image_data))

            if img.mode in ("RGBA", "P"):
                logger.debug(f"Conversion {img.mode} -> RGB", 4)
                img = img.convert("RGB")

            # Creer le dossier si necessaire
            os.makedirs(IMAGES_DIR, exist_ok=True)

            webp_name = filename.replace(".jpg", ".webp")
            full_path = os.path.join(IMAGES_DIR, webp_name)

            img.thumbnail((1200, 1200))
            img.save(full_path, "WEBP", quality=85, optimize=True, method=6)

            file_size = os.path.getsize(full_path)
            logger.success(f"[SAVED] {full_path} ({file_size // 1024} KB)", 4)
            logger.image_saved(webp_name, file_size // 1024)

            alt_text = generate_seo_alt_text(clean_prompt[:50], alt_context)
            logger.info(f"Alt: {alt_text[:50]}...", 4)

            return f"{IMAGES_DIR}/{webp_name}", alt_text

        except Exception as e:
            logger.error(f"Erreur traitement image: {str(e)[:50]}", 4)

    # FALLBACK: Utiliser placeholder
    logger.error(f"[FAIL] Echec apres {IMAGE_RETRY_MAX} tentatives - Placeholder utilise", 4)
    return "https://placehold.co/1200x675/F48C06/FFFFFF/png?text=Smart+Genius", "educational content"


# [PARTIE 3 SUIT avec liens internes/TPT...]

# ===================================================================
# LIENS INTERNES & TPT (identique V3.1)
# ===================================================================

def get_relevant_tpt_products(category: str, keywords: str) -> List[Dict]:
    """Retourne les produits TPT pertinents selon categorie/mots-cles"""
    keywords_lower = keywords.lower()

    if "spot" in keywords_lower or "visual" in keywords_lower or "difference" in keywords_lower:
        return (TPT_PRODUCTS_FULL["spot_difference_photorealistic"][:1] + 
                TPT_PRODUCTS_FULL["spot_difference_kids"][:1])

    elif "word" in keywords_lower or "spelling" in keywords_lower or "vocabulary" in keywords_lower:
        return TPT_PRODUCTS_FULL["word_search"][:2]

    elif "color" in keywords_lower or "art" in keywords_lower:
        return TPT_PRODUCTS_FULL["coloring"][:2]

    else:
        return (TPT_PRODUCTS_FULL["spot_difference_kids"][:1] + 
                TPT_PRODUCTS_FULL["free"][:1])


def get_relevant_freebies(category: str, keywords: str) -> List[str]:
    """Retourne les freebies pertinents"""
    keywords_lower = keywords.lower()

    if "math" in keywords_lower or "number" in keywords_lower:
        return FREEBIES_CATEGORIES["math"]
    elif "word" in keywords_lower or "spelling" in keywords_lower:
        return FREEBIES_CATEGORIES["word"]
    elif "logic" in keywords_lower or "puzzle" in keywords_lower:
        return FREEBIES_CATEGORIES["logic"]
    else:
        return FREEBIES_CATEGORIES["creative"][:2]


def inject_internal_links(content: str, category: str, keywords: str, logger: DetailedLogger) -> str:
    """Injecte 4+ liens internes dans le contenu"""
    logger.info("Injection des liens internes", 3)

    # 1. Lien vers freebies
    freebies = get_relevant_freebies(category, keywords)
    freebie_text = f'<a href="{INTERNAL_LINKS["freebies"]}" target="_blank">free downloadable {freebies[0]}</a>'

    patterns_freebies = [
        (r'\bfree\s+worksheets?\b', freebie_text),
        (r'\bfree\s+printables?\b', freebie_text),
        (r'\bfree\s+resources?\b', freebie_text)
    ]

    for pattern, replacement in patterns_freebies:
        if re.search(pattern, content, re.IGNORECASE):
            content = re.sub(pattern, replacement, content, count=1, flags=re.IGNORECASE)
            logger.debug(f"Lien freebies injecte: {freebies[0]}", 4)
            break

    # 2. Lien vers products
    products_text = f'<a href="{INTERNAL_LINKS["products"]}" target="_blank">our premium worksheets collection</a>'

    patterns_products = [
        (r'\bpremium\s+worksheets?\b', products_text),
        (r'\bquality\s+worksheets?\b', products_text),
        (r'\bprofessional\s+worksheets?\b', products_text)
    ]

    for pattern, replacement in patterns_products:
        if re.search(pattern, content, re.IGNORECASE):
            content = re.sub(pattern, replacement, content, count=1, flags=re.IGNORECASE)
            logger.debug("Lien products injecte", 4)
            break

    # 3. Lien vers blog
    blog_text = f'<a href="{INTERNAL_LINKS["blog"]}">our blog</a>'
    content = re.sub(r'\bblog\b', blog_text, content, count=1, flags=re.IGNORECASE)
    logger.debug("Lien blog injecte", 4)

    # 4. Ajouter CTA avec liens TPT
    tpt_products = get_relevant_tpt_products(category, keywords)

    cta_html = f"""
<div class="cta-box" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 15px; margin: 30px 0; text-align: center;">
    <h3 style="color: white; margin-bottom: 15px;">Ready to Enhance Your Teaching?</h3>
    <p style="color: white; margin-bottom: 20px;">Explore our premium educational resources:</p>
    <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
        <a href="{tpt_products[0]['url']}" target="_blank" rel="noopener" style="background: white; color: #667eea; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold;">{tpt_products[0]['name']}</a>
        <a href="{INTERNAL_LINKS['freebies']}" style="background: #F48C06; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold;">Get Free Resources</a>
    </div>
</div>"""

    if '<div class="faq-section' in content:
        content = content.replace('<div class="faq-section', cta_html + '<div class="faq-section')
        logger.debug("CTA avec liens TPT ajoute avant FAQ", 4)
    else:
        content += cta_html
        logger.debug("CTA avec liens TPT ajoute en fin", 4)

    logger.success("4+ liens internes/externes injectes", 3)
    return content


# ===================================================================
# CORRECTION SEO AVEC SPECIALISTE DEDIE
# ===================================================================

class SEOCorrector:
    """Correction SEO automatique avec specialiste dedie"""

    @staticmethod
    def correct_title(title: str, target_length: int, logger: DetailedLogger) -> str:
        """Corrige le titre pour SEO optimal"""
        if 30 <= len(title) <= 60:
            return title

        logger.fix("Titre hors limites SEO, correction avec specialiste...", 3)

        prompt = f"""Fix this blog title to be exactly between 30-60 characters while keeping the main message.

Current title ({len(title)} chars): "{title}"

Rules:
- Must be between 30-60 characters
- Keep the main keyword
- Be compelling and clickable
- Natural, not truncated

Return ONLY the new title, nothing else."""

        corrected = correct_with_seo_specialist(prompt, logger, "TITRE")

        if corrected:
            corrected = corrected.strip().strip('"')
            if 30 <= len(corrected) <= 60:
                logger.success(f"Titre corrige: {len(corrected)} chars", 4)
                logger.correction_applied("Titre trop long/court", f"{title} -> {corrected}")
                return corrected

        # Fallback
        if len(title) > 60:
            corrected = title[:57] + "..."
        else:
            corrected = title + " - Ultimate Guide"

        logger.warning(f"Fallback: {corrected}", 4)
        return corrected

    @staticmethod
    def correct_meta_description(desc: str, content: str, logger: DetailedLogger) -> str:
        """Corrige la meta description"""
        if 120 <= len(desc) <= 155:
            return desc

        logger.fix("Meta description hors limites, correction avec specialiste...", 3)

        first_p = re.search(r'<p>([^<]+)</p>', content)
        context = first_p.group(1)[:200] if first_p else content[:200]

        prompt = f"""Create a compelling meta description exactly between 120-155 characters.

Context: {context}

Rules:
- Exactly 120-155 characters
- Include main benefit/hook
- Natural, engaging tone
- Include call-to-action

Return ONLY the meta description, nothing else."""

        corrected = correct_with_seo_specialist(prompt, logger, "META DESCRIPTION")

        if corrected:
            corrected = corrected.strip().strip('"')
            if 120 <= len(corrected) <= 155:
                logger.success(f"Meta description corrigee: {len(corrected)} chars", 4)
                logger.correction_applied("Meta description invalide", f"Nouvelle: {corrected[:50]}...")
                return corrected

        # Fallback
        if len(desc) > 155:
            corrected = desc[:152] + "..."
        else:
            corrected = desc + " Learn more about effective learning strategies."

        logger.warning("Fallback utilise", 4)
        return corrected[:155]


# ===================================================================
# VERIFICATION & CORRECTION QUALITE (identique V3.1)
# ===================================================================

class ContentVerifier:
    """Verification et correction automatique du contenu"""

    @staticmethod
    def verify_content(content: dict, logger: DetailedLogger) -> Tuple[bool, List[str]]:
        """Verifie le contenu et retourne (ok, liste_problemes)"""

        logger.step_start("ETAPE 6/10: VERIFICATION QUALITE", 
                         "Analyse approfondie du contenu genere")

        issues = []

        # 1. Verification longueur
        logger.check("Verification longueur du contenu", 2)
        word_count = len(re.findall(r'\w+', re.sub(r'<[^>]+>', '', content.get('content', ''))))
        if word_count < MIN_WORD_COUNT:
            issue = f"Contenu trop court: {word_count} mots (min: {MIN_WORD_COUNT})"
            issues.append(issue)
            logger.verification_result("Longueur", False, issue)
        else:
            logger.verification_result("Longueur", True, f"{word_count} mots")

        # 2. Verification structure H2/H3
        logger.check("Verification structure titres", 2)
        html_content = content.get('content', '')
        h2_count = len(re.findall(r'<h2>', html_content))
        h3_count = len(re.findall(r'<h3>', html_content))

        if h2_count < 3:
            issue = f"Pas assez de H2: {h2_count} (min: 3)"
            issues.append(issue)
            logger.verification_result("Structure H2", False, issue)
        else:
            logger.verification_result("Structure H2", True, f"{h2_count} sections")

        if h3_count < 2:
            issue = f"Pas assez de H3: {h3_count} (min: 2)"
            issues.append(issue)
            logger.verification_result("Structure H3", False, issue)
        else:
            logger.verification_result("Structure H3", True, f"{h3_count} sous-sections")

        # 3. Verification images
        logger.check("Verification images", 2)
        img_count = len(re.findall(r'<img', html_content))
        if img_count < NUM_CONTENT_IMAGES:
            issue = f"Images manquantes: {img_count}/{NUM_CONTENT_IMAGES}"
            issues.append(issue)
            logger.verification_result("Images", False, issue)
        else:
            logger.verification_result("Images", True, f"{img_count} images")

        # 4. Verification alt text
        logger.check("Verification alt text", 2)
        alt_count = len(re.findall(r'alt="[^"]+"', html_content))
        if alt_count < img_count:
            issue = f"Alt text incomplets: {alt_count}/{img_count}"
            issues.append(issue)
            logger.verification_result("Alt text", False, issue)
        else:
            logger.verification_result("Alt text", True, f"{alt_count} alt text")

        logger.step_end("ETAPE 6/10: VERIFICATION QUALITE", "success" if not issues else "warning")

        return len(issues) == 0, issues


# ===================================================================
# OPTIMISATION SEO (identique V3.1)
# ===================================================================

class SEOOptimizer:
    """Optimisation SEO avancee"""

    @staticmethod
    def calculate_reading_time(content: str) -> int:
        words = len(re.findall(r'\w+', re.sub(r'<[^>]+>', '', content)))
        return max(1, round(words / 200))

    @staticmethod
    def extract_keywords(title: str, content: str) -> List[str]:
        text = re.sub(r'<[^>]+>', '', content).lower()
        words = re.findall(r'\b[a-z]{4,}\b', text)
        stopwords = {'that', 'this', 'with', 'from', 'have', 'will', 'your', 
                     'more', 'they', 'were', 'been', 'their', 'which', 'when'}
        word_freq = {}
        for word in words:
            if word not in stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:5]]

    @staticmethod
    def generate_meta_description(content: str, max_length: int = 155) -> str:
        text = re.sub(r'<[^>]+>', '', content)
        sentences = re.split(r'[.!?]', text)
        description = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if len(description) + len(sentence) < max_length - 3:
                description += sentence + ". "
            else:
                break
        return description.strip()[:max_length] + "..."

    @staticmethod
    def optimize_slug(title: str) -> str:
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')[:60]

    @staticmethod
    def calculate_seo_score(article_data: dict, logger: DetailedLogger) -> Tuple[int, List[str]]:
        """Calcule le score SEO"""
        logger.check("Calcul du score SEO", 2)

        score = 0
        suggestions = []

        title = article_data.get('title', '')
        content = article_data.get('content', '')
        meta_desc = article_data.get('meta_description', '')

        # Titre
        if 30 <= len(title) <= 60:
            score += 15
            logger.verification_result("Titre SEO", True, f"{len(title)} chars")
        else:
            suggestions.append(f"Titre: {len(title)} chars (optimal: 30-60)")
            logger.verification_result("Titre SEO", False, f"{len(title)} chars")

        # Meta description
        if 120 <= len(meta_desc) <= 155:
            score += 15
            logger.verification_result("Meta description", True, f"{len(meta_desc)} chars")
        else:
            suggestions.append(f"Meta desc: {len(meta_desc)} chars (optimal: 120-155)")
            logger.verification_result("Meta description", False, f"{len(meta_desc)} chars")

        # Word count
        word_count = len(re.findall(r'\w+', re.sub(r'<[^>]+>', '', content)))
        if word_count >= TARGET_WORD_COUNT:
            score += 20
            logger.verification_result("Longueur article", True, f"{word_count} mots")
        elif word_count >= MIN_WORD_COUNT:
            score += 10
            logger.verification_result("Longueur article", True, f"{word_count} mots (acceptable)")
        else:
            suggestions.append(f"Contenu: {word_count} mots (min: {MIN_WORD_COUNT})")
            logger.verification_result("Longueur article", False, f"{word_count} mots")

        # Structure
        h2_count = len(re.findall(r'<h2>', content))
        h3_count = len(re.findall(r'<h3>', content))
        if h2_count >= 3 and h3_count >= 2:
            score += 15
            logger.verification_result("Structure H2/H3", True, f"{h2_count} H2, {h3_count} H3")
        else:
            suggestions.append(f"Structure: {h2_count} H2, {h3_count} H3 (min: 3 H2, 2 H3)")
            logger.verification_result("Structure H2/H3", False, f"{h2_count} H2, {h3_count} H3")

        # Images
        img_count = len(re.findall(r'<img', content))
        if img_count >= NUM_CONTENT_IMAGES:
            score += 15
            logger.verification_result("Images", True, f"{img_count} images")
        else:
            suggestions.append(f"Images: {img_count} (min: {NUM_CONTENT_IMAGES})")
            logger.verification_result("Images", False, f"{img_count} images")

        # Alt text
        alt_count = len(re.findall(r'alt="[^"]+"', content))
        if alt_count == img_count and img_count > 0:
            score += 10
            logger.verification_result("Alt text", True, f"{alt_count}/{img_count}")
        else:
            suggestions.append(f"Alt text: {alt_count}/{img_count}")
            logger.verification_result("Alt text", False, f"{alt_count}/{img_count}")

        # Liens internes
        internal_links = len(re.findall(r'href="[^"]*(?:freebies|products|blog)', content))
        if internal_links >= 2:
            score += 10
            logger.verification_result("Liens internes", True, f"{internal_links} liens")
        else:
            suggestions.append(f"Liens internes: {internal_links} (min: 2)")
            logger.verification_result("Liens internes", False, f"{internal_links} liens")

        logger.quality_score("Score SEO", score, 100)

        return score, suggestions


# [PARTIE 4 SUIT avec moteur principal...]

# ===================================================================
# MOTEUR PRINCIPAL V3.2 - CONFIGURATION API SPECIALISEE
# ===================================================================

def generate_ultimate_article():
    """Generation avec configuration API specialisee V3.2"""

    global session_api_config
    session_api_config = {"key": None, "model": None}

    # Initialisation
    product = get_random_product()
    persona = get_persona()

    temp_slug = SEOOptimizer.optimize_slug(f"{product['name']}-{int(time.time())}")
    logger = DetailedLogger(temp_slug)

    logger.banner("AUTO BLOG ULTIMATE V3.2 - CONFIGURATION API SPECIALISEE", "=")
    print(f"Sujet: {product['name']}")
    print(f"Persona: {persona['role']}")
    print(f"Categorie: {product['category']}")
    print(f"Mots-cles: {product['keywords']}")
    print(f"Slug: {temp_slug}")
    print(f"Demarrage: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Images: {TOTAL_IMAGES} ({NUM_CONTENT_IMAGES} dans contenu + 1 cover)")
    print(f"\nConfiguration API V3.2:")
    print(f"   Plan: GOOGLE_API_KEY_1 (Chef Orchestre)")
    print(f"   Contenu: GOOGLE_API_KEY_2 + KEY_3 (Redacteurs Pro x{len(CONTENT_KEYS)})")
    print(f"   Dir. Artistique: GOOGLE_API_KEY_Dir_Art")
    print(f"   Images: Pollinations Klein-Large (x{len(POLLINATIONS_KEYS)} cles)")
    print(f"   SEO: GOOGLE_API_KEY_SEO (Specialiste)")

    # ETAPE 1: PLAN avec Chef d'Orchestre
    logger.step_start("ETAPE 1/10: CREATION DU PLAN SEO",
                     "Generation avec Chef Orchestre (GOOGLE_API_KEY_1)")

    plan_prompt = f"""You are {persona['role']}.
Expertise: {persona['expertise']}
Tone: {persona['tone']}

Create a comprehensive SEO article plan for "Little Smart Genius" blog.

Topic: {product['name']}
Category: {product['category']}
Keywords: {product['keywords']}
Target: Parents of children aged 4-12

OUTPUT FORMAT (JSON):
{{
  "title": "SEO-optimized title (30-60 chars, include main keyword)",
  "meta_description": "Compelling description (120-155 chars)",
  "primary_keyword": "Main keyword",
  "cover_concept": "Detailed visual concept for hero image optimized for Flux Klein-Large",
  "sections": [
    {{
      "h2": "Section title",
      "h3_subsections": ["Subsection 1", "Subsection 2"],
      "key_points": ["Point 1", "Point 2", "Point 3"],
      "image_concept": "Visual concept for this section, detailed for Flux Klein-Large"
    }}
  ],
  "faq": [
    {{"q": "Question?", "a": "Detailed answer (2-3 sentences)"}}
  ]
}}

Requirements:
- 4-5 main sections (H2)
- 2-3 subsections (H3) per H2
- 3 image concepts (detailed, optimized for Flux Klein-Large model)
- 3-5 FAQ questions
- Natural, human-friendly tone
- Practical, actionable advice"""

    raw_plan = generate_plan(plan_prompt, logger)
    if not raw_plan:
        logger.error("Echec critique: plan", 2)
        logger.save()
        return None

    try:
        clean_json = re.sub(r'```json|```', '', raw_plan).strip()
        plan = json.loads(clean_json[clean_json.find("{"):clean_json.rfind("}")+1])

        logger.success("Plan parse avec succes", 2)
        logger.metric("Sections", len(plan.get('sections', [])), 2)
        logger.metric("FAQ", len(plan.get('faq', [])), 2)
        logger.metric("Images prevues", len([s for s in plan.get('sections', []) if 'image_concept' in s]), 2)

    except Exception as e:
        logger.error(f"Parsing JSON: {str(e)}", 2)
        logger.save()
        return None

    logger.step_end("ETAPE 1/10: CREATION DU PLAN SEO")

    # ETAPE 2: CONTENU avec Redacteurs Pro
    logger.step_start("ETAPE 2/10: REDACTION DU CONTENU",
                     f"Generation avec Redacteurs Pro ({len(CONTENT_KEYS)} cles en rotation)")

    content_prompt = f"""You are {persona['role']}.
Write as a real human with personality, NOT as AI.

Topic: {plan['title']}
Primary Keyword: {plan.get('primary_keyword', product['keywords'])}
Target: {TARGET_WORD_COUNT} words MINIMUM

WRITING STYLE (IMPORTANT):
- Write naturally with varied sentence lengths
- Use conversational tone with personality
- Include personal insights and examples
- Ask rhetorical questions to engage readers
- Use transitions like "Here's the thing", "In my experience", "You know what?"
- Avoid AI phrases like "It's important to note", "Moreover", "Furthermore"
- Write short paragraphs (2-4 sentences max)
- Use active voice

STRUCTURE:
1. Introduction (150 words):
   - Personal hook or story
   - Problem identification
   - Promise of solution

2. Main Content (follow the plan sections):
{json.dumps([{"h2": s.get("h2"), "h3": s.get("h3_subsections", []), "points": s.get("key_points", [])} for s in plan.get('sections', [])], indent=2)}

3. Conclusion (100 words):
   - Summary with personal touch
   - Call-to-action

4. FAQ Section:
{json.dumps(plan.get('faq', []), indent=2)}

FORMAT:
- Use HTML: <h2>, <h3>, <p>, <ul>, <li>, <strong>
- Insert [IMAGE_1], [IMAGE_2], [IMAGE_3] in relevant sections
- NO <html>, <head>, or <body> tags
- Use <strong> for keywords (sparingly)
- Naturally mention "free worksheets" and "premium resources" for internal linking

HUMAN TOUCH:
- Share personal anecdotes
- Use "I", "you", "we"
- Include actionable tips
- Be warm and encouraging"""

    html_content = generate_content(content_prompt, logger)
    if not html_content:
        logger.error("Echec critique: contenu", 2)
        logger.save()
        return None

    html_content = re.sub(r'```html|```', '', html_content).strip()

    word_count = len(re.findall(r'\w+', re.sub(r'<[^>]+>', '', html_content)))
    h2_count = len(re.findall(r'<h2>', html_content))
    h3_count = len(re.findall(r'<h3>', html_content))

    logger.metric("Mots generes", word_count, 2)
    logger.metric("Sections H2", h2_count, 2)
    logger.metric("Sous-sections H3", h3_count, 2)

    if word_count >= TARGET_WORD_COUNT:
        logger.success(f"Objectif atteint: {word_count}/{TARGET_WORD_COUNT} mots", 2)
    else:
        logger.warning(f"Sous l'objectif: {word_count}/{TARGET_WORD_COUNT} mots", 2)

    logger.step_end("ETAPE 2/10: REDACTION DU CONTENU")

    # ETAPE 3: VISUELS avec Directeur Artistique + Pollinations Klein-Large
    logger.step_start("ETAPE 3/10: GENERATION DES VISUELS KLEIN-LARGE",
                     f"Dir. Artistique + Pollinations Klein-Large ({len(POLLINATIONS_KEYS)} cles)")

    slug = SEOOptimizer.optimize_slug(plan['title'])
    ts = int(time.time())
    logger.info(f"Slug final: {slug}", 2)

    # Image de couverture
    logger.info(f"Image 1/{TOTAL_IMAGES}: COUVERTURE", 2)
    cover_prompt = plan['cover_concept']
    cover_path, cover_alt = download_and_optimize_image(
        cover_prompt,
        f"{slug}-cover-{ts}.jpg",
        logger,
        plan['title']
    )
    logger.progress(1, TOTAL_IMAGES, "Images generees")

    # Images de contenu (3)
    section_images = []
    for i, section in enumerate(plan.get('sections', [])[:NUM_CONTENT_IMAGES], 1):
        logger.info(f"Image {i+1}/{TOTAL_IMAGES}: {section.get('h2', '')[:40]}...", 2)
        img_concept = section.get('image_concept', plan['cover_concept'])
        img_path, img_alt = download_and_optimize_image(
            img_concept,
            f"{slug}-img{i}-{ts}.jpg",
            logger,
            section.get('h2', '')
        )
        section_images.append((img_path, img_alt))
        logger.progress(i+1, TOTAL_IMAGES, "Images generees")

    # Injection des images
    logger.info("Injection des images dans le contenu", 2)
    for i, (img_path, img_alt) in enumerate(section_images, 1):
        img_tag = f'<figure class="article-image"><img src="../{img_path}" alt="{img_alt}" loading="lazy" width="1200" height="675"></figure>'
        html_content = html_content.replace(f"[IMAGE_{i}]", img_tag)
        logger.debug(f"Image {i} injectee: {img_path}", 3)

    html_content = re.sub(r'\[IMAGE_\d+\]', '', html_content)
    logger.success(f"Toutes les {TOTAL_IMAGES} images integrees", 2)

    logger.step_end("ETAPE 3/10: GENERATION DES VISUELS KLEIN-LARGE")

    # ETAPE 4: FAQ
    logger.step_start("ETAPE 4/10: AJOUT DE LA FAQ",
                     f"Integration de {len(plan.get('faq', []))} questions")

    faq_html = '<div class="faq-section mt-12"><h2>Frequently Asked Questions</h2>'
    for idx, faq in enumerate(plan.get('faq', []), 1):
        faq_html += f'<div class="faq-item mb-6"><h3 class="font-bold text-lg mb-2">{faq["q"]}</h3><p>{faq["a"]}</p></div>'
        logger.debug(f"FAQ {idx}: {faq['q'][:50]}...", 2)
    faq_html += '</div>'

    html_content += faq_html
    logger.success(f"FAQ ajoutee ({len(plan.get('faq', []))} questions)", 2)

    logger.step_end("ETAPE 4/10: AJOUT DE LA FAQ")

    # ETAPE 5: LIENS INTERNES & TPT
    logger.step_start("ETAPE 5/10: INJECTION LIENS INTERNES & TPT",
                     "Ajout de liens vers freebies, products et store TPT")

    html_content = inject_internal_links(html_content, product['category'], product['keywords'], logger)

    logger.step_end("ETAPE 5/10: INJECTION LIENS INTERNES & TPT")

    # ETAPE 6-10: Construire donnees finales
    meta_desc = plan.get('meta_description') or SEOOptimizer.generate_meta_description(html_content)
    keywords = SEOOptimizer.extract_keywords(plan['title'], html_content)
    reading_time = SEOOptimizer.calculate_reading_time(html_content)

    final_data = {
        "title": plan['title'],
        "slug": slug,
        "author": persona['id'],
        "author_name": persona['role'],
        "date": datetime.now().strftime("%B %d, %Y"),
        "iso_date": datetime.now().isoformat(),
        "category": product['category'],
        "image": cover_path,
        "content": html_content,
        "excerpt": meta_desc,
        "meta_description": meta_desc,
        "primary_keyword": plan.get('primary_keyword', ''),
        "keywords": keywords,
        "reading_time": reading_time,
        "word_count": word_count,
        "faq_schema": plan.get('faq', [])
    }

    # Verification qualite
    is_valid, issues = ContentVerifier.verify_content(final_data, logger)

    # Score SEO
    seo_score, seo_suggestions = SEOOptimizer.calculate_seo_score(final_data, logger)

    # Corrections SEO si necessaire avec Specialiste
    if seo_score < 85:
        logger.step_start("ETAPE 8/10: CORRECTIONS SEO AVEC SPECIALISTE",
                         f"Score actuel: {seo_score}/100 - Corrections par Specialiste SEO")

        if not (30 <= len(final_data['title']) <= 60):
            logger.fix("Correction du titre avec Specialiste SEO", 2)
            target_length = 50 if len(final_data['title']) > 60 else 40
            final_data['title'] = SEOCorrector.correct_title(final_data['title'], target_length, logger)

        if not (120 <= len(final_data['meta_description']) <= 155):
            logger.fix("Correction meta description avec Specialiste SEO", 2)
            final_data['meta_description'] = SEOCorrector.correct_meta_description(
                final_data['meta_description'],
                final_data['content'],
                logger
            )
            final_data['excerpt'] = final_data['meta_description']

        seo_score_new, seo_suggestions_new = SEOOptimizer.calculate_seo_score(final_data, logger)

        if seo_score_new > seo_score:
            logger.success(f"Score ameliore: {seo_score} -> {seo_score_new}", 2)
            seo_score = seo_score_new
            seo_suggestions = seo_suggestions_new

        logger.step_end("ETAPE 8/10: CORRECTIONS SEO AVEC SPECIALISTE", "success")
    else:
        logger.success(f"Score SEO excellent: {seo_score}/100 - Aucune correction necessaire", 2)

    # SAUVEGARDE
    logger.step_start("ETAPE 10/10: SAUVEGARDE FINALE",
                     "Ecriture du fichier JSON")

    os.makedirs(POSTS_DIR, exist_ok=True)
    output_file = f"{POSTS_DIR}/{slug}-{ts}.json"

    logger.info(f"Fichier: {output_file}", 2)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)

    file_size = os.path.getsize(output_file)
    logger.success(f"Sauvegarde ({file_size // 1024} KB)", 2)

    logger.step_end("ETAPE 10/10: SAUVEGARDE FINALE")

    logger.save()

    # RAPPORT FINAL
    logger.banner("GENERATION TERMINEE AVEC SUCCES", "=")
    print(f"Fichier: {output_file}")
    print(f"\nStatistiques finales:")
    print(f"   - Mots: {word_count}")
    print(f"   - Structure: {h2_count} H2, {h3_count} H3")
    print(f"   - Images: {TOTAL_IMAGES} (1 cover + {NUM_CONTENT_IMAGES} contenu)")
    print(f"   - FAQ: {len(plan.get('faq', []))} questions")
    print(f"   - Temps lecture: {reading_time} min")
    print(f"   - Score SEO: {seo_score}/100")
    print(f"   - Liens internes/TPT: 4+")

    print(f"\nConfiguration API V3.2:")
    print(f"   - Plan: Chef Orchestre (KEY_1)")
    print(f"   - Contenu: Redacteurs Pro x{len(CONTENT_KEYS)} (KEY_2+3)")
    print(f"   - Prompts: Directeur Artistique (KEY_Dir_Art)")
    print(f"   - Images: Pollinations Klein-Large x{len(POLLINATIONS_KEYS)} cles")
    print(f"   - SEO: Specialiste (KEY_SEO)")

    images_saved = len([img for img in logger.logs["images_generated"]])
    if images_saved > 0:
        print(f"\nImages sauvegardees ({images_saved}):")
        for img_data in logger.logs["images_generated"]:
            print(f"   - {img_data['filename']} ({img_data['size_kb']} KB)")
    else:
        print(f"\nATTENTION: Aucune image reelle sauvegardee (placeholders utilises)")

    if seo_suggestions:
        print(f"\nSuggestions SEO:")
        for suggestion in seo_suggestions:
            print(f"   - {suggestion}")

    print(f"\nTermine: {datetime.now().strftime('%H:%M:%S')}")
    print("="*80)

    return final_data


if __name__ == "__main__":
    try:
        generate_ultimate_article()
    except KeyboardInterrupt:
        print("\n\nInterruption utilisateur")
    except Exception as e:
        print(f"\n\nERREUR CRITIQUE: {str(e)}")
        import traceback
        traceback.print_exc()
