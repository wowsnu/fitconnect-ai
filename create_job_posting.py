"""
채용공고 생성 스크립트
"""

import requests
import json

BACKEND_URL = "http://54.89.71.175:8000"
TEST_COMPANY_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxOCIsImVtYWlsIjoic2FuZzFAbmF2ZXIuY29tIiwicm9sZSI6ImNvbXBhbnkiLCJleHAiOjE3NjA0MzI2MDJ9.AR_pOctvku3LaU3OWwuqSjkWYin3t0a04bLnnvjpsao"


def create_job_posting():
    """채용공고 생성"""

    print("=" * 80)
    print("채용공고 생성")
    print("=" * 80)

    # 채용공고 데이터
    job_posting_data = {
        "title": "시니어 백엔드 개발자",
        "position_group": "개발",
        "position": "Backend Developer",
        "department": "개발팀",
        "employment_type": "FULL_TIME",
        "location_city": "서울",
        "career_level": "시니어",
        "education_level": "학력무관",
        "responsibilities": """- RESTful API 설계 및 개발
- 데이터베이스 스키마 설계 및 최적화
- 마이크로서비스 아키텍처 설계 및 구현
- 성능 모니터링 및 최적화
- 코드 리뷰 및 기술 문서 작성""",
        "requirements_must": """- Python 3년 이상 경험
- Django 또는 FastAPI 프레임워크 경험
- PostgreSQL, MySQL 등 RDBMS 경험
- RESTful API 설계 및 개발 경험
- Git을 이용한 협업 경험""",
        "requirements_nice": """- AWS, GCP 등 클라우드 서비스 경험
- Docker, Kubernetes 등 컨테이너 기술 경험
- Redis, Celery 등 비동기 처리 경험
- 대규모 트래픽 처리 경험
- MSA(Microservice Architecture) 경험""",
        "competencies": [
            "백엔드 개발",
            "API 설계",
            "데이터베이스 최적화",
            "성능 튜닝",
            "시스템 아키텍처"
        ],
        "salary_band": {
            "min": 6000,
            "max": 9000,
            "currency": "KRW",
            "unit": "만원"
        },
        "status": "PUBLISHED"
    }

    print("\n채용공고 정보:")
    print(f"  제목: {job_posting_data['title']}")
    print(f"  포지션: {job_posting_data['position']}")
    print(f"  위치: {job_posting_data['location_city']}")

    # API 호출
    response = requests.post(
        f"{BACKEND_URL}/api/me/company/job-postings",
        headers={
            "Authorization": f"Bearer {TEST_COMPANY_TOKEN}",
            "Content-Type": "application/json"
        },
        json=job_posting_data
    )

    if response.status_code != 200 and response.status_code != 201:
        print(f"\n❌ 채용공고 생성 실패: {response.status_code}")
        print(f"응답: {response.text}")
        return None

    data = response.json()

    if data.get("ok"):
        job_posting = data.get("data", {})
        job_posting_id = job_posting.get("id")

        print("\n✅ 채용공고 생성 성공!")
        print(f"  ID: {job_posting_id}")
        print(f"  제목: {job_posting.get('title')}")

        return job_posting_id
    else:
        print(f"\n❌ 채용공고 생성 실패")
        print(f"응답: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return None


def list_job_postings():
    """채용공고 목록 조회"""

    print("\n" + "=" * 80)
    print("채용공고 목록 조회")
    print("=" * 80)

    response = requests.get(
        f"{BACKEND_URL}/api/me/company/job-postings",
        headers={"Authorization": f"Bearer {TEST_COMPANY_TOKEN}"}
    )

    if response.status_code != 200:
        print(f"❌ 조회 실패: {response.status_code}")
        print(f"응답: {response.text}")
        return

    data = response.json()
    postings = data.get("data", [])

    if not postings:
        print("등록된 채용공고가 없습니다.")
        return

    print(f"\n총 {len(postings)}개 채용공고:")
    for p in postings:
        print(f"\n  ID: {p['id']}")
        print(f"  제목: {p['title']}")
        print(f"  포지션: {p.get('position', 'N/A')}")
        print(f"  상태: {p['status']}")


if __name__ == "__main__":
    # 1. 먼저 목록 조회
    list_job_postings()

    # 2. 채용공고 생성
    print("\n" + "=" * 80)
    choice = input("채용공고를 생성하시겠습니까? (y/n): ").strip().lower()

    if choice == 'y':
        job_posting_id = create_job_posting()

        if job_posting_id:
            # 3. 다시 목록 조회
            list_job_postings()

            print("\n" + "=" * 80)
            print(f"✅ 완료! job_posting_id = {job_posting_id}")
            print("이제 test_company_jd_integration.py를 실행하세요!")
    else:
        print("취소됨")
