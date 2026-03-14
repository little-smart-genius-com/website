"""
MASTER PROMPTS V8 — Ultimate 3D Pixar-style image generation.
This version holds 6 highly detailed, distinct lighting/style prompt templates
provided by the user for Cover + Img1 through Img5.
"""

# Image 1 de couverture : Intense Golden Hour
PROMPT_COVER = (
    "A feature-film quality 3D CGI render in the distinct modern Pixar/Disney animation style, featuring [SUJET]. "
    "The scene utilizes dramatic golden hour cinematography with intense, warm backlighting creating prominent rim lights "
    "on subjects and volumetric sun rays. The atmosphere is glowing and highly textured with a shallow depth of field. "
    "8K resolution masterpiece with photorealistic rendering engine details; the entire image is rendered explicitly "
    "without containing any text, letters, words, numbers, watermarks, signatures, deformed anatomy, distorted faces, "
    "ugly features, poorly drawn hands, missing limbs, extra fingers, mutated shapes, blurry artifacts, low resolution areas, "
    "bad proportions, crossed eyes, creepy expressions, or floating objects."
)

# Image 2 (img1) : Bright & Airy Morning
PROMPT_IMG1 = (
    "A pristine 3D CGI animated render in the modern Pixar/Disney style, featuring [SUJET], focused on clean geometry "
    "and soft, inviting textures. The lighting setup is high-key and airy, simulating clean morning daylight with balanced "
    "exposure, soft diffused shadows, and a fresh, cheerful color grading. The background is smoothly blurred. 8K resolution, "
    "highly detailed render; the entire image is rendered explicitly without containing any text, letters, words, numbers, "
    "watermarks, signatures, deformed anatomy, distorted faces, ugly features, poorly drawn hands, missing limbs, extra fingers, "
    "mutated shapes, blurry artifacts, low resolution areas, bad proportions, crossed eyes, creepy expressions, or floating objects."
)

# Image 3 (img2) : Cozy Evening Intimacy
PROMPT_IMG2 = (
    "A highly detailed 3D animated render in the modern Pixar production style, featuring [SUJET]. The lighting is a low-key "
    "interior setup, characterized by deep, warm tones from practical light sources creating an intimate and tranquil mood. "
    "Emphasis on rich texture details, warm highlights, and significant bokeh depth of field. 8K masterpiece render; the entire "
    "image is rendered explicitly without containing any text, letters, words, numbers, watermarks, signatures, deformed anatomy, "
    "distorted faces, ugly features, poorly drawn hands, missing limbs, extra fingers, mutated shapes, blurry artifacts, "
    "low resolution areas, bad proportions, crossed eyes, creepy expressions, or floating objects."
)

# Image 4 (img3) : Soft Dappled Natural Light
PROMPT_IMG3 = (
    "A high-quality 3D CGI render displaying modern Disney/Pixar animation aesthetics, featuring [SUJET] with gentle, "
    "rounded character designs. The lighting is naturalistic and tranquil, utilizing a dappled sunlight effect through off-camera "
    "foliage to create soft, organic light and shadow patterns across the scene. 8K resolution, photorealistic texture rendering; "
    "the entire image is rendered explicitly without containing any text, letters, words, numbers, watermarks, signatures, "
    "deformed anatomy, distorted faces, ugly features, poorly drawn hands, missing limbs, extra fingers, mutated shapes, "
    "blurry artifacts, low resolution areas, bad proportions, crossed eyes, creepy expressions, or floating objects."
)

# Image 5 (img4) : Vibrant & Joyful Daytime
PROMPT_IMG4 = (
    "A vibrant 3D animated CGI render in the professional style of modern Pixar, featuring [SUJET]. The art direction emphasizes "
    "a highly saturated color palette, soft expressive textures, and clean forms. The illumination is bright, even daytime lighting, "
    "optimizing color pop and creating an energetic atmosphere with a clean focus fall-off in the background. 8K masterpiece quality; "
    "the entire image is rendered explicitly without containing any text, letters, words, numbers, watermarks, signatures, "
    "deformed anatomy, distorted faces, ugly features, poorly drawn hands, missing limbs, extra fingers, mutated shapes, "
    "blurry artifacts, low resolution areas, bad proportions, crossed eyes, creepy expressions, or floating objects."
)

# Image 6 (img5) : Soft Overcast Diffused Light
PROMPT_IMG5 = (
    "A high-fidelity 3D animated CGI render in the modern Pixar/Disney animation style, featuring [SUJET]. The lighting scenario "
    "is soft, diffused daylight typical of an overcast sky, resulting in ultra-soft, nearly invisible shadows and a peaceful, "
    "comforting interior ambiance. Emphasis on tactile material textures and a warmly blurred background with shallow depth of field. "
    "8K resolution masterpiece; the entire image is rendered explicitly without containing any text, letters, words, numbers, "
    "watermarks, signatures, deformed anatomy, distorted faces, ugly features, poorly drawn hands, missing limbs, extra fingers, "
    "mutated shapes, blurry artifacts, low resolution areas, bad proportions, crossed eyes, creepy expressions, or floating objects."
)

PROMPTS = [
    PROMPT_COVER,
    PROMPT_IMG1,
    PROMPT_IMG2,
    PROMPT_IMG3,
    PROMPT_IMG4,
    PROMPT_IMG5
]

def build_prompt(subject_description: str, image_index: int = 0) -> str:
    """
    Returns the full prompt with the [SUJET] placeholder replaced,
    using the specific template for the given image index.
    """
    if image_index < 0 or image_index >= len(PROMPTS):
        image_index = 0
    template = PROMPTS[image_index]
    return template.replace("[SUJET]", subject_description)
