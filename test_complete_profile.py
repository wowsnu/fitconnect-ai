#!/usr/bin/env python3
"""
전체 플로우 테스트: 면접 → 통합 → 임베딩 (원스톱)
"""

import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

from ai.llm import create_complete_candidate_profile

# 샘플 DB 프로필
SAMPLE_DB_PROFILE = {
    "user_id": 1,
    "profile": {"name": "김개발", "birth_date": "1990-01-01"},
    "educations": [
        {
            "school_name": "서울대학교",
            "major": "컴퓨터공학",
            "status": "졸업",
            "start_ym": "2010-03",
            "end_ym": "2014-02"
        }
    ],
    "experiences": [
        {
            "company_name": "네이버",
            "title": "백엔드 개발자",
            "start_ym": "2014-03",
            "end_ym": "2019-12",
            "summary": "대용량 API 서버 개발 및 운영"
        }
    ],
    "activities": [],
    "certifications": []
}

# 샘플 면접 텍스트
SAMPLE_INTERVIEW_TEXT = """
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


def test_complete_profile():
    """전체 플로우 테스트"""
    print("\n" + "="*80)
    print("🚀 전체 플로우 테스트: 면접 → 통합 → 임베딩")
    print("="*80)

    # 텍스트를 바이트로 변환 (실제로는 음성 파일)
    # 참고: STT는 건너뛰고 텍스트만 테스트
    print("\n⚠️  참고: STT는 실제 음성 파일이 필요하므로 텍스트로 대체합니다")
    print("실제 사용 시에는 audio_data에 음성 파일의 bytes를 전달하세요\n")

    # 간단한 테스트를 위해 텍스트를 임시 파일로 저장
    temp_audio_file = "/tmp/temp_interview.txt"
    with open(temp_audio_file, "w", encoding="utf-8") as f:
        f.write(SAMPLE_INTERVIEW_TEXT)

    with open(temp_audio_file, "rb") as f:
        audio_data = f.read()

    # 전체 플로우 실행
    try:
        result = create_complete_candidate_profile(
            audio_data=audio_data,
            db_profile=SAMPLE_DB_PROFILE,
            filename="interview.txt",  # txt로 테스트
            language="ko"
        )

        if "error" in result:
            print(f"❌ 에러 발생: {result['error']}")
            return

        # 결과 출력
        print("\n✅ 전체 플로우 완료!")
        print("\n" + "-"*80)
        print("1. 📝 면접 텍스트 (Transcript):")
        print("-"*80)
        print(result.get("transcript", "N/A")[:200] + "...")

        print("\n" + "-"*80)
        print("2. 🎤 면접 분석 (Interview Analysis):")
        print("-"*80)
        analysis = result.get("interview_analysis", {})
        print(f"- 기술 스킬: {', '.join(analysis.get('technical_skills', []))}")
        print(f"- 도구/플랫폼: {', '.join(analysis.get('tools_and_platforms', []))}")
        print(f"- 회사: {', '.join(analysis.get('companies_mentioned', []))}")
        print(f"- 소프트 스킬: {', '.join(analysis.get('soft_skills', []))}")

        print("\n" + "-"*80)
        print("3. 🔗 통합 프로필 (Integrated Profile):")
        print("-"*80)
        profile = result.get("integrated_profile", {})
        print(f"- 통합 기술 스킬: {', '.join(profile.get('technical_skills', []))}")
        print(f"- 경력: {profile.get('experience_level', 'N/A')}")
        print(f"- 회사: {', '.join(profile.get('companies', []))}")
        print(f"- 선호 업무환경: {profile.get('work_preferences', 'N/A')}")

        print("\n" + "-"*80)
        print("4. 🔢 임베딩 벡터 (Embedding Vector):")
        print("-"*80)
        vector = result.get("embedding_vector", [])
        metadata = result.get("vector_metadata", {})
        print(f"- 벡터 차원: {metadata.get('dimension', 'N/A')}")
        print(f"- 모델: {metadata.get('model', 'N/A')}")
        print(f"- 벡터 샘플: [{', '.join(map(str, vector[:5]))}...]")

        print("\n" + "="*80)
        print("✨ 테스트 완료! DB 저장 준비 완료")
        print("="*80)

        # 실제 사용 예시
        print("\n" + "="*80)
        print("💡 실제 사용 예시:")
        print("="*80)
        print("""
from ai.llm import create_complete_candidate_profile

# 1. 음성 파일 읽기
with open("interview.wav", "rb") as f:
    audio_data = f.read()

# 2. DB 프로필 조회
db_profile = get_db_profile(user_id)

# 3. 전체 플로우 실행
result = create_complete_candidate_profile(
    audio_data=audio_data,
    db_profile=db_profile
)

# 4. DB 저장
save_to_db({
    "user_id": user_id,
    "transcript": result["transcript"],
    "analysis": result["integrated_profile"],
    "embedding_vector": result["embedding_vector"]
})
        """)

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_complete_profile()
