import re
import codecs
import hashlib
from functools import lru_cache
from typing import List
from tree_sitter import Language, Parser
from detection.ast_comparator import LANGUAGE_REGISTRY

# ─────────────────────────────────────────
# UNIVERSAL LOGIC KEYWORDS
# ─────────────────────────────────────────
UNIVERSAL_KEYWORDS = {
    'if', 'else', 'elif', 'switch', 'case', 'default',
    'for', 'while', 'do', 'foreach', 'break', 'continue',
    'try', 'catch', 'finally', 'throw', 'throws',
    'return', 'yield', 'await', 'async',
    'class', 'interface', 'struct', 'enum', 'def', 'function', 'fn',
    'public', 'private', 'protected', 'static', 'final', 'abstract',
    'import', 'from', 'package', 'using', 'include', 'namespace',
    'const', 'let', 'var', 'val', 'new', 'this', 'super',
}

# ─────────────────────────────────────────
# CLEAN CODE FROM DB
# ─────────────────────────────────────────


def clean_code_from_db(source_code: str) -> str:
    try:
        cleaned = codecs.decode(source_code, 'unicode_escape')
        return cleaned
    except Exception:
        cleaned = source_code.replace('\\n', '\n')
        cleaned = cleaned.replace('\\t', '\t')
        cleaned = cleaned.replace('\\r', '\r')
        return cleaned

# ─────────────────────────────────────────
# REMOVE COMMENTS USING TREE-SITTER
# ─────────────────────────────────────────


def remove_comments_universally(code: str, language: str) -> str:
    lang = language.lower().strip()
    lang_module = LANGUAGE_REGISTRY.get(lang)

    if not lang_module:
        code = re.sub(r'//.*|#.*', '', code)
        return code

    try:
        ts_lang = Language(lang_module.language())
        parser = Parser(ts_lang)
        tree = parser.parse(bytes(code, "utf8"))

        comments = []

        def find_comments(node):
            if "comment" in node.type:
                comments.append((node.start_byte, node.end_byte))
            for child in node.children:
                find_comments(child)

        find_comments(tree.root_node)

        code_bytes = bytearray(code, "utf8")
        for start, end in sorted(comments, reverse=True):
            del code_bytes[start:end]

        return code_bytes.decode("utf8", errors="ignore")

    except Exception as e:
        print(f"[Tokenizer] Tree-Sitter cleaning failed for {language}: {e}")
        return code

# ─────────────────────────────────────────
# NORMALIZATION
# ─────────────────────────────────────────


def normalize_code(source_code: str, language: str = 'python') -> str:
    code = clean_code_from_db(source_code)
    code = remove_comments_universally(code, language)

    # Strip string literals before anything else so their contents don't pollute tokens
    code = re.sub(r'"[^"]*"', 'STR', code)
    code = re.sub(r"'[^']*'", 'STR', code)

    lines = [line.strip() for line in code.splitlines() if line.strip()]
    code = ' '.join(lines)

    def replace_identifier(match):
        word = match.group(0)
        if word in UNIVERSAL_KEYWORDS:
            return word
        return 'VAR'

    code = re.sub(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', replace_identifier, code)

    # Strip all punctuation/symbols so only clean tokens remain
    code = re.sub(r'[(){}\[\];,.:"\']', ' ', code)

    return code

# ─────────────────────────────────────────
# TOKENIZATION
# ─────────────────────────────────────────


@lru_cache(maxsize=10000)
def tokenize(source_code: str, language: str = 'python') -> tuple:
    normalized = normalize_code(source_code, language)
    # Filter out empty strings from split
    return tuple([t for t in normalized.split() if t])

# ─────────────────────────────────────────
# ORIGINAL K-GRAM (optional - kept for hybrid use)
# ─────────────────────────────────────────


def get_fingerprint(tokens: List[str], k: int = 3) -> set:
    fingerprint = set()
    for i in range(len(tokens) - k + 1):
        kgram = tuple(tokens[i:i+3])
        fingerprint.add(kgram)
    return fingerprint

# ─────────────────────────────────────────
# WINNOWING IMPLEMENTATION
# ─────────────────────────────────────────


def hash_kgram(kgram: tuple) -> int:
    kgram_str = ' '.join(kgram)
    return int(hashlib.md5(kgram_str.encode()).hexdigest(), 16)


def winnowing(tokens: List[str], k: int = 12, window_size: int = 4) -> set:
    if len(tokens) < k:
        return set()

    hashes = []
    for i in range(len(tokens) - k + 1):
        kgram = tuple(tokens[i:i+k])
        hashes.append(hash_kgram(kgram))

    fingerprints = set()
    for i in range(len(hashes) - window_size + 1):
        window = hashes[i:i+window_size]
        fingerprints.add(min(window))

    return fingerprints

# ─────────────────────────────────────────
# SIMILARITY FUNCTION (UPDATED)
# ─────────────────────────────────────────


def token_similarity_percent(code_a: str, code_b: str, language: str = 'python') -> float:
    tokens_a = tokenize(code_a, language)
    tokens_b = tokenize(code_b, language)

    if not tokens_a or not tokens_b:
        return 0.0

    # 🔥 Use Winnowing instead of raw k-grams
    fingerprint_a = winnowing(tokens_a)
    fingerprint_b = winnowing(tokens_b)

    intersection = fingerprint_a & fingerprint_b
    union = fingerprint_a | fingerprint_b

    if not union:
        return 0.0

    score = (len(intersection) / len(union)) * 100
    return round(score, 2)
