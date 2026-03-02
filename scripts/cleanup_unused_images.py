"""
cleanup_unused_images.py
Scans all HTML, CSS, JS files for image references,
then identifies and deletes images on disk that are NOT referenced anywhere.
"""
import os, re, glob

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
THUMBS_DIR = os.path.join(IMAGES_DIR, "thumbs")

# File types that can reference images
SCAN_EXTENSIONS = ["*.html", "*.css", "*.js", "*.json", "*.xml", "*.md"]
# Image extensions to check
IMAGE_EXTENSIONS = {".webp", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico"}


def collect_all_image_files():
    """Collect ALL image files on disk (images/ and images/thumbs/)."""
    files = {}
    for root, dirs, filenames in os.walk(IMAGES_DIR):
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext in IMAGE_EXTENSIONS:
                full_path = os.path.join(root, fn)
                rel = os.path.relpath(full_path, PROJECT_ROOT).replace("\\", "/")
                files[fn] = {"path": full_path, "rel": rel, "size": os.path.getsize(full_path)}
    return files


def collect_all_references():
    """Scan all source files for any image filename references."""
    referenced = set()

    for ext_pattern in SCAN_EXTENSIONS:
        for f in glob.glob(os.path.join(PROJECT_ROOT, "**", ext_pattern), recursive=True):
            # Skip node_modules, .git, etc.
            if ".git" in f or "node_modules" in f:
                continue
            try:
                content = open(f, encoding="utf-8", errors="ignore").read()
            except:
                continue

            # Find all image filenames mentioned anywhere
            # Match patterns like: src="...filename.webp", url(...filename.png), etc.
            for match in re.finditer(r'[\w\-]+\.(?:webp|png|jpg|jpeg|gif|svg|ico)', content, re.IGNORECASE):
                referenced.add(match.group(0))

    return referenced


def main():
    print("=" * 65)
    print("  UNUSED IMAGE SCANNER & CLEANER")
    print("=" * 65)

    # 1. Collect all image files on disk
    all_images = collect_all_image_files()
    print(f"\n  Total image files on disk: {len(all_images)}")

    # 2. Collect all references from source files
    referenced = collect_all_references()
    print(f"  Total unique image filenames referenced: {len(referenced)}")

    # 3. Find unused
    unused = {}
    used = {}
    for fn, info in all_images.items():
        if fn in referenced:
            used[fn] = info
        else:
            unused[fn] = info

    print(f"\n  Used images: {len(used)}")
    print(f"  UNUSED images: {len(unused)}")

    if not unused:
        print("\n  No unused images found! Everything is clean.")
        return

    # 4. Show unused images sorted by size
    total_waste = 0
    sorted_unused = sorted(unused.items(), key=lambda x: x[1]["size"], reverse=True)

    print(f"\n{'=' * 65}")
    print(f"  UNUSED IMAGES TO DELETE ({len(unused)} files):")
    print(f"{'=' * 65}")
    for fn, info in sorted_unused:
        size_kb = info["size"] / 1024
        total_waste += info["size"]
        print(f"  {size_kb:8.1f} KB  {info['rel']}")

    total_waste_mb = total_waste / (1024 * 1024)
    print(f"\n  Total wasted space: {total_waste_mb:.2f} MB")

    # 5. Delete unused files
    print(f"\n{'=' * 65}")
    print(f"  DELETING {len(unused)} unused images...")
    print(f"{'=' * 65}")

    deleted = 0
    for fn, info in sorted_unused:
        try:
            os.remove(info["path"])
            deleted += 1
        except Exception as e:
            print(f"  [ERROR] Could not delete {fn}: {e}")

    print(f"\n  DONE: {deleted}/{len(unused)} files deleted, {total_waste_mb:.2f} MB freed")


if __name__ == "__main__":
    main()
