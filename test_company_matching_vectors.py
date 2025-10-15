"""
기업 인터뷰 전체 플로우 + 매칭 벡터 테스트

General → Technical → Situational → JD + Card + Matching Vectors 생성
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api"
BACKEND_URL = "http://54.89.71.175:8000"

# 기업용 JWT 토큰 (role: company)
TEST_COMPANY_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxOCIsImVtYWlsIjoic2FuZzFAbmF2ZXIuY29tIiwicm9sZSI6ImNvbXBhbnkiLCJleHAiOjE3NjA0Njc0ODB9.9Dl647p1q-osXVotGq_1Zvmh3Fm81cxZuU-sxqoJv7g"


def test_full_company_interview():
    """전체 기업 인터뷰 플로우 테스트"""

    print("=" * 80)
    print("기업 인터뷰 전체 플로우 + 매칭 벡터 테스트")
    print("=" * 80)

    # 1. General 면접 시작
    print("\n[1단계] General 면접 시작")
    response = requests.post(
        f"{BASE_URL}/company-interview/general/start",
        json={"access_token": TEST_COMPANY_TOKEN}
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
        return

    data = response.json()
    session_id = data["session_id"]
    print(f"✅ Session ID: {session_id}")

    # 2. General 면접 답변 (5개)
    print("\n[2단계] General 면접 답변 제출 (5개)")
    general_answers = [
        "저희는 혁신, 투명성, 협력을 핵심 가치로 하는 AI 스타트업입니다.",
        "자율성과 책임감을 중시하며, 빠른 의사결정과 실행력이 강한 문화입니다.",
        "문제 해결 능력이 뛰어나고 적극적으로 소통하며 성장 마인드를 가진 인재를 찾습니다.",
        "애자일 방식으로 일하며, 2주 스프린트로 빠르게 제품을 개선합니다.",
        "신규 서비스 출시와 조직 확장을 위해 시니어 백엔드 개발자를 채용하려고 합니다."
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

    # 3. Technical 면접 시작
    print("\n[3단계] Technical 면접 시작")
    response = requests.post(
        f"{BASE_URL}/company-interview/technical/start",
        json={
            "session_id": session_id,
            "access_token": TEST_COMPANY_TOKEN
        }
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
        return

    print("✅ Technical 면접 시작")

    # 4. Technical 면접 답변 (동적 질문, is_finished까지)
    print("\n[4단계] Technical 면접 답변 제출")
    technical_answers = [
        "시니어 백엔드 개발자 포지션입니다.",
        "RESTful API 설계 및 개발, 데이터베이스 최적화, 마이크로서비스 아키텍처 구현, 코드 리뷰 및 주니어 멘토링이 주요 업무입니다.",
        "Python 5년 이상, FastAPI 실무 경험, PostgreSQL 최적화 경험, Redis 캐싱 전략 수립 경험이 필수입니다.",
        "AWS/GCP 인프라 운영, Kubernetes 경험, Kafka 경험, MSA 설계 경험이 있으면 우대합니다.",
        "대규모 트래픽 처리 시스템 구축과 레거시 코드 리팩토링이 주요 도전 과제입니다."
    ]

    answer_count = 0
    for answer in technical_answers:
        response = requests.post(
            f"{BASE_URL}/company-interview/technical/answer",
            json={"session_id": session_id, "answer": answer}
        )
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return

        data = response.json()
        answer_count += 1
        print(f"  답변 {answer_count} 완료")

        if data.get("is_finished"):
            print("✅ Technical 면접 완료")
            break

    # 5. Situational 면접 시작
    print("\n[5단계] Situational 면접 시작")
    response = requests.post(
        f"{BASE_URL}/company-interview/situational/start",
        params={"session_id": session_id}
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
        return

    print("✅ Situational 면접 시작")

    # 6. Situational 면접 답변
    print("\n[6단계] Situational 면접 답변 제출")
    situational_answers = [
        "현재 4명의 백엔드 개발자로 구성되어 있으며, 주니어 2명, 미들 1명, 시니어 1명입니다. 빠르게 성장 중이라 추가 시니어가 필요합니다.",
        "2주 스프린트로 애자일 개발을 하며, 데일리 스탠드업과 코드 리뷰를 필수로 합니다. Slack과 Notion으로 비동기 소통도 활발합니다.",
        "데이터와 논리를 기반으로 논의하며, 팀 전체가 의사결정에 참여합니다. 의견 충돌 시에는 A/B 테스트나 PoC로 검증합니다.",
        "재택/사무실 하이브리드이며, 코어타임(11~4시)만 지키면 자율 출퇴근입니다. 집중 시간 확보를 위해 회의는 오후에만 잡습니다.",
        "주도적이고 자율적인 업무 스타일을 선호하며, 문제를 발견하면 스스로 해결책을 제시하고 실행하는 분을 찾습니다."
    ]

    answer_count = 0
    for answer in situational_answers:
        response = requests.post(
            f"{BASE_URL}/company-interview/situational/answer",
            json={"session_id": session_id, "answer": answer}
        )
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return

        data = response.json()
        answer_count += 1
        print(f"  답변 {answer_count} 완료")

        if data.get("is_finished"):
            print("✅ Situational 면접 완료")
            break

    # 7. JD + Card + Matching Vector 생성
    print("\n[7단계] JD + Card + Matching Vector 생성")
    print("  (약 5-10초 소요)")

    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/company-interview/job-posting",
        params={
            "session_id": session_id,
            "access_token": TEST_COMPANY_TOKEN
        }
    )
    elapsed = time.time() - start_time

    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
        return

    data = response.json()
    print(f"✅ 생성 완료! (소요 시간: {elapsed:.2f}초)")

    # 8. 결과 출력
    print("\n" + "=" * 80)
    print("📊 생성 결과")
    print("=" * 80)

    print(f"\n✅ Job Posting ID: {data.get('job_posting_id')}")
    print(f"✅ Card ID: {data.get('card_id')}")
    print(f"✅ Matching Vector ID: {data.get('matching_vector_id')}")

    # JD 정보
    job_posting = data.get("job_posting", {})
    print(f"\n📄 채용공고:")
    print(f"  - 제목: {job_posting.get('title')}")
    print(f"  - 위치: {job_posting.get('location_city')}")
    print(f"  - 경력: {job_posting.get('career_level')}")
    print(f"  - 고용 형태: {job_posting.get('employment_type')}")
    print(f"\n  주요 업무:")
    for line in job_posting.get('responsibilities', '').split('\n')[:3]:
        if line.strip():
            print(f"    {line.strip()}")
    print(f"\n  필수 요건:")
    for line in job_posting.get('requirements_must', '').split('\n')[:3]:
        if line.strip():
            print(f"    {line.strip()}")

    # Card 정보
    card = data.get("card", {})
    print(f"\n🎴 카드:")
    print(f"  - 헤더: {card.get('header_title')}")
    print(f"  - 뱃지: {card.get('badge_role')}")
    print(f"  - 헤드라인: {card.get('headline')}")
    print(f"\n  주요 업무:")
    for resp in card.get('responsibilities', [])[:2]:
        print(f"    - {resp}")
    print(f"\n  필수 요건:")
    for req in card.get('requirements', [])[:2]:
        print(f"    - {req}")

    # Matching Texts
    matching_texts = data.get("matching_texts", {})
    if matching_texts:
        print(f"\n🎯 매칭 텍스트 생성 확인:")
        print(f"  ✅ roles_text: {len(matching_texts.get('roles_text', ''))}자")
        print(f"  ✅ skills_text: {len(matching_texts.get('skills_text', ''))}자")
        print(f"  ✅ growth_text: {len(matching_texts.get('growth_text', ''))}자")
        print(f"  ✅ career_text: {len(matching_texts.get('career_text', ''))}자")
        print(f"  ✅ vision_text: {len(matching_texts.get('vision_text', ''))}자")
        print(f"  ✅ culture_text: {len(matching_texts.get('culture_text', ''))}자")

        print(f"\n📝 매칭 텍스트 예시 (roles_text):")
        print(f"  {matching_texts.get('roles_text', '')[:200]}...")

    print("\n" + "=" * 80)
    print("✅ 전체 플로우 테스트 성공!")
    print("=" * 80)

    # 9. 백엔드에서 매칭 벡터 확인 (선택적)
    print("\n[8단계] 백엔드 매칭 벡터 확인 (선택적)")
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/me/matching-vectors",
            headers={"Authorization": f"Bearer {TEST_COMPANY_TOKEN}"}
        )

        if response.status_code == 200:
            backend_data = response.json()
            vectors = backend_data.get("data", {})
            print(f"✅ 백엔드 매칭 벡터 저장 확인:")
            print(f"  - ID: {vectors.get('id')}")
            print(f"  - Role: {vectors.get('role')}")
            print(f"  - Updated At: {vectors.get('updated_at')}")

            # 벡터 차원 확인
            if vectors.get('vector_roles'):
                embedding = vectors['vector_roles'].get('embedding', [])
                print(f"  - Vector Dimension: {len(embedding)}")
        else:
            print(f"ℹ️  백엔드 GET API 미지원 (이미 POST 응답에서 확인 완료)")
    except Exception as e:
        print(f"ℹ️  백엔드 확인 생략 (이미 POST 응답에서 확인 완료)")


if __name__ == "__main__":
    test_full_company_interview()
