# Code Plagiarism Detection Service
## Complete Demo Presentation with Screenshots Guide

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Technical Architecture](#technical-architecture)
3. [Core Detection Methods](#core-detection-methods)
4. [Demo Walkthrough](#demo-walkthrough)
5. [Screenshot Guide](#screenshot-guide)
6. [API Documentation](#api-documentation)
7. [Q&A Section](#qa-section)

---

## Project Overview

### What is This?
A production-ready FastAPI service that detects code plagiarism across 26+ programming languages using Token-based and AST-based analysis.

### Key Features
- ✅ Multi-language support (Python, Java, JavaScript, C++, Rust, Go, PHP, Ruby, Swift, Kotlin, and 16+ more)
- ✅ Dual-engine detection (Token-based + AST-based)
- ✅ Catches sophisticated plagiarism (renamed variables, added dummy code)
- ✅ 7 risk classification levels
- ✅ REST API with automatic documentation
- ✅ Scalable batch processing

### Why It Matters
Traditional plagiarism tools only check text similarity. Students can easily fool them by:
- Renaming variables (`max` → `highest`)
- Adding dummy print statements
- Changing comments

Our system uses **Token-based and AST analysis** to catch these tricks by comparing code patterns and logic structure, not just the text.

---

## Technical Architecture

### Tech Stack
```
Backend:    FastAPI (Python 3.x)
Database:   PostgreSQL (Neon serverless)
Parsers:    Tree-sitter (26+ languages)
Detection:  Token-based (Winnowing) + AST-based (Set comparison)
```

### Project Structure
```
plagiarism-service/
├── main.py                      # FastAPI REST API
├── db/
│   └── neon.py                 # Database connection
├── detection/
│   ├── tokenizer.py            # Token-based similarity (Winnowing)
│   ├── ast_comparator.py       # AST structural analysis
│   └── scorer.py               # Scoring engine & label classification
├── models/
│   └── schemas.py              # API request/response models
└── demo_showcase.py            # Full demo script
```

---

## Core Detection Methods

### 
**Purpose**: Detect copied code even with noise insertions

**How it works**:
1. Normalize code (remove comments, replace identifiers with `VAR`)
2. Create k-grams (sequences of 5 tokens)
3. Hash each k-gram
4. Use sliding window to select minimum hashes
5. Compare fingerprint sets

**Example**:
```python
# Original
def find_max(arr):
    max = arr[0]
    return max

# After normalization
def VAR(VAR): VAR = VAR[0] return VAR

# K-grams (k=5)
['def', 'VAR', 'VAR', 'VAR', '=']
['VAR', 'VAR', 'VAR', '=', 'VAR']
...
```

**Why it's better than simple text comparison**:
- Ignores whitespace, comments, variable names
- Resistant to small insertions (dummy prints)
- Guarantees detection of matches above threshold

---

### 2. AST-Based Detection (Structural Analysis)
**Purpose**: Catch "smart plagiarism" where students add dummy code but keep the core logic structure

**How it works**:
1. Parse code into tree structure using Tree-sitter
2. Extract structural node types (FunctionDef, For, If, Return, etc.)
3. Filter out non-structural nodes (Call, Expr for print statements)
4. Compare unique node type sets using Jaccard similarity

**Example**:
```python
# Student A
def find_max(arr):
    max_val = arr[0]
    for num in arr:
        if num > max_val:
            max_val = num
    return max_val

# AST nodes (structural only)
['Module', 'FunctionDef', 'Assign', 'For', 'If', 'Compare', 'Assign', 'Return']

# Student B (added dummy prints)
def get_highest(items):
    print("Starting...")
    highest = items[0]
    for item in items:
        print("Checking...")
        if item > highest:
            highest = item
    return highest

# AST nodes (structural only - Call nodes from print() are filtered out)
['Module', 'FunctionDef', 'Assign', 'For', 'If', 'Compare', 'Assign', 'Return']
```

**Result**: Token similarity: 57%, AST similarity: 100% → AST catches the identical logic despite dummy code!

---

### 3. Tree-Sitter Universal Parser
**Purpose**: Parse 26+ languages with production-grade accuracy

**Supported Languages**:
Python, Java, JavaScript, TypeScript, C, C++, Rust, Go, PHP, Ruby, Swift, Kotlin, Scala, Haskell, Lua, Bash, HTML, CSS, JSON, YAML, TOML, SQL, OCaml, and more

**Why Tree-sitter**:
- Used by GitHub Copilot, Atom editor
- Handles syntax errors gracefully
- Incremental parsing (fast)
- Battle-tested on millions of repos

---

### 4. Label Classification Engine

**7 Risk Categories**:

| Label | Token % | AST % | Risk | Description |
|-------|---------|-------|------|-------------|
| **Exact copy** | 100 | 100 | 🔴 HIGH | Completely identical |
| **Almost identical** | 90+ | Any | 🔴 HIGH | Tiny changes only |
| **Highly similar** | 75-89 | Any | 🟡 MEDIUM | Clear copying with renaming |
| **Smart copy — logic identical** | <75 | 95+ | 🔴 HIGH | Rewrote surface, kept logic (WORST!) |
| **Suspicious — high structural overlap** | 50+ | 75+ | 🟡 MEDIUM | Significant structural match |
| **Moderately similar** | 50+ | <75 | 🟢 LOW | Generic overlap |
| **Slightly similar** | 25+ | 50+ | 🟢 LOW | Minor similarities |

---

## Demo Walkthrough

### Running the Demo
```bash
python demo_showcase.py
```

### What the Demo Shows
- 7 different plagiarism cases
- 7 different programming languages
- All 7 label categories
- Side-by-side code comparison
- Token + AST scores for each case

---

## Screenshot Guide



## API Documentation

### Endpoint: POST `/check-plagiarism`

**Request Body**:
```json
{
  "batch_id": "string"
}
```

**Response**:
```json
{
  "batch_id": "batch_001",
  "total_submissions": 50,
  "total_pairs_checked": 1225,
  "summary_by_question": [
    {
      "question_id": "q1",
      "total_pairs_checked": 300,
      "exact_copies": 5,
      "almost_identical": 3,
      "highly_similar": 8,
      "moderately_similar": 12,
      "slightly_similar": 15
    }
  ],
  "results": [
    {
      "candidate_a": "student_001",
      "candidate_b": "student_002",
      "question_id": "q1",
      "language": "python",
      "token_similarity_pct": 92.5,
      "ast_similarity_pct": 95.0,
      "label": "Almost identical"
    }
  ]
}
```

### Starting the Server
```bash
uvicorn main:app --reload
```

### Accessing API Docs
```
http://localhost:8000/docs
```

---

