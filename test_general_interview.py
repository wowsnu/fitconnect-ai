"""
구조화 면접 (General Interview) 테스트
"""

import asyncio
from ai.interview.general import GeneralInterview, analyze_general_interview, GENERAL_QUESTIONS


def test_general_interview_flow():
    """구조화 면접 전체 플로우 테스트"""

    print("=" * 60)
    print("구조화 면접 테스트 시작")
    print("=" * 60)

    # 1. 인터뷰 초기화
    interview = GeneralInterview()
    print(f"\n총 질문 수: {len(interview.questions)}")
    print(f"질문 목록:")
    for i, q in enumerate(interview.questions, 1):
        print(f"  {i}. {q}")

    # 2. 모의 답변 데이터
    mock_answers = [
        "안녕하세요. 저는 백엔드 개발자로 2년 정도 일했습니다. 최근 6개월 동안은 FastAPI로 E-commerce API를 만드는데 집중했어요. Redis 캐싱을 도입해서 응답속도를 50% 개선했습니다.",
        "가장 의미있던 프로젝트는 실시간 채팅 서버 구축이었어요. WebSocket과 FastAPI를 사용했고, 동시 접속자 1만명을 처리할 수 있게 만들었습니다. 저는 백엔드 아키텍처 설계와 성능 최적화를 담당했어요.",
        "저는 코드 리뷰를 적극적으로 하는 편입니다. 팀원들의 코드를 보면서 더 나은 방법을 제안하고, 제 코드도 리뷰받으면서 배우는 걸 좋아해요.",
        "성능과 안정성을 가장 중요하게 생각합니다. 빠르고 안정적인 시스템을 만드는 게 제 목표예요.",
        "시니어 백엔드 엔지니어가 되어서 대규모 시스템 설계 경험을 쌓고 싶습니다. 특히 분산 시스템과 MSA 아키텍처에 관심이 많아요."
    ]

    print("\n" + "=" * 60)
    print("질문 및 답변 진행")
    print("=" * 60)

    # 3. 질문-답변 진행
    for i, answer_text in enumerate(mock_answers, 1):
        # 질문 받기
        question = interview.get_next_question()
        if not question:
            break

        print(f"\n[질문 {i}]")
        print(question)

        print(f"\n[답변 {i}]")
        print(answer_text)

        # 답변 제출
        result = interview.submit_answer(answer_text)
        print(f"\n제출 결과: {result['question_number']}/{result['total_questions']} 완료")

    # 4. 완료 여부 확인
    print(f"\n모든 질문 완료: {interview.is_finished()}")

    # 5. 모든 답변 조회
    all_answers = interview.get_answers()
    print(f"\n총 답변 수: {len(all_answers)}")

    return all_answers


async def test_answer_analysis():
    """답변 분석 테스트 (LLM 호출)"""

    print("\n\n" + "=" * 60)
    print("답변 분석 테스트 (LLM)")
    print("=" * 60)

    # 먼저 인터뷰 진행
    all_answers = test_general_interview_flow()

    print("\n\n답변 분석 시작...")
    print("(LLM 호출 중... 5-10초 소요)")

    # LLM 분석
    analysis = analyze_general_interview(all_answers)

    print("\n" + "=" * 60)
    print("분석 결과")
    print("=" * 60)

    print(f"\n1. 주요 테마 (key_themes):")
    for theme in analysis.key_themes:
        print(f"   - {theme}")

    print(f"\n2. 관심 분야 (interests):")
    for interest in analysis.interests:
        print(f"   - {interest}")

    print(f"\n3. 업무 스타일 힌트 (work_style_hints):")
    for hint in analysis.work_style_hints:
        print(f"   - {hint}")

    print(f"\n4. 강조한 경험 (emphasized_experiences):")
    for exp in analysis.emphasized_experiences:
        print(f"   - {exp}")

    print(f"\n5. 기술 키워드 (technical_keywords):")
    for keyword in analysis.technical_keywords:
        print(f"   - {keyword}")

    print("\n" + "=" * 60)
    print("분석 완료!")
    print("=" * 60)

    return analysis


if __name__ == "__main__":
    # 비동기 실행
    asyncio.run(test_answer_analysis())
