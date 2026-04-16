# The Entry Point: Setting up the Internet Server
from fastapi import FastAPI, HTTPException
from collections import defaultdict
from models.schemas import (
    PlagiarismRequest,
    PlagiarismResponse,
    PairResult,
    QuestionSummary
)
from db.neon import fetch_submissions
from detection.scorer import run_plagiarism_check

# Declares that this python file is a web server waiting for traffic
app = FastAPI(
    title="Plagiarism Detection Service",
    description="Detects plagiarism with ring detection for Python, Java and JavaScript",
    version="3.0.0"
)

@app.get("/")
def health_check():
    # If someone pings the root of your IP address, it just replies "I am alive"
    return {
        "status":   "Plagiarism service is running",
        "version":  "3.0.0",
        "features": [
            "Token-based similarity",
            "AST structural analysis",
            "Smart copy detection"
        ]
    }


# The Plagiarism Endpoint: Orchestrates the entire checking process
@app.post("/check-plagiarism", response_model=PlagiarismResponse)
def check_plagiarism(request: PlagiarismRequest):

    # 1. Grab DB Submissions (Runs neon.py fetching the database rows)
    submissions = fetch_submissions(request.batch_id)

    if not submissions:
        raise HTTPException(
            status_code=404,
            detail=f"No submissions found for batch_id: {request.batch_id}"
        )

    print(f"\nRunning plagiarism check for batch: {request.batch_id}")
    print(f"Total submissions: {len(submissions)}")

    # 2. Run the Comparison (Runs scorer.py which triggers tokenizer.py & ast_comparator.py)
    raw_results  = run_plagiarism_check(submissions)
    pair_results = [PairResult(**r) for r in raw_results]

    # 3. Math. Count up the exact copies across the question to create a "Dashboard Summary" for the Recruiter UI.
    by_question = defaultdict(list)
    for r in raw_results:
        by_question[r["question_id"]].append(r)

    summaries = []
    for qid, pairs in sorted(by_question.items()):
        # FIX 4: Derive summary counts from the assigned label (which reflects BOTH engines)
        # Previously, this block ignored the AST signal entirely by calculating
        # buckets using only 'token_similarity_pct'.
        summaries.append(QuestionSummary(
            question_id                 = qid,
            total_pairs_checked         = len(pairs),
            exact_match                 = sum(1 for p in pairs if p["label"] == "Exact match"),
            near_identical_text         = sum(1 for p in pairs if p["label"] == "Near-identical text"),
            high_token_overlap          = sum(1 for p in pairs if p["label"] == "High token overlap"),
            low_text_high_structure     = sum(1 for p in pairs if p["label"] == "Low text overlap, high structural similarity"),
            moderate_structural_textual = sum(1 for p in pairs if p["label"] == "Moderate similarity — structural and textual"),
            moderate_text_similarity    = sum(1 for p in pairs if p["label"] == "Moderate text similarity"),
            slight_text_similarity      = sum(1 for p in pairs if p["label"] == "Slight text similarity"),
        ))

    total_pairs = sum(len(v) for v in by_question.values())
    print(f"Total pairs checked: {total_pairs}")

    # 4. Returning the final Payload to the internet!
    # This enforces the rule that we only spit out the Batch ID, Summaries, and specific Pairs requested by the Node.js app.
    return PlagiarismResponse(
        batch_id            = request.batch_id,
        total_submissions   = len(submissions),
        total_pairs_checked = total_pairs,
        summary_by_question = summaries,
        results             = pair_results
    )