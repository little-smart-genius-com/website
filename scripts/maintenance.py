#!/usr/bin/env python3
"""
MAINTENANCE.PY — Little Smart Genius Blog Maintenance Tool
===========================================================
Scans posts/archive/ for stale articles, optionally refreshes them via
DeepSeek, and cleans old archived JSON files.

Usage:
    python maintenance.py --scan                # Show stale articles (> 6 months)
    python maintenance.py --scan --days 90      # Show articles older than 90 days
    python maintenance.py --clean-archive 30    # Delete archived JSON > 30 days old
    python maintenance.py --clean-archive 30 --dry-run   # Preview deletions
    python maintenance.py --refresh --limit 3   # Refresh top-3 oldest articles via API
    python maintenance.py --refresh --dry-run   # Preview refresh candidates
    python maintenance.py --stats               # Show archive/article statistics
"""

import os
import sys
import json
import glob
import argparse
from datetime import datetime, timedelta

# ─── CONFIG ────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARCHIVE_DIR = os.path.join(PROJECT_ROOT, "posts", "archive")
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
DEFAULT_STALE_DAYS = 180  # 6 months


def get_archive_files():
    """List all JSON files in the archive directory."""
    if not os.path.exists(ARCHIVE_DIR):
        return []
    return sorted(glob.glob(os.path.join(ARCHIVE_DIR, "*.json")))


def get_article_files():
    """List all HTML files in the articles directory."""
    if not os.path.exists(ARTICLES_DIR):
        return []
    return sorted(glob.glob(os.path.join(ARTICLES_DIR, "*.html")))


def parse_iso_date(date_str):
    """Parse an ISO date string, tolerant of different formats."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00").split("+")[0])
    except (ValueError, AttributeError):
        return None


def load_json_safe(filepath):
    """Load JSON with error handling."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"  WARNING: Could not parse {filepath}: {e}")
        return None


# ═══════════════════════════════════════════════════════
# SCAN — find stale articles
# ═══════════════════════════════════════════════════════

def cmd_scan(args):
    """Scan archive for stale articles."""
    cutoff_days = args.days or DEFAULT_STALE_DAYS
    cutoff_date = datetime.now() - timedelta(days=cutoff_days)
    archive_files = get_archive_files()

    if not archive_files:
        print("No archived JSON files found.")
        return

    print(f"\nScanning {len(archive_files)} archived articles (stale = older than {cutoff_days} days)...\n")

    stale = []
    for fp in archive_files:
        data = load_json_safe(fp)
        if not data:
            continue

        iso_date = data.get("iso_date", "")
        article_date = parse_iso_date(iso_date)
        if not article_date:
            # Use file modification time as fallback
            article_date = datetime.fromtimestamp(os.path.getmtime(fp))

        age_days = (datetime.now() - article_date).days

        if article_date < cutoff_date:
            stale.append({
                "file": os.path.basename(fp),
                "title": data.get("title", "Untitled"),
                "date": iso_date or "unknown",
                "age_days": age_days,
            })

    if stale:
        stale.sort(key=lambda x: x["age_days"], reverse=True)
        print(f"Found {len(stale)} stale articles:\n")
        for i, s in enumerate(stale, 1):
            print(f"  {i:3d}. [{s['age_days']:4d}d] {s['title'][:60]}")
            print(f"       File: {s['file']}  |  Date: {s['date']}")
    else:
        print(f"No stale articles found (all within {cutoff_days} days).")


# ═══════════════════════════════════════════════════════
# CLEAN-ARCHIVE — delete old archived JSONs
# ═══════════════════════════════════════════════════════

def cmd_clean_archive(args):
    """Delete archived JSON files older than N days."""
    max_age_days = args.clean_archive
    dry_run = args.dry_run
    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    archive_files = get_archive_files()

    if not archive_files:
        print("No archived JSON files found.")
        return

    prefix = "[DRY-RUN] " if dry_run else ""
    print(f"\n{prefix}Cleaning archive: deleting JSON files older than {max_age_days} days...\n")

    deleted = 0
    total_bytes = 0

    for fp in archive_files:
        mod_time = datetime.fromtimestamp(os.path.getmtime(fp))
        age_days = (datetime.now() - mod_time).days

        if mod_time < cutoff_date:
            size = os.path.getsize(fp)
            print(f"  {prefix}DELETE  {os.path.basename(fp)}  ({age_days}d old, {size:,} bytes)")
            if not dry_run:
                os.remove(fp)
            deleted += 1
            total_bytes += size

    print(f"\n{prefix}{deleted} files {'would be ' if dry_run else ''}deleted ({total_bytes:,} bytes freed)")


# ═══════════════════════════════════════════════════════
# REFRESH — flag/prepare articles for re-generation
# ═══════════════════════════════════════════════════════

def cmd_refresh(args):
    """Identify oldest articles for content refresh.
    
    This creates a refresh_queue.json that auto_blog_v4.py could use
    to prioritize re-generation of stale content.
    """
    limit = args.limit or 5
    dry_run = args.dry_run
    archive_files = get_archive_files()

    if not archive_files:
        print("No archived JSON files to refresh.")
        return

    # Build age-sorted list
    candidates = []
    for fp in archive_files:
        data = load_json_safe(fp)
        if not data:
            continue
        iso_date = data.get("iso_date", "")
        article_date = parse_iso_date(iso_date)
        if not article_date:
            article_date = datetime.fromtimestamp(os.path.getmtime(fp))

        candidates.append({
            "file": os.path.basename(fp),
            "path": fp,
            "title": data.get("title", "Untitled"),
            "date": iso_date,
            "age_days": (datetime.now() - article_date).days,
            "category": data.get("category", ""),
            "slug": data.get("slug", os.path.splitext(os.path.basename(fp))[0]),
        })

    candidates.sort(key=lambda x: x["age_days"], reverse=True)
    selected = candidates[:limit]

    prefix = "[DRY-RUN] " if dry_run else ""
    print(f"\n{prefix}Top {len(selected)} candidates for content refresh:\n")

    for i, c in enumerate(selected, 1):
        print(f"  {i}. [{c['age_days']}d] {c['title'][:55]}")
        print(f"     Slug: {c['slug']}  |  Category: {c['category']}")

    if not dry_run:
        queue_file = "refresh_queue.json"
        queue = {
            "generated_at": datetime.now().isoformat(),
            "total": len(selected),
            "articles": [
                {"slug": c["slug"], "title": c["title"], "category": c["category"], "age_days": c["age_days"]}
                for c in selected
            ],
        }
        with open(queue_file, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)
        print(f"\n  Refresh queue saved: {queue_file}")
        print(f"  Use auto_blog_v4.py to regenerate these articles.")


# ═══════════════════════════════════════════════════════
# STATS — overview of the blog system
# ═══════════════════════════════════════════════════════

def cmd_stats(args):
    """Show archive and article statistics."""
    archive_files = get_archive_files()
    article_files = get_article_files()
    report_files = sorted(glob.glob(os.path.join(REPORTS_DIR, "*.json"))) if os.path.exists(REPORTS_DIR) else []

    # Search index
    search_index_size = 0
    search_index_count = 0
    if os.path.exists(os.path.join(PROJECT_ROOT, "search_index.json")):
        search_index_size = os.path.getsize(os.path.join(PROJECT_ROOT, "search_index.json"))
        try:
            data = json.load(open(os.path.join(PROJECT_ROOT, "search_index.json"), "r", encoding="utf-8"))
            search_index_count = data.get("total_articles", 0)
        except Exception:
            pass

    # Archive stats
    archive_size = sum(os.path.getsize(f) for f in archive_files)
    oldest_archive = None
    if archive_files:
        oldest_archive = min(datetime.fromtimestamp(os.path.getmtime(f)) for f in archive_files)

    print("\n" + "=" * 60)
    print("  LITTLE SMART GENIUS -- BLOG STATISTICS")
    print("=" * 60)
    print(f"\n  Articles (HTML):       {len(article_files):>6}")
    print(f"  Archived JSONs:        {len(archive_files):>6} ({archive_size:,} bytes)")
    print(f"  Conversion reports:    {len(report_files):>6}")
    print(f"  search_index.json:     {search_index_count:>6} articles ({search_index_size:,} bytes)")

    if oldest_archive:
        age = (datetime.now() - oldest_archive).days
        print(f"\n  Oldest archive:        {age} days ago ({oldest_archive.strftime('%Y-%m-%d')})")

    # Categories breakdown
    if os.path.exists(os.path.join(PROJECT_ROOT, "search_index.json")):
        try:
            data = json.load(open(os.path.join(PROJECT_ROOT, "search_index.json"), "r", encoding="utf-8"))
            cats = {}
            for a in data.get("articles", []):
                cat = a.get("category", "Uncategorized")
                cats[cat] = cats.get(cat, 0) + 1
            if cats:
                print(f"\n  Categories:")
                for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
                    print(f"    {cat:.<30s} {count}")
        except Exception:
            pass

    # Disk usage
    print(f"\n  Disk usage:")
    for dirname in [ARTICLES_DIR, ARCHIVE_DIR, REPORTS_DIR, os.path.join(PROJECT_ROOT, "posts"), os.path.join(PROJECT_ROOT, "backups")]:
        if os.path.exists(dirname):
            total = sum(
                os.path.getsize(os.path.join(dp, f))
                for dp, _, fns in os.walk(dirname) for f in fns
            )
            fcount = sum(len(fns) for _, _, fns in os.walk(dirname))
            print(f"    {dirname + '/':.<30s} {fcount:>4} files, {total:>10,} bytes")

    print()


# ═══════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Little Smart Genius — Blog Maintenance Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python maintenance.py --stats
  python maintenance.py --scan
  python maintenance.py --scan --days 90
  python maintenance.py --clean-archive 30 --dry-run
  python maintenance.py --clean-archive 30
  python maintenance.py --refresh --limit 3 --dry-run
  python maintenance.py --refresh --limit 3
        """,
    )
    parser.add_argument("--scan", action="store_true", help="Scan for stale articles")
    parser.add_argument("--days", type=int, help=f"Stale threshold in days (default: {DEFAULT_STALE_DAYS})")
    parser.add_argument("--clean-archive", type=int, metavar="DAYS",
                        help="Delete archived JSON files older than N days")
    parser.add_argument("--refresh", action="store_true", help="Identify articles for content refresh")
    parser.add_argument("--limit", type=int, help="Max articles to refresh (default: 5)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying files")
    parser.add_argument("--stats", action="store_true", help="Show blog system statistics")

    args = parser.parse_args()

    if not any([args.scan, args.clean_archive, args.refresh, args.stats]):
        parser.print_help()
        return

    if args.stats:
        cmd_stats(args)
    if args.scan:
        cmd_scan(args)
    if args.clean_archive:
        cmd_clean_archive(args)
    if args.refresh:
        cmd_refresh(args)


if __name__ == "__main__":
    main()
