"""
Text Embedding for Matching Vectors

텍스트를 벡터로 임베딩하여 DB에 저장 가능한 형식으로 변환
"""

from typing import List
from openai import OpenAI
from config.settings import get_settings


class EmbeddingService:
    """텍스트 임베딩 서비스"""

    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "text-embedding-3-small"  # 1536 dimensions

    def embed_text(self, text: str) -> List[float]:
        """
        단일 텍스트를 벡터로 임베딩

        Args:
            text: 임베딩할 텍스트

        Returns:
            벡터 리스트 (1536 dimensions)
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        여러 텍스트를 한 번에 벡터로 임베딩 (배치 처리)

        Args:
            texts: 임베딩할 텍스트 리스트

        Returns:
            벡터 리스트의 리스트
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [data.embedding for data in response.data]


# 싱글톤 인스턴스
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """임베딩 서비스 싱글톤 인스턴스 반환"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def embed_matching_texts(
    roles_text: str,
    skills_text: str,
    growth_text: str,
    career_text: str,
    vision_text: str,
    culture_text: str
) -> dict:
    """
    6가지 매칭 텍스트를 벡터로 임베딩하여 DB 저장 형식으로 변환

    Args:
        roles_text: 역할 적합도 텍스트
        skills_text: 역량 적합도 텍스트
        growth_text: 성장 가능성 텍스트
        career_text: 커리어 방향 텍스트
        vision_text: 비전/협업 텍스트
        culture_text: 조직/문화 적합도 텍스트

    Returns:
        {
            "vector_roles": {"vector": [float, ...]},
            "vector_skills": {"vector": [float, ...]},
            "vector_growth": {"vector": [float, ...]},
            "vector_career": {"vector": [float, ...]},
            "vector_vision": {"vector": [float, ...]},
            "vector_culture": {"vector": [float, ...]}
        }
    """
    service = get_embedding_service()

    # 배치로 한 번에 임베딩 (효율적)
    texts = [
        roles_text,
        skills_text,
        growth_text,
        career_text,
        vision_text,
        culture_text
    ]

    vectors = service.embed_texts(texts)

    # 백엔드 API 스펙에 맞춰 "vector" 키 사용
    return {
        "vector_roles": {"vector": vectors[0]},
        "vector_skills": {"vector": vectors[1]},
        "vector_growth": {"vector": vectors[2]},
        "vector_career": {"vector": vectors[3]},
        "vector_vision": {"vector": vectors[4]},
        "vector_culture": {"vector": vectors[5]}
    }
