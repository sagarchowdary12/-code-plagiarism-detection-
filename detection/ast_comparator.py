import ast
import codecs
import hashlib

# ─────────────────────────────────────────
# TREE-SITTER UNIVERSAL IMPORTS
# ─────────────────────────────────────────
from tree_sitter import Language, Parser


def _try_import(module_name):
    try:
        import importlib
        return importlib.import_module(module_name)
    except ImportError:
        return None


_ts_java = _try_import("tree_sitter_java")
_ts_js = _try_import("tree_sitter_javascript")
_ts_c = _try_import("tree_sitter_c")
_ts_cpp = _try_import("tree_sitter_cpp")
_ts_php = _try_import("tree_sitter_php")

if _ts_php is not None:
    _php_module = _ts_php

    class _PHPWrapper:
        @staticmethod
        def language():
            return _php_module.language_php()
    _ts_php = _PHPWrapper()

_ts_rust = _try_import("tree_sitter_rust")
_ts_go = _try_import("tree_sitter_go")
_ts_ruby = _try_import("tree_sitter_ruby")

_ts_ts_raw = _try_import("tree_sitter_typescript")
if _ts_ts_raw is not None:
    _ts_ts_mod = _ts_ts_raw

    class _TSWrapper:
        @staticmethod
        def language():
            return _ts_ts_mod.language_typescript()
    _ts_ts = _TSWrapper()
else:
    _ts_ts = None
_ts_bash = _try_import("tree_sitter_bash")
_ts_html = _try_import("tree_sitter_html")
_ts_css = _try_import("tree_sitter_css")
_ts_json = _try_import("tree_sitter_json")
_ts_yaml = _try_import("tree_sitter_yaml")
_ts_toml = _try_import("tree_sitter_toml")
_ts_kotlin = _try_import("tree_sitter_kotlin")
_ts_scala = _try_import("tree_sitter_scala")
_ts_haskell = _try_import("tree_sitter_haskell")
_ts_lua = _try_import("tree_sitter_lua")
_ts_swift = _try_import("tree_sitter_swift")
_ts_sql = _try_import("tree_sitter_sql")
_ts_ocaml = _try_import("tree_sitter_ocaml")

# ─────────────────────────────────────────
# LANGUAGE REGISTRY
# ─────────────────────────────────────────
LANGUAGE_REGISTRY = {
    "javascript":  _ts_js,
    "js":          _ts_js,
    "typescript":  _ts_ts,
    "ts":          _ts_ts,
    "html":        _ts_html,
    "css":         _ts_css,
    "json":        _ts_json,
    "yaml":        _ts_yaml,
    "toml":        _ts_toml,
    "java":        _ts_java,
    "c":           _ts_c,
    "cpp":         _ts_cpp,
    "c++":         _ts_cpp,
    "rust":        _ts_rust,
    "go":          _ts_go,
    "swift":       _ts_swift,
    "php":         _ts_php,
    "ruby":        _ts_ruby,
    "bash":        _ts_bash,
    "shell":       _ts_bash,
    "lua":         _ts_lua,
    "kotlin":      _ts_kotlin,
    "scala":       _ts_scala,
    "haskell":     _ts_haskell,
    "ocaml":       _ts_ocaml,
    "sql":         _ts_sql,
}

LANGUAGE_REGISTRY = {k: v for k,
                     v in LANGUAGE_REGISTRY.items() if v is not None}
print(f"[AST] Tree-Sitter loaded for: {sorted(set(LANGUAGE_REGISTRY.keys()))}")

# ─────────────────────────────────────────
# CLEAN CODE
# ─────────────────────────────────────────


def clean_code(source_code: str) -> str:
    try:
        return codecs.decode(source_code, 'unicode_escape')
    except Exception:
        cleaned = source_code.replace('\\n', '\n')
        cleaned = source_code.replace('\\t', '\t')
        return cleaned

# ─────────────────────────────────────────
# PYTHON AST
# ─────────────────────────────────────────


def get_python_ast_nodes(source_code: str) -> list:
    code = clean_code(source_code)
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    # Filter to only structural/control flow nodes, ignore expression details and calls
    structural_types = {
        'Module', 'FunctionDef', 'AsyncFunctionDef', 'ClassDef',
        'Return', 'Delete', 'Assign', 'AugAssign', 'AnnAssign',
        'For', 'AsyncFor', 'While', 'If', 'With', 'AsyncWith',
        'Raise', 'Try', 'Assert', 'Import', 'ImportFrom',
        'Global', 'Nonlocal', 'Pass', 'Break', 'Continue',
        'BoolOp', 'BinOp', 'UnaryOp', 'Lambda', 'IfExp',
        'Compare', 'Attribute', 'Subscript',
        'ListComp', 'SetComp', 'DictComp', 'GeneratorExp'
        # Removed 'Call' - function calls like print() should be ignored
    }
    
    return [type(node).__name__ for node in ast.walk(tree) 
            if type(node).__name__ in structural_types]

# ─────────────────────────────────────────
# TREE-SITTER PARSER
# ─────────────────────────────────────────


def get_tree_sitter_nodes(source_code: str, lang_module) -> list:
    code = clean_code(source_code)
    try:
        lang = Language(lang_module.language())
        parser = Parser(lang) 
        tree = parser.parse(bytes(code, "utf8"))

        nodes = []

        def walk(node):
            nodes.append(node.type)
            for child in node.children:
                walk(child)

        walk(tree.root_node)
        return nodes

    except Exception as e:
        print(f"[AST] Tree-Sitter Parsing Error: {e}")
        return []

# ─────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────


def get_structural_tokens(source_code: str, language: str) -> list:
    lang = language.lower().strip()

    if lang == 'python':
        return get_python_ast_nodes(source_code)

    module = LANGUAGE_REGISTRY.get(lang)
    if module:
        return get_tree_sitter_nodes(source_code, module)

    print(f"[AST] Unsupported language '{language}'")
    return []

# ─────────────────────────────────────────
# WINNOWING (AST)
# ─────────────────────────────────────────


def hash_kgram(kgram: tuple) -> int:
    return int(hashlib.md5(' '.join(kgram).encode()).hexdigest(), 16)


def winnowing_ast(nodes: list, k: int = 3, window_size: int = 4) -> set:
    if len(nodes) < k:
        return set()

    hashes = []
    for i in range(len(nodes) - k + 1):
        kgram = tuple(nodes[i:i+k])
        hashes.append(hash_kgram(kgram))

    fingerprints = set()
    for i in range(len(hashes) - window_size + 1):
        window = hashes[i:i+window_size]
        fingerprints.add(min(window))

    return fingerprints

# ─────────────────────────────────────────
# SIMILARITY (WITH WINNOWING AST)
# ─────────────────────────────────────────


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
