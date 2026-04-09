# Alternative Methods to Normalization in Plagiarism Detection

## Current Approach: Aggressive Normalization
Our current system replaces ALL identifiers with `VAR`:
- `findMax` → `VAR`
- `getHighest` → `VAR`
- Result: 100% match for renamed copies

**Problem**: Too aggressive - can't distinguish between good and bad variable names.

---

## Alternative Methods

### 1. Semantic Hashing (Embeddings)

**Concept**: Use machine learning to convert code into vector embeddings that capture semantic meaning.

**How it works**:
```python
# Student A
def find_max(arr):
    max_val = arr[0]
    for num in arr:
        if num > max_val:
            max_val = num
    return max_val

# Convert to embedding
embedding_a = [0.23, 0.45, 0.12, ..., 0.89]  # 768-dimensional vector

# Student B (renamed)
def get_highest(items):
    highest = items[0]
    for item in items:
        if item > highest:
            highest = item
    return highest

# Convert to embedding
embedding_b = [0.24, 0.44, 0.13, ..., 0.88]  # Similar vector

# Cosine similarity
similarity = cosine_similarity(embedding_a, embedding_b)  # ~0.95
```

**Tools**:
- **CodeBERT**: Pre-trained model for code understanding (Microsoft)
- **GraphCodeBERT**: Considers code structure
- **CodeT5**: Encoder-decoder model for code

**Advantages**:
- Understands semantic meaning, not just syntax
- Can detect similar algorithms even with different implementations
- Language-agnostic (one model for all languages)

**Disadvantages**:
- Requires GPU for fast inference
- Large model size (500MB+)
- Slower than token-based methods
- Needs training data

**Implementation Example**:
```python
from transformers import AutoTokenizer, AutoModel
import torch

tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
model = AutoModel.from_pretrained("microsoft/codebert-base")

def get_code_embedding(code):
    inputs = tokenizer(code, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    # Use [CLS] token embedding
    return outputs.last_hidden_state[:, 0, :].numpy()

def semantic_similarity(code_a, code_b):
    emb_a = get_code_embedding(code_a)
    emb_b = get_code_embedding(code_b)
    # Cosine similarity
    similarity = np.dot(emb_a, emb_b.T) / (np.linalg.norm(emb_a) * np.linalg.norm(emb_b))
    return similarity[0][0]
```

---

### 2. Partial Normalization (Hybrid Approach)

**Concept**: Instead of replacing ALL identifiers with `VAR`, preserve some information.

#### Option A: Keep First Letter
```python
# Original
def findMax(arr):
    max_val = arr[0]

# Normalized
def VAR_f(VAR_a):
    VAR_m = VAR_a[0]
```

**Advantages**:
- Still catches most plagiarism
- Allows some differentiation
- Fast (no ML needed)

**Disadvantages**:
- Students can fool it by renaming `findMax` → `getMax` (both become `VAR_f` and `VAR_g`)

#### Option B: Keep Length
```python
# Original
def findMax(arr):
    max_val = arr[0]

# Normalized
def VAR7(VAR3):
    VAR7 = VAR3[0]
```

**Advantages**:
- Preserves some structure information
- Fast

**Disadvantages**:
- Students can fool it by using same-length names

#### Option C: Hash Identifiers
```python
# Original
def findMax(arr):
    max_val = arr[0]

# Normalized
def VAR_a3f2(VAR_b8c1):
    VAR_d4e9 = VAR_b8c1[0]
```

**Advantages**:
- Same name → same hash (consistent)
- Different name → different hash
- Still catches exact copies

**Disadvantages**:
- Doesn't catch renamed copies (which is the point of normalization)

---

### 3. Control Flow Graph (CFG) Comparison

**Concept**: Convert code to a graph showing program flow, then compare graphs.

**How it works**:
```python
# Student A
def find_max(arr):
    max_val = arr[0]
    for num in arr:
        if num > max_val:
            max_val = num
    return max_val

# Control Flow Graph
START → ASSIGN(max_val) → FOR_LOOP → IF_CONDITION → ASSIGN(max_val) → RETURN
```

**Graph Representation**:
```
    [START]
       ↓
   [max_val = arr[0]]
       ↓
   [for num in arr]
       ↓
   [if num > max_val]
      ↙     ↘
  [assign]  [skip]
      ↘     ↙
   [return max_val]
       ↓
     [END]
```

**Comparison**: Use graph isomorphism algorithms to check if two CFGs are similar.

**Tools**:
- **NetworkX**: Python graph library
- **Graph Edit Distance**: Measure similarity between graphs

**Advantages**:
- Catches structural plagiarism
- Resistant to variable renaming
- Resistant to statement reordering (within blocks)

**Disadvantages**:
- Complex to implement
- Graph comparison is computationally expensive (NP-hard in general case)
- May miss simple text-based copying

**Implementation Example**:
```python
import networkx as nx
from networkx.algorithms import isomorphism

def build_cfg(code):
    # Parse code into AST
    tree = ast.parse(code)
    
    # Build control flow graph
    G = nx.DiGraph()
    node_id = 0
    
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            G.add_edge(node_id, node_id + 1, label="condition")
            G.add_edge(node_id, node_id + 2, label="else")
            node_id += 2
        elif isinstance(node, ast.For):
            G.add_edge(node_id, node_id + 1, label="loop")
            node_id += 1
        # ... handle other node types
    
    return G

def cfg_similarity(code_a, code_b):
    cfg_a = build_cfg(code_a)
    cfg_b = build_cfg(code_b)
    
    # Check if graphs are isomorphic
    matcher = isomorphism.GraphMatcher(cfg_a, cfg_b)
    if matcher.is_isomorphic():
        return 100.0
    
    # Calculate graph edit distance
    distance = nx.graph_edit_distance(cfg_a, cfg_b)
    max_nodes = max(len(cfg_a.nodes), len(cfg_b.nodes))
    similarity = (1 - distance / max_nodes) * 100
    return similarity
```

---

### 4. Program Dependence Graph (PDG)

**Concept**: Similar to CFG but also captures data dependencies.

**How it works**:
```python
# Code
def calculate(a, b):
    x = a + 1
    y = b + 2
    z = x + y
    return z

# PDG shows:
# - Control dependencies (which statements depend on which conditions)
# - Data dependencies (which variables depend on which other variables)

# Dependencies:
# z depends on x and y
# x depends on a
# y depends on b
```

**Advantages**:
- Captures both control flow and data flow
- Very robust against reordering
- Catches semantic plagiarism

**Disadvantages**:
- Very complex to implement
- Computationally expensive
- Requires deep program analysis

---

### 5. Token Sequence Alignment (Edit Distance)

**Concept**: Use string alignment algorithms (like DNA sequence alignment) to find longest common subsequences.

**How it works**:
```python
# Student A tokens
['def', 'VAR', 'VAR', 'VAR', '=', 'VAR', 'for', 'VAR', 'if', 'VAR', '>', 'VAR', 'VAR', '=', 'VAR', 'return', 'VAR']

# Student B tokens (with extra prints)
['def', 'VAR', 'VAR', 'print', 'VAR', '=', 'VAR', 'for', 'VAR', 'print', 'if', 'VAR', '>', 'VAR', 'VAR', '=', 'VAR', 'return', 'VAR']

# Longest Common Subsequence (LCS)
['def', 'VAR', 'VAR', 'VAR', '=', 'VAR', 'for', 'VAR', 'if', 'VAR', '>', 'VAR', 'VAR', '=', 'VAR', 'return', 'VAR']

# Similarity = LCS_length / max(len_a, len_b)
similarity = 17 / 19 = 89.5%
```

**Algorithms**:
- **Levenshtein Distance**: Minimum edits to transform one sequence to another
- **Longest Common Subsequence (LCS)**: Longest sequence appearing in both
- **Smith-Waterman**: Local sequence alignment (from bioinformatics)

**Advantages**:
- Handles insertions/deletions naturally
- Well-studied algorithms
- Exact results (not probabilistic)

**Disadvantages**:
- O(n*m) time complexity (slower than winnowing)
- Doesn't handle reordering well
- May be too sensitive to small changes

**Implementation Example**:
```python
from difflib import SequenceMatcher

def lcs_similarity(tokens_a, tokens_b):
    matcher = SequenceMatcher(None, tokens_a, tokens_b)
    # Get longest matching block
    match = matcher.find_longest_match(0, len(tokens_a), 0, len(tokens_b))
    lcs_length = match.size
    
    max_length = max(len(tokens_a), len(tokens_b))
    similarity = (lcs_length / max_length) * 100
    return similarity
```

---

### 6. N-gram Frequency Analysis

**Concept**: Instead of winnowing, use frequency of n-grams as features.

**How it works**:
```python
# Student A tokens
['def', 'VAR', 'VAR', 'for', 'VAR', 'if', 'VAR', 'return']

# Trigrams (n=3)
('def', 'VAR', 'VAR'): 1
('VAR', 'VAR', 'for'): 1
('VAR', 'for', 'VAR'): 1
('for', 'VAR', 'if'): 1
('VAR', 'if', 'VAR'): 1
('if', 'VAR', 'return'): 1

# Create frequency vector
vector_a = [1, 1, 1, 1, 1, 1, 0, 0, ...]

# Compare using cosine similarity
similarity = cosine_similarity(vector_a, vector_b)
```

**Advantages**:
- Simple to implement
- Fast comparison (vector operations)
- Captures local patterns

**Disadvantages**:
- High-dimensional vectors (many possible n-grams)
- Doesn't handle insertions as well as winnowing
- Sensitive to n-gram size choice

---

### 7. Compression-Based Similarity

**Concept**: Use data compression to measure similarity. If two files compress well together, they're similar.

**How it works**:
```python
# Kolmogorov Complexity approximation
size_a = len(gzip.compress(code_a))
size_b = len(gzip.compress(code_b))
size_ab = len(gzip.compress(code_a + code_b))

# Normalized Compression Distance (NCD)
ncd = (size_ab - min(size_a, size_b)) / max(size_a, size_b)
similarity = (1 - ncd) * 100
```

**Advantages**:
- Language-agnostic
- No need for parsing or tokenization
- Theoretically sound (based on Kolmogorov complexity)

**Disadvantages**:
- Sensitive to compression algorithm
- Not intuitive (hard to explain why two codes are similar)
- May not work well for very short code

**Implementation Example**:
```python
import gzip

def compression_similarity(code_a, code_b):
    # Compress individually
    size_a = len(gzip.compress(code_a.encode()))
    size_b = len(gzip.compress(code_b.encode()))
    
    # Compress together
    size_ab = len(gzip.compress((code_a + code_b).encode()))
    
    # Normalized Compression Distance
    ncd = (size_ab - min(size_a, size_b)) / max(size_a, size_b)
    
    # Convert to similarity percentage
    similarity = (1 - ncd) * 100
    return max(0, similarity)  # Ensure non-negative
```

---

### 8. Fuzzy Hashing (ssdeep)

**Concept**: Create fuzzy hashes that are similar for similar inputs.

**How it works**:
```python
# Student A
hash_a = ssdeep.hash(code_a)
# "3:ABC123:XYZ789"

# Student B (slightly different)
hash_b = ssdeep.hash(code_b)
# "3:ABC124:XYZ788"

# Compare hashes
similarity = ssdeep.compare(hash_a, hash_b)
# Returns 0-100
```

**Advantages**:
- Fast comparison (just compare hashes)
- Handles small changes well
- Used in malware detection

**Disadvantages**:
- Not designed for code (designed for binary files)
- Less accurate than specialized code comparison
- Black box (hard to explain results)

---

## Comparison Table

| Method | Speed | Accuracy | Robustness | Complexity | GPU Needed |
|--------|-------|----------|------------|------------|------------|
| **Current (Normalization + Winnowing)** | ⚡⚡⚡ Fast | ⭐⭐⭐⭐ High | ⭐⭐⭐⭐ High | ⭐⭐ Medium | ❌ No |
| **Semantic Embeddings** | ⚡ Slow | ⭐⭐⭐⭐⭐ Very High | ⭐⭐⭐⭐⭐ Very High | ⭐⭐⭐⭐ High | ✅ Yes |
| **Partial Normalization** | ⚡⚡⚡ Fast | ⭐⭐⭐ Medium | ⭐⭐⭐ Medium | ⭐ Low | ❌ No |
| **Control Flow Graph** | ⚡⚡ Medium | ⭐⭐⭐⭐ High | ⭐⭐⭐⭐⭐ Very High | ⭐⭐⭐⭐ High | ❌ No |
| **Edit Distance** | ⚡⚡ Medium | ⭐⭐⭐ Medium | ⭐⭐⭐ Medium | ⭐⭐ Medium | ❌ No |
| **N-gram Frequency** | ⚡⚡⚡ Fast | ⭐⭐⭐ Medium | ⭐⭐⭐ Medium | ⭐ Low | ❌ No |
| **Compression-Based** | ⚡⚡ Medium | ⭐⭐ Low | ⭐⭐ Low | ⭐ Low | ❌ No |
| **Fuzzy Hashing** | ⚡⚡⚡ Fast | ⭐⭐ Low | ⭐⭐ Low | ⭐ Low | ❌ No |

---

## Recommended Hybrid Approach

**Best of both worlds**: Combine multiple methods

### Tier 1: Fast Filtering (Current System)
- Normalization + Winnowing
- Filters out obvious non-matches quickly
- Catches 90% of plagiarism

### Tier 2: Deep Analysis (For suspicious cases)
- Control Flow Graph comparison
- Semantic embeddings
- Only run on pairs with 40-80% token similarity

**Implementation**:
```python
def hybrid_plagiarism_check(code_a, code_b):
    # Tier 1: Fast token-based check
    token_sim = token_similarity_percent(code_a, code_b)
    
    if token_sim >= 80:
        return {"similarity": token_sim, "label": "Highly similar", "method": "token"}
    
    if token_sim < 40:
        return {"similarity": token_sim, "label": "Likely original", "method": "token"}
    
    # Tier 2: Suspicious range - do deep analysis
    cfg_sim = cfg_similarity(code_a, code_b)
    semantic_sim = semantic_similarity(code_a, code_b)
    
    # Weighted average
    final_sim = (token_sim * 0.4 + cfg_sim * 0.3 + semantic_sim * 0.3)
    
    if final_sim >= 70:
        return {"similarity": final_sim, "label": "Smart copy detected", "method": "hybrid"}
    else:
        return {"similarity": final_sim, "label": "Moderately similar", "method": "hybrid"}
```

---

## Conclusion

**Current approach (Normalization + Winnowing) is excellent for**:
- Fast, scalable plagiarism detection
- Catching renamed variables
- Handling dummy code insertions
- Production deployment

**Consider alternatives for**:
- Research projects (semantic embeddings)
- Very sophisticated plagiarism (CFG/PDG)
- When you need explainability (edit distance)

**Best recommendation**: Stick with current approach for production, but add semantic embeddings as Tier 2 for suspicious cases (40-80% token similarity).

---

## Implementation Priority

If you want to enhance the system:

1. **Easy win**: Add edit distance as a third score (alongside token and AST)
2. **Medium effort**: Implement CFG comparison for suspicious cases
3. **High effort**: Add semantic embeddings with CodeBERT

All three can coexist with the current system!
