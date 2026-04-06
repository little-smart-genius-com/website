import os
import subprocess

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# The 9 most recent articles ONLINE (April 05-06, 2026) - affected by photorealistic style
SLUGS = [
    "why-bilingual-matching-beats-flashcards-and-apps",
    "best-strategy-board-games-that-teach-kids-critical-thinking",
    "how-spot-the-difference-builds-focus-without-screens",
    "kindergarten-summer-critical-thinking-activities",
    "a-kindergarten-day-guide-for-visual-discrimination-exercises",
    "from-frustrated-to-focused-a-math-puzzle-breakthrough",
    "best-word-search-puzzles-for-kids-vocabulary-building",
    "how-multi-sensory-word-searches-build-reading-skills-in-kids",
    "screen-free-observation-skills-games-for-kids",
]

def main():
    total = len(SLUGS)
    print(f"=== Regenerating images for the {total} most recent ONLINE articles ===\n")
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    success = 0
    failed = 0
    
    for i, slug in enumerate(SLUGS, 1):
        print(f"[{i}/{total}] {slug}")
        cmd = ["python", os.path.join("scripts", "fix_images.py"), "--force", "--slug", slug]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
        
        if result.returncode == 0:
            print(f"  -> OK")
            success += 1
        else:
            print(f"  -> FAILED")
            if result.stderr:
                print(f"     {result.stderr[:300]}")
            failed += 1

    print(f"\n=== Done: {success} OK / {failed} failed ===")

if __name__ == "__main__":
    main()
