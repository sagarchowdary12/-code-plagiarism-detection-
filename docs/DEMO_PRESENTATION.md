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
├── db/
│   └── neon.py                 # Neon Serverless Database Logic
├── models/
│   └── schemas.py              # Schema for label-based metrics (Fix 4)
├── main.py                      # FastAPI REST API
├── test_75_students.py          # Python Stress Test
├── test_1000_students_java.py   # Java Stress Test (1,000 students)
```

---

## The 6 Architectural Fixes
This version of the service implements six critical fixes to move from a prototype to a production-ready engine:

1. Fix 1: Language-Based Grouping - Prevented invalid cross-language comparisons.
2. Fix 2: Independent AST Pipeline - Removed the "token gate" so smart copies are always caught.
3. Fix 3: AST Winnowing - Replaced naive set comparison with ordered structural hashing.
4. Fix 4: Label-Derived Metrics  - Dashboard summary is now powered by detection labels.
5. Fix 5: Neutral Recalibration  - All labels converted to legally safe, signal-based terms.
6. Fix 6: Strict Token Gating  - Comments are stripped before checking code length.
7. Fix 7: AST DFS & Tuning     - Depth-First Search and k-gram sensitivity tuning.

---

## Core Detection Methods

### 1. Token-Based Winnowing
Purpose: Detect copied code snippets even with noise insertions.

How it works :
1. Normalize code (remove comments, genericize identifiers).
2. Create sliding k-gram windows.
3. Hash and "winnow" to create a unique code fingerprint.
4. Compare fingerprints to find overlapping regions.

---

### 2. AST-Based Detection (Structural Winnowing)
Purpose : Catch "smart plagiarism" where students hide the copy by renaming everything.

How it works:
1. Parse code into a Tree-Sitter AST.
2. Filter for Structural nodes only (loops, conditionals, assignments).
3. Apply winnowing hashing to the node sequence, preserving order and depth.
4. Catch pairs where surface text is different but logic structure is identical.

Result : Even if a student renames `max` to `highest` and adds 10 `print()` statements, the AST Winnowed score remains nearly 100%.

---

## Demo Walkthrough

### Running the Stress Tests
```bash
# Python
python test_75_students.py

# Java
python test_1000_students_java.py
```

### Key Demo Segments:
- **Set A**: Python stress test (75 students).
- **Set B**: Java stress test (1,000 students).
- **Critical Logic**: Proves ZERO cross-algorithm false positives.
- **Structural Integrity**: DFS traversal catches reordered logic.

---

## API Documentation

### Endpoint: POST `/check-plagiarism`
Returns metrics derived from the new **Fix 4** summary logic.

**Example Response**:
```json
{
  "batch_id": "batch_005",
  "total_submissions": 20,
  "total_pairs_checked": 190,
  "summary_by_question": [
    {
      "question_id": "matrix_multiply",
      "total_pairs_checked": 45,
      "exact_match": 2,
      "near_identical_text": 1,
      "high_token_overlap": 4,
      "low_text_high_structure": 1,
      "moderate_structural_textual": 2,
      "moderate_text_similarity": 5,
      "slight_text_similarity": 10
    }
  ],
  "results": [
    {
      "candidate_a": "alice_dev",
      "candidate_b": "bob_enterprise",
      "question_id": "matrix_multiply",
      "language": "python",
      "token_similarity_pct": 12.5,
      "ast_similarity_pct": 98.4,
      "label": "Low text overlap, high structural similarity"
    }
  ]
}
```

---

### Professional Testing Suite
Show your manager that the system is self-verifying.
- **Run**: `pytest`
- **What it proves**: "We have automated unit tests that verify variable renaming detection, comment stripping, and structural logical matching (Fix 7). This ensures the system remains accurate even as we scale."

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

