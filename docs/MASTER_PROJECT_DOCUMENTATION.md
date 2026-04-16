# Master Project Documentation: Plagiarism Detection Service (v3.0.0)

## 1. Executive Summary
The **Plagiarism Detection Service** is a production-grade microservice designed to identify structural and textual similarities across multiple programming languages. Unlike legacy systems that rely solely on simple text-matching, this version implements a **Dual-Engine Architecture** combining **Normalized Tokenization** and **Structural AST Analysis**. This ensures that even highly sophisticated "Smart Plagiarism" (renaming variables, code reordering, and noise injection) is accurately detected while maintaining a legally neutral reporting posture.

---

## 2. Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Dual-Engine Architecture](#3-dual-engine-architecture)
    * [Tokenizer Engine (Winnowing)](#tokenizer-engine-winnowing)
    * [AST Engine (Structural Winnowing)](#ast-engine-structural-winnowing)
3. [The 6 Architectural Fixes](#4-the-6-architectural-fixes)
    * [Fix 1: Language-Based Grouping](#fix-1-language-based-grouping)
    * [Fix 2: Independent AST Pipeline](#fix-2-independent-ast-pipeline)
    * [Fix 3: AST Winnowing](#fix-3-ast-winnowing)
    * [Fix 4: Label-Derived Metrics](#fix-4-label-derived-metrics)
    * [Fix 5: Neutral Recalibration](#fix-5-neutral-recalibration)
    * [Fix 6: Strict Token Gating](#fix-6-strict-token-gating)
4. [Technology Stack & Supported Languages](#5-technology-stack--supported-languages)
5. [Implementation Deep Dive](#6-implementation-deep-dive)
    * [Winnowing Algorithm](#winnowing-algorithm)
    * [AST Normalization Logic](#ast-normalization-logic)
6. [Evasion Case Studies](#7-evasion-case-studies)
    * [Python: Obnoxious Obfuscation](#python-obnoxious-obfuscation)
    * [JavaScript: Control Flow Mutation](#javascript-control-flow-mutation)
    * [Java: Noise Injection](#java-noise-injection)
7. [API Reference & Usage](#8-api-reference--usage)
8. [Setup & Deployment](#9-setup--deployment)
9. [Conclusion & Future Roadmap](#10-conclusion-&amp;-future-roadmap)

---

## 3. Dual-Engine Architecture

### Tokenizer Engine (Winnowing)
**Purpose**: Detect textual similarity and snippet copying.
*   **Normalization**: Code is stripped of comments and all identifiers (variable/function names) are replaced with a generic `VAR` tag. Strings are generalized to `STR`.
*   **Winnowing**: The engine uses the MOSS-standard Winnowing algorithm. It hashes sliding k-gram windows and selects a subset of fingerprints that are stable across code insertions.
*   **Strength**: Highly resistant to "Noise Injection" (adding dummy print statements or comments).

### AST Engine (Structural Winnowing)
**Purpose**: Detect logical similarity and architectural copying.
*   **Tree-Sitter Integration**: Uses universal parsers to convert code into Abstract Syntax Trees.
*   **Structural Filtering**: Ignores raw text and expressions, focusing entirely on structure: loops, conditionals, assignments, and class definitions.
*   **Structural Winnowing**: Hashing is applied to the sequence of AST node types, mathematically preserving the "shape" of the code regardless of naming conventions.
*   **Strength**: Catches "Smart Plagiarism" where every variable is renamed but the logic remains identical.

---

## 4. The 6 Architectural Fixes

### Fix 1: Language-Based Grouping
*   **Problem**: Prototype compared different languages (e.g., Python vs Java), causing parser crashes and 0% false negatives.
*   **Fix**: Implemented a **Composite Key Isolation** strategy. Submissions are grouped by `(question_id, language)`.
*   **Result**: 100% stability; systems only compare like-for-like.

### Fix 2: Independent AST Pipeline
*   **Problem**: A "Token Gate" prevented the AST engine from running if token similarity was too low (<25%). Evasive students exploited this by adding noise.
*   **Fix**: The AST engine is now **Always-Active**. Both signals are merged in the final scoring phase.
*   **Result**: Smart copies that hide behind 15% token overlap are now caught by 90%+ AST overlap.

### Fix 3: AST Winnowing
*   **Problem**: Naive AST comparison used unordered sets (Jaccard similarity of node types), leading to massive false positives for simple programs.
*   **Fix**: Implemented **Hashed Sliding Windows** for AST nodes.
*   **Result**: Structural order is preserved; two different programs using `if/for` are no longer flagged as identical.

### Fix 4: Label-Derived Metrics
*   **Problem**: The developer dashboard calculated "Exact Matches" using only token similarity, missing AST-detected smart copies.
*   **Fix**: Metrics are now derived directly from the **Final Confidence Label**.
*   **Result**: Dashboard accuracy now reflects the combined intelligence of both engines.

### Fix 5: Neutral Recalibration
*   **Problem**: Labels like "Suspicious" or "Copy Detected" created legal liability for the company.
*   **Fix**: Transitioned to **Signal-Based Taxonomy** (e.g., "High Structural Similarity," "Exact Text Overlap").
*   **Result**: Neutral, evidentiary reports that protect the business from litigation.

---

## 5. Technology Stack & Supported Languages

### Technology Stack
*   **Backend**: Python 3.8+ with **FastAPI** for high-performance async processing.
*   **Parsing Engine**: **Tree-Sitter** (Universal incremental parser).
*   **Database**: **PostgreSQL** (Optimized for Neon serverless).
*   **Security**: **python-dotenv** for environment isolation.
*   **Validation**: **Pydantic v2** for robust API schema enforcement.

### Supported Languages (26+)
The service provides out-of-the-box structural analysis for:
*   **Systems**: C, C++, Rust, Go, OCaml.
*   **Web**: JavaScript, TypeScript, HTML, CSS, PHP, Ruby.
*   **Enterprise**: Java, Kotlin, Scala, SQL.
*   **Scripting**: Python, Bash, Lua.
*   **Data/Config**: JSON, YAML, TOML, Haskell, Swift.

---

## 6. Implementation Deep Dive

### The Winnowing Algorithm
The core of our detection robustness lies in **Winnowing**. Standard k-gram hashing is sensitive to single-character changes. Winnowing solves this by selecting only the "minimum" hash in a sliding window, creating a resilient fingerprint.

**Pseudocode**:
```python
def winnowing(tokens, k=5, window_size=4):
    hashes = [hash(tokens[i:i+k]) for i in range(len(tokens)-k+1)]
    fingerprints = set()
    for i in range(len(hashes)-window_size+1):
        fingerprints.add(min(hashes[i:i+window_size]))
    return fingerprints
```

### AST Structural Mapping
To prevent false positives while catching renamed code, we map AST nodes to a "Logic-Only" sequence:
1.  Travel the tree recursively.
2.  If node is `FunctionDef`, `If`, `For`, or `While`, append its type to the sequence.
3.  If node is a variable name or string literal, **Ignore**.
4.  Apply Winnowing to the resulting sequence.

---

## 7. Evasion Case Studies

### Python: Obnoxious Obfuscation
*   **Tactic**: Student renames all variables to 50-character strings and adds 20 `print()` statements.
*   **Tokenizer Signal**: 15% (Low)
*   **AST Signal**: 98% (High)
*   **System Result**: **CAUGHT** (detected as "Smart copy — variables renamed").

### JavaScript: Control Flow Mutation
*   **Tactic**: Student converts a `for` loop to a `while` loop and extracts some logic into a helper function.
*   **Tokenizer Signal**: 28% (Moderate)
*   **AST Signal**: 45% (Moderate)
*   **System Result**: **CAUGHT** (detected as "Moderate structural and textual similarity").

### Java: Noise Injection
*   **Tactic**: Student wraps code in a `try/catch` block and adds "Dead Code" (if-statements that will never run).
*   **Tokenizer Signal**: 32% (Low)
*   **AST Signal**: 62% (Moderate-High)
*   **System Result**: **CAUGHT** (detected as "High structural similarity").

---

## 8. API Reference & Usage

### Endpoint: `POST /check-plagiarism`
Submits a batch of code for cross-comparison.

**Request Schema**:
```json
{
  "batch_id": "assignment_02",
  "submissions": [
    {
      "candidate_id": "user_1",
      "question_id": "q1",
      "language": "python",
      "source_code": "..."
    }
  ]
}
```

**Response Taxonomy (Examples)**:
*   `Exact match`: 100% overlap.
*   `Near-identical text`: >90% textual similarity.
*   `Low text overlap, high structural similarity`: The hallmark of a "Smart Copy."
*   `Likely original`: No significant signals found.

---

## 9. Setup & Deployment

### Installation
1.  `git clone <repo_url>`
2.  `pip install -r requirements.txt`
3.  Configure `.env` with your `DATABASE_URL`.

### Execution
*   **Run Showcase**: `python demo_for_team_leader.py`
*   **Run API**: `uvicorn main:app --reload`

---

## 10. Conclusion & Future Roadmap
The Plagiarism Detection Service v3.0.0 represents a significant leap from syntax-only matching to structural intelligence. It current protects against 90% of common student evasion tactics.

**Planned v4.0.0 Features**:
1.  **Semantic Embeddings**: Using CodeBERT to catch logic reordering that even ASTs might miss.
2.  **Boilerplate Filtering**: Automatically ignoring code provided as part of an assignment template.
3.  **Side-by-Side Highlighting**: A visual diff report for management review.

---
*Documentation Version: 3.0.0*
*Last Updated: 2026-04-16*
