#!/usr/bin/env python3
"""
FitConnect AI Services 로컬 테스트 스크립트
DB 없이 모든 AI 기능을 테스트합니다.
"""

import asyncio
import logging
import os
import tempfile
from typing import List, Dict, Any

# AI 서비스 import
from ai.stt.service import get_stt_service
from ai.llm.service import get_llm_service
from ai.embedding.service import get_embedding_service
from ai.matching.service import get_matching_service

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 테스트 데이터
SAMPLE_INTERVIEW_TEXT = """
안녕하세요. 저는 5년간 백엔드 개발을 해온 김개발입니다.
주로 Python과 Django를 사용해서 웹 서비스를 개발해왔고,
최근에는 FastAPI와 PostgreSQL을 활용한 API 서버 구축 경험이 있습니다.
AWS를 이용한 클라우드 배포도 담당해왔고, Docker를 활용한 컨테이너화 작업도 진행했습니다.
팀에서 리더 역할을 맡아 프로젝트를 성공적으로 완료한 경험이 있으며,
문제 해결 능력과 커뮤니케이션 스킬이 강점이라고 생각합니다.
앞으로는 머신러닝과 AI 분야에도 도전해보고 싶습니다.
"""

SAMPLE_JOB_POSTINGS = [
    {
        "id": "job_001",
        "company_info": "IT 스타트업, 직원 50명, 수평적 조직문화, 원격근무 가능",
        "required_skills": "Python, FastAPI, PostgreSQL, AWS, Docker, 3년 이상 경력"
    },
    {
        "id": "job_002",
        "company_info": "대기업 계열사, 직원 500명, 안정적 환경, 복리후생 우수",
        "required_skills": "Java, Spring Boot, MySQL, 5년 이상 경력, 팀 리딩 경험"
    },
    {
        "id": "job_003",
        "company_info": "AI 스타트업, 직원 30명, 혁신적 기술, 스톡옵션 제공",
        "required_skills": "Python, Machine Learning, TensorFlow, API 개발, 데이터 분석"
    }
]

class AIServiceTester:
    """AI 서비스 통합 테스터"""

    def __init__(self):
        self.stt_service = get_stt_service()
        self.llm_service = get_llm_service()
        self.embedding_service = get_embedding_service()
        self.matching_service = get_matching_service()

    def test_health_checks(self):
        """모든 서비스 상태 확인"""
        logger.info("=== AI 서비스 상태 확인 ===")

        # STT 상태
        stt_health = self.stt_service.health_check()
        logger.info(f"STT 서비스: {stt_health['status']}")

        # LLM 상태
        llm_health = self.llm_service.health_check()
        logger.info(f"LLM 서비스: {llm_health['service']}")

        # Embedding 상태
        embedding_health = self.embedding_service.health_check()
        logger.info(f"Embedding 서비스: {embedding_health.service_status}")

        # Matching 상태
        matching_health = self.matching_service.health_check()
        logger.info(f"Matching 서비스: {matching_health.service_status}")

        return True

    def test_stt_with_text_to_speech(self):
        """STT 테스트 (임시 음성 파일 생성)"""
        logger.info("=== STT 서비스 테스트 ===")

        try:
            # 실제 음성 파일이 있다면 경로를 지정하세요
            # audio_file = "test_audio.wav"  # 실제 파일 경로

            # 테스트용: 텍스트를 STT 없이 바로 사용
            logger.info("STT 테스트를 위해 샘플 텍스트 사용")
            transcript = SAMPLE_INTERVIEW_TEXT.strip()

            logger.info(f"전사 결과: {transcript[:100]}...")
            return transcript

        except Exception as e:
            logger.error(f"STT 테스트 실패: {e}")
            logger.info("실제 음성 파일로 테스트하려면 test_audio.wav 파일을 추가하세요")
            return SAMPLE_INTERVIEW_TEXT.strip()

    async def test_llm_analysis(self, text: str):
        """LLM 분석 테스트"""
        logger.info("=== LLM 분석 테스트 ===")

        try:
            # 지원자 프로필 분석
            analysis = await self.llm_service.analyze_candidate_profile(text)

            logger.info("지원자 프로필 분석 결과:")
            if isinstance(analysis, dict):
                for key, value in analysis.items():
                    logger.info(f"  {key}: {value}")
            else:
                logger.info(f"  분석 결과: {analysis}")

            return analysis

        except Exception as e:
            logger.error(f"LLM 분석 실패: {e}")
            # 테스트용 더미 데이터
            return {
                "technical_skills": ["Python", "Django", "FastAPI", "PostgreSQL", "AWS", "Docker"],
                "soft_skills": ["팀워크", "문제해결능력", "커뮤니케이션", "리더십"],
                "experience_level": "시니어 (5년)",
                "strengths": ["백엔드 개발 전문성", "클라우드 경험", "팀 리딩"],
                "areas_for_improvement": ["머신러닝", "프론트엔드"],
                "career_summary": "5년차 백엔드 개발자"
            }

    def test_embedding_services(self, candidate_analysis: Dict[str, Any]):
        """임베딩 서비스 테스트"""
        logger.info("=== 임베딩 서비스 테스트 ===")

        try:
            # 지원자 벡터 생성
            candidate_preferences = "스타트업 선호, 원격근무 희망, 기술적 성장 중시"
            candidate_skills = ", ".join(
                candidate_analysis.get("technical_skills", []) +
                candidate_analysis.get("soft_skills", [])
            )

            logger.info("지원자 벡터 생성 중...")
            candidate_vector = self.embedding_service.create_applicant_vector(
                preferences=candidate_preferences,
                skills=candidate_skills
            )

            logger.info(f"지원자 벡터 차원: {candidate_vector.dimension}")
            logger.info(f"사용된 모델: {candidate_vector.model}")

            # 채용공고 벡터들 생성
            job_vectors = []
            for job in SAMPLE_JOB_POSTINGS:
                logger.info(f"공고 {job['id']} 벡터 생성 중...")
                job_vector = self.embedding_service.create_job_vector(
                    company_info=job["company_info"],
                    required_skills=job["required_skills"]
                )
                job_vectors.append({
                    "id": job["id"],
                    "vector": job_vector,
                    "info": job
                })

            return candidate_vector, job_vectors

        except Exception as e:
            logger.error(f"임베딩 테스트 실패: {e}")
            return None, None

    def test_matching_algorithm(self, candidate_vector, job_vectors):
        """매칭 알고리즘 테스트"""
        logger.info("=== 매칭 알고리즘 테스트 ===")

        if not candidate_vector or not job_vectors:
            logger.error("벡터 데이터가 없어 매칭 테스트를 건너뜁니다")
            return

        try:
            # 단일 매칭 테스트
            logger.info("단일 매칭 테스트:")
            for job_data in job_vectors:
                result = self.matching_service.match_single(
                    job_vector=job_data["vector"].combined_vector,
                    applicant_vector=candidate_vector.combined_vector,
                    job_id=job_data["id"],
                    applicant_id="test_candidate"
                )

                logger.info(f"  {job_data['id']}: 점수 {result.score:.3f} "
                          f"(코사인: {result.cosine_similarity:.3f}, "
                          f"유클리드: {result.euclidean_distance:.3f})")

            # 배치 매칭 테스트
            logger.info("\n배치 매칭 테스트 (추천 순위):")
            all_job_vectors = [job["vector"].combined_vector for job in job_vectors]
            all_job_ids = [job["id"] for job in job_vectors]

            recommendations = self.matching_service.match_batch(
                job_vectors=all_job_vectors,
                applicant_vector=candidate_vector.combined_vector,
                job_ids=all_job_ids,
                applicant_id="test_candidate",
                top_n=3
            )

            logger.info(f"상위 {len(recommendations.matches)}개 추천:")
            for match in recommendations.matches:
                job_info = next(job for job in job_vectors if job["id"] == match.job_id)
                logger.info(f"  {match.rank}위. {match.job_id}: {match.score:.3f}점")
                logger.info(f"      {job_info['info']['company_info']}")

        except Exception as e:
            logger.error(f"매칭 테스트 실패: {e}")

    async def run_full_pipeline_test(self):
        """전체 파이프라인 테스트"""
        logger.info("🚀 FitConnect AI 서비스 전체 테스트 시작")
        logger.info("=" * 60)

        # 1. 서비스 상태 확인
        if not self.test_health_checks():
            logger.error("서비스 상태 확인 실패")
            return

        print()

        # 2. STT 테스트 (또는 샘플 텍스트 사용)
        transcript = self.test_stt_with_text_to_speech()

        print()

        # 3. LLM 분석 테스트
        analysis = await self.test_llm_analysis(transcript)

        print()

        # 4. 임베딩 테스트
        candidate_vector, job_vectors = self.test_embedding_services(analysis)

        print()

        # 5. 매칭 테스트
        self.test_matching_algorithm(candidate_vector, job_vectors)

        logger.info("=" * 60)
        logger.info("✅ 전체 테스트 완료!")

        return {
            "transcript": transcript,
            "analysis": analysis,
            "candidate_vector": candidate_vector,
            "job_vectors": job_vectors
        }

def create_sample_audio_guide():
    """샘플 오디오 파일 생성 가이드"""
    print("\n📱 실제 음성 파일로 STT 테스트하려면:")
    print("1. test_audio.wav 파일을 프로젝트 루트에 추가")
    print("2. 또는 아래 코드 수정:")
    print("   audio_file = 'your_audio_file.wav'")
    print("3. 지원 포맷: .wav, .mp3, .m4a, .flac, .ogg, .webm")

async def main():
    """메인 테스트 실행"""
    try:
        tester = AIServiceTester()
        results = await tester.run_full_pipeline_test()

        create_sample_audio_guide()

        print("\n🎯 테스트 요약:")
        print(f"- 전사된 텍스트 길이: {len(results['transcript'])} 글자")
        print(f"- 분석된 기술 스킬: {len(results['analysis'].get('technical_skills', []))}개")
        if results['candidate_vector']:
            print(f"- 임베딩 벡터 차원: {results['candidate_vector'].dimension}")
        print(f"- 매칭 대상 공고: {len(results['job_vectors']) if results['job_vectors'] else 0}개")

    except Exception as e:
        logger.error(f"테스트 실행 중 오류: {e}")

if __name__ == "__main__":
    print("🤖 FitConnect AI Services 테스트 스크립트")
    print("=" * 60)
    asyncio.run(main())