"""
PROMPT TEMPLATES — V5.0 SUPREME
Premium prompt architecture for 90/100+ SEO articles.
5 specialized AI roles: SEO Strategist, Expert Writer, Art Director, SEO Auditor, Content Humanizer.
Each returns plan_prompt + content_prompt_builder for the 2-step generation pipeline.
"""


# ═══════════════════════════════════════════════════════════════
# ANTI-AI PHRASES (to detect and remove) — EXTENDED FOR V5.1 DEEPSEEK
# ═══════════════════════════════════════════════════════════════

AI_DETECTION_PHRASES = [
    # Intros / Outros
    "dans cet article", "nous allons découvrir", "il est important de noter", 
    "en conclusion", "pour conclure", "en résumé", "aujourd'hui", "de nos jours",
    "it's important to note", "it is important to note", "in this article",
    "in today's world", "in today's fast-paced", "without further ado",
    "in a nutshell", "at the end of the day", "it goes without saying",
    
    # Transitions
    "moreover", "furthermore", "additionally", "subsequently", "consequently",
    "needless to say", "as a matter of fact", "last but not least",
    "notablement", "cependant", "néanmoins", "par ailleurs", "en outre",
    
    # Vocabulary & Verbs
    "delve into", "delve deeper", "let's delve", "dive into", "deep dive",
    "embark on", "navigate the", "navigate through", "unlock the power",
    "unlock the potential", "leverage", "utilize", "facilitate", "foster",
    "spearhead", "orchestrate", "elevate", "optimize", "maximize",
    
    # Metaphors & Nouns
    "tapestry of", "plethora of", "symphony of", "myriad of", "cornucopia of",
    "paradigm shift", "game-changer", "testament to", "crucial", "pivotal",
    "comprehensive guide", "comprehensive overview", "in the realm of",
    "in the world of", "landscape", "beacon of", "cornerstone"
]

# Transition words that signal human writing
TRANSITION_WORDS = [
    "here's the thing", "honestly", "look", "okay so", "let's be real",
    "in my experience", "what I've found", "here's why", "think about it",
    "the truth is", "real talk", "fun fact", "by the way", "plus",
    "quick tip", "one thing I love", "something I noticed", "the best part?",
    "you know what", "I'll be honest", "between you and me", "the reality is",
    "bottom line", "long story short", "the good news", "the catch?",
    "here's what works", "here's a secret", "pro tip", "fair warning",
]


# ═══════════════════════════════════════════════════════════════
# LSI KEYWORD CLUSTERS (semantic SEO)
# ═══════════════════════════════════════════════════════════════

LSI_CLUSTERS = {
    "spot the difference": [
        "visual perception", "observation skills", "attention to detail",
        "cognitive development", "visual discrimination", "focus activities",
        "brain games", "picture puzzles", "find differences", "visual scanning"
    ],
    "word search": [
        "vocabulary building", "letter recognition", "spelling practice",
        "word puzzles", "word games", "reading skills", "phonics",
        "hidden words", "word hunt", "language arts"
    ],
    "math": [
        "number sense", "arithmetic", "counting skills", "problem solving",
        "mathematical thinking", "numeracy", "number recognition",
        "math games", "mental math", "math practice"
    ],
    "critical thinking": [
        "logic puzzles", "reasoning skills", "problem solving",
        "analytical thinking", "decision making", "strategic thinking",
        "cognitive skills", "brain teasers", "logical reasoning", "deduction"
    ],
    "montessori": [
        "hands-on learning", "self-directed", "sensory activities",
        "practical life skills", "prepared environment", "child-led",
        "tactile learning", "fine motor skills", "independence", "exploration"
    ],
    "printable": [
        "worksheets", "educational activities", "downloadable",
        "PDF resources", "classroom materials", "homeschool",
        "teaching resources", "learning materials", "activity sheets", "workbook"
    ],
    "coloring": [
        "fine motor skills", "creativity", "color recognition",
        "hand-eye coordination", "artistic expression", "coloring pages",
        "art activities", "creative play", "color therapy", "drawing"
    ],
}


def _get_lsi_keywords(topic: str) -> list:
    """Find the best LSI keyword cluster for a topic."""
    topic_lower = topic.lower()
    best_cluster = []
    best_score = 0
    for key, cluster in LSI_CLUSTERS.items():
        if key in topic_lower:
            score = len(key)
            if score > best_score:
                best_score = score
                best_cluster = cluster
    if not best_cluster:
        # Fallback: general education cluster
        best_cluster = [
            "child development", "learning activities", "educational resources",
            "cognitive skills", "fine motor skills", "age-appropriate",
            "hands-on learning", "classroom activities", "homeschool", "printable worksheets"
        ]
    return best_cluster


# ═══════════════════════════════════════════════════════════════
# 1. KEYWORD ARTICLE PROMPTS (SEO Informational)
# ═══════════════════════════════════════════════════════════════

def build_keyword_prompt(keyword: str, persona: dict) -> dict:
    """
    Build premium prompts for a pure SEO informational article.
    V5.0: Enhanced with LSI keywords, keyword density targets, and anti-AI instructions.
    """
    lsi_keywords = _get_lsi_keywords(keyword)
    lsi_str = ", ".join(lsi_keywords[:8])

    plan_prompt = f"""You are a Senior SEO Content Strategist with 10+ years experience ranking 500+ articles on Google page 1 for educational niches.

IDENTITY: {persona['role']}
EXPERTISE: {persona['expertise']}
VOICE: {persona['tone']}

═══ MISSION ═══
Create a DETAILED article blueprint for "Little Smart Genius" blog that WILL rank on Google for:

PRIMARY KEYWORD: "{keyword}"
LSI KEYWORDS: {lsi_str}
AUDIENCE: Parents and educators of children aged 4-12
ARTICLE TYPE: Informational SEO pillar content (2000+ words)

═══ OUTPUT FORMAT (JSON ONLY — no markdown, no explanation) ═══
{{
  "title": "SEO title — 30-60 chars, keyword in FIRST 3 WORDS, use power word (Best/Ultimate/Essential/Proven/Top)",
  "meta_description": "120-155 chars, include keyword naturally, end with call-to-action or benefit",
  "primary_keyword": "{keyword}",
  "lsi_keywords": {lsi_keywords[:6]},
  "target_keyword_density": "1.5-2.5%",
  "cover_concept": "Detailed visual: [SCENE] + [SUBJECTS] + [ACTION] + [MOOD] + [COLORS]. Example: 'A bright, warm classroom with a 6-year-old girl joyfully solving a colorful puzzle at her desk, sunlight streaming through windows, pastel yellows and soft blues, 3D Pixar-style illustration, depth of field, ultra-detailed'",
  "sections": [
    {{
      "h2": "Section title — MUST include keyword variation or LSI keyword, use question format when natural",
      "h3_subsections": ["Subsection 1 (specific, actionable)", "Subsection 2", "Subsection 3"],
      "key_points": ["Detailed point with example", "Point with statistic or research reference", "Actionable tip with age-specific advice"],
      "image_concept": "UNIQUE visual concept for this section — different composition, subject, and dominant color from other sections. Format: [SCENE] + [SUBJECTS] + [ACTION] + [STYLE]",
      "internal_link_opportunity": "Phrase that could naturally link to freebies.html, products.html, or blog.html"
    }}
  ],
  "faq": [
    {{"q": "People Also Ask style question (start with What/How/Why/When/Is)?", "a": "Direct answer in 2-3 sentences. Include a specific fact, age range, or actionable tip."}}
  ]
}}

═══ MANDATORY REQUIREMENTS ═══
- 6 main sections (H2) — each with a keyword variation or LSI keyword
- 3 subsections (H3) per H2 = 18 total subsections
- 5 UNIQUE image concepts (different scenes, compositions, dominant colors)
- 5 FAQ questions targeting Google's "People Also Ask"
- Internal link opportunities in at least 3 sections
- Cover concept must be specific enough to generate a premium image
- Title MUST start with the keyword or a very close variation

═══ STYLE RULES ═══
- H2 titles should use power words: "Best", "Ultimate", "Essential", "How to", "Why", "Top"
- FAQ answers should be direct (start with the answer, not filler)
- Image concepts must each have a DIFFERENT dominant scene and color palette"""

    def content_prompt_builder(plan: dict, target_words: int = 2000) -> str:
        import json
        sections_json = json.dumps(
            [{"h2": s.get("h2"), "h3": s.get("h3_subsections", []),
              "points": s.get("key_points", []),
              "link_opportunity": s.get("internal_link_opportunity", "")}
             for s in plan.get("sections", [])],
            indent=2
        )
        faq_json = json.dumps(plan.get("faq", []), indent=2)
        lsi_from_plan = plan.get("lsi_keywords", lsi_keywords[:6])
        lsi_plan_str = ", ".join(lsi_from_plan) if isinstance(lsi_from_plan, list) else str(lsi_from_plan)

        return f"""You are {persona['role']} writing for the "Little Smart Genius" educational blog.
You write like a REAL HUMAN — warm, personal, slightly informal. You are NOT an AI.

═══ ARTICLE SPECS ═══
Title: {plan.get('title', keyword)}
Primary Keyword: {plan.get('primary_keyword', keyword)}
LSI Keywords (weave naturally): {lsi_plan_str}
Target: {target_words} words MINIMUM (aim for 2000-2200)
Article Type: SEO Informational — must rank on Google for "{keyword}"

═══ WRITING PERSONALITY & RHYTHM (CRITICAL ANTI-AI) ═══
- Write like a REAL HUMAN writing to a friend: authentic, slightly informal, nuanced.
- VARY YOUR RHYTHM (Burstiness): Mix very short, punchy sentences (2-5 words) with longer, flowing ones.
- NO SYMMETRY: Do NOT use a perfectly balanced "H2 -> intro paragraph -> bullet list -> conclusion" format in every section. Break the pattern.
- Be concrete: Use real-world examples, not theoretical fluff.
- Include transitions naturally: "Here's the thing", "Honestly", "Plus".
- NEVER start an introduction with "In this article..." or "Today we will discover...".
- Use ACTIVE VOICE exclusively.

═══ BANNED PHRASES (AI detection — NEVER use these) ═══
"It's important to note", "Moreover", "Furthermore", "In conclusion", "Delve into",
"Dive into", "In today's world", "Comprehensive guide", "Embark on", "Navigate the",
"Leverage", "Utilize", "Facilitate", "Game-changer", "Unlock the potential",
"Without further ado", "Needless to say", "Plethora of", "Tapestry of", "Testament to",
"Crucial", "Pivotal", "Dans cet article", "Nous allons", "Il est important de"

═══ STRUCTURE ═══
1. INTRODUCTION (150-200 words):
   - Open with a relatable scenario or quick personal story about {keyword}
   - State the problem parents face (why they're searching)
   - Promise what they'll learn (be specific: "5 techniques", "3 activities")
   - Include PRIMARY KEYWORD in the first 100 words naturally

2. MAIN CONTENT — Follow this structure:
{sections_json}

3. CONCLUSION (100-150 words):
   - Practical 3-point summary (what to remember)
   - Encouragement for parents
   - Mention "free worksheets" and "premium resources" naturally for internal linking

4. FAQ SECTION:
{faq_json}

═══ TECHNICAL SEO REQUIREMENTS (NON-NEGOTIABLE) ═══
- Include "{keyword}" in first paragraph + last paragraph
- Use keyword 8-12 times total (1.5-2.5% density for 2000 words)
- Each H2 must contain a keyword variation or LSI keyword
- Include at least 2 numbered lists (<ol>) and 2 bulleted lists (<ul>)
- Bold the keyword with <strong> 3-5 times across different sections
- Insert [IMAGE_1], [IMAGE_2], [IMAGE_3], [IMAGE_4], [IMAGE_5] placed in different sections evenly spaced (roughly every 400 words), each after a paragraph ending — NEVER two images in succession
- Include internal link anchors naturally: "free worksheets", "free printables", "premium resources", "educational activities"
- Include 1 external authority reference (mention a study, organization, or expert)

═══ HTML FORMAT ═══
- Use: <h2>, <h3>, <p>, <ul>, <ol>, <li>, <strong>, <em>, <figure>, <blockquote>
- NO <html>, <head>, <body>, or <style> tags
- Use <strong> for keywords (3-5 times max)
- Use <em> for emphasis on tips and important phrases
- Use <blockquote> for 1 expert quote or parent testimonial"""

    return {"plan_prompt": plan_prompt, "content_prompt_builder": content_prompt_builder}


# ═══════════════════════════════════════════════════════════════
# 2. PRODUCT REVIEW PROMPTS
# ═══════════════════════════════════════════════════════════════

def build_product_prompt(product_data: dict, persona: dict) -> dict:
    """
    Build premium prompts for a product review/showcase article.
    V5.0: Educational value first, product recommendation second.
    """
    product_name = product_data.get("name", "Educational Worksheet")
    product_url = product_data.get("url", "")
    product_price = product_data.get("price", "")
    product_category = product_data.get("category", "Education")
    lsi_keywords = _get_lsi_keywords(product_category)
    lsi_str = ", ".join(lsi_keywords[:8])

    plan_prompt = f"""You are a Senior SEO Content Strategist specializing in educational product reviews.

IDENTITY: {persona['role']}
EXPERTISE: {persona['expertise']}
VOICE: {persona['tone']}

═══ MISSION ═══
Create an article blueprint that EDUCATES first and RECOMMENDS second.
This is NOT a sales page — it's a genuine educational guide that naturally features a recommended resource.

PRODUCT: {product_name}
CATEGORY: {product_category}
PRICE: {product_price}
URL: {product_url}
LSI KEYWORDS: {lsi_str}
AUDIENCE: Parents and teachers of children aged 4-12

═══ OUTPUT FORMAT (JSON ONLY) ═══
{{
  "title": "SEO title 30-60 chars — educational angle, NOT 'Review of X'. Use format: 'How [Activity Type] Boosts [Skill] in Kids' or 'Best [Activity Type] for [Age Group]'",
  "meta_description": "120-155 chars — mention educational benefit + call to action",
  "primary_keyword": "derived keyword (e.g., '{product_category.lower()} activities for kids')",
  "lsi_keywords": ["6 LSI keywords relevant to this product type"],
  "cover_concept": "Specific visual: child using {product_category} materials in a bright setting",
  "sections": [
    {{
      "h2": "Section title with keyword variation",
      "h3_subsections": ["Sub 1", "Sub 2", "Sub 3"],
      "key_points": ["Point 1", "Point 2", "Point 3"],
      "image_concept": "Unique visual concept — different from other sections",
      "internal_link_opportunity": "Natural anchor text for internal link"
    }}
  ],
  "product_spotlight": {{
    "headline": "Why We Recommend {product_name}",
    "benefits": ["3 specific benefits"],
    "age_range": "Best age range for this product",
    "cta_text": "Natural CTA text"
  }},
  "faq": [
    {{"q": "Question about this activity type?", "a": "Helpful answer"}}
  ]
}}

═══ SECTION PLAN ═══
- Section 1: Why [activity type] matters for child development (research-backed)
- Section 2: Age-specific benefits (4-6, 7-9, 10-12)
- Section 3: How to use [activity type] at home/classroom (step-by-step)
- Section 4: PRODUCT SPOTLIGHT — naturally introduce {product_name} as a recommended resource
- Section 5: Tips and creative variations
- Section 6: Common mistakes parents make with [activity type]
- 5 FAQ questions
- 4 unique image concepts"""

    def content_prompt_builder(plan: dict, target_words: int = 2000) -> str:
        import json
        sections_json = json.dumps(
            [{"h2": s.get("h2"), "h3": s.get("h3_subsections", []),
              "points": s.get("key_points", [])}
             for s in plan.get("sections", [])],
            indent=2
        )
        faq_json = json.dumps(plan.get("faq", []), indent=2)
        spotlight = plan.get("product_spotlight", {})

        return f"""You are {persona['role']} writing an educational guide with product recommendation.
Write like a REAL HUMAN — passionate educator, NOT a salesperson.

═══ ARTICLE SPECS ═══
Title: {plan.get('title', product_name)}
Primary Keyword: {plan.get('primary_keyword', '')}
Product: {product_name} ({product_price})
Product Link: {product_url}
Target: {target_words} words MINIMUM
RATIO: 80% educational value, 20% product recommendation

═══ WRITING PERSONALITY & RHYTHM (CRITICAL ANTI-AI) ═══
- Write as a passionate, real educator, not a salesperson or encyclopedia.
- Share a classroom/parenting experience (1-2 sentences in intro). MUST feel authentic.
- VARY YOUR RHYTHM (Burstiness): Mix very short, spontaneous sentences (2-5 words) with longer explanations.
- NO SYMMETRY: Do NOT use the exact same paragraph-list structure in every section. 
- Break the pattern. Add a 1-sentence paragraph for emphasis.
- Include tips that work even WITHOUT buying the product.
- Use transitions like: "Let's be real", "What I've found works best", "One thing I love about".
- NEVER start an introduction with "In this article..." or "Today we will explore...".

═══ BANNED PHRASES (AI detection — NEVER use these) ═══
"It's important to note", "Moreover", "Furthermore", "In conclusion", "Delve into",
"Dive into", "In today's world", "Comprehensive guide", "Embark on", "Navigate the",
"Leverage", "Utilize", "Facilitate", "Game-changer", "Unlock the potential",
"Without further ado", "Needless to say", "Plethora of", "Tapestry of", "Testament to",
"Crucial", "Pivotal", "Dans cet article", "Nous allons", "Il est important de"

═══ STRUCTURE ═══
1. INTRODUCTION (150-200 words):
   - Personal classroom story about using {product_category} activities
   - Why this skill matters (cite 1 study or expert opinion)
   - What readers will learn

2. MAIN CONTENT:
{sections_json}

3. PRODUCT SPOTLIGHT:
   - Headline: "{spotlight.get('headline', f'Why We Love {product_name}')}"
   - Naturally introduce {product_name} as YOUR recommended resource
   - Mention specific features and age groups: {spotlight.get('age_range', 'ages 4-12')}
   - Include CTA: '<a href="{product_url}" target="_blank" rel="noopener">Check out {product_name} on TPT</a>'
   - Keep it genuine — 1-2 paragraphs max, NOT a sales pitch

4. CONCLUSION + FAQ:
{faq_json}

═══ TECHNICAL SEO (NON-NEGOTIABLE) ═══
- Keyword in first 100 words + last paragraph
- Keyword density 1.5-2.5%
- 2 numbered lists + 2 bulleted lists
- Bold keyword 3-5 times with <strong>
- [IMAGE_1] to [IMAGE_4] in different sections
- Internal link anchors: "free worksheets", "premium resources"
- Product link appears 2 times max (natural, not forced)
- HTML only: <h2>, <h3>, <p>, <ul>, <ol>, <li>, <strong>, <em>, <blockquote>
- NO <html>, <head>, <body> tags"""

    return {"plan_prompt": plan_prompt, "content_prompt_builder": content_prompt_builder}


# ═══════════════════════════════════════════════════════════════
# 3. FREEBIE TUTORIAL PROMPTS
# ═══════════════════════════════════════════════════════════════

def build_freebie_prompt(freebie_data: dict, persona: dict) -> dict:
    """
    Build premium prompts for a freebie tutorial/activity guide.
    V5.0: Step-by-step tutorial with free download CTA.
    """
    freebie_name = freebie_data.get("name", "Educational Activity")
    freebie_url = freebie_data.get("url", "")
    freebie_desc = freebie_data.get("desc", "")
    lsi_keywords = _get_lsi_keywords(freebie_name)
    lsi_str = ", ".join(lsi_keywords[:8])

    plan_prompt = f"""You are a Senior SEO Content Strategist specializing in educational tutorial content.

IDENTITY: {persona['role']}
EXPERTISE: {persona['expertise']}
VOICE: {persona['tone']}

═══ MISSION ═══
Create a TUTORIAL article blueprint that teaches parents how to use a free activity with their children.
The article educates FIRST, then offers the free download as a bonus.

FREE RESOURCE: {freebie_name}
DESCRIPTION: {freebie_desc}
DOWNLOAD: {freebie_url}
LSI KEYWORDS: {lsi_str}
AUDIENCE: Parents and teachers of children aged 4-12

═══ OUTPUT FORMAT (JSON ONLY) ═══
1. INTENT & E-E-A-T FOCUS (CRITICAL)
   - Every plan MUST include a pedagogical focus: What is the goal? Who is it for (Age/Grade)?
   - Include sections for "Materials Needed", "Step-by-Step Instructions", and "Variations/Modifications".
   - The FAQ MUST address real parent/teacher concerns (e.g., "What if my child gets frustrated?").  

2. The response must be valid JSON matching this schema exactly:
{{
  "title": "Engaging and emotional title with the primary keyword",
  "slug": "seo-friendly-url-slug-no-stopwords",
  "meta_description": "Compelling meta description addressing the parent/teacher's pain point.",
  "primary_keyword": "{freebie_name.lower()} for kids",
  "keywords": ["LSI keyword 1", "LSI keyword 2", "LSI keyword 3"],
  "category": "education",
  "cover_concept": "High-quality scene showing...",
  "sections": [
    {{
      "h2": "Pedagogical Goal & Why This Works",
      "h3s": ["Cognitive Benefits", "Ideal Age Group"],
      "image_concept": "Vector illustration showing..."
    }},
    {{
      "h2": "Materials Needed & Preparation",
      "h3s": []
    }},
    {{
      "h2": "Step-by-Step Activity Instructions",
      "h3s": ["Step 1: Setup", "Step 2: Execution", "Variations for Older/Younger Kids"]
    }}
  ],
  "faq_schema": [
    {{"q": "Real parent question?", "a": "Detailed answer."}},
    {{"q": "Real teacher question?", "a": "Detailed answer."}}
  ]
}}

═══ SECTION PLAN ═══
- Section 1: What is {freebie_name} and why kids love it
- Section 2: Skills it develops (cognitive, motor, social)
- Section 3: Step-by-step guide (how to use effectively)
- Section 4: Age-specific tips (younger vs older kids)
- Section 5: Creative variations and extensions
- Section 6: FREE DOWNLOAD section with CTA
- 5 FAQ questions
- 4 unique image concepts"""

    def content_prompt_builder(plan: dict, target_words: int = 2000) -> str:
        import json
        sections_json = json.dumps(
            [{"h2": s.get("h2"), "h3": s.get("h3_subsections", []),
              "points": s.get("key_points", [])}
             for s in plan.get("sections", [])],
            indent=2
        )
        faq_json = json.dumps(plan.get("faq", []), indent=2)
        download = plan.get("download_cta", {})

        return f"""You are {persona['role']} writing a tutorial guide for a free educational resource.
Write like a REAL HUMAN — enthusiastic, helpful friend, NOT an AI.

═══ ARTICLE SPECS ═══
Title: {plan.get('title', freebie_name)}
Primary Keyword: {plan.get('primary_keyword', '')}
Free Resource: {freebie_name}
Download Link: {freebie_url}
Target: {target_words} words MINIMUM
TONE: Enthusiastic friend explaining their favorite activity

═══ WRITING PERSONALITY & RHYTHM (CRITICAL ANTI-AI) ═══
- Write like a REAL HUMAN excitedly sharing a find with a friend.
- Include a quick personal anecdote about using this activity.
- VARY YOUR RHYTHM (Burstiness): Mix very short, punchy sentences (2-5 words) with longer explanations.
- NO SYMMETRY: Break the mold. Don't use the exact same format for every section.
- Be step-by-step practical (number your instructions), but keep the tone conversational.
- Use transitions like: "Here's the fun part", "What I love about this", "Pro tip from experience".
- NEVER start an introduction with "In this article..." or "Today we will discover...".

═══ BANNED PHRASES (AI detection — NEVER use these) ═══
"It's important to note", "Moreover", "Furthermore", "In conclusion", "Delve into",
"Dive into", "In today's world", "Comprehensive guide", "Embark on", "Navigate the",
"Leverage", "Utilize", "Facilitate", "Game-changer", "Unlock the potential",
"Without further ado", "Needless to say", "Plethora of", "Tapestry of", "Testament to",
"Crucial", "Pivotal", "Dans cet article", "Nous allons", "Il est important de"

═══ STRUCTURE ═══
1. INTRODUCTION (150-200 words):
   - Fun hook about {freebie_name}
   - What skills it develops (be specific)
   - Mention it's available as a FREE printable

2. MAIN CONTENT:
{sections_json}

3. FREE DOWNLOAD CTA:
   Create this exact HTML block:
   '<div class="download-cta" style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); padding: 30px; border-radius: 15px; margin: 30px 0; text-align: center;">
     <h3 style="color: white; margin-bottom: 10px;">{download.get("headline", f"Download {freebie_name} — FREE!")}</h3>
     <p style="color: white; margin-bottom: 15px;">{download.get("description", freebie_desc)}</p>
     <a href="{freebie_url}" target="_blank" rel="noopener" style="background: white; color: #059669; padding: 12px 30px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block;">Download Now (Free PDF)</a>
   </div>'

4. CONCLUSION + FAQ:
{faq_json}

═══ TECHNICAL SEO (NON-NEGOTIABLE) ═══
- Keyword in first 100 words + last paragraph
- Keyword density 1.5-2.5%
- 2 numbered lists + 2 bulleted lists
- Bold keyword 3-5 times with <strong>
- [IMAGE_1] to [IMAGE_4] in different sections
- Internal links: "free worksheets", "premium resources"
- Download link appears 2-3 times (intro + CTA section + conclusion)
- HTML only: <h2>, <h3>, <p>, <ul>, <ol>, <li>, <strong>, <em>
- NO <html>, <head>, <body> tags"""

    return {"plan_prompt": plan_prompt, "content_prompt_builder": content_prompt_builder}


# ═══════════════════════════════════════════════════════════════
# 4. ART DIRECTOR PROMPT (V5.0 — 4 unique styles)
# ═══════════════════════════════════════════════════════════════

IMAGE_STYLE_PRESETS = [
    {
        "name": "Hero / Establishing Shot",
        "composition": "Wide shot, rule of thirds, subject in center-left",
        "style": "3D Pixar-style illustration, ultra-detailed, 8K render quality",
        "lighting": "Warm golden hour lighting, soft shadows, volumetric light",
        "palette": "Warm: amber, soft coral, cream, teal accents",
    },
    {
        "name": "Close-up / Hands-on",
        "composition": "Close-up, shallow depth of field, overhead or 45-degree angle",
        "style": "Soft watercolor style with crisp edges, gentle textures",
        "lighting": "Diffused natural light, minimal shadows",
        "palette": "Cool: lavender, mint green, baby blue, white",
    },
    {
        "name": "Infographic / Process",
        "composition": "Clean layout, centered, isometric perspective",
        "style": "Flat illustration with subtle gradients, modern vector look",
        "lighting": "Even, flat lighting, no harsh shadows",
        "palette": "Vibrant: coral, turquoise, sunshine yellow, navy blue",
    },
    {
        "name": "Lifestyle / Context",
        "composition": "Environmental portrait, medium shot, natural setting",
        "style": "3D clay rendering, Claymation-inspired, tactile feel",
        "lighting": "Soft morning light, gentle rim lighting on subjects",
        "palette": "Earthy: sage green, warm brown, peach, ivory",
    },
]

def build_art_director_prompt(basic_concept: str, context: str, image_index: int) -> str:
    """
    Build a specialized art director prompt for each image position.
    V5.0: Each image gets a unique style preset to ensure visual diversity.
    """
    preset = IMAGE_STYLE_PRESETS[image_index % len(IMAGE_STYLE_PRESETS)]

    return f"""You are an expert Art Director with 20 years in children's educational content.

═══ YOUR TASK ═══
Transform this basic concept into a PREMIUM image prompt for Flux Klein-Large (9B parameters).

BASIC CONCEPT: {basic_concept}
ARTICLE CONTEXT: {context}
IMAGE ROLE: {preset['name']} (Image #{image_index + 1})
TARGET: Parents and teachers of children aged 4-12

═══ STYLE PRESET ═══
- Composition: {preset['composition']}
- Style: {preset['style']}
- Lighting: {preset['lighting']}
- Color Palette: {preset['palette']}

═══ RULES (NON-NEGOTIABLE) ═══
- ABSOLUTELY NO text, letters, words, numbers, labels, captions, or symbols inside the image
- NO brand logos, watermarks, or UI overlays of any kind
- If the scene includes papers, worksheets, or screens — they must be blank or filled with abstract patterns ONLY (no readable text)
- Children depicted should be diverse (mix ethnicities)
- Keep it child-safe and family-friendly
- Include educational elements (books, puzzles, worksheets visible)
- Subjects should show JOY and ENGAGEMENT
- Pure visual storytelling only — communicate emotion and action, not text

═══ OUTPUT ═══
Return ONLY the enhanced prompt as 1-2 sentences. Include specific details about:
1. Scene and setting
2. Subject(s) and their action
3. Emotional tone
4. Technical specs (style, lighting, quality)

Now enhance:
{basic_concept}"""


# ═══════════════════════════════════════════════════════════════
# 5. ROUTER
# ═══════════════════════════════════════════════════════════════

def get_prompt_builder(slot: str):
    """Return the appropriate prompt builder function for a slot."""
    builders = {
        "keyword": build_keyword_prompt,
        "product": build_product_prompt,
        "freebie": build_freebie_prompt,
    }
    if slot not in builders:
        raise ValueError(f"Unknown slot: {slot}. Use 'keyword', 'product', or 'freebie'.")
    return builders[slot]


# --- Self-test ---
if __name__ == "__main__":
    print("=" * 60)
    print("PROMPT TEMPLATES V5.0 — Self Test")
    print("=" * 60)

    test_persona = {
        "id": "Sarah_Teacher",
        "role": "Elementary School Teacher (15 years experience)",
        "expertise": "Classroom management, differentiated instruction",
        "tone": "Warm, professional, evidence-based",
        "img_style": "bright classroom, educational setting, 3D Pixar style"
    }

    # Test keyword prompt
    result = build_keyword_prompt("printable logic puzzles for kids ages 6-10", test_persona)
    assert "plan_prompt" in result
    assert callable(result["content_prompt_builder"])
    print(f"\n[KEYWORD] Plan prompt: {len(result['plan_prompt'])} chars")

    # Test content prompt builder
    test_plan = {
        "title": "Best Printable Logic Puzzles for Kids Ages 6-10",
        "primary_keyword": "printable logic puzzles for kids",
        "lsi_keywords": ["cognitive skills", "critical thinking"],
        "sections": [{"h2": "Why Logic Puzzles Matter", "h3_subsections": ["Brain Development"], "key_points": ["Point 1"]}],
        "faq": [{"q": "What age should kids start logic puzzles?", "a": "Age 4-5 with simple puzzles."}]
    }
    content = result["content_prompt_builder"](test_plan)
    assert "NON-NEGOTIABLE" in content
    assert "BANNED PHRASES" in content
    print(f"[KEYWORD] Content prompt: {len(content)} chars")

    # Test product prompt
    result = build_product_prompt({
        "name": "Spot the Difference Animals Vol.1",
        "url": "https://example.com/product",
        "price": "$3.00",
        "category": "Spot the Difference"
    }, test_persona)
    assert "plan_prompt" in result
    print(f"[PRODUCT] Plan prompt: {len(result['plan_prompt'])} chars")

    # Test freebie prompt
    result = build_freebie_prompt({
        "name": "Sudoku",
        "url": "https://example.com/download",
        "desc": "Classic number puzzle for logical thinking",
    }, test_persona)
    assert "plan_prompt" in result
    print(f"[FREEBIE] Plan prompt: {len(result['plan_prompt'])} chars")

    # Test art director
    art_prompt = build_art_director_prompt(
        "A child solving puzzles", "Logic puzzles article", 0
    )
    assert "Flux Klein-Large" in art_prompt
    print(f"[ART DIR] Prompt: {len(art_prompt)} chars")

    # Test LSI keywords
    lsi = _get_lsi_keywords("spot the difference puzzles")
    assert len(lsi) > 0
    print(f"[LSI] Found {len(lsi)} keywords for 'spot the difference puzzles'")

    print(f"\n[AI DETECT] {len(AI_DETECTION_PHRASES)} banned phrases loaded")
    print(f"[STYLES] {len(IMAGE_STYLE_PRESETS)} image style presets loaded")

    print("\nAll V5.0 tests passed!")
