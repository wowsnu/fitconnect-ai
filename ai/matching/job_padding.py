"""
Job-specific padding text generator.

인재/기업 매칭 텍스트에 동일한 직무 맥락을 추가하여 벡터 유사도를 보정한다.
"""

from typing import Iterable, Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from config.settings import get_settings


def generate_job_padding_text(
    role_name: str,
    perspective: Literal["talent", "company"],
    context_info: str
) -> str:
    """
    직무명을 기반으로 직무 설명 패딩 텍스트를 생성한다.

    Args:
        role_name: 직무명 (예: 백엔드 개발자)
        perspective: "talent" 또는 "company"
        context_info: 직무 관련 참고 정보 (키워드, 요구역량 등)

    Returns:
        패딩 텍스트 (없으면 빈 문자열)
    """
    clean_role = (role_name or "").strip()
    if not clean_role:
        return ""

    perspective_label = "인재 관점" if perspective == "talent" else "기업 관점"
    context_block = (context_info or "").strip() or "관련 정보 부족"

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 채용 매칭을 위한 직무 정보를 만드는 전문가입니다.

주어진 직무명과 참고 정보를 사용해 직무 자체를 설명하는 짧고 밀도 높은 텍스트를 한국어로 작성하세요.

출력 규칙:
- "직무: ..." 형태의 제목 1줄 + 불릿 4~5줄
- 각 불릿에는 핵심 업무, 필요한 기술, 협업 방식, 산업/도메인 맥락 등을 포함
- 직무명과 그 영어 표현/별칭을 2번 이상 언급
- 참고 정보에 있는 키워드가 보이면 자연스럽게 녹여쓰기
- 이 텍스트는 임베딩 패딩용이므로 명확하고 일반적인 표현 사용
- 다른 설명 없이 결과만 출력"""),
        ("user", """## 직무명
{role_name}

## 관점
{perspective_label}

## 참고 정보
{context_block}
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        api_key=settings.OPENAI_API_KEY
    )

    response = (prompt | llm).invoke({
        "role_name": clean_role,
        "perspective_label": perspective_label,
        "context_block": context_block
    })

    return response.content.strip()


def append_padding_to_texts(
    texts: dict[str, str],
    padding: str,
    include_keys: Iterable[str] | None = None
) -> dict[str, str]:
    """
    매칭 텍스트 중 지정된 항목에만 직무 패딩을 추가한다.

    Args:
        texts: {field_name: text} dict
        padding: 덧붙일 텍스트
        include_keys: 패딩을 적용할 필드 목록 (None이면 전체)

    Returns:
        패딩이 적용된 새 dict
    """
    if not padding:
        return texts

    suffix = f"\n\n[직무 패딩]\n{padding}"
    target_keys = set(include_keys) if include_keys else set(texts.keys())

    patched: dict[str, str] = {}
    for key, value in texts.items():
        if key in target_keys:
            patched[key] = f"{value.rstrip()}{suffix}"
        else:
            patched[key] = value
    return patched
