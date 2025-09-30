#!/usr/bin/env python3
"""
면접 분석 테스트 (STT + LLM) - 개선된 플로우
"""

import asyncio
import json
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

from ai.stt.service import get_stt_service
from ai.llm.service import get_llm_service
from ai.embedding.service import get_embedding_service

# 샘플 면접 텍스트들
SAMPLE_INTERVIEWS = [
    {
        "name": "경력직 백엔드 개발자 면접",
        "text": """
        안녕하세요. 저는 5년간 백엔드 개발을 해온 김개발입니다.

        이전 회사인 네이버에서는 주로 대용량 API 서버 개발을 담당했습니다.
        Python과 Django를 주로 사용했고, 최근에는 FastAPI로 마이크로서비스 아키텍처를 구축하는 경험도 했습니다.

        저의 강점은 문제 해결 능력이라고 생각합니다.
        복잡한 시스템 이슈가 발생했을 때 차근차근 원인을 분석하고 해결하는 것을 좋아합니다.

        팀워크도 중시합니다. 코드 리뷰를 통해 동료들과 지식을 공유하고,
        주니어 개발자들을 멘토링하는 역할도 자주 맡았습니다.

        앞으로는 시스템 아키텍처 설계 전문가가 되고 싶습니다.
        특히 클라우드 네이티브 환경에서 확장 가능한 시스템을 구축하는 일에 관심이 많습니다.

        업무 환경은 자율적이고 수평적인 조직문화를 선호합니다.
        기술적 도전이 있는 프로젝트에서 일하고 싶고, 원격근무가 가능한 환경이면 더 좋겠습니다.
        """
    },
    {
        "name": "신입 프론트엔드 개발자 면접",
        "text": """
        안녕하세요. 컴퓨터공학과를 졸업한 신입 개발자 박신입입니다.

        대학교에서 React와 JavaScript를 주로 공부했고,
        졸업 프로젝트로 실시간 채팅 애플리케이션을 개발했습니다.

        개인적으로 사용자 경험에 대해 관심이 많습니다.
        단순히 기능이 작동하는 것을 넘어서, 사용자가 편리하고 즐겁게 사용할 수 있는 인터페이스를 만들고 싶습니다.

        저는 꼼꼼한 성격이고 새로운 것을 배우는 것을 좋아합니다.
        최근에는 TypeScript와 Next.js를 독학으로 공부하고 있습니다.

        팀 프로젝트에서는 주로 커뮤니케이션 역할을 맡았습니다.
        팀원들의 의견을 잘 들어주고 조율하는 편입니다.

        목표는 풀스택 개발자가 되는 것입니다.
        지금은 프론트엔드에 집중하고 있지만, 나중에는 백엔드도 할 수 있는 개발자가 되고 싶습니다.

        빠르게 성장할 수 있는 스타트업 환경에서 일하고 싶습니다.
        멘토링을 받을 수 있고, 다양한 경험을 쌓을 수 있는 곳이면 좋겠습니다.
        """
    },
    {
        "name": "데이터 사이언티스트 면접",
        "text": """
        안녕하세요. 데이터 분석 분야에서 3년간 일해온 이데이터입니다.

        이전 회사에서는 주로 고객 행동 분석과 추천 시스템 개발을 담당했습니다.
        Python과 pandas, scikit-learn을 주로 사용했고,
        최근에는 TensorFlow와 PyTorch로 딥러닝 모델링도 하고 있습니다.

        저의 강점은 데이터에서 의미있는 인사이트를 찾아내는 능력입니다.
        복잡한 데이터를 시각화해서 비즈니스 팀이 이해하기 쉽게 전달하는 것도 잘합니다.

        또한 비즈니스 감각도 갖추려고 노력합니다.
        단순히 모델 성능만 높이는 것이 아니라, 실제 비즈니스 가치를 만들어내는 것이 중요하다고 생각합니다.

        의사소통 능력도 중요하게 생각합니다.
        개발팀, 기획팀과 협업할 때 서로 다른 관점을 이해하고 조율하는 역할을 자주 했습니다.

        앞으로는 MLOps 분야로 확장하고 싶습니다.
        모델을 개발하는 것뿐만 아니라 프로덕션 환경에 안정적으로 배포하고 운영하는 전 과정을 경험해보고 싶습니다.

        데이터 중심의 의사결정을 하는 회사에서 일하고 싶습니다.
        AI/ML 기술이 핵심인 프로덕트를 만드는 팀이면 더욱 좋겠습니다.
        """
    }
]

# 더미 DB 프로필 데이터
DUMMY_DB_PROFILES = [
    {
        "user_id": 1,
        "profile": {"name": "김개발", "birth_date": "1990-01-01"},
        "educations": [
            {
                "school_name": "서울대학교",
                "major": "컴퓨터공학",
                "status": "졸업",
                "start_ym": "2012-03",
                "end_ym": "2016-02"
            }
        ],
        "experiences": [
            {
                "company_name": "네이버",
                "title": "백엔드 개발자",
                "start_ym": "2016-03",
                "end_ym": "2021-12",
                "summary": "대용량 API 서버 개발 및 운영"
            },
            {
                "company_name": "현재회사",
                "title": "시니어 백엔드 개발자",
                "start_ym": "2022-01",
                "end_ym": None,
                "summary": "마이크로서비스 아키텍처 구축"
            }
        ],
        "activities": [
            {
                "name": "오픈소스 기여",
                "category": "개발",
                "description": "Django, FastAPI 오픈소스 프로젝트 기여"
            }
        ],
        "certifications": [
            {
                "name": "AWS Solutions Architect",
                "acquired_ym": "2020-06"
            }
        ]
    },
    {
        "user_id": 2,
        "profile": {"name": "박신입", "birth_date": "1998-05-15"},
        "educations": [
            {
                "school_name": "연세대학교",
                "major": "컴퓨터공학",
                "status": "졸업",
                "start_ym": "2018-03",
                "end_ym": "2024-02"
            }
        ],
        "experiences": [],  # 신입이므로 경력 없음
        "activities": [
            {
                "name": "졸업 프로젝트",
                "category": "프로젝트",
                "description": "React 기반 실시간 채팅 애플리케이션"
            },
            {
                "name": "프로그래밍 동아리",
                "category": "동아리",
                "description": "웹 개발 스터디 리더"
            }
        ],
        "certifications": []
    }
]

def test_interview_analysis_only(interview_data):
    """면접 분석만 테스트 (STT 제외, 텍스트 직접 사용)"""
    print(f"\n🎤 {interview_data['name']} 분석 중...")
    print("=" * 50)

    try:
        # LLM으로 면접 내용 분석
        llm_service = get_llm_service()

        # 프롬프트 모듈에서 가져오기
        from ai.llm.prompts import build_interview_analysis_messages

        messages = build_interview_analysis_messages(interview_data['text'])

        response = llm_service.generate_completion(messages=messages, temperature=0.7)

        print("✅ 면접 분석 완료!")
        print(f"응답 길이: {len(response.content)} 글자")
        print(f"사용 모델: {response.model}")

        # JSON 파싱 시도 (개선된 파싱 로직)
        from ai.llm.utils import parse_llm_json_response, format_list_display, format_text_display

        analysis = parse_llm_json_response(response.content)

        if analysis:
            print("\n📊 구조화된 분석 결과:")
            for key, value in analysis.items():
                if isinstance(value, list):
                    print(f"  {key}: {format_list_display(value)}")
                else:
                    print(f"  {key}: {format_text_display(str(value), 80)}")

            return analysis
        else:
            print("⚠️  JSON 파싱 실패, 원본 텍스트 응답:")
            print(response.content[:300] + "...")
            return {"raw_response": response.content}

    except Exception as e:
        print(f"❌ 면접 분석 실패: {e}")
        return None

def test_db_interview_integration(db_profile, interview_analysis):
    """DB 프로필 + 면접 분석 통합 테스트"""
    print(f"\n🔗 DB + 면접 통합 분석 테스트")
    print("=" * 50)

    try:
        llm_service = get_llm_service()

        # 프롬프트 모듈에서 가져오기
        from ai.llm.prompts import build_integration_messages

        messages = build_integration_messages(db_profile, interview_analysis)
        response = llm_service.generate_completion(messages=messages, temperature=0.5)

        print("✅ 통합 분석 완료!")

        # JSON 파싱 시도 (개선된 파싱 로직)
        from ai.llm.utils import parse_llm_json_response, format_list_display, format_text_display

        integrated_profile = parse_llm_json_response(response.content)

        if integrated_profile:
            print("\n🎯 최종 통합 프로필:")
            for key, value in integrated_profile.items():
                if isinstance(value, list):
                    print(f"  {key}: {format_list_display(value, 4)}")
                else:
                    print(f"  {key}: {format_text_display(str(value), 100)}")

            return integrated_profile
        else:
            print("⚠️  JSON 파싱 실패, 원본 응답:")
            print(response.content[:400] + "...")
            return {"raw_response": response.content}

    except Exception as e:
        print(f"❌ 통합 분석 실패: {e}")
        return None

def test_embedding_generation(integrated_profile):
    """통합 프로필로 임베딩 벡터 생성 테스트"""
    print(f"\n🔢 임베딩 벡터 생성 테스트")
    print("=" * 50)

    try:
        embedding_service = get_embedding_service()

        # 프로필에서 텍스트 추출 (안전하게)
        from ai.llm.utils import safe_get_from_dict, format_text_display

        preferences = safe_get_from_dict(integrated_profile, 'work_preferences', '업무 환경 선호사항 없음')
        technical_skills = safe_get_from_dict(integrated_profile, 'technical_skills', [])
        soft_skills = safe_get_from_dict(integrated_profile, 'soft_skills', [])

        skills = ', '.join(technical_skills + soft_skills)
        if not skills.strip():
            skills = '스킬 정보 없음'

        print(f"선호사항: {format_text_display(preferences, 100)}")
        print(f"스킬: {format_text_display(skills, 100)}")

        # 임베딩 벡터 생성
        candidate_vector = embedding_service.create_applicant_vector(
            preferences=preferences,
            skills=skills
        )

        print("✅ 임베딩 벡터 생성 완료!")
        print(f"벡터 차원: {candidate_vector.dimension}")
        print(f"사용 모델: {candidate_vector.model}")
        print(f"일반 벡터 크기: {len(candidate_vector.general_vector)}")
        print(f"스킬 벡터 크기: {len(candidate_vector.skills_vector)}")
        print(f"통합 벡터 크기: {len(candidate_vector.combined_vector)}")

        return candidate_vector

    except Exception as e:
        print(f"❌ 임베딩 생성 실패: {e}")
        return None

def main():
    """메인 테스트 실행"""
    print("🚀 개선된 면접 분석 플로우 테스트")
    print("=" * 60)

    # LLM 서비스 상태 확인
    llm_service = get_llm_service()
    health = llm_service.health_check()

    if health.get('status') != 'healthy':
        print("❌ LLM 서비스가 정상적이지 않습니다. API 키를 확인해주세요.")
        print(f"실제 헬스체크 결과: {health}")
        return

    # 임베딩 서비스 상태 확인
    embedding_service = get_embedding_service()
    embedding_health = embedding_service.health_check()
    print(f"📊 서비스 상태 - LLM: {health.get('status')}, 임베딩: {embedding_health.service_status}")

    # 각 샘플에 대해 전체 플로우 테스트
    for i, (interview, db_profile) in enumerate(zip(SAMPLE_INTERVIEWS, DUMMY_DB_PROFILES)):
        print(f"\n{'='*20} 테스트 케이스 {i+1} {'='*20}")

        # 1. 면접 분석
        interview_analysis = test_interview_analysis_only(interview)
        if not interview_analysis:
            continue

        # 2. DB + 면접 통합
        integrated_profile = test_db_interview_integration(db_profile, interview_analysis)
        if not integrated_profile:
            continue

        # 3. 임베딩 벡터 생성
        candidate_vector = test_embedding_generation(integrated_profile)

        print(f"\n✅ 케이스 {i+1} 완료!")

    print("\n" + "=" * 60)
    print("🎉 전체 테스트 완료!")
    print("\n🎯 결과 요약:")
    print("- 면접 내용만 LLM 분석 (STT 제외)")
    print("- DB 데이터는 구조화된 상태로 직접 사용")
    print("- 두 결과를 LLM으로 통합")
    print("- 최종 프로필로 임베딩 벡터 생성")

if __name__ == "__main__":
    main()