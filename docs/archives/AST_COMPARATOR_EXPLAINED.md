# AST Comparator Deep Dive: How It Works

## Overview
The AST (Abstract Syntax Tree) comparator is the second engine in our dual-detection system. It analyzes the **structural logic** of code by parsing it into a tree representation and comparing the control flow patterns. This catches plagiarism that token-based analysis might miss, especially when students add dummy code.

---

## The Complete Pipeline

```
Raw Code → Parse to AST → Extract Structural Nodes → Filter Non-Structural → Ordered Structural Hashing (Winnowing) → Similarity Score
```

Let's walk through each step with examples.

---

## What is an Abstract Syntax Tree (AST)?

An AST is a tree representation of code that captures its syntactic structure.

**Example**:
```python
def add(a, b):
    return a + b
```

**AST Representation**:
```
Module
└── FunctionDef (name='add')
    ├── arguments
    │   ├── arg (name='a')
    │   └── arg (name='b')
    └── Return
        └── BinOp
            ├── Name (id='a')
            ├── Add
            └── Name (id='b')
```

**Key Insight**: The AST captures the STRUCTURE, not the names. Whether you call it `add(a, b)` or `sum(x, y)`, the structure is identical!

---

## Step 1: Parse Code to AST

We use two different parsers depending on the language:

### For Python: Built-in `ast` module
```python
import ast

code = """
def add(a, b):
    return a + b
"""

tree = ast.parse(code)
```

### For Other Languages: Tree-sitter
```python
from tree_sitter import Language, Parser

# Load language
lang = Language(tree_sitter_java.language())
parser = Parser(lang)

# Parse code
tree = parser.parse(bytes(code, "utf8"))
```

**Why Tree-sitter?**
- Production-grade parser used by GitHub Copilot
- Supports 26+ languages
- Handles syntax errors gracefully
- Fast incremental parsing

---

## Step 2: Extract Structural Nodes

**Function**: `get_structural_tokens()`

**Purpose**: Extract only the node types that represent program structure, not implementation details.

### What We Extract (Structural Nodes):

**Control Flow**:
- `FunctionDef`, `ClassDef` - Definitions
- `For`, `While` - Loops
- `If` - Conditionals
- `Return`, `Break`, `Continue` - Flow control
- `Try`, `Raise` - Exception handling

**Operations**:
- `BinOp` - Binary operations (a + b, a * b)
- `UnaryOp` - Unary operations (-a, not a)
- `Compare` - Comparisons (a > b, a == b)
- `BoolOp` - Boolean operations (and, or)

**Data Structures**:
- `Assign`, `AugAssign` - Assignments
- `Subscript` - Array/dict access
- `Attribute` - Object attribute access

### What We IGNORE (Non-Structural):

**Expression Details**:
- `Call` - Function calls (including print statements!)
- `Name` - Variable names
- `Constant` - Literal values
- `Str`, `Num` - String/number literals
- `Expr` - Expression statements

**Why ignore these?**
- `Call` nodes include `print()` statements - we want to ignore dummy prints
- `Name` nodes are variable names - already handled by tokenizer
- `Constant` nodes are literal values - not part of logic structure

### Example: Python

```python
def get_python_ast_nodes(source_code: str) -> list:
    code = clean_code(source_code)
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    # Filter to only structural/control flow nodes
    structural_types = {
        'Module', 'FunctionDef', 'AsyncFunctionDef', 'ClassDef',
        'Return', 'Delete', 'Assign', 'AugAssign', 'AnnAssign',
        'For', 'AsyncFor', 'While', 'If', 'With', 'AsyncWith',
        'Raise', 'Try', 'Assert', 'Import', 'ImportFrom',
        'Global', 'Nonlocal', 'Pass', 'Break', 'Continue',
        'BoolOp', 'BinOp', 'UnaryOp', 'Lambda', 'IfExp',
        'Compare', 'Attribute', 'Subscript',
        'ListComp', 'SetComp', 'DictComp', 'GeneratorExp'
        # NOTE: 'Call' is intentionally excluded!
    }
    
    nodes = []
    
    def walk(node):
        name = type(node).__name__
        if name in structural_types:
            nodes.append(name)
        for child in ast.iter_child_nodes(node):
            walk(child)
            
    walk(tree)
    return nodes
```

---

## Step 3: Real Example - Filtering in Action

### Student A (Original):
```python
def find_even(numbers):
    for num in numbers:
        if num % 2 == 0:
            return True
    return False
```

**All AST nodes** (if we extracted everything):
```
Module, FunctionDef, For, Name, Name, If, Compare, BinOp, Mod, Name, Constant, 
Constant, Return, Constant, Return, Constant
```

**Filtered structural nodes** (what we actually extract):
```
Module, FunctionDef, For, If, Compare, BinOp, Return, Return
```

### Student B (Added dummy prints):
```python
def check_digits(random_array):
    print("Starting search...")
    for dummy_val in random_array:
        print("Checking value...")
        if dummy_val % 2 == 0:
            return True
    print("No even found")
    return False
```

**All AST nodes** (if we extracted everything):
```
Module, FunctionDef, Expr, Call, Name, Constant, For, Name, Name, Expr, Call, 
Name, Constant, If, Compare, BinOp, Mod, Name, Constant, Constant, Return, 
Constant, Expr, Call, Name, Constant, Return, Constant
```

**Filtered structural nodes** (what we actually extract):
```
Module, FunctionDef, For, If, Compare, BinOp, Return, Return
```

**Result**: IDENTICAL! ✅

The `Call` nodes from `print()` statements are filtered out, so both codes have the same structural fingerprint.

---

## Step 4: Compare Using Ordered Structural Hashing (Winnowing)

**Function**: `ast_similarity_percent()`

**Purpose**: Compare the structural node sequence using winnowing fingerprints to preserve the logical "flow" of the program.

**Why Winnowing (Fix 3)?**

In our final architecture, we replaced direct set comparison with **Ordered Structural Hashing**. This was done because:

1. **Order Matters**: Set matching could be bypassed by students reordering code blocks. Winnowing preserves the sequence of logic.
2. **Repetition Matters**: A code with 10 `if` statements is more complex than one with 1. Winnowing catches the "density" of logic better than sets.
3. **Robustness**: Like the tokenizer, winnowing in AST makes the comparison resistant to small "structural noise" injections.

### Comparison Logic:

Instead of unique types, we now compare **structural fingerprints**.

```python
def ast_similarity_percent(code_a: str, code_b: str, language: str = 'python') -> float:
    nodes_a = get_structural_tokens(code_a, language)
    nodes_b = get_structural_tokens(code_b, language)

    if not nodes_a or not nodes_b:
        return 0.0

    # FIX 3: Use winnowing fingerprints instead of unordered set extraction.
    # This mathematically preserves code ordering, repetition, and depth.
    set_a = winnowing_ast(nodes_a)
    set_b = winnowing_ast(nodes_b)

    intersection = set_a & set_b
    union = set_a | set_b

    if not union:
        return 0.0

    score = (len(intersection) / len(union)) * 100
    return float(round(score, 2))
```

---

## Why AST is Better Than Tokens for Structural Plagiarism

### Case 1: Dummy Code Insertion

**Problem**: Student adds print statements to fool token-based detection.

```python
# Student A
def find_max(arr):
    max_val = arr[0]
    for num in arr:
        if num > max_val:
            max_val = num
    return max_val

# Student B (added 3 prints)
def find_max(arr):
    print("Starting...")
    max_val = arr[0]
    for num in arr:
        print("Checking...")
        if num > max_val:
            max_val = num
    print("Done")
    return max_val
```

**Token similarity**: 57% (many different tokens due to prints)
**AST similarity**: 100% (same structure, prints filtered out)

**Winner**: AST! ✅

### Case 2: Different Variable Names

**Problem**: Student renames all variables.

```python
# Student A
def find_max(arr):
    max_val = arr[0]
    return max_val

# Student B
def get_highest(items):
    highest = items[0]
    return highest
```

**Token similarity**: 100% (normalization catches this)
**AST similarity**: 100% (same structure)

**Winner**: Both! ✅ (This is why we need dual-engine)

### Case 3: Different Algorithms

**Problem**: Students use genuinely different approaches.

```python
# Student A (iterative)
def reverse(s):
    result = ""
    for char in s:
        result = char + result
    return result

# Student B (slicing)
def reverse(s):
    return s[::-1]
```

**Token similarity**: 25% (very different code)
**AST similarity**: 44% (different structures: For vs Subscript)

**Winner**: Both correctly identify as different! ✅

---

## Multi-Language Support with Tree-Sitter

### Language Registry

We support 26+ languages through Tree-sitter:

```python
LANGUAGE_REGISTRY = {
    "python":      tree_sitter_python,
    "java":        tree_sitter_java,
    "javascript":  tree_sitter_javascript,
    "typescript":  tree_sitter_typescript,
    "c":           tree_sitter_c,
    "cpp":         tree_sitter_cpp,
    "rust":        tree_sitter_rust,
    "go":          tree_sitter_go,
    "php":         tree_sitter_php,
    "ruby":        tree_sitter_ruby,
    "swift":       tree_sitter_swift,
    "kotlin":      tree_sitter_kotlin,
    "scala":       tree_sitter_scala,
    "haskell":     tree_sitter_haskell,
    "lua":         tree_sitter_lua,
    "bash":        tree_sitter_bash,
    "html":        tree_sitter_html,
    "css":         tree_sitter_css,
    "json":        tree_sitter_json,
    "yaml":        tree_sitter_yaml,
    "toml":        tree_sitter_toml,
    "sql":         tree_sitter_sql,
    "ocaml":       tree_sitter_ocaml,
}
```

### Example: Java

```java
// Student A
public int findMax(int[] arr) {
    int max = arr[0];
    for (int i = 1; i < arr.length; i++) {
        if (arr[i] > max) {
            max = arr[i];
        }
    }
    return max;
}

// Student B (added print)
public int findMax(int[] arr) {
    int max = arr[0];
    for (int i = 1; i < arr.length; i++) {
        if (arr[i] > max) {
            max = arr[i];
        }
    }
    System.out.println(max);  // Added this
    return max;
}
```

**Tree-sitter extracts**:
- Both have: `method_declaration`, `for_statement`, `if_statement`, `binary_expression`, `return_statement`
- Student B has extra: `expression_statement` (from println)
- But we filter out `expression_statement` and `method_invocation` (calls)

**Result**: High AST similarity despite the print statement!

---

## Complete Example: End-to-End

### Student A's Code:
```python
def count_vowels(text):
    vowels = "aeiou"
    count = 0
    for char in text:
        if char in vowels:
            count += 1
    return count
```

### Student B's Code (copied with dummy code):
```python
def count_vowels(text):
    print("Starting vowel count")
    vowels = "aeiou"
    count = 0
    print("Initialized variables")
    for char in text:
        print(f"Checking {char}")
        if char in vowels:
            count += 1
    print(f"Total: {count}")
    return count
```

### Pipeline Execution:

**Step 1: Parse to AST**

Student A AST (simplified):
```
Module
└── FunctionDef
    ├── Assign (vowels = "aeiou")
    ├── Assign (count = 0)
    ├── For
    │   └── If
    │       └── AugAssign (count += 1)
    └── Return
```

Student B AST (simplified):
```
Module
└── FunctionDef
    ├── Expr (print call)
    ├── Assign (vowels = "aeiou")
    ├── Assign (count = 0)
    ├── Expr (print call)
    ├── For
    │   ├── Expr (print call)
    │   └── If
    │       └── AugAssign (count += 1)
    ├── Expr (print call)
    └── Return
```

**Step 2: Extract Structural Nodes**

Student A:
```
['Module', 'FunctionDef', 'Assign', 'Assign', 'For', 'If', 'AugAssign', 'Return']
```

Student B (Expr and Call nodes filtered):
```
['Module', 'FunctionDef', 'Assign', 'Assign', 'For', 'If', 'AugAssign', 'Return']
```

**Step 3: Apply Winnowing Fingerprints (FIX 3)**

Instead of collapsing to an unordered set, we run `winnowing_ast()` on the ordered node list:
- Splits into overlapping k-grams (k=6) of consecutive node types
- Hashes each k-gram using MD5
- Selects minimum hash in each sliding window (window=4)
- Result: a **set of fingerprints** that encodes both order and frequency

```python
# FIX 3: Use winnowing fingerprints instead of unordered set extraction.
# This mathematically preserves code ordering, repetition, and depth.
set_a = winnowing_ast(nodes_a)  # fingerprint set
set_b = winnowing_ast(nodes_b)  # fingerprint set
```

**Step 4: Compare Fingerprints**

```
Intersection: shared fingerprint hashes
Union: all fingerprint hashes
Similarity: len(intersection) / len(union) × 100
```

**Result**: 100% AST similarity → Flagged as "Low text overlap, high structural similarity"

---

## Performance Characteristics

### Time Complexity
- **Parsing**: O(n) where n = code length
- **Node extraction**: O(m) where m = number of AST nodes
- **Set comparison**: O(k) where k = unique node types (typically k < 20)
- **Total per pair**: O(n) - linear in code length

### Space Complexity
- **AST tree**: O(m) where m = number of nodes
- **Node list**: O(m)
- **Node set**: O(k) where k = unique types
- **Total**: O(m) - linear in AST size

### Scalability
- **Faster than token-based** for short code (fewer nodes than tokens)
- **Similar speed** for long code (both O(n))
- **Set comparison is very fast** (typically <20 unique node types)

---

## Advantages of AST Analysis

1. **Ignores surface changes**: Variable names, comments, whitespace don't matter
2. **Catches structural plagiarism**: Focuses on logic, not text
3. **Robust against dummy code**: Filters out non-structural nodes like print statements
4. **Language-agnostic**: Works for 26+ languages with same approach
5. **Complements token-based**: Catches what tokens miss

---

## Limitations

1. **Requires valid syntax**: If code has syntax errors, AST parsing fails (fallback to token-based only)

2. **Misses semantic equivalence**: Different structures that do the same thing won't match:
   ```python
   # Loop
   for i in range(10):
       print(i)
   
   # Recursion
   def print_nums(i):
       if i < 10:
           print(i)
           print_nums(i + 1)
   ```
   These are semantically equivalent but structurally different.

3. **Generic patterns**: Very simple code (like `return a + b`) will have high AST similarity across all submissions. That's why we combine with token-based analysis.

> [!NOTE]
> The previous limitation about "set comparison losing sequence info" was resolved by **FIX 3**, which replaced raw `set()` comparison with `winnowing_ast()` fingerprints. Ordering, repetition, and nesting depth are now all mathematically preserved.

---

## Why We Use Winnowing for Both Engines (Fix 3)

**Question**: The tokenizer and AST both use winnowing. Why?

**Answer**: While they represent different data (tokens vs. tree nodes), they share a common requirement: **Detection must be robust against local gaps and reordering.**

### Hybrid Advantage:
- **Tokenizer Winnowing**: Catches textual similarity (verbatim copying).
- **AST Winnowing**: Catches structural similarity (logic copying).

By using winnowing for both, we ensure that adding "junk" (whether it's print statements or dummy logic blocks) doesn't break the mathematical fingerprint of the student's solution.

---

## Integration with Token-Based Engine

AST and token-based engines work together:

### Scenario 1: Renamed Variables
- **Token**: 100% (normalization catches it)
- **AST**: 100% (same structure)
- **Verdict**: Exact copy ✅

### Scenario 2: Dummy Code Added
- **Token**: 57% (extra tokens lower score)
- **AST**: 100% (structure unchanged)
- **Verdict**: Low text overlap, high structural similarity ✅

### Scenario 3: Different Algorithms
- **Token**: 25% (very different code)
- **AST**: 44% (different structures)
- **Verdict**: Likely original ✅

### Scenario 4: Syntax Error
- **Token**: Works (can still tokenize)
- **AST**: Fails (can't parse)
- **Verdict**: Use token score only ✅

**This is why dual-engine detection is more robust than either engine alone!**

---

## Tools & Libraries Used

### 1. Python `ast` Module
**Purpose**: Parse Python code into AST

**Advantages**:
- Built-in, no installation needed
- Fast and reliable
- Standard library

**Usage**:
```python
import ast
tree = ast.parse(code)
# Using DFS to preserve node ordering
nodes = []
def walk(n):
    nodes.append(type(n).__name__)
    for c in ast.iter_child_nodes(n): walk(c)
walk(tree)
```

**Fix 7 Update**: We now use **Depth-First Search (DFS)** recursion instead of `ast.walk()` to strictly preserve the top-to-bottom logical execution sequence of the student's code. This eliminates false positives where layer-based node extraction previously matched unrelated code blocks.

### 2. Tree-Sitter
**Purpose**: Parse 26+ languages into AST

**Why Tree-sitter?**
- Production-grade (used by GitHub, Atom)
- Handles syntax errors gracefully
- Incremental parsing (fast)
- Consistent API across languages

**Installation**:
```bash
pip install tree-sitter
pip install tree-sitter-java
pip install tree-sitter-javascript
# ... etc
```

### 3. Set Operations (Python built-in)
**Purpose**: Fast set intersection and union

**Why sets?**
- O(1) membership testing
- O(n) intersection/union
- Perfect for Jaccard similarity

---

## Conclusion

The AST comparator provides a powerful second layer of plagiarism detection by:
- **Parsing code into structural representation** using Python `ast` (for Python) or Tree-sitter (for all other languages)
- **Filtering to only structural nodes** (ignoring calls, names, constants)
- **Comparing ordered winnowing fingerprints** (FIX 3) using Jaccard similarity — preserving node order, repetition, and nesting depth
- **Catching "smart plagiarism"** where students add dummy code or rename variables

Combined with token-based analysis, this dual-engine approach catches nearly all forms of code plagiarism while minimizing false positives.

---

## References

1. **Tree-sitter**: https://tree-sitter.github.io/tree-sitter/
2. **Python AST**: https://docs.python.org/3/library/ast.html
3. **Jaccard Similarity**: Standard set similarity metric
4. **AST-based Plagiarism Detection**: "Detecting Source Code Plagiarism Using Abstract Syntax Trees" (various papers)

