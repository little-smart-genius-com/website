"""
image_integrity_scan.py
Scans all 29 articles and verifies that every referenced image:
  1. Exists locally on disk
  2. Is accessible online via HTTP (littlesmartgenius.com)
Reports any missing or broken images.
"""
import os, re, glob, sys, time
import urllib.request
import urllib.error

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
BASE_URL = "https://littlesmartgenius.com"

def extract_images_from_html(html_path):
    """Extract all image src and srcset references from an HTML file."""
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    images = set()

    # src="..." attributes
    for match in re.finditer(r'src="([^"]*\.(?:webp|png|jpg|jpeg|gif|svg))"', html, re.IGNORECASE):
        images.add(match.group(1))

    # srcset="..." attributes (extract individual URLs)
    for match in re.finditer(r'srcset="([^"]+)"', html):
        srcset = match.group(1)
        for part in srcset.split(","):
            url = part.strip().split()[0]
            if re.search(r'\.(?:webp|png|jpg|jpeg|gif|svg)$', url, re.IGNORECASE):
                images.add(url)

    # background-image: url(...)
    for match in re.finditer(r"url\(['\"]?([^'\")\s]+\.(?:webp|png|jpg|jpeg|gif|svg))['\"]?\)", html, re.IGNORECASE):
        images.add(match.group(1))

    return sorted(images)


def check_local(image_ref, article_dir):
    """Check if the image exists locally on disk."""
    if image_ref.startswith("http"):
        return None  # External URL, skip local check

    # Resolve relative path from the article's directory
    resolved = os.path.normpath(os.path.join(article_dir, image_ref))
    exists = os.path.isfile(resolved)
    size = os.path.getsize(resolved) if exists else 0
    return {"exists": exists, "path": resolved, "size": size}


def check_online(image_ref, article_slug):
    """Check if the image is accessible online via HTTP HEAD."""
    if image_ref.startswith("http"):
        url = image_ref
    elif image_ref.startswith("../"):
        url = f"{BASE_URL}/{image_ref[3:]}"
    elif image_ref.startswith("/"):
        url = f"{BASE_URL}{image_ref}"
    else:
        url = f"{BASE_URL}/articles/{image_ref}"

    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "Mozilla/5.0")
        resp = urllib.request.urlopen(req, timeout=10)
        return {"accessible": True, "status": resp.status, "url": url}
    except urllib.error.HTTPError as e:
        return {"accessible": False, "status": e.code, "url": url}
    except Exception as e:
        return {"accessible": False, "status": str(e)[:50], "url": url}


def main():
    articles = sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html")))

    print("=" * 70)
    print("  FULL IMAGE INTEGRITY SCAN — Local + Online")
    print(f"  {len(articles)} articles to scan")
    print("=" * 70)

    total_images = 0
    total_local_ok = 0
    total_local_fail = 0
    total_online_ok = 0
    total_online_fail = 0
    all_failures = []

    for i, article_path in enumerate(articles, 1):
        slug = os.path.basename(article_path).replace(".html", "")
        article_dir = os.path.dirname(article_path)
        images = extract_images_from_html(article_path)

        print(f"\n[{i}/{len(articles)}] {slug[:55]}")
        print(f"  Images referenced: {len(images)}")

        article_ok = True
        for img_ref in images:
            # Skip data: URIs and SVG inline
            if img_ref.startswith("data:") or img_ref.startswith("blob:"):
                continue

            total_images += 1
            basename = os.path.basename(img_ref)

            # LOCAL CHECK
            local = check_local(img_ref, article_dir)
            if local is not None:
                if local["exists"]:
                    total_local_ok += 1
                    local_status = f"OK ({local['size']//1024}KB)"
                else:
                    total_local_fail += 1
                    local_status = "MISSING"
                    article_ok = False
                    all_failures.append({"article": slug, "image": img_ref, "issue": "LOCAL MISSING"})
            else:
                local_status = "EXTERNAL"

            # ONLINE CHECK
            online = check_online(img_ref, slug)
            if online["accessible"]:
                total_online_ok += 1
                online_status = f"OK ({online['status']})"
            else:
                total_online_fail += 1
                online_status = f"FAIL ({online['status']})"
                article_ok = False
                all_failures.append({"article": slug, "image": img_ref, "issue": f"ONLINE {online['status']}", "url": online["url"]})

            # Only print failures or summary
            if not (local is None or local["exists"]) or not online["accessible"]:
                print(f"    FAIL: {basename[:50]}")
                print(f"           Local: {local_status}")
                print(f"           Online: {online_status}")

        if article_ok:
            print(f"  => ALL {len(images)} images OK")

        # Small delay between articles to not hammer the server
        if i < len(articles):
            time.sleep(0.5)

    # SUMMARY
    print(f"\n{'=' * 70}")
    print("  SCAN COMPLETE — SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Total images checked:  {total_images}")
    print(f"  Local OK:              {total_local_ok}")
    print(f"  Local MISSING:         {total_local_fail}")
    print(f"  Online OK:             {total_online_ok}")
    print(f"  Online FAIL:           {total_online_fail}")

    if all_failures:
        print(f"\n{'=' * 70}")
        print(f"  FAILURES ({len(all_failures)}):")
        print(f"{'=' * 70}")
        for f in all_failures:
            print(f"  [{f['issue']}] {f['article'][:40]} -> {os.path.basename(f['image'])[:50]}")
            if "url" in f:
                print(f"           URL: {f['url']}")
    else:
        print(f"\n  ALL IMAGES ARE PRESENT — locally and online!")

    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
