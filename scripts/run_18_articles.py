"""
Run 18 articles: 6 batches x 3 articles (keyword, product, freebie).
"""
import auto_blog_v4 as ab
import time

TOTAL_BATCHES = 6
all_results = []

for batch in range(TOTAL_BATCHES):
    print("\n" + "=" * 80)
    print(f"  MEGA BATCH {batch+1}/{TOTAL_BATCHES}")
    print("=" * 80)

    results = ab.run_daily_batch()
    if results:
        all_results.extend(results)

    if batch < TOTAL_BATCHES - 1:
        print(f"\n[MEGA] Pause 15s before next batch...")
        time.sleep(15)

print("\n" + "=" * 80)
print("  ALL 18 ARTICLES DONE")
print("=" * 80)
print(f"Total generated: {len(all_results)}/18")
for r in all_results:
    slot = r["slot"].upper()
    title = r["title"][:55]
    wc = r["word_count"]
    print(f"  [{slot:8s}] {title:55s} ({wc} words)")
