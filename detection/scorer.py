from itertools import combinations
from collections import defaultdict
from detection.tokenizer import token_similarity_percent, clean_code_from_db as clean_code
from detection.ast_comparator import ast_similarity_percent

# Minimum tokens required to compare two submissions
MIN_TOKEN_LENGTH = 5

# Only return pairs where token similarity is AT LEAST this percentage
# Pairs below this are two students who wrote genuinely different solutions
# 25% is very generous — anything below is just noise
MINIMUM_REPORT_PERCENT = 25.0


def get_token_count(source_code: str) -> int:
    cleaned = clean_code(source_code)
    return len(cleaned.split())


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
        return "Exact copy"

    # Token very high — obvious copy with tiny changes
    if token_pct >= 90:
        return "Almost identical"

    # Token high — clearly copied with some renaming
    if token_pct >= 75:
        return "Highly similar"

    # HUGE: Text is very different (under 75 words match), but the underlying Blueprint is almost perfectly identical (over 95)!
    # This means student rewrote the surface but kept exact same logic. This is deliberate smart plagiarism — worst kind
    if token_pct < 75 and ast_pct >= 95:
        return "Smart copy — logic identical"

    # Suspicious logic overlap (Token is generic, but structural skeleton matches heavily)
    if token_pct >= 50 and ast_pct >= 75:
        return "Suspicious — high structural overlap"

    # Token moderate (Generic text overlap, logic wasn't strong enough to hit trap above)
    if token_pct >= 50:
        return "Moderately similar"

    # Token low but AST moderate — slightly suspicious
    if token_pct >= 25 and ast_pct >= 50:
        return "Slightly similar"

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

        # Skip if either code is too short
        if get_token_count(code_a) < MIN_TOKEN_LENGTH:
            continue
        if get_token_count(code_b) < MIN_TOKEN_LENGTH:
            continue

        # Get token similarity percentage
        tok_pct = token_similarity_percent(code_a, code_b, language)

        # SKIP pairs below minimum report threshold
        # These are not worth showing to the recruiter at all
        if tok_pct < MINIMUM_REPORT_PERCENT:
            continue

        # Short-Circuit: If the token score is already an exact copy (>95%), we don't need to waste CPU running the AST parser!
        if tok_pct >= 95:
            ast_pct = tok_pct
        else:
            ast_pct = ast_similarity_percent(code_a, code_b, language)

        # Get human readable label
        label = get_label(tok_pct, ast_pct)

        results.append({
            "candidate_a":          sub_a["candidate_id"],
            "candidate_b":          sub_b["candidate_id"],
            "question_id":          question_id,
            "language":             language,
            "token_similarity_pct": tok_pct,
            "ast_similarity_pct":   ast_pct,
            "label":                label,
        })

    # Sort by token similarity — highest first so worst cases appear at top
    results.sort(key=lambda x: x["token_similarity_pct"], reverse=True)

    return results


def run_plagiarism_check(all_submissions: list) -> list:
    # Group submissions by question_id
    groups = defaultdict(list)
    for submission in all_submissions:
        groups[submission["question_id"]].append(submission)

    all_results = []
    for question_id, group in sorted(groups.items()):
        if len(group) < 2:
            continue

        total_pairs = len(group) * (len(group) - 1) // 2
        print(f"  Checking {question_id} — "
              f"{len(group)} submissions — "
              f"{total_pairs} possible pairs")

        results = compare_all_submissions(group)
        print(f"  Pairs worth reporting: {len(results)}")
        all_results.extend(results)

    return all_results
