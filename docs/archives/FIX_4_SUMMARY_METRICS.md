# Fix 4: Correct Summary Metrics and Response Semantics

## Overview

This document explains why Fix 4 was required, what the problem was in the original payload generation, and exactly what was changed to fix it.

**File changed**: `main.py` and `models/schemas.py`  
**Priority**: 🟡 Medium  
**Raised by**: post-demo review

---

## What the Code Did Before

When a user hit the `/check-plagiarism` API endpoint, the application passed the results to `main.py`. This script aggregated the pairs to create a **Summary Payload** meant to be displayed on the Recruiter Dashboard.

```python
# ❌ The Problem: Calculating buckets purely with token_similarity_pct
summaries.append(QuestionSummary(
    question_id         = qid,
    total_pairs_checked = len(pairs),
    exact_match         = sum(1 for p in pairs if p["token_similarity_pct"] == 100),
    near_identical_text = sum(1 for p in pairs if 90  <= p["token_similarity_pct"] < 100),
    highly_similar      = sum(1 for p in pairs if 75  <= p["token_similarity_pct"] < 90),
    moderately_similar  = sum(1 for p in pairs if 50  <= p["token_similarity_pct"] < 75),
    slightly_similar    = sum(1 for p in pairs if 25  <= p["token_similarity_pct"] < 50),
))
```

---

## Why This Is a Problem

This logic completely ignored the **AST analysis engine**. 

If a student submitted a "Smart Copy", the tokenizer engine might score the surface-level text at **15%**, but the AST engine would score it at **100%**. 

Inside `scorer.py`, this pair would correctly be caught by the hybrid rule and flagged under the label `"Low text overlap, high structural similarity"`.

**However**, when `main.py` gathered the summary metrics, it only looked at: `p["token_similarity_pct"]`. Since `15%` is less than `25%`, this pair was **discarded from the summary dashboard entirely**. 

This resulted in a broken user experience: A recruiter would look at the summary and see **0 pairs flagged**, but when they opened the detailed results, they would see a "Low text overlap, high structural similarity" pair sitting right there!

---

## The Fix

I removed the raw math from the API layer (`main.py`) entirely. Instead, we instructed the summary aggregator to group the pairs based **on the final label assigned by the scoring engine**.

Since `scorer.py` already factored both the Token and AST engines into its decision to assign a label, we just count those labels directly!

### Step 1: Add the missing AST labels to the Schema
In `models/schemas.py`, I added the two labels that were missing:
```python
    smart_copies:          int
    suspicious_structural: int
```

### Step 2: Swap the logic in main.py
```python
# ✅ The Fix: Count by label instead of by token percentage
summaries.append(QuestionSummary(
    question_id           = qid,
    total_pairs_checked   = len(pairs),
    exact_match                 = sum(1 for p in pairs if p["label"] == "Exact match"),
    near_identical_text         = sum(1 for p in pairs if p["label"] == "Near-identical text"),
    highly_similar        = sum(1 for p in pairs if p["label"] == "High token overlap"),
    smart_copies          = sum(1 for p in pairs if p["label"] == "Low text overlap, high structural similarity"),
    suspicious_structural = sum(1 for p in pairs if p["label"] == "Moderate similarity — structural and textual"),
    moderately_similar    = sum(1 for p in pairs if p["label"] == "Moderate text similarity"),
    slightly_similar      = sum(1 for p in pairs if p["label"] == "Slight text similarity"),
))
```

---

## What Stays the Same

- The actual plagiarism detection math (`scorer.py`) was not touched here.
- We still return `QuestionSummary` so the frontend doesn't break; it just gives more accurate data now.

---

## Summary of Change

| Metric Strategy | Before | After |
|-------|--------|-------|
| Grouping Criteria | Derived dynamically by `main.py` doing its own math | Directly uses the `Label` assigned by `scorer.py` |
| AST Visibility | ❌ Invisible in dashboard | ✅ Fully visible via `smart_copies` |
| Predictability | Prone to mismatch | Guaranteed 1-to-1 match |

---
