"""
Backend API Client for Interview System
백엔드 API 호출 (인재 프로필, 기업 정보 등)
"""

import httpx
from typing import Optional
from ai.interview.talent.models import CandidateProfile
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

    async def get_talent_profile(self, access_token: str) -> CandidateProfile:
        """
        인재 프로필 조회 (GET /api/me/talent/full)

        JWT 토큰으로 현재 사용자를 식별하여 프로필 반환

        Args:
            access_token: JWT 액세스 토큰

        Returns:
            CandidateProfile (profile.basic.user_id에 사용자 ID 포함)

        Raises:
            httpx.HTTPStatusError: API 호출 실패
        """
        url = f"{self.backend_url}/api/me/talent/full"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
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

    async def post_talent_card(self, talent_card_data: dict, access_token: str) -> dict:
        """
        인재 프로필 카드 전송 (POST /api/talent_cards/)

        Args:
            talent_card_data: 백엔드 형식의 카드 데이터
            access_token: JWT 액세스 토큰

        Returns:
            생성된 카드 정보 dict

        Raises:
            httpx.HTTPStatusError: API 호출 실패
        """
        url = f"{self.backend_url}/api/talent_cards/"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.post(url, headers=headers, json=talent_card_data)

            # 409 Conflict: 이미 존재하는 경우 기존 카드 유지
            if response.status_code == 409:
                print(f"[INFO] Talent card already exists for user_id={talent_card_data.get('user_id')}, using existing one")
                return {"id": "existing", "status": "conflict", "message": "Using existing talent card"}

            response.raise_for_status()

            data = response.json()

            if not data.get("ok"):
                raise ValueError(f"Backend API returned ok=false: {data}")

            return data.get("data", {})

    async def post_matching_vectors(self, vectors_data: dict, access_token: str, role: str = "talent") -> dict:
        """
        매칭 벡터 전송 (POST /api/me/matching-vectors)

        Args:
            vectors_data: 매칭 벡터 데이터 (vector_roles, vector_skills, etc.)
            access_token: JWT 액세스 토큰
            role: "talent" 또는 "company"

        Returns:
            저장된 벡터 정보 dict

        Raises:
            httpx.HTTPStatusError: API 호출 실패
        """
        url = f"{self.backend_url}/api/me/matching-vectors"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # role 필드 추가
        payload = {**vectors_data, "role": role}

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.post(url, headers=headers, json=payload)

            # 409 Conflict: 이미 존재하는 경우 기존 벡터 유지
            if response.status_code == 409:
                print(f"[INFO] Matching vector already exists, using existing one")
                return {"id": "existing", "status": "conflict", "message": "Using existing matching vector"}

            response.raise_for_status()

            data = response.json()

            if not data.get("ok"):
                raise ValueError(f"Backend API returned ok=false: {data}")

            return data.get("data", {})

    async def get_company_profile(self, access_token: str) -> dict:
        """
        기업 프로필 가져오기 (GET /api/me/company/)

        Args:
            access_token: JWT 액세스 토큰

        Returns:
            기업 프로필 정보 dict

        Raises:
            httpx.HTTPStatusError: API 호출 실패
        """
        url = f"{self.backend_url}/api/me/company/"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()

            if not data.get("ok"):
                raise ValueError(f"Backend API returned ok=false: {data}")

            return data.get("data", {})

    async def get_job_posting(self, job_posting_id: int, access_token: str) -> dict:
        """
        특정 채용공고 가져오기 (GET /api/me/company/job-postings)

        Args:
            job_posting_id: 채용공고 ID
            access_token: JWT 액세스 토큰

        Returns:
            채용공고 정보 dict

        Raises:
            httpx.HTTPStatusError: API 호출 실패
            ValueError: 채용공고를 찾을 수 없음
        """
        url = f"{self.backend_url}/api/me/company/job-postings"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()

            if not data.get("ok"):
                raise ValueError(f"Backend API returned ok=false: {data}")

            postings = data.get("data", [])

            # job_posting_id로 필터링
            for posting in postings:
                if posting.get("id") == job_posting_id:
                    return posting

            raise ValueError(f"Job posting with id {job_posting_id} not found")

    async def create_job_posting(self, access_token: str, job_posting_data: dict) -> dict:
        """
        채용공고 생성 (POST /api/me/company/job-postings)

        Args:
            access_token: JWT 액세스 토큰
            job_posting_data: 채용공고 데이터 (선택적 필드 포함)

        Returns:
            생성된 채용공고 정보 dict

        Raises:
            httpx.HTTPStatusError: API 호출 실패
            ValueError: API 응답 오류
        """
        url = f"{self.backend_url}/api/me/company/job-postings"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.post(url, headers=headers, json=job_posting_data)

            # 201 Created도 성공으로 처리
            if response.status_code not in [200, 201]:
                error_detail = response.text
                raise ValueError(f"Backend API error {response.status_code}: {error_detail}")

            data = response.json()

            if not data.get("ok"):
                raise ValueError(f"Backend API returned ok=false: {data}")

            return data.get("data", {})

    async def update_job_posting(self, job_posting_id: int, access_token: str, updates: dict) -> dict:
        """
        채용공고 부분 업데이트 (PATCH /api/me/company/job-postings/{posting_id})

        Args:
            job_posting_id: 채용공고 ID
            access_token: JWT 액세스 토큰
            updates: 업데이트할 필드들 (예: {"responsibilities": "...", "competencies": "..."})

        Returns:
            업데이트된 채용공고 정보 dict

        Raises:
            httpx.HTTPStatusError: API 호출 실패
            ValueError: API 응답 오류
        """
        url = f"{self.backend_url}/api/me/company/job-postings/{job_posting_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.patch(url, headers=headers, json=updates)

            if response.status_code not in [200, 201]:
                error_detail = response.text
                raise ValueError(f"Backend API error {response.status_code}: {error_detail}")

            data = response.json()

            if not data.get("ok"):
                raise ValueError(f"Backend API returned ok=false: {data}")

            return data.get("data", {})

    async def create_job_posting_card(self, access_token: str, card_data: dict) -> dict:
        """
        채용공고 카드 생성 (POST /api/job_posting_cards/)

        Args:
            access_token: JWT 액세스 토큰
            card_data: 카드 데이터 (header_title, responsibilities, etc.)

        Returns:
            생성된 카드 정보 dict

        Raises:
            httpx.HTTPStatusError: API 호출 실패
            ValueError: API 응답 오류
        """
        url = f"{self.backend_url}/api/job_posting_cards"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.post(url, headers=headers, json=card_data)

            # 201 Created도 성공으로 처리
            if response.status_code not in [200, 201]:
                error_detail = response.text
                raise ValueError(f"Backend API error {response.status_code}: {error_detail}")

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
