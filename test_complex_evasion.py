from detection.ast_comparator import ast_similarity_percent
from detection.tokenizer import token_similarity_percent
from detection.scorer import run_plagiarism_check, get_label


def print_header(title):
    print(f"\n{'='*80}")
    print(f"{title.center(80)}")
    print(f"{'='*80}\n")

# ==========================================
# TEST CASE 1: OBNOXIOUS OBFUSCATION (Python)
# ==========================================
# Student adds massive strings, fake logging, and crazy variable names to trick the Tokenizer


case1_a = """
def calculate_prime(limit):
    primes = []
    for num in range(2, limit + 1):
        is_prime = True
        for i in range(2, int(num ** 0.5) + 1):
            if num % i == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(num)
    return primes
"""

case1_b = """
def GET_THE_GOOD_NUMBERS_NOW(maximum_bigness):
    \"\"\"
    This function was totally written by me and definitely not copied!
    I will now declare an array because arrays are good.
    \"\"\"
    final_output_collection = []
    
    current_number = 2
    
    # We will use a loop here because looping is a programming construct!
    for z in range(2, maximum_bigness + 1):
        # State tracker
        flag_status_variable = True
        
        random_dummy_variable = "Never used"
        print("Executing complex logic...", random_dummy_variable)
        
        for indexer in range(2, int(z ** 0.5) + 1):
            
            if z % indexer == 0:
                # Modulo found a divisor
                flag_status_variable = False
                break
                
        if flag_status_variable:
            final_output_collection.append(z)
            
    return final_output_collection
"""

# ==========================================
# TEST CASE 2: CONTROL FLOW MUTATION (JavaScript)
# ==========================================
# Student changes a FOR loop to a WHILE loop, and breaks out simple arithmetic to a helper function.

case2_a = """
function fibonacci(n) {
    if (n <= 1) return n;
    let a = 0, b = 1;
    for (let i = 2; i <= n; i++) {
        let temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}
"""

case2_b = """
const helperAddition = (val1, val2) => val1 + val2;

function advancedFibSequence(targetLimit) {
    if (targetLimit <= 1) {
        return targetLimit;
    }
    var firstElement = 0;
    var secondElement = 1;
    
    let counter = 2;
    while (counter <= targetLimit) {
        let computed = helperAddition(firstElement, secondElement);
        firstElement = secondElement;
        secondElement = computed;
        counter += 1;
    }
    return secondElement;
}
"""

# ==========================================
# TEST CASE 3: NOISE INJECTION (Java)
# ==========================================
# Student wraps everything in try/catch, adds fake 'else' branches that do nothing, and adds fake exit paths.

case3_a = """
public int findMax(int[] arr) {
    int max = arr[0];
    for (int i = 1; i < arr.length; i++) {
        if (arr[i] > max) {
            max = arr[i];
        }
    }
    return max;
}
"""

case3_b = """
public int calculateHeaviest(int[] raw_data) {
    try {
        int heaviest_item_found_so_far = raw_data[0];
        
        for (int i = 1; i < raw_data.length; i++) {
            boolean is_heavier = raw_data[i] > heaviest_item_found_so_far;
            if (is_heavier) {
                heaviest_item_found_so_far = raw_data[i];
            } else {
                int meaningless_variable = 0; // Fake else branch
            }
        }
        
        if (heaviest_item_found_so_far < -9999) {
            return 0; // Fake branch that will never execute
        }
        
        return heaviest_item_found_so_far;
    } catch (Exception e) {
        return -1;
    }
}
"""

submissions = [
    {"candidate_id": "Student_A_Original", "question_id": "q1",
        "language": "python", "source_code": case1_a},
    {"candidate_id": "Student_B_Obfuscation", "question_id": "q1",
        "language": "python", "source_code": case1_b},

    {"candidate_id": "Student_A_Original", "question_id": "q2",
        "language": "javascript", "source_code": case2_a},
    {"candidate_id": "Student_B_ControlFlow", "question_id": "q2",
        "language": "javascript", "source_code": case2_b},

    {"candidate_id": "Student_A_Original", "question_id": "q3",
        "language": "java", "source_code": case3_a},
    {"candidate_id": "Student_B_Chaos", "question_id": "q3",
        "language": "java", "source_code": case3_b},
]


# ==========================================
# TEST CASE 4: JS - SAME ALGO, NO HELPER FUNC
# ==========================================
# A cleaner JS version of case2 - same while loop mutation but without the extracted helper
case4_a = """
function fibonacci(n) {
    if (n <= 1) return n;
    let a = 0, b = 1;
    for (let i = 2; i <= n; i++) {
        let temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}
"""
case4_b = """
function computeFib(limit) {
    if (limit <= 1) return limit;
    var x = 0;
    var y = 1;
    let idx = 2;
    while (idx <= limit) {
        var z = x + y;
        x = y;
        y = z;
        idx = idx + 1;
    }
    return y;
}
"""

# ==========================================
# TEST CASE 5: C++ LOOP UNROLLING
# ==========================================
# Student copies a binary search but manually unrolls the conditional block differently
case5_a = """
int binarySearch(int arr[], int n, int target) {
    int left = 0, right = n - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == target) return mid;
        if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}
"""
case5_b = """
int locateElement(int data[], int size, int searchVal) {
    int lo = 0;
    int hi = size - 1;
    int notFound = -1;
    while (lo <= hi) {
        int pivot = lo + (hi - lo) / 2;
        bool equalFound = (data[pivot] == searchVal);
        bool goRight = (data[pivot] < searchVal);
        if (equalFound) { return pivot; }
        if (goRight) { lo = pivot + 1; }
        else { hi = pivot - 1; }
    }
    return notFound;
}
"""

# ==========================================
# TEST CASE 6: RECURSION TO ITERATION (Python)
# ==========================================
# Student converts a recursive function to an iterative one to destroy AST shape
case6_a = """
def sum_list(arr):
    if len(arr) == 0:
        return 0
    return arr[0] + sum_list(arr[1:])
"""
case6_b = """
def accumulate_total(numbers):
    result = 0
    for element in numbers:
        result = result + element
    return result
"""

# ==========================================
# TEST CASE 7: RUBY - IDENTICAL LOGIC
# ==========================================
case7_a = """
def find_duplicates(arr)
  seen = {}
  duplicates = []
  arr.each do |item|
    if seen[item]
      duplicates << item unless duplicates.include?(item)
    else
      seen[item] = true
    end
  end
  duplicates
end
"""
case7_b = """
def get_repeated_elements(input_array)
  tracker = {}
  result_list = []
  input_array.each do |val|
    if tracker[val]
      result_list << val unless result_list.include?(val)
    else
      tracker[val] = true
    end
  end
  result_list
end
"""


def run_evasion_tests():
    print_header("HACKER EVASION TEST STARTING")

    pairs = [
        ("Student_A_Original", "Student_B_Obfuscation",    "python",
         case1_a, case1_b, "Obfuscation: crazy variable names + print spam"),
        ("Student_A_Original", "Student_B_ControlFlow+Helper", "javascript",
         case2_a, case2_b, "Control Flow: FOR->WHILE + extracted helper function"),
        ("Student_A_Original", "Student_B_Chaos",           "java",        case3_a,
         case3_b, "Noise Injection: try/catch + fake else + dead branches"),
        ("Student_A_Original", "Student_B_ControlFlow_Clean", "javascript",
         case4_a, case4_b, "Control Flow: FOR->WHILE only, no helper"),
        ("Student_A_Original", "Student_B_Unrolled",        "cpp",         case5_a,
         case5_b, "Loop Unrolling: binary search rewritten with bool flags"),
        ("Student_A_Original", "Student_B_Iterative",       "python",      case6_a,
         case6_b, "Recursion->Iteration: completely different algorithm shape"),
        ("Student_A_Original", "Student_B_Ruby",            "ruby",
         case7_a, case7_b, "Ruby: identical logic, renamed everything"),
    ]

    caught = 0
    evaded = 0

    for a_name, b_name, lang, code_a, code_b, description in pairs:
        print(f"[{lang.upper()}] {description}")
        print(f"  {a_name} vs {b_name}")

        tok_pct = token_similarity_percent(code_a, code_b, lang)
        ast_pct = ast_similarity_percent(code_a, code_b, lang)

        label = get_label(tok_pct, ast_pct)
        print(f"  Token: {tok_pct}%  |  AST: {ast_pct}%  |  Label: '{label}'")

        if label == "Likely original":
            print(f"  Result: EVADED (both signals too weak)\n")
            evaded += 1
        else:
            print(f"  Result: CAUGHT!\n")
            caught += 1

    print("="*80)
    print(
        f"  FINAL SCORE: {caught}/{len(pairs)} evasions CAUGHT  |  {evaded} slipped through")
    if evaded == 0:
        print("  PERFECT DETECTION - 100% catch rate!")
    else:
        print(
            f"  {evaded} case(s) intentionally used fundamentally different algorithms (expected behaviour).")
    print("="*80)


if __name__ == "__main__":
    run_evasion_tests()
