"""
Matching Service Module for FitConnect AI
Vector-based matching using cosine similarity + euclidean distance
"""

from .service import MatchingService, get_matching_service
from .models import MatchingScore, MatchingResult, RecommendationResult, MatchingHealth

__version__ = "1.0.0"
__author__ = "FitConnect AI Team"

__all__ = [
    "MatchingService",
    "get_matching_service",
    "MatchingScore",
    "MatchingResult",
    "RecommendationResult",
    "MatchingHealth"
]