#!/usr/bin/env python3
"""
간소화된 매칭 시스템 테스트
1. 구직자 → 공고 추천
2. 공고 → 구직자 추천
"""

import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

from ai.embedding.service import get_embedding_service
from ai.matching.service import get_matching_service

# 테스트용 샘플 데이터
SAMPLE_JOBS = [
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

SAMPLE_APPLICANTS = [
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
    }
]

def prepare_data():
    """테스트 데이터 준비"""
    print("🔢 벡터 생성 중...")

    embedding_service = get_embedding_service()

    # 공고 데이터 준비
    job_data = []
    for job in SAMPLE_JOBS:
        vector = embedding_service.create_job_vector(
            company_info=job["company_info"],
            required_skills=job["required_skills"]
        )
        job_data.append({
            "id": job["id"],
            "vector": vector.combined_vector,
            **job["requirements"]
        })

    # 구직자 데이터 준비
    applicant_data = []
    for applicant in SAMPLE_APPLICANTS:
        vector = embedding_service.create_applicant_vector(
            preferences=applicant["preferences"],
            skills=applicant["skills"]
        )
        applicant_data.append({
            "id": applicant["id"],
            "vector": vector.combined_vector,
            **applicant["profile"]
        })

    print(f"벡터 생성 완료: 공고 {len(job_data)}개, 구직자 {len(applicant_data)}명")
    return job_data, applicant_data

def test_job_recommendation():
    """구직자에게 공고 추천 테스트"""
    print("\n👤 구직자에게 공고 추천 테스트")
    print("=" * 50)

    try:
        job_data, applicant_data = prepare_data()
        matching_service = get_matching_service()

        # 테스트 구직자 선택
        test_applicant = applicant_data[0]  # user_001
        original_applicant = SAMPLE_APPLICANTS[0]

        print(f"구직자: {test_applicant['id']}")
        print(f"선호조건: {original_applicant['preferences']}")

        # 공고 추천
        result = matching_service.recommend_jobs_for_applicant(
            applicant_vector=test_applicant["vector"],
            job_candidates=job_data,
            applicant_preferences=test_applicant,
            applicant_id=test_applicant["id"],
            top_n=3
        )

        print(f"\n📋 추천 공고 ({len(result.matches)}개):")
        for i, match in enumerate(result.matches, 1):
            meta = match.metadata
            print(f"  {i}. {match.job_id}: 최종점수 {match.score:.4f}")
            print(f"     벡터점수: {meta['vector_score']:.4f} × 호환성: {meta['compatibility_score']:.3f}")
            print(f"     요약: {meta['compatibility_summary']}")

            # 세부 점수 표시
            details = meta['compatibility_details']
            detail_str = ", ".join([f"{k}: {v:.2f}" for k, v in details.items()])
            print(f"     세부: {detail_str}")

        return True

    except Exception as e:
        print(f"❌ 공고 추천 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_candidate_recommendation():
    """공고에 구직자 추천 테스트"""
    print("\n🏢 공고에 구직자 추천 테스트")
    print("=" * 50)

    try:
        job_data, applicant_data = prepare_data()
        matching_service = get_matching_service()

        # 테스트 공고 선택
        test_job = job_data[0]  # job_001
        original_job = SAMPLE_JOBS[0]

        print(f"공고: {test_job['id']}")
        print(f"요구사항: {original_job['required_skills']}")

        # 구직자 추천
        matches = matching_service.recommend_candidates_for_job(
            job_vector=test_job["vector"],
            applicant_candidates=applicant_data,
            job_requirements=test_job,
            job_id=test_job["id"],
            top_n=3
        )

        print(f"\n👥 추천 구직자 ({len(matches)}명):")
        for i, match in enumerate(matches, 1):
            meta = match.metadata
            print(f"  {i}. {match.applicant_id}: 최종점수 {match.score:.4f}")
            print(f"     벡터점수: {meta['vector_score']:.4f} × 호환성: {meta['compatibility_score']:.3f}")
            print(f"     요약: {meta['compatibility_summary']}")

            # 세부 점수 표시
            details = meta['compatibility_details']
            detail_str = ", ".join([f"{k}: {v:.2f}" for k, v in details.items()])
            print(f"     세부: {detail_str}")

        return True

    except Exception as e:
        print(f"❌ 구직자 추천 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 실행"""
    print("🎯 간소화된 매칭 시스템 테스트")
    print("=" * 60)
    print("소프트 필터링만 사용하는 깔끔한 매칭 시스템")
    print("=" * 60)

    # 1. 구직자 → 공고 추천
    job_rec_ok = test_job_recommendation()

    # 2. 공고 → 구직자 추천
    if job_rec_ok:
        test_candidate_recommendation()

    print("\n" + "=" * 60)
    print("🎉 간소화된 매칭 시스템 완료!")
    print("\n💡 특징:")
    print("- ✅ 하드 필터링 제거, 소프트 필터링만 사용")
    print("- ✅ 명확한 두 가지 매칭 방향")
    print("- ✅ 벡터 유사도 × 호환성 점수 = 통합 점수")
    print("- ✅ 모든 후보 고려, 더 유연한 매칭")

if __name__ == "__main__":
    main()