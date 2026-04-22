from test_1000_students import algo_1, algo_2, algo_3, algo_4
from detection.ast_comparator import ast_similarity_percent, get_structural_tokens
from detection.tokenizer import token_similarity_percent

code_1 = algo_1.format(VAR="1", COMMENT="test", DEAD_CODE="print('A')")
code_1_diff_dead = algo_1.format(VAR="2", COMMENT="test2", DEAD_CODE="print('B')\n    print('C')")
code_2 = algo_2.format(VAR="1", COMMENT="test", DEAD_CODE="pass")

print("--- Same Approach (Different Dead Code) ---")
print("AST:", ast_similarity_percent(code_1, code_1_diff_dead))
print("Token:", token_similarity_percent(code_1, code_1_diff_dead))

print("\n--- Cross Approach (Algo 1 vs Algo 2) ---")
print("AST:", ast_similarity_percent(code_1, code_2))
print("Token:", token_similarity_percent(code_1, code_2))
