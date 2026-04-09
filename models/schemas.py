from pydantic import BaseModel
from typing import List


class PlagiarismRequest(BaseModel):
    batch_id: str


class PairResult(BaseModel):
    candidate_a:          str
    candidate_b:          str
    question_id:          str
    language:             str
    token_similarity_pct: float
    ast_similarity_pct:   float
    label:                str


class QuestionSummary(BaseModel):
    question_id:         str
    total_pairs_checked: int
    exact_copies:        int
    almost_identical:    int
    highly_similar:      int
    moderately_similar:  int
    slightly_similar:    int


class PlagiarismResponse(BaseModel):
    batch_id:            str
    total_submissions:   int
    total_pairs_checked: int
    summary_by_question: List[QuestionSummary]
    results:             List[PairResult]
