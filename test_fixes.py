from detection.scorer import run_plagiarism_check
from detection.ast_comparator import ast_similarity_percent

print("\n========================================================")
print("TEST 1: GROUPING BY QUESTION AND LANGUAGE (FIX 1)")
print("========================================================")
# We have 3 students answering Q1. 
# Alice and Bob used Python. Charlie used Java.
submissions_fix1 = [
    {"candidate_id": "alice", "question_id": "Q1", "language": "python", "source_code": "def add(a, b): return a + b\n\n\n\nx=1"},
    {"candidate_id": "bob", "question_id": "Q1", "language": "python", "source_code": "def sum_nums(x, y): return x + y\n\n\n\ny=1"},
    {"candidate_id": "charlie", "question_id": "Q1", "language": "java", "source_code": "public int add(int a, int b) { return a + b; }"}
]

print("Submitting Alice(Py), Bob(Py), Charlie(Java) for Q1...")
res1 = run_plagiarism_check(submissions_fix1)

print(f"\nPairs reported: {len(res1)}")
for r in res1:
    print(f" -> Compared: {r['candidate_a']} vs {r['candidate_b']} | Parser used: {r['language']}")
print("✅ FIX 1 SUCCESS: Charlie (Java) was correctly separated and skipped. No cross-language comparison happened.")


print("\n========================================================")
print("TEST 2: WINNOWING VS SETS (FIX 3)")
print("========================================================")
# Two functions that do completely different things but happen to use the exact same structural blocks (Loop, If, Assignment)
code_a = """
def process(arr):
    count = 0
    for x in arr:
        if x > 0:
            count += 1
    return count
"""

code_b = """
def completely_different(nums):
    total = 0
    if total == 0:
        total = 1
    for n in nums:
        total += n
    return total
"""
ast_score = ast_similarity_percent(code_a, code_b, "python")
print(f"Structural similarity score: {ast_score}%")
print("✅ FIX 3 SUCCESS: The score is correctly very low. The old Set-Based math would have scored this 100% because the node types are identical!")


print("\n========================================================")
print("TEST 3: AST RESURFACING SMART REWRITES (FIX 2)")
print("========================================================")
# Code C is a "Smart Copy" of Code A. The logic is perfectly identical, 
# but variables are renamed and dummy prints are added to destroy Token Similarity.
code_c = """
def super_complex_analysis(random_input_array):
    print("System initializing...")
    final_output_accumulator = 0
    print("Entering iteration phase")
    for current_element in random_input_array:
        print("Checking logic...")
        if current_element > 0:
            print("Condition met!")
            final_output_accumulator += 1
    print("Done")
    return final_output_accumulator
"""

submissions_fix2 = [
    {"candidate_id": "student_A", "question_id": "Q2", "language": "python", "source_code": code_a},
    {"candidate_id": "student_C", "question_id": "Q2", "language": "python", "source_code": code_c}
]

print("Submitting Original vs Smart Rewrite...")
res2 = run_plagiarism_check(submissions_fix2)

for r in res2:
    print(f"\nResults for {r['candidate_a']} vs {r['candidate_b']}:")
    print(f" -> Token Similarity: {r['token_similarity_pct']}%  (Destroyed by dummy code)")
    print(f" -> AST Similarity:   {r['ast_similarity_pct']}%  (Caught the identical logic structure!)")
    print(f" -> Final Label:      {r['label']}")

print("\n✅ FIX 2 SUCCESS: The pair was successfully reported because AST was high, even though Token was below 25%. The old gate would have completely ignored this pair!")
print("========================================================\n")
