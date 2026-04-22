"""
test_1000_students.py
=====================
Massive stress test: 1,000 students for a single question (Prime Number Check) in Python.
Generates 4 distinct algorithmic approaches (different ASTs) and mixes them up.
This tests if the system can correctly identify plagiarized variations WITHIN the same approach
while NOT flagging students who used a different logical approach.
"""

from collections import defaultdict
from detection.scorer import run_plagiarism_check
import sys
import os
import random
import time
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ── 4 DISTINCT ALGORITHMIC TEMPLATES (Completely different ASTs) ──

# Template 1: Basic loop up to N (Very slow, basic logic)
algo_1 = """
def is_prime_{VAR}(n):
    # {COMMENT}
    if n < 2: return False
    {DEAD_CODE}
    for i in range(2, n):
        if n % i == 0: return False
    return True
"""

# Template 2: Math library Square Root logic
algo_2 = """
import math
def is_prime_{VAR}(num):
    # {COMMENT}
    if num < 2: return False
    {DEAD_CODE}
    limit = int(math.sqrt(num)) + 1
    for i in range(2, limit):
        if num % i == 0: 
            return False
    return True
"""

# Template 3: Optimized While-Loop (Steps by 2)
algo_3 = """
def check_prime_{VAR}(x):
    # {COMMENT}
    if x < 2: return False
    if x == 2: return True
    if x % 2 == 0: return False
    {DEAD_CODE}
    i = 3
    while i * i <= x:
        if x % i == 0: return False
        i += 2
    return True
"""

# Template 4: Factor counting (Weird logic, completely different structure)
algo_4 = """
def prime_test_{VAR}(val):
    # {COMMENT}
    if val < 2: return False
    factors = []
    {DEAD_CODE}
    for i in range(1, val + 1):
        if val % i == 0:
            factors.append(i)
    return len(factors) == 2
"""

templates = [algo_1, algo_2, algo_3, algo_4]

comments = [
    "Check if prime", "Prime logic here", "Return true if prime",
    "Math function", "Assignment 2", "Student answer",
    "Do not modify", "Loop starts here", "Initialize"
]

dead_codes = [
    "x = 10\n    y = 20",
    "print('Checking')",
    "pass",
    "a, b = 0, 1",
    "status = True",
    "temp_arr = []",
    ""
]

if __name__ == "__main__":
    submissions = []
    random.seed(42)  # For reproducible results

    print("\n" + "="*70)
    print("  DUAL-ENGINE PLAGIARISM DETECTOR — 1,000 STUDENT STRESS TEST")
    print("="*70)

    print("Generating 1,000 students using 4 completely distinct logic algorithms...")
    for i in range(1, 1001):
        t = random.choice(templates)
        c = random.choice(comments)
        dc = random.choice(dead_codes)

        code = t.format(VAR=i, COMMENT=c, DEAD_CODE=dc)
        submissions.append({
            "candidate_id": f"s_{i:04d}",
            "question_id": "Q_PRIME",
            "language": "python",
            "source_code": code
        })

    total_pairs = (1000 * 999) // 2
    print(f"Total students      : {len(submissions)}")
    print(f"Language            : Python")
    print(f"Unique approaches   : 4 (Meaning cross-approach pairs should be Likely Original!)")
    print(f"Comparisons to run  : {total_pairs:,} pairs")
    print("="*70)

    print("Starting dual-engine scoring... (this may take a couple of minutes...)")
    start_time = time.time()

    # RUN THE ENGINE!
    results = run_plagiarism_check(submissions)

    end_time = time.time()
    print("\n" + "="*70)
    print(f"  SCORING COMPLETE IN {end_time - start_time:.2f} SECONDS")
    print("="*70)

    print(f"\n  Total flagged pairs : {len(results):,}")

    # Group by label to see the distribution
    lc = defaultdict(int)
    for r in results:
        lc[r["label"]] += 1

    print("\n  Label Distribution:")
    for label, cnt in sorted(lc.items()):
        print(f"    {cnt:8,d}x  {label}")

    print(f"\n{'='*70}\n  TEST COMPLETE\n{'='*70}\n")
