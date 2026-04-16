# Code Plagiarism Detection Service
## Complete Demo Presentation Guide (v2.0 - Final Refactor)

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Technical Architecture (Finalized)](#technical-architecture)
3. [The 6 Architectural Fixes](#the-6-architectural-fixes)
4. [Core Detection Methods](#core-detection-methods)
5. [Demo Walkthrough](#demo-walkthrough)
---

## Project Overview

### What is This?
A production-ready FastAPI service that detects code plagiarism across 26+ programming languages using dual-engine analysis (Token-based + Structural AST).

### Key Features
- ✅ **Multi-language support**: Python, Java, JS, C++, Rust, Go, Ruby, Swift, Kotlin, and 16+ more.
- ✅ **Dual-engine detection**: Token-based Winnowing + Structural AST Winnowing.
- ✅ **Smart Evasion Detection**: Catches renamed variables, dummy code, loop mutations, and class-wrapping.
- ✅ **Neutral Legal Labeling**: Uses non-accusatory signal-based terminology.
- ✅ **Composite Routing**: Isolated comparisons by `(question_id, language)`.

### Why It Matters
Traditional tools only check text. Students easily fool them by renaming variables or adding comments. Our system compares **logic structure**, not just the text, making it nearly impossible to evade by simple variable swapping.

---

## Technical Architecture

### Tech Stack
```
Backend:    FastAPI (Python 3.x)
Database:   PostgreSQL (Neon serverless)
Parsers:    Tree-sitter (Universal Parser)
Detection:  Token-based (Winnowing) + AST-based (Structural Winnowing)
```

### Project Structure
```
plagiarism-service/
├── main.py                      # FastAPI REST API
├── detection/
│   ├── tokenizer.py            # Tokenization & Winnowing
│   ├── ast_comparator.py       # AST Structural Winnowing (Fix 3)
│   └── scorer.py               # Hybrid Scoring & Neutral Labeling (Fix 5)
├── models/
│   └── schemas.py              # Schema for label-based metrics (Fix 4)
└── demo_for_team_leader.py      # New Comprehensive Demo Script
```

---

## The 6 Architectural Fixes
This version of the service implements six critical fixes to move from a prototype to a production-ready engine:

1.  **Fix 1: Language-Based Grouping** - Prevented invalid cross-language comparisons.
2.  **Fix 2: Independent AST Pipeline** - Removed the "token gate" so smart copies are always caught.
3.  **Fix 3: AST Winnowing** - Replaced naive set comparison with ordered structural hashing.
4.  **Fix 4: Label-Derived Metrics** - Dashboard summary is now powered by detection labels.
5.  **Fix 5: Neutral Recalibration** - All labels converted to legally safe, signal-based terms.
6.  **Fix 6: Strict Token Gating** - Comments are stripped before checking code length.

---

## Core Detection Methods

### 1. Token-Based Winnowing
**Purpose**: Detect copied code snippets even with noise insertions.

**How it works**:
1. Normalize code (remove comments, genericize identifiers).
2. Create sliding k-gram windows.
3. Hash and "winnow" to create a unique code fingerprint.
4. Compare fingerprints to find overlapping regions.

---

### 2. AST-Based Detection (Structural Winnowing)
**Purpose**: Catch "smart plagiarism" where students hide the copy by renaming everything.

**How it works**:
1. Parse code into a Tree-Sitter AST.
2. Filter for **Structural nodes** only (loops, conditionals, assignments).
3. Apply winnowing hashing to the **node sequence**, preserving order and depth.
4. Catch pairs where surface text is different but logic structure is identical.

**Result**: Even if a student renames `max` to `highest` and adds 10 `print()` statements, the AST Winnowed score remains nearly **100%**.

---

## Demo Walkthrough

### Running the Demo
```bash
python demo_for_team_leader.py
```

### Key Demo Segments:
- **Set A**: String algorithms in **Go, Rust, Kotlin**.
- **Set B**: Data structures in **Python, Java, JS**.
- **Set C (Critical)**: Two different algorithms to prove **ZERO false positives**.
- **Set D**: Evasion attempt (Loop mutation) caught via AST.
- **Multi-Lang**: Bubble Sort across 5 different parsers.

---

## API Documentation

### Endpoint: POST `/check-plagiarism`
Returns metrics derived from the new **Fix 4** summary logic.

**Example Response**:
```json
{
  "batch_id": "batch_005",
  "summary_by_question": [
    {
      "question_id": "matrix_multiply",
      "exact_match": 2,
      "low_text_high_structure": 1,
      "high_token_overlap": 4,
      "likely_original": 43
    }
  ],
  "results": [
    {
      "candidate_a": "alice_dev",
      "candidate_b": "bob_enterprise",
      "label": "Low text overlap, high structural similarity"
    }
  ]
}
```

---

### Final Service Status
- **Accuracy**: High (Dual-Engine)
- **Legal Stand**: Neutral (Signal-Based Labels)
- **Parsers**: Stable (Tree-Sitter)
- **Status**: **READY FOR STAGING DEPLOYMENT**
```bash
uvicorn main:app --reload
```

### Accessing API Docs
```
```

---

