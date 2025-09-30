"""
LLM 응답 처리 유틸리티 함수들
"""

import json
import re
from typing import Any, Dict, Optional


def clean_json_response(response_text: str) -> str:
    """
    LLM 응답에서 JSON 추출 및 정리
    마크다운 코드 블록 제거, 주석 제거 등
    """
    # 1. 마크다운 코드 블록 제거 (```json ... ``` 또는 ``` ... ```)
    cleaned = re.sub(r'```(?:json\s*)?\n?(.*?)\n?```', r'\1', response_text, flags=re.DOTALL)

    # 2. 앞뒤 공백 제거
    cleaned = cleaned.strip()

    # 3. 주석 제거 (// 주석)
    lines = cleaned.split('\n')
    cleaned_lines = []
    for line in lines:
        # // 주석 제거 (단, 문자열 내부는 제외)
        if '//' in line and not ('"' in line and line.find('//') > line.find('"')):
            line = line[:line.find('//')]
        cleaned_lines.append(line)

    cleaned = '\n'.join(cleaned_lines)

    return cleaned


def parse_llm_json_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    LLM 응답을 JSON으로 파싱
    실패 시 None 반환
    """
    try:
        # 1. 응답 정리
        cleaned = clean_json_response(response_text)

        # 2. JSON 파싱 시도
        return json.loads(cleaned)

    except json.JSONDecodeError as e:
        print(f"JSON 파싱 오류: {e}")
        print(f"정리된 텍스트: {cleaned[:200]}...")
        return None
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return None


def safe_get_from_dict(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    딕셔너리에서 안전하게 값 가져오기
    빈 값도 기본값으로 처리
    """
    value = data.get(key, default)

    # 빈 문자열, 빈 리스트도 기본값으로 처리
    if value == "" or value == [] or value is None:
        return default

    return value


def format_list_display(items: list, max_items: int = 3) -> str:
    """
    리스트를 화면 표시용으로 포맷팅
    """
    if not items:
        return "없음"

    if len(items) <= max_items:
        return ', '.join(items)
    else:
        displayed = ', '.join(items[:max_items])
        return f"{displayed}... (+{len(items) - max_items}개)"


def format_text_display(text: str, max_length: int = 100) -> str:
    """
    긴 텍스트를 화면 표시용으로 포맷팅
    """
    if not text or text.strip() == "":
        return "없음"

    text = text.strip()
    if len(text) <= max_length:
        return text
    else:
        return text[:max_length] + "..."