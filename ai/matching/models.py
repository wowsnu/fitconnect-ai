"""
Data models for matching service - Pure Python
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class MatchingScore:
    """Individual matching score result"""
    score: float
    cosine_similarity: float
    euclidean_distance: float
    alpha: float
    beta: float


@dataclass
class MatchingResult:
    """Result of matching between job and applicant"""
    job_id: str
    applicant_id: str
    score: float
    cosine_similarity: float
    euclidean_distance: float
    rank: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RecommendationResult:
    """Recommendation result with top N matches"""
    applicant_id: str
    matches: List[MatchingResult]
    total_candidates: int
    filters_applied: Optional[Dict[str, Any]] = None


@dataclass
class MatchingHealth:
    """Health status of matching service"""
    service_status: str
    algorithm_loaded: bool
    default_params: Dict[str, float]