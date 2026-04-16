# Fix 3: Replace Set-Based AST Comparison

## Overview

This document explains why Fix 3 was required, what the problem was in the original code, and exactly what was changed to fix it.

**File changed**: `detection/ast_comparator.py`  
**Function changed**: `ast_similarity_percent()`  
**Priority**: 🔴 Critical  
**Raised by**: post-demo review

---

## What the Code Did Before

Inside `ast_comparator.py`, the similarity between two AST (Abstract Syntax Tree) traversals was calculated using basic **Python sets**:

```python
def ast_similarity_percent(code_a: str, code_b: str, language: str = 'python') -> float:
    nodes_a = get_structural_tokens(code_a, language)
    nodes_b = get_structural_tokens(code_b, language)

    # ❌ The Problem: Converting lists to unordered sets
    set_a = set(nodes_a)
    set_b = set(nodes_b)

    intersection = set_a & set_b
    union = set_a | set_b

    score = (len(intersection) / len(union)) * 100
    return round(score, 2)
```

---

## Why This Is a Problem

An AST traversal produces an ordered list of nodes representing the structure of the code (e.g., `['FunctionDef', 'For', 'If', 'Assign', 'Return']`).

When you convert a list into a Python `set()`, two critical things are destroyed:
1. **Order is lost**: `['For', 'If']` becomes identical to `['If', 'For']`
2. **Frequency is lost**: `['Assign', 'Assign', 'Assign']` shrinks to just `{'Assign'}`

### The specific failure scenario (False Positives):

Imagine two completely different student submissions that simply belong to the same concept (like an array manipulation question). Both students write a `for` loop, an `if` statement, and an `assign` statement. 

Because they use the same basic building blocks, their sets of node *types* will be identical:
`{'FunctionDef', 'For', 'If', 'Assign', 'Return', 'BinOp'}`

Even if Student A wrote a single elegant loop and Student B wrote a messy 5-loop disaster, the set-based comparison will score them as **100% structurally identical**. This ruins the credibility of the AST engine.

---

## The Fix

We replace the naive set comparison with **Winnowing Fingerprints over ordered k-gram hashes**. 

Interestingly, the math for this (`winnowing_ast()`) was already written earlier in the `ast_comparator.py` file, but it was being skipped. We simply changed the main scoring function to use it.

```python
# BEFORE (Set comparison)
set_a = set(nodes_a)
set_b = set(nodes_b)

# AFTER (Winnowing comparison)
# I use the existing winnowing_ast() function instead
set_a = winnowing_ast(nodes_a)
set_b = winnowing_ast(nodes_b)
```

### Why Winnowing is mathematically superior:
Winnowing splits the ordered list of nodes into overlapping chunks (k-grams), hashes them, and selects a mathematically representative fingerprint. 

Because it operates on **sequences** rather than individual isolated nodes:
- It respects the exact order the nodes appear in the tree
- It respects how deeply nested the logic is
- It catches large blocks of copied structure even if some surrounding code was modified

### Example: Before vs After

**Scenario:** Two students write completely different algorithms that both happen to use loops and conditions.

| Metric | Before Fix 3 | After Fix 3 |
|--------|--------------|-------------|
| Extracted Nodes A | `['For', 'If', 'Assign']` | `['For', 'If', 'Assign']` |
| Extracted Nodes B | `['If', 'Assign', 'For']` | `['If', 'Assign', 'For']` |
| Ordered? | ❌ Destroyed by `set()` | ✅ Preserved by `winnowing` |
| Comparison Score | **100%** (False Positive) | **0%** (Correctly different) |

---

## What Stays the Same

- The Tree-Sitter language parsers are untouched
- The Python built-in AST parser is untouched
- No dependencies are added

---

## Summary of Change

| | Before | After |
|--|--------|-------|
| Comparison Method | `set(nodes)` | `winnowing_ast(nodes)` |
| Handles Ordering? | No | Yes |
| Susceptible to False Positives? | Highly susceptible | Highly resistant |

---

## See Also

- `detection/ast_comparator.py` — the file this fix was applied to
- `docs/FIX_2_AST_PIPELINE.md` — Fix 2 (applied before this)
