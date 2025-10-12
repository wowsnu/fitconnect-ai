"""
매칭 벡터 생성 테스트

전체 플로우:
1. 3가지 면접 완료
2. 매칭 벡터 생성 (6가지 텍스트 + 임베딩)
3. 결과 확인

실행 방법:
python test_matching_vectors.py
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

# 실제 JWT 토큰
TEST_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMSIsImVtYWlsIjoic2FuZ3dvb0BuYXZlci5jb20iLCJyb2xlIjoidGFsZW50IiwiZXhwIjoxNzYwMjg4OTM3fQ.neoG4RZ7NVHZNvDWa3_O9aN-qXocprMOLN4vqfP7yB0"


def test_matching_vectors_generation():
    """매칭 벡터 생성 테스트"""

    print("=" * 80)
    print("매칭 벡터 생성 테스트")
    print("=" * 80)

    # ==================== 1. 구조화 면접 ====================
    print("\n[1단계] 구조화 면접 시작")
    response = requests.post(f"{BASE_URL}/interview/general/start")

    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
        return

    data = response.json()
    session_id = data["session_id"]
    print(f"✅ Session ID: {session_id}")

    # 구조화 면접 답변
    general_answers = [
        "안녕하세요. 저는 FastAPI와 Django로 백엔드 개발을 3년간 해왔습니다. 최근에는 AI 추천 시스템 API를 개발했고, Redis 캐싱으로 응답 속도를 70% 개선했습니다.",
        "가장 의미있던 프로젝트는 실시간 채팅 서버였어요. WebSocket과 Redis Pub/Sub를 활용해 동시 접속자 5만명을 처리할 수 있게 만들었습니다.",
        "저는 코드 리뷰와 페어 프로그래밍을 선호합니다. 팀원들과 적극적으로 소통하면서 함께 성장하는 걸 좋아해요.",
        "성능 최적화와 확장 가능한 아키텍처에 관심이 많습니다. 특히 분산 시스템과 MSA 구조를 깊이 공부하고 있어요.",
        "시니어 백엔드 엔지니어로 성장해서 대규모 트래픽을 처리하는 시스템을 설계하고 싶습니다."
    ]

    print("\n[2단계] 구조화 면접 답변 제출")
    for i, answer in enumerate(general_answers, 1):
        response = requests.post(
            f"{BASE_URL}/interview/general/answer/text",
            json={"session_id": session_id, "answer": answer}
        )
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return
        print(f"  답변 {i}/{len(general_answers)} 완료")

    print("✅ 구조화 면접 완료")

    # ==================== 2. 직무 적합성 면접 ====================
    print("\n[3단계] 직무 적합성 면접 시작")
    response = requests.post(
        f"{BASE_URL}/interview/technical/start",
        json={"session_id": session_id, "access_token": TEST_ACCESS_TOKEN}
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
        print("⚠️  백엔드 API 연결 필요")
        return

    data = response.json()
    print(f"✅ 선정된 기술: {data.get('selected_skills', [])}")

    # 직무 면접 9개 답변
    technical_answers = [
        "FastAPI는 3년간 사용했습니다. 비동기 처리가 뛰어나고, Pydantic으로 타입 안정성을 확보할 수 있어서 좋아요.",
        "비동기 엔드포인트에서 DB 쿼리 최적화와 캐싱 전략을 적용했습니다. Uvicorn worker를 4개로 늘려 동시 처리량을 높였어요.",
        "대규모 트래픽 환경에서는 Redis 캐싱과 DB 커넥션 풀 관리가 중요합니다. 모니터링도 필수고요.",
        "PostgreSQL을 주로 사용합니다. 인덱싱과 쿼리 최적화에 관심이 많고, EXPLAIN ANALYZE로 성능을 분석해요.",
        "JOIN 최적화와 인덱스 설계를 중점적으로 했습니다. 특히 복합 인덱스를 활용해 쿼리 속도를 10배 개선한 경험이 있어요.",
        "파티셔닝과 샤딩을 고려하고 있습니다. 대용량 데이터 처리 시 필수적이라고 생각해요.",
        "Redis를 캐싱과 세션 저장소로 사용했습니다. TTL 설정과 메모리 관리가 중요하더라고요.",
        "Cache-aside 패턴을 주로 사용하고, 캐시 무효화 전략도 함께 설계했습니다.",
        "Cluster 모드와 Sentinel을 활용한 고가용성 구성을 경험해봤어요. 장애 대응이 중요하다고 느꼈습니다."
    ]

    print("\n[4단계] 직무 적합성 면접 답변 제출")
    for i, answer in enumerate(technical_answers, 1):
        response = requests.post(
            f"{BASE_URL}/interview/technical/answer",
            json={"session_id": session_id, "answer": answer}
        )
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return
        print(f"  답변 {i}/{len(technical_answers)} 완료")
        data = response.json()
        if data['is_finished']:
            break

    print("✅ 직무 적합성 면접 완료")

    # ==================== 3. 상황 면접 ====================
    print("\n[5단계] 상황 면접 시작")
    response = requests.post(
        f"{BASE_URL}/interview/situational/start?session_id={session_id}"
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
        return

    print("✅ 상황 면접 시작")

    # 상황 면접 6개 답변
    situational_answers = [
        "의견이 나뉠 때는 각자의 근거를 듣고, 데이터나 사례를 기반으로 논의합니다. 합의가 안되면 프로토타입을 만들어서 비교해봐요.",
        "우선순위를 빠르게 판단하고, 필요하면 팀에 도움을 요청합니다. 혼자 해결하려다 시간을 낭비하지 않으려고 해요.",
        "공식 문서를 먼저 읽고, 간단한 프로젝트를 만들어보면서 학습합니다. 실습 중심으로 배우는 게 효과적이더라고요.",
        "팀원들과 더 자주 소통하고, 진행 상황을 공유하면서 문제를 함께 해결하려고 노력해요.",
        "제 의견이 틀렸을 수도 있다는 걸 인정하고, 상대방의 근거를 다시 들어봅니다. 논리적으로 설득되면 제 의견을 바꿔요.",
        "기술 블로그를 운영하면서 배운 내용을 정리하고, 오픈소스 기여도 하고 있어요. 꾸준히 성장하고 싶습니다."
    ]

    print("\n[6단계] 상황 면접 답변 제출")
    for i, answer in enumerate(situational_answers, 1):
        response = requests.post(
            f"{BASE_URL}/interview/situational/answer",
            json={"session_id": session_id, "answer": answer}
        )
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return
        print(f"  답변 {i}/{len(situational_answers)} 완료")
        data = response.json()
        if data['is_finished']:
            break

    print("✅ 상황 면접 완료")

    # ==================== 4. 매칭 벡터 생성 ====================
    print("\n[7단계] 매칭 벡터 생성 (LLM + 임베딩 - 10-20초 소요)")
    response = requests.post(
        f"{BASE_URL}/interview/matching-vectors/generate",
        json={"session_id": session_id}
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
        return

    data = response.json()

    print("\n" + "=" * 80)
    print("매칭 벡터 생성 결과")
    print("=" * 80)

    texts = data['texts']
    vectors = data['vectors']

    print("\n📝 6가지 매칭 텍스트:")
    print(f"\n1️⃣  역할 적합도/역할 수행력:")
    print(f"   {texts['roles_text']}")

    print(f"\n2️⃣  역량 적합도:")
    print(f"   {texts['skills_text']}")

    print(f"\n3️⃣  성장 가능성:")
    print(f"   {texts['growth_text']}")

    print(f"\n4️⃣  커리어 방향:")
    print(f"   {texts['career_text']}")

    print(f"\n5️⃣  비전/협업 기여도:")
    print(f"   {texts['vision_text']}")

    print(f"\n6️⃣  조직/문화 적합도:")
    print(f"   {texts['culture_text']}")

    print("\n" + "=" * 80)
    print("벡터 정보")
    print("=" * 80)
    print(f"✅ Role: {vectors['role']}")
    print(f"✅ vector_roles: {len(vectors['vector_roles'])} dimensions - {vectors['vector_roles'][:5]}...")
    print(f"✅ vector_skills: {len(vectors['vector_skills'])} dimensions - {vectors['vector_skills'][:5]}...")
    print(f"✅ vector_growth: {len(vectors['vector_growth'])} dimensions - {vectors['vector_growth'][:5]}...")
    print(f"✅ vector_career: {len(vectors['vector_career'])} dimensions - {vectors['vector_career'][:5]}...")
    print(f"✅ vector_vision: {len(vectors['vector_vision'])} dimensions - {vectors['vector_vision'][:5]}...")
    print(f"✅ vector_culture: {len(vectors['vector_culture'])} dimensions - {vectors['vector_culture'][:5]}...")

    print("\n" + "=" * 80)
    print("백엔드 POST 형식 (vectors만)")
    print("=" * 80)
    print(json.dumps(vectors, indent=2, ensure_ascii=False)[:500] + "...")

    print("\n" + "=" * 80)
    print("✅ 테스트 완료!")
    print("=" * 80)


def test_health_check():
    """서버 상태 확인"""
    print("\n서버 상태 확인...")
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ 서버가 정상 동작 중입니다.")
            return True
        else:
            print(f"❌ 서버 응답 이상: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다.")
        print("먼저 서버를 실행하세요: python main.py")
        return False


if __name__ == "__main__":
    if test_health_check():
        test_matching_vectors_generation()
