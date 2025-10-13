"""
Technical Interview Flow 테스트

FastAPI 서버를 실행한 후 이 스크립트로 Technical Interview API를 테스트합니다.

실행 방법:
1. 터미널 1: python main.py  (서버 시작)
2. 터미널 2: python test_technical_interview_flow.py  (API 테스트)
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_technical_interview_flow():
    """Technical Interview 전체 플로우 테스트"""

    print("=" * 60)
    print("직무 적합성 면접 (Technical Interview) API 테스트")
    print("=" * 60)

    # 1. 먼저 General Interview 진행 (필수)
    print("\n[사전 준비] 구조화 면접 진행")
    response = requests.post(f"{BASE_URL}/interview/general/start")
    if response.status_code != 200:
        print(f"Error starting general interview: {response.text}")
        return

    data = response.json()
    session_id = data["session_id"]
    print(f"Session ID: {session_id}")

    # General Interview 답변들 (간단히)
    mock_answers = [
        "저는 백엔드 개발자로 3년 일했습니다. FastAPI, PostgreSQL, Redis를 주로 사용했고, 최근에는 대규모 트래픽 처리와 성능 최적화에 집중했습니다.",
        "가장 의미있던 건 결제 시스템 구축이었어요. 트랜잭션 처리와 데이터 정합성을 보장하면서 응답속도도 200ms 이하로 유지했습니다.",
        "코드 리뷰와 페어 프로그래밍을 적극적으로 합니다. 팀원들과 지식을 공유하면서 함께 성장하는 걸 중요하게 생각해요.",
        "안정성과 유지보수성을 가장 중요하게 생각합니다. 테스트 커버리지를 높이고 명확한 코드를 작성하려고 노력해요.",
        "시니어 개발자가 되어서 시스템 아키텍처 설계 경험을 더 쌓고 싶습니다. MSA와 분산 시스템에 특히 관심이 많아요."
    ]

    for answer in mock_answers:
        response = requests.post(
            f"{BASE_URL}/interview/general/answer/text",
            json={"session_id": session_id, "answer": answer}
        )
        if response.status_code != 200:
            print(f"Error: {response.text}")
            return

    print("✅ 구조화 면접 완료")

    # 2. Technical Interview 시작
    print("\n[1단계] 직무 적합성 면접 시작")

    # 모의 access_token (실제로는 JWT)
    mock_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxNiIsImVtYWlsIjoic2FuZ0BuYXZlci5jb20iLCJyb2xlIjoidGFsZW50IiwiZXhwIjoxNzYwMjcwMDI1fQ.O8ZBAxnuDYJIYrqp0NJJuqY8Z5T-K7KZ9pVwmcGw1Z0"

    response = requests.post(
        f"{BASE_URL}/interview/technical/start",
        json={
            "session_id": session_id,
            "access_token": mock_token
        }
    )

    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(f"Error: {response.text}")
        print("\n⚠️  백엔드 API 연동이 필요합니다.")
        print("이 테스트는 실제 백엔드 서버가 실행 중이어야 합니다.")
        return

    data = response.json()
    print(f"\n평가 기술: {data['skill']}")
    print(f"질문 번호: {data['question_number']}")
    print(f"질문: {data['question']}")
    print(f"질문 이유: {data['why']}")
    print(f"진행도: {data['progress']}")

    # 3. 답변 제출 (9개 질문)
    print("\n[2단계] 답변 제출 (9개 질문)")

    # 다양한 기술 답변들
    technical_answers = [
        # 기술 1 - 질문 1, 2, 3
        "FastAPI를 2년 정도 사용했습니다. E-commerce API를 만들 때 async/await를 활용해서 동시성을 높였고, Pydantic으로 데이터 검증을 깔끔하게 처리했어요. 특히 dependency injection 패턴이 테스트하기 편했습니다.",
        "Redis를 캐싱 레이어로 사용했어요. LRU 정책으로 자주 조회되는 상품 정보를 캐싱하고, TTL을 5분으로 설정했습니다. 캐시 미스율을 모니터링하면서 최적화했고, 결과적으로 DB 부하가 60% 감소했습니다.",
        "MSA 전환 과정에서 API Gateway 패턴을 도입했어요. 각 서비스의 독립성과 전체 시스템의 일관성 사이에서 균형을 맞추는 게 어려웠습니다. 결국 Event-driven 아키텍처로 서비스 간 결합도를 낮췄어요.",

        # 기술 2 - 질문 1, 2, 3
        "PostgreSQL을 주로 사용했습니다. 인덱스 설계할 때 B-tree vs GiST 선택하고, EXPLAIN ANALYZE로 쿼리 성능을 분석했어요. 특히 복합 인덱스 순서가 성능에 큰 영향을 준다는 걸 배웠습니다.",
        "N+1 쿼리 문제를 자주 만났어요. ORM을 사용할 때 join이나 prefetch를 명시적으로 해줘야 했습니다. 실시간 모니터링으로 슬로우 쿼리를 잡아내고 개선했어요.",
        "트랜잭션 isolation level을 Read Committed로 설정하고, 동시성 문제가 있는 부분은 SELECT FOR UPDATE로 락을 걸었습니다. 데드락 모니터링도 추가했어요.",

        # 기술 3 - 질문 1, 2, 3
        "Docker로 개발 환경을 통일했고, docker-compose로 로컬에서 전체 스택을 쉽게 띄울 수 있게 했어요. 멀티 스테이지 빌드로 이미지 크기를 300MB에서 80MB로 줄였습니다.",
        "CI/CD 파이프라인을 GitHub Actions로 구축했어요. 테스트 → 빌드 → 배포가 자동으로 진행되고, 배포 전에 smoke test로 헬스체크를 합니다.",
        "쿠버네티스 환경에서 rolling update를 사용하고 있어요. replica 수를 조절하면서 무중단 배포를 달성했고, HPA로 오토스케일링도 적용했습니다. 다만 stateful 서비스는 아직 고민 중이에요."
    ]

    for i, answer in enumerate(technical_answers, 1):
        print(f"\n--- 답변 {i}/9 제출 ---")
        response = requests.post(
            f"{BASE_URL}/interview/technical/answer",
            json={
                "session_id": session_id,
                "answer": answer
            }
        )

        if response.status_code != 200:
            print(f"Error: {response.text}")
            continue

        data = response.json()

        # 피드백 출력
        if 'feedback' in data:
            print(f"주요 포인트: {', '.join(data['feedback'].get('key_points', []))[:100]}...")
            print(f"파고들 영역: {', '.join(data['feedback'].get('depth_areas', []))}")

        # 다음 질문
        if data.get('next_question'):
            next_q = data['next_question']
            print(f"\n다음 질문 [{next_q['progress']}]:")
            print(f"기술: {next_q['skill']}")
            print(f"질문: {next_q['question'][:100]}...")

        if data.get('is_finished'):
            print("\n✅ 모든 기술 면접 완료!")
            break

    # 4. 최종 결과 조회
    print("\n[3단계] 최종 결과 조회")
    response = requests.get(f"{BASE_URL}/interview/technical/results/{session_id}")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\n평가된 기술: {', '.join(data['skills_evaluated'])}")
        print(f"총 질문 수: {data['total_questions']}")

        print("\n=== 상세 결과 ===")
        for skill, questions in data['results'].items():
            print(f"\n[{skill}] - {len(questions)}개 질문")
            for q in questions:
                print(f"  Q{q['question_number']}: {q['question'][:80]}...")
                print(f"  A: {q['answer'][:80]}...")
                print(f"  키포인트: {', '.join(q['feedback']['key_points'][:2])}")
                print()

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
        test_technical_interview_flow()
