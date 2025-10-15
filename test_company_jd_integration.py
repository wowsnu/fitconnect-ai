"""
기업 인터뷰 JD 연동 테스트

백엔드에서 실제 채용공고를 가져와서 Technical 면접에 사용
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

# 기업용 JWT 토큰 (role: company)
TEST_COMPANY_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxOCIsImVtYWlsIjoic2FuZzFAbmF2ZXIuY29tIiwicm9sZSI6ImNvbXBhbnkiLCJleHAiOjE3NjA0MzI2MDJ9.AR_pOctvku3LaU3OWwuqSjkWYin3t0a04bLnnvjpsao"


def test_company_interview_with_jd():
    """기업 인터뷰 + JD 연동 테스트"""

    print("=" * 80)
    print("기업 인터뷰 JD 연동 테스트")
    print("=" * 80)

    # 0. 토큰 확인
    if TEST_COMPANY_TOKEN == "YOUR_COMPANY_TOKEN_HERE":
        print("❌ 기업 계정 토큰이 필요합니다!")
        print("백엔드에서 기업 계정으로 로그인 후 access_token을 여기에 입력하세요.")
        return

    # 1. 채용공고 목록 확인
    print("\n[1단계] 채용공고 목록 확인")
    try:
        backend_url = "http://54.89.71.175:8000"  # 백엔드 서버
        response = requests.get(
            f"{backend_url}/api/me/company/job-postings",
            headers={"Authorization": f"Bearer {TEST_COMPANY_TOKEN}"}
        )

        if response.status_code != 200:
            print(f"❌ 채용공고 조회 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return

        data = response.json()
        postings = data.get("data", [])

        if not postings:
            print("⚠️  등록된 채용공고가 없습니다!")
            print("백엔드에서 채용공고를 먼저 생성해주세요.")
            return

        print(f"✅ 총 {len(postings)}개 채용공고 발견")
        for p in postings:
            print(f"  - ID: {p['id']}, 제목: {p['title']}")

        # 첫 번째 채용공고 사용
        job_posting_id = postings[0]["id"]
        print(f"\n테스트에 사용할 채용공고 ID: {job_posting_id}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return

    # 2. General 면접 시작 (회사명 자동 로드)
    print("\n[2단계] General 면접 시작 (회사명 자동 로드)")
    response = requests.post(
        f"{BASE_URL}/company-interview/general/start",
        json={
            "access_token": TEST_COMPANY_TOKEN
            # company_name 없음 - 백엔드에서 자동 로드
        }
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
        return

    data = response.json()
    session_id = data["session_id"]
    print(f"✅ Session ID: {session_id}")

    # 3. General 면접 답변
    print("\n[3단계] General 면접 답변 제출")
    general_answers = [
        "저희는 혁신적인 AI 기술로 채용 시장을 혁신하고자 합니다.",
        "빠른 의사결정과 자율성을 중시하는 스타트업 문화입니다.",
        "우수한 백엔드 개발자를 찾고 있습니다.",
        "Python, FastAPI, PostgreSQL 경험이 있는 분을 선호합니다.",
        "팀 규모 확장과 신규 서비스 출시를 위해 채용합니다."
    ]

    for i, answer in enumerate(general_answers, 1):
        response = requests.post(
            f"{BASE_URL}/company-interview/general/answer",
            json={"session_id": session_id, "answer": answer}
        )
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return
        print(f"  답변 {i}/5 완료")

    print("✅ General 면접 완료")

    # 4. Technical 면접 시작 (JD 포함)
    print("\n[4단계] Technical 면접 시작 (JD 자동 로드)")
    print(f"  job_posting_id: {job_posting_id}")

    response = requests.post(
        f"{BASE_URL}/company-interview/technical/start",
        json={
            "session_id": session_id,
            "access_token": TEST_COMPANY_TOKEN,
            "job_posting_id": job_posting_id
        }
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
        return

    data = response.json()
    print("✅ Technical 면접 시작 성공!")
    print(f"\n첫 질문: {data['next_question']['question']}")

    # 5. Technical 면접 답변 (간단히 3개만)
    print("\n[5단계] Technical 면접 답변 제출 (3개만)")
    technical_answers = [
        "주요 업무는 API 개발과 데이터베이스 설계입니다.",
        "Python과 FastAPI 경험이 필수이고, 3년 이상의 경력이 필요합니다.",
        "AWS 경험과 대규모 트래픽 처리 경험이 있으면 우대합니다."
    ]

    for i, answer in enumerate(technical_answers, 1):
        response = requests.post(
            f"{BASE_URL}/company-interview/technical/answer",
            json={"session_id": session_id, "answer": answer}
        )
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return
        print(f"  답변 {i}/3 완료")

    print("\n" + "=" * 80)
    print("✅ 테스트 성공!")
    print("=" * 80)
    print("\n📌 서버 로그를 확인하세요:")
    print("   [INFO] Loaded JD for job posting {job_posting_id}")
    print("   위 메시지가 보이면 JD가 성공적으로 로드된 것입니다!")


def test_format_jd():
    """JD 포맷팅 함수 테스트"""
    print("=" * 80)
    print("JD 포맷팅 함수 테스트")
    print("=" * 80)

    from ai.interview.company_technical import format_job_posting_to_jd

    # 샘플 채용공고 데이터
    sample_posting = {
        "id": 1,
        "title": "시니어 백엔드 개발자",
        "position": "Backend Developer",
        "department": "개발팀",
        "employment_type": "FULL_TIME",
        "location_city": "서울",
        "responsibilities": "- API 개발 및 유지보수\n- 데이터베이스 설계 및 최적화\n- 시스템 아키텍처 설계",
        "requirements_must": "- Python 3년 이상\n- Django 또는 FastAPI 경험\n- PostgreSQL 경험",
        "requirements_nice": "- AWS 경험\n- Docker/Kubernetes 경험\n- 대규모 트래픽 처리 경험",
        "competencies": ["백엔드 개발", "API 설계", "데이터베이스 최적화"]
    }

    formatted_jd = format_job_posting_to_jd(sample_posting)

    print("\n📝 포맷팅된 JD:")
    print("-" * 80)
    print(formatted_jd)
    print("-" * 80)

    print("\n✅ 포맷팅 성공!")


if __name__ == "__main__":
    print("테스트 선택:")
    print("1. JD 포맷팅 함수만 테스트 (토큰 불필요)")
    print("2. 전체 플로우 테스트 (기업 토큰 필요)")

    choice = input("\n선택 (1 or 2): ").strip()

    if choice == "1":
        test_format_jd()
    elif choice == "2":
        test_company_interview_with_jd()
    else:
        print("잘못된 선택입니다.")
