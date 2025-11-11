"""
매칭 벡터 데이터 변환 유틸리티

AI 서버의 벡터/텍스트 형식을 백엔드 API 스펙에 맞게 변환
"""

def convert_to_backend_format(vectors: dict, texts: dict) -> dict:
    """
    AI 서버 형식을 백엔드 API 형식으로 변환
    
    Args:
        vectors: {
            "vector_roles": {"vector": [float, ...]},
            "vector_skills": {"vector": [float, ...]},
            ...
        }
        texts: {
            "roles_text": "텍스트...",
            "skills_text": "텍스트...",
            ...
        }
    
    Returns:
        {
            "vector_roles": {"embedding": [float, ...]},
            "text_roles": "텍스트...",
            "vector_skills": {"embedding": [float, ...]},
            "text_skills": "텍스트...",
            ...
        }
    """
    result = {}
    
    # 6개 차원 매핑
    dimensions = [
        ("roles", "roles_text"),
        ("skills", "skills_text"),
        ("growth", "growth_text"),
        ("career", "career_text"),
        ("vision", "vision_text"),
        ("culture", "culture_text")
    ]
    
    for vector_key, text_key in dimensions:
        # 벡터 변환: {"vector": [...]} → {"embedding": [...]}
        vector_field = f"vector_{vector_key}"
        if vector_field in vectors and "vector" in vectors[vector_field]:
            result[vector_field] = {
                "embedding": vectors[vector_field]["vector"]
            }
        
        # 텍스트 변환: "roles_text" → "text_roles"
        if text_key in texts:
            result[f"text_{vector_key}"] = texts[text_key]
    
    return result
