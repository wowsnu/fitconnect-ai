"""
Backend API Client for Interview System
백엔드 API 호출 (인재 프로필, 기업 정보 등)
"""

import httpx
from typing import Optional
from ai.interview.models import CandidateProfile
from config.settings import get_settings


class BackendAPIClient:
    """백엔드 API 호출 클라이언트"""

    def __init__(self, backend_url: Optional[str] = None):
        """
        Args:
            backend_url: 백엔드 API URL (기본값: settings에서 가져옴)
        """
        settings = get_settings()
        self.backend_url = backend_url or settings.BACKEND_API_URL
        self.timeout = 30.0  # 30초 타임아웃

    async def get_talent_profile(self, user_id: int, access_token: str) -> CandidateProfile:
        """
        인재 프로필 조회 (GET /api/me/talent/full)

        Args:
            user_id: 사용자 ID (로깅용)
            access_token: JWT 액세스 토큰

        Returns:
            CandidateProfile

        Raises:
            httpx.HTTPStatusError: API 호출 실패
        """
        url = f"{self.backend_url}/api/me/talent/full"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()

            # 응답 구조: {"ok": true, "data": {...}}
            if not data.get("ok"):
                raise ValueError(f"Backend API returned ok=false: {data}")

            profile_data = data.get("data")
            if not profile_data:
                raise ValueError("Backend API returned empty data")

            # CandidateProfile로 변환
            return CandidateProfile(**profile_data)

    async def get_company_profile(self, user_id: int, access_token: str) -> dict:
        """
        기업 프로필 조회 (GET /api/me/company/)

        Args:
            user_id: 사용자 ID
            access_token: JWT 액세스 토큰

        Returns:
            기업 프로필 dict

        Raises:
            httpx.HTTPStatusError: API 호출 실패
        """
        url = f"{self.backend_url}/api/me/company/"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()

            if not data.get("ok"):
                raise ValueError(f"Backend API returned ok=false: {data}")

            return data.get("data", {})


# 싱글톤 인스턴스
_client_instance = None


def get_backend_client() -> BackendAPIClient:
    """백엔드 클라이언트 싱글톤 인스턴스 반환"""
    global _client_instance
    if _client_instance is None:
        _client_instance = BackendAPIClient()
    return _client_instance
