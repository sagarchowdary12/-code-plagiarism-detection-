# Fix 6: Align Short-Code Gating with the Tokenizer

## Overview

This document explains Fix 6, covering the problem with how the engine handles very short student submissions, and how we are fixing it.

**File to be changed**: `detection/scorer.py`  
**Priority**: 🟡 Medium  
**Raised by**: post-demo review

---

## What the Code Does Right Now

Before running the heavy, expensive similarity checks, `scorer.py` has a "Filter Gate". It checks if the submission is so short that it's meaningless (e.g., someone just typing "pass"). 

Currently, the gate does this:
```python
# The current flawed logic:
def get_token_count(source_code: str) -> int:
    cleaned = clean_code(source_code)
    return len(cleaned.split()) # Splits by whitespace
```

It just counts the raw words separated by spaces. If a student's code has fewer than 5 words, it skips it.

---

## Why This Is a Problem

The gate (which decides who is allowed into the process) uses **different math** than the Tokenizer (which actually does the work). 

If a student pastes 50 lines of English comments but only 2 lines of real code (`def foo(): return 1`), the whitespace splitter counts 150 words! The submission sails right through the gate. 
But when it hits the real Tokenizer, all those comments are instantly deleted, leaving only `['def', 'VAR', 'return', '1']`. This produces an empty winnowing set and crashes the similarity percentages for that pair.

You must only measure length using **the exact same normalized tokens** that the engine compares.

---

## The Fix

We will discard the raw whitespace splitter and switch the filter gate to use the full `tokenize()` function. 

### Step 1: Update the Import
In `scorer.py`, we will import `tokenize` from the `tokenizer.py` engine.

### Step 2: Update the length check
We will rewrite the length checker to run the exact same `tokenize` method:
```python
# ✅ The Fix
def get_token_count(source_code: str, language: str) -> int:
    return len(tokenize(source_code, language))
```

### Step 3: Update the Loop
Inside the main loop, we will pass the `language` argument into the function so the Tokenizer knows how to handle the code:
```python
    # Skip if either code's normalized tokens are too short
    if get_token_count(code_a, language) < MIN_TOKEN_LENGTH:
        continue
```

---

## Review Required

Please take a look! Does making the gate use the same token math as the engine make sense? If you are good with this, just give me the thumbs up and I will apply our final code fix!
