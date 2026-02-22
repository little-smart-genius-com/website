"""
AUTO BLOG V4.0 — MOTEUR DE GENERATION
Daily batch engine with 3-slot topic selection, smart linking, and Instagram post generation.
Preserves all V3.4 API config, image pipeline, SEO correction, and quality verification.
(c) 2026 Little Smart Genius

Usage:
  python auto_blog_v4.py --batch                 # Daily batch (3 articles)
  python auto_blog_v4.py --slot keyword           # Single article by slot
  python auto_blog_v4.py --slot product
  python auto_blog_v4.py --slot freebie
  python auto_blog_v4.py                          # Legacy: single random article
"""

import os
import sys
import io
import json
import random
import re
import time
import argparse
import requests
import urllib.parse
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional, Tuple

# Fix Windows terminal encoding
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass

from dotenv import load_dotenv
from PIL import Image

# Resolve project root (parent of scripts/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# V4.0 modules (same directory as this script)
from data_parsers import parse_products_tpt, parse_download_links
from topic_selector import TopicSelector
from prompt_templates import get_prompt_builder
from smart_linker import SmartLinker
from instagram_generator import generate_instagram_post, send_to_makecom

load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# ===================================================================
# CONFIGURATION (preserved from V3.4)
# ===================================================================

# TEXTE — DeepSeek (primary: reasoner, fallback: chat)
DEEPSEEK_API_KEY    = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_TEXT_MODEL = "deepseek-reasoner"
DEEPSEEK_FALLBACK_MODEL = "deepseek-chat"
DEEPSEEK_TEXT_URL   = "https://api.deepseek.com/v1/chat/completions"

# IMAGES — Pollinations Klein-Large (5 keys)
_keys_in_env = [
    os.environ.get("POLLINATIONS_API_KEY_1"),
    os.environ.get("POLLINATIONS_API_KEY_2"),
    os.environ.get("POLLINATIONS_API_KEY_3"),
    os.environ.get("POLLINATIONS_API_KEY_4"),
    os.environ.get("POLLINATIONS_API_KEY_5"),
]
POLLINATIONS_KEYS = [k for k in _keys_in_env if k and len(k) > 5]
POLLINATIONS_MODEL = "klein-large"

# Small debug (safe)
if os.environ.get("GITHUB_ACTIONS") == "true":
    print(f"[CI-DEBUG] Pollinations keys found in env: {len(POLLINATIONS_KEYS)} / {len(_keys_in_env)}")

# Compatibility
CONTENT_KEYS = [DEEPSEEK_API_KEY] if DEEPSEEK_API_KEY else []

# Directories (relative to project root)
POSTS_DIR = os.path.join(PROJECT_ROOT, "posts")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# Limits
TARGET_WORD_COUNT = 2000
MIN_WORD_COUNT = 1600
MAX_RETRIES = 3
IMAGE_RETRY_MAX = 3
NUM_CONTENT_IMAGES = 4
TOTAL_IMAGES = 5

SITE_BASE_URL = "https://littlesmartgenius.com"

# Batch config
DAILY_SLOTS = ["keyword", "product", "freebie"]  # 3 articles per day
PAUSE_BETWEEN_ARTICLES = 30  # seconds

# Model ranking (preserved)
MODELS_RANKING = [
    "gemini-2.5-pro", "gemini-2.5-flash", "gemini-exp-1206",
    "gemini-pro-latest", "gemini-flash-latest",
    "gemini-2.0-flash", "gemini-2.0-flash-001",
    "gemini-2.5-flash-lite", "gemini-2.0-flash-lite", "gemini-flash-lite-latest",
    "gemini-3-pro-preview", "gemini-3-flash-preview", "gemini-2.5-flash-preview-09-2025",
]

# Personas — 6 Named Team Members
# Admin gets weight 3 (≈50%), others weight 1 each (≈10% each)
PERSONAS = [
    # ── ADMIN (50% of articles — weight 3) ──
    {
        "id": "LSG_Admin",
        "role": "Little Smart Genius — Founder & Lead Editor",
        "author_display": "Little Smart Genius",
        "expertise": "Curriculum design, educational publishing, content strategy for parents & educators",
        "tone": "Warm, authoritative, brand-native — writes as the voice of the Little Smart Genius platform",
        "img_style": "bright, colorful educational scenes, 3D Pixar style, brand orange accents",
        "weight": 3
    },
    # ── TEACHER ──
    {
        "id": "Sarah_Mitchell",
        "role": "Sarah Mitchell — Senior Content Creator & Elementary Teacher (15 years)",
        "author_display": "Sarah Mitchell",
        "expertise": "Classroom management, differentiated instruction, K-5 literacy & numeracy",
        "tone": "Warm, professional, evidence-based — speaks from daily classroom experience",
        "img_style": "bright classroom, educational setting, 3D Pixar style",
        "weight": 1
    },
    # ── PSYCHOLOGIST ──
    {
        "id": "Dr_Emily_Carter",
        "role": "Dr. Emily Carter — Child Development Advisor (PhD in Developmental Psychology)",
        "author_display": "Dr. Emily Carter",
        "expertise": "Cognitive development, learning psychology, executive function, screen-time research",
        "tone": "Authoritative, research-driven, accessible — translates science into parent-friendly language",
        "img_style": "modern office, professional setting, clean 3D",
        "weight": 1
    },
    # ── MONTESSORI MOM ──
    {
        "id": "Rachel_Nguyen",
        "role": "Rachel Nguyen — Parenting & Montessori Specialist",
        "author_display": "Rachel Nguyen",
        "expertise": "Montessori at home, child-led learning, hands-on sensory activities, nature play",
        "tone": "Friendly, encouraging, practical — speaks parent-to-parent with Montessori wisdom",
        "img_style": "cozy home learning space, warm colors, 3D illustration",
        "weight": 1
    },
    # ── PEDAGOGY EXPERT (NEW) ──
    {
        "id": "David_Moreau",
        "role": "David Moreau — Education & Pedagogy Specialist (M.Ed., 12 years)",
        "author_display": "David Moreau",
        "expertise": "Instructional design, differentiated pedagogy, formative assessment, project-based learning",
        "tone": "Clear, structured, methodical — explains teaching strategies with precision and care",
        "img_style": "organized classroom, anchor charts, structured learning environment, 3D illustration",
        "weight": 1
    },
    # ── EDUCATIONAL DESIGNER (NEW) ──
    {
        "id": "Lina_Bautista",
        "role": "Lina Bautista — Educational Designer & Visual Learning Expert",
        "author_display": "Lina Bautista",
        "expertise": "Graphic design for education, worksheet UX, color psychology, visual scaffolding, gamification",
        "tone": "Creative, visual-thinking, enthusiastic — sees learning through the lens of design and aesthetics",
        "img_style": "colorful design studio, art supplies, creative workspace, vibrant 3D illustration",
        "weight": 1
    },
]

session_api_config = {"key": None, "model": None}


# ===================================================================
# LOGGER (preserved from V3.4)
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
                "step": step, "status": status,
                "duration_seconds": round(elapsed, 2)
            })

    def log(self, level: str, message: str, indent: int = 1):
        icons = {
            "info": "[INFO]", "success": "[OK]", "warning": "[WARN]",
            "error": "[ERR]", "debug": "[DEBUG]", "api": "[API]",
            "check": "[CHECK]", "fix": "[FIX]", "quality": "[QUALITY]"
        }
        icon = icons.get(level, "  ")
        prefix = "   " * indent
        print(f"{prefix}{icon} {message}")

    def info(self, msg, indent=1): self.log("info", msg, indent)
    def success(self, msg, indent=1): self.log("success", msg, indent)
    def warning(self, msg, indent=1): self.log("warning", msg, indent)
    def error(self, msg, indent=1): self.log("error", msg, indent)
    def debug(self, msg, indent=1): self.log("debug", msg, indent)
    def check(self, msg, indent=1): self.log("check", msg, indent)
    def fix(self, msg, indent=1): self.log("fix", msg, indent)
    def quality(self, msg, indent=1): self.log("quality", msg, indent)

    def show_prompt(self, prompt_type: str, prompt: str, max_length: int = 400):
        print(f"\n   [PROMPT] {prompt_type}")
        print("   " + "+" + "-" * 74 + "+")
        lines = prompt[:max_length].split("\n")
        for line in lines[:10]:
            truncated = line[:71] + "..." if len(line) > 71 else line
            print(f"   | {truncated:<71} |")
        if len(prompt) > max_length:
            print(f"   | ... [{len(prompt) - max_length} caracteres supplementaires]")
        print("   " + "+" + "-" * 74 + "+")
        self.logs["prompts"].append({
            "type": prompt_type, "prompt": prompt,
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
            "model": model, "account": account,
            "success": success, "response_length": length
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
            "check": check_name, "passed": passed, "details": details
        })

    def correction_applied(self, issue: str, fix: str):
        print(f"   [FIX] CORRECTION: {issue}")
        print(f"      -> {fix}")
        self.logs["corrections"].append({
            "timestamp": datetime.now().isoformat(),
            "issue": issue, "fix": fix
        })

    def quality_score(self, category: str, score: int, max_score: int):
        percentage = (score / max_score) * 100
        icon = "[EXCELLENT]" if percentage >= 80 else "[OK]" if percentage >= 60 else "[FAIBLE]"
        print(f"   {icon} {category}: {score}/{max_score} ({percentage:.0f}%)")
        self.logs["quality_scores"][category] = {
            "score": score, "max": max_score, "percentage": round(percentage, 1)
        }

    def image_saved(self, filename: str, size_kb: int):
        self.logs["images_generated"].append({
            "filename": filename, "size_kb": size_kb,
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


# ===================================================================
# TEXT GENERATION (preserved from V3.4 — DeepSeek)
# ===================================================================

def _call_deepseek(prompt: str, model: str, headers: dict, logger: DetailedLogger,
                   account_label: str, max_retries: int = MAX_RETRIES,
                   min_response_len: int = 100) -> Optional[str]:
    """Low-level DeepSeek API call with retries."""
    payload = {
        "model": model,
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
            logger.debug(f"Appel DeepSeek ({account_label}) - {model}", 3)
            start_time = time.time()
            resp = requests.post(DEEPSEEK_TEXT_URL, headers=headers,
                                 json=payload, timeout=180)
            elapsed = time.time() - start_time

            if resp.status_code == 200:
                data = resp.json()
                msg  = data["choices"][0]["message"]
                text = msg.get("content") or msg.get("reasoning_content", "")
                if text and len(text.strip()) >= min_response_len:
                    logger.api_call(model, account_label, True, len(text))
                    logger.success(f"Succes en {elapsed:.2f}s ({len(text)} chars)", 3)
                    logger.show_response(text)
                    return text.strip()
                else:
                    logger.api_call(model, account_label, False)
                    logger.warning(f"Reponse vide ou trop courte ({len(text.strip()) if text else 0} < {min_response_len})", 4)
            elif resp.status_code == 429:
                logger.api_call(model, account_label, False)
                logger.warning(f"Rate limit (429) - retry dans {2**attempt}s", 3)
            elif resp.status_code == 402:
                logger.api_call(model, account_label, False)
                logger.error("Solde DeepSeek insuffisant (402)", 3)
                return None
            else:
                logger.api_call(model, account_label, False)
                logger.warning(f"HTTP {resp.status_code}", 3)

        except requests.exceptions.Timeout:
            logger.api_call(model, account_label, False)
            logger.warning(f"Timeout 180s (attempt {attempt+1}/{max_retries})", 3)
        except Exception as e:
            logger.api_call(model, account_label, False)
            logger.error(f"Erreur: {str(e)[:80]}", 3)

    return None


def generate_text_specialized(prompt: str, logger: DetailedLogger, prompt_type: str,
                               role: str = "content", max_retries: int = MAX_RETRIES) -> Optional[str]:
    """Generation texte via DeepSeek avec fallback automatique reasoner -> chat."""
    role_labels = {
        "plan": "Chef Orchestre", "content": "Redacteur Pro",
        "dir_art": "Directeur Artistique", "seo": "SEO Corrector"
    }
    account_label = role_labels.get(role, "Generic")

    # Set minimum response length based on role
    min_len_map = {"seo": 10, "dir_art": 50, "plan": 500, "content": 500}
    min_response_len = min_len_map.get(role, 100)

    if not DEEPSEEK_API_KEY:
        logger.error("Aucune cle DEEPSEEK_API_KEY configuree dans .env", 2)
        return None

    logger.info(f"Generation: {prompt_type} (Role: {role}) via {DEEPSEEK_TEXT_MODEL}", 2)
    logger.show_prompt(prompt_type, prompt)

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    # Try primary model (deepseek-reasoner)
    result = _call_deepseek(prompt, DEEPSEEK_TEXT_MODEL, headers, logger,
                            account_label, max_retries, min_response_len)
    if result:
        return result

    # Fallback to deepseek-chat if reasoner failed
    if DEEPSEEK_FALLBACK_MODEL and DEEPSEEK_FALLBACK_MODEL != DEEPSEEK_TEXT_MODEL:
        logger.warning(f"FALLBACK: {DEEPSEEK_TEXT_MODEL} echoue -> essai {DEEPSEEK_FALLBACK_MODEL}", 2)
        result = _call_deepseek(prompt, DEEPSEEK_FALLBACK_MODEL, headers, logger,
                                f"{account_label} (Fallback)", max_retries, min_response_len)
        if result:
            return result

    logger.error(f"Echec total apres {DEEPSEEK_TEXT_MODEL} + {DEEPSEEK_FALLBACK_MODEL}", 2)
    return None


def generate_plan(prompt, logger): return generate_text_specialized(prompt, logger, "PLAN SEO", role="plan")
def generate_content(prompt, logger): return generate_text_specialized(prompt, logger, "CONTENU ARTICLE", role="content")
def correct_with_seo_specialist(prompt, logger, correction_type):
    return generate_text_specialized(prompt, logger, f"CORRECTION SEO: {correction_type}", role="seo")


# ===================================================================
# IMAGE GENERATION (preserved from V3.4 — Pollinations Klein-Large)
# ===================================================================

def optimize_image_prompt_dir_art(basic_prompt: str, context: str, logger: DetailedLogger, image_index: int = 0) -> str:
    """Optimisation prompt image par directeur artistique V5.0 — styles uniques par image."""
    from prompt_templates import build_art_director_prompt
    optimization_prompt = build_art_director_prompt(basic_prompt, context, image_index)

    enhanced = generate_text_specialized(optimization_prompt, logger,
        f"ART DIRECTOR V5 (Image #{image_index + 1})", role="dir_art")

    if enhanced and len(enhanced) > 50:
        enhanced_clean = enhanced.strip().strip('"').strip("'")
        logger.success(f"Prompt optimise (style #{image_index % 4 + 1}): {len(enhanced_clean)} chars", 4)
        return enhanced_clean
    else:
        logger.warning("Optimisation echouee, utilisation prompt basique", 4)
        return f"{basic_prompt}, {context}, 3D Pixar style, high quality, vibrant colors, educational"



def download_image_pollinations_klein(prompt: str, seed: int, logger: DetailedLogger) -> Optional[bytes]:
    """Telecharge image depuis Pollinations avec Klein-Large et rotation des cles."""
    if not POLLINATIONS_KEYS:
        logger.error("Aucune cle Pollinations configuree", 5)
        return None

    for key_idx, api_key in enumerate(POLLINATIONS_KEYS, 1):
        try:
            safe_prompt = urllib.parse.quote(prompt)
            url = f"https://gen.pollinations.ai/image/{safe_prompt}"
            params = {
                "width": 1200, "height": 675, "seed": seed,
                "model": POLLINATIONS_MODEL, "nologo": "true", "enhance": "true"
            }
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            logger.debug(f"Pollinations Klein-Large (Cle #{key_idx})", 5)
            resp = requests.get(url, params=params, headers=headers, timeout=90)

            if resp.status_code == 200 and len(resp.content) > 1024:
                logger.success(f"Pollinations cle #{key_idx} OK: {len(resp.content)//1024} KB", 5)
                return resp.content
            else:
                logger.warning(f"Pollinations cle #{key_idx} FAIL: {resp.status_code}", 5)
                if resp.status_code == 429 and key_idx < len(POLLINATIONS_KEYS):
                    continue
        except Exception as e:
            logger.error(f"Pollinations cle #{key_idx} error: {str(e)[:50]}", 5)
            if key_idx < len(POLLINATIONS_KEYS):
                continue

    logger.error("Toutes les cles Pollinations ont echoue", 5)
    return None


def generate_seo_alt_text(concept: str, context: str) -> str:
    alt = f"{concept} {context}"
    alt = re.sub(r'[^a-zA-Z0-9\s-]', '', alt)
    alt = re.sub(r'\s+', '-', alt)
    return alt.lower()[:125]


def download_and_optimize_image(prompt: str, filename: str, logger: DetailedLogger,
                                alt_context: str = "", image_index: int = 0) -> Tuple[str, str]:
    """Telecharge et optimise une image (Dir. Artistique V5.0 + Pollinations Klein-Large)."""
    logger.info(f"Image: {filename}", 3)

    optimized_prompt = optimize_image_prompt_dir_art(prompt, alt_context, logger, image_index)

    clean_prompt = re.sub(r'[^a-zA-Z0-9 ,.-]', '', optimized_prompt)

    image_data = None
    for attempt in range(IMAGE_RETRY_MAX):
        seed = random.randint(0, 999999)
        logger.debug(f"Tentative {attempt + 1}/{IMAGE_RETRY_MAX}...", 4)
        image_data = download_image_pollinations_klein(clean_prompt, seed, logger)
        if image_data:
            break
        if attempt < IMAGE_RETRY_MAX - 1:
            time.sleep(2)

    if image_data and len(image_data) > 1024:
        try:
            img = Image.open(BytesIO(image_data))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            os.makedirs(IMAGES_DIR, exist_ok=True)
            webp_name = filename.replace(".jpg", ".webp")
            full_path = os.path.join(IMAGES_DIR, webp_name)

            img.thumbnail((1200, 1200))
            img.save(full_path, "WEBP", quality=85, optimize=True, method=6)

            file_size = os.path.getsize(full_path)
            logger.success(f"[SAVED] {full_path} ({file_size // 1024} KB)", 4)
            logger.image_saved(webp_name, file_size // 1024)

            alt_text = generate_seo_alt_text(clean_prompt[:50], alt_context)
            return f"{IMAGES_DIR}/{webp_name}", alt_text
        except Exception as e:
            logger.error(f"Erreur traitement image: {str(e)[:50]}", 4)

    logger.error(f"[FAIL] Echec - Placeholder utilise", 4)
    return "https://placehold.co/1200x675/F48C06/FFFFFF/png?text=Smart+Genius", "educational content"


# ===================================================================
# SEO CORRECTION (preserved from V3.4)
# ===================================================================

class SEOCorrector:
    @staticmethod
    def correct_title(title: str, target_length: int, logger: DetailedLogger):
        prompt = f"""You are an SEO expert. Fix this title to be {target_length} characters:
Current: "{title}" ({len(title)} chars)
Rules: Keep main keyword, be compelling, {target_length} chars max.
Return ONLY the corrected title, nothing else."""
        result = correct_with_seo_specialist(prompt, logger, "TITLE")
        if result:
            clean = result.strip().strip('"').strip("'")
            if 20 <= len(clean) <= 70:
                logger.correction_applied(f"Title: {len(title)}c -> {len(clean)}c", clean)
                return clean
        return title

    @staticmethod
    def correct_meta_description(desc: str, content: str, logger: DetailedLogger):
        prompt = f"""You are an SEO expert. Fix this meta description to be 120-155 characters:
Current: "{desc}" ({len(desc)} chars)
Context: Article about educational worksheets for kids.
Rules: Compelling, include call-to-action, 120-155 chars.
Return ONLY the corrected description."""
        result = correct_with_seo_specialist(prompt, logger, "META DESC")
        if result:
            clean = result.strip().strip('"').strip("'")
            if 100 <= len(clean) <= 170:
                logger.correction_applied(f"Meta: {len(desc)}c -> {len(clean)}c", clean[:60] + "...")
                return clean
        return desc


# ===================================================================
# CONTENT VERIFICATION (preserved from V3.4)
# ===================================================================

class ContentVerifier:
    @staticmethod
    def verify_content(content: dict, logger: DetailedLogger) -> Tuple[bool, List[str]]:
        logger.step_start("VERIFICATION QUALITE", "Analyse du contenu")
        issues = []

        # Title check
        title = content.get("title", "")
        if len(title) < 20:
            issues.append(f"Titre trop court: {len(title)} chars")
        elif len(title) > 70:
            issues.append(f"Titre trop long: {len(title)} chars")
        logger.verification_result("Titre (20-70 chars)", 20 <= len(title) <= 70, f"{len(title)} chars")

        # Meta description
        meta = content.get("meta_description", "")
        logger.verification_result("Meta desc (100-170 chars)", 100 <= len(meta) <= 170, f"{len(meta)} chars")

        # Word count
        word_count = content.get("word_count", 0)
        if word_count < MIN_WORD_COUNT:
            issues.append(f"Contenu trop court: {word_count} mots (min {MIN_WORD_COUNT})")
        logger.verification_result(f"Mots (>={MIN_WORD_COUNT})", word_count >= MIN_WORD_COUNT, f"{word_count} mots")

        # H2 sections
        html = content.get("content", "")
        h2_count = len(re.findall(r'<h2>', html))
        logger.verification_result("Sections H2 (>=3)", h2_count >= 3, f"{h2_count} H2")

        # Images
        img_count = len(re.findall(r'<img', html))
        logger.verification_result("Images (>=1)", img_count >= 1, f"{img_count} images")

        is_valid = len(issues) == 0
        logger.step_end("VERIFICATION QUALITE", "success" if is_valid else "warning")
        return is_valid, issues


# ===================================================================
# SEO OPTIMIZER (preserved from V3.4)
# ===================================================================

class SEOOptimizer:
    @staticmethod
    def calculate_reading_time(content: str) -> int:
        word_count = len(re.findall(r'\w+', re.sub(r'<[^>]+>', '', content)))
        return max(1, word_count // 200)

    @staticmethod
    def extract_keywords(title: str, content: str) -> List[str]:
        text = re.sub(r'<[^>]+>', '', f"{title} {content}").lower()
        words = re.findall(r'\b[a-z]{4,}\b', text)
        freq = {}
        for w in words:
            if w not in {"this", "that", "with", "from", "have", "been", "your", "they", "them"}:
                freq[w] = freq.get(w, 0) + 1
        sorted_kw = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [kw for kw, _ in sorted_kw[:10]]

    @staticmethod
    def generate_meta_description(content: str, max_length: int = 155) -> str:
        text = re.sub(r'<[^>]+>', '', content)
        sentences = re.split(r'[.!?]+', text)
        desc = ""
        for s in sentences:
            s = s.strip()
            if len(s) > 30 and len(desc) + len(s) < max_length:
                desc += s + ". "
                if len(desc) > 100:
                    break
        return desc.strip()[:max_length]

    @staticmethod
    def optimize_slug(title: str) -> str:
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug).strip('-')
        return slug[:80]

    @staticmethod
    def calculate_seo_score(article_data: dict, logger: DetailedLogger) -> Tuple[int, List[str]]:
        """V5.0 — 20-criteria SEO scoring system for 90/100 minimum target."""
        logger.step_start("SCORE SEO V5.0", "20 criteres d'analyse")
        score = 0
        max_score = 100
        suggestions = []

        title = article_data.get("title", "")
        meta = article_data.get("meta_description", "")
        content = article_data.get("content", "")
        word_count = article_data.get("word_count", 0)
        keyword = article_data.get("primary_keyword", "")
        plain_text = re.sub(r'<[^>]+>', '', content).lower()

        # 1. Title length (8 pts)
        if 30 <= len(title) <= 60:
            score += 8
        elif 20 <= len(title) <= 70:
            score += 4
            suggestions.append(f"Titre: {len(title)} chars (optimal: 30-60)")
        else:
            suggestions.append(f"Titre: {len(title)} chars (optimal: 30-60)")

        # 2. Keyword in title — first 3 words ideal (7 pts)
        if keyword:
            title_lower = title.lower()
            kw_lower = keyword.lower()
            title_words = title_lower.split()[:3]
            title_start = " ".join(title_words)
            if kw_lower in title_lower:
                if any(kw_word in title_start for kw_word in kw_lower.split()):
                    score += 7  # keyword word in first 3 words
                else:
                    score += 5  # keyword present but not at start
            else:
                kw_words = kw_lower.split()
                if sum(1 for w in kw_words if w in title_lower) >= len(kw_words) // 2:
                    score += 3  # partial keyword match
                else:
                    suggestions.append("Keyword absent du titre")

        # 3. Meta description length (7 pts)
        if 120 <= len(meta) <= 155:
            score += 7
        elif 100 <= len(meta) <= 170:
            score += 4
            suggestions.append(f"Meta: {len(meta)} chars (optimal: 120-155)")
        else:
            suggestions.append(f"Meta: {len(meta)} chars (optimal: 120-155)")

        # 4. Keyword in meta description (5 pts)
        if keyword and keyword.lower() in meta.lower():
            score += 5
        elif keyword:
            kw_words = keyword.lower().split()
            if sum(1 for w in kw_words if w in meta.lower()) >= len(kw_words) // 2:
                score += 3
            else:
                suggestions.append("Keyword absent de la meta description")

        # 5. Word count (8 pts)
        if word_count >= TARGET_WORD_COUNT:
            score += 8
        elif word_count >= MIN_WORD_COUNT:
            score += 5
            suggestions.append(f"Contenu: {word_count} mots (cible: {TARGET_WORD_COUNT})")
        else:
            suggestions.append(f"Contenu trop court: {word_count} mots (min: {MIN_WORD_COUNT})")
            score += 2

        # 6. H2 structure (5 pts)
        h2_count = len(re.findall(r'<h2[^>]*>', content))
        if h2_count >= 5:
            score += 5
        elif h2_count >= 3:
            score += 3
        else:
            suggestions.append(f"H2: {h2_count} (cible: 5+)")

        # 7. H3 structure (3 pts)
        h3_count = len(re.findall(r'<h3[^>]*>', content))
        if h3_count >= 8:
            score += 3
        elif h3_count >= 4:
            score += 2
        else:
            suggestions.append(f"H3: {h3_count} (cible: 8+)")

        # 8. Images with alt text (7 pts)
        img_tags = re.findall(r'<img[^>]+>', content)
        img_with_alt = [img for img in img_tags if 'alt="' in img and 'alt=""' not in img]
        if len(img_with_alt) >= 4:
            score += 7
        elif len(img_with_alt) >= 2:
            score += 4
        else:
            suggestions.append(f"Images: {len(img_with_alt)} avec alt (cible: 4+)")

        # 9. Keyword density (8 pts) — optimal 1.0-3.0%
        if keyword and word_count > 0:
            kw_lower = keyword.lower()
            kw_occurrences = plain_text.count(kw_lower)
            kw_word_count = len(kw_lower.split())
            density = (kw_occurrences * kw_word_count / word_count) * 100
            if 1.0 <= density <= 3.0:
                score += 8
            elif 0.5 <= density <= 4.0:
                score += 5
                suggestions.append(f"Keyword density: {density:.1f}% (optimal: 1.0-3.0%)")
            else:
                suggestions.append(f"Keyword density: {density:.1f}% (optimal: 1.0-3.0%)")
                score += 2

        # 10. Keyword in first 100 words (5 pts)
        if keyword:
            first_100 = " ".join(plain_text.split()[:100])
            if keyword.lower() in first_100:
                score += 5
            else:
                kw_words = keyword.lower().split()
                if sum(1 for w in kw_words if w in first_100) >= len(kw_words) // 2:
                    score += 3
                else:
                    suggestions.append("Keyword absent des 100 premiers mots")

        # 11. Internal links (5 pts)
        internal_links = re.findall(r'<a\s+[^>]*href\s*=\s*["\'][^"\']*(?:littlesmartgenius|blog|freebies|products|posts/)[^"\']*["\']', content)
        all_links = re.findall(r'<a\s+href', content)
        link_count = len(all_links)
        if link_count >= 4:
            score += 5
        elif link_count >= 2:
            score += 3
        else:
            suggestions.append(f"Liens: {link_count} (cible: 4+)")

        # 12. External links (3 pts)
        external_links = re.findall(r'<a\s+[^>]*href\s*=\s*["\']https?://(?!littlesmartgenius)', content)
        if len(external_links) >= 1:
            score += 3
        else:
            suggestions.append("Ajouter 1+ lien externe (autorite)")

        # 13. FAQ section (5 pts)
        if '<div class="faq-section' in content or '<div class="faq' in content:
            score += 5
        else:
            suggestions.append("Section FAQ manquante")

        # 14. Lists: ul and ol (4 pts)
        ul_count = len(re.findall(r'<ul[^>]*>', content))
        ol_count = len(re.findall(r'<ol[^>]*>', content))
        total_lists = ul_count + ol_count
        if total_lists >= 3:
            score += 4
        elif total_lists >= 1:
            score += 2
        else:
            suggestions.append(f"Listes: {total_lists} (cible: 3+)")

        # 15. Bold keywords with <strong> (3 pts)
        strong_count = len(re.findall(r'<strong>', content))
        if strong_count >= 3:
            score += 3
        elif strong_count >= 1:
            score += 1
        else:
            suggestions.append("Ajouter 3+ <strong> pour les keywords")

        # 16. Slug length (3 pts)
        slug = article_data.get("slug", "")
        if 10 <= len(slug) <= 60:
            score += 3
        elif len(slug) <= 80:
            score += 2
        else:
            suggestions.append(f"Slug trop long: {len(slug)} chars (max: 60)")

        # 17. Reading time sweet spot: 8-15 min (3 pts)
        reading_time = article_data.get("reading_time", word_count // 200)
        if 8 <= reading_time <= 15:
            score += 3
        elif 5 <= reading_time <= 20:
            score += 2
        else:
            suggestions.append(f"Reading time: {reading_time} min (optimal: 8-15)")

        # 18. Transition words (3 pts)
        from prompt_templates import TRANSITION_WORDS
        transition_count = sum(1 for tw in TRANSITION_WORDS if tw.lower() in plain_text)
        if transition_count >= 5:
            score += 3
        elif transition_count >= 2:
            score += 2
        else:
            suggestions.append(f"Transition words: {transition_count} (cible: 5+)")

        # 19. Short paragraphs — avg ≤ 4 sentences (4 pts)
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', content, re.DOTALL)
        if paragraphs:
            avg_sentences = sum(
                len(re.findall(r'[.!?]+', re.sub(r'<[^>]+>', '', p)))
                for p in paragraphs
            ) / max(len(paragraphs), 1)
            if avg_sentences <= 4:
                score += 4
            elif avg_sentences <= 6:
                score += 2
            else:
                suggestions.append(f"Paragraphes trop longs: avg {avg_sentences:.1f} phrases (max: 4)")
        else:
            score += 2  # no <p> tags = unusual but not penalized hard

        # 20. Anti-AI detection (3 pts)
        from prompt_templates import AI_DETECTION_PHRASES
        ai_phrases_found = [phrase for phrase in AI_DETECTION_PHRASES if phrase.lower() in plain_text]
        if len(ai_phrases_found) == 0:
            score += 3
        elif len(ai_phrases_found) <= 2:
            score += 1
            suggestions.append(f"AI phrases detectees ({len(ai_phrases_found)}): {', '.join(ai_phrases_found[:3])}")
        else:
            suggestions.append(f"AI phrases detectees ({len(ai_phrases_found)}): {', '.join(ai_phrases_found[:5])}")

        final_score = min(score, max_score)

        # Detailed quality score breakdown
        logger.quality_score("SEO Score V5.0", final_score, max_score)
        if suggestions:
            for s in suggestions[:5]:
                logger.info(f"  -> {s}", 2)
        logger.step_end("SCORE SEO V5.0")
        return final_score, suggestions



# ===================================================================
# V4.0 ARTICLE GENERATION ENGINE
# ===================================================================

def generate_article(slot: str, topic: dict, topic_selector: TopicSelector) -> Optional[Dict]:
    """
    Generate a single article for a given slot and topic.
    Uses the V4 prompt templates and smart linker.
    """
    global session_api_config
    session_api_config = {"key": None, "model": None}

    weights = [p.get('weight', 1) for p in PERSONAS]
    persona = random.choices(PERSONAS, weights=weights, k=1)[0]
    topic_name = topic["topic_name"]
    category = topic["category"]
    keywords = topic["keywords"]
    product_data = topic.get("product_data")

    temp_slug = SEOOptimizer.optimize_slug(f"{topic_name}-{int(time.time())}")
    logger = DetailedLogger(temp_slug)

    logger.banner(f"AUTO BLOG V4.0 — {slot.upper()} ARTICLE", "=")
    print(f"Slot: {slot}")
    print(f"Sujet: {topic_name[:60]}")
    print(f"Persona: {persona['role']}")
    print(f"Categorie: {category}")
    print(f"Mots-cles: {keywords[:60]}")
    print(f"Demarrage: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Images: {TOTAL_IMAGES} ({NUM_CONTENT_IMAGES} contenu + 1 cover)")

    # --- STEP 1: Build prompts using V4 templates ---
    logger.step_start("ETAPE 1/8: CREATION DU PLAN SEO",
                     f"Prompt template: {slot}")

    prompt_builder = get_prompt_builder(slot)

    if slot == "keyword":
        prompts = prompt_builder(topic_name, persona)
    elif slot == "product":
        prompts = prompt_builder(product_data, persona)
    elif slot == "freebie":
        prompts = prompt_builder(product_data, persona)
    else:
        prompts = prompt_builder(topic_name, persona)

    # --- STEP 2: Generate plan ---
    raw_plan = generate_plan(prompts["plan_prompt"], logger)
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
    except Exception as e:
        logger.error(f"Parsing JSON: {str(e)}", 2)
        logger.save()
        return None

    logger.step_end("ETAPE 1/8: CREATION DU PLAN SEO")

    # --- STEP 3: Generate content ---
    logger.step_start("ETAPE 2/8: REDACTION DU CONTENU", f"Slot: {slot}")

    content_prompt = prompts["content_prompt_builder"](plan, TARGET_WORD_COUNT)
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

    logger.step_end("ETAPE 2/8: REDACTION DU CONTENU")

    # --- STEP 4: Images ---
    logger.step_start("ETAPE 3/8: GENERATION DES VISUELS", f"Klein-Large ({len(POLLINATIONS_KEYS)} cles)")

    slug = SEOOptimizer.optimize_slug(plan['title'])
    ts = int(time.time())

    # Cover image (style preset #0: Hero/Establishing Shot)
    logger.info(f"Image 1/{TOTAL_IMAGES}: COUVERTURE", 2)
    cover_prompt = plan.get('cover_concept', f"{topic_name} educational illustration")
    cover_path, cover_alt = download_and_optimize_image(cover_prompt, f"{slug}-cover-{ts}.jpg", logger, plan['title'], image_index=0)
    logger.progress(1, TOTAL_IMAGES, "Images")

    # Content images (style presets #1-3: Close-up, Infographic, Lifestyle, then cycle)
    section_images = []
    for i, section in enumerate(plan.get('sections', [])[:NUM_CONTENT_IMAGES], 1):
        logger.info(f"Image {i+1}/{TOTAL_IMAGES}: {section.get('h2', '')[:40]}...", 2)
        img_concept = section.get('image_concept', cover_prompt)
        img_path, img_alt = download_and_optimize_image(img_concept, f"{slug}-img{i}-{ts}.jpg", logger, section.get('h2', ''), image_index=i)
        section_images.append((img_path, img_alt))
        logger.progress(i+1, TOTAL_IMAGES, "Images")

    # Inject images
    for i, (img_path, img_alt) in enumerate(section_images, 1):
        img_tag = f'<figure class="article-image"><img src="../{img_path}" alt="{img_alt}" loading="lazy" width="1200" height="675"></figure>'
        html_content = html_content.replace(f"[IMAGE_{i}]", img_tag)
    # FAILSAFE: If AI didn't include [IMAGE_X] placeholders, force-inject at H2 boundaries
    img_count_in_content = len(re.findall(r'<img[^>]+>', html_content))
    if img_count_in_content == 0 and section_images:
        logger.warning(f"Aucune image detectee dans le contenu — injection forcee aux H2", 2)
        h2_positions = [m.start() for m in re.finditer(r'<h2[^>]*>', html_content)]
        for idx, (img_path, img_alt) in enumerate(section_images):
            if idx < len(h2_positions):
                insert_pos = h2_positions[idx]
                img_tag = f'<figure class="article-image"><img src="../{img_path}" alt="{img_alt}" loading="lazy" width="1200" height="675"></figure>\n'
                html_content = html_content[:insert_pos] + img_tag + html_content[insert_pos:]
                # Recalculate positions since we inserted content
                h2_positions = [m.start() for m in re.finditer(r'<h2[^>]*>', html_content)]
                logger.success(f"Image {idx+1} injectee avant H2 #{idx+1}", 3)

    html_content = re.sub(r'\[IMAGE_\d+\]', '', html_content)

    logger.step_end("ETAPE 3/8: GENERATION DES VISUELS")

    # --- STEP 5: FAQ ---
    logger.step_start("ETAPE 4/8: AJOUT FAQ", f"{len(plan.get('faq', []))} questions")

    faq_html = '<div class="faq-section mt-12"><h2>Frequently Asked Questions</h2>'
    for faq in plan.get('faq', []):
        faq_html += f'<div class="faq-item mb-6"><h3 class="font-bold text-lg mb-2">{faq["q"]}</h3><p>{faq["a"]}</p></div>'
    faq_html += '</div>'
    html_content += faq_html

    logger.step_end("ETAPE 4/8: AJOUT FAQ")

    # --- STEP 6: Smart Linking (V4.0 — replaces old inject_internal_links) ---
    logger.step_start("ETAPE 5/8: SMART LINKING V4.0", "Scan articles + liens internes")

    smart_linker = SmartLinker()
    html_content = smart_linker.inject_smart_links(
        html_content, plan['title'], category, keywords, slug, logger
    )

    # Add CTA box with product link (for product/freebie slots)
    if slot == "product" and product_data:
        cta_html = f"""
<div class="cta-box" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 15px; margin: 30px 0; text-align: center;">
    <h3 style="color: white; margin-bottom: 15px;">Ready to Enhance Your Teaching?</h3>
    <p style="color: white; margin-bottom: 20px;">Explore our premium educational resources:</p>
    <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
        <a href="{product_data['url']}" target="_blank" rel="noopener" style="background: white; color: #667eea; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold;">{product_data['name'][:50]}</a>
        <a href="{SITE_BASE_URL}/freebies.html" style="background: #F48C06; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold;">Get Free Resources</a>
    </div>
</div>"""
        html_content += cta_html
    elif slot == "freebie" and product_data:
        # CTA already in prompt template output — add fallback
        if '<div class="download-cta"' not in html_content:
            cta_html = f"""
<div class="download-cta" style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); padding: 30px; border-radius: 15px; margin: 30px 0; text-align: center;">
    <h3 style="color: white; margin-bottom: 10px;">Download {product_data['name']} — FREE!</h3>
    <p style="color: white; margin-bottom: 15px;">{product_data.get('desc', 'Free educational printable')}</p>
    <a href="{product_data['url']}" target="_blank" rel="noopener" style="background: white; color: #059669; padding: 12px 30px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block;">Download Now (Free PDF)</a>
</div>"""
            html_content += cta_html
    else:
        # Keyword slot: generic CTA
        cta_html = f"""
<div class="cta-box" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 15px; margin: 30px 0; text-align: center;">
    <h3 style="color: white; margin-bottom: 15px;">Love Learning Activities?</h3>
    <p style="color: white; margin-bottom: 20px;">Discover our free printable worksheets and premium resources:</p>
    <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
        <a href="{SITE_BASE_URL}/freebies.html" style="background: #F48C06; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold;">Free Worksheets</a>
        <a href="{SITE_BASE_URL}/products.html" style="background: white; color: #667eea; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold;">Premium Resources</a>
    </div>
</div>"""
        html_content += cta_html

    logger.step_end("ETAPE 5/8: SMART LINKING V4.0")

    # --- STEP 7: Build final data ---
    meta_desc = plan.get('meta_description') or SEOOptimizer.generate_meta_description(html_content)
    kw_list = SEOOptimizer.extract_keywords(plan['title'], html_content)
    reading_time = SEOOptimizer.calculate_reading_time(html_content)

    final_data = {
        "title": plan['title'],
        "slug": slug,
        "author": persona['id'],
        "author_name": persona.get('author_display', persona['role']),
        "date": datetime.now().strftime("%B %d, %Y"),
        "iso_date": datetime.now().isoformat(),
        "category": category,
        "image": cover_path,
        "content": html_content,
        "excerpt": meta_desc,
        "meta_description": meta_desc,
        "primary_keyword": plan.get('primary_keyword', keywords),
        "keywords": kw_list,
        "reading_time": reading_time,
        "word_count": word_count,
        "faq_schema": plan.get('faq', []),
        "slot": slot,
        "topic_name": topic_name,
    }

    # Verification
    is_valid, issues = ContentVerifier.verify_content(final_data, logger)

    # SEO Score
    seo_score, seo_suggestions = SEOOptimizer.calculate_seo_score(final_data, logger)

    # SEO corrections V5.0: correction loop until 90+ (max 2 rounds)
    MAX_CORRECTION_ROUNDS = 2
    for correction_round in range(MAX_CORRECTION_ROUNDS):
        if seo_score >= 90:
            logger.success(f"SEO V5.0: {seo_score}/100 — objectif 90+ atteint!", 2)
            break

        logger.step_start(f"ETAPE 6/8: CORRECTIONS SEO V5 (Round {correction_round + 1})",
                         f"Score: {seo_score}/100 — cible: 90+")

        content_modified = False

        # Fix 1: Title length — force truncate if API correction fails
        if not (30 <= len(final_data['title']) <= 60):
            target_len = 50 if len(final_data['title']) > 60 else 40
            corrected = SEOCorrector.correct_title(final_data['title'], target_len, logger)
            if corrected and corrected != final_data['title']:
                final_data['title'] = corrected
            elif len(final_data['title']) > 60:
                # Force truncation fallback
                truncated = final_data['title'][:57] + '...'
                logger.correction_applied(f"Title force-truncated: {len(final_data['title'])}c -> {len(truncated)}c", truncated[:50])
                final_data['title'] = truncated
            content_modified = True

        # Fix 2: Meta description
        if not (120 <= len(final_data['meta_description']) <= 155):
            final_data['meta_description'] = SEOCorrector.correct_meta_description(
                final_data['meta_description'], final_data['content'], logger)
            final_data['excerpt'] = final_data['meta_description']
            content_modified = True

        # Fix 3: Remove AI detection phrases
        from prompt_templates import AI_DETECTION_PHRASES
        content_fixed = final_data['content']
        ai_fixes = 0
        for phrase in AI_DETECTION_PHRASES:
            if phrase.lower() in content_fixed.lower():
                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                content_fixed = pattern.sub("", content_fixed, count=1)
                ai_fixes += 1
        if ai_fixes > 0:
            final_data['content'] = content_fixed
            logger.correction_applied(f"Removed {ai_fixes} AI-detection phrases", "Content cleaned")
            content_modified = True

        # Fix 4: Keyword density — add <strong>keyword</strong> if too low
        kw = final_data.get('primary_keyword', '')
        if kw:
            plain = re.sub(r'<[^>]+>', '', final_data['content']).lower()
            wc = len(plain.split())
            kw_count = plain.count(kw.lower())
            kw_words = len(kw.split())
            density = (kw_count * kw_words / max(wc, 1)) * 100 if wc > 0 else 0
            if density < 1.0:
                # Inject keyword naturally in some paragraphs
                paragraphs = re.findall(r'(<p[^>]*>)(.*?)(</p>)', final_data['content'], re.DOTALL)
                injected = 0
                for idx in range(2, min(len(paragraphs), 10), 3):  # Every 3rd paragraph
                    p_open, p_content, p_close = paragraphs[idx]
                    if kw.lower() not in p_content.lower() and injected < 3:
                        # Add at end of paragraph
                        new_p = f"{p_open}{p_content} This is especially helpful for <strong>{kw}</strong>.{p_close}"
                        final_data['content'] = final_data['content'].replace(
                            f"{p_open}{p_content}{p_close}", new_p, 1)
                        injected += 1
                if injected > 0:
                    logger.correction_applied(f"Keyword density boost: +{injected} mentions", f"{kw} (was {density:.1f}%)")
                    content_modified = True

        # Fix 5: Add external authority link if missing
        if not re.search(r'<a\s+[^>]*href\s*=\s*["\']https?://(?!littlesmartgenius)', final_data['content']):
            ext_link = '<p><em>According to the <a href="https://www.naeyc.org/resources" target="_blank" rel="noopener">National Association for the Education of Young Children (NAEYC)</a>, hands-on educational activities are crucial for early childhood development.</em></p>'
            # Insert before the FAQ section or at the end
            if '<div class="faq-section' in final_data['content']:
                final_data['content'] = final_data['content'].replace(
                    '<div class="faq-section', f'{ext_link}\n<div class="faq-section', 1)
            else:
                final_data['content'] += ext_link
            logger.correction_applied("External link added", "NAEYC authority reference")
            content_modified = True

        # Fix 6: Ensure keyword in first paragraph
        if kw:
            first_p = re.search(r'<p[^>]*>(.*?)</p>', final_data['content'], re.DOTALL)
            if first_p and kw.lower() not in first_p.group(1).lower():
                original_p = first_p.group(0)
                kw_sentence = f" When it comes to <strong>{kw}</strong>, parents have many great options."
                new_p = original_p.replace('</p>', f'{kw_sentence}</p>', 1)
                final_data['content'] = final_data['content'].replace(original_p, new_p, 1)
                logger.correction_applied("Keyword added to first paragraph", kw[:40])
                content_modified = True

        # Re-score
        new_score, new_suggestions = SEOOptimizer.calculate_seo_score(final_data, logger)
        if new_score > seo_score:
            logger.success(f"Score ameliore: {seo_score} -> {new_score}", 2)
            seo_score = new_score
            seo_suggestions = new_suggestions

        logger.step_end(f"ETAPE 6/8: CORRECTIONS SEO V5 (Round {correction_round + 1})")


    # --- STEP 8: Save ---
    logger.step_start("ETAPE 7/8: SAUVEGARDE", "Ecriture JSON")

    os.makedirs(POSTS_DIR, exist_ok=True)
    output_file = f"{POSTS_DIR}/{slug}-{ts}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)

    file_size = os.path.getsize(output_file)
    logger.success(f"Sauvegarde ({file_size // 1024} KB): {output_file}", 2)

    # Mark topic as used
    topic_selector.mark_used(slot, topic_name)
    logger.success(f"Topic marque comme utilise: {topic_name[:40]}", 2)

    logger.step_end("ETAPE 7/8: SAUVEGARDE")

    # --- STEP 9: Instagram post ---
    logger.step_start("ETAPE 8/8: INSTAGRAM POST", "Generation post 1080x1080")

    # Resolve cover image path for Instagram
    ig_cover = None
    if cover_path and not cover_path.startswith("http"):
        ig_cover = os.path.join(BASE_DIR, cover_path) if not os.path.isabs(cover_path) else cover_path

    ig_result = generate_instagram_post(final_data, ig_cover)
    if ig_result:
        logger.success(f"Instagram post: {ig_result['image_path']}", 2)
        # Send to Make.com for auto-posting
        article_url = f"{SITE_BASE_URL}/articles/{slug}.html"
        if send_to_makecom(ig_result, article_url):
            logger.success("Make.com webhook sent — Instagram post queued", 2)
        else:
            logger.info("Make.com webhook skipped (no URL configured or error)", 2)
    else:
        logger.warning("Instagram post skipped (Pillow not available or error)", 2)

    logger.step_end("ETAPE 8/8: INSTAGRAM POST")

    logger.save()

    # Final report
    logger.banner("GENERATION V4.0 TERMINEE", "=")
    print(f"Fichier: {output_file}")
    print(f"Slot: {slot}")
    print(f"Sujet: {topic_name[:60]}")
    print(f"\nStatistiques:")
    print(f"   - Mots: {word_count}")
    print(f"   - Structure: {h2_count} H2, {h3_count} H3")
    print(f"   - Images: {TOTAL_IMAGES}")
    print(f"   - FAQ: {len(plan.get('faq', []))}")
    print(f"   - Score SEO: {seo_score}/100")
    print(f"   - Temps lecture: {reading_time} min")
    if ig_result:
        print(f"   - Instagram: {ig_result['image_path']}")
    print(f"\nTermine: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 80)

    return final_data


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ===================================================================
# DAILY BATCH ORCHESTRATOR
# ===================================================================

def run_daily_batch():
    """Run the daily batch: generate 3 articles (keyword, product, freebie)."""
    print("\n" + "=" * 80)
    print("  AUTO BLOG V4.0 — DAILY BATCH")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    ts = TopicSelector()
    stats = ts.get_stats()
    print(f"\nTopic Pool:")
    print(f"  Keywords: {stats['keywords_remaining']}/{stats['keywords_total']} remaining")
    print(f"  Products: {stats['products_remaining']}/{stats['products_total']} remaining")
    print(f"  Freebies: {stats['freebies_remaining']}/{stats['freebies_total']} remaining")
    print(f"  Total articles generated: {stats['total_articles']}")

    results = []
    for i, slot in enumerate(DAILY_SLOTS):
        print(f"\n{'='*80}")
        print(f"  ARTICLE {i+1}/{len(DAILY_SLOTS)} — Slot: {slot.upper()}")
        print(f"{'='*80}")

        topic = ts.get_next_topic(slot)
        if not topic:
            print(f"\n[SKIP] No available topics for slot '{slot}'")
            continue

        print(f"  Topic: {topic['topic_name'][:60]}")
        print(f"  Category: {topic['category']}")

        try:
            result = generate_article(slot, topic, ts)
            if result:
                results.append({
                    "slot": slot,
                    "title": result["title"],
                    "slug": result["slug"],
                    "word_count": result["word_count"],
                })
                print(f"\n[OK] Article {i+1} generated successfully")
            else:
                print(f"\n[FAIL] Article {i+1} generation failed")
        except Exception as e:
            print(f"\n[ERROR] Article {i+1}: {str(e)}")
            import traceback
            traceback.print_exc()

        # Pause between articles
        if i < len(DAILY_SLOTS) - 1:
            print(f"\n[PAUSE] Waiting {PAUSE_BETWEEN_ARTICLES}s before next article...")
            time.sleep(PAUSE_BETWEEN_ARTICLES)

    # Summary
    print("\n" + "=" * 80)
    print("  DAILY BATCH COMPLETE")
    print("=" * 80)
    print(f"\nArticles generated: {len(results)}/{len(DAILY_SLOTS)}")
    for r in results:
        print(f"  [{r['slot'].upper()}] {r['title'][:50]}  ({r['word_count']} words)")

    # Updated stats
    ts2 = TopicSelector()
    stats2 = ts2.get_stats()
    print(f"\nUpdated Pool:")
    print(f"  Keywords remaining: {stats2['keywords_remaining']}/{stats2['keywords_total']}")
    print(f"  Products remaining: {stats2['products_remaining']}/{stats2['products_total']}")
    print(f"  Freebies remaining: {stats2['freebies_remaining']}/{stats2['freebies_total']}")
    print(f"  Total articles: {stats2['total_articles']}")

    return results


def run_single(slot: str = None):
    """Run a single article generation."""
    ts = TopicSelector()

    if slot:
        topic = ts.get_next_topic(slot)
    else:
        # Legacy mode: random slot
        slot = random.choice(DAILY_SLOTS)
        topic = ts.get_next_topic(slot)

    if not topic:
        print(f"[ERROR] No available topics for slot '{slot}'")
        return None

    return generate_article(slot, topic, ts)


# ===================================================================
# CLI ENTRY POINT
# ===================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Auto Blog V4.0 — Generation Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python auto_blog_v4.py --batch              # Daily batch (3 articles)
  python auto_blog_v4.py --slot keyword       # Single keyword article
  python auto_blog_v4.py --slot product       # Single product article
  python auto_blog_v4.py --slot freebie       # Single freebie article
  python auto_blog_v4.py --stats              # Show topic pool stats
  python auto_blog_v4.py                      # Single random article (legacy)
"""
    )
    parser.add_argument("--batch", action="store_true", help="Run daily batch (3 articles)")
    parser.add_argument("--slot", choices=["keyword", "product", "freebie"],
                       help="Generate a single article for this slot")
    parser.add_argument("--stats", action="store_true", help="Show topic pool statistics")

    args = parser.parse_args()

    if args.stats:
        ts = TopicSelector()
        stats = ts.get_stats()
        print("\n  AUTO BLOG V4.0 — Topic Pool Statistics")
        print("  " + "=" * 50)
        for key, val in stats.items():
            print(f"  {key}: {val}")
        return

    if args.batch:
        run_daily_batch()
    elif args.slot:
        run_single(args.slot)
    else:
        run_single()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterruption utilisateur")
    except Exception as e:
        print(f"\n\nERREUR CRITIQUE: {str(e)}")
        import traceback
        traceback.print_exc()
