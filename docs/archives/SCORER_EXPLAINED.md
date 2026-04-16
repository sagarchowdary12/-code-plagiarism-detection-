# Scorer Deep Dive: How It Works

## Overview
The scorer is the orchestration engine that ties everything together. It takes submissions, runs both detection engines (token-based and AST-based), calculates similarity scores, assigns risk labels, and returns structured results. This is the "brain" of the plagiarism detection system.

---

## The Complete Pipeline

```
Submissions → Group by Question → Compare All Pairs → Token Score → AST Score → Label → Filter → Sort → Return Results
```

Let's walk through each step with examples.

---

## Step 1: Input - Submissions

The scorer receives a list of submissions:

```python
submissions = [
    {
        "candidate_id": "alice",
        "question_id": "q1_sum",
        "language": "python",
        "source_code": "def add(a, b):\n    return a + b"
    },
    {
        "candidate_id": "bob",
        "question_id": "q1_sum",
        "language": "python",
        "source_code": "def sum(x, y):\n    return x + y"
    },
    {
        "candidate_id": "charlie",
        "question_id": "q2_max",
        "language": "java",
        "source_code": "public int findMax(int[] arr) { ... }"
    }
]
```

---

## Step 2: Group by Question

**Function**: `run_plagiarism_check()`

**Purpose**: Group submissions by question_id so we only compare submissions for the same question.

**Why?** Students solving different questions will have different code - that's not plagiarism!

```python
def run_plagiarism_check(all_submissions: list) -> list:
    # Group submissions by question_id
    groups = defaultdict(list)
    for submission in all_submissions:
        groups[submission["question_id"]].append(submission)
    
    # Process each group separately
    all_results = []
    for question_id, group in sorted(groups.items()):
        if len(group) < 2:
            continue  # Need at least 2 submissions to compare
        
        results = compare_all_submissions(group)
        all_results.extend(results)
    
    return all_results
```

**Example**:
```python
# Input: 3 submissions
[alice_q1, bob_q1, charlie_q2]

# After grouping
{
    "q1_sum": [alice_q1, bob_q1],      # 2 submissions → 1 pair
    "q2_max": [charlie_q2]              # 1 submission → skip
}
```

---

## Step 3: Generate All Pairs

**Function**: `compare_all_submissions()`

**Purpose**: Compare every possible pair of submissions for a question.

**Formula**: For n submissions, we have n×(n-1)/2 pairs

**Example**:
```python
# 2 submissions → 1 pair
[alice, bob] → [(alice, bob)]

# 3 submissions → 3 pairs
[alice, bob, charlie] → [(alice, bob), (alice, charlie), (bob, charlie)]

# 10 submissions → 45 pairs
# 50 submissions → 1,225 pairs
# 100 submissions → 4,950 pairs
```

**Implementation**:
```python
from itertools import combinations

def compare_all_submissions(submissions: list) -> list:
    results = []
    
    # Generate all pairs
    for sub_a, sub_b in combinations(submissions, 2):
        # Skip if same candidate (shouldn't happen, but safety check)
        if sub_a["candidate_id"] == sub_b["candidate_id"]:
            continue
        
        # Compare this pair
        result = compare_pair(sub_a, sub_b)
        if result:
            results.append(result)
    
    return results
```

---

## Step 4: Filter Short Code

**Purpose**: Skip code that's too short to meaningfully compare.

**Threshold**: Minimum 5 tokens

**Why?** Very short code like `return a + b` is too generic. Many students will write identical trivial code without copying.

```python
MIN_TOKEN_LENGTH = 5

def get_token_count(source_code: str) -> int:
    cleaned = clean_code(source_code)
    return len(cleaned.split())

# In compare_all_submissions:
if get_token_count(code_a) < MIN_TOKEN_LENGTH:
    continue  # Skip this pair
if get_token_count(code_b) < MIN_TOKEN_LENGTH:
    continue  # Skip this pair
```

**Example**:
```python
# Too short - skip
"return a + b"  # 4 tokens

# Long enough - compare
"def add(a, b):\n    return a + b"  # 8 tokens
```

---

## Step 5: Calculate Token Similarity

**Function**: `token_similarity_percent()`

**Purpose**: Get similarity score from token-based engine (with winnowing).

```python
from detection.tokenizer import token_similarity_percent

tok_pct = token_similarity_percent(code_a, code_b, language)
```

**Example**:
```python
# Code A
def add(a, b):
    return a + b

# Code B (renamed)
def sum(x, y):
    return x + y

# Token similarity
tok_pct = 100.0  # Normalization catches renamed variables
```

---

## Step 6: Calculate AST Similarity

**Function**: `ast_similarity_percent()`

**Purpose**: Get similarity score from AST-based engine.

**Optimization**: If token similarity is already ≥95%, skip AST parsing (it's expensive) and just use the token score.

**Why?** If tokens are 95%+ similar, AST will also be very high. No need to waste CPU.

```python
from detection.ast_comparator import ast_similarity_percent

# Short-circuit optimization
if tok_pct >= 95:
    ast_pct = tok_pct  # Assume AST is also high
else:
    ast_pct = ast_similarity_percent(code_a, code_b, language)
```

**Example**:
```python
# Exact copy
tok_pct = 100.0
ast_pct = 100.0  # Just use token score, skip AST parsing

# Different code
tok_pct = 57.14
ast_pct = 100.0  # Need to calculate AST (might be high despite low token)
```

---

## Step 7: Filter by Minimum Threshold

**Purpose**: Only report pairs with token similarity ≥ 25%.

**Threshold**: `MINIMUM_REPORT_PERCENT = 25.0`

**Why?** Below 25%, the code is too different to be plagiarism. This filters out noise and reduces false positives.

```python
MINIMUM_REPORT_PERCENT = 25.0

# In compare_all_submissions:
if tok_pct < MINIMUM_REPORT_PERCENT:
    continue  # Don't report this pair
```

**Example**:
```python
# Report these
tok_pct = 100.0  # Exact copy
tok_pct = 75.0   # Highly similar
tok_pct = 50.0   # Moderately similar
tok_pct = 25.0   # Slightly similar (just at threshold)

# Don't report these
tok_pct = 24.9   # Too different
tok_pct = 10.0   # Completely different
tok_pct = 0.0    # No similarity
```

---

## Step 8: Assign Risk Label

**Function**: `get_label()`

**Purpose**: Convert numeric scores into human-readable risk labels.

This is the MOST IMPORTANT logic in the entire system!

### The Label Engine

```python
def get_label(token_pct: float, ast_pct: float) -> str:
    # Rule 1: Exactly identical
    if token_pct == 100 and ast_pct == 100:
        return "Exact copy"
    
    # Rule 2: Token very high (90%+)
    if token_pct >= 90:
        return "Almost identical"
    
    # Rule 3: Token high (75-89%)
    if token_pct >= 75:
        return "Highly similar"
    
    # Rule 4: SMART PLAGIARISM - Low token but very high AST
    # This is the WORST kind - student rewrote surface but kept exact logic
    if token_pct < 75 and ast_pct >= 95:
        return "Smart copy — logic identical"
    
    # Rule 5: Suspicious - Both moderate-high
    if token_pct >= 50 and ast_pct >= 75:
        return "Suspicious — high structural overlap"
    
    # Rule 6: Token moderate (50%+)
    if token_pct >= 50:
        return "Moderately similar"
    
    # Rule 7: Token low but AST moderate
    if token_pct >= 25 and ast_pct >= 50:
        return "Slightly similar"
    
    # Rule 8: Below all thresholds
    return "Likely original"
```

### Label Decision Tree

```
                    Token = 100 & AST = 100?
                           /        \
                         Yes         No
                          |           |
                    "Exact copy"   Token ≥ 90?
                                    /        \
                                  Yes         No
                                   |           |
                          "Almost identical" Token ≥ 75?
                                              /        \
                                            Yes         No
                                             |           |
                                    "Highly similar"  Token < 75 & AST ≥ 95?
                                                        /              \
                                                      Yes               No
                                                       |                 |
                                          "Smart copy — logic identical" ...
```

### Examples:

```python
# Case 1: Exact copy
get_label(100.0, 100.0) → "Exact copy"

# Case 2: Tiny change
get_label(92.5, 95.0) → "Almost identical"

# Case 3: Renamed variables
get_label(100.0, 100.0) → "Exact copy"

# Case 4: Smart plagiarism (added dummy prints)
get_label(57.14, 100.0) → "Smart copy — logic identical"

# Case 5: Moderate similarity
get_label(55.0, 60.0) → "Moderately similar"

# Case 6: Low similarity
get_label(30.0, 45.0) → "Slightly similar"

# Case 7: Very different
get_label(15.0, 20.0) → "Likely original" (but won't be reported due to 25% threshold)
```

---

## Step 9: Create Result Object

**Purpose**: Package the comparison results into a structured format.

```python
result = {
    "candidate_a":          sub_a["candidate_id"],
    "candidate_b":          sub_b["candidate_id"],
    "question_id":          question_id,
    "language":             language,
    "token_similarity_pct": tok_pct,
    "ast_similarity_pct":   ast_pct,
    "label":                label,
}
```

**Example**:
```python
{
    "candidate_a": "alice",
    "candidate_b": "bob",
    "question_id": "q1_sum",
    "language": "python",
    "token_similarity_pct": 100.0,
    "ast_similarity_pct": 100.0,
    "label": "Exact copy"
}
```

---

## Step 10: Sort Results

**Purpose**: Show the most suspicious pairs first (highest token similarity).

```python
# Sort by token similarity - highest first
results.sort(key=lambda x: x["token_similarity_pct"], reverse=True)
```

**Why token, not AST?** Token similarity is more intuitive for humans. High token = obvious copy.

**Example**:
```python
# Before sorting
[
    {"candidate_a": "alice", "token_similarity_pct": 57.14},
    {"candidate_a": "bob", "token_similarity_pct": 100.0},
    {"candidate_a": "charlie", "token_similarity_pct": 75.0}
]

# After sorting
[
    {"candidate_a": "bob", "token_similarity_pct": 100.0},    # Worst case first
    {"candidate_a": "charlie", "token_similarity_pct": 75.0},
    {"candidate_a": "alice", "token_similarity_pct": 57.14}
]
```

---

## Complete Example: End-to-End

### Input: 3 Submissions for Same Question

```python
submissions = [
    {
        "candidate_id": "alice",
        "question_id": "q1_even",
        "language": "python",
        "source_code": """
def is_even(n):
    return n % 2 == 0
"""
    },
    {
        "candidate_id": "bob",
        "question_id": "q1_even",
        "language": "python",
        "source_code": """
def check_even(num):
    return num % 2 == 0
"""
    },
    {
        "candidate_id": "charlie",
        "question_id": "q1_even",
        "language": "python",
        "source_code": """
def is_even(n):
    print("Checking...")
    result = n % 2 == 0
    print(f"Result: {result}")
    return result
"""
    }
]
```

### Execution:

**Step 1: Group by Question**
```python
{
    "q1_even": [alice, bob, charlie]  # 3 submissions
}
```

**Step 2: Generate Pairs**
```python
Pairs to compare:
1. (alice, bob)
2. (alice, charlie)
3. (bob, charlie)

Total: 3 pairs
```

**Step 3: Compare Pair 1 (alice vs bob)**
```python
# Token similarity
# Both normalize to: "def VAR VAR return VAR % 2 == 0"
tok_pct = 100.0

# AST similarity
# Both have: Module, FunctionDef, Return, Compare, BinOp
ast_pct = 100.0

# Label
label = "Exact copy"

# Result
{
    "candidate_a": "alice",
    "candidate_b": "bob",
    "token_similarity_pct": 100.0,
    "ast_similarity_pct": 100.0,
    "label": "Exact copy"
}
```

**Step 4: Compare Pair 2 (alice vs charlie)**
```python
# Token similarity
# Alice: "def VAR VAR return VAR % 2 == 0"
# Charlie: "def VAR VAR VAR STR VAR = VAR % 2 == 0 VAR STR return VAR"
tok_pct = 57.14

# AST similarity
# Alice: Module, FunctionDef, Return, Compare, BinOp
# Charlie: Module, FunctionDef, Assign, Return, Compare, BinOp (Call nodes filtered)
ast_pct = 83.33

# Label
label = "Suspicious — high structural overlap"

# Result
{
    "candidate_a": "alice",
    "candidate_b": "charlie",
    "token_similarity_pct": 57.14,
    "ast_similarity_pct": 83.33,
    "label": "Suspicious — high structural overlap"
}
```

**Step 5: Compare Pair 3 (bob vs charlie)**
```python
# Similar to pair 2
tok_pct = 57.14
ast_pct = 83.33
label = "Suspicious — high structural overlap"
```

**Step 6: Sort Results**
```python
[
    {
        "candidate_a": "alice",
        "candidate_b": "bob",
        "token_similarity_pct": 100.0,  # Highest - show first
        "ast_similarity_pct": 100.0,
        "label": "Exact copy"
    },
    {
        "candidate_a": "alice",
        "candidate_b": "charlie",
        "token_similarity_pct": 57.14,
        "ast_similarity_pct": 83.33,
        "label": "Suspicious — high structural overlap"
    },
    {
        "candidate_a": "bob",
        "candidate_b": "charlie",
        "token_similarity_pct": 57.14,
        "ast_similarity_pct": 83.33,
        "label": "Suspicious — high structural overlap"
    }
]
```

### Final Output:

```
Checking q1_even — 3 submissions — 3 possible pairs
Pairs worth reporting: 3

Results:
1. alice vs bob: 100% token, 100% AST → "Exact copy"
2. alice vs charlie: 57% token, 83% AST → "Suspicious — high structural overlap"
3. bob vs charlie: 57% token, 83% AST → "Suspicious — high structural overlap"
```

---

## Key Parameters & Thresholds

### 1. Minimum Token Length
```python
MIN_TOKEN_LENGTH = 5
```
**Purpose**: Skip trivial code
**Example**: `return a + b` (4 tokens) is skipped

### 2. Minimum Report Threshold
```python
MINIMUM_REPORT_PERCENT = 25.0
```
**Purpose**: Filter out noise
**Example**: 24% similarity is not reported

### 3. Label Thresholds
```python
Exact copy:           token = 100 AND ast = 100
Almost identical:     token ≥ 90
Highly similar:       token ≥ 75
Smart copy:           token < 75 AND ast ≥ 95
Suspicious:           token ≥ 50 AND ast ≥ 75
Moderately similar:   token ≥ 50
Slightly similar:     token ≥ 25 AND ast ≥ 50
```

### 4. AST Short-Circuit Threshold
```python
AST_SHORTCUT_THRESHOLD = 95.0
```
**Purpose**: Skip expensive AST parsing if token is already very high
**Example**: If token = 98%, assume AST is also high

---

## Performance Optimizations

### 1. Early Filtering
```python
# Skip short code BEFORE comparing
if get_token_count(code_a) < MIN_TOKEN_LENGTH:
    continue
```
**Benefit**: Saves 2 engine calls per skipped pair

### 2. Threshold Filtering
```python
# Skip low similarity BEFORE AST
if tok_pct < MINIMUM_REPORT_PERCENT:
    continue
```
**Benefit**: Saves 1 AST call per filtered pair

### 3. AST Short-Circuit
```python
# Skip AST if token is already very high
if tok_pct >= 95:
    ast_pct = tok_pct
```
**Benefit**: Saves expensive AST parsing for obvious copies

### 4. Grouping by Question
```python
# Only compare submissions for same question
groups = defaultdict(list)
for sub in submissions:
    groups[sub["question_id"]].append(sub)
```
**Benefit**: Reduces unnecessary comparisons

### Performance Impact:

For 50 submissions per question:
- **Without optimizations**: 1,225 pairs × 2 engines = 2,450 engine calls
- **With optimizations**: ~1,000 token calls + ~500 AST calls = 1,500 total
- **Speedup**: ~40% faster

---

## Error Handling

### 1. Empty Submissions
```python
if not submissions:
    return []
```

### 2. Single Submission
```python
if len(group) < 2:
    continue  # Need at least 2 to compare
```

### 3. Same Candidate
```python
if sub_a["candidate_id"] == sub_b["candidate_id"]:
    continue  # Don't compare submission to itself
```

### 4. Parsing Failures
```python
# If AST parsing fails, it returns 0.0
# Token-based still works, so we can still report
```

---

## Integration with API

The scorer is called by the FastAPI endpoint:

```python
@app.post("/check-plagiarism")
def check_plagiarism(request: PlagiarismRequest):
    # 1. Fetch submissions from database
    submissions = fetch_submissions_from_db(request.batch_id)
    
    # 2. Run plagiarism check
    results = run_plagiarism_check(submissions)
    
    # 3. Generate summary statistics
    summary = generate_summary(results)
    
    # 4. Return structured response
    return PlagiarismResponse(
        batch_id=request.batch_id,
        total_submissions=len(submissions),
        total_pairs_checked=len(results),
        summary_by_question=summary,
        results=results
    )
```

---

## Output Format

### Individual Result:
```python
{
    "candidate_a": "alice",
    "candidate_b": "bob",
    "question_id": "q1_sum",
    "language": "python",
    "token_similarity_pct": 100.0,
    "ast_similarity_pct": 100.0,
    "label": "Exact copy"
}
```

### Complete Response:
```python
{
    "batch_id": "batch_001",
    "total_submissions": 50,
    "total_pairs_checked": 1225,
    "summary_by_question": [
        {
            "question_id": "q1_sum",
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
            "candidate_a": "alice",
            "candidate_b": "bob",
            "token_similarity_pct": 100.0,
            "ast_similarity_pct": 100.0,
            "label": "Exact copy"
        },
        ...
    ]
}
```

---

## Label Interpretation Guide

### For Instructors:

| Label | Risk | Action |
|-------|------|--------|
| **Exact copy** | 🔴 HIGH | Investigate immediately - likely plagiarism |
| **Almost identical** | 🔴 HIGH | Investigate - very suspicious |
| **Highly similar** | 🟡 MEDIUM | Review - probably plagiarism |
| **Smart copy — logic identical** | 🔴 HIGH | Investigate - sophisticated cheating |
| **Suspicious — high structural overlap** | 🟡 MEDIUM | Review - may be plagiarism |
| **Moderately similar** | 🟢 LOW | Monitor - could be coincidence |
| **Slightly similar** | 🟢 LOW | Likely original - common patterns |

### Decision Matrix:

```
Token High + AST High = Definite plagiarism
Token High + AST Low  = Surface copy (less serious)
Token Low  + AST High = Smart plagiarism (WORST!)
Token Low  + AST Low  = Likely original
```

---

## Advantages of This Scoring System

1. **Dual-engine**: Combines token and AST for robust detection
2. **Graduated labels**: 7 risk levels instead of binary yes/no
3. **Optimized**: Early filtering and short-circuits for speed
4. **Flexible**: Configurable thresholds
5. **Actionable**: Clear labels guide instructor decisions

---

## Limitations

1. **Threshold tuning**: The 25%, 50%, 75%, 90%, 95% thresholds are somewhat arbitrary. May need adjustment based on real-world data.

2. **No semantic analysis**: Can't detect if two different algorithms solve the problem the same way (e.g., bubble sort vs selection sort).

3. **Generic code**: Very simple problems (like `return a + b`) will show high similarity even without plagiarism.

4. **No cross-question comparison**: Only compares submissions for the same question. Can't detect if student copied from a different question.

5. **No external source detection**: Only compares within the batch. Can't detect copying from online sources (would need a reference database).

---

## Future Improvements

### 1. Dynamic Thresholds
Adjust thresholds based on problem complexity:
```python
# Simple problem (high expected similarity)
if problem_complexity == "simple":
    MINIMUM_REPORT_PERCENT = 50.0  # Raise threshold

# Complex problem (low expected similarity)
if problem_complexity == "complex":
    MINIMUM_REPORT_PERCENT = 15.0  # Lower threshold
```

### 2. Confidence Scores
Add confidence to labels:
```python
{
    "label": "Exact copy",
    "confidence": 0.95  # 95% confident
}
```

### 3. Explanation Generation
Provide reasons for the label:
```python
{
    "label": "Smart copy — logic identical",
    "explanation": "Token similarity is low (57%) due to renamed variables and added print statements, but AST similarity is 100%, indicating identical logic structure."
}
```

### 4. Clustering
Group similar submissions together:
```python
{
    "cluster_1": ["alice", "bob", "charlie"],  # All copied from same source
    "cluster_2": ["david", "eve"]              # Different source
}
```

---

## Conclusion

The scorer is the orchestration layer that:
- **Groups submissions** by question
- **Generates all pairs** to compare
- **Filters** short code and low similarity
- **Runs both engines** (token + AST)
- **Assigns risk labels** based on dual scores
- **Sorts and returns** structured results

The label engine is particularly important - it translates numeric scores into actionable risk levels that instructors can understand and act upon.

Combined with the token-based and AST-based engines, this creates a comprehensive plagiarism detection system that catches nearly all forms of code plagiarism while minimizing false positives.

---

## References

1. **Combinatorics**: Pair generation using combinations
2. **Jaccard Similarity**: Standard set similarity metric
3. **MOSS**: Stanford's plagiarism detection system (inspiration for thresholds)
4. **Information Retrieval**: Threshold-based filtering techniques

