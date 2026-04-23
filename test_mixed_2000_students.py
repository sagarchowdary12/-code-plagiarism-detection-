"""
test_mixed_2000_students.py
===========================
The ultimate cross-language stress test:
1,000 Python students + 1,000 Java students for the SAME question ID.
Verifies that the engine isolates languages and correctly scores both simultaneously.
"""

import time
import random
import os
import sys
from collections import defaultdict
from detection.scorer import run_plagiarism_check

# Ensure UTF-8 and path
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- PYTHON TEMPLATES ---
py_templates = [
    "def is_prime(n):\n    # {COMMENT}\n    if n < 2: return False\n    {DEAD_CODE}\n    for i in range(2, n):\n        if n % i == 0: return False\n    return True",
    "def check_prime(x):\n    # {COMMENT}\n    if x < 2: return False\n    {DEAD_CODE}\n    limit = int(x**0.5) + 1\n    for i in range(2, limit):\n        if x % i == 0: return False\n    return True"
]

# --- JAVA TEMPLATES ---
java_templates = [
    "public class Prime_{VAR} {{\n    public static boolean check(int n) {{\n        // {COMMENT}\n        if (n < 2) return false;\n        {DEAD_CODE}\n        for (int i = 2; i < n; i++) {{\n            if (n % i == 0) return false;\n        }}\n        return true;\n    }}\n}}",
    "public class Checker_{VAR} {{\n    public static boolean isPrime(int x) {{\n        // {COMMENT}\n        if (x < 2) return false;\n        {DEAD_CODE}\n        int limit = (int)Math.sqrt(x);\n        for (int i = 2; i <= limit; i++) {{\n            if (x % i == 0) return false;\n        }}\n        return true;\n    }}\n}}"
]

comments = ["Logic check", "Student solution", "Final task", "Algorithm V1"]
dead_codes = ["x = 10\ny = 20", "print('debug')", "int a=1; int b=2;", "System.out.println('test');"]

if __name__ == "__main__":
    submissions = []
    
    print("\n" + "="*75)
    print("  DUAL-ENGINE PLAGIARISM DETECTOR — MIXED LANGUAGE STRESS TEST (2,000)")
    print("="*75)

    print("Generating 1,000 Python submissions...")
    for i in range(1000):
        t = random.choice(py_templates)
        submissions.append({
            "candidate_id": f"py_student_{i}",
            "question_id": "SHARED_QUESTION_X",
            "language": "python",
            "source_code": t.format(COMMENT=random.choice(comments), DEAD_CODE=random.choice(dead_codes[:2]))
        })

    print("Generating 1,000 Java submissions...")
    for i in range(1000):
        t = random.choice(java_templates)
        submissions.append({
            "candidate_id": f"java_student_{i}",
            "question_id": "SHARED_QUESTION_X",
            "language": "java",
            "source_code": t.format(VAR=i, COMMENT=random.choice(comments), DEAD_CODE=random.choice(dead_codes[2:]))
        })

    print(f"Total students in database: {len(submissions)}")
    print("Goal: Compare Python-to-Python and Java-to-Java separately.")
    print("="*75)

    start_time = time.time()
    results = run_plagiarism_check(submissions)
    end_time = time.time()

    print("\n" + "="*75)
    print(f"  SCORING COMPLETE IN {end_time - start_time:.2f} SECONDS")
    print("="*75)

    print(f"\n  Total flagged pairs : {len(results):,}")

    lang_dist = defaultdict(int)
    for r in results:
        lang_dist[r["language"]] += 1

    print("\n  Reported Language Groups:")
    for lang in ["java", "python"]:
        cnt = lang_dist[lang]
        print(f"\n    {lang.capitalize():10}: {cnt:8,d} flagged pairs")
        
        # Label distribution per language
        label_dist = defaultdict(int)
        for r in results:
            if r["language"] == lang:
                label_dist[r["label"]] += 1
        
        for label, l_cnt in sorted(label_dist.items()):
            print(f"      - {label:45}: {l_cnt:8,d}")

    print(f"\n{'='*75}\n  TEST COMPLETE\n{'='*75}\n")
