# Fix 2: Restructure the AST Analysis Pipeline

## Overview

This document explains why Fix 2 was required, what the problem was in the original code, and exactly what was changed to fix it.

**File changed**: `detection/scorer.py`  
**Function changed**: `compare_all_submissions()`  
**Priority**: 🔴 Critical  
**Raised by**: post-demo review

---

## What the Code Did Before

Inside `compare_all_submissions()`, the pair comparison followed this exact order:

```python
# 1. Get token similarity
tok_pct = token_similarity_percent(code_a, code_b, language)

# 2. SKIP the pair if token similarity is below 25%
if tok_pct < MINIMUM_REPORT_PERCENT:   # MINIMUM_REPORT_PERCENT = 25.0
    continue                            # ← pair is dropped here, AST never runs

# 3. Short-circuit: skip AST if token is already very high
if tok_pct >= 95:
    ast_pct = tok_pct
else:
    ast_pct = ast_similarity_percent(code_a, code_b, language)
```

The key problem is **step 2** — the `continue` statement drops the pair entirely based on token similarity alone, **before AST analysis ever has a chance to run**.

---

## Why This Is a Problem

The product has two detection engines:

| Engine | What it measures |
|--------|-----------------|
| **Tokenizer** | How similar the surface text is — keywords, identifiers, structure as text |
| **AST** | How similar the underlying logical structure is — control flow, nesting, operations |

These two engines are designed to cover **different types of copying**:

- **Token engine catches**: Direct copies, simple variable renames, whitespace changes
- **AST engine catches**: Rewrites where the code looks different but the logic is identical

### The scenario the bug misses:

A student copies another student's solution and then:
- Renames every variable and function
- Adds 10–15 print statements throughout
- Splits one function into two
- Adds comments everywhere

After these changes, the **token similarity might drop to 12–18%** — well below the 25% gate. The pair is silently dropped. The recruiter never sees it.

But the **AST structural fingerprint** of both submissions is still **85–95% similar** because the underlying logic — the loops, conditions, operations, return structures — is unchanged.

```python
# Example

# Original (alice)
def find_max(arr):
    max_val = arr[0]
    for x in arr:
        if x > max_val:
            max_val = x
    return max_val

# Rewritten copy (bob)
def get_largest(numbers):
    print("Starting search...")
    result = numbers[0]
    print(f"Initial: {result}")
    for num in numbers:
        print(f"Checking {num}")
        if num > result:
            result = num
    print(f"Done: {result}")
    return result
```

Token similarity: **~20%** — DROPPED by the gate  
AST similarity: **~90%** — would clearly flag this as suspicious

The AST engine exists exactly for this scenario — and the gate prevents it from ever running.

---

## The Fix

Remove the hard token precondition that gates the entire pair. Instead, compute AST similarity **for all valid pairs**, and use a **hybrid rule**: either token similarity OR AST similarity above their respective thresholds can flag a pair.

```python
# BEFORE — token gate blocks AST entirely for low-token pairs
tok_pct = token_similarity_percent(code_a, code_b, language)

if tok_pct < MINIMUM_REPORT_PERCENT:
    continue   # ← drops the pair, AST never runs

if tok_pct >= 95:
    ast_pct = tok_pct
else:
    ast_pct = ast_similarity_percent(code_a, code_b, language)


# AFTER — AST always runs, hybrid threshold decides whether to report
tok_pct = token_similarity_percent(code_a, code_b, language)

# FIX 2: Always compute AST — do not skip it because token is low.
# This is where smart rewrites are caught.
ast_pct = ast_similarity_percent(code_a, code_b, language)

# Either signal independently can justify reporting the pair
MIN_TOKEN_REPORT_PCT = 25.0
MIN_AST_REPORT_PCT   = 40.0

if tok_pct < MIN_TOKEN_REPORT_PCT and ast_pct < MIN_AST_REPORT_PCT:
    continue   # Both signals are low — this pair is genuinely different
```

---

## The New Threshold Logic

Two separate thresholds now exist:

| Threshold | Value | Meaning |
|-----------|-------|---------|
| `MIN_TOKEN_REPORT_PCT` | 25.0 | Minimum token similarity to flag a pair on token signal alone |
| `MIN_AST_REPORT_PCT` | 40.0 | Minimum AST similarity to flag a pair on structural signal alone |

A pair is **reported** if either condition is true:
- Token similarity ≥ 25%, OR
- AST similarity ≥ 40%

A pair is **dropped** only if **both** are below their thresholds — meaning neither engine found meaningful similarity.

---

## What Happens to the AST Short-Circuit?

The original code had an optimisation:

```python
# Old short-circuit: skip AST if token is already very high
if tok_pct >= 95:
    ast_pct = tok_pct
```

This was removed as part of Fix 2. With the new approach, AST always runs. The short-circuit saved CPU time but it was part of the same pipeline that gated AST from running at all. Since AST must now always run, the short-circuit no longer makes sense and is removed.

**Performance note**: Yes, this means AST runs on more pairs than before. But the AST engine is the primary tool for catching sophisticated cheating — accuracy is the priority here over speed.

---

## Example: Before vs After

### Scenario: Smart rewrite — low token, high AST

| | Before Fix 2 | After Fix 2 |
|--|-------------|-------------|
| Token similarity | 18% | 18% |
| AST similarity | (never computed) | 88% |
| Reported? | ❌ No — dropped at gate | ✅ Yes — AST ≥ 40% |
| Label | (none) | Low text overlap, high structural similarity |

### Scenario: Genuinely different code — low token, low AST

| | Before Fix 2 | After Fix 2 |
|--|-------------|-------------|
| Token similarity | 12% | 12% |
| AST similarity | (never computed) | 15% |
| Reported? | ❌ No — dropped at gate | ❌ No — both below threshold |
| Result | Same outcome — correctly dropped |

---

## What Stays the Same

- The 25% minimum token threshold still exists — it just no longer gates AST
- The label engine (`get_label()`) is unchanged in this fix
- All other filters (minimum token length, same candidate skip) are unchanged

---

## Summary of Change

| | Before | After |
|--|--------|-------|
| When AST runs | Only if token ≥ 25% | Always, for every valid pair |
| What drops a pair | Token < 25% | Token < 25% AND AST < 40% |
| Smart rewrites | Silently missed | Caught by AST signal |
| Performance | Fewer AST calls | More AST calls (necessary trade-off) |

---

## See Also

- `detection/scorer.py` — the file this fix was applied to
- `detection/ast_comparator.py` — the AST engine being called
- `docs/FIX_1_LANGUAGE_GROUPING.md` — Fix 1 (applied before this)
- `docs/SCORER_EXPLAINED.md` — full explanation of the scoring pipeline
- `docs/AST_COMPARATOR_EXPLAINED.md` — how the AST engine works internally
