#!/usr/bin/env python3
"""
A/B Test Dashboard
Analyze which video styles perform best
"""

import json
import os
from collections import defaultdict
from datetime import datetime

AB_TEST_FILE = "ab_test_results.json"

def load_ab_results():
    """Load all A/B test results"""
    if not os.path.exists(AB_TEST_FILE):
        print("No A/B test data yet. Videos haven't been uploaded.")
        return {}
    
    with open(AB_TEST_FILE, "r") as f:
        return json.load(f)

def analyze_results():
    """Analyze A/B test performance"""
    results = load_ab_results()
    
    if not results:
        return
    
    # Group by variant
    variants = defaultdict(list)
    for video_id, data in results.items():
        variant = data.get("variant", "unknown")
        variants[variant].append(data)
    
    print("\n" + "="*60)
    print("📊 A/B TEST ANALYSIS")
    print("="*60)
    
    for variant, videos in variants.items():
        print(f"\n{variant.upper()}:")
        print(f"  Videos uploaded: {len(videos)}")
        print(f"  Latest: {videos[-1]['date']}")
        print(f"  Titles:")
        for v in videos:
            print(f"    - {v['title']}")
            print(f"      {v['url']}")
    
    print("\n" + "="*60)
    print("💡 TIPS:")
    print("  1. Use YouTube Analytics to check watch time")
    print("  2. Check click-through rate (CTR) per variant")
    print("  3. Compare engagement metrics")
    print("  4. Run for at least 20 videos per variant for accuracy")
    print("="*60 + "\n")

if __name__ == "__main__":
    analyze_results()
