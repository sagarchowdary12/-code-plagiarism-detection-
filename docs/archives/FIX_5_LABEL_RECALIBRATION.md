# Fix 5: Recalibrate Pair Labels to Match Actual Confidence

## Overview

This document explains why Fix 5 was required, what the problem was with the original labels, and the changes applied.

**Files changed**: `detection/scorer.py`, `models/schemas.py`, `main.py`  
**Priority**: 🟡 Medium  
**Raised by**: post-demo review  
**Status**: ✅ Applied

---

## What the Code Does Right Now

When `scorer.py` determines that two pieces of code look alike, it assigns a human-readable label. Right now, it assigns the following labels:
- `"Exact copy"`
- `"Almost identical"`
- `"Highly similar"`
- `"Smart copy — logic identical"`
- `"Suspicious — high structural overlap"`
- `"Moderately similar"`
- `"Slightly similar"`

---

## Why This Is a Problem

Your manager correctly pointed out a major liability issue with these labels: **They accuse the student of "copying" and acting "suspiciously".**

In an academic or legal setting, an automated algorithm cannot **prove intent**, it can only **prove overlap**. If a student challenges a plagiarism accusation, a tool that claims "the student copied" is legally much weaker than a tool that claims "there is 98% textual overlap". 

Using words like "copy", "identical logic", and "suspicious" assumes we know *why* the student wrote the code, which we don't. We only know *what* they wrote.

---

## The Fix

We need to reword these definitions so they only describe **observable similarity signals**, not conclusions about cheating.

We will update all the Python files to use the following new labels:

| Old Label | New Label we will use |
|-----------|-----------|
| `Exact copy` | `Exact match` |
| `Almost identical` | `Near-identical text` |
| `Highly similar` | `High token overlap` |
| `Smart copy — logic identical` | `Low text overlap, high structural similarity` |
| `Suspicious — high structural overlap` | `Moderate similarity — structural and textual` |
| `Moderately similar` | `Moderate text similarity` *(I will add "text" for clarity)* |
| `Slightly similar` | `Slight text similarity` *(I will add "text" for clarity)* |

### How this affected the code (applied changes):
1. **`scorer.py`**: All string returns in `get_label()` were replaced with the new neutral labels.
2. **`models/schemas.py`**: The `QuestionSummary` schema fields were renamed to match the new neutral labels (e.g., `smart_copies` → `low_text_high_structure`).
3. **`main.py`**: The dashboard aggregation buckets were updated to count by the new label strings.

---

## Status: ✅ Complete

All three files have been updated. The new labels are live in production.
