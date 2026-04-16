# Fix 1: Group Submissions by Question AND Language

## Overview

This document explains why Fix 1 was required, what the problem was in the original code, and exactly what was changed to fix it.

**File changed**: `detection/scorer.py`  
**Function changed**: `run_plagiarism_check()`  
**Priority**: 🔴 Critical  
**Raised by**:post-demo review

---

## What the Code Did Before

The `run_plagiarism_check()` function grouped all submissions **only by `question_id`**:

```python
def run_plagiarism_check(all_submissions: list) -> list:
    # Group submissions by question_id  ← ONLY question_id
    groups = defaultdict(list)
    for submission in all_submissions:
        groups[submission["question_id"]].append(submission)
```

Once grouped, `compare_all_submissions()` was called for each group. Inside that function, the **language was taken from the first submission in the group** and applied to all comparisons:

```python
def compare_all_submissions(submissions: list) -> list:
    question_id = submissions[0]["question_id"]
    language    = submissions[0]["language"]   # ← First submission's language only!

    for sub_a, sub_b in combinations(submissions, 2):
        tok_pct = token_similarity_percent(code_a, code_b, language)  # language applied to ALL pairs
        ast_pct = ast_similarity_percent(code_a, code_b, language)
```

---

## Why This Is a Problem

The database (`neon.py`) fetches submissions like this:

```python
SELECT candidate_id, question_id, source_code, language
FROM assessment_submissions_coding
WHERE assessment_id = %s
ORDER BY question_id, candidate_id
```

Each submission has its **own `language` field**. If two candidates answer the same question — one in Python and one in Java — both get placed into the same group.

### What goes wrong:

```python
# Example — Q1 accepts both Python and Java
submissions_for_Q1 = [
    {"candidate_id": "alice",   "question_id": "Q1", "language": "python", "source_code": "..."},
    {"candidate_id": "bob",     "question_id": "Q1", "language": "java",   "source_code": "..."},
    {"candidate_id": "charlie", "question_id": "Q1", "language": "python", "source_code": "..."},
]

# After grouping by question_id only:
groups = {
    "Q1": [alice_python, bob_java, charlie_python]  # Mixed languages in one group!
}

# compare_all_submissions() takes language from submissions[0]:
language = "python"   # alice's language

# Now ALL pairs use "python" as the language — including alice vs bob (python vs java)
# bob's Java code is being parsed and compared using the Python tokenizer → garbage
```

### The three bad outcomes:

| Pair | Reality | What happened |
|------|---------|---------------|
| alice (Python) vs bob (Java) | Completely different languages | Compared using Python parser → meaningless score |
| alice (Python) vs charlie (Python) | Same language | Correct |
| bob (Java) vs charlie (Python) | Different languages | Compared using Python parser → meaningless score |

The result for `alice vs bob` and `bob vs charlie` could show **0% similarity** (which looks like they're clearly original) or produce **random scores** depending on how much the Java code accidentally matches Python tokens. Either way the output is wrong and cannot be trusted.

---

## The Fix

Group submissions by **both** `question_id` **and** `language` together, so each comparison group is guaranteed to contain only same-language submissions:

```python
# BEFORE
groups[submission["question_id"]].append(submission)

# AFTER
key = (submission["question_id"], submission["language"].lower().strip())
groups[key].append(submission)
```

The loop then iterates over `(question_id, language)` pairs instead of just `question_id`:

```python
# BEFORE
for question_id, group in sorted(groups.items()):
    print(f"  Checking {question_id} — {len(group)} submissions")
    results = compare_all_submissions(group)

# AFTER
for (question_id, language), group in sorted(groups.items()):
    print(f"  Checking {question_id} [{language}] — {len(group)} submissions")
    results = compare_all_submissions(group)
```

---

## Example: Before vs After

### Before Fix — Mixed language group

```
Input batch: Q1 with 3 students (2 Python, 1 Java)

Grouping:
  "Q1" → [alice_python, bob_java, charlie_python]

Comparisons:
  alice vs bob     → compared using Python (WRONG — bob wrote Java)
  alice vs charlie → compared using Python (correct)
  bob vs charlie   → compared using Python (WRONG — bob wrote Java)

Output: 3 pairs — 2 of which have unreliable scores
```

### After Fix — Separate groups per language

```
Input batch: Q1 with 3 students (2 Python, 1 Java)

Grouping:
  ("Q1", "python") → [alice_python, charlie_python]
  ("Q1", "java")   → [bob_java]   ← only 1 submission, skipped (needs ≥ 2)

Comparisons:
  alice vs charlie → compared using Python (correct)

Output: 1 pair — all scores are reliable
```

---

## What Stays the Same

- `compare_all_submissions()` is **not changed** — it still takes a flat list of submissions and compares every pair
- The `language` variable inside `compare_all_submissions()` is still taken from `submissions[0]["language"]` — but now that is safe because **every submission in the group has the same language**
- All thresholds, labels, and scoring logic are unchanged

---

## Impact on Existing Batches

If your current database only has **single-language questions** (every submission for Q1 is Python, every submission for Q2 is Java, etc.), then the grouping key changes from `"Q1"` to `("Q1", "python")` — but the groups contain exactly the same submissions as before. **Results are identical.**

The fix only changes behaviour when a question genuinely has mixed-language submissions — and in that case the old behaviour was producing bad results anyway.

---

## Summary of Change

| | Before | After |
|--|--------|-------|
| Grouping key | `question_id` | `(question_id, language)` |
| Mixed-language pairs | Silently compared using wrong parser | Placed in separate groups, never mixed |
| Same-language batches | Works correctly | Works identically |
| Print output | `Checking Q1 — 3 submissions` | `Checking Q1 [python] — 2 submissions` |

---

## See Also

- `detection/scorer.py` — the file this fix was applied to
- `db/neon.py` — where submissions are fetched from the database (each row has its own `language` field)
- `SCORER_EXPLAINED.md` — full explanation of the scoring pipeline
