from itertools import combinations
from collections import defaultdict
from detection.tokenizer import (
    token_similarity_percent,
    clean_code_from_db as clean_code,
    tokenize,
)
from detection.ast_comparator import ast_similarity_percent

# Minimum tokens required to compare two submissions
MIN_TOKEN_LENGTH = 5

# Hybrid Reporting Thresholds:
# Pairs are only dropped if BOTH signals fall below these minimums
MIN_TOKEN_REPORT_PCT = 25.0
MIN_AST_REPORT_PCT = 40.0


def get_token_count(source_code: str, language: str) -> int:
    # Use the actual normalized tokens for gating to avoid whitespace noise
    return len(tokenize(source_code, language))


def group_identical_submissions(submissions: list) -> dict:
    # Groups candidates who submitted the EXACT same code
    groups = defaultdict(list)
    for sub in submissions:
        cleaned = clean_code(sub["source_code"]).strip()
        groups[cleaned].append(sub["candidate_id"])
    return groups


# The Label Engine (The most important logic in the whole app!)
def get_label(token_pct: float, ast_pct: float) -> str:
    # Exactly identical text and logic
    if token_pct == 100 and ast_pct == 100:
        return "Exact match"

    # Token very high — obvious copy with tiny changes
    if token_pct >= 90:
        return "Near-identical text"

    # Token high — clearly copied with some renaming
    if token_pct >= 75:
        return "High token overlap"

    # HUGE: Text is very different (under 75 words match), but the underlying Blueprint is almost perfectly identical (over 95)!
    # This means student rewrote the surface but kept exact same logic. This is deliberate smart plagiarism — worst kind
    if token_pct < 75 and ast_pct >= 95:
        return "Low text overlap, high structural similarity"

    # Suspicious logic overlap (Token is generic, but structural skeleton matches heavily)
    if token_pct >= 50 and ast_pct >= 75:
        return "Moderate similarity — structural and textual"

    # Token moderate (Generic text overlap, logic wasn't strong enough to hit trap above)
    if token_pct >= 50:
        return "Moderate text similarity"

    # Token low but AST moderate — slightly suspicious
    if token_pct >= 25 and ast_pct >= 50:
        return "Slight text similarity"

    return "Likely original"


# The Execution Loop


def compare_all_submissions(submissions: list) -> list:
    results = []

    if not submissions:
        return results

    question_id = submissions[0]["question_id"]
    language = submissions[0]["language"]

    # Compare every pair (but skip comparing a submission to itself)
    for sub_a, sub_b in combinations(submissions, 2):
        # Skip if it's literally the same submission (same candidate_id)
        if sub_a["candidate_id"] == sub_b["candidate_id"]:
            continue

        code_a = sub_a["source_code"]
        code_b = sub_b["source_code"]

        # Skip if either code's normalized tokens are too short
        if get_token_count(code_a, language) < MIN_TOKEN_LENGTH:
            continue
        if get_token_count(code_b, language) < MIN_TOKEN_LENGTH:
            continue

        # Get token similarity percentage
        tok_pct = token_similarity_percent(code_a, code_b, language)

        # Compute AST similarity for all pairs to catch smart rewrites
        # where token similarity is low but structure is identical.
        ast_pct = ast_similarity_percent(code_a, code_b, language)

        # Hybrid decision rule: Either token >= 25% or AST >= 40% independently flags the result.
        # We only drop the pair if BOTH are considered noise.
        if tok_pct < MIN_TOKEN_REPORT_PCT and ast_pct < MIN_AST_REPORT_PCT:
            continue

        # Get human readable label
        label = get_label(tok_pct, ast_pct)

        results.append(
            {
                "candidate_a": sub_a["candidate_id"],
                "candidate_b": sub_b["candidate_id"],
                "question_id": question_id,
                "language": language,
                "token_similarity_pct": tok_pct,
                "ast_similarity_pct": ast_pct,
                "label": label,
            }
        )

    # Sort by token similarity — highest first so worst cases appear at top
    results.sort(key=lambda x: x["token_similarity_pct"], reverse=True)

    return results


def run_plagiarism_check(all_submissions: list) -> list:
    # Group by (question_id, language) to prevent cross-language submissions
    # from being compared with the wrong parser.
    groups = defaultdict(list)
    for submission in all_submissions:
        key = (submission["question_id"], submission["language"].lower().strip())
        groups[key].append(submission)

    all_results = []
    for (question_id, language), group in sorted(groups.items()):
        if len(group) < 2:
            continue

        total_pairs = len(group) * (len(group) - 1) // 2
        print(
            f"  Checking {question_id} [{language}] — "
            f"{len(group)} submissions — "
            f"{total_pairs} possible pairs"
        )

        results = compare_all_submissions(group)
        print(f"  Pairs worth reporting: {len(results)}")
        all_results.extend(results)

    return all_results
