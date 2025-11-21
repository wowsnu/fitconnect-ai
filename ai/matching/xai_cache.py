"""
XAI cache integration with main FitConnect backend.

AI 서비스는 LangGraph 결과를 생성한 뒤, 백엔드의 내부 캐시 API
`PUT /internal/xai/match-cache` 로 업서트한다.
"""

import logging
from typing import Any, Dict, Optional

import httpx

from config.settings import get_settings

logger = logging.getLogger(__name__)


async def fetch_cache_from_backend(
    talent_id: int,
    jd_id: int,
) -> Optional[Dict[str, Any]]:
    """
    Try to fetch cached XAI result from backend.
    Returns response_json dict on hit, or None on miss/error.
    """
    settings = get_settings()
    url = f"{settings.BACKEND_API_URL.rstrip('/')}/internal/xai/match-cache"
    params = {"talent_id": talent_id, "jd_id": jd_id}

    try:
        timeout = httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 404:
                return None
            if resp.status_code != 200:
                logger.warning(f"[XAI] Cache GET failed {resp.status_code}: {resp.text}")
                return None

            data = resp.json()
            # Accept flexible response shapes: {response_json: {...}} or {data: {...}} etc.
            candidate = data.get("data", data)
            response_json = (
                candidate.get("response_json")
                or candidate.get("response")
                or candidate.get("final_explanation")
            )
            if response_json:
                logger.info(f"[XAI] Cache hit from backend (talent_id={talent_id}, jd_id={jd_id})")
                return response_json
            return None
    except Exception as e:
        logger.warning(f"[XAI] Cache GET exception: {e}")
        return None


def build_cache_payload(
    talent_id: int,
    jd_id: int,
    request_json: Dict[str, Any],
    response_json: Dict[str, Any],
    model_version: Optional[str] = None,
    lang: Optional[str] = "ko",
) -> Dict[str, Any]:
    settings = get_settings()
    return {
        "talent_id": talent_id,
        "jd_id": jd_id,
        "request_json": request_json,
        "response_json": response_json,
        "model_version": model_version or getattr(settings, "XAI_MODEL_VERSION", "v1"),
        "lang": lang or "ko",
    }


async def save_cache_to_backend(
    talent_id: int,
    jd_id: int,
    request_json: Dict[str, Any],
    response_json: Dict[str, Any],
    model_version: Optional[str] = None,
    lang: Optional[str] = "ko",
) -> bool:
    """
    Call backend cache API to upsert XAI result.

    Returns:
        True on success, False on failure (errors are logged, not raised).
    """
    settings = get_settings()
    url = f"{settings.BACKEND_API_URL.rstrip('/')}/internal/xai/match-cache"

    payload = build_cache_payload(
        talent_id=talent_id,
        jd_id=jd_id,
        request_json=request_json,
        response_json=response_json,
        model_version=model_version,
        lang=lang,
    )

    try:
        timeout = httpx.Timeout(connect=10.0, read=20.0, write=20.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.put(url, json=payload)
            if resp.status_code not in (200, 201):
                logger.warning(
                    f"[XAI] Cache PUT failed {resp.status_code}: {resp.text}"
                )
                return False
            logger.info(
                f"[XAI] Cache saved to backend (talent_id={talent_id}, jd_id={jd_id})"
            )
            return True
    except Exception as e:
        logger.warning(f"[XAI] Cache PUT exception: {e}")
        return False
