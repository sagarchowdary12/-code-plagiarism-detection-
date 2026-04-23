"""
test_1000_students_java.py
==========================
Massive stress test: 1,000 students for a single question (Prime Number Check) in Java.
Generates 4 distinct algorithmic approaches (different ASTs) and mixes them up.
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

# ── 4 DISTINCT JAVA ALGORITHMIC TEMPLATES ──

# Template 1: Basic loop up to N
algo_1 = """
public class PrimeCheck_{VAR} {{
    public static boolean isPrime(int n) {{
        // {COMMENT}
        if (n < 2) return false;
        {DEAD_CODE}
        for (int i = 2; i < n; i++) {{
            if (n % i == 0) return false;
        }}
        return true;
    }}
}}
"""

# Template 2: Using Math.sqrt
algo_2 = """
public class Checker_{VAR} {{
    public static boolean check(int num) {{
        // {COMMENT}
        if (num < 2) return false;
        {DEAD_CODE}
        int limit = (int) Math.sqrt(num);
        for (int i = 2; i <= limit; i++) {{
            if (num % i == 0) return false;
        }}
        return true;
    }}
}}
"""

# Template 3: Optimized While-Loop
algo_3 = """
public class PrimeTest_{VAR} {{
    public static boolean test(int x) {{
        // {COMMENT}
        if (x < 2) return false;
        if (x == 2) return true;
        if (x % 2 == 0) return false;
        {DEAD_CODE}
        int i = 3;
        while (i * i <= x) {{
            if (x % i == 0) return false;
            i += 2;
        }}
        return true;
    }}
}}
"""

# Template 4: Factor counting
algo_4 = """
public class Solution_{VAR} {{
    public static boolean isPrime(int val) {{
        // {COMMENT}
        if (val < 2) return false;
        int count = 0;
        {DEAD_CODE}
        for (int i = 1; i <= val; i++) {{
            if (val % i == 0) {{
                count++;
            }}
        }}
        return count == 2;
    }}
}}
"""

templates = [algo_1, algo_2, algo_3, algo_4]

comments = [
    "Check if prime", "Java solution", "Prime check",
    "Assignment task", "Return true for prime", "Logic here"
]

dead_codes = [
    "int a = 10;\n        int b = 20;",
    "System.out.println(\"Checking\");",
    "// dummy",
    "int[] temp = new int[0];",
    "boolean flag = true;",
    ""
]

if __name__ == "__main__":
    submissions = []
    random.seed(42)  # For reproducible results

    print("\n" + "="*70)
    print("  DUAL-ENGINE PLAGIARISM DETECTOR — 1,000 STUDENT STRESS TEST (JAVA)")
    print("="*70)

    print("Generating 1,000 Java students using 4 distinct algorithms...")
    for i in range(1, 1001):
        t = random.choice(templates)
        c = random.choice(comments)
        dc = random.choice(dead_codes)

        code = t.format(VAR=i, COMMENT=c, DEAD_CODE=dc)
        submissions.append({
            "candidate_id": f"s_{i:04d}",
            "question_id": "Q_PRIME_JAVA",
            "language": "java",
            "source_code": code
        })

    total_pairs = (1000 * 999) // 2
    print(f"Total students      : {len(submissions)}")
    print(f"Language            : Java")
    print(f"Unique approaches   : 4")
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

    lc = defaultdict(int)
    for r in results:
        lc[r["label"]] += 1

    print("\n  Label Distribution:")
    for label, cnt in sorted(lc.items()):
        print(f"    {cnt:8,d}x  {label}")

    print(f"\n{'='*70}\n  TEST COMPLETE\n{'='*70}\n")
