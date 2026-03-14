"""
Instagram file auto-cleanup utility.

USAGE:
  # Mark a file as successfully posted:
  python scripts/instagram_cleanup.py mark <filename>

  # Check and delete files posted more than 48h ago:
  python scripts/instagram_cleanup.py cleanup

  # Show current tracking status:
  python scripts/instagram_cleanup.py status

Files are tracked in instagram/posted_log.json.
Both the image (.jpg) and caption (.txt) are deleted together.
Instagram requires JPG — do NOT convert to WebP.
"""
import os, sys, json, time
from datetime import datetime, timezone

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTA_DIR  = os.path.join(BASE_DIR, "instagram")
LOG_FILE   = os.path.join(INSTA_DIR, "posted_log.json")
KEEP_HOURS = 48  # delete after this many hours


def load_log() -> dict:
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_log(log: dict):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)


def mark(filename: str):
    """Mark a file as successfully posted at current UTC time."""
    log = load_log()
    # Store the base name without extension
    stem = os.path.splitext(filename)[0]
    ts   = time.time()
    log[stem] = {
        "posted_at": ts,
        "posted_at_human": datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "delete_after": datetime.fromtimestamp(ts + KEEP_HOURS * 3600, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    }
    save_log(log)
    print(f"  Marked: {stem}")
    print(f"  Will be deleted after: {log[stem]['delete_after']}")


def cleanup():
    """Delete all files whose 48h window has expired."""
    log  = load_log()
    now  = time.time()
    cutoff = KEEP_HOURS * 3600
    deleted = []

    for stem, info in list(log.items()):
        posted_at = info.get("posted_at", 0)
        if now - posted_at >= cutoff:
            for ext in (".jpg", ".jpeg", ".png", ".txt"):
                path = os.path.join(INSTA_DIR, stem + ext)
                if os.path.exists(path):
                    os.remove(path)
                    print(f"  Deleted: {stem + ext}")
            del log[stem]
            deleted.append(stem)

    save_log(log)
    if deleted:
        print(f"\n  Cleaned up {len(deleted)} posted item(s).")
    else:
        print("  Nothing to clean up yet.")


def status():
    """Show status of all tracked posts."""
    log = load_log()
    if not log:
        print("  No tracked posts.")
        return

    now = time.time()
    print(f"\n  {'File':<60} {'Posted':<20} {'Delete After':<20} Status")
    print("  " + "-" * 110)
    for stem, info in sorted(log.items(), key=lambda x: x[1].get("posted_at", 0)):
        posted_at = info.get("posted_at", 0)
        hours_ago = (now - posted_at) / 3600
        remaining = max(0, KEEP_HOURS - hours_ago)
        status_str = f"DELETE in {remaining:.1f}h" if remaining > 0 else "READY TO DELETE"
        print(f"  {stem[:58]:<60} {info.get('posted_at_human','?'):<20} {info.get('delete_after','?'):<20} {status_str}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "mark" and len(sys.argv) > 2:
        mark(sys.argv[2])
    elif cmd == "cleanup":
        cleanup()
    elif cmd == "status":
        status()
    else:
        print(__doc__)
