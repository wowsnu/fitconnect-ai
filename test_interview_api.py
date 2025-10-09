"""
Interview API 테스트

FastAPI 서버를 실행한 후 이 스크립트로 API를 테스트합니다.

실행 방법:
1. 터미널 1: python main.py  (서버 시작)
2. 터미널 2: python test_interview_api.py  (API 테스트)
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_interview_flow():
    """전체 인터뷰 플로우 테스트"""

    print("=" * 60)
    print("구조화 면접 API 테스트")
    print("=" * 60)

    # 1. 인터뷰 시작
    print("\n[1단계] 인터뷰 시작")
    response = requests.post(f"{BASE_URL}/interview/general/start")
    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(f"Error: {response.text}")
        return

    data = response.json()
    session_id = data["session_id"]
    print(f"Session ID: {session_id}")
    print(f"첫 질문: {data['question']}")
    print(f"진행: {data['question_number']}/{data['total_questions']}")

    # 2. 모의 답변들
    mock_answers = [
        "안녕하세요. 저는 백엔드 개발자로 2년 정도 일했습니다. 최근 6개월 동안은 FastAPI로 E-commerce API를 만드는데 집중했어요. Redis 캐싱을 도입해서 응답속도를 50% 개선했습니다.",
        "가장 의미있던 프로젝트는 실시간 채팅 서버 구축이었어요. WebSocket과 FastAPI를 사용했고, 동시 접속자 1만명을 처리할 수 있게 만들었습니다. 저는 백엔드 아키텍처 설계와 성능 최적화를 담당했어요.",
        "저는 코드 리뷰를 적극적으로 하는 편입니다. 팀원들의 코드를 보면서 더 나은 방법을 제안하고, 제 코드도 리뷰받으면서 배우는 걸 좋아해요.",
        "성능과 안정성을 가장 중요하게 생각합니다. 빠르고 안정적인 시스템을 만드는 게 제 목표예요.",
        "시니어 백엔드 엔지니어가 되어서 대규모 시스템 설계 경험을 쌓고 싶습니다. 특히 분산 시스템과 MSA 아키텍처에 관심이 많아요."
    ]

    # 3. 답변 제출 (텍스트)
    print("\n[2단계] 답변 제출")
    for i, answer in enumerate(mock_answers, 1):
        print(f"\n--- 답변 {i} 제출 ---")
        response = requests.post(
            f"{BASE_URL}/interview/general/answer/text",
            json={
                "session_id": session_id,
                "answer": answer
            }
        )

        if response.status_code != 200:
            print(f"Error: {response.text}")
            continue

        data = response.json()
        print(f"진행: {data['question_number']}/{data['total_questions']}")

        if data['next_question']:
            print(f"다음 질문: {data['next_question']}")

        if data['is_finished']:
            print("\n✅ 모든 질문 완료!")
            break

    # 4. 세션 정보 조회
    print("\n[3단계] 세션 정보 조회")
    response = requests.get(f"{BASE_URL}/interview/general/session/{session_id}")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"세션 상태: {json.dumps(data, indent=2, ensure_ascii=False)}")

    # 5. 분석 결과 조회
    print("\n[4단계] 분석 결과 조회 (LLM 호출 - 5-10초 소요)")
    response = requests.get(f"{BASE_URL}/interview/general/analysis/{session_id}")
    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(f"Error: {response.text}")
        return

    data = response.json()
    print("\n" + "=" * 60)
    print("분석 결과")
    print("=" * 60)
    print(f"\n1. 주요 테마 (key_themes):")
    for theme in data['key_themes']:
        print(f"   - {theme}")

    print(f"\n2. 관심 분야 (interests):")
    for interest in data['interests']:
        print(f"   - {interest}")

    print(f"\n3. 업무 스타일 힌트 (work_style_hints):")
    for hint in data['work_style_hints']:
        print(f"   - {hint}")

    print(f"\n4. 강조한 경험 (emphasized_experiences):")
    for exp in data['emphasized_experiences']:
        print(f"   - {exp}")

    print(f"\n5. 기술 키워드 (technical_keywords):")
    for keyword in data['technical_keywords']:
        print(f"   - {keyword}")

    # 6. 세션 삭제
    print("\n[5단계] 세션 삭제")
    response = requests.delete(f"{BASE_URL}/interview/general/session/{session_id}")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print("✅ 세션 삭제 완료")

    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)


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
        test_interview_flow()
