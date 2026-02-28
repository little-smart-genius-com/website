#!/usr/bin/env python3
"""
clean_og_images.py — Auto-Cleanup of old OpenGraph images
=========================================================
Deletes OG images (.jpg) that are older than 48 hours to save space.

Usage:
  python scripts/clean_og_images.py
"""

import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OG_DIR = os.path.join(BASE_DIR, "images", "og")
KEEP_HOURS = 48

def clean_og_images():
    if not os.path.exists(OG_DIR):
        print(f"Directory {OG_DIR} does not exist.")
        return

    now = time.time()
    cutoff = now - (KEEP_HOURS * 3600)
    count = 0
    total_size = 0

    for filename in os.listdir(OG_DIR):
        if not filename.endswith(".jpg"):
            continue
            
        path = os.path.join(OG_DIR, filename)
        if not os.path.isfile(path):
            continue
            
        # Get last modification time
        mtime = os.path.getmtime(path)
        
        if mtime < cutoff:
            size = os.path.getsize(path)
            os.remove(path)
            count += 1
            total_size += size
            print(f"  [DELETED] {filename}")

    if count > 0:
        print(f"\nCleanup complete. Deleted {count} OG image(s) older than {KEEP_HOURS}h.")
        print(f"Freed space: {total_size / 1024 / 1024:.2f} MB")
    else:
        print(f"Cleanup complete. No OG images older than {KEEP_HOURS}h found.")

if __name__ == "__main__":
    clean_og_images()
