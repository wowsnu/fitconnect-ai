#!/usr/bin/env python3
"""
필터링이 통합된 매칭 시스템 테스트
1단계: 필수조건 필터 + 벡터 매칭
"""

import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

from ai.embedding.service import get_embedding_service
from ai.matching.service import get_matching_service
from ai.matching.filters import get_filter_service

# 테스트용 샘플 데이터 (필터 정보 포함)
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
        "id": "user_004",  # 필터에서 탈락할 후보
        "preferences": "아무 회사나, 부산 근무, 연봉 3000만원",
        "skills": "HTML, CSS, JavaScript, 1년 프론트엔드 경험",
        "profile": {
            "years_experience": 1,  # 경력 부족
            "preferred_locations": ["부산"],  # 지역 불일치
            "preferred_employment_types": ["인턴"],
            "salary_expectation_min": 2500,
            "salary_expectation_max": 3500,
            "korean_level": 5,
            "english_level": 1,
            "remote_work_ok": False
        }
    }
]

def test_filter_only():
    """필터링만 단독 테스트"""
    print("🔍 필터링 시스템 단독 테스트")
    print("=" * 50)

    try:
        filter_service = get_filter_service()

        # 1. 구직자 필터링 테스트
        print("👤 구직자 필터링 테스트 (job_001 요구사항):")
        job_001_requirements = SAMPLE_JOBS_WITH_REQUIREMENTS[0]["requirements"]

        candidates = [applicant["profile"] for applicant in SAMPLE_APPLICANTS_WITH_PREFERENCES]
        for i, applicant in enumerate(SAMPLE_APPLICANTS_WITH_PREFERENCES):
            candidates[i]["id"] = applicant["id"]

        filtered_candidates = filter_service.filter_candidates(
            candidates=candidates,
            job_requirements=job_001_requirements
        )

        print(f"원본 후보: {len(candidates)}명")
        print(f"필터 통과: {len(filtered_candidates)}명")

        for candidate in candidates:
            status = "✅ 통과" if candidate.get("filter_passed", False) else "❌ 탈락"
            reason = candidate.get("filter_reason", "")
            print(f"  {candidate['id']}: {status} - {reason}")

        # 2. 공고 필터링 테스트
        print("\n🏢 공고 필터링 테스트 (user_001 선호조건):")
        user_001_preferences = SAMPLE_APPLICANTS_WITH_PREFERENCES[0]["profile"]

        jobs = [job["requirements"] for job in SAMPLE_JOBS_WITH_REQUIREMENTS]
        for i, job in enumerate(SAMPLE_JOBS_WITH_REQUIREMENTS):
            jobs[i]["id"] = job["id"]

        filtered_jobs = filter_service.filter_jobs(
            jobs=jobs,
            applicant_preferences=user_001_preferences
        )

        print(f"원본 공고: {len(jobs)}개")
        print(f"필터 통과: {len(filtered_jobs)}개")

        for job in jobs:
            status = "✅ 통과" if job.get("filter_passed", False) else "❌ 탈락"
            reason = job.get("filter_reason", "")
            print(f"  {job['id']}: {status} - {reason}")

        return True

    except Exception as e:
        print(f"❌ 필터링 테스트 실패: {e}")
        return False

def test_integrated_matching():
    """필터링 + 벡터 매칭 통합 테스트"""
    print("\n🎯 통합 매칭 테스트 (필터 + 벡터)")
    print("=" * 50)

    try:
        # 임베딩 및 매칭 서비스 초기화
        embedding_service = get_embedding_service()
        matching_service = get_matching_service()

        # 1. 벡터 생성
        print("🔢 벡터 생성 중...")

        # 공고 벡터 생성
        job_vectors = {}
        job_data_with_vectors = []

        for job in SAMPLE_JOBS_WITH_REQUIREMENTS:
            vector = embedding_service.create_job_vector(
                company_info=job["company_info"],
                required_skills=job["required_skills"]
            )
            job_vectors[job["id"]] = vector

            # 매칭용 데이터 구성
            job_data = {
                "id": job["id"],
                "vector": vector.combined_vector,
                **job["requirements"]  # 필터링용 요구사항 포함
            }
            job_data_with_vectors.append(job_data)

        # 구직자 벡터 생성
        applicant_vectors = {}
        applicant_data_with_vectors = []

        for applicant in SAMPLE_APPLICANTS_WITH_PREFERENCES:
            vector = embedding_service.create_applicant_vector(
                preferences=applicant["preferences"],
                skills=applicant["skills"]
            )
            applicant_vectors[applicant["id"]] = vector

            # 매칭용 데이터 구성
            applicant_data = {
                "id": applicant["id"],
                "vector": vector.combined_vector,
                **applicant["profile"]  # 필터링용 프로필 포함
            }
            applicant_data_with_vectors.append(applicant_data)

        print(f"벡터 생성 완료: 공고 {len(job_vectors)}개, 구직자 {len(applicant_vectors)}명")

        # 2. 구직자 관점 매칭 (user_001이 공고 찾기)
        print("\n👤 구직자 관점 매칭 (user_001 → 공고들):")

        user_001_vector = applicant_vectors["user_001"]
        user_001_preferences = SAMPLE_APPLICANTS_WITH_PREFERENCES[0]["profile"]

        result = matching_service.match_with_filters(
            query_vector=user_001_vector.combined_vector,
            candidates=job_data_with_vectors,
            query_requirements=user_001_preferences,
            query_id="user_001",
            query_type="applicant",
            top_n=5
        )

        print(f"매칭 결과: {len(result.matches)}개")
        print(f"필터링 통계: {result.filters_applied}")

        for i, match in enumerate(result.matches, 1):
            print(f"  {i}. {match.job_id}: 점수 {match.score:.4f} "
                  f"(cos:{match.cosine_similarity:.3f}, euc:{match.euclidean_distance:.3f})")

        # 3. 공고 관점 매칭 (job_001이 구직자 찾기)
        print("\n🏢 공고 관점 매칭 (job_001 → 구직자들):")

        job_001_vector = job_vectors["job_001"]
        job_001_requirements = SAMPLE_JOBS_WITH_REQUIREMENTS[0]["requirements"]

        result = matching_service.match_with_filters(
            query_vector=job_001_vector.combined_vector,
            candidates=applicant_data_with_vectors,
            query_requirements=job_001_requirements,
            query_id="job_001",
            query_type="job",
            top_n=5
        )

        print(f"매칭 결과: {len(result.matches)}개")
        print(f"필터링 통계: {result.filters_applied}")

        for i, match in enumerate(result.matches, 1):
            print(f"  {i}. {match.applicant_id}: 점수 {match.score:.4f} "
                  f"(cos:{match.cosine_similarity:.3f}, euc:{match.euclidean_distance:.3f})")

        return True

    except Exception as e:
        print(f"❌ 통합 매칭 테스트 실패: {e}")
        return False

def compare_with_without_filters():
    """필터 있음/없음 비교 테스트"""
    print("\n📊 필터 효과 비교 테스트")
    print("=" * 50)

    try:
        embedding_service = get_embedding_service()
        matching_service = get_matching_service()

        # 벡터 생성 (간단히)
        user_001 = SAMPLE_APPLICANTS_WITH_PREFERENCES[0]
        user_001_vector = embedding_service.create_applicant_vector(
            preferences=user_001["preferences"],
            skills=user_001["skills"]
        )

        job_data = []
        for job in SAMPLE_JOBS_WITH_REQUIREMENTS:
            vector = embedding_service.create_job_vector(
                company_info=job["company_info"],
                required_skills=job["required_skills"]
            )
            job_data.append({
                "id": job["id"],
                "vector": vector.combined_vector,
                **job["requirements"]
            })

        # 1. 필터 없이 매칭 (기존 방식)
        print("1️⃣ 필터 없는 매칭:")
        basic_matches = []
        for job in job_data:
            result = matching_service.match_single(
                job_vector=job["vector"],
                applicant_vector=user_001_vector.combined_vector,
                job_id=job["id"],
                applicant_id="user_001"
            )
            basic_matches.append(result)

        basic_matches.sort(key=lambda x: x.score, reverse=True)
        for match in basic_matches:
            print(f"  {match.job_id}: {match.score:.4f}")

        # 2. 필터 있는 매칭
        print("\n2️⃣ 필터 있는 매칭:")
        filtered_result = matching_service.match_with_filters(
            query_vector=user_001_vector.combined_vector,
            candidates=job_data,
            query_requirements=user_001["profile"],
            query_id="user_001",
            query_type="applicant"
        )

        for match in filtered_result.matches:
            print(f"  {match.job_id}: {match.score:.4f} ✅ 필터 통과")

        print(f"\n📈 필터 효과:")
        print(f"  필터 전: {len(basic_matches)}개 공고")
        print(f"  필터 후: {len(filtered_result.matches)}개 공고")
        print(f"  필터링율: {(len(basic_matches) - len(filtered_result.matches))/len(basic_matches)*100:.1f}%")

        return True

    except Exception as e:
        print(f"❌ 비교 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 실행"""
    print("🎯 필터링 통합 매칭 시스템 테스트")
    print("=" * 60)

    # 1. 필터링만 테스트
    filter_ok = test_filter_only()

    # 2. 통합 매칭 테스트
    if filter_ok:
        integrated_ok = test_integrated_matching()

        # 3. 비교 테스트
        if integrated_ok:
            compare_with_without_filters()

    print("\n" + "=" * 60)
    print("🎉 1단계 필터링 시스템 테스트 완료!")
    print("\n💡 주요 개선사항:")
    print("- ✅ 필수조건 필터링으로 부적합 후보 제거")
    print("- ✅ 경력, 지역, 급여, 언어 등 하드 조건 적용")
    print("- ✅ 필터 통과 후보만 벡터 매칭으로 정밀 순위")
    print("- ✅ 구직자/공고 양방향 매칭 지원")

if __name__ == "__main__":
    main()