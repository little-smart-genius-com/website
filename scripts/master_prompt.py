"""
MASTER PROMPT for 3D Pixar-style image generation.
This file stores the canonical master prompt template that the Art Director
(DeepSeek) must use as a base. The Art Director only replaces the [SUBJECT] placeholder.
"""

MASTER_PROMPT = (
    "A high-quality 3D animated CGI render in the style of modern Pixar or Disney animation, "
    "featuring a diverse group of joyful young children with expressive big eyes, soft rounded features, "
    "and warm smiles, [SUBJECT]. "
    "The scene is set in a bright, tidy, and cozy indoor classroom environment with bookshelves, "
    "educational toys, and plants in a softly blurred background using a shallow depth of field. "
    "The lighting is incredibly warm, cheerful, and cinematic, with golden sunlight streaming through "
    "a nearby window, casting beautiful soft glowing rim lights on the subjects' hair and cozy clothing, "
    "creating a focused and educational atmosphere, 8k resolution, highly detailed masterpiece; "
    "the entire image is rendered explicitly without containing any text, letters, words, numbers, "
    "watermarks, signatures, deformed anatomy, distorted faces, ugly features, poorly drawn hands, "
    "missing limbs, extra fingers, mutated shapes, blurry artifacts, low resolution areas, bad proportions, "
    "crossed eyes, creepy expressions, or floating objects"
)


def build_prompt(subject_description: str) -> str:
    """
    Returns the full prompt with the [SUBJECT] placeholder replaced.
    
    Args:
        subject_description: e.g. "sitting around a table solving a colorful jigsaw puzzle together"
    
    Returns:
        The complete prompt string ready for the image generation API.
    """
    return MASTER_PROMPT.replace("[SUBJECT]", subject_description)


# Art Director system prompt for DeepSeek
ART_DIRECTOR_SYSTEM = (
    "You are an expert Art Director for children's educational content. "
    "You will receive an article title and a section context. "
    "Your ONLY job is to return a SHORT subject/activity description (1 sentence, max 20 words) "
    "that describes what the children are doing in the scene. "
    "This description will be inserted into a master prompt template. "
    "Do NOT return a full prompt. Do NOT include style, lighting, or quality instructions. "
    "Do NOT include 'no text' or negative prompts. "
    "ONLY describe the children's activity/pose/interaction relevant to the educational topic. "
    "Examples: "
    "'eagerly tracing dotted letters on colorful worksheets with crayons' "
    "'building a tall tower with wooden alphabet blocks while laughing' "
    "'carefully comparing two nearly identical photographs side by side'"
)

ART_DIRECTOR_USER_TEMPLATE = (
    "Article: {title}\n"
    "Section: {section}\n"
    "Image role: {role}\n\n"
    "Describe ONLY the children's activity in 1 sentence (max 20 words):"
)
