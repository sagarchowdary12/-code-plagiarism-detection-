from detection.scorer import run_plagiarism_check

print("\n" + "=" * 100)
print(" " * 30 + "CODE PLAGIARISM DETECTION DEMO")
print(" " * 25 + "Showcasing All 7 Detection Categories")
print("=" * 100)

# ═══════════════════════════════════════════════════════════════════════════════
# CASE 1: EXACT COPY (100% Token, 100% AST)
# Two students submitted identical Python code
# ═══════════════════════════════════════════════════════════════════════════════

submissions_case1 = [
    {
        "candidate_id": "alice", "question_id": "q1_sum", "language": "python",
        "source_code": """
def calculate_sum(a, b):
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both arguments must be numbers")
    result = a + b
    return result
"""
    },
    {
        "candidate_id": "bob", "question_id": "q1_sum", "language": "python",
        "source_code": """
def calculate_sum(a, b):
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both arguments must be numbers")
    result = a + b
    return result
"""
    },
]

print("\n" + "─" * 100)
print("CASE 1: EXACT COPY [HIGH RISK - Python]")
print("─" * 100)
print("\n📝 ALICE'S CODE:")
print(submissions_case1[0]["source_code"])
print("\n📝 BOB'S CODE:")
print(submissions_case1[1]["source_code"])
print("\n🔍 ANALYSIS:")

results = run_plagiarism_check(submissions_case1)
if results:
    r = results[0]
    print(f"   Token Similarity: {r['token_similarity_pct']}%")
    print(f"   AST Similarity:   {r['ast_similarity_pct']}%")
    print(f"   ⚠️  VERDICT: {r['label']}")
else:
    print("   ✓ No plagiarism detected")

# ═══════════════════════════════════════════════════════════════════════════════
# CASE 2: ALMOST IDENTICAL (90%+ Token)
# Student added one extra line but otherwise identical
# ═══════════════════════════════════════════════════════════════════════════════

submissions_case2 = [
    {
        "candidate_id": "charlie", "question_id": "q2_max", "language": "java",
        "source_code": """
public class Solution {
    public int findMax(int[] arr) {
        int max = arr[0];
        for (int i = 1; i < arr.length; i++) {
            if (arr[i] > max) {
                max = arr[i];
            }
        }
        return max;
    }
}
"""
    },
    {
        "candidate_id": "diana", "question_id": "q2_max", "language": "java",
        "source_code": """
public class Solution {
    public int findMax(int[] arr) {
        int max = arr[0];
        for (int i = 1; i < arr.length; i++) {
            if (arr[i] > max) {
                max = arr[i];
            }
        }
        System.out.println(max);
        return max;
    }
}
"""
    },
]

print("\n" + "─" * 100)
print("CASE 2: ALMOST IDENTICAL [HIGH RISK - Java]")
print("─" * 100)
print("\n📝 CHARLIE'S CODE:")
print(submissions_case2[0]["source_code"])
print("\n📝 DIANA'S CODE:")
print(submissions_case2[1]["source_code"])
print("\n🔍 ANALYSIS:")

results = run_plagiarism_check(submissions_case2)
if results:
    r = results[0]
    print(f"   Token Similarity: {r['token_similarity_pct']}%")
    print(f"   AST Similarity:   {r['ast_similarity_pct']}%")
    print(f"   ⚠️  VERDICT: {r['label']}")
else:
    print("   ✓ No plagiarism detected")

# ═══════════════════════════════════════════════════════════════════════════════
# CASE 3: HIGHLY SIMILAR (75-89% Token)
# Renamed variables but same structure
# ═══════════════════════════════════════════════════════════════════════════════

submissions_case3 = [
    {
        "candidate_id": "eve", "question_id": "q3_palindrome", "language": "javascript",
        "source_code": """
function isPalindrome(str) {
    let left = 0;
    let right = str.length - 1;
    while (left < right) {
        if (str[left] !== str[right]) {
            return false;
        }
        left++;
        right--;
    }
    return true;
}
"""
    },
    {
        "candidate_id": "frank", "question_id": "q3_palindrome", "language": "javascript",
        "source_code": """
function checkPalindrome(text) {
    let start = 0;
    let end = text.length - 1;
    while (start < end) {
        if (text[start] !== text[end]) {
            return false;
        }
        start++;
        end--;
    }
    return true;
}
"""
    },
]

print("\n" + "─" * 100)
print("CASE 3: HIGHLY SIMILAR [MEDIUM RISK - JavaScript]")
print("─" * 100)
print("\n📝 EVE'S CODE:")
print(submissions_case3[0]["source_code"])
print("\n📝 FRANK'S CODE:")
print(submissions_case3[1]["source_code"])
print("\n🔍 ANALYSIS:")

results = run_plagiarism_check(submissions_case3)
if results:
    r = results[0]
    print(f"   Token Similarity: {r['token_similarity_pct']}%")
    print(f"   AST Similarity:   {r['ast_similarity_pct']}%")
    print(f"   ⚠️  VERDICT: {r['label']}")
else:
    print("   ✓ No plagiarism detected")

# ═══════════════════════════════════════════════════════════════════════════════
# CASE 4: SMART COPY — LOGIC IDENTICAL (<75% Token, 95%+ AST)
# THE WORST KIND - Student added dummy prints to hide but kept exact logic
# ═══════════════════════════════════════════════════════════════════════════════

submissions_case4 = [
    {
        "candidate_id": "grace", "question_id": "q4_even", "language": "python",
        "source_code": """
def find_even(numbers):
    for num in numbers:
        if num % 2 == 0:
            return True
    return False
"""
    },
    {
        "candidate_id": "henry", "question_id": "q4_even", "language": "python",
        "source_code": """
def check_digits(random_array):
    print("Starting search...")
    for dummy_val in random_array:
        print("Checking value...")
        if dummy_val % 2 == 0:
            return True
    print("No even found")
    return False
"""
    },
]

print("\n" + "─" * 100)
print(
    "CASE 4: SMART COPY — LOGIC IDENTICAL [HIGH RISK - Python] ⚠️  WORST TYPE!")
print("─" * 100)
print("\n📝 GRACE'S CODE:")
print(submissions_case4[0]["source_code"])
print("\n📝 HENRY'S CODE:")
print(submissions_case4[1]["source_code"])
print("\n🔍 ANALYSIS:")

results = run_plagiarism_check(submissions_case4)
if results:
    r = results[0]
    print(f"   Token Similarity: {r['token_similarity_pct']}%")
    print(f"   AST Similarity:   {r['ast_similarity_pct']}%")
    print(f"   ⚠️  VERDICT: {r['label']}")
    print("   � NOTE: Low token similarity but moderate structural overlap")
    print("          Traditional tools would miss this case!")
else:
    print("   ✓ No plagiarism detected")

# ═══════════════════════════════════════════════════════════════════════════════
# CASE 5: SUSPICIOUS — HIGH STRUCTURAL OVERLAP (50%+ Token, 75%+ AST)
# ═══════════════════════════════════════════════════════════════════════════════

submissions_case5 = [
    {
        "candidate_id": "iris", "question_id": "q5_count", "language": "cpp",
        "source_code": """
int countVowels(string s) {
    string vowels = "aeiou";
    int count = 0;
    for (char c : s) {
        if (vowels.find(c) != string::npos) {
            count++;
        }
    }
    return count;
}
"""
    },
    {
        "candidate_id": "jack", "question_id": "q5_count", "language": "cpp",
        "source_code": """
int countVowels(string text) {
    string vowel_list = "aeiou";
    int total = 0;
    for (char letter : text) {
        if (vowel_list.find(letter) != string::npos) {
            total++;
        }
    }
    return total;
}
"""
    },
]

print("\n" + "─" * 100)
print("CASE 5: SUSPICIOUS — HIGH STRUCTURAL OVERLAP [MEDIUM RISK - C++]")
print("─" * 100)
print("\n📝 IRIS'S CODE:")
print(submissions_case5[0]["source_code"])
print("\n📝 JACK'S CODE:")
print(submissions_case5[1]["source_code"])
print("\n🔍 ANALYSIS:")

results = run_plagiarism_check(submissions_case5)
if results:
    r = results[0]
    print(f"   Token Similarity: {r['token_similarity_pct']}%")
    print(f"   AST Similarity:   {r['ast_similarity_pct']}%")
    print(f"   ⚠️  VERDICT: {r['label']}")
else:
    print("   ✓ No plagiarism detected")

# ═══════════════════════════════════════════════════════════════════════════════
# CASE 6: MODERATELY SIMILAR (50%+ Token, <75% AST)
# ═══════════════════════════════════════════════════════════════════════════════

submissions_case6 = [
    {
        "candidate_id": "kate", "question_id": "q6_factorial", "language": "rust",
        "source_code": """
fn factorial(n: u32) -> u32 {
    let mut result = 1;
    for i in 1..=n {
        result *= i;
    }
    result
}
"""
    },
    {
        "candidate_id": "leo", "question_id": "q6_factorial", "language": "rust",
        "source_code": """
fn factorial(n: u32) -> u32 {
    if n == 0 {
        return 1;
    }
    let mut result = 1;
    for i in 1..=n {
        result *= i;
    }
    result
}
"""
    },
]

print("\n" + "─" * 100)
print("CASE 6: MODERATELY SIMILAR [LOW RISK - Rust]")
print("─" * 100)
print("\n📝 KATE'S CODE:")
print(submissions_case6[0]["source_code"])
print("\n📝 LEO'S CODE:")
print(submissions_case6[1]["source_code"])
print("\n🔍 ANALYSIS:")

results = run_plagiarism_check(submissions_case6)
if results:
    r = results[0]
    print(f"   Token Similarity: {r['token_similarity_pct']}%")
    print(f"   AST Similarity:   {r['ast_similarity_pct']}%")
    print(f"   ⚠️  VERDICT: {r['label']}")
else:
    print("   ✓ No plagiarism detected")

# ═══════════════════════════════════════════════════════════════════════════════
# CASE 7: SLIGHTLY SIMILAR (25%+ Token, 50%+ AST)
# Different approaches to same problem
# ═══════════════════════════════════════════════════════════════════════════════

submissions_case7 = [
    {
        "candidate_id": "mike", "question_id": "q7_reverse", "language": "go",
        "source_code": """
package main

func reverseString(s string) string {
    runes := []rune(s)
    n := len(runes)
    for i := 0; i < n/2; i++ {
        runes[i], runes[n-1-i] = runes[n-1-i], runes[i]
    }
    return string(runes)
}
"""
    },
    {
        "candidate_id": "nina", "question_id": "q7_reverse", "language": "go",
        "source_code": """
package main

func reverseString(s string) string {
    runes := []rune(s)
    result := make([]rune, len(runes))
    for i, r := range runes {
        result[len(runes)-1-i] = r
    }
    return string(result)
}
"""
    },
]

print("\n" + "─" * 100)
print("CASE 7: SLIGHTLY SIMILAR [LOW RISK - Go]")
print("─" * 100)
print("\n📝 MIKE'S CODE:")
print(submissions_case7[0]["source_code"])
print("\n📝 NINA'S CODE:")
print(submissions_case7[1]["source_code"])
print("\n🔍 ANALYSIS:")

results = run_plagiarism_check(submissions_case7)
if results:
    r = results[0]
    print(f"   Token Similarity: {r['token_similarity_pct']}%")
    print(f"   AST Similarity:   {r['ast_similarity_pct']}%")
    print(f"   ⚠️  VERDICT: {r['label']}")
else:
    print("   ✓ No plagiarism detected")

# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 100)
print(" " * 35 + "DEMO SUMMARY")
print("=" * 100)
print("\n✅ Demonstrated all 7 detection categories across 7 different languages")
print("✅ Showed both token-based and AST-based analysis")
print("\n📊 Risk Level Breakdown:")
print("   🔴 HIGH RISK (Definite plagiarism):     Cases 1, 2, 4")
print("   🟡 MEDIUM RISK (Suspicious):            Cases 3, 5")
print("   🟢 LOW RISK (Likely original):          Cases 6, 7")
print("\n💡 Key Insight:")
print("   Traditional plagiarism tools only check text similarity (token-based).")
print("   Our dual-engine system (Token + AST) catches sophisticated attempts")
print("   where students try to hide plagiarism by adding dummy code or renaming.")
print("\n" + "=" * 100 + "\n")
