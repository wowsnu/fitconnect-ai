#!/usr/bin/env python3
"""
매칭 시스템 테스트
임베딩 → 벡터 → 매칭 스코어 전체 플로우 테스트
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
        "job_id": "job_001",
        "company_info": "스타트업, 서울 강남구, 수평적 조직문화, 원격근무 가능, 연봉 6000-8000만원",
        "required_skills": "Python, Django, PostgreSQL, AWS, 3년 이상 백엔드 경험"
    },
    {
        "job_id": "job_002",
        "company_info": "대기업, 서울 판교, 안정적 환경, 주 5일 출근, 연봉 5000-7000만원",
        "required_skills": "Java, Spring Boot, MySQL, 5년 이상 백엔드 경험"
    },
    {
        "job_id": "job_003",
        "company_info": "AI 스타트업, 서울 홍대, 혁신적 문화, 하이브리드 근무, 연봉 7000-9000만원",
        "required_skills": "Python, FastAPI, Machine Learning, Docker, 2년 이상 경험"
    }
]

SAMPLE_APPLICANTS = [
    {
        "applicant_id": "user_001",
        "preferences": "스타트업, 서울 근무 선호, 원격근무 가능, 수평적 문화, 연봉 7000만원 희망",
        "skills": "Python, Django, FastAPI, PostgreSQL, AWS, 5년 백엔드 개발 경험"
    },
    {
        "applicant_id": "user_002",
        "preferences": "안정적인 대기업, 서울 근무, 출퇴근 무관, 연봉 6000만원 희망",
        "skills": "Java, Spring Boot, MySQL, Oracle, 3년 백엔드 개발 경험"
    },
    {
        "applicant_id": "user_003",
        "preferences": "AI/머신러닝 회사, 서울 근무, 하이브리드 근무 선호, 연봉 8000만원 희망",
        "skills": "Python, FastAPI, TensorFlow, Docker, Kubernetes, 4년 개발 경험"
    }
]

def test_embedding_generation():
    """임베딩 벡터 생성 테스트"""
    print("🔢 임베딩 벡터 생성 테스트")
    print("=" * 50)

    try:
        embedding_service = get_embedding_service()

        # 채용 공고 벡터 생성
        print("📋 채용 공고 벡터 생성:")
        job_vectors = {}
        for job in SAMPLE_JOBS:
            vector = embedding_service.create_job_vector(
                company_info=job["company_info"],
                required_skills=job["required_skills"]
            )
            job_vectors[job["job_id"]] = vector
            print(f"  {job['job_id']}: 차원={vector.dimension}, 모델={vector.model}")

        # 구직자 벡터 생성
        print("\n👤 구직자 벡터 생성:")
        applicant_vectors = {}
        for applicant in SAMPLE_APPLICANTS:
            vector = embedding_service.create_applicant_vector(
                preferences=applicant["preferences"],
                skills=applicant["skills"]
            )
            applicant_vectors[applicant["applicant_id"]] = vector
            print(f"  {applicant['applicant_id']}: 차원={vector.dimension}, 모델={vector.model}")

        return job_vectors, applicant_vectors

    except Exception as e:
        print(f"❌ 임베딩 생성 실패: {e}")
        return None, None

def test_matching_scores(job_vectors, applicant_vectors):
    """매칭 스코어 계산 테스트"""
    print("\n🎯 매칭 스코어 계산 테스트")
    print("=" * 50)

    try:
        matching_service = get_matching_service()

        print("📊 전체 매칭 결과:")
        print("구직자 ID → 채용공고 ID: 점수 (코사인유사도, 유클리드거리)")
        print("-" * 60)

        all_results = []

        for applicant_id, applicant_vector in applicant_vectors.items():
            print(f"\n👤 {applicant_id}:")
            applicant_scores = []

            for job_id, job_vector in job_vectors.items():
                # 매칭 스코어 계산
                result = matching_service.match_single(
                    job_vector=job_vector.combined_vector,
                    applicant_vector=applicant_vector.combined_vector,
                    job_id=job_id,
                    applicant_id=applicant_id
                )

                score_info = {
                    "applicant_id": applicant_id,
                    "job_id": job_id,
                    "score": result.score,
                    "cosine_similarity": result.cosine_similarity,
                    "euclidean_distance": result.euclidean_distance
                }
                applicant_scores.append(score_info)
                all_results.append(score_info)

                print(f"  → {job_id}: {result.score:.4f} "
                      f"(cos:{result.cosine_similarity:.3f}, "
                      f"euc:{result.euclidean_distance:.3f})")

            # 해당 구직자의 최고 매칭 찾기
            best_match = max(applicant_scores, key=lambda x: x["score"])
            print(f"  ✅ 최고 매칭: {best_match['job_id']} (점수: {best_match['score']:.4f})")

        return all_results

    except Exception as e:
        print(f"❌ 매칭 스코어 계산 실패: {e}")
        return None

def test_batch_matching(job_vectors, applicant_vectors):
    """배치 매칭 테스트 (1:N, N:1)"""
    print("\n🔄 배치 매칭 테스트")
    print("=" * 50)

    try:
        matching_service = get_matching_service()

        # 1:N 매칭 (한 구직자 → 여러 공고)
        print("📊 1:N 매칭 (구직자 user_001 → 모든 공고):")
        user_001_vector = applicant_vectors["user_001"]

        # 간단한 1:N 매칭 (개별 계산)
        results = []
        for job_id, job_vector in job_vectors.items():
            result = matching_service.match_single(
                job_vector=job_vector.combined_vector,
                applicant_vector=user_001_vector.combined_vector,
                job_id=job_id,
                applicant_id="user_001"
            )
            results.append(result)

        # 점수 순으로 정렬
        results.sort(key=lambda x: x.score, reverse=True)

        for result in results:
            print(f"  → {result.job_id}: {result.score:.4f}")

        print(f"  ✅ 최고 매칭: {results[0].job_id} (점수: {results[0].score:.4f})")

        return True

    except Exception as e:
        print(f"❌ 배치 매칭 테스트 실패: {e}")
        return False

def analyze_matching_patterns(all_results):
    """매칭 패턴 분석"""
    print("\n📈 매칭 패턴 분석")
    print("=" * 50)

    if not all_results:
        print("❌ 분석할 결과가 없습니다.")
        return

    # 구직자별 최고 매칭
    print("👤 구직자별 최고 매칭:")
    applicant_best = {}
    for result in all_results:
        applicant_id = result["applicant_id"]
        if applicant_id not in applicant_best or result["score"] > applicant_best[applicant_id]["score"]:
            applicant_best[applicant_id] = result

    for applicant_id, best_result in applicant_best.items():
        print(f"  {applicant_id} → {best_result['job_id']} (점수: {best_result['score']:.4f})")

    # 채용공고별 최고 매칭
    print("\n📋 채용공고별 최고 매칭:")
    job_best = {}
    for result in all_results:
        job_id = result["job_id"]
        if job_id not in job_best or result["score"] > job_best[job_id]["score"]:
            job_best[job_id] = result

    for job_id, best_result in job_best.items():
        print(f"  {job_id} → {best_result['applicant_id']} (점수: {best_result['score']:.4f})")

    # 점수 분포
    scores = [result["score"] for result in all_results]
    print(f"\n📊 점수 분포:")
    print(f"  최고점: {max(scores):.4f}")
    print(f"  최저점: {min(scores):.4f}")
    print(f"  평균점: {sum(scores)/len(scores):.4f}")

def explain_sample_data():
    """샘플 데이터 설명"""
    print("📋 테스트 샘플 데이터 설명")
    print("=" * 50)

    print("🏢 채용 공고:")
    for i, job in enumerate(SAMPLE_JOBS, 1):
        print(f"  {i}. {job['job_id']}: {job['company_info'][:50]}...")
        print(f"     요구사항: {job['required_skills'][:50]}...")

    print("\n👤 구직자:")
    for i, applicant in enumerate(SAMPLE_APPLICANTS, 1):
        print(f"  {i}. {applicant['applicant_id']}: {applicant['preferences'][:50]}...")
        print(f"     보유기술: {applicant['skills'][:50]}...")

def main():
    """메인 테스트 실행"""
    print("🎯 매칭 시스템 전체 테스트")
    print("=" * 60)

    # 샘플 데이터 설명
    explain_sample_data()

    # 1. 임베딩 벡터 생성
    job_vectors, applicant_vectors = test_embedding_generation()
    if not job_vectors or not applicant_vectors:
        return

    # 2. 매칭 스코어 계산
    all_results = test_matching_scores(job_vectors, applicant_vectors)
    if not all_results:
        return

    # 3. 배치 매칭 테스트
    test_batch_matching(job_vectors, applicant_vectors)

    # 4. 매칭 패턴 분석
    analyze_matching_patterns(all_results)

    print("\n" + "=" * 60)
    print("🎉 매칭 시스템 테스트 완료!")
    print("\n💡 결과 해석:")
    print("- 높은 점수: 구직자와 공고가 잘 매칭됨")
    print("- 낮은 점수: 매칭도가 낮음 (필터링 대상)")
    print("- 코사인 유사도: 방향성 (기술/선호도 일치)")
    print("- 유클리드 거리: 크기 차이 (역량 격차)")

if __name__ == "__main__":
    main()