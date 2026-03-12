"""
AUTO BLOG V6 ULTIMATE — MULTI-AGENT GENERATION ENGINE
Fusion of V4 ecosystem + V5 parallel multi-agent architecture.
7 AI Agents (deepseek-reasoner) + parallel image generation.
60-criteria SEO audit (50 AI + 10 local) + auto-corrections.

Usage:
  python auto_blog_v6_ultimate.py --batch              # Daily batch (3 articles)
  python auto_blog_v6_ultimate.py --slot keyword       # Single article by slot
  python auto_blog_v6_ultimate.py --slot product
  python auto_blog_v6_ultimate.py --slot freebie
  python auto_blog_v6_ultimate.py --schedule           # Schedule-aware
  python auto_blog_v6_ultimate.py --regenerate SLUG    # Regenerate by slug
  python auto_blog_v6_ultimate.py --stats              # Show topic pool stats
  python auto_blog_v6_ultimate.py                      # Single random article

(c) 2026 Little Smart Genius
"""

import os
import sys
import io
import json
import glob
import random
import re
import time
import asyncio
import aiohttp
import argparse
import requests
import urllib.parse
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional, Tuple

# No manual stdout encoding forced - handled by Python automatically.

from dotenv import load_dotenv
from PIL import Image

# Resolve project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# V6 modules
from data_parsers import parse_products_tpt, parse_download_links
from topic_selector import TopicSelector
from prompt_templates import get_prompt_builder, AI_DETECTION_PHRASES, TRANSITION_WORDS, IMAGE_STYLE_PRESETS, build_art_director_prompt
from smart_linker import SmartLinker
from instagram_generator import generate_instagram_post, send_to_makecom
from master_prompt import build_prompt as master_build_prompt  # V8 master prompts (6 lighting templates)

load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# ===================================================================
# MODULE 1: CONFIGURATION
# ===================================================================

# 7 DeepSeek API keys (1 per agent)
DEEPSEEK_KEYS = {}
for i in range(1, 8):
    key = os.getenv(f"DEEPSEEK_API_KEY_{i}")
    if key:
        DEEPSEEK_KEYS[i] = key
# Fallback: single key
if not DEEPSEEK_KEYS:
    single_key = os.getenv("DEEPSEEK_API_KEY")
    if single_key:
        for i in range(1, 8):
            DEEPSEEK_KEYS[i] = single_key

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL_REASONER = "deepseek-reasoner"
MODEL_CHAT = "deepseek-chat"

# Pollinations keys (primary + backup)
POLLINATIONS_KEYS = []
POLLINATIONS_BACKUP_KEYS = []
for k, v in os.environ.items():
    if k.startswith("POLLINATIONS_API_KEY_BCK_") and v and len(v) > 5:
        POLLINATIONS_BACKUP_KEYS.append(v)
    elif k.startswith("POLLINATIONS_API_KEY_") and v and len(v) > 5:
        POLLINATIONS_KEYS.append(v)

POLLINATIONS_MODEL = "klein-large"
POLLINATIONS_FALLBACK_MODEL = "klein"

if not POLLINATIONS_KEYS:
    POLLINATIONS_KEYS = [""]

# Directories
POSTS_DIR = os.path.join(PROJECT_ROOT, "posts")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# Limits
TARGET_WORD_COUNT = 2000
MIN_WORD_COUNT = 1600
MAX_RETRIES = 3
IMAGE_RETRY_MAX = 10
TOTAL_IMAGES = 6    # 1 cover + 5 content images
NUM_CONTENT_IMAGES = 5
SITE_BASE_URL = "https://littlesmartgenius.com"

# Batch config
DAILY_SLOTS = ["keyword", "product", "freebie"]
PAUSE_BETWEEN_ARTICLES = 30

# ── CONTENT DIVERSIFICATION ANGLES ──────────────────────────────────
# One angle is randomly injected into every article prompt to force
# a fundamentally different perspective, even on the same topic/series.
CONTENT_ANGLES = [
    "Focus on ONE specific age (pick randomly: 4, 5, 6, 7, 8, or 9) and tailor every tip, example, and anecdote exclusively to that age",
    "Structure the entire article around a 'Day in the Life' narrative — follow one family's morning-to-evening routine using this activity",
    "Compare-and-contrast angle: pit this activity against 2 alternative approaches and argue why this one wins",
    "Seasonal/holiday angle — tie every section to a specific season or upcoming holiday (pick one: summer, back-to-school, winter break, spring)",
    "Mistakes-first structure: open with the 5 biggest mistakes parents make with this activity, then solve each one",
    "Science-backed deep dive — cite 3+ different research studies throughout and make data the backbone of the article",
    "Budget-conscious angle — emphasize free and DIY alternatives alongside the resource, target cost-aware families",
    "Classroom teacher perspective — focus entirely on group activities, classroom management tips, and teacher workflows",
    "Reluctant learner angle — every single tip specifically targets kids who resist learning or get frustrated easily",
    "Multi-sensory approach — organize sections by sense (sight, touch, sound, movement) and tie each to a learning benefit",
    "Progress tracking angle — show parents exactly how to measure and celebrate growth over 4-6 weeks with concrete milestones",
    "Sibling/multi-age angle — every activity variation is designed for mixed age groups (e.g., 4-year-old + 8-year-old together)",
    "Travel and on-the-go — position every activity as portable: car rides, waiting rooms, restaurants, airplane trips",
    "Screen-time replacement — frame each section as a specific screen-free alternative to popular apps/games kids use",
    "Gift guide angle — frame the resource as a creative gift idea with wrapping, presentation, and surprise reveal tips",
    "Storytelling angle — weave a continuous fictional narrative of a child character throughout the entire article",
    "Challenge/gamification angle — turn every activity into a scored challenge, competition, or achievement system",
    "Parent-child bonding focus — emphasize togetherness, quality time, and emotional connection over pure academics",
    "Neurodiversity-inclusive angle — include specific adaptations for ADHD, dyslexia, and autism spectrum in every section",
    "Before-and-after transformation — structure around dramatic skill improvement stories with measurable results",
]

# Escalating Schedule — cron expression → slot mapping
# Used when GitHub Actions passes the exact cron that fired via --cron
CRON_TO_SLOT = {
    "0 8 * * *":   ("keyword", 1),     # Matin slot 1 — always
    "30 9 * * *":  ("product", 7),     # Matin slot 2 — week 7+
    "0 14 * * *":  ("product", 1),     # Après-midi slot 1 — always
    "30 15 * * *": ("keyword", 4),     # Après-midi slot 2 — week 4+
    "0 20 * * *":  ("freebie", 1),     # Soir slot 1 — always
    "30 21 * * *": ("keyword", 10),    # Soir slot 2 — week 10+
}

# Fallback: wide time windows (for manual --schedule without --cron)
SCHEDULE_SLOTS_FALLBACK = {
    (6, 13):  ("keyword", 1),     # Morning block
    (13, 19): ("product", 1),     # Afternoon block
    (19, 24): ("freebie", 1),     # Evening block
}

# 6 Personas (weighted)
PERSONAS = [
    {
        "id": "LSG_Admin",
        "role": "Little Smart Genius -- Founder & Lead Editor",
        "author_display": "Little Smart Genius",
        "expertise": "Curriculum design, educational publishing, content strategy for parents & educators",
        "tone": "Warm, authoritative, brand-native -- writes as the voice of the Little Smart Genius platform",
        "img_style": "bright, colorful educational scenes, 3D Pixar style, brand orange accents",
        "weight": 3
    },
    {
        "id": "Sarah_Mitchell",
        "role": "Sarah Mitchell -- Senior Content Creator & Elementary Teacher (15 years)",
        "author_display": "Sarah Mitchell",
        "expertise": "Classroom management, differentiated instruction, K-5 literacy & numeracy",
        "tone": "Warm, professional, evidence-based -- speaks from daily classroom experience",
        "img_style": "bright classroom, educational setting, 3D Pixar style",
        "weight": 1
    },
    {
        "id": "Dr_Emily_Carter",
        "role": "Dr. Emily Carter -- Child Development Advisor (PhD in Developmental Psychology)",
        "author_display": "Dr. Emily Carter",
        "expertise": "Cognitive development, learning psychology, executive function, screen-time research",
        "tone": "Authoritative, research-driven, accessible -- translates science into parent-friendly language",
        "img_style": "modern office, professional setting, clean 3D",
        "weight": 1
    },
    {
        "id": "Rachel_Nguyen",
        "role": "Rachel Nguyen -- Parenting & Montessori Specialist",
        "author_display": "Rachel Nguyen",
        "expertise": "Montessori at home, child-led learning, hands-on sensory activities, nature play",
        "tone": "Friendly, encouraging, practical -- speaks parent-to-parent with Montessori wisdom",
        "img_style": "cozy home learning space, warm colors, 3D illustration",
        "weight": 1
    },
    {
        "id": "David_Moreau",
        "role": "David Moreau -- Education & Pedagogy Specialist (M.Ed., 12 years)",
        "author_display": "David Moreau",
        "expertise": "Instructional design, differentiated pedagogy, formative assessment, project-based learning",
        "tone": "Clear, structured, methodical -- explains teaching strategies with precision and care",
        "img_style": "organized classroom, anchor charts, structured learning environment, 3D illustration",
        "weight": 1
    },
    {
        "id": "Lina_Bautista",
        "role": "Lina Bautista -- Educational Designer & Visual Learning Expert",
        "author_display": "Lina Bautista",
        "expertise": "Graphic design for education, worksheet UX, color psychology, visual scaffolding, gamification",
        "tone": "Creative, visual-thinking, enthusiastic -- sees learning through the lens of design and aesthetics",
        "img_style": "colorful design studio, art supplies, creative workspace, vibrant 3D illustration",
        "weight": 1
    },
]


# ===================================================================
# MODULE 2: DETAILED LOGGER (from V4)
# ===================================================================

class DetailedLogger:
    def __init__(self, article_slug: str):
        os.makedirs(LOGS_DIR, exist_ok=True)
        self.slug = article_slug
        self.log_file = os.path.join(LOGS_DIR, f"{article_slug}_{int(time.time())}.json")
        self.logs = {
            "slug": article_slug,
            "version": "V6-Ultimate",
            "start_time": datetime.now().isoformat(),
            "steps": [], "verifications": [], "corrections": [],
            "errors": [], "metrics": {}, "api_calls": [], "prompts": [],
            "quality_scores": {}, "images_generated": [],
            "api_config": {
                "text_provider": "DeepSeek",
                "text_model": MODEL_REASONER,
                "text_endpoint": DEEPSEEK_API_URL,
                "image_provider": "Pollinations",
                "image_model": POLLINATIONS_MODEL,
                "image_keys": f"{len(POLLINATIONS_KEYS)}/5 primary + {len(POLLINATIONS_BACKUP_KEYS)}/5 backup",
                "deepseek_keys": f"{len(DEEPSEEK_KEYS)}/7 active",
                "architecture": "7 AI Agents (parallel)"
            }
        }
        self.step_timers = {}
        self.current_step = None

    def banner(self, text: str, char: str = "="):
        print(f"\n{char*80}", flush=True)
        print(f"  {text}", flush=True)
        print(f"{char*80}", flush=True)

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
        print(f"{prefix}{icon} {message}", flush=True)

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
# MODULE 3: ASYNC DEEPSEEK CLIENT (deepseek-reasoner default)
# ===================================================================

async def call_deepseek_async(session, system_prompt, user_prompt, agent_id=1,
                               temperature=0.3, require_json=False, logger=None):
    """
    Async DeepSeek API call with key rotation per agent.
    Hybrid model strategy:
      - Agent 1 (Architect) & Agent 7 (Validator): deepseek-reasoner (deep analysis)
      - Agents 2-6 (Writers, Art, Assembler): deepseek-chat (speed + creativity)
      - JSON mode always uses deepseek-chat (reasoner doesn't support response_format)
    """
    all_keys = [DEEPSEEK_KEYS.get(i) for i in range(1, 8) if DEEPSEEK_KEYS.get(i)]
    if not all_keys:
        raise Exception("No DeepSeek API keys configured")

    # Hybrid model selection: reasoner for strategic agents, chat for creative/speed
    REASONER_AGENTS = {1, 7}  # Architect + Validator
    if require_json:
        model = MODEL_CHAT  # Reasoner doesn't support JSON response_format
    elif agent_id in REASONER_AGENTS:
        model = MODEL_REASONER  # Deep thinking for planning & auditing
    else:
        model = MODEL_CHAT  # Fast creative writing for writers/art/assembler

    # max_tokens: reasoner can output up to 64K, chat up to 8K
    max_tokens = 16384 if model == MODEL_REASONER else 8192

    start_idx = (agent_id - 1) % len(all_keys)
    max_retries = len(all_keys)
    last_error = None

    for attempt in range(max_retries):
        current_key = all_keys[(start_idx + attempt) % len(all_keys)]
        key_num = ((start_idx + attempt) % len(all_keys)) + 1

        headers = {
            "Authorization": f"Bearer {current_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if require_json:
            payload["response_format"] = {"type": "json_object"}

        try:
            t0 = time.time()
            async with session.post(DEEPSEEK_API_URL, headers=headers, json=payload,
                                     timeout=aiohttp.ClientTimeout(total=300)) as response:
                elapsed = round(time.time() - t0, 1)

                if response.status != 200:
                    text = await response.text()
                    last_error = f"HTTP {response.status}: {text[:100]}"
                    if logger:
                        logger.api_call(model, f"Key#{key_num}", False)
                    print(f"   [API WARNING] Key {key_num} failed: {response.status}. Trying next...")

                    # If reasoner fails, try chat as fallback
                    if model == MODEL_REASONER and attempt == 0:
                        model = MODEL_CHAT
                        print(f"   [API FALLBACK] Switching to {MODEL_CHAT}")
                    continue

                data = await response.json()
                msg = data['choices'][0]['message']
                content = msg.get('content') or msg.get('reasoning_content', '')

                if logger:
                    logger.api_call(model, f"Key#{key_num} Agent#{agent_id}", True, len(content))

                if require_json:
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.startswith("```"):
                        content = content[3:]
                    if content.endswith("```"):
                        content = content[:-3]
                    try:
                        return json.loads(content.strip())
                    except json.JSONDecodeError as e:
                        last_error = f"JSON Parse Error: {e}"
                        print(f"   [API ERROR] JSON parse failed, retrying...")
                        continue

                return content.strip()

        except asyncio.TimeoutError:
            last_error = "Timeout 300s"
            if logger:
                logger.api_call(model, f"Key#{key_num}", False)
            print(f"   [API WARNING] Timeout with Key {key_num}. Trying next...")
        except Exception as e:
            last_error = str(e)
            if logger:
                logger.api_call(model, f"Key#{key_num}", False)
            print(f"   [API WARNING] Exception with Key {key_num}: {e}. Trying next...")

    raise Exception(f"CRITICAL: All DeepSeek API keys failed. Last error: {last_error}")


def call_deepseek_sync(prompt: str, logger: DetailedLogger, prompt_type: str = "",
                       role: str = "content") -> Optional[str]:
    """Synchronous DeepSeek call (for SEO corrections). Uses single key."""
    key = DEEPSEEK_KEYS.get(1) or os.getenv("DEEPSEEK_API_KEY")
    if not key:
        logger.error("No DeepSeek API key available for sync call")
        return None

    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    for model in [MODEL_REASONER, MODEL_CHAT]:
        try:
            if logger and prompt_type:
                logger.show_prompt(prompt_type, prompt)

            resp = requests.post(DEEPSEEK_API_URL, headers=headers,
                                  json={"model": model, "messages": [{"role": "user", "content": prompt}]},
                                  timeout=300)
            if resp.status_code == 200:
                data = resp.json()
                msg = data["choices"][0]["message"]
                text = msg.get("content") or msg.get("reasoning_content", "")
                if text and len(text.strip()) >= 10:
                    if logger:
                        logger.api_call(model, role, True, len(text))
                    return text.strip()
            elif resp.status_code == 402:
                logger.error("DeepSeek insufficient balance (402)")
                return None
        except Exception as e:
            if logger:
                logger.api_call(model, role, False)

    return None


# ===================================================================
# MODULE 4: AUTOBLOG V6 CLASS — 7 AGENTS PARALLEL PIPELINE
# ===================================================================

class SEOUtils:
    """Static SEO helper methods (from V4)."""
    @staticmethod
    def optimize_slug(title: str) -> str:
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug).strip('-')
        return slug[:80]

    @staticmethod
    def calculate_reading_time(content: str) -> int:
        word_count = len(re.findall(r'\w+', re.sub(r'<[^>]+>', '', content)))
        return max(1, word_count // 200)

    @staticmethod
    def extract_keywords(title: str, content: str) -> List[str]:
        """Extract meaningful 2-3 word long-tail keyword phrases (bigrams + trigrams)."""
        text = re.sub(r'<[^>]+>', '', f"{title} {content}").lower()
        words = re.findall(r'\b[a-z]{3,}\b', text)
        
        # Extensive stop words — filter out all generic/common terms
        stop = {
            'the', 'and', 'for', 'that', 'this', 'with', 'from', 'have', 'been',
            'your', 'they', 'them', 'when', 'will', 'more', 'each', 'also', 'about',
            'into', 'like', 'make', 'some', 'very', 'than', 'even', 'most', 'much',
            'such', 'only', 'many', 'over', 'well', 'here', 'then', 'right', 'look',
            'every', 'good', 'give', 'keep', 'help', 'think', 'just', 'what', 'their',
            'first', 'where', 'could', 'would', 'should', 'which', 'there', 'other',
            'after', 'before', 'still', 'while', 'really', 'great', 'these', 'those',
            'start', 'things', 'being', 'does', 'doesn', 'didn', 'aren', 'isn', 'was',
            'were', 'are', 'has', 'had', 'not', 'but', 'can', 'all', 'one', 'two',
            'you', 'our', 'how', 'its', 'get', 'got', 'let', 'say', 'see', 'way',
            'new', 'now', 'use', 'may', 'try', 'too', 'own', 'why', 'put', 'old',
            'big', 'few', 'end', 'ask', 'run', 'need', 'know', 'want', 'come', 'take',
            'work', 'going', 'using', 'because', 'through', 'between', 'different',
            'another', 'something', 'anything', 'everything', 'without', 'during',
        }
        
        filtered = [w for w in words if w not in stop and len(w) >= 3]
        
        # Build bigrams and trigrams
        from collections import Counter
        bigrams = [f"{filtered[i]} {filtered[i+1]}" for i in range(len(filtered)-1)]
        trigrams = [f"{filtered[i]} {filtered[i+1]} {filtered[i+2]}" for i in range(len(filtered)-2)]
        
        # Count frequencies
        bi_freq = Counter(bigrams)
        tri_freq = Counter(trigrams)
        
        # Combine and sort by frequency
        all_phrases = {}
        for phrase, count in tri_freq.items():
            if count >= 2:
                all_phrases[phrase] = count * 1.5  # Boost trigrams
        for phrase, count in bi_freq.items():
            if count >= 2 and phrase not in all_phrases:
                all_phrases[phrase] = count
        
        sorted_phrases = sorted(all_phrases.items(), key=lambda x: x[1], reverse=True)
        result = [phrase for phrase, _ in sorted_phrases[:10]]
        
        # Fallback: if not enough phrases found, use best bigrams regardless of frequency
        if len(result) < 5:
            for phrase, count in bi_freq.most_common(20):
                if phrase not in result:
                    result.append(phrase)
                if len(result) >= 10:
                    break
        
        return result[:10]

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
    def generate_seo_alt_text(concept: str, context: str) -> str:
        alt = f"{concept} {context}"
        alt = re.sub(r'[^a-zA-Z0-9\s-]', '', alt)
        alt = re.sub(r'\s+', '-', alt)
        return alt.lower()[:125]


class AutoBlogV6:
    """V6 Ultimate Multi-Agent Engine."""

    def __init__(self, slot, topic, persona, logger, used_topics_ref=None):
        self.slot = slot
        self.topic_name = topic["topic_name"]
        self.category = topic["category"]
        self.keywords = topic["keywords"]
        self.product_data = topic.get("product_data")
        self.persona = persona
        self.logger = logger
        self.used_topics_ref = used_topics_ref or {}  # For series-aware diversification
        self.plan = None
        self.content_builder_fn = None
        self.html_sections = []
        self.image_prompts = []
        self.image_paths = []
        self.final_content = ""

    async def run_pipeline(self):
        """Full V6 multi-agent pipeline."""
        self.logger.banner("AUTO BLOG V6 ULTIMATE -- MULTI-AGENT PIPELINE", "=")
        print(f"Topic: {self.topic_name}")
        print(f"Slot: {self.slot} | Persona: {self.persona['role'][:50]}")
        print(f"Category: {self.category}")
        print(f"Architecture: 7 Agents HYBRID (reasoner: Agent 1+7 | chat: Agent 2-6)", flush=True)
        print(f"Start: {datetime.now().strftime('%H:%M:%S')}", flush=True)

        async with aiohttp.ClientSession() as session:
            # === PHASE 1: ARCHITECT (sequential) ===
            self.logger.step_start("PHASE 1/8: ARCHITECT", "Agent 1 builds JSON plan")
            await self.agent_1_architect(session)
            self.logger.step_end("PHASE 1/8: ARCHITECT")

            # === PHASE 2: WRITERS + ART DIRECTOR (parallel) ===
            self.logger.step_start("PHASE 2/8: WRITERS + ART DIRECTOR",
                                    "3 Writers + 1 Art Director in parallel")

            total_sections = len(self.plan.get('sections', []))
            if total_sections < 3:
                chunks = [self.plan['sections']]
            else:
                chunk_size = total_sections // 3
                rem = total_sections % 3
                chunks = []
                idx = 0
                for i in range(3):
                    sz = chunk_size + (1 if i < rem else 0)
                    chunks.append(self.plan['sections'][idx:idx+sz])
                    idx += sz

            writer_tasks = []
            for i, chunk in enumerate(chunks):
                if chunk:
                    writer_tasks.append(self.agent_seo_writer(session, i+1, chunk))

            art_task = self.agent_5_art_director(session)
            results = await asyncio.gather(*writer_tasks, art_task)

            writer_results = results[:-1]
            self.image_prompts = results[-1]
            writer_results.sort(key=lambda x: x[0])
            self.html_sections = [res[1] for res in writer_results]

            self.logger.metric("Writers completed", len(writer_results))
            self.logger.metric("Image prompts", len(self.image_prompts))
            self.logger.step_end("PHASE 2/8: WRITERS + ART DIRECTOR")

            # === PHASE 2.5: KEY VALIDATION ===
            self.logger.step_start("PHASE 2.5/8: KEY VALIDATION", "Checking balances to prioritize keys with most pollen")
            await self.validate_and_sort_image_keys(session)
            self.logger.step_end("PHASE 2.5/8: KEY VALIDATION")

            # === PHASE 3: IMAGES (parallel) ===
            self.logger.step_start("PHASE 3/8: IMAGE GENERATION",
                                    f"5 images, 8 attempts each, {len(POLLINATIONS_KEYS)} primary + {len(POLLINATIONS_BACKUP_KEYS)} backup keys")
            self.image_paths = await self.artists_generate_images(session)
            self.logger.step_end("PHASE 3/8: IMAGE GENERATION")

            # === PHASE 4: ASSEMBLER (sequential) ===
            self.logger.step_start("PHASE 4/8: ASSEMBLER", "Agent 6 merges + harmonizes")
            await self.agent_6_assembler(session)
            self.logger.step_end("PHASE 4/8: ASSEMBLER")

            # === PHASE 5: HUMANIZER (self-review pass) ===
            self.logger.step_start("PHASE 5/8: HUMANIZER", "Agent 8 — human self-review pass")
            await self.agent_8_humanizer(session)
            self.logger.step_end("PHASE 5/8: HUMANIZER")

            # === PHASE 6: POST-PROCESSING (V4 ecosystem) ===
            self.logger.step_start("PHASE 6/8: POST-PROCESSING", "SmartLinker + FAQ + CTA")
            self.post_process()
            self.logger.step_end("PHASE 6/8: POST-PROCESSING")

            # === PHASE 7: SEO AUDIT (60 criteria) ===
            self.logger.step_start("PHASE 7/8: SEO AUDIT (60 criteria)",
                                    "Agent 7 (50 AI) + 10 local checks + corrections")
            seo_score = await self.phase_6_seo_audit(session)
            self.logger.step_end("PHASE 7/8: SEO AUDIT (60 criteria)")

            # === PHASE 8: SAVE + INSTAGRAM ===
            self.logger.step_start("PHASE 8/8: SAVE + SYNDICATION", "JSON + Instagram + Webhook")
            final_data = self.compile_and_save()
            self.logger.step_end("PHASE 8/8: SAVE + SYNDICATION")

            self.logger.save()
            return final_data

    # --- AGENT 1: ARCHITECT ---
    async def agent_1_architect(self, session):
        # ── Select random content angle for diversification ──
        angle = random.choice(CONTENT_ANGLES)
        self.logger.info(f"Content angle selected: {angle[:80]}...")

        # ── Build series context (same-series product awareness) ──
        series_context = ""
        if self.slot == "product" and self.used_topics_ref:
            base_name = re.sub(r'\|.*$', '', self.topic_name).strip()
            used_products = self.used_topics_ref.get("product", [])
            same_series = [p for p in used_products if base_name in p and p != self.topic_name]
            if same_series:
                series_context = (
                    "\n\n⚠️ CRITICAL DIVERSIFICATION — SAME SERIES ALERT:\n"
                    "Articles ALREADY EXIST for these products in the same series:\n"
                    + "\n".join(f"  • {p}" for p in same_series)
                    + "\n\nYou MUST create a COMPLETELY DIFFERENT article:\n"
                    "- Use a DIFFERENT title structure and angle\n"
                    "- Use DIFFERENT H2 section topics and ordering\n"
                    "- Use DIFFERENT intro scenarios, anecdotes, and FAQ questions\n"
                    "- Target at least 70% unique content vs what those articles would contain\n"
                    "- Pick a DIFFERENT primary educational benefit to emphasize"
                )
                self.logger.info(f"Series context: {len(same_series)} same-series articles detected")

        prompt_builder = get_prompt_builder(self.slot)
        if self.slot == "product" or self.slot == "freebie":
            prompts = prompt_builder(self.product_data, self.persona, angle=angle, series_context=series_context)
        else:
            prompts = prompt_builder(self.topic_name, self.persona, angle=angle, series_context=series_context)

        self.content_builder_fn = prompts['content_prompt_builder']

        system_prompt = "You are Agent 1, the Master Architect. Return ONLY valid JSON."
        self.plan = await call_deepseek_async(
            session, system_prompt, prompts['plan_prompt'],
            agent_id=1, temperature=1.0, require_json=True, logger=self.logger
        )

        if 'primary_keyword' not in self.plan:
            self.plan['primary_keyword'] = self.topic_name

        # Enforce minimum 6 sections
        if 'sections' in self.plan:
            while len(self.plan['sections']) < 6:
                idx = len(self.plan['sections']) + 1
                self.plan['sections'].append({
                    "h2": f"Additional Tips for {self.plan['primary_keyword']} (Part {idx})",
                    "h3_subsections": ["Why Consistency Matters", "Long-term Benefits", "Expert Advice"],
                    "key_points": ["Establish a routine", "Track progress over time", "Make learning enjoyable"],
                    "image_concept": "A bright educational setting with a child engaged in learning",
                    "internal_link_opportunity": "Click here for more educational resources"
                })

        self.logger.metric("Plan sections", len(self.plan.get('sections', [])))
        self.logger.metric("Plan FAQ", len(self.plan.get('faq', [])))

    # --- AGENTS 2/3/4: SEO WRITERS ---
    async def agent_seo_writer(self, session, writer_id, sections_chunk):
        print(f"   [AGENT {writer_id+1}] Writing {len(sections_chunk)} sections...")

        partial_plan = dict(self.plan)
        partial_plan['sections'] = sections_chunk

        base_prompt = self.content_builder_fn(partial_plan, target_words=2000)

        system_prompt = f"""You are SEO Writer #{writer_id}. You are part of a 3-agent team.
YOUR SOLE JOB is to write the specific sections assigned to you below in HTML format.

ASSIGNED SECTIONS TO WRITE:
{json.dumps([s.get('h2') for s in sections_chunk], indent=2)}

CRITICAL RULES:
1. ONLY return the HTML (<h2>, <h3>, <p>, <ul>) for your assigned sections.
2. DO NOT write the Introduction (unless you are Writer 1 and it's in your prompt).
3. DO NOT write the Conclusion or FAQ (unless you are Writer 3).
4. Do NOT output markdown code blocks. Just the raw HTML.
5. Apply the strictest 'Anti-AI' humanization rules from your instructions.
6. Use varied paragraph lengths, conversational tone, NO AI phrases."""

        user_prompt = f"""{base_prompt}

Now, WRITE YOUR ASSIGNED SECTIONS ONLY. Remember: varied paragraph lengths, conversational tone, NO AI phrases."""

        agent_id = writer_id + 1
        html_output = await call_deepseek_async(
            session, system_prompt, user_prompt,
            agent_id=agent_id, temperature=1.5, logger=self.logger
        )

        html_output = re.sub(r'```html|```', '', html_output).strip()
        word_count = len(re.findall(r'\w+', re.sub(r'<[^>]+>', '', html_output)))
        print(f"   [AGENT {writer_id+1}] Done! ({word_count} words)")
        return (writer_id, html_output)

    # --- AGENT 5: ART DIRECTOR (V8 MASTER PROMPT INTEGRATION) ---
    async def agent_5_art_director(self, session):
        print("   [AGENT 5] Art Director drafting 6 image prompts (V8 master templates)...")

        # V8 Art Director System Prompt — contains all user directives:
        # - Joyful/happy/glowing smiles on ALL characters
        # - No tongues sticking out
        # - Mix of children AND parents/teachers
        # - Specific tangible educational props
        # - Warm cozy environment with sunlight
        ART_DIRECTOR_SYSTEM_V8 = (
            "You are an expert Art Director for educational children's content. "
            "Your ONLY job is to return a highly descriptive, unique, and highly creative subject text (around 60 to 90 words). "
            "This text will replace the [SUJET] placeholder in a film-grade Pixar template. "
            "You MUST be extremely creative. Each image in the article must have a completely distinct scene, action, "
            "and materials based specifically on the provided H2 Section Context. "
            "CRITICAL REQUIREMENTS:\n"
            "1. All characters (children AND adults) MUST be explicitly described as joyful, happy, and having glowing smiles.\n"
            "2. NO characters should have their tongues sticking out (mouths closed or gently smiling).\n"
            "3. IMPORTANT: Include a mix of characters. Do not only feature children. Frequently include a parent or a teacher actively enthusiastically playing, guiding, or cooperating with the kids.\n"
            "4. Detail specific, tangible, interactive educational props (e.g., holding a shiny magnifying glass, assembling large colorful floor puzzles, moving pieces on a board game, coloring on vibrant worksheets).\n"
            "5. Emphasize a warm, cozy, highly detailed classroom or home environment with sunlight streaming in.\n"
            "6. DO NOT output full prompts, lighting terminology, or style formatting. DO NOT include 'Pixar', '3D', 'Golden hour', etc.\n"
            "7. DIVERSIFY compositions based on your assigned 'Role'. If assigned a wide shot, show the environment AND people. If assigned a flat-lay or detailed shot, focus tightly on HANDS and MATERIALS from an overhead/bird's-eye or close-up perspective, explicitly mentioning hands holding tools.\n"
            "Just describe the specific unique characters (or just hands), their activity with props, and their surroundings."
        )

        # V8 Image Roles for variety (Updated for extreme composition diversity)
        IMAGE_ROLES = [
            "Image 1 (Cover): Wide shot of children/parents engaged in activity (current style)",
            "Image 2: CLOSE-UP flat-lay of hands working on the worksheet/puzzle (bird's-eye angle, focus on hands and materials)",
            "Image 3: OVERHEAD shot of multiple children's hands collaborating on a shared activity page",
            "Image 4: DETAIL SHOT of the actual educational material with art supplies around (colored pencils, scissors)",
            "Image 5: Close-up of a child's hands interacting with a specific prop (puzzle piece, game board, coloring page)",
            "Image 6: Wide or medium shot showing the learning environment with visible worksheets on the table",
        ]

        # Gather section contexts from the plan
        concepts = [self.plan.get('cover_concept', f'Educational illustration about {self.topic_name}')]
        for s in self.plan.get('sections', []):
            if 'image_concept' in s:
                concepts.append(s['image_concept'])

        # Ensure we have exactly 6 concepts (1 cover + 5 inline)
        while len(concepts) < 6:
            concepts.append(f"Educational activity scene related to {self.topic_name}")
        concepts = concepts[:6]

        tasks = []
        for i, concept in enumerate(concepts):
            role = IMAGE_ROLES[i % len(IMAGE_ROLES)]
            user_prompt = (
                f"Article Title: {self.plan.get('title', self.topic_name)}\n"
                f"Context: {concept}\n"
                f"Role: {role}\n\n"
                f"Write the ~60-90 word unique children's activity description:"
            )
            tasks.append(call_deepseek_async(
                session, ART_DIRECTOR_SYSTEM_V8, user_prompt,
                agent_id=5, temperature=1.5, logger=self.logger
            ))

        raw_prompts = await asyncio.gather(*tasks, return_exceptions=True)

        # Validate and wrap each subject with the master prompt template
        validated_prompts = []
        for i, (subject, concept) in enumerate(zip(raw_prompts, concepts)):
            if isinstance(subject, Exception) or not subject or len(str(subject).strip()) < 20:
                # Fallback subject if art director fails
                fallback_subject = (
                    f"a group of joyful, diverse children and a smiling teacher "
                    f"engaged in {concept} activities together, carefully placing "
                    f"pieces and smiling, in a warm cozy classroom with sunlight streaming in"
                )
                self.logger.warning(f"Agent 5 prompt #{i+1} invalid -- using fallback", 3)
                subject_text = fallback_subject
            else:
                subject_text = str(subject).strip().strip('"').strip("'")
                # Clean out any leaked instructions (Pixar, 3D, etc.)
                import re as _re
                for bad in ["3D", "Pixar", "Disney", "Golden hour", "lighting", "shadow"]:
                    if bad.lower() in subject_text.lower():
                        subject_text = _re.sub(_re.escape(bad), '', subject_text, flags=_re.IGNORECASE).strip()
                subject_text = _re.sub(r'\s+', ' ', subject_text).strip(' ,.')

            # Wrap with the master prompt template for this image index
            full_prompt = master_build_prompt(subject_text, image_index=i)
            validated_prompts.append(full_prompt)

        ai_ok = sum(1 for p in raw_prompts if not isinstance(p, Exception) and p and len(str(p)) >= 20)
        ai_fail = sum(1 for p in raw_prompts if isinstance(p, Exception) or not p or len(str(p)) < 20)
        print(f"   [AGENT 5] 6 Prompts validated ({ai_ok} AI + {ai_fail} fallback). Master templates applied.")
        return validated_prompts

    # --- MODULE 6: IMAGE PIPELINE (8 attempts + hybrid fallback) ---
    async def fetch_and_save_image(self, session, prompt, idx):
        width, height = 1200, 675  # Consistent landscape 16:9 for all images (cover + content)
        seed = int(time.time()) + idx * 100
        # Append strict no-text instruction to every prompt
        no_text_suffix = ", ABSOLUTELY NO text, letters, words, numbers, titles, captions, labels, watermarks, or UI overlays in the image, pure visual storytelling only"
        clean_prompt = re.sub(r'[^a-zA-Z0-9 ,.-]', '', prompt + no_text_suffix)
        encoded_prompt = urllib.parse.quote(clean_prompt)

        slug = SEOUtils.optimize_slug(self.plan.get('title', self.topic_name))
        ts = int(time.time())
        suffix = "cover" if idx == 0 else f"img{idx}"
        out_name = f"{slug}-{suffix}-{ts}.webp"
        out_path = os.path.join(IMAGES_DIR, out_name)
        os.makedirs(IMAGES_DIR, exist_ok=True)

        for attempt in range(IMAGE_RETRY_MAX):
            # Key rotation: first 3 attempts with primary keys, then backup
            if attempt < 3 and POLLINATIONS_KEYS:
                api_key = POLLINATIONS_KEYS[(idx + attempt) % len(POLLINATIONS_KEYS)]
            elif POLLINATIONS_BACKUP_KEYS:
                backup_idx = (idx + attempt) % len(POLLINATIONS_BACKUP_KEYS)
                api_key = POLLINATIONS_BACKUP_KEYS[backup_idx]
            else:
                api_key = POLLINATIONS_KEYS[0] if POLLINATIONS_KEYS else None

            # Use V4's working URL format: gen.pollinations.ai/image/
            url = f"https://gen.pollinations.ai/image/{encoded_prompt}"
            # Primary model for first half of attempts, fallback for second half
            current_model = POLLINATIONS_MODEL if attempt < (IMAGE_RETRY_MAX // 2) else POLLINATIONS_FALLBACK_MODEL
            if attempt == (IMAGE_RETRY_MAX // 2):
                self.logger.warning(f"Image {idx+1}: switching to fallback model '{POLLINATIONS_FALLBACK_MODEL}'", 3)
            params = {
                "width": width, "height": height, "seed": seed,
                "model": current_model, "nologo": "true", "enhance": "true"
            }
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            try:
                async with session.get(url, params=params, headers=headers,
                                        timeout=aiohttp.ClientTimeout(total=90)) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        if len(data) > 1024:
                            img = Image.open(BytesIO(data)).convert("RGB")
                            img.thumbnail((1200, 1200))  # cap size like V4
                            img.save(out_path, "WEBP", quality=85, optimize=True, method=6)
                            
                            # Auto-generate lightweight thumbnail for cover images only
                            if idx == 0:
                                thumbs_dir = os.path.join(os.path.dirname(out_path), "thumbs")
                                os.makedirs(thumbs_dir, exist_ok=True)
                                thumb_path = os.path.join(thumbs_dir, os.path.basename(out_path))
                                if img.width > 600:
                                    aspect_ratio = img.height / img.width
                                    new_height = int(600 * aspect_ratio)
                                    thumb_img = img.resize((600, new_height), Image.LANCZOS)
                                else:
                                    thumb_img = img.copy()
                                thumb_img.save(thumb_path, "WEBP", quality=80, optimize=True)
                                
                            size_kb = os.path.getsize(out_path) // 1024
                            self.logger.image_saved(out_name, size_kb)
                            self.logger.success(f"Image {idx+1} saved ({size_kb}KB) attempt {attempt+1}", 3)
                            return f"images/{out_name}"
                    else:
                        self.logger.warning(f"Image {idx+1}, attempt {attempt+1}: HTTP {resp.status}", 3)
            except Exception as e:
                self.logger.warning(f"Image {idx+1}, attempt {attempt+1}: {str(e)[:50]}", 3)
                await asyncio.sleep(3)
                seed += 1

        # HYBRID FALLBACK: placeholder instead of abort
        self.logger.warning(f"Image {idx+1}: all {IMAGE_RETRY_MAX} attempts failed -- using placeholder", 2)
        return "https://placehold.co/1200x675/F48C06/FFFFFF/png?text=Smart+Genius"

    async def validate_and_sort_image_keys(self, session):
        global POLLINATIONS_KEYS, POLLINATIONS_BACKUP_KEYS
        all_keys = list(set(POLLINATIONS_KEYS + POLLINATIONS_BACKUP_KEYS))
        if not all_keys or all_keys == [""]:
            return
        
        async def check_balance(key):
            try:
                url = "https://gen.pollinations.ai/account/balance"
                headers = {"User-Agent": "Mozilla/5.0", "Authorization": f"Bearer {key}"}
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return key, float(data.get("balance", 0.0))
            except Exception:
                pass
            return key, 0.0

        tasks = [check_balance(k) for k in all_keys]
        results = await asyncio.gather(*tasks)
        
        valid_keys = [(k, bal) for k, bal in results if bal > 0]
        valid_keys.sort(key=lambda x: x[1], reverse=True)
        
        if valid_keys:
            sorted_keys = [k for k, bal in valid_keys]
            POLLINATIONS_KEYS = sorted_keys[:5]
            POLLINATIONS_BACKUP_KEYS = sorted_keys[5:]
            self.logger.success(f"Validated {len(valid_keys)} keys with pollen. Top balance: {valid_keys[0][1]:.2f}", 2)
        else:
            self.logger.warning("No Pollinations keys with pollen balance found (all 0). HTTP 402 likely.", 2)

    async def artists_generate_images(self, session):
        # Generate all images (6: 1 cover + 5 inline) — prompts already wrapped with master templates
        tasks = [self.fetch_and_save_image(session, p, i) for i, p in enumerate(self.image_prompts)]
        return await asyncio.gather(*tasks)

    # --- AGENT 6: ASSEMBLER ---
    async def agent_6_assembler(self, session):
        raw_html = "\n".join(self.html_sections)

        images_info = f"Cover Image: <img src='../{self.image_paths[0]}' alt='Cover' class='w-full rounded-2xl mb-8'>\n"
        for i in range(1, 6):  # indices 1..5 = 5 content images (index 0 is cover)
            path = self.image_paths[i] if i < len(self.image_paths) else "images/placeholder.webp"
            alt = SEOUtils.generate_seo_alt_text(
                self.image_prompts[i][:100] if i < len(self.image_prompts) else "",
                self.topic_name
            )
            images_info += f"[IMAGE_{i}]: <figure class='my-8'><img src='../{path}' alt='{alt} - {self.plan.get("primary_keyword", self.topic_name)}' loading='lazy' width='1200' height='675' class='w-full rounded-xl shadow-md'></figure>\n"

        sys_prompt = """You are Agent 6, the Chief Editor and Assembler.
Your job is to take raw drafted sections and merge them into a single, cohesive, perfectly flowing article in HTML.

ASSEMBLY RULES:
1. Harmonize the tone so it sounds like ONE single passionate human author.
2. Ensure transitions between sections are smooth and natural.
3. Replace the 5 placeholders [IMAGE_1] through [IMAGE_5] with the provided image tags INSIDE the body content.
4. SPACING RULE: Place images EVENLY across the article — roughly every 300-400 words. NEVER place two images back-to-back or adjacent without text in between. There must be at least one full paragraph (≥3 sentences) separating any two images.
5. DO NOT change the core meaning or remove keywords.
6. Provide ONLY the inner HTML elements (e.g. <h2>, <p>, <ul>). NEVER output <!DOCTYPE html>, <html>, <head>, <style>, or <body> tags.
7. DO NOT include the cover image — it is already displayed separately above the article. Only use [IMAGE_1] through [IMAGE_5] for inline content images.
8. DO NOT include a 'You Might Also Like', related articles, or FAQ section — these are injected separately.

HUMANIZATION RULES (CRITICAL — check during assembly):
9. VOICE CONSISTENCY: The entire article must sound like ONE real person talking. If sections have different tones (one formal, one casual), normalize to the more conversational one.
10. CONTRACTIONS: Ensure contractions are used throughout (you'll, it's, don't, they're). Replace any "it is", "do not", "you will" with contractions.
11. SENTENCE RHYTHM: Check that no paragraph has 3+ sentences of similar length. If found, break a long one or merge two short ones.
12. RHETORICAL QUESTIONS: Ensure the article has at least 3 rhetorical questions across all sections (outside FAQ). If missing, add 1-2 natural ones.
13. EM-DASH ASIDES: Ensure at least 2 em-dash asides exist (– like this –). If missing, add them where natural.
14. PARAGRAPH VARIETY: Vary paragraph lengths — some should be 1-2 sentences, others 4-5. Never make all paragraphs the same length.
15. BANNED AI PHRASES: NEVER use any of these phrases anywhere in the output, and REPLACE them if found in the draft sections: 'Moreover', 'Furthermore', 'Additionally', 'It's worth noting', 'It's worth mentioning', 'When it comes to', 'In terms of', 'This is particularly', 'This is especially', 'Plays a crucial role', 'Plays a vital role', 'It should be noted', 'It is essential', 'In order to', 'A wide range of', 'Undoubtedly', 'Undeniably', 'Holistic approach', 'Seamless integration', 'In today's world', 'Let's explore', 'Let's take a look', 'In essence', 'Cornerstone', 'Beacon of', 'Testament to'. Replace with natural human transitions like 'Plus', 'On top of that', 'Here's the thing', 'The best part?', 'Honestly', 'Real talk'."""

        user_prompt = f"""IMAGES TO INJECT:
{images_info}

RAW DRAFT SECTIONS:
{raw_html}

Please assemble the final HTML article now. Ensure all [IMAGE_X] placeholders are replaced."""

        self.final_content = await call_deepseek_async(
            session, sys_prompt, user_prompt,
            agent_id=6, temperature=1.3, logger=self.logger
        )

        self.final_content = re.sub(r'```html|```', '', self.final_content).strip()

        # Failsafe: force-inject images if assembler missed them
        img_count = len(re.findall(r'<img[^>]+>', self.final_content))
        if img_count == 0 and self.image_paths:
            self.logger.warning("No images detected -- force-injecting at H2 boundaries", 2)
            h2_positions = [m.start() for m in re.finditer(r'<h2[^>]*>', self.final_content)]
            for idx in range(min(5, len(h2_positions), len(self.image_paths)-1)): # 5 content images
                img_path = self.image_paths[idx+1]
                img_tag = f'<figure class="article-image"><img src="../{img_path}" alt="educational illustration" loading="lazy" width="1200" height="675"></figure>\n'
                pos = h2_positions[idx]
                self.final_content = self.final_content[:pos] + img_tag + self.final_content[pos:]
                h2_positions = [m.start() for m in re.finditer(r'<h2[^>]*>', self.final_content)]

        self.final_content = re.sub(r'\[IMAGE_\d+\]', '', self.final_content)
        self.logger.success("Assembly complete — HTML unified and 6 images injected", 2)

    # ===============================================================
    # AGENT 8: HUMANIZER — Self-Review Humanization Pass
    # ===============================================================

    async def agent_8_humanizer(self, session):
        """Agent 8: Make the article sound more human. Second-pass rewrite focused on
        sentence rhythm, syntactic variety, and natural voice — without changing facts."""

        self.logger.step_start("AGENT 8: HUMANIZER", "Self-review humanization pass")

        content_preview = self.final_content[:12000]
        word_count = len(re.sub(r'<[^>]+>', '', self.final_content).split())

        prompt = f"""You are a HUMAN EDITOR reviewing a blog article. Your ONLY job is to make this text sound
MORE like a real human blogger wrote it. You must NOT change the facts, structure, keywords, HTML tags, links, or images.

═══ YOUR REVIEW CHECKLIST ═══

1. SENTENCE RHYTHM:
   - Scan every paragraph. If you see 3+ sentences in a row with similar length (±5 words), 
     break one long sentence into two, or merge two short ones.
   - Ensure each paragraph has a MIX of short (3-7 words), medium (10-18 words), 
     and occasional long sentences (20-30+ words).

2. SENTENCE OPENINGS:
   - Scan for paragraphs where 2+ sentences start the same way (e.g., "This...", "The...", "It...").
   - Rewrite one of them to start differently (gerund, question, prepositional phrase, fragment).

3. CONVERSATIONAL TONE:
   - Replace any stiff or academic phrasing with casual equivalents.
     "It is recommended that" → "You'll want to"
     "Children tend to" → "Most kids"
     "This can be beneficial" → "This really helps"
     "It is advisable to" → "Try to"
   - Add contractions where natural (it is → it's, you will → you'll, do not → don't).

4. MICRO-ANECDOTES:
   - Where the text feels generic or reads like a textbook, add a quick personal comment
     (1 sentence max). Example: "I've seen this work wonders with my 6-year-old."
   - Do NOT add more than 3-4 new micro-comments total. Keep them short.

5. RHETORICAL QUESTIONS:
   - If the article has fewer than 3 rhetorical questions total, add 1-2 natural ones.
     Example: "So what makes this different?" or "Sound familiar?"

6. NATURAL TOUCHES:
   - Ensure at least 2 em-dash asides exist (– like this –).
   - Ensure at least 2 informal expressions exist ("no-brainer", "this one's a keeper", etc.).
   - Vary paragraph lengths: short (1-2 sentences) mixed with longer (4-5 sentences).

═══ STRICT RULES ═══
- Do NOT add or remove any <h2>, <h3>, <img>, <a>, <div> tags.
- Do NOT change any URLs, image paths, or link text.
- Do NOT remove keywords or change keyword density significantly.
- Do NOT add any <html>, <head>, <body>, <style>, or <!DOCTYPE> tags.
- Do NOT shorten the article. Keep the word count within ±5% of {word_count} words.
- Return ONLY the revised HTML content. No explanations, no markdown.

═══ ARTICLE TO HUMANIZE ═══
{content_preview}"""

        if len(self.final_content) > 12000:
            prompt += f"\n\n... [CONTINUED — full article is {word_count} words] ...\n"
            prompt += f"\n{self.final_content[12000:]}"

        try:
            system_prompt = "You are Agent 8, the Humanizer. Your job is to rewrite this article to sound indistinguishable from a human-written piece. Follow the rules exactly. Return ONLY the revised HTML."
            result = await call_deepseek_async(
                session, system_prompt, prompt,
                agent_id=8, temperature=1.5, logger=self.logger
            )

            if result and len(result) > len(self.final_content) * 0.8:
                # Verify the humanized version still has essential elements
                original_h2s = len(re.findall(r'<h2[^>]*>', self.final_content))
                new_h2s = len(re.findall(r'<h2[^>]*>', result))
                original_imgs = len(re.findall(r'<img[^>]*>', self.final_content))
                new_imgs = len(re.findall(r'<img[^>]*>', result))

                if new_h2s >= original_h2s - 1 and new_imgs >= original_imgs - 1:
                    self.final_content = result.strip()
                    new_word_count = len(re.sub(r'<[^>]+>', '', self.final_content).split())
                    self.logger.success(
                        f"Humanization pass complete: {word_count} → {new_word_count} words, "
                        f"{new_h2s} H2s, {new_imgs} images preserved", 2
                    )
                else:
                    self.logger.warning(
                        f"Humanizer output rejected: lost structure (H2: {original_h2s}→{new_h2s}, "
                        f"imgs: {original_imgs}→{new_imgs}). Keeping original.", 2
                    )
            else:
                self.logger.warning("Humanizer returned insufficient content. Keeping original.", 2)

        except Exception as e:
            self.logger.warning(f"Humanizer failed: {str(e)[:60]}. Keeping original.", 2)

        self.logger.step_end("AGENT 8: HUMANIZER")

    # --- PHASE 5: POST-PROCESSING ---
    def post_process(self):
        # Smart Linking
        slug = SEOUtils.optimize_slug(self.plan['title'])
        smart_linker = SmartLinker()
        self.final_content = smart_linker.inject_smart_links(
            self.final_content, self.plan['title'], self.category,
            self.keywords, slug, self.logger
        )

        # CTA Box
        if self.slot == "product" and self.product_data:
            self.final_content += f"""
<div class="cta-box" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 15px; margin: 30px 0; text-align: center;">
    <h3 style="color: white; margin-bottom: 15px;">Ready to Enhance Your Teaching?</h3>
    <p style="color: white; margin-bottom: 20px;">Explore our premium educational resources:</p>
    <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
        <a href="{self.product_data['url']}" target="_blank" rel="noopener" style="background: white; color: #667eea; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold;">{self.product_data['name'][:50]}</a>
        <a href="{SITE_BASE_URL}/freebies.html" style="background: #F48C06; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold;">Get Free Resources</a>
    </div>
</div>"""
        elif self.slot == "freebie" and self.product_data:
            if '<div class="download-cta"' not in self.final_content:
                self.final_content += f"""
<div class="download-cta" style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); padding: 30px; border-radius: 15px; margin: 30px 0; text-align: center;">
    <h3 style="color: white; margin-bottom: 10px;">Download {self.product_data['name']} -- FREE!</h3>
    <p style="color: white; margin-bottom: 15px;">{self.product_data.get('desc', 'Free educational printable')}</p>
    <a href="{self.product_data['url']}" target="_blank" rel="noopener" style="background: white; color: #059669; padding: 12px 30px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block;">Download Now (Free PDF)</a>
</div>"""
        else:
            self.final_content += f"""
<div class="cta-box" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 15px; margin: 30px 0; text-align: center;">
    <h3 style="color: white; margin-bottom: 15px;">Love Learning Activities?</h3>
    <p style="color: white; margin-bottom: 20px;">Discover our free printable worksheets and premium resources:</p>
    <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
        <a href="{SITE_BASE_URL}/freebies.html" style="background: #F48C06; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold;">Free Worksheets</a>
        <a href="{SITE_BASE_URL}/products.html" style="background: white; color: #667eea; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold;">Premium Resources</a>
    </div>
</div>"""

        self.logger.success("Post-processing done (FAQ + SmartLinker + CTA)", 2)

    # ===============================================================
    # MODULE 5: PHASE 6 — SEO AUDIT (50 AI + 10 local + corrections)
    # ===============================================================

    async def phase_6_seo_audit(self, session):
        """60-criteria SEO audit: Agent 7 (50 AI) + 20 local checks + auto-corrections."""

        # --- STEP A: Agent 7 AI Audit (50 criteria / 1000 pts) ---
        self.logger.info("STEP A: Agent 7 -- AI Audit (50 criteria / 1000 pts)", 2)
        audit = await self.agent_7_validator(session)
        ai_score = audit.get("score", 0)
        ai_score_100 = round(ai_score / 10)  # normalize to /100
        self.logger.quality_score("Agent 7 AI Audit", ai_score, 1000)

        if audit.get("issues"):
            for issue in audit.get("issues", [])[:5]:
                self.logger.info(f"  -> {issue}", 2)

        # --- STEP B: 20 Local Criteria Checks (ported from V4) ---
        self.logger.info("STEP B: 20 Local Criteria Checks (code-based)", 2)
        local_score, local_suggestions = self.local_seo_checks()
        self.logger.quality_score("Local SEO Checks (20 criteria)", local_score, 100)

        combined_score = ai_score_100 + local_score
        self.logger.quality_score("Combined SEO Score", combined_score, 200)

        # --- STEP C: Auto-Corrections (5 rounds max) ---
        for correction_round in range(5):
            if combined_score >= 184:  # 92% of 200
                self.logger.success(f"SEO target reached: {combined_score}/200", 2)
                break

            self.logger.info(f"Correction Round {correction_round + 1}/5 (score: {combined_score}/200)", 2)
            self.apply_seo_corrections()

            # Re-check local score
            local_score, local_suggestions = self.local_seo_checks()
            combined_score = ai_score_100 + local_score
            self.logger.quality_score(f"Score after round {correction_round+1}", combined_score, 200)

        # Content verification
        self.content_verify()

        return combined_score

    async def agent_7_validator(self, session):
        sys_prompt = """You are Agent 7, the Premium SEO & Compliance Auditor.
Analyze the provided HTML article against our strict 50-criteria (1000 points total) grid.

CRITERIA & SCORING MATRICES:

1. INTENT & KEYWORDS (200 pts)
   - Primary keyword in H1, URL, Intro, & at least one H2 (40 pts)
   - Secondary/LSI keywords naturally present (40 pts)
   - Title/Meta descriptive with clear reader benefit (40 pts)
   - Answers the user's intent immediately in the intro (40 pts)
   - One clear subject, not diluted (40 pts)

2. CONTENT & PEDAGOGY (200 pts)
   - Length is sufficient (1000+ words) and well contextualized (40 pts)
   - Pedagogical explanations for adults (40 pts)
   - Clear structure (Objective, Materials, Instructions, Variations) (40 pts)
   - Dedicated FAQ addressing real parent/teacher questions (40 pts)
   - Vocabulary is accessible, sentences are short/punchy (40 pts)

3. MEDIA & UX (200 pts)
   - 5 Images present with descriptive Alt Text (50 pts)
   - Content is well spaced, easy to read on mobile (50 pts)
   - No aggressive elements (50 pts)
   - Clear and visible formatting for download/print CTAs (50 pts)

4. INTERNAL LINKING (200 pts)
   - Mentions/Hooks for internal links are natural (100 pts)
   - No duplicated or keyword-stuffed anchor text (100 pts)

5. E-E-A-T & HUMAN TONE (200 pts)
   - ZERO AI phrases ("In conclusion", "Moreover", "It is important") (100 pts)
   - Tone is authentic, experienced, and trustworthy (E-E-A-T) (100 pts)

Return a strictly formatted JSON object:
{"score": 950, "issues": ["List of issues"], "verdict": "PASS"}
PASS if score >= 900, otherwise REJECT."""

        kw = self.plan.get('primary_keyword', self.topic_name)
        user_prompt = f"Primary Keyword: {kw}\n\nARTICLE HTML:\n{self.final_content[:8000]}"

        try:
            audit = await call_deepseek_async(
                session, sys_prompt, user_prompt,
                agent_id=7, temperature=1.0, require_json=True, logger=self.logger
            )
            return audit
        except Exception as e:
            self.logger.error(f"Agent 7 failed: {e}", 2)
            return {"score": 700, "issues": [f"Agent 7 error: {str(e)[:50]}"], "verdict": "SKIP"}

    def local_seo_checks(self) -> Tuple[int, List[str]]:
        """20 local code-based SEO checks (100 pts total) — ported from V4."""
        score = 0
        suggestions = []
        content = self.final_content
        plain = re.sub(r'<[^>]+>', '', content).lower()
        word_count = len(plain.split())
        title = self.plan.get('title', '')
        meta = self.plan.get('meta_description', '')
        kw = self.plan.get('primary_keyword', '').lower()

        # 1. Title length (30-60 chars) — 5 pts
        if 30 <= len(title) <= 60:
            score += 5
        else:
            suggestions.append(f"Title: {len(title)} chars (optimal: 30-60)")

        # 2. Keyword in first 3 words of title — 5 pts
        if kw:
            title_lower = title.lower()
            first_3 = " ".join(title_lower.split()[:3])
            kw_words = kw.split()
            if any(w in first_3 for w in kw_words):
                score += 5
            elif kw in title_lower:
                score += 3  # keyword present but not at start
                suggestions.append("Keyword not in first 3 words of title")
            else:
                suggestions.append("Keyword absent from title")

        # 3. Meta description length (120-155 chars) — 5 pts
        if 120 <= len(meta) <= 155:
            score += 5
        else:
            suggestions.append(f"Meta: {len(meta)} chars (optimal: 120-155)")

        # 4. Keyword in meta description — 5 pts
        if kw and kw in meta.lower():
            score += 5
        elif kw:
            kw_parts = kw.split()
            if sum(1 for w in kw_parts if w in meta.lower()) >= len(kw_parts) // 2:
                score += 3
            else:
                suggestions.append("Keyword absent from meta description")

        # 5. Word count ≥2000 — 5 pts
        if word_count >= TARGET_WORD_COUNT:
            score += 5
        elif word_count >= MIN_WORD_COUNT:
            score += 3
            suggestions.append(f"Word count: {word_count} (target: {TARGET_WORD_COUNT})")
        else:
            suggestions.append(f"Word count too low: {word_count} (min: {MIN_WORD_COUNT})")

        # 6. H2 structure (5+) — 5 pts
        h2_count = len(re.findall(r'<h2[^>]*>', content))
        if h2_count >= 5:
            score += 5
        elif h2_count >= 3:
            score += 3
        else:
            suggestions.append(f"H2: {h2_count} (target: 5+)")

        # 7. H3 structure (8+) — 5 pts
        h3_count = len(re.findall(r'<h3[^>]*>', content))
        if h3_count >= 8:
            score += 5
        elif h3_count >= 4:
            score += 3
        else:
            suggestions.append(f"H3: {h3_count} (target: 8+)")

        # 8. Images with descriptive alt text (4+) — 5 pts
        img_tags = re.findall(r'<img[^>]+>', content)
        imgs_with_alt = [img for img in img_tags if 'alt="' in img and 'alt=""' not in img]
        if len(imgs_with_alt) >= 4:
            score += 5
        elif len(imgs_with_alt) >= 2:
            score += 3
        else:
            suggestions.append(f"Images with alt text: {len(imgs_with_alt)} (target: 4+)")

        # 9. Keyword density (1-3%) — 5 pts
        if kw and word_count > 0:
            kw_count = plain.count(kw)
            kw_words_n = len(kw.split())
            density = (kw_count * kw_words_n / word_count) * 100
            if 1.0 <= density <= 3.0:
                score += 5
            else:
                suggestions.append(f"Keyword density: {density:.1f}% (optimal: 1-3%)")

        # 10. Keyword in first 100 words — 5 pts
        if kw:
            first_100 = " ".join(plain.split()[:100])
            if kw in first_100:
                score += 5
            else:
                kw_parts = kw.split()
                if sum(1 for w in kw_parts if w in first_100) >= len(kw_parts) // 2:
                    score += 3
                else:
                    suggestions.append("Keyword absent from first 100 words")

        # 11. Internal links (4+) — 5 pts
        int_links = re.findall(
            r'<a\s+[^>]*href\s*=\s*["\'][^"\']*(?:littlesmartgenius|freebies|products|blog)[^"\']*["\']',
            content
        )
        all_links = re.findall(r'<a\s+href', content)
        if len(all_links) >= 4:
            score += 5
        elif len(all_links) >= 2:
            score += 3
        else:
            suggestions.append(f"Internal links: {len(all_links)} (target: 4+)")

        # 12. External authority link (1+) — 5 pts
        ext_links = re.findall(r'<a\s+[^>]*href\s*=\s*["\']https?://(?!littlesmartgenius)', content)
        if len(ext_links) >= 1:
            score += 5
        else:
            suggestions.append("No external authority link found")

        # 13. FAQ section present — 5 pts
        if '<div class="faq-section' in content or '<div class="faq' in content:
            score += 5
        else:
            suggestions.append("FAQ section missing")

        # 14. Lists ul/ol (3+) — 5 pts
        list_count = len(re.findall(r'<[uo]l[^>]*>', content))
        if list_count >= 3:
            score += 5
        elif list_count >= 1:
            score += 3
        else:
            suggestions.append(f"Lists: {list_count} (target: 3+)")

        # 15. Bold <strong> (3+) — 5 pts
        strong_count = len(re.findall(r'<strong>', content))
        if strong_count >= 3:
            score += 5
        elif strong_count >= 1:
            score += 2
        else:
            suggestions.append("No <strong> tags found (target: 3+)")

        # 16. Slug length (10-60 chars) — 5 pts
        slug = SEOUtils.optimize_slug(title)
        if 10 <= len(slug) <= 60:
            score += 5
        elif len(slug) <= 80:
            score += 3
        else:
            suggestions.append(f"Slug: {len(slug)} chars (max: 60)")

        # 17. Reading time (8-15 min) — 5 pts
        reading_time = max(1, word_count // 200)
        if 8 <= reading_time <= 15:
            score += 5
        elif 5 <= reading_time <= 20:
            score += 3
        else:
            suggestions.append(f"Reading time: {reading_time} min (optimal: 8-15)")

        # 18. Transition words (5+) — 5 pts
        transition_count = sum(1 for tw in TRANSITION_WORDS if tw.lower() in plain)
        if transition_count >= 5:
            score += 5
        elif transition_count >= 2:
            score += 3
        else:
            suggestions.append(f"Transition words: {transition_count} (target: 5+)")

        # 19. Short paragraphs (avg ≤4 sentences) — 5 pts
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', content, re.DOTALL)
        if paragraphs:
            avg_sentences = sum(
                len(re.findall(r'[.!?]+', re.sub(r'<[^>]+>', '', p)))
                for p in paragraphs
            ) / max(len(paragraphs), 1)
            if avg_sentences <= 4:
                score += 5
            elif avg_sentences <= 6:
                score += 3
            else:
                suggestions.append(f"Paragraphs too long: avg {avg_sentences:.1f} sentences (max: 4)")
        else:
            score += 3  # no <p> tags is unusual but not penalized hard

        # 20. Anti-AI phrase detection (0 found) — 5 pts
        ai_phrases_found = [p for p in AI_DETECTION_PHRASES if p.lower() in plain]
        if len(ai_phrases_found) == 0:
            score += 5
        else:
            suggestions.append(f"AI phrases detected ({len(ai_phrases_found)}): {', '.join(ai_phrases_found[:5])}")

        # ── HUMANIZATION CHECKS (bonus 20 pts) ──

        # 21. Sentence length variance — 5 pts
        sentences = re.findall(r'[^.!?]+[.!?]', plain)
        if len(sentences) >= 10:
            lengths = [len(s.split()) for s in sentences]
            avg_len = sum(lengths) / len(lengths)
            variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
            std_dev = variance ** 0.5
            if std_dev >= 6:
                score += 5  # Good variety
            elif std_dev >= 4:
                score += 3
            else:
                suggestions.append(f"Sentence length variety low: std_dev={std_dev:.1f} (target: 6+)")
        else:
            score += 3

        # 22. Contractions present (3+) — 5 pts
        contractions = re.findall(r"(?:don't|won't|can't|you'll|it's|they're|we're|I'm|I've|isn't|aren't|doesn't|weren't|shouldn't|couldn't|wouldn't|he's|she's|that's|there's|here's|what's|who's|let's)", plain)
        if len(contractions) >= 5:
            score += 5
        elif len(contractions) >= 2:
            score += 3
        else:
            suggestions.append(f"Contractions: {len(contractions)} (target: 5+ for natural voice)")

        # 23. Rhetorical questions (2+) — 5 pts
        # Count question marks NOT inside FAQ section
        content_no_faq = re.sub(r'<div class="faq.*?</div>', '', content, flags=re.DOTALL)
        questions = re.findall(r'\?', content_no_faq)
        if len(questions) >= 3:
            score += 5
        elif len(questions) >= 1:
            score += 3
        else:
            suggestions.append(f"Rhetorical questions: {len(questions)} (target: 3+ outside FAQ)")

        # 24. Informal markers: em-dashes + fragments — 5 pts
        em_dashes = len(re.findall(r'[–—]', content))
        fragments = len(re.findall(r'<p[^>]*>[^<]{3,30}\.</p>', content))
        informal_score = min(em_dashes, 3) + min(fragments, 2)
        if informal_score >= 4:
            score += 5
        elif informal_score >= 2:
            score += 3
        else:
            suggestions.append(f"Informal markers low: {em_dashes} em-dashes, {fragments} fragments (target: 2+ each)")
        # 25. Paragraph opening word diversity — 5 pts
        # Penalize if >30% of paragraphs start with the same word
        p_texts = [re.sub(r'<[^>]+>', '', p).strip() for p in paragraphs if re.sub(r'<[^>]+>', '', p).strip()]
        if len(p_texts) >= 6:
            first_words = [t.split()[0].lower() for t in p_texts if t.split()]
            if first_words:
                from collections import Counter
                word_counts = Counter(first_words)
                most_common_word, most_common_count = word_counts.most_common(1)[0]
                ratio = most_common_count / len(first_words)
                if ratio <= 0.25:
                    score += 5  # Excellent diversity
                elif ratio <= 0.35:
                    score += 3
                else:
                    suggestions.append(f"Paragraph openings: {most_common_count}/{len(first_words)} start with '{most_common_word}' ({ratio:.0%}) — target: <30%")
        else:
            score += 3  # Not enough paragraphs to judge

        for s in suggestions:
            self.logger.verification_result(s, False)

        return score, suggestions


    def apply_seo_corrections(self):
        """Auto-corrections from V4 (title, meta, AI phrases, density, external link, keyword)."""
        title = self.plan.get('title', '')
        meta = self.plan.get('meta_description', '')
        kw = self.plan.get('primary_keyword', '')

        # Fix 1: Title too long/short or contains ellipses
        if len(title) > 60 or len(title) < 30 or "..." in title:
            corrected = call_deepseek_sync(
                f"Fix this title to be exactly 30-60 characters, with NO ellipses (...):\n\"{title}\"\nReturn ONLY the corrected title.",
                self.logger, "TITLE FIX", "seo"
            )
            if corrected and 30 <= len(corrected.strip().strip('"').strip("'")) <= 60:
                self.plan['title'] = corrected.strip().strip('"').strip("'")
                self.logger.correction_applied(f"Title: {len(title)}c -> {len(self.plan['title'])}c", self.plan['title'][:50])
            else:
                self.plan['title'] = title[:57]
                self.logger.correction_applied("Title forced hard cut", self.plan['title'][:50])

        # Fix 2: Meta description — try DeepSeek correction first (like V4), then extraction fallback
        if not (120 <= len(meta) <= 155):
            corrected_meta = call_deepseek_sync(
                f"Fix this meta description to be 120-155 characters:\n\"{meta}\"\nContext: Educational blog for kids.\nRules: Compelling, include call-to-action, 120-155 chars.\nReturn ONLY the corrected description.",
                self.logger, "META FIX", "seo"
            )
            if corrected_meta:
                clean = corrected_meta.strip().strip('"').strip("'")
                if 100 <= len(clean) <= 170:
                    self.plan['meta_description'] = clean
                    self.plan['excerpt'] = clean  # sync excerpt like V4
                    self.logger.correction_applied(f"Meta (AI fix): {len(meta)}c -> {len(clean)}c", clean[:50])
                    meta = clean
            # Fallback to extraction if AI fix failed
            if not (100 <= len(self.plan.get('meta_description', '')) <= 170):
                new_meta = SEOUtils.generate_meta_description(self.final_content)
                if 100 <= len(new_meta) <= 170:
                    self.plan['meta_description'] = new_meta
                    self.plan['excerpt'] = new_meta  # sync excerpt
                    self.logger.correction_applied(f"Meta (extract): {len(meta)}c -> {len(new_meta)}c", new_meta[:50])

        # Fix 3: Remove AI phrases
        ai_fixes = 0
        for phrase in AI_DETECTION_PHRASES:
            if phrase.lower() in self.final_content.lower():
                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                self.final_content = pattern.sub("", self.final_content, count=1)
                ai_fixes += 1
        if ai_fixes:
            self.logger.correction_applied(f"Removed {ai_fixes} AI phrases", "Content cleaned")

        # Fix 4: Keyword density boost
        if kw:
            plain = re.sub(r'<[^>]+>', '', self.final_content).lower()
            wc = len(plain.split())
            kw_count = plain.count(kw.lower())
            kw_words = len(kw.split())
            density = (kw_count * kw_words / max(wc, 1)) * 100
            if density < 1.0:
                # Pool of 10 natural keyword density formulations (rotated randomly)
                kw_templates = [
                    f"That's where <strong>{kw}</strong> really makes a difference.",
                    f"It's one of the reasons <strong>{kw}</strong> works so well.",
                    f"Parents looking into <strong>{kw}</strong> will love this approach.",
                    f"This ties directly into what makes <strong>{kw}</strong> so effective.",
                    f"And that's exactly why <strong>{kw}</strong> matters at this age.",
                    f"If you're serious about <strong>{kw}</strong>, this is a great place to start.",
                    f"It's a big part of why <strong>{kw}</strong> has become so popular.",
                    f"For families exploring <strong>{kw}</strong>, this tip is gold.",
                    f"This is the kind of thing that sets great <strong>{kw}</strong> apart.",
                    f"When it comes to <strong>{kw}</strong>, small details like this add up.",
                ]
                random.shuffle(kw_templates)
                paragraphs = re.findall(r'(<p[^>]*>)(.*?)(</p>)', self.final_content, re.DOTALL)
                injected = 0
                for idx in range(2, min(len(paragraphs), 10), 3):
                    p_open, p_content, p_close = paragraphs[idx]
                    if kw.lower() not in p_content.lower() and injected < 3:
                        template = kw_templates[injected % len(kw_templates)]
                        new_p = f"{p_open}{p_content} {template}{p_close}"
                        self.final_content = self.final_content.replace(f"{p_open}{p_content}{p_close}", new_p, 1)
                        injected += 1
                if injected:
                    self.logger.correction_applied(f"Keyword density boost: +{injected}", kw[:40])

        # Fix 5: External authority link
        if not re.search(r'<a\s+[^>]*href\s*=\s*["\']https?://(?!littlesmartgenius)', self.final_content):
            authority_links = [
                '<p><em>According to the <a href="https://www.naeyc.org/resources" target="_blank" rel="noopener">National Association for the Education of Young Children (NAEYC)</a>, hands-on educational activities are crucial for early childhood development.</em></p>',
                '<p><em>Research from <a href="https://www.edutopia.org/" target="_blank" rel="noopener">Edutopia</a> highlights the importance of engaging, play-based learning at home.</em></p>',
                '<p><em>As noted by <a href="https://www.scholastic.com/parents/school-success/learning-toolkit-blog.html" target="_blank" rel="noopener">Scholastic Parents</a>, early childhood resources help build foundational cognitive skills.</em></p>',
                '<p><em>Experts at <a href="https://www.pbs.org/parents/" target="_blank" rel="noopener">PBS Kids for Parents</a> recommend active problem-solving games to boost confidence.</em></p>',
                '<p><em>The <a href="https://childmind.org/" target="_blank" rel="noopener">Child Mind Institute</a> emphasizes that structured educational play reduces anxiety and improves focus.</em></p>',
                '<p><em>As described on <a href="https://en.wikipedia.org/wiki/Early_childhood_education" target="_blank" rel="noopener">Wikipedia</a>, early childhood education lays the groundwork for lifelong cognitive and social development.</em></p>',
                '<p><em>The concept of <a href="https://en.wikipedia.org/wiki/Montessori_education" target="_blank" rel="noopener">Montessori education</a> emphasizes hands-on, self-directed learning that nurtures independence from a young age.</em></p>',
                '<p><em>According to <a href="https://en.wikipedia.org/wiki/Educational_psychology" target="_blank" rel="noopener">educational psychology research</a>, active engagement with materials dramatically improves knowledge retention in children.</em></p>',
                '<p><em>Studies referenced by the <a href="https://en.wikipedia.org/wiki/Constructivism_(philosophy_of_education)" target="_blank" rel="noopener">constructivist learning theory</a> show that children learn best when they build knowledge through experience.</em></p>',
                '<p><em>The principles behind <a href="https://en.wikipedia.org/wiki/Zone_of_proximal_development" target="_blank" rel="noopener">Vygotsky\'s Zone of Proximal Development</a> remind us that the right challenge level is key to growth.</em></p>',
                '<p><em>As highlighted by the <a href="https://www.understood.org/" target="_blank" rel="noopener">Understood.org</a> team, structured learning activities can help all children — including those with learning differences — thrive.</em></p>'
            ]
            ext_link = random.choice(authority_links)
            if '<div class="faq-section' in self.final_content:
                self.final_content = self.final_content.replace('<div class="faq-section', f'{ext_link}\n<div class="faq-section', 1)
            else:
                self.final_content += ext_link
            self.logger.correction_applied("External link added", "Dynamic authority reference")

        # Fix 6: Keyword in first paragraph
        if kw:
            first_p = re.search(r'<p[^>]*>(.*?)</p>', self.final_content, re.DOTALL)
            if first_p and kw.lower() not in first_p.group(1).lower():
                original_p = first_p.group(0)
                # Pool of natural keyword introductions (no AI-detectable patterns)
                kw_intro_pool = [
                    f" If you've been looking into <strong>{kw}</strong>, you're in the right place.",
                    f" That's exactly why <strong>{kw}</strong> has become such a hot topic among parents.",
                    f" And honestly, <strong>{kw}</strong> is one of the best ways to get started.",
                ]
                kw_sentence = random.choice(kw_intro_pool)
                new_p = original_p.replace('</p>', f'{kw_sentence}</p>', 1)
                self.final_content = self.final_content.replace(original_p, new_p, 1)
                self.logger.correction_applied("Keyword added to first paragraph", kw[:40])

    def content_verify(self):
        """ContentVerifier: 5 basic health checks."""
        content = self.final_content
        title = self.plan.get('title', '')
        meta = self.plan.get('meta_description', '')
        word_count = len(re.sub(r'<[^>]+>', '', content).split())

        self.logger.verification_result("Title (30-60 chars)", 30 <= len(title) <= 60, f"{len(title)} chars")
        self.logger.verification_result("Meta desc (120-155 chars)", 120 <= len(meta) <= 155, f"{len(meta)} chars")
        self.logger.verification_result(f"Words (>=1600)", word_count >= 1600, f"{word_count} words")
        h2_count = len(re.findall(r'<h2', content))
        self.logger.verification_result(f"Sections H2 (>=6)", h2_count >= 6, f"{h2_count} H2")
        self.logger.verification_result("Images (>=5)", len(re.findall(r'<img', content)) >= 5)

    # ===============================================================
    # PHASE 7: COMPILE & SAVE + INSTAGRAM
    # ===============================================================

    def compile_and_save(self):
        slug = SEOUtils.optimize_slug(self.plan['title'])
        ts = int(time.time())

        # ── DUPLICATE SLUG CHECK ──
        # Prevent creating a second article with the same slug
        # Check both posts/ (pending JSONs) and articles/ (already built HTML)
        os.makedirs(POSTS_DIR, exist_ok=True)
        articles_dir = os.path.join(PROJECT_ROOT, "articles")
        existing_posts = glob.glob(os.path.join(POSTS_DIR, f"{slug}-*.json"))
        existing_html = os.path.exists(os.path.join(articles_dir, f"{slug}.html"))
        if existing_posts or existing_html:
            source = os.path.basename(existing_posts[0]) if existing_posts else f"{slug}.html"
            self.logger.warning(f"DUPLICATE BLOCKED: slug '{slug}' already exists → {source}", 2)
            self.logger.warning("Skipping save to prevent duplicate article.", 2)
            return {
                "title": self.plan['title'],
                "slug": slug,
                "word_count": 0,
                "skipped_duplicate": True
            }

        # ── SEMANTIC TITLE DEDUP ──
        # Prevent near-duplicate articles (same topic, different slug)
        # by comparing title word overlap against all existing articles
        TITLE_STOP_WORDS = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'has', 'have', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'shall', 'not', 'no', 'so', 'if',
            'how', 'what', 'why', 'when', 'where', 'who', 'which', 'that', 'this',
            'it', 'its', 'your', 'our', 'their', 'my', 'his', 'her', 'best',
            'top', 'ultimate', 'guide', 'tips', 'essential',
        }

        def _basic_stem(word):
            """Lightweight stemmer: strip common suffixes for comparison."""
            for suffix in ['tion', 'sion', 'ment', 'ness', 'ious', 'eous', 'ical',
                           'ting', 'ing', 'ies', 'ful', 'ous', 'ive', 'led', 'ted',
                           'ers', 'est', 'als', 'ble', 'ity', 'ent', 'ant',
                           'ed', 'es', 'ly', 'er', 'al', 'en']:
                if word.endswith(suffix) and len(word) - len(suffix) >= 3:
                    return word[:-len(suffix)]
            if word.endswith('s') and len(word) > 4:
                return word[:-1]
            return word

        def _title_words(title):
            words = set(re.findall(r'[a-z]{3,}', title.lower()))
            return {_basic_stem(w) for w in words - TITLE_STOP_WORDS}

        new_words = _title_words(self.plan['title'])
        # Skip semantic dedup for product-slot articles — they are intentionally
        # similar series (e.g. "Spot the Difference Vol.1", Vol.2, Vol.3…)
        is_product_slot = getattr(self, 'slot', '') == 'product'
        if new_words and not is_product_slot:
            # Collect existing titles from articles.json + pending posts
            existing_titles = []
            articles_json = os.path.join(PROJECT_ROOT, "articles.json")
            if os.path.exists(articles_json):
                try:
                    with open(articles_json, 'r', encoding='utf-8') as f:
                        idx = json.load(f)
                    for a in idx.get('articles', []):
                        existing_titles.append(a.get('title', ''))
                except Exception:
                    pass
            # Also scan pending posts
            for pf in glob.glob(os.path.join(POSTS_DIR, "*.json")):
                try:
                    with open(pf, 'r', encoding='utf-8') as f:
                        existing_titles.append(json.load(f).get('title', ''))
                except Exception:
                    pass

            for existing_title in existing_titles:
                existing_words = _title_words(existing_title)
                if not existing_words:
                    continue
                overlap = new_words & existing_words
                smaller = min(len(new_words), len(existing_words))
                similarity = len(overlap) / smaller if smaller > 0 else 0
                if similarity >= 0.9:
                    self.logger.warning(f"SEMANTIC DUPLICATE BLOCKED: '{self.plan['title'][:50]}' is too similar ({similarity:.0%}) to '{existing_title[:50]}'", 2)
                    self.logger.warning("Skipping save to prevent near-duplicate article.", 2)
                    return {
                        "title": self.plan['title'],
                        "slug": slug,
                        "word_count": 0,
                        "skipped_duplicate": True
                    }

        meta_desc = self.plan.get('meta_description') or SEOUtils.generate_meta_description(self.final_content)
        kw_list = SEOUtils.extract_keywords(self.plan['title'], self.final_content)
        word_count = len(re.findall(r'\w+', re.sub(r'<[^>]+>', '', self.final_content)))
        reading_time = SEOUtils.calculate_reading_time(self.final_content)

        final_data = {
            "title": self.plan['title'],
            "slug": slug,
            "author": self.persona['id'],
            "author_name": self.persona.get('author_display', self.persona['role']),
            "date": datetime.now().strftime("%B %d, %Y"),
            "iso_date": datetime.now().isoformat(),
            "category": self.category,
            "image": self.image_paths[0] if self.image_paths else "images/placeholder.webp",
            "content": self.final_content,
            "excerpt": meta_desc,
            "meta_description": meta_desc,
            "primary_keyword": self.plan.get('primary_keyword', self.keywords),
            "keywords": kw_list,
            "reading_time": reading_time,
            "word_count": word_count,
            "faq_schema": self.plan.get('faq', []),
            "slot": self.slot,
            "topic_name": self.topic_name,
            "version": "V6-Ultimate"
        }

        # Save JSON
        output_file = os.path.join(POSTS_DIR, f"{slug}-{ts}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)

        file_size = os.path.getsize(output_file)
        self.logger.success(f"Saved ({file_size // 1024} KB): {output_file}", 2)

        # Instagram + Make.com Webhook
        ig_cover = None
        if self.image_paths and not self.image_paths[0].startswith("http"):
            ig_cover = os.path.join(PROJECT_ROOT, self.image_paths[0])

        try:
            from instagram_generator import generate_instagram_post, send_to_makecom
            ig_result = generate_instagram_post(final_data, ig_cover)
            if ig_result:
                self.logger.success(f"Instagram post: {ig_result['image_path']}", 2)
                article_url = f"{SITE_BASE_URL}/articles/{slug}.html"
                if send_to_makecom(ig_result, article_url):
                    self.logger.success("Make.com webhook sent", 2)
                    try:
                        from instagram_cleanup import mark as ig_mark
                        ig_mark(os.path.basename(ig_result['image_path']))
                    except Exception:
                        pass
        except Exception as e:
            self.logger.warning(f"Instagram failed: {str(e)[:50]}", 2)

        # Final report
        self.logger.banner("V6 ULTIMATE GENERATION COMPLETE", "=")
        print(f"File: {output_file}")
        print(f"Slot: {self.slot} | Words: {word_count}")
        print(f"Images: {len(self.image_paths)} | Reading: {reading_time} min")
        print(f"Finished: {datetime.now().strftime('%H:%M:%S')}")

        return final_data


# ===================================================================
# MODULE 8: BATCH ORCHESTRATOR + SINGLE + REGENERATE
# ===================================================================

def generate_article_v6(slot: str, topic: dict, topic_selector: TopicSelector) -> Optional[Dict]:
    """Generate a single article using V6 multi-agent pipeline."""
    weights = [p.get('weight', 1) for p in PERSONAS]
    persona = random.choices(PERSONAS, weights=weights, k=1)[0]

    temp_slug = SEOUtils.optimize_slug(f"{topic['topic_name']}-{int(time.time())}")
    logger = DetailedLogger(temp_slug)

    engine = AutoBlogV6(slot, topic, persona, logger, used_topics_ref=topic_selector.used)

    try:
        result = asyncio.run(engine.run_pipeline())
        if result:
            topic_selector.mark_used(slot, topic['topic_name'])
        return result
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        logger.save()
        return None


def run_daily_batch():
    """Run daily batch: generate 3 articles (keyword, product, freebie)."""
    try:
        from instagram_cleanup import cleanup as ig_cleanup
        ig_cleanup()
    except Exception:
        pass

    print("\n" + "=" * 80)
    print("  AUTO BLOG V6 ULTIMATE -- DAILY BATCH")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    ts = TopicSelector()
    stats = ts.get_stats()
    print(f"\nTopic Pool:")
    print(f"  Keywords: {stats['keywords_remaining']}/{stats['keywords_total']} remaining")
    print(f"  Products: {stats['products_remaining']}/{stats['products_total']} remaining")
    print(f"  Freebies: {stats['freebies_remaining']}/{stats['freebies_total']} remaining")

    results = []
    for i, slot in enumerate(DAILY_SLOTS):
        print(f"\n{'='*80}")
        print(f"  ARTICLE {i+1}/{len(DAILY_SLOTS)} -- Slot: {slot.upper()}")
        print(f"{'='*80}")

        topic = ts.get_next_topic(slot)
        if not topic:
            print(f"\n[SKIP] No available topics for slot '{slot}'")
            continue

        result = generate_article_v6(slot, topic, ts)
        if result:
            # Detect silently blocked articles (duplicate or 0-word)
            if result.get('skipped_duplicate') or result.get('word_count', 0) == 0:
                print(f"\n  [WARNING] Article '{result.get('title', 'Unknown')[:50]}' was BLOCKED (duplicate or 0 words). NOT counted as success.")
                print(f"  [WARNING] Slug: {result.get('slug', 'N/A')}, word_count: {result.get('word_count', 0)}")
            else:
                results.append({"slot": slot, "title": result["title"], "slug": result["slug"], "word_count": result["word_count"]})

        if i < len(DAILY_SLOTS) - 1:
            print(f"\n[PAUSE] Waiting {PAUSE_BETWEEN_ARTICLES}s...")
            time.sleep(PAUSE_BETWEEN_ARTICLES)

    print("\n" + "=" * 80)
    print(f"  DAILY BATCH COMPLETE: {len(results)}/{len(DAILY_SLOTS)} articles")
    print("=" * 80)
    for r in results:
        print(f"  [{r['slot'].upper()}] {r['title'][:50]}  ({r['word_count']} words)")

    # --- POST-BATCH: SmartLinker re-injection pass ---
    # Now that all articles exist, re-run SmartLinker on each generated JSON
    # so cross-linking ("You Might Also Like") is populated correctly.
    if results:
        print("\n[POST-BATCH] Running SmartLinker cross-linking pass...")
        try:
            smart_linker = SmartLinker()
            if smart_linker.articles:
                print(f"  SmartLinker found {len(smart_linker.articles)} articles for cross-linking.")
            else:
                print("  SmartLinker: no articles found yet (will be linked after build_articles.py).")
        except Exception as e:
            print(f"  SmartLinker post-batch pass skipped: {str(e)[:50]}")

    return results


def run_single(slot: str = None):
    ts = TopicSelector()
    if not slot:
        slot = random.choice(DAILY_SLOTS)

    # Debug: show topic pool stats
    stats = ts.get_stats()
    print(f"[SINGLE] Topic Pool: kw={stats.get('keywords_remaining',0)}/{stats.get('keywords_total',0)} "
          f"prod={stats.get('products_remaining',0)}/{stats.get('products_total',0)} "
          f"free={stats.get('freebies_remaining',0)}/{stats.get('freebies_total',0)}")

    topic = ts.get_next_topic(slot)
    if not topic:
        print(f"[ERROR] No available topics for slot '{slot}'")
        return None
    print(f"[SINGLE] Selected topic: '{topic['topic_name'][:60]}' for slot '{slot}'")
    return generate_article_v6(slot, topic, ts)


def run_regenerate(slug: str):
    ts = TopicSelector()
    posts_dir = POSTS_DIR
    json_path = os.path.join(posts_dir, f"{slug}.json")

    topic_name = slug.replace('-', ' ').title()
    category = "education"
    keywords = topic_name

    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            topic_name = data.get('title', topic_name)
            category = data.get('category', category)
            keywords = data.get('keywords', keywords)
            if isinstance(keywords, list):
                keywords = ', '.join(keywords)
        except Exception:
            pass

    topic = {"topic_name": topic_name, "category": category, "keywords": keywords, "product_data": None}
    return generate_article_v6("keyword", topic, ts)


# ===================================================================
# MODULE 9: SCHEDULE ENGINE + CLI
# ===================================================================

def get_current_week():
    launch_str = os.environ.get("LAUNCH_DATE", "2026-03-10")
    try:
        launch = datetime.strptime(launch_str, "%Y-%m-%d")
    except ValueError:
        launch = datetime(2026, 3, 10)
    delta = datetime.utcnow() - launch
    return max(1, (delta.days // 7) + 1)


def run_schedule(cron_expr=None):
    current_hour = datetime.utcnow().hour
    current_week = get_current_week()

    print(f"\n{'=' * 80}")
    print(f"  AUTO BLOG V6 ULTIMATE -- SCHEDULE MODE")
    print(f"  Week: {current_week} | UTC Hour: {current_hour} | Cron: '{cron_expr or 'none'}'")
    print(f"{'=' * 80}")

    matched_slot = None
    matched_min_week = None

    # Method 1: Use exact cron expression (reliable, no delay issues)
    if cron_expr and cron_expr.strip():
        clean_cron = cron_expr.strip()
        if clean_cron in CRON_TO_SLOT:
            matched_slot, matched_min_week = CRON_TO_SLOT[clean_cron]
            print(f"[SCHEDULE] Matched cron '{clean_cron}' → slot '{matched_slot}' (min week {matched_min_week})")
        else:
            print(f"[SCHEDULE] WARNING: Cron '{clean_cron}' not found in CRON_TO_SLOT!")
            print(f"[SCHEDULE] Available crons: {list(CRON_TO_SLOT.keys())}")
            print(f"[SCHEDULE] Falling back to time-based slot selection...")

    # Method 2: Fallback — wide time windows (if cron didn't match or not provided)
    if not matched_slot:
        for (h_start, h_end), (slot_type, min_week) in SCHEDULE_SLOTS_FALLBACK.items():
            if h_start <= current_hour < h_end:
                matched_slot = slot_type
                matched_min_week = min_week
                print(f"[SCHEDULE] Fallback matched: hour {current_hour} → slot '{matched_slot}' (min week {matched_min_week})")
                break

    if not matched_slot:
        print(f"[SCHEDULE] No slot for hour {current_hour}. Skipping.")
        return

    if current_week < matched_min_week:
        print(f"[SCHEDULE] Slot '{matched_slot}' requires week {matched_min_week}+, currently week {current_week}. Skipping.")
        return

    print(f"[SCHEDULE] Running slot '{matched_slot}' (active from week {matched_min_week})")
    run_single(matched_slot)


def main():
    parser = argparse.ArgumentParser(
        description="Auto Blog V6 Ultimate -- Multi-Agent Generation Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python auto_blog_v6_ultimate.py --batch              # Daily batch (3 articles)
  python auto_blog_v6_ultimate.py --schedule           # Schedule-aware
  python auto_blog_v6_ultimate.py --slot keyword       # Single keyword article
  python auto_blog_v6_ultimate.py --slot product       # Single product article
  python auto_blog_v6_ultimate.py --slot freebie       # Single freebie article
  python auto_blog_v6_ultimate.py --regenerate SLUG    # Regenerate by slug
  python auto_blog_v6_ultimate.py --stats              # Show topic pool stats
  python auto_blog_v6_ultimate.py                      # Single random article
"""
    )
    parser.add_argument("--batch", action="store_true", help="Run daily batch (3 articles)")
    parser.add_argument("--schedule", action="store_true", help="Schedule-aware generation")
    parser.add_argument("--cron", metavar="EXPR", help="Cron expression that triggered this run (from github.event.schedule)")
    parser.add_argument("--slot", choices=["keyword", "product", "freebie"], help="Single article slot")
    parser.add_argument("--regenerate", metavar="SLUG", help="Regenerate article by slug")
    parser.add_argument("--stats", action="store_true", help="Show topic pool statistics")

    args = parser.parse_args()

    if args.stats:
        ts = TopicSelector()
        stats = ts.get_stats()
        print("\n  AUTO BLOG V6 ULTIMATE -- Topic Pool Statistics")
        print("  " + "=" * 50)
        for key, val in stats.items():
            print(f"  {key}: {val}")
        return

    if args.regenerate:
        run_regenerate(args.regenerate)
    elif args.schedule:
        run_schedule(args.cron)
    elif args.batch:
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
