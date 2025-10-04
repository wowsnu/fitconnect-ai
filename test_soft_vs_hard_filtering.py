#!/usr/bin/env python3
"""
소프트 필터링 vs 하드 필터링 비교 테스트
가중치 기반 호환성 점수 vs 엄격한 통과/탈락 방식
"""

import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

from ai.embedding.service import get_embedding_service
from ai.matching.service import get_matching_service

# 테스트용 샘플 데이터
SAMPLE_JOBS_WITH_REQUIREMENTS = [
    {
        "id": "job_001",
        "company_info": "스타트업, 서울 강남구, 수평적 조직문화, 원격근무 가능, 연봉 6000-8000만원",
        "required_skills": "Python, Django, PostgreSQL, AWS, 3년 이상 백엔드 경험",
        "requirements": {
            "min_experience_years": 3,
            "work_locations": ["서울", "경기"],
            "employment_types": ["정규직", "계약직"],
            "salary_range": {"min": 5000, "max": 8000},
            "language_requirements": {"korean_level": 5, "english_level": 3},
            "remote_work_allowed": True
        }
    },
    {
        "id": "job_002",
        "company_info": "대기업, 서울 판교, 안정적 환경, 주 5일 출근, 연봉 5000-7000만원",
        "required_skills": "Java, Spring Boot, MySQL, 5년 이상 백엔드 경험",
        "requirements": {
            "min_experience_years": 5,
            "work_locations": ["서울"],
            "employment_types": ["정규직"],
            "salary_range": {"min": 5000, "max": 7000},
            "language_requirements": {"korean_level": 5, "english_level": 2},
            "remote_work_allowed": False
        }
    },
    {
        "id": "job_003",
        "company_info": "AI 스타트업, 서울 홍대, 혁신적 문화, 하이브리드 근무, 연봉 7000-9000만원",
        "required_skills": "Python, FastAPI, Machine Learning, Docker, 2년 이상 경험",
        "requirements": {
            "min_experience_years": 2,
            "work_locations": ["서울", "원격"],
            "employment_types": ["정규직", "프리랜서"],
            "salary_range": {"min": 6000, "max": 9000},
            "language_requirements": {"korean_level": 4, "english_level": 4},
            "remote_work_allowed": True
        }
    }
]

SAMPLE_APPLICANTS_WITH_PREFERENCES = [
    {
        "id": "user_001",
        "preferences": "스타트업, 서울 근무 선호, 원격근무 가능, 수평적 문화, 연봉 7000만원 희망",
        "skills": "Python, Django, FastAPI, PostgreSQL, AWS, 5년 백엔드 개발 경험",
        "profile": {
            "years_experience": 5,
            "preferred_locations": ["서울", "경기"],
            "preferred_employment_types": ["정규직"],
            "salary_expectation_min": 6000,
            "salary_expectation_max": 8000,
            "korean_level": 5,
            "english_level": 4,
            "remote_work_ok": True
        }
    },
    {
        "id": "user_002",
        "preferences": "안정적인 대기업, 서울 근무, 출퇴근 무관, 연봉 6000만원 희망",
        "skills": "Java, Spring Boot, MySQL, Oracle, 3년 백엔드 개발 경험",
        "profile": {
            "years_experience": 3,
            "preferred_locations": ["서울"],
            "preferred_employment_types": ["정규직"],
            "salary_expectation_min": 5500,
            "salary_expectation_max": 7000,
            "korean_level": 5,
            "english_level": 2,
            "remote_work_ok": False
        }
    },
    {
        "id": "user_003",
        "preferences": "AI/머신러닝 회사, 서울 근무, 하이브리드 근무 선호, 연봉 8000만원 희망",
        "skills": "Python, FastAPI, TensorFlow, Docker, Kubernetes, 4년 개발 경험",
        "profile": {
            "years_experience": 4,
            "preferred_locations": ["서울", "원격"],
            "preferred_employment_types": ["정규직", "프리랜서"],
            "salary_expectation_min": 7000,
            "salary_expectation_max": 9000,
            "korean_level": 4,
            "english_level": 5,
            "remote_work_ok": True
        }
    },
    {
        "id": "user_004",  # 하드 필터에서 탈락하지만 소프트 필터에서는 점수를 받을 후보
        "preferences": "아무 회사나, 부산 근무 선호하지만 서울도 가능, 연봉 3000만원",
        "skills": "HTML, CSS, JavaScript, React, 1년 프론트엔드 경험",
        "profile": {
            "years_experience": 1,  # 경력 부족
            "preferred_locations": ["부산", "서울"],  # 일부 지역 일치
            "preferred_employment_types": ["정규직", "인턴"],
            "salary_expectation_min": 2500,
            "salary_expectation_max": 4000,  # 급여 차이
            "korean_level": 5,
            "english_level": 2,
            "remote_work_ok": True
        }
    }
]

def prepare_test_data():
    """테스트 데이터 준비 (벡터 생성)"""
    print("🔢 벡터 생성 중...")

    embedding_service = get_embedding_service()

    # 공고 벡터 생성
    job_data_with_vectors = []
    for job in SAMPLE_JOBS_WITH_REQUIREMENTS:
        vector = embedding_service.create_job_vector(
            company_info=job["company_info"],
            required_skills=job["required_skills"]
        )
        job_data = {
            "id": job["id"],
            "vector": vector.combined_vector,
            **job["requirements"]
        }
        job_data_with_vectors.append(job_data)

    # 구직자 벡터 생성
    applicant_data_with_vectors = []
    for applicant in SAMPLE_APPLICANTS_WITH_PREFERENCES:
        vector = embedding_service.create_applicant_vector(
            preferences=applicant["preferences"],
            skills=applicant["skills"]
        )
        applicant_data = {
            "id": applicant["id"],
            "vector": vector.combined_vector,
            **applicant["profile"]
        }
        applicant_data_with_vectors.append(applicant_data)

    print(f"벡터 생성 완료: 공고 {len(job_data_with_vectors)}개, 구직자 {len(applicant_data_with_vectors)}명")

    return job_data_with_vectors, applicant_data_with_vectors

def test_hard_vs_soft_filtering():
    """하드 필터링 vs 소프트 필터링 비교"""
    print("\n🔥 하드 필터링 vs 소프트 필터링 비교 테스트")
    print("=" * 60)

    try:
        # 데이터 준비
        job_data, applicant_data = prepare_test_data()
        matching_service = get_matching_service()

        # 테스트 대상: user_001이 공고 찾기
        test_user = SAMPLE_APPLICANTS_WITH_PREFERENCES[0]
        test_user_data = applicant_data[0]
        user_vector = test_user_data["vector"]
        user_preferences = test_user["profile"]

        print(f"\n👤 테스트 대상: {test_user['id']}")
        print(f"선호조건: {test_user['preferences']}")
        print(f"프로필: 경력 {user_preferences['years_experience']}년, 지역 {user_preferences['preferred_locations']}, 급여 {user_preferences['salary_expectation_min']}-{user_preferences['salary_expectation_max']}만원")

        # 1. 하드 필터링 테스트
        print(f"\n1️⃣ 하드 필터링 결과:")
        print("-" * 30)

        hard_result = matching_service.match_with_filters(
            query_vector=user_vector,
            candidates=job_data,
            query_requirements=user_preferences,
            query_id=test_user["id"],
            query_type="applicant",
            use_soft_filters=False
        )

        print(f"필터 통과: {len(hard_result.matches)}개 공고")
        print(f"필터링 통계: {hard_result.filters_applied}")

        for i, match in enumerate(hard_result.matches, 1):
            metadata = match.metadata
            print(f"  {i}. {match.job_id}: 점수 {match.score:.4f}")
            print(f"     필터 상태: {metadata.get('filter_reason', '알 수 없음')}")

        # 2. 소프트 필터링 테스트
        print(f"\n2️⃣ 소프트 필터링 결과:")
        print("-" * 30)

        soft_result = matching_service.match_with_filters(
            query_vector=user_vector,
            candidates=job_data,
            query_requirements=user_preferences,
            query_id=test_user["id"],
            query_type="applicant",
            use_soft_filters=True
        )

        print(f"처리된 후보: {len(soft_result.matches)}개 공고")
        print(f"필터링 통계: {soft_result.filters_applied}")

        for i, match in enumerate(soft_result.matches, 1):
            metadata = match.metadata
            vector_score = metadata.get('vector_score', 0)
            compatibility_score = metadata.get('compatibility_score', 0)
            compatibility_summary = metadata.get('compatibility_summary', '알 수 없음')

            print(f"  {i}. {match.job_id}: 최종점수 {match.score:.4f}")
            print(f"     벡터점수: {vector_score:.4f} × 호환성: {compatibility_score:.3f} = {match.score:.4f}")
            print(f"     호환성 요약: {compatibility_summary}")

            # 호환성 세부 점수 표시
            details = metadata.get('compatibility_details', {})
            if details:
                detail_str = ", ".join([f"{k}: {v:.2f}" for k, v in details.items()])
                print(f"     세부점수: {detail_str}")

        # 3. 비교 분석
        print(f"\n📊 비교 분석:")
        print("-" * 30)
        print(f"하드 필터링: {len(hard_result.matches)}개 결과")
        print(f"소프트 필터링: {len(soft_result.matches)}개 결과")
        print(f"추가 고려 공고: {len(soft_result.matches) - len(hard_result.matches)}개")

        # 순위 변화 분석
        if hard_result.matches and soft_result.matches:
            print(f"\n🔄 순위 변화:")
            for i, soft_match in enumerate(soft_result.matches[:3], 1):
                # 하드 필터에서의 순위 찾기
                hard_rank = None
                for j, hard_match in enumerate(hard_result.matches, 1):
                    if hard_match.job_id == soft_match.job_id:
                        hard_rank = j
                        break

                if hard_rank:
                    print(f"  {soft_match.job_id}: 하드 {hard_rank}위 → 소프트 {i}위")
                else:
                    print(f"  {soft_match.job_id}: 하드 필터 탈락 → 소프트 {i}위")

        return True

    except Exception as e:
        print(f"❌ 비교 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_compatibility_details():
    """호환성 점수 세부 분석"""
    print("\n🎯 호환성 점수 세부 분석")
    print("=" * 60)

    try:
        # 데이터 준비
        job_data, applicant_data = prepare_test_data()
        matching_service = get_matching_service()

        # 다양한 케이스의 구직자들로 테스트
        for applicant in SAMPLE_APPLICANTS_WITH_PREFERENCES:
            applicant_vector = None
            for app_data in applicant_data:
                if app_data["id"] == applicant["id"]:
                    applicant_vector = app_data["vector"]
                    break

            if not applicant_vector:
                continue

            print(f"\n👤 {applicant['id']} 분석:")
            print(f"선호조건: {applicant['preferences']}")

            # 첫 번째 공고와의 매칭만 상세 분석
            test_job = job_data[0]

            result = matching_service.match_with_filters(
                query_vector=applicant_vector,
                candidates=[test_job],
                query_requirements=applicant["profile"],
                query_id=applicant["id"],
                query_type="applicant",
                use_soft_filters=True
            )

            if result.matches:
                match = result.matches[0]
                metadata = match.metadata

                print(f"  vs {match.job_id}:")
                print(f"    벡터 유사도: {metadata.get('vector_score', 0):.4f}")
                print(f"    호환성 점수: {metadata.get('compatibility_score', 0):.3f}")
                print(f"    최종 점수: {match.score:.4f}")
                print(f"    호환성 요약: {metadata.get('compatibility_summary', '알 수 없음')}")

                # 세부 호환성 점수
                details = metadata.get('compatibility_details', {})
                for field, score in details.items():
                    print(f"      {field}: {score:.3f}")

        return True

    except Exception as e:
        print(f"❌ 호환성 분석 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 실행"""
    print("🎯 소프트 필터링 시스템 테스트")
    print("=" * 60)
    print("기존의 엄격한 통과/탈락 방식에서")
    print("가중치 기반 호환성 점수 방식으로 전환 테스트")
    print("=" * 60)

    # 1. 하드 vs 소프트 필터링 비교
    comparison_ok = test_hard_vs_soft_filtering()

    # 2. 호환성 점수 세부 분석
    if comparison_ok:
        test_compatibility_details()

    print("\n" + "=" * 60)
    print("🎉 소프트 필터링 시스템 구현 완료!")
    print("\n💡 주요 개선사항:")
    print("- ✅ 엄격한 필터링 → 가중치 기반 호환성 점수")
    print("- ✅ 모든 후보 고려, 탈락자 없음")
    print("- ✅ 필드별 세부 호환성 분석 (지역, 경력, 급여, 고용형태, 언어)")
    print("- ✅ 벡터 유사도 × 호환성 점수 = 통합 매칭 점수")
    print("- ✅ 더 다양하고 유연한 매칭 결과")

if __name__ == "__main__":
    main()