#!/usr/bin/env python3
"""
Talent Interview End-to-End Flow Test

구조화 → 직무 → 상황 면접을 순서대로 진행하고,
프로필 카드 생성과 매칭 벡터 생성까지 확인하는 스크립트입니다.

실행 전 준비:
1. `poetry shell` 또는 가상환경 활성화
2. `.env`에 `OPENAI_API_KEY` 설정 (필수)
3. 필요한 경우 `BACKEND_API_URL`은 무시됩니다. 모든 데이터는 샘플로 생성합니다.

실행:
    python test_talent_interview_flow.py
"""

from __future__ import annotations

import textwrap
from itertools import cycle

from dotenv import load_dotenv

from ai.interview.talent import (
    GeneralInterview,
    analyze_general_interview,
    analyze_general_interview_for_card,
    TechnicalInterview,
    analyze_technical_interview_for_card,
    SituationalInterview,
    analyze_situational_interview_for_card,
    generate_candidate_profile_card,
    convert_card_to_backend_format,
)
from ai.interview.talent.models import (
    CandidateProfile,
    TalentBasic,
    Experience,
    Education,
    Activity,
    Certification,
    FinalPersonaReport,
)
from ai.matching.vector_generator import generate_talent_matching_vectors


def create_sample_profile() -> CandidateProfile:
    """테스트용 더미 프로필 데이터 생성."""
    return CandidateProfile(
        basic=TalentBasic(
            user_id=1,
            name="홍길동",
            tagline="백엔드 개발자",
            is_submitted=True,
        ),
        experiences=[
            Experience(
                id=1,
                user_id=1,
                company_name="테크파이브",
                title="Senior Backend Engineer",
                start_ym="2021-03",
                end_ym=None,
                duration_years=3,
                summary="Python, FastAPI, PostgreSQL, Redis, AWS, Microservices",
            ),
            Experience(
                id=2,
                user_id=1,
                company_name="클라우드웨이브",
                title="Backend Engineer",
                start_ym="2018-01",
                end_ym="2021-02",
                duration_years=3,
                summary="Django, Celery, RabbitMQ, Docker, Kubernetes",
            ),
        ],
        educations=[
            Education(
                id=1,
                user_id=1,
                school_name="서울대학교",
                major="컴퓨터공학",
                status="졸업",
                start_ym="2012-03",
                end_ym="2016-02",
            )
        ],
        activities=[
            Activity(
                id=1,
                user_id=1,
                name="오픈소스 멘토링",
                category="대외활동",
                description="주니어 개발자 대상 비동기 처리 워크숍 진행",
            )
        ],
        certifications=[
            Certification(
                id=1,
                user_id=1,
                name="정보처리기사",
                acquired_ym="2016-05",
            )
        ],
    )


def simulate_general_interview() -> tuple[GeneralInterview, list[str]]:
    """구조화 면접 진행 및 답변 컬렉션."""
    general_interview = GeneralInterview()
    sample_answers = [
        "안녕하세요. 최근에는 AI 추천 시스템 백엔드 고도화 프로젝트에 몰입했습니다. FastAPI와 Redis를 활용해 응답 속도를 60% 개선했습니다.",
        "가장 의미 있었던 프로젝트는 대규모 채팅 서비스입니다. WebSocket과 Kafka를 조합해 동시 접속자 5만명을 안정적으로 처리했습니다.",
        "저는 코드 리뷰와 페어 프로그래밍을 즐깁니다. 팀원들이 어려워하는 부분을 함께 해결하며 지식 공유를 적극적으로 합니다.",
        "고객 경험과 데이터 기반 의사결정을 가장 중요하게 생각합니다. 성능과 안정성을 위해 꼼꼼히 모니터링하고 개선합니다.",
        "시니어 백엔드 엔지니어로 성장해 분산 시스템 아키텍처 전문가가 되고 싶습니다. 클라우드 네이티브 환경에서 대규모 트래픽을 다루고자 합니다.",
    ]

    print("\n[1] General Interview")
    question = general_interview.get_next_question()
    for answer in sample_answers:
        if not question:
            print("  (더 이상 질문이 없어 루프를 종료합니다.)")
            break

        print(f"Q: {question}")
        result = general_interview.submit_answer(answer)
        question = result["next_question"]

    return general_interview, sample_answers


def simulate_technical_interview(profile, general_analysis) -> TechnicalInterview:
    """직무 면접 진행 (질문 생성 + 답변 제출)."""
    technical_interview = TechnicalInterview(
        profile=profile,
        general_analysis=general_analysis,
        num_skills=2,
        questions_per_skill=2,
    )

    print("\n[2] Technical Interview")
    answer_templates = cycle(
        [
            "프로젝트에서 {skill}을 활용하여 확장성과 안정성을 확보했습니다. 문제 발생 시 로깅과 모니터링을 통해 빠르게 대응했습니다.",
            "{skill} 기반 서비스에서 성능 병목을 찾기 위해 프로파일링을 했고, 캐싱과 비동기 처리를 적용해 처리량을 높였습니다.",
        ]
    )

    question = technical_interview.get_next_question()
    while question:
        skill = question["skill"]
        print(f"Q ({question['progress']} / {skill}): {question['question']}")
        answer = next(answer_templates).format(skill=skill)
        result = technical_interview.submit_answer(answer)
        question = result["next_question"]

    return technical_interview


def simulate_situational_interview() -> tuple[SituationalInterview, FinalPersonaReport]:
    """상황 면접 진행."""
    situational_interview = SituationalInterview()
    sample_answers = cycle(
        [
            "의견이 나뉠 때는 먼저 팀원들의 우려를 구체적으로 듣고, 데이터와 사례를 근거로 공감대를 찾습니다.",
            "급한 이슈가 생기면 우선순위를 재정비하고, 필요한 자원을 확보해 단계적으로 해결합니다.",
            "새로운 분야는 공식 문서와 예제를 먼저 훑어보고, 작은 실험을 통해 학습합니다.",
            "강한 책임감을 가지고 주도적으로 업무를 리딩하면서도 팀원들과 정기적으로 싱크하여 공감대를 맞춥니다.",
            "문제가 발생하면 근본 원인을 분석하고, 팀과 함께 가설을 세워 실험을 반복합니다.",
            "치열한 상황에서도 차분함을 유지하고, 체크리스트와 사전 점검으로 리스크를 관리합니다.",
        ]
    )

    print("\n[3] Situational Interview")
    question = situational_interview.get_next_question()
    while question:
        print(f"Q ({question['progress']} / {question['phase']}): {question['question']}")
        result = situational_interview.submit_answer(next(sample_answers))
        question = result["next_question"]

    report = situational_interview.get_final_report()
    return situational_interview, report


def main():
    load_dotenv()

    profile = create_sample_profile()

    # 1. General Interview
    general_interview, _ = simulate_general_interview()
    general_answers = general_interview.get_answers()
    general_analysis = analyze_general_interview(general_answers)
    general_part = analyze_general_interview_for_card(
        candidate_profile=profile,
        general_analysis=general_analysis,
        answers=general_answers,
    )

    # 2. Technical Interview
    technical_interview = simulate_technical_interview(profile, general_analysis)
    technical_results = technical_interview.get_results()
    technical_part = analyze_technical_interview_for_card(
        candidate_profile=profile,
        technical_results=technical_results,
    )

    # 3. Situational Interview
    situational_interview, situational_report = simulate_situational_interview()
    situational_part = analyze_situational_interview_for_card(
        candidate_profile=profile,
        situational_report=situational_report,
        qa_history=situational_interview.qa_history,
        general_part=general_part,
        technical_part=technical_part,
    )

    # 4. Profile Card 생성 및 변환
    card = generate_candidate_profile_card(
        candidate_profile=profile,
        general_part=general_part,
        technical_part=technical_part,
        situational_part=situational_part,
    )
    backend_payload = convert_card_to_backend_format(card, profile)

    print("\n[4] Candidate Profile Card (요약)")
    print(f"- 이름: {card.candidate_name}")
    print(f"- 직무: {card.role}")
    print(f"- 경력: {card.experience_years}년 / 현재 회사: {card.company}")
    print(f"- 주요 경험: {card.key_experiences}")
    print(f"- 강점: {card.strengths}")
    print(f"- 직무 역량: {[f'{s.name}({s.level})' for s in card.technical_skills]}")
    print(f"- 직무 적합성: {card.job_fit}")
    print(f"- 협업 성향: {card.team_fit}")
    print(f"- 성장 가능성: {card.growth_potential}")

    print("\n[백엔드 전송 형태]")
    for key, value in backend_payload.items():
        if isinstance(value, list):
            formatted = textwrap.shorten(", ".join(map(str, value)), width=120, placeholder=" ...")
            print(f"- {key}: {formatted}")
        else:
            print(f"- {key}: {value}")

    # 5. Matching Vectors
    matching_result = generate_talent_matching_vectors(
        candidate_profile=profile,
        general_analysis=general_analysis,
        technical_results=technical_results,
        situational_report=situational_report,
    )

    print("\n[5] Matching Texts (요약)")
    for key, text in matching_result["texts"].items():
        snippet = textwrap.shorten(text, width=100, placeholder=" ...")
        print(f"- {key}: {snippet}")

    print("\n[완료] 전체 플로우를 성공적으로 수행했습니다.")


if __name__ == "__main__":
    main()
