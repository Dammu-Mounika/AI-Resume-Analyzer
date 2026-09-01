"""
Keyword match, semantic similarity, and overall job match scoring.
"""

from dataclasses import dataclass
from typing import Any, Dict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Configurable scoring weights (must sum to 1.0)
KEYWORD_WEIGHT = 0.70
SEMANTIC_WEIGHT = 0.30


@dataclass
class ScoreResult:
    """Combined scoring output."""

    keyword_score: float
    semantic_score: float
    overall_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "keyword_score": self.keyword_score,
            "semantic_score": self.semantic_score,
            "overall_score": self.overall_score,
        }


def calculate_semantic_similarity(resume_text: str, job_description: str) -> float:
    """
    Compute semantic similarity using TF-IDF + cosine similarity.

    Returns a score from 0 to 100.
    """
    if not resume_text.strip() or not job_description.strip():
        return 0.0

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=5000,
        )
        tfidf_matrix = vectorizer.fit_transform([resume_text, job_description])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return round(max(0.0, min(1.0, float(similarity))) * 100, 1)
    except ValueError:
        return 0.0


def calculate_overall_score(keyword_score: float, semantic_score: float) -> ScoreResult:
    """
    Calculate overall Job Match Score using weighted formula:

    Overall = (70% × Keyword Match) + (30% × Semantic Similarity)
    """
    keyword = round(float(keyword_score), 1)
    semantic = round(float(semantic_score), 1)
    overall = round((KEYWORD_WEIGHT * keyword) + (SEMANTIC_WEIGHT * semantic), 1)

    return ScoreResult(
        keyword_score=keyword,
        semantic_score=semantic,
        overall_score=overall,
    )
