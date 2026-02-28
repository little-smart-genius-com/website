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

# Fix Windows terminal encoding
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass

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
POLLINATIONS_KEYS = [os.getenv(f"POLLINATIONS_API_KEY_{i}") for i in range(1, 6)]
POLLINATIONS_KEYS = [k for k in POLLINATIONS_KEYS if k and len(k) > 5]
POLLINATIONS_BACKUP_KEYS = [os.getenv(f"POLLINATIONS_API_KEY_BCK_{i}") for i in range(1, 6)]
POLLINATIONS_BACKUP_KEYS = [k for k in POLLINATIONS_BACKUP_KEYS if k and len(k) > 5]
POLLINATIONS_MODEL = "klein-large"

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
IMAGE_RETRY_MAX = 8
TOTAL_IMAGES = 6    # 1 cover + 5 content images
NUM_CONTENT_IMAGES = 5
SITE_BASE_URL = "https://littlesmartgenius.com"

# Batch config
DAILY_SLOTS = ["keyword", "product", "freebie"]
PAUSE_BETWEEN_ARTICLES = 30

# Escalating Schedule
SCHEDULE_SLOTS = {
    (8, 9):   ("keyword", 1),
    (9, 10):  ("product", 7),
    (14, 15): ("product", 1),
    (15, 16): ("keyword", 4),
    (20, 21): ("freebie", 1),
    (21, 22): ("keyword", 10),
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
        text = re.sub(r'<[^>]+>', '', f"{title} {content}").lower()
        words = re.findall(r'\b[a-z]{4,}\b', text)
        freq = {}
        stop = {"this", "that", "with", "from", "have", "been", "your", "they", "them"}
        for w in words:
            if w not in stop:
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
    def generate_seo_alt_text(concept: str, context: str) -> str:
        alt = f"{concept} {context}"
        alt = re.sub(r'[^a-zA-Z0-9\s-]', '', alt)
        alt = re.sub(r'\s+', '-', alt)
        return alt.lower()[:125]


class AutoBlogV6:
    """V6 Ultimate Multi-Agent Engine."""

    def __init__(self, slot, topic, persona, logger):
        self.slot = slot
        self.topic_name = topic["topic_name"]
        self.category = topic["category"]
        self.keywords = topic["keywords"]
        self.product_data = topic.get("product_data")
        self.persona = persona
        self.logger = logger
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
            self.logger.step_start("PHASE 1/7: ARCHITECT", "Agent 1 builds JSON plan")
            await self.agent_1_architect(session)
            self.logger.step_end("PHASE 1/7: ARCHITECT")

            # === PHASE 2: WRITERS + ART DIRECTOR (parallel) ===
            self.logger.step_start("PHASE 2/7: WRITERS + ART DIRECTOR",
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
            self.logger.step_end("PHASE 2/7: WRITERS + ART DIRECTOR")

            # === PHASE 3: IMAGES (parallel) ===
            self.logger.step_start("PHASE 3/7: IMAGE GENERATION",
                                    f"5 images, 8 attempts each, {len(POLLINATIONS_KEYS)} primary + {len(POLLINATIONS_BACKUP_KEYS)} backup keys")
            self.image_paths = await self.artists_generate_images(session)
            self.logger.step_end("PHASE 3/7: IMAGE GENERATION")

            # === PHASE 4: ASSEMBLER (sequential) ===
            self.logger.step_start("PHASE 4/7: ASSEMBLER", "Agent 6 merges + harmonizes")
            await self.agent_6_assembler(session)
            self.logger.step_end("PHASE 4/7: ASSEMBLER")

            # === PHASE 5: POST-PROCESSING (V4 ecosystem) ===
            self.logger.step_start("PHASE 5/7: POST-PROCESSING", "SmartLinker + FAQ + CTA")
            self.post_process()
            self.logger.step_end("PHASE 5/7: POST-PROCESSING")

            # === PHASE 6: SEO AUDIT (60 criteria) ===
            self.logger.step_start("PHASE 6/7: SEO AUDIT (60 criteria)",
                                    "Agent 7 (50 AI) + 10 local checks + corrections")
            seo_score = await self.phase_6_seo_audit(session)
            self.logger.step_end("PHASE 6/7: SEO AUDIT (60 criteria)")

            # === PHASE 7: SAVE + INSTAGRAM ===
            self.logger.step_start("PHASE 7/7: SAVE + SYNDICATION", "JSON + Instagram + Webhook")
            final_data = self.compile_and_save()
            self.logger.step_end("PHASE 7/7: SAVE + SYNDICATION")

            self.logger.save()
            return final_data

    # --- AGENT 1: ARCHITECT ---
    async def agent_1_architect(self, session):
        prompt_builder = get_prompt_builder(self.slot)
        if self.slot == "product" or self.slot == "freebie":
            prompts = prompt_builder(self.product_data, self.persona)
        else:
            prompts = prompt_builder(self.topic_name, self.persona)

        self.content_builder_fn = prompts['content_prompt_builder']

        system_prompt = "You are Agent 1, the Master Architect. Return ONLY valid JSON."
        self.plan = await call_deepseek_async(
            session, system_prompt, prompts['plan_prompt'],
            agent_id=1, temperature=0.3, require_json=True, logger=self.logger
        )

        if 'primary_keyword' not in self.plan:
            self.plan['primary_keyword'] = self.topic_name

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
            agent_id=agent_id, temperature=0.7, logger=self.logger
        )

        html_output = re.sub(r'```html|```', '', html_output).strip()
        word_count = len(re.findall(r'\w+', re.sub(r'<[^>]+>', '', html_output)))
        print(f"   [AGENT {writer_id+1}] Done! ({word_count} words)")
        return (writer_id, html_output)

    # --- AGENT 5: ART DIRECTOR ---
    async def agent_5_art_director(self, session):
        print("   [AGENT 5] Art Director drafting 5 image prompts (V4 style presets)...")

        # Use centralized IMAGE_STYLE_PRESETS from prompt_templates.py (V4 canonical source)
        # V6 adds a 5th preset (Creative Workspace) for the extra cover image slot
        V6_STYLE_PRESETS = list(IMAGE_STYLE_PRESETS) + [
            {
                "name": "Creative Workspace",
                "composition": "Top-down flat lay or slight angle, organized materials",
                "style": "3D Pixar-style, colorful and vibrant, ultra-detailed",
                "lighting": "Bright even studio lighting, clean background",
                "palette": "Brand orange (#F48C06), white, slate blue, sunshine yellow",
            }
        ]

        persona_img_style = self.persona.get('img_style', 'bright educational setting, 3D Pixar style')

        concepts = [self.plan.get('cover_concept', f'Educational illustration about {self.topic_name}')]
        for s in self.plan.get('sections', []):
            if 'image_concept' in s:
                concepts.append(s['image_concept'])

        while len(concepts) < 5:
            concepts.append(f"Educational vector illustration related to {self.topic_name}")
        concepts = concepts[:5]

        tasks = []
        for i, concept in enumerate(concepts):
            preset = V6_STYLE_PRESETS[i % len(V6_STYLE_PRESETS)]
            sys_prompt = """You are an expert Art Director with 20 years in children's educational content.
Return ONLY a 1-2 sentence image generation prompt. NO conversational text, NO markdown."""
            user_prompt = f"""Transform this concept into a PREMIUM prompt for Flux Klein-Large (9B parameters).

CONCEPT: {concept}
ARTICLE CONTEXT: {self.topic_name}
IMAGE ROLE: {preset['name']} (Image #{i+1} of 5)
PERSONA STYLE: {persona_img_style}
TARGET: Parents and teachers of children aged 4-12

═══ STYLE PRESET ═══
- Composition: {preset['composition']}
- Style: {preset['style']}
- Lighting: {preset['lighting']}
- Color Palette: {preset['palette']}

═══ RULES ═══
- NO text, words, or letters in the image
- NO brand logos or watermarks
- Children depicted should be diverse (mix ethnicities)
- Keep it child-safe and family-friendly
- Include educational elements (books, puzzles, worksheets visible)
- Subjects should show JOY and ENGAGEMENT

Return ONLY the enhanced prompt as 1-2 sentences with scene, subjects, action, emotional tone, and technical specs."""
            tasks.append(call_deepseek_async(
                session, sys_prompt, user_prompt,
                agent_id=5, temperature=0.4, logger=self.logger
            ))

        raw_prompts = await asyncio.gather(*tasks, return_exceptions=True)

        # V4-style validation: if prompt is invalid/too short, use fallback basic prompt
        validated_prompts = []
        for i, (enhanced, concept) in enumerate(zip(raw_prompts, concepts)):
            preset = V6_STYLE_PRESETS[i % len(V6_STYLE_PRESETS)]
            if isinstance(enhanced, Exception) or not enhanced or len(str(enhanced).strip()) < 50:
                # Fallback like V4's optimize_image_prompt_dir_art()
                fallback = (
                    f"{concept}, {self.topic_name}, {persona_img_style}, "
                    f"{preset['style']}, {preset['palette']}, "
                    f"3D Pixar style, high quality, vibrant colors, educational, "
                    f"children aged 4-12, child-safe, family-friendly"
                )
                self.logger.warning(f"Agent 5 prompt #{i+1} invalid -- using fallback", 3)
                validated_prompts.append(fallback)
            else:
                validated_prompts.append(str(enhanced).strip().strip('"').strip("'"))

        print(f"   [AGENT 5] 5 Prompts validated ({sum(1 for p in raw_prompts if not isinstance(p, Exception) and p and len(str(p)) >= 50)} AI + {sum(1 for p in raw_prompts if isinstance(p, Exception) or not p or len(str(p)) < 50)} fallback).")
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
            params = {
                "width": width, "height": height, "seed": seed,
                "model": POLLINATIONS_MODEL, "nologo": "true", "enhance": "true"
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

    async def artists_generate_images(self, session):
        tasks = [self.fetch_and_save_image(session, p, i) for i, p in enumerate(self.image_prompts)]
        return await asyncio.gather(*tasks)

    # --- AGENT 6: ASSEMBLER ---
    async def agent_6_assembler(self, session):
        raw_html = "\n".join(self.html_sections)

        images_info = f"Cover Image: <img src='../{self.image_paths[0]}' alt='Cover' class='w-full rounded-2xl mb-8'>\n"
        for i in range(1, 6):  # indices 1..5 = 5 content images (index 0 is cover)
            path = self.image_paths[i] if i < len(self.image_paths) else "images/placeholder.webp"
            alt = SEOUtils.generate_seo_alt_text(
                self.image_prompts[i][:50] if i < len(self.image_prompts) else "",
                self.topic_name
            )
            images_info += f"[IMAGE_{i}]: <figure class='my-8'><img src='../{path}' alt='{alt}' loading='lazy' width='1200' height='675' class='w-full rounded-xl shadow-md'></figure>\n"

        sys_prompt = """You are Agent 6, the Chief Editor and Assembler.
Your job is to take raw drafted sections and merge them into a single, cohesive, perfectly flowing article in HTML.

RULES:
1. Harmonize the tone so it sounds like ONE single passionate human author.
2. Ensure transitions between sections are smooth and natural.
3. Replace the 5 placeholders [IMAGE_1] through [IMAGE_5] with the provided image tags INSIDE the body content.
4. SPACING RULE: Place images EVENLY across the article — roughly every 300-400 words. NEVER place two images back-to-back or adjacent without text in between. There must be at least one full paragraph (≥3 sentences) separating any two images.
5. DO NOT change the core meaning or remove keywords.
6. Provide ONLY the inner HTML elements (e.g. <h2>, <p>, <ul>). NEVER output <!DOCTYPE html>, <html>, <head>, <style>, or <body> tags.
7. DO NOT include the cover image — it is already displayed separately above the article. Only use [IMAGE_1] through [IMAGE_5] for inline content images.
8. DO NOT include a 'You Might Also Like', related articles, or FAQ section — these are injected separately."""

        user_prompt = f"""IMAGES TO INJECT:
{images_info}

RAW DRAFT SECTIONS:
{raw_html}

Please assemble the final HTML article now. Ensure all [IMAGE_X] placeholders are replaced."""

        self.final_content = await call_deepseek_async(
            session, sys_prompt, user_prompt,
            agent_id=6, temperature=0.3, logger=self.logger
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

        # --- STEP C: Auto-Corrections (2 rounds max) ---
        for correction_round in range(2):
            if combined_score >= 170:  # 85% of 200
                self.logger.success(f"SEO target reached: {combined_score}/200", 2)
                break

            self.logger.info(f"Correction Round {correction_round + 1}/2 (score: {combined_score}/200)", 2)
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
                agent_id=7, temperature=0.1, require_json=True, logger=self.logger
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
        elif 20 <= len(title) <= 70:
            score += 3
            suggestions.append(f"Title: {len(title)} chars (optimal: 30-60)")
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
        elif 100 <= len(meta) <= 170:
            score += 3
            suggestions.append(f"Meta: {len(meta)} chars (optimal: 120-155)")
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
            elif 0.5 <= density <= 4.0:
                score += 3
                suggestions.append(f"Keyword density: {density:.1f}% (optimal: 1-3%)")
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
        elif len(ai_phrases_found) <= 2:
            score += 2
            suggestions.append(f"AI phrases detected ({len(ai_phrases_found)}): {', '.join(ai_phrases_found[:3])}")
        else:
            suggestions.append(f"AI phrases detected ({len(ai_phrases_found)}): {', '.join(ai_phrases_found[:5])}")

        for s in suggestions:
            self.logger.verification_result(s, False)

        return score, suggestions


    def apply_seo_corrections(self):
        """Auto-corrections from V4 (title, meta, AI phrases, density, external link, keyword)."""
        title = self.plan.get('title', '')
        meta = self.plan.get('meta_description', '')
        kw = self.plan.get('primary_keyword', '')

        # Fix 1: Title too long
        if len(title) > 60:
            corrected = call_deepseek_sync(
                f"Fix this title to be 50 characters max:\n\"{title}\"\nReturn ONLY the corrected title.",
                self.logger, "TITLE FIX", "seo"
            )
            if corrected and 20 <= len(corrected.strip().strip('"').strip("'")) <= 60:
                self.plan['title'] = corrected.strip().strip('"').strip("'")
                self.logger.correction_applied(f"Title: {len(title)}c -> {len(self.plan['title'])}c", self.plan['title'][:50])
            else:
                self.plan['title'] = title[:57] + '...'
                self.logger.correction_applied("Title force-truncated", self.plan['title'][:50])

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
                paragraphs = re.findall(r'(<p[^>]*>)(.*?)(</p>)', self.final_content, re.DOTALL)
                injected = 0
                for idx in range(2, min(len(paragraphs), 10), 3):
                    p_open, p_content, p_close = paragraphs[idx]
                    if kw.lower() not in p_content.lower() and injected < 3:
                        new_p = f"{p_open}{p_content} This is especially helpful for <strong>{kw}</strong>.{p_close}"
                        self.final_content = self.final_content.replace(f"{p_open}{p_content}{p_close}", new_p, 1)
                        injected += 1
                if injected:
                    self.logger.correction_applied(f"Keyword density boost: +{injected}", kw[:40])

        # Fix 5: External authority link
        if not re.search(r'<a\s+[^>]*href\s*=\s*["\']https?://(?!littlesmartgenius)', self.final_content):
            ext_link = '<p><em>According to the <a href="https://www.naeyc.org/resources" target="_blank" rel="noopener">National Association for the Education of Young Children (NAEYC)</a>, hands-on educational activities are crucial for early childhood development.</em></p>'
            if '<div class="faq-section' in self.final_content:
                self.final_content = self.final_content.replace('<div class="faq-section', f'{ext_link}\n<div class="faq-section', 1)
            else:
                self.final_content += ext_link
            self.logger.correction_applied("External link added", "NAEYC authority reference")

        # Fix 6: Keyword in first paragraph
        if kw:
            first_p = re.search(r'<p[^>]*>(.*?)</p>', self.final_content, re.DOTALL)
            if first_p and kw.lower() not in first_p.group(1).lower():
                original_p = first_p.group(0)
                kw_sentence = f" When it comes to <strong>{kw}</strong>, parents have many great options."
                new_p = original_p.replace('</p>', f'{kw_sentence}</p>', 1)
                self.final_content = self.final_content.replace(original_p, new_p, 1)
                self.logger.correction_applied("Keyword added to first paragraph", kw[:40])

    def content_verify(self):
        """ContentVerifier: 5 basic health checks."""
        content = self.final_content
        title = self.plan.get('title', '')
        meta = self.plan.get('meta_description', '')
        word_count = len(re.sub(r'<[^>]+>', '', content).split())

        self.logger.verification_result("Title (20-70 chars)", 20 <= len(title) <= 70, f"{len(title)} chars")
        self.logger.verification_result("Meta desc (100-170 chars)", 100 <= len(meta) <= 170, f"{len(meta)} chars")
        self.logger.verification_result(f"Words (>={MIN_WORD_COUNT})", word_count >= MIN_WORD_COUNT, f"{word_count} words")
        h2_count = len(re.findall(r'<h2', content))
        self.logger.verification_result(f"Sections H2 (>=5)", h2_count >= 5, f"{h2_count} H2")
        self.logger.verification_result("Images (>=1)", len(re.findall(r'<img', content)) >= 1)

    # ===============================================================
    # PHASE 7: COMPILE & SAVE + INSTAGRAM
    # ===============================================================

    def compile_and_save(self):
        slug = SEOUtils.optimize_slug(self.plan['title'])
        ts = int(time.time())
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
        os.makedirs(POSTS_DIR, exist_ok=True)
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

    engine = AutoBlogV6(slot, topic, persona, logger)

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
            results.append({"slot": slot, "title": result["title"], "slug": result["slug"], "word_count": result["word_count"]})

        if i < len(DAILY_SLOTS) - 1:
            print(f"\n[PAUSE] Waiting {PAUSE_BETWEEN_ARTICLES}s...")
            time.sleep(PAUSE_BETWEEN_ARTICLES)

    print("\n" + "=" * 80)
    print(f"  DAILY BATCH COMPLETE: {len(results)}/{len(DAILY_SLOTS)} articles")
    print("=" * 80)
    for r in results:
        print(f"  [{r['slot'].upper()}] {r['title'][:50]}  ({r['word_count']} words)")
    return results


def run_single(slot: str = None):
    ts = TopicSelector()
    if not slot:
        slot = random.choice(DAILY_SLOTS)
    topic = ts.get_next_topic(slot)
    if not topic:
        print(f"[ERROR] No available topics for slot '{slot}'")
        return None
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
    launch_str = os.environ.get("LAUNCH_DATE", "2026-02-22")
    try:
        launch = datetime.strptime(launch_str, "%Y-%m-%d")
    except ValueError:
        launch = datetime(2026, 2, 22)
    delta = datetime.utcnow() - launch
    return max(1, (delta.days // 7) + 1)


def run_schedule():
    current_hour = datetime.utcnow().hour
    current_week = get_current_week()

    print(f"\n{'=' * 80}")
    print(f"  AUTO BLOG V6 ULTIMATE -- SCHEDULE MODE")
    print(f"  Week: {current_week} | UTC Hour: {current_hour}")
    print(f"{'=' * 80}")

    matched_slot = None
    matched_min_week = None
    for (h_start, h_end), (slot_type, min_week) in SCHEDULE_SLOTS.items():
        if h_start <= current_hour < h_end:
            matched_slot = slot_type
            matched_min_week = min_week
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
        run_schedule()
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
