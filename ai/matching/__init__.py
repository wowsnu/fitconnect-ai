"""
Matching Vector Generation Module for FitConnect AI

6가지 매칭 기준별 벡터 임베딩:
1. 역할 적합도/역할 수행력 (vector_roles)
2. 역량 적합도 (vector_skills)
3. 성장 기회 제공/성장 가능성 (vector_growth)
4. 커리어 방향 (vector_career)
5. 비전 신뢰도/협업 기여도 (vector_vision)
6. 조직/문화 적합도 (vector_culture)
"""

from .vector_generator import (
    TalentMatchingTexts,
    generate_talent_matching_texts,
    generate_talent_matching_vectors
)
from .embedding import (
    EmbeddingService,
    get_embedding_service,
    embed_matching_texts
)

__version__ = "2.0.0"
__author__ = "FitConnect AI Team"

__all__ = [
    "TalentMatchingTexts",
    "generate_talent_matching_texts",
    "generate_talent_matching_vectors",
    "EmbeddingService",
    "get_embedding_service",
    "embed_matching_texts"
]