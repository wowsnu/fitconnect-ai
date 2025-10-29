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

        409 에러 발생 시 자동으로 PATCH로 업데이트

        Args:
            talent_card_data: 백엔드 형식의 카드 데이터
            access_token: JWT 액세스 토큰

        Returns:
            생성된 또는 업데이트된 카드 정보 dict

        Raises:
            httpx.HTTPStatusError: API 호출 실패
        """
        url = f"{self.backend_url}/api/talent_cards"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.post(url, headers=headers, json=talent_card_data)

            # 409 Conflict: 이미 존재하는 경우 PATCH로 업데이트
            if response.status_code == 409:
                print(f"[INFO] Talent card already exists. Attempting to update with PATCH...")

                # 409 응답에서 user_id 가져오기
                user_id = talent_card_data.get('user_id')
                if not user_id:
                    raise ValueError("user_id is required for updating talent card")

                # PATCH로 업데이트
                return await self.update_talent_card(
                    user_id=user_id,
                    card_data=talent_card_data,
                    access_token=access_token
                )

            response.raise_for_status()

            data = response.json()

            if not data.get("ok"):
                raise ValueError(f"Backend API returned ok=false: {data}")

            return data.get("data", {})

    async def update_talent_card(self, user_id: int, card_data: dict, access_token: str) -> dict:
        """
        인재 카드 업데이트 (PATCH /api/talent_cards/{user_id})

        Args:
            user_id: 사용자 ID (인재 카드의 식별자)
            card_data: 업데이트할 카드 데이터
            access_token: JWT 액세스 토큰

        Returns:
            업데이트된 카드 정보 dict

        Raises:
            httpx.HTTPStatusError: API 호출 실패
        """
        url = f"{self.backend_url}/api/talent_cards/{user_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.patch(url, headers=headers, json=card_data)

            if response.status_code not in [200, 201]:
                error_detail = response.text
                raise ValueError(f"Backend API error {response.status_code}: {error_detail}")

            data = response.json()

            if not data.get("ok"):
                raise ValueError(f"Backend API returned ok=false: {data}")

            print(f"[INFO] Talent card updated successfully for user_id={user_id}")
            return data.get("data", {})

    async def post_matching_vectors(
        self,
        vectors_data: dict,
        access_token: str,
        role: str = "talent",
        job_posting_id: int = None
    ) -> dict:
        """
        매칭 벡터 전송 (POST /api/me/matching-vectors)

        이미 존재하면 자동으로 PATCH로 업데이트

        Args:
            vectors_data: 매칭 벡터 데이터 (vector_roles, vector_skills, etc.)
            access_token: JWT 액세스 토큰
            role: "talent" 또는 "company"
            job_posting_id: 채용공고 ID (company인 경우 필수)

        Returns:
            저장된 벡터 정보 dict

        Raises:
            httpx.HTTPStatusError: API 호출 실패
            ValueError: company인데 job_posting_id가 없는 경우
        """
        url = f"{self.backend_url}/api/me/matching-vectors"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # role 필드 추가
        payload = {**vectors_data, "role": role}

        # company인 경우 job_posting_id 필수
        if role == "company":
            if not job_posting_id:
                raise ValueError("job_posting_id is required for company role")
            payload["job_posting_id"] = job_posting_id
            print(f"[INFO] Adding job_posting_id={job_posting_id} for company role")
        elif job_posting_id:
            # talent인데 job_posting_id가 있으면 경고
            print(f"[WARNING] job_posting_id provided for talent role, ignoring")

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.post(url, headers=headers, json=payload)

            # 409 Conflict: 이미 존재하는 경우 PATCH로 업데이트
            if response.status_code == 409:
                print(f"[INFO] Matching vector already exists. Attempting to update with PATCH...")

                # 409 응답에서 기존 벡터 ID를 받을 수 있는지 확인
                conflict_data = response.json()
                existing_vector_id = None

                # 백엔드가 기존 벡터 정보를 반환하는 경우
                if conflict_data.get("data") and conflict_data["data"].get("id"):
                    existing_vector_id = conflict_data["data"]["id"]
                    print(f"[INFO] Found existing vector ID from 409 response: {existing_vector_id}")
                else:
                    # 벡터 ID를 찾기 위해 GET 요청
                    print(f"[INFO] Getting existing vector ID from GET request...")
                    existing_vector_id = await self._get_matching_vector_id(access_token, role, job_posting_id)

                if existing_vector_id:
                    # PATCH로 업데이트
                    return await self.update_matching_vectors(
                        matching_vector_id=existing_vector_id,
                        vectors_data=vectors_data,
                        access_token=access_token
                    )
                else:
                    print(f"[WARNING] Could not find existing vector ID. Using existing vector without update.")
                    return {"id": "existing", "status": "conflict", "message": "Using existing matching vector"}

            response.raise_for_status()

            data = response.json()

            if not data.get("ok"):
                raise ValueError(f"Backend API returned ok=false: {data}")

            return data.get("data", {})

    async def update_matching_vectors(
        self,
        matching_vector_id: int,
        vectors_data: dict,
        access_token: str
    ) -> dict:
        """
        매칭 벡터 업데이트 (PATCH /api/me/matching-vectors/{matching_vector_id})

        Args:
            matching_vector_id: 매칭 벡터 ID
            vectors_data: 업데이트할 벡터 데이터
            access_token: JWT 액세스 토큰

        Returns:
            업데이트된 벡터 정보 dict

        Raises:
            httpx.HTTPStatusError: API 호출 실패
        """
        url = f"{self.backend_url}/api/me/matching-vectors/{matching_vector_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.patch(url, headers=headers, json=vectors_data)

            if response.status_code not in [200, 201]:
                error_detail = response.text
                raise ValueError(f"Backend API error {response.status_code}: {error_detail}")

            data = response.json()

            if not data.get("ok"):
                raise ValueError(f"Backend API returned ok=false: {data}")

            print(f"[INFO] Matching vector {matching_vector_id} updated successfully")
            return data.get("data", {})

    async def _get_matching_vector_id(
        self,
        access_token: str,
        role: str,
        job_posting_id: int = None
    ) -> int:
        """
        사용자의 매칭 벡터 ID 조회 (내부 헬퍼 메서드)

        Args:
            access_token: JWT 액세스 토큰
            role: "talent" 또는 "company"
            job_posting_id: 채용공고 ID (company인 경우)

        Returns:
            매칭 벡터 ID (없으면 None)
        """
        # GET /api/me/matching-vectors로 내 벡터 목록 조회
        url = f"{self.backend_url}/api/me/matching-vectors"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)

            if response.status_code != 200:
                print(f"[WARNING] Failed to get matching vectors: {response.status_code}")
                return None

            data = response.json()

            if not data.get("ok"):
                return None

            vectors = data.get("data", [])

            # role과 job_posting_id로 필터링
            for vector in vectors:
                if vector.get("role") == role:
                    if role == "company":
                        if vector.get("job_posting_id") == job_posting_id:
                            return vector.get("id")
                    else:  # talent
                        return vector.get("id")

            return None

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

        409 에러 발생 시 자동으로 PATCH로 업데이트

        Args:
            access_token: JWT 액세스 토큰
            card_data: 카드 데이터 (header_title, responsibilities, etc.)

        Returns:
            생성된 또는 업데이트된 카드 정보 dict

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

            # 409 Conflict: 이미 존재하는 경우 PATCH로 업데이트
            if response.status_code == 409:
                print(f"[INFO] Job posting card already exists. Attempting to update with PATCH...")

                # job_posting_id는 card_data에 포함되어 있어야 함
                job_posting_id = card_data.get('job_posting_id')
                if not job_posting_id:
                    raise ValueError("job_posting_id is required for updating job posting card")

                # PATCH로 업데이트
                return await self.update_job_posting_card(
                    job_posting_id=job_posting_id,
                    access_token=access_token,
                    card_data=card_data
                )

            # 201 Created도 성공으로 처리
            if response.status_code not in [200, 201]:
                error_detail = response.text
                raise ValueError(f"Backend API error {response.status_code}: {error_detail}")

            data = response.json()

            if not data.get("ok"):
                raise ValueError(f"Backend API returned ok=false: {data}")

            return data.get("data", {})

    async def update_job_posting_card(self, job_posting_id: int, access_token: str, card_data: dict) -> dict:
        """
        채용공고 카드 업데이트 (PATCH /api/job_posting_cards/{job_posting_id})

        Args:
            job_posting_id: 채용공고 ID (카드와 1:1 매핑)
            access_token: JWT 액세스 토큰
            card_data: 업데이트할 카드 데이터

        Returns:
            업데이트된 카드 정보 dict

        Raises:
            httpx.HTTPStatusError: API 호출 실패
            ValueError: API 응답 오류
        """
        url = f"{self.backend_url}/api/job_posting_cards/{job_posting_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.patch(url, headers=headers, json=card_data)

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
