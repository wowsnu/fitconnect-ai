"""
Company Interview System Test

기업 면접 전체 플로우 테스트:
1. General Interview (5개 고정)
2. Technical Interview (5개 고정 + 2-3개 실시간)
3. Situational Interview (5개 고정 + 2-3개 실시간)
4. Job Posting Card 생성
"""

import asyncio
from ai.interview.company_general import (
    CompanyGeneralInterview,
    analyze_company_general_interview
)
from ai.interview.company_technical import (
    CompanyTechnicalInterview,
    analyze_company_technical_interview
)
from ai.interview.company_situational import (
    CompanySituationalInterview,
    analyze_company_situational_interview
)
from ai.interview.company_job_posting import generate_job_posting_card


async def test_company_interview_flow():
    """전체 기업 면접 플로우 테스트"""

    print("=" * 60)
    print("기업 면접 시스템 테스트 시작")
    print("=" * 60)

    # ==================== 1. General Interview ====================
    print("\n[1단계] General Interview (HR 관점)")
    print("-" * 60)

    general_interview = CompanyGeneralInterview()

    # 5개 고정 질문
    general_answers_data = [
        {
            "question": "우리 팀/회사의 핵심 가치는 무엇인가요?",
            "answer": "저희는 투명성, 협력, 혁신을 가장 중요하게 생각합니다. 특히 수평적 문화에서 자유롭게 의견을 나누고, 실패를 두려워하지 않는 도전 정신을 중요시합니다."
        },
        {
            "question": "어떤 인재를 채용하고 싶으신가요? (3-5가지 특징)",
            "answer": "첫째, 빠른 학습 능력이 있는 분. 둘째, 적극적으로 커뮤니케이션하는 분. 셋째, 문제를 스스로 해결하려는 주도성이 있는 분. 넷째, 팀워크를 중시하는 분입니다."
        },
        {
            "question": "팀의 업무 방식과 문화를 설명해주세요",
            "answer": "애자일 방식으로 2주 스프린트로 일하고 있고, 매일 데일리 스탠드업을 합니다. 재택과 사무실 근무를 자유롭게 선택할 수 있고, 코드 리뷰와 페어 프로그래밍을 적극 활용합니다."
        },
        {
            "question": "이번 채용을 통해 해결하고 싶은 문제는 무엇인가요?",
            "answer": "현재 백엔드 팀원이 2명밖에 없어서 업무 부담이 큽니다. 신규 기능 개발보다 유지보수에 시간을 많이 쓰고 있어요. 한 분이 합류하시면 팀이 안정화되고 새로운 도전도 할 수 있을 것 같습니다."
        },
        {
            "question": "이 포지션에서 가장 중요하게 생각하는 인재상이나 가치관은 무엇인가요?",
            "answer": "주인의식을 가지고 일하는 분이면 좋겠어요. 단순히 주어진 일만 하는 게 아니라, 제품과 사용자를 생각하며 능동적으로 개선점을 찾는 분을 찾습니다."
        }
    ]

    print("\n질문 & 답변:")
    for i, qa in enumerate(general_answers_data, 1):
        print(f"\n[Q{i}] {qa['question']}")
        print(f"[A{i}] {qa['answer']}")

        # 실제 면접처럼 처리
        if i == 1:
            general_interview.get_next_question()
        general_interview.submit_answer(qa['answer'])

    print("\n✅ General Interview 완료")

    # 분석
    print("\n📊 General 분석 중...")
    general_analysis = analyze_company_general_interview(general_interview.get_answers())

    print(f"\n[분석 결과]")
    print(f"- 핵심 가치: {', '.join(general_analysis.core_values)}")
    print(f"- 이상적 인재: {', '.join(general_analysis.ideal_candidate_traits)}")
    print(f"- 팀 문화: {general_analysis.team_culture}")
    print(f"- 업무 방식: {general_analysis.work_style}")
    print(f"- 채용 이유: {general_analysis.hiring_reason}")

    # ==================== 2. Technical Interview ====================
    print("\n\n[2단계] Technical Interview (직무 관점)")
    print("-" * 60)

    technical_interview = CompanyTechnicalInterview(
        general_analysis=general_analysis,
        existing_jd=None  # 기존 JD 없음
    )

    # 고정 5개 질문 먼저
    technical_fixed_answers = [
        {
            "question": "이 포지션에서 수행할 주요 업무는 무엇인가요?",
            "answer": "RESTful API 설계 및 개발, 데이터베이스 스키마 설계, 서버 성능 최적화, 그리고 기존 레거시 코드 리팩토링이 주요 업무입니다."
        },
        {
            "question": "필수로 갖춰야 할 기술/역량은 무엇인가요?",
            "answer": "Python 3년 이상, FastAPI 또는 Django 경험, PostgreSQL 사용 경험, Git 협업 경험이 필수입니다."
        },
        {
            "question": "우대하는 기술/역량이 있다면 무엇인가요?",
            "answer": "Docker, Kubernetes 경험이 있으면 좋고, AWS 인프라 경험, Redis 캐싱 경험, 그리고 테스트 코드 작성 경험이 있으면 우대합니다."
        },
        {
            "question": "이 포지션에서 뛰어난 성과를 낸 직원은 어떤 특징을 가지고 있었나요?",
            "answer": "이번에 새로 만들어진 포지션입니다. 기존에 시니어 개발자 한 분이 혼자 백엔드를 맡고 계셨는데, 팀이 커지면서 미들급 개발자를 추가로 채용하게 되었습니다."
        },
        {
            "question": "이 포지션에서 예상되는 어려움이나 도전 과제는 무엇인가요?",
            "answer": "레거시 코드가 많아서 처음엔 코드 파악에 시간이 걸릴 수 있어요. 그리고 사용자가 빠르게 늘고 있어서 스케일링 이슈를 경험하게 될 거예요. 하지만 이게 성장의 기회이기도 합니다."
        }
    ]

    print("\n[고정 질문 5개]")
    for i, qa in enumerate(technical_fixed_answers, 1):
        print(f"\n[Q{i}] {qa['question']}")
        print(f"[A{i}] {qa['answer']}")

        if i == 1:
            technical_interview.get_next_question()
        technical_interview.submit_answer(qa['answer'])

    print("\n✅ 고정 질문 완료")

    # 실시간 추천 질문 (자동 생성됨)
    print("\n🤖 실시간 추천 질문 생성 중...")
    print(f"\n생성된 추천 질문: {len(technical_interview.dynamic_questions)}개")

    for i, q in enumerate(technical_interview.dynamic_questions, 1):
        print(f"\n[동적 Q{i}] {q.question}")
        print(f"[목적] {q.purpose}")

        # 간단한 답변 (실제로는 사용자 입력)
        dummy_answer = "네, 그렇습니다. 구체적으로 말씀드리면..."
        print(f"[A] {dummy_answer}")
        technical_interview.submit_answer(dummy_answer)

    print("\n✅ Technical Interview 완료")

    # 분석
    print("\n📊 Technical 분석 중...")
    technical_requirements = analyze_company_technical_interview(
        answers=technical_interview.get_answers(),
        general_analysis=general_analysis
    )

    print(f"\n[분석 결과]")
    print(f"- 직무명: {technical_requirements.job_title}")
    print(f"- 주요 업무: {', '.join(technical_requirements.main_responsibilities)}")
    print(f"- 필수 역량: {', '.join(technical_requirements.required_skills)}")
    print(f"- 우대 역량: {', '.join(technical_requirements.preferred_skills)}")
    print(f"- 예상 도전: {technical_requirements.expected_challenges}")

    # ==================== 3. Situational Interview ====================
    print("\n\n[3단���] Situational Interview (팀 문화 & 핏)")
    print("-" * 60)

    situational_interview = CompanySituationalInterview(
        general_analysis=general_analysis,
        technical_requirements=technical_requirements
    )

    # 고정 5개 질문
    situational_fixed_answers = [
        {
            "question": "현재 팀의 상황은 어떤가요? (성장기, 안정기 등)",
            "answer": "명확히 성장기입니다. 사용자가 매달 2배씩 늘고 있고, 팀도 3개월마다 1명씩 늘리고 있어요. 불확실성이 높지만 재미있는 시기입니다."
        },
        {
            "question": "팀에서 잘 맞는 성향이나 협업 스타일은 어떤 것인가요?",
            "answer": "적극적으로 질문하고 의견을 나누는 분이 잘 맞아요. 저희는 주니어라도 좋은 아이디어가 있으면 바로 실행해보는 문화라서, 수동적이면 아쉬울 수 있어요."
        },
        {
            "question": "팀 내에서 의견 충돌이 있을 때 어떻게 해결하나요?",
            "answer": "데이터와 사용자 피드백을 기준으로 결정합니다. 의견이 갈리면 A/B 테스트를 해보거나, 작은 규모로 실험해보고 판단해요."
        },
        {
            "question": "빠르게 변화하는 환경 vs 안정적인 환경, 우리 팀은?",
            "answer": "완전히 빠르게 변화하는 환경이에요. 우선순위가 주마다 바뀔 수 있고, 새로운 기술 도입도 적극적입니다. 안정을 원하시는 분에게는 맞지 않을 수 있어요."
        },
        {
            "question": "독립적으로 일하는 사람 vs 협업하는 사람, 어떤 게 더 필요한가요?",
            "answer": "협업이 더 중요합니다. 팀이 작아서 서로 의존도가 높아요. 프론트엔드, 백엔드, 디자이너가 매일 얘기하면서 일합니다."
        }
    ]

    print("\n[고정 질문 5개]")
    for i, qa in enumerate(situational_fixed_answers, 1):
        print(f"\n[Q{i}] {qa['question']}")
        print(f"[A{i}] {qa['answer']}")

        if i == 1:
            situational_interview.get_next_question()
        situational_interview.submit_answer(qa['answer'])

    print("\n✅ 고정 질문 완료")

    # 실시간 추천 질문
    print("\n🤖 실시간 추천 질문 생성 중...")
    print(f"\n생성된 추천 질문: {len(situational_interview.dynamic_questions)}개")

    for i, q in enumerate(situational_interview.dynamic_questions, 1):
        print(f"\n[동적 Q{i}] {q.question}")
        print(f"[목적] {q.purpose}")

        dummy_answer = "네, 그렇게 생각합니다."
        print(f"[A] {dummy_answer}")
        situational_interview.submit_answer(dummy_answer)

    print("\n✅ Situational Interview 완료")

    # 분석
    print("\n📊 Situational 분석 중...")
    situational_profile = analyze_company_situational_interview(
        answers=situational_interview.get_answers(),
        general_analysis=general_analysis,
        technical_requirements=technical_requirements
    )

    print(f"\n[분석 결과]")
    print(f"- 팀 현황: {situational_profile.team_situation}")
    print(f"- 협업 스타일: {situational_profile.collaboration_style}")
    print(f"- 갈등 해결: {situational_profile.conflict_resolution}")
    print(f"- 업무 환경: {situational_profile.work_environment}")
    print(f"- 선호 스타일: {situational_profile.preferred_work_style}")

    # ==================== 4. Job Posting Card 생성 ====================
    print("\n\n[최종] Job Posting Card 생성")
    print("=" * 60)

    job_posting = generate_job_posting_card(
        company_name="FitConnect",
        general_analysis=general_analysis,
        technical_requirements=technical_requirements,
        situational_profile=situational_profile,
        existing_jd=None,
        deadline="2025-12-31"
    )

    print("\n📄 채용 공고 카드")
    print("-" * 60)
    print(f"회사명: {job_posting.company_name}")
    print(f"포지션: {job_posting.position_title}")
    print(f"마감일: {job_posting.deadline}")
    print()
    print(f"[공고 정보]")
    print(f"- 경력: {job_posting.experience_level}")
    print(f"- 근무 기간: {job_posting.contract_duration}")
    print(f"- 부서: {job_posting.department}")
    print(f"- 고용 형태: {job_posting.employment_type}")
    print(f"- 연봉: {job_posting.salary_info}")
    print()
    print(f"[주요 업무] ({len(job_posting.main_responsibilities)}개)")
    for i, resp in enumerate(job_posting.main_responsibilities, 1):
        print(f"  {i}. {resp}")
    print()
    print(f"[필수 역량] ({len(job_posting.required_skills)}개)")
    for i, skill in enumerate(job_posting.required_skills, 1):
        print(f"  {i}. {skill}")
    print()
    print(f"[우대 역량] ({len(job_posting.preferred_skills)}개)")
    for i, skill in enumerate(job_posting.preferred_skills, 1):
        print(f"  {i}. {skill}")
    print()
    print(f"[기업 정보]")
    print(f"- 투자 단계: {job_posting.company_info.funding_stage}")
    print(f"- 조직 문화: {job_posting.company_info.company_culture}")
    print(f"- 복리후생: {', '.join(job_posting.company_info.benefits) if job_posting.company_info.benefits else '없음'}")
    print()
    print(f"[인재상]")
    print(f"{job_posting.personality_fit}")
    print()
    print(f"[도전 과제]")
    print(f"{job_posting.challenges}")

    print("\n" + "=" * 60)
    print("✅ 전체 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_company_interview_flow())
