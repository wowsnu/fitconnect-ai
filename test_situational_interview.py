"""
상황 면접 테스트 스크립트
답변 예시로 전체 플로우 테스트
"""

import asyncio
import httpx

# 설정
AI_URL = "http://127.0.0.1:8000"  # AI 서버 URL
SESSION_ID = "test-situational-session-001"

# 답변 예시 (총 6개 - 상황에 따라 질문이 달라질 수 있음)
ANSWER_EXAMPLES = [
    # 질문 1: 팀에서 중요한 의사결정을 내려야 할 때, 의견이 나뉘면 어떻게 해결하나요?
    """
    먼저 각 팀원의 의견을 충분히 듣고 정리합니다. 그리고 각 의견의 장단점을
    데이터나 과거 사례를 바탕으로 객관적으로 분석합니다. 저는 팀 전체가
    납득할 수 있는 방향으로 합의를 이끌어내는 것을 중요하게 생각합니다.
    만약 결정이 어렵다면, 작은 프로토타입을 만들어 실제로 테스트해보고
    결과를 보면서 결정하는 것도 좋은 방법이라고 생각합니다.
    """,

    # 질문 2: 급하게 처리해야 할 일이 갑자기 생겼을 때, 어떻게 대응하나요?
    """
    먼저 상황을 빠르게 파악하고 우선순위를 정합니다. 가장 중요하고
    긴급한 것부터 처리하되, 완벽하게 하기보다는 최소한으로 동작하는
    버전을 먼저 만드는 것을 선호합니다. 시간이 정말 부족하면 동료에게
    도움을 요청하기도 하고, 나중에 여유가 생기면 코드를 개선합니다.
    급한 상황에서도 침착하게 단계별로 접근하려고 노력합니다.
    """,

    # 질문 3: 완전히 새로운 분야를 짧은 시간 안에 배워야 할 때, 어떤 방식으로 접근하나요?
    """
    공식 문서를 먼저 빠르게 읽고, 전체적인 개념과 구조를 파악합니다.
    그 다음 간단한 예제 프로젝트를 직접 만들어보면서 실습합니다.
    저는 이론만 공부하는 것보다 실제로 코드를 작성해보면서 배우는 것이
    훨씬 빠르고 효과적이라고 생각합니다. 막히는 부분이 있으면
    스택오버플로우나 커뮤니티를 찾아보고, 필요하면 경험 있는 동료에게
    조언을 구합니다.
    """,

    # 질문 4-6: 심화/검증 질문은 답변에 따라 달라지므로 범용 답변 준비
    """
    제 경험상 이런 상황에서는 먼저 상황을 정확히 이해하고, 가능한
    옵션들을 빠르게 정리합니다. 그리고 각 옵션의 리스크와 장점을
    평가한 후, 팀과 논의하면서 최선의 방법을 찾습니다. 혼자 결정하기보다는
    팀원들의 의견을 듣고 함께 결정하는 것을 선호합니다. 결정 후에는
    빠르게 실행하고, 결과를 확인하면서 필요하면 조정합니다.
    """,

    """
    저는 새로운 도전을 긍정적으로 받아들이는 편입니다. 처음에는
    부담스럽더라도 이것이 성장의 기회라고 생각하고 적극적으로 접근합니다.
    모르는 것은 빠르게 배우고, 필요하면 주변에 도움을 요청합니다.
    실수를 하더라도 그것을 학습의 기회로 삼아서 다음에는 더 잘할 수
    있도록 노력합니다.
    """,

    """
    의견 차이가 있을 때는 먼저 상대방의 입장을 충분히 이해하려고 노력합니다.
    그리고 저의 생각을 논리적으로, 데이터나 근거를 들어 설명합니다.
    감정적으로 대응하기보다는 객관적인 사실에 기반해서 대화하려고 합니다.
    만약 합의가 어렵다면, 제3자의 의견을 구하거나 실험을 통해 결과로
    증명하는 방법을 선택합니다.
    """
]


async def test_situational_interview():
    """상황 면접 테스트 실행"""

    print("=" * 60)
    print("상황 면접 테스트 시작")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. 상황 면접 시작
        print("\n[1단계] 상황 면접 시작...")
        try:
            response = await client.post(
                f"{AI_URL}/api/interview/situational/start",
                params={
                    "session_id": SESSION_ID,
                    "skip_validation": True  # 테스트용으로 이전 면접 검증 스킵
                }
            )
            response.raise_for_status()
            data = response.json()

            question = data.get("question")
            phase = data.get("phase")
            progress = data.get("progress")

            print(f"\n첫 질문 받기 성공!")
            print(f"Phase: {phase}")
            print(f"Progress: {progress}")
            print(f"질문: {question}")

        except Exception as e:
            print(f"❌ 실패: {e}")
            return

        # 2. 6개 답변 제출
        for idx, answer_text in enumerate(ANSWER_EXAMPLES, 1):
            print(f"\n[{idx}번째 답변] 제출 중...")

            try:
                response = await client.post(
                    f"{AI_URL}/api/interview/situational/answer",
                    json={
                        "session_id": SESSION_ID,
                        "answer": answer_text.strip()
                    }
                )
                response.raise_for_status()
                data = response.json()

                analysis = data.get("analysis", {})
                next_question = data.get("next_question")
                is_finished = data.get("is_finished", False)

                print(f"✅ 답변 제출 성공!")
                print(f"분석: {analysis.get('reasoning', '없음')[:100]}...")

                if next_question:
                    print(f"\n다음 질문 ({next_question.get('progress')}):")
                    print(f"{next_question.get('question')}")

                if is_finished:
                    print("\n✅ 모든 질문 완료!")
                    break

            except Exception as e:
                print(f"❌ {idx}번째 답변 실패: {e}")
                return

        # 3. 최종 리포트 조회
        print("\n[3단계] 최종 페르소나 리포트 조회...")
        try:
            response = await client.get(
                f"{AI_URL}/api/interview/situational/report/{SESSION_ID}"
            )
            response.raise_for_status()
            data = response.json()

            persona = data.get("persona", {})
            summary = data.get("summary", "")
            team_env = data.get("recommended_team_environment", "")

            print("\n" + "=" * 60)
            print("📊 최종 페르소나 분석 결과")
            print("=" * 60)
            print(f"\n🎯 업무 스타일: {persona.get('work_style', '알 수 없음')}")
            print(f"🧩 문제 해결: {persona.get('problem_solving', '알 수 없음')}")
            print(f"📚 학습 성향: {persona.get('learning', '알 수 없음')}")
            print(f"💪 스트레스 대응: {persona.get('stress_response', '알 수 없음')}")
            print(f"💬 커뮤니케이션: {persona.get('communication', '알 수 없음')}")
            print(f"\n📝 요약: {summary}")
            print(f"\n🏢 추천 팀 환경: {team_env}")
            print("\n" + "=" * 60)

            return data

        except Exception as e:
            print(f"❌ 리포트 조회 실패: {e}")
            return


if __name__ == "__main__":
    print("🚀 상황 면접 테스트를 시작합니다...")
    print(f"Session ID: {SESSION_ID}")
    print(f"AI Server: {AI_URL}")
    print("\n답변 예시로 6개 질문을 자동으로 진행합니다.\n")

    result = asyncio.run(test_situational_interview())

    if result:
        print("\n✅ 테스트 완료! 모든 단계가 성공적으로 완료되었습니다.")
    else:
        print("\n❌ 테스트 실패. 위의 에러 메시지를 확인하세요.")
