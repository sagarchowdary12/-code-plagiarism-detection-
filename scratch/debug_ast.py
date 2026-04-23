import ast
from detection.ast_comparator import (
    get_structural_tokens,
    winnowing_ast,
    ast_similarity_percent,
)

code1 = """
def process_list(data):
    results = []
    for x in data:
        if x % 2 == 0:
            y = x * 2
            results.append(y)
        else:
            y = x + 1
            results.append(y)
    return results
"""

code2 = """
def handle_array(items):
    print("Starting...")
    out = []
    for val in items:
        print("Looping")
        if val % 2 == 0:
            res = val * 2
            out.append(res)
        else:
            res = val + 1
            out.append(res)
    print("Done")
    return out
"""

print("--- DEBUGGING AST ---")
nodes1 = get_structural_tokens(code1, "python")
nodes2 = get_structural_tokens(code2, "python")

print(f"Nodes 1 (len {len(nodes1)}): {nodes1}")
print(f"Nodes 2 (len {len(nodes2)}): {nodes2}")

f1 = winnowing_ast(nodes1)
f2 = winnowing_ast(nodes2)

print(f"Fingerprints 1: {f1}")
print(f"Fingerprints 2: {f2}")

score = ast_similarity_percent(code1, code2, "python")
print(f"Final Score: {score}")
