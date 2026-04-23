 # Tokenizer Deep Dive: How It Works

## Overview
The tokenizer is the first engine in our dual-detection system. It converts source code into normalized tokens and uses the **Winnowing algorithm** to create fingerprints that can detect copied code even when students try to hide it.

---

## The Complete Pipeline

```
Raw Code → Clean → Remove Comments → Normalize → Tokenize → Winnowing → Fingerprint → Compare
```

Let's walk through each step with examples.

---

## Step 1: Clean Code from Database

**Function**: `clean_code_from_db()`

**Purpose**: Database stores code with escaped characters like `\n` and `\t`. We need to convert these back to actual newlines and tabs.

**Example**:
```python
# From database
"def add(a, b):\\n    return a + b"

# After cleaning 
"def add(a, b):
    return a + b"
```

**Implementation**:
```python
def clean_code_from_db(source_code: str) -> str:
    try:
        # Try unicode escape decoding
        cleaned = codecs.decode(source_code, 'unicode_escape')
        return cleaned
    except Exception:
        # Fallback: manual replacement
        cleaned = source_code.replace('\\n', '\n')
        cleaned = cleaned.replace('\\t', '\t')
        cleaned = cleaned.replace('\\r', '\r')
        return cleaned
```

---
## Step 2: Remove Comments & Strict Token Gating (Fix 6)

**Function**: `remove_comments_universally()`

**Purpose**: Comments are not just noise—they can be used to bypass plagiarism detection systems. We remove them completely to ensure the system analyzes only the actual logic.

**Fix 6: Strict Token Gating**: Previously, students could "inject noise" by adding thousands of lines of comments. This would trick the system into thinking a submission was a large project, effectively "diluting" the copied code percentage. 

In our final architecture, we perform **Strict Gating**. We strip ALL comments **before** calculating the token length or any similarity metrics. This ensures that a 100-line copied file cannot hide inside a 2000-line file of junk comments.

**Why Tree-Sitter for Fix 6?**
- Regex-based removal is unreliable.
- Tree-sitter guarantees that only actual `comment` nodes are removed.
- Allows for accurate "net code" measurement.

**How it works**:
1. Parse code using Tree-sitter (lightweight parsing, just to find comments)
2. Find all nodes with type containing "comment"
3. Delete those byte ranges from the source
4. Return cleaned code

**Important**: This is NOT the same as AST analysis! Here we're only using Tree-sitter's parser to identify and remove comments. The actual AST structural analysis happens in a separate engine (`ast_comparator.py`).

**Example**:
```python
# Original Python code
def add(a, b):
    # This adds two numbers
    result = a + b  # Store result
    return result

# After comment removal
def add(a, b):
    result = a + b
    return result
```

**Implementation**:
```python
def remove_comments_universally(code: str, language: str) -> str:
    lang_module = LANGUAGE_REGISTRY.get(language.lower())
    
    if not lang_module:
        # Fallback to simple regex
        code = re.sub(r'//.*|#.*', '', code)
        return code
    
    try:
        # Parse with Tree-sitter
        ts_lang = Language(lang_module.language())
        parser = Parser(ts_lang)
        tree = parser.parse(bytes(code, "utf8"))
        
        # Find all comment nodes
        comments = []
        def find_comments(node):
            if "comment" in node.type:
                comments.append((node.start_byte, node.end_byte))
            for child in node.children:
                find_comments(child)
        
        find_comments(tree.root_node)
        
        # Delete comments (in reverse order to preserve byte positions)
        code_bytes = bytearray(code, "utf8")
        for start, end in sorted(comments, reverse=True):
            del code_bytes[start:end]
        
        return code_bytes.decode("utf8", errors="ignore")
    except Exception as e:
        print(f"Tree-Sitter failed: {e}")
        return code
```

---

## Step 3: Normalize Code

**Function**: `normalize_code()`

**Purpose**: Make code look the same regardless of variable names, string contents, or formatting. This is the KEY to catching plagiarism.

**Normalization Steps**:

### 3.1 Strip String Literals
Replace all string contents with `STR` placeholder.

**Why?** Students might change string messages but keep the logic identical.

```python
# Before
print("Hello World")
print("Starting calculation")

# After
print(STR)
print(STR)
```

### 3.2 Remove Whitespace
Join all lines, strip extra spaces.

```python
# Before
def add(a, b):
    result = a + b
    return result

# After
def add(a, b): result = a + b return result
```

### 3.3 Replace Identifiers with VAR
This is the MOST IMPORTANT step. Replace all variable/function names with `VAR`, but keep keywords.

**Keywords preserved**: `if`, `else`, `for`, `while`, `return`, `def`, `class`, etc.

**Example**:
```python
# Original
def calculate_sum(num1, num2):
    total = num1 + num2
    return total

# After normalization
def VAR(VAR, VAR): VAR = VAR + VAR return VAR
```

**Why this works**:
- Student A: `def find_max(arr)` → `def VAR(VAR)`
- Student B: `def get_highest(items)` → `def VAR(VAR)`
- Both become identical after normalization!

### 3.4 Strip Punctuation
Remove brackets, semicolons, colons so only meaningful tokens remain.

```python
# Before
def VAR(VAR, VAR): VAR = VAR + VAR return VAR

# After
def VAR VAR VAR VAR = VAR + VAR return VAR
```

**Full Implementation**:
```python
def normalize_code(source_code: str, language: str = 'python') -> str:
    code = clean_code_from_db(source_code)
    code = remove_comments_universally(code, language)
    
    # Strip string literals
    code = re.sub(r'"[^"]*"', 'STR', code)
    code = re.sub(r"'[^']*'", 'STR', code)
    
    # Remove whitespace
    lines = [line.strip() for line in code.splitlines() if line.strip()]
    code = ' '.join(lines)
    
    # Replace identifiers
    def replace_identifier(match):
        word = match.group(0)
        if word in UNIVERSAL_KEYWORDS:
            return word  # Keep keywords
        return 'VAR'    # Replace everything else
    
    code = re.sub(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', replace_identifier, code)
    
    # Strip punctuation
    code = re.sub(r'[(){}\[\];,.:"\']', ' ', code)
    
    return code
```

---

## Step 4: Tokenize

**Function**: `tokenize()`

**Purpose**: Split normalized code into individual tokens (words).

**Example**:
```python
# Normalized code
"def VAR VAR VAR VAR = VAR + VAR return VAR"

# Tokens
['def', 'VAR', 'VAR', 'VAR', 'VAR', '=', 'VAR', '+', 'VAR', 'return', 'VAR']
```

**Implementation**:
```python
def tokenize(source_code: str, language: str = 'python') -> List[str]:
    normalized = normalize_code(source_code, language)
    # Filter out empty strings
    return [t for t in normalized.split() if t]
```

---

## Step 5: Winnowing Algorithm (The Magic!)

**Function**: `winnowing()`

**Purpose**: Create a "fingerprint" of the code that is:
- Resistant to small insertions (dummy print statements)
- Resistant to reordering
- Guarantees detection of matches above a threshold

### How Winnowing Works

**Step 5.1: Create K-grams**

A k-gram is a sequence of k consecutive tokens. We use k=12 in production, but we will use k=5 here for simplicity.

**Example**:
```python
Tokens: ['def', 'VAR', 'VAR', 'VAR', '=', 'VAR', '+', 'VAR', 'return', 'VAR']

K-grams (k=5):
1. ('def', 'VAR', 'VAR', 'VAR', '=')
2. ('VAR', 'VAR', 'VAR', '=', 'VAR')
3. ('VAR', 'VAR', '=', 'VAR', '+')
4. ('VAR', '=', 'VAR', '+', 'VAR')
5. ('=', 'VAR', '+', 'VAR', 'return')
6. ('VAR', '+', 'VAR', 'return', 'VAR')
```

**Step 5.2: Hash Each K-gram**

Convert each k-gram to a hash number using MD5.

```python
def hash_kgram(kgram: tuple) -> int:
    kgram_str = ' '.join(kgram)
    return int(hashlib.md5(kgram_str.encode()).hexdigest(), 16)
```

**Example**:
```python
('def', 'VAR', 'VAR', 'VAR', '=') → 123456789012345678901234567890
('VAR', 'VAR', 'VAR', '=', 'VAR') → 987654321098765432109876543210
...
```

**Step 5.3: Sliding Window - Select Minimum Hashes**

Use a sliding window of size 4. In each window, select the MINIMUM hash.

**Why minimum?** This guarantees that if two documents share a substring of length ≥ k+window-1, at least one hash will match.

**Example**:
```python
Hashes: [h1, h2, h3, h4, h5, h6, h7, h8]

Window 1: [h1, h2, h3, h4] → select min(h1, h2, h3, h4) = h2
Window 2: [h2, h3, h4, h5] → select min(h2, h3, h4, h5) = h2
Window 3: [h3, h4, h5, h6] → select min(h3, h4, h5, h6) = h3
Window 4: [h4, h5, h6, h7] → select min(h4, h5, h6, h7) = h5
Window 5: [h5, h6, h7, h8] → select min(h5, h6, h7, h8) = h5

Fingerprint: {h2, h3, h5}
```

**Full Implementation**:
```python
def winnowing(tokens: List[str], k: int = 12, window_size: int = 4) -> set:
    if len(tokens) < k:
        return set()
    
    # Step 1: Create k-grams
    hashes = []
    for i in range(len(tokens) - k + 1):
        kgram = tuple(tokens[i:i+k])
        hashes.append(hash_kgram(kgram))
    
    # Step 2: Sliding window - select minimums
    fingerprints = set()
    for i in range(len(hashes) - window_size + 1):
        window = hashes[i:i+window_size]
        fingerprints.add(min(window))
    
    return fingerprints
```

---

## Step 6: Compare Fingerprints

**Function**: `token_similarity_percent()`

**Purpose**: Compare two code fingerprints using Jaccard similarity.

**Jaccard Similarity Formula**:
```
similarity = |A ∩ B| / |A ∪ B|
```

Where:
- A ∩ B = intersection (common fingerprints)
- A ∪ B = union (all unique fingerprints)

**Example**:
```python
Code A fingerprints: {h1, h2, h3, h4, h5}
Code B fingerprints: {h2, h3, h4, h6, h7}

Intersection: {h2, h3, h4} → 3 elements
Union: {h1, h2, h3, h4, h5, h6, h7} → 7 elements

Similarity = 3/7 = 42.86%
```

**Implementation**:
```python
def token_similarity_percent(code_a: str, code_b: str, language: str = 'python') -> float:
    # Tokenize both codes
    tokens_a = tokenize(code_a, language)
    tokens_b = tokenize(code_b, language)
    
    if not tokens_a or not tokens_b:
        return 0.0
    
    # Create fingerprints using winnowing
    fingerprint_a = winnowing(tokens_a)
    fingerprint_b = winnowing(tokens_b)
    
    # Calculate Jaccard similarity
    intersection = fingerprint_a & fingerprint_b
    union = fingerprint_a | fingerprint_b
    
    if not union:
        return 0.0
    
    score = (len(intersection) / len(union)) * 100
    return round(score, 2)
```

---

## Why Winnowing is Better Than Simple Text Comparison

### Problem 1: Dummy Code Insertion

**Simple text comparison fails**:
```python
# Student A (original)
def find_max(arr):
    max_val = arr[0]
    for num in arr:
        if num > max_val:
            max_val = num
    return max_val

# Student B (added dummy prints)
def find_max(arr):
    print("Starting...")
    max_val = arr[0]
    print("Initialized")
    for num in arr:
        print("Checking...")
        if num > max_val:
            max_val = num
    print("Done")
    return max_val

# Simple text comparison: ~60% match (lots of different lines)
# Winnowing: ~85% match (core logic fingerprints still match)
```

**Why winnowing works**: The dummy prints create new k-grams, but the core logic k-grams remain unchanged. The sliding window still selects many of the same minimum hashes.

### Problem 2: Variable Renaming

**Simple text comparison fails**:
```python
# Student A
def find_max(arr):
    max_val = arr[0]
    return max_val

# Student B
def get_highest(items):
    highest = items[0]
    return highest

# Simple text comparison: ~30% match (different variable names)
# After normalization + winnowing: 100% match
```

**Why normalization works**: Both become `def VAR(VAR): VAR = VAR[0] return VAR` after normalization.

### Problem 3: Reordering

**Winnowing is somewhat resistant**:
```python
# Student A
def process(x):
    a = x + 1
    b = x * 2
    return a + b

# Student B (reordered)
def process(x):
    b = x * 2
    a = x + 1
    return a + b

# Winnowing: ~70% match (some k-grams still match)
```

---

## Complete Example: End-to-End

Let's trace two submissions through the entire pipeline:

### Student A's Code:
```python
def calculate_sum(num1, num2):
    # Add two numbers
    result = num1 + num2
    return result
```

### Student B's Code (copied with changes):
```python
def add_values(a, b):
    # Different comment
    total = a + b
    return total
```

### Pipeline Execution:

**Step 1: Clean** (no escaped chars, so no change)

**Step 2: Remove Comments**
```python
# Student A
def calculate_sum(num1, num2):
    result = num1 + num2
    return result

# Student B
def add_values(a, b):
    total = a + b
    return total
```

**Step 3: Normalize**
```python
# Both become
def VAR VAR VAR VAR = VAR + VAR return VAR
```

**Step 4: Tokenize**
```python
# Both become
['def', 'VAR', 'VAR', 'VAR', 'VAR', '=', 'VAR', '+', 'VAR', 'return', 'VAR']
```

**Step 5: Winnowing (k=5, window=4) (Note: Production uses k=12)**
```python
# K-grams (same for both)
1. ('def', 'VAR', 'VAR', 'VAR', 'VAR')
2. ('VAR', 'VAR', 'VAR', 'VAR', '=')
3. ('VAR', 'VAR', 'VAR', '=', 'VAR')
4. ('VAR', 'VAR', '=', 'VAR', '+')
5. ('VAR', '=', 'VAR', '+', 'VAR')
6. ('=', 'VAR', '+', 'VAR', 'return')
7. ('+', 'VAR', 'return', 'VAR')

# Hashes (same for both)
h1, h2, h3, h4, h5, h6, h7

# Fingerprints (same for both)
{h1, h3, h5, h7}  (example - actual values depend on min selection)
```

**Step 6: Compare**
```python
Fingerprint A: {h1, h3, h5, h7}
Fingerprint B: {h1, h3, h5, h7}

Intersection: 4
Union: 4

Similarity: 4/4 = 100%
```

**Result**: 100% token similarity → Flagged as "Exact match"

---

## Key Parameters

### K-gram Size (k=12)
- **Too small (k=5)**: Too many false positives on generic loop structures
- **Too large (k=20)**: Misses short copied segments
- **k=12**: Good balance for fierce structural uniqueness

### Window Size (window=4)
- **Too small (window=2)**: Too many fingerprints, slow comparison
- **Too large (window=10)**: Might miss matches
- **window=4**: Optimal for most code

### Minimum Token Length (5 tokens)
- Filters out trivial code like `return a + b`
- Prevents false positives on generic patterns

### Minimum Report Threshold (25%)
- Only report pairs with ≥25% similarity
- Filters out noise (common boilerplate code)

---

## Tools & Libraries Used

### 1. Tree-Sitter
**Purpose**: Production-grade code parsing for 26+ languages

**Why not regex?**
- Regex fails on nested structures, strings containing comment markers, etc.
- Tree-sitter understands code syntax perfectly

**Languages supported**:
Python, Java, JavaScript, TypeScript, C, C++, Rust, Go, PHP, Ruby, Swift, Kotlin, Scala, Haskell, Lua, Bash, HTML, CSS, JSON, YAML, TOML, SQL, OCaml

**Installation**:
```bash
pip install tree-sitter
pip install tree-sitter-python
pip install tree-sitter-java
# ... etc for each language
```

### 2. Hashlib (MD5)
**Purpose**: Hash k-grams into fixed-size integers

**Why MD5?**
- Fast (not used for security, just fingerprinting)
- Produces uniform distribution
- 128-bit hash → very low collision probability

### 3. Codecs
**Purpose**: Decode escaped characters from database

**Why needed?**
- Database stores `\n` as literal backslash-n
- Need to convert to actual newline character

### 4. Regular Expressions (re)
**Purpose**: Pattern matching for normalization

**Used for**:
- Stripping string literals
- Replacing identifiers
- Removing punctuation

---

## Performance Characteristics

### Time Complexity
- **Normalization**: O(n) where n = code length
- **Tokenization**: O(n)
- **Winnowing**: O(m) where m = number of tokens
- **Comparison**: O(f) where f = fingerprint size (typically f << m)
- **Total per pair**: O(n) - linear in code length

### Space Complexity
- **Tokens**: O(m) where m = number of tokens
- **Fingerprints**: O(f) where f = fingerprint size
- **Total**: O(m) - linear in code length

### Scalability
- **50 submissions**: 1,225 pairs → ~2 seconds
- **100 submissions**: 4,950 pairs → ~8 seconds
- **500 submissions**: 124,750 pairs → ~3 minutes

---

## Advantages of This Approach

1. **Language-agnostic**: Works for 26+ languages with same pipeline
2. **Robust**: Catches renamed variables, added comments, dummy code
3. **Fast**: Linear time per comparison
4. **Proven**: Winnowing is used by Google, Stanford MOSS
5. **Tunable**: Can adjust k, window size, thresholds

---

## Limitations

1. **Structural changes**: If student completely rewrites the algorithm (e.g., loop → recursion), token similarity will be low. That's why we also use AST analysis.

2. **Very short code**: Code with <5 tokens is skipped (too generic to compare)

3. **Boilerplate code**: Common patterns like `if __name__ == "__main__"` will match across all Python submissions. That's why we have a 25% minimum threshold.

4. **Normalization trade-off**: Aggressive normalization (all identifiers → VAR) means we can't distinguish between `good_variable_name` and `x`. But this is intentional - we want to catch renamed copies.

---

## Conclusion

The tokenizer uses a sophisticated pipeline combining:
- **Tree-sitter** for robust comment removal
- **Normalization** to catch renamed variables
- **Winnowing algorithm** to create robust fingerprints
- **Jaccard similarity** to compare fingerprints

This makes it extremely difficult for students to hide plagiarism through simple tricks like renaming variables or adding dummy code. Combined with AST analysis (the second engine) and optimized k-gram sensitivity (Fix 7), we catch nearly all forms of code plagiarism.

---

## References

1. **Winnowing Algorithm**: "Winnowing: Local Algorithms for Document Fingerprinting" by Schleimer, Wilkerson, and Aiken (2003)
2. **Tree-sitter**: https://tree-sitter.github.io/tree-sitter/
3. **MOSS (Measure of Software Similarity)**: Stanford's plagiarism detection system
4. **Jaccard Similarity**: Standard set similarity metric
