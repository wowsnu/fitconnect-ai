"""
Matching service implementation using cosine similarity + euclidean distance
Score = α × cosine(u,v) − β × ||u−v||
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances

from .models import MatchingScore, MatchingResult, RecommendationResult, MatchingHealth

logger = logging.getLogger(__name__)


class MatchingService:
    """Vector-based matching service for jobs and applicants"""

    def __init__(self, alpha: float = 0.7, beta: float = 0.3):
        """
        Initialize matching service

        Args:
            alpha: Weight for cosine similarity (역량별 가중치)
            beta: Weight for euclidean distance (절대적 역량 크기)
        """
        self.alpha = alpha
        self.beta = beta
        self.default_params = {"alpha": alpha, "beta": beta}

        logger.info(f"MatchingService initialized with alpha={alpha}, beta={beta}")

    def calculate_similarity_score(
        self,
        job_vector: List[float],
        applicant_vector: List[float],
        alpha: Optional[float] = None,
        beta: Optional[float] = None
    ) -> MatchingScore:
        """
        Calculate matching score between job and applicant vectors
        Score = α × cosine(u,v) − β × ||u−v||

        Args:
            job_vector: Job vector (company + required skills)
            applicant_vector: Applicant vector (preferences + skills)
            alpha: Weight for cosine similarity (default: self.alpha)
            beta: Weight for euclidean distance (default: self.beta)

        Returns:
            MatchingScore object with detailed metrics
        """
        try:
            alpha = alpha or self.alpha
            beta = beta or self.beta

            # Convert to numpy arrays
            job_vec = np.array(job_vector).reshape(1, -1)
            applicant_vec = np.array(applicant_vector).reshape(1, -1)

            # Check dimension compatibility
            if job_vec.shape[1] != applicant_vec.shape[1]:
                raise ValueError(f"Vector dimension mismatch: job={job_vec.shape[1]}, applicant={applicant_vec.shape[1]}")

            # Calculate cosine similarity
            cos_sim = cosine_similarity(job_vec, applicant_vec)[0, 0]

            # Calculate euclidean distance
            eucl_dist = euclidean_distances(job_vec, applicant_vec)[0, 0]

            # Calculate final score: α × cosine(u,v) − β × ||u−v||
            score = alpha * cos_sim - beta * eucl_dist

            logger.debug(f"Similarity calculated - Cosine: {cos_sim:.4f}, Euclidean: {eucl_dist:.4f}, Score: {score:.4f}")

            return MatchingScore(
                score=score,
                cosine_similarity=cos_sim,
                euclidean_distance=eucl_dist,
                alpha=alpha,
                beta=beta
            )

        except Exception as e:
            logger.error(f"Failed to calculate similarity score: {e}")
            raise

    def match_single(
        self,
        job_vector: List[float],
        applicant_vector: List[float],
        job_id: str,
        applicant_id: str,
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MatchingResult:
        """
        Match single job and applicant

        Returns:
            MatchingResult object
        """
        try:
            score_result = self.calculate_similarity_score(
                job_vector, applicant_vector, alpha, beta
            )

            return MatchingResult(
                job_id=job_id,
                applicant_id=applicant_id,
                score=score_result.score,
                cosine_similarity=score_result.cosine_similarity,
                euclidean_distance=score_result.euclidean_distance,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Failed to match single pair: {e}")
            raise

    def match_batch(
        self,
        job_vectors: List[List[float]],
        applicant_vector: List[float],
        job_ids: List[str],
        applicant_id: str,
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
        top_n: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> RecommendationResult:
        """
        Match applicant against multiple jobs and return top N recommendations

        Args:
            job_vectors: List of job vectors
            applicant_vector: Single applicant vector
            job_ids: List of job IDs corresponding to job_vectors
            applicant_id: Applicant ID
            alpha: Weight for cosine similarity
            beta: Weight for euclidean distance
            top_n: Number of top matches to return (default: all)
            filters: Additional filtering criteria

        Returns:
            RecommendationResult with ranked matches
        """
        try:
            if len(job_vectors) != len(job_ids):
                raise ValueError("Number of job vectors must match number of job IDs")

            matches = []

            # Calculate matching scores for all jobs
            for i, (job_vector, job_id) in enumerate(zip(job_vectors, job_ids)):
                try:
                    match_result = self.match_single(
                        job_vector=job_vector,
                        applicant_vector=applicant_vector,
                        job_id=job_id,
                        applicant_id=applicant_id,
                        alpha=alpha,
                        beta=beta
                    )
                    matches.append(match_result)

                except Exception as e:
                    logger.warning(f"Failed to match job {job_id}: {e}")
                    continue

            # Sort by score (descending)
            matches.sort(key=lambda x: x.score, reverse=True)

            # Add rank information
            for rank, match in enumerate(matches, 1):
                match.rank = rank

            # Apply top_n filter if specified
            if top_n:
                matches = matches[:top_n]

            logger.info(f"Batch matching completed - {len(matches)} matches for applicant {applicant_id}")

            return RecommendationResult(
                applicant_id=applicant_id,
                matches=matches,
                total_candidates=len(job_vectors),
                filters_applied=filters
            )

        except Exception as e:
            logger.error(f"Failed to perform batch matching: {e}")
            raise

    def match_reverse_batch(
        self,
        job_vector: List[float],
        applicant_vectors: List[List[float]],
        job_id: str,
        applicant_ids: List[str],
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
        top_n: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MatchingResult]:
        """
        Match job against multiple applicants and return top N candidates

        Args:
            job_vector: Single job vector
            applicant_vectors: List of applicant vectors
            job_id: Job ID
            applicant_ids: List of applicant IDs
            alpha: Weight for cosine similarity
            beta: Weight for euclidean distance
            top_n: Number of top matches to return
            filters: Additional filtering criteria

        Returns:
            List of MatchingResult objects, ranked by score
        """
        try:
            if len(applicant_vectors) != len(applicant_ids):
                raise ValueError("Number of applicant vectors must match number of applicant IDs")

            matches = []

            # Calculate matching scores for all applicants
            for applicant_vector, applicant_id in zip(applicant_vectors, applicant_ids):
                try:
                    match_result = self.match_single(
                        job_vector=job_vector,
                        applicant_vector=applicant_vector,
                        job_id=job_id,
                        applicant_id=applicant_id,
                        alpha=alpha,
                        beta=beta
                    )
                    matches.append(match_result)

                except Exception as e:
                    logger.warning(f"Failed to match applicant {applicant_id}: {e}")
                    continue

            # Sort by score (descending)
            matches.sort(key=lambda x: x.score, reverse=True)

            # Add rank information
            for rank, match in enumerate(matches, 1):
                match.rank = rank

            # Apply top_n filter if specified
            if top_n:
                matches = matches[:top_n]

            logger.info(f"Reverse batch matching completed - {len(matches)} matches for job {job_id}")

            return matches

        except Exception as e:
            logger.error(f"Failed to perform reverse batch matching: {e}")
            raise

    def apply_structural_filters(
        self,
        matches: List[MatchingResult],
        filters: Dict[str, Any]
    ) -> List[MatchingResult]:
        """
        Apply structural filtering (experience years, position level, etc.)

        Args:
            matches: List of matching results
            filters: Filtering criteria

        Returns:
            Filtered list of matches
        """
        try:
            filtered_matches = matches.copy()

            # This is a placeholder for structural filtering logic
            # In real implementation, you would filter based on:
            # - Required years of experience
            # - Position level
            # - Education requirements
            # - Location preferences
            # - Salary range
            # etc.

            logger.info(f"Structural filtering applied - {len(matches)} -> {len(filtered_matches)} matches")

            return filtered_matches

        except Exception as e:
            logger.error(f"Failed to apply structural filters: {e}")
            raise

    def update_parameters(self, alpha: float, beta: float):
        """Update matching parameters"""
        self.alpha = alpha
        self.beta = beta
        self.default_params = {"alpha": alpha, "beta": beta}
        logger.info(f"Parameters updated - alpha={alpha}, beta={beta}")

    def health_check(self) -> MatchingHealth:
        """Check service health"""
        return MatchingHealth(
            service_status="healthy",
            algorithm_loaded=True,
            default_params=self.default_params
        )


# Global service instance
matching_service = MatchingService()


def get_matching_service() -> MatchingService:
    """Get global matching service instance"""
    return matching_service