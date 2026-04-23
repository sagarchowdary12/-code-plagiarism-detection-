import pytest
import textwrap
from detection.tokenizer import tokenize
from detection.scorer import get_token_count
from detection.ast_comparator import ast_similarity_percent


def test_normalization_catches_renaming():
    """
    Verify that changing variable names results in 100% token similarity.
    """
    code1 = textwrap.dedent("""
        def find_max(numbers):
            my_res = numbers[0]
            return my_res
    """).strip()

    code2 = textwrap.dedent("""
        def get_top(items):
            the_output = items[0]
            return the_output
    """).strip()

    tokens1 = tokenize(code1, "python")
    tokens2 = tokenize(code2, "python")

    assert tokens1 == tokens2
    assert len(tokens1) > 0


def test_comment_stripping():
    """
    Verify that comments are ignored when counting tokens.
    """
    code_with_comments = textwrap.dedent("""
        def add(a, b):
            # This is a very long junk comment to bypass gating
            # Adding more lines of comments here
            return a + b
    """).strip()

    code_pure = "def add(a, b): return a + b"

    count_with_comments = get_token_count(code_with_comments, "python")
    count_pure = get_token_count(code_pure, "python")

    assert count_with_comments == count_pure


def test_ast_structural_similarity_long_code():
    """
    Verify that identical logic structure gets high score even if
    the text changes. We use longer code here to satisfy the
    production sensitivity (k=6, window=4).
    """
    code1 = textwrap.dedent("""
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
    """).strip()

    # Same logic but with extra print noise and different names
    code2 = textwrap.dedent("""
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
    """).strip()

    score = ast_similarity_percent(code1, code2, "python")

    # Structural similarity should be 100% since prints are ignored.
    assert score > 90


def test_language_isolation_baseline():
    """
    Ensure that a Java file compared to Python logic (as text)
    fails gracefully or shows zero logical similarity.
    """
    python_code = "def add(a, b): return a + b"
    java_code = "public int add(int a, int b) { return a + b; }"

    tokens_py = tokenize(python_code, "python")
    tokens_java = tokenize(java_code, "java")

    assert tokens_py != tokens_java
