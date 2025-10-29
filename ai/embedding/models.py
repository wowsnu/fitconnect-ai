"""
Data models for embedding service - Pure Python (no Pydantic/FastAPI dependencies)
"""

from typing import List, Optional, Dict, Any, NamedTuple
from dataclasses import dataclass


@dataclass
class EmbeddingResult:
    """Result of text embedding"""
    embedding: List[float]
    model: str
    dimension: int


@dataclass
class VectorResult:
    """Result of job/applicant vector creation"""
    general_vector: List[float]
    skills_vector: List[float]
    combined_vector: List[float]
    model: str
    dimension: int


@dataclass
class EmbeddingHealth:
    """Health status of embedding service"""
    service_status: str
    available_models: List[str]
    model_status: Dict[str, bool]
    device: str