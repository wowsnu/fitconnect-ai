"""
LLM 프롬프트 템플릿 관리
모든 프롬프트를 중앙에서 관리하여 일관성과 재사용성 확보
"""

from typing import Dict, Any

# 면접 분석 프롬프트 (user 메시지용)
INTERVIEW_ANALYSIS_PROMPT = """
면접 내용을 다음 JSON 형식으로 분석해주세요:

{
    "technical_skills": ["언급된 정확한 기술 스킬명 (예: Python, Django, React)"],
    "tools_and_platforms": ["언급된 정확한 도구/플랫폼명 (예: Git, AWS, Docker)"],
    "companies_mentioned": ["언급된 회사명 그대로"],
    "soft_skills": ["면접에서 드러난 소프트 스킬들 (추론 가능)"],
    "core_competencies": ["핵심 역량들 (추론 가능)"],
    "strengths": ["주요 강점들"],
    "key_experiences": ["핵심 경험들"],
    "personality": "성격 및 업무 스타일 (추론 가능)",
    "career_goals": "커리어 목표",
    "work_preferences": "선호하는 업무 환경",
    "communication_style": "커뮤니케이션 스타일",
    "motivation": "동기부여 요소",
    "experience_insights": "경험에서 드러난 역량"
}

**중요 규칙**:
- technical_skills, tools_and_platforms, companies_mentioned는 언급된 **정확한 명칭 그대로** 보존
- 예: "파이썬" → "Python", "장고" → "Django"
- soft_skills, personality 등은 추론/해석 가능
- 언급되지 않은 내용은 추측하지 말고 빈 배열/빈 문자열로
"""

# DB + 면접 통합 분석 프롬프트
def create_integration_prompt(db_profile: Dict[str, Any], interview_analysis: Dict[str, Any]) -> str:
    """DB 프로필과 면접 분석을 통합하는 프롬프트 생성"""
    return f"""
구조화된 DB 프로필 데이터와 면접 분석 결과를 통합해서 완전한 구직자 프로필을 생성해주세요:

[DB 구조화 데이터 (정확한 팩트)]
이름: {db_profile.get('profile', {}).get('name', '알 수 없음')}
학력: {db_profile.get('educations', [])}
경력: {db_profile.get('experiences', [])}
활동: {db_profile.get('activities', [])}
자격: {db_profile.get('certifications', [])}

[면접 분석 결과]
{interview_analysis}

다음 JSON 형식으로 통합된 최종 프로필을 생성해주세요:
{{
    "technical_skills": ["DB 경력 + 면접에서 언급된 모든 기술 스킬명 (정확한 명칭, 중복 제거)"],
    "tools_and_platforms": ["DB + 면접에서 언급된 모든 도구/플랫폼명 (정확한 명칭)"],
    "companies": ["경력 회사명 정확히"],
    "soft_skills": ["면접에서 드러난 소프트 스킬들 (추론 가능)"],
    "experience_level": "DB 경력 데이터를 기준으로 정확히 계산 (예: 신입, 주니어 2년, 시니어 5년)",
    "strengths": ["DB + 면접 내용을 종합한 주요 강점 3-5개"],
    "personality": "면접에서 파악된 성격 및 업무 스타일 (추론 가능)",
    "career_goals": "면접에서 언급된 커리어 목표",
    "work_preferences": "선호하는 업무 환경 및 조건",
    "education_background": "학력 요약 (학교, 전공, 졸업년도)",
    "career_summary": "경력 요약 (주요 회사, 직책, 기간)",
    "key_achievements": ["주목할 만한 성과나 프로젝트"],
    "growth_potential": "성장 가능성 및 학습 의지 평가 (추론 가능)"
}}

**중요 규칙**:
- technical_skills, tools_and_platforms, companies는 DB와 면접에서 **언급된 정확한 명칭 그대로** 보존
- 예: "Python", "Django", "AWS", "네이버" 같이 정확히
- soft_skills, personality, growth_potential 등은 추론/해석 가능
- DB 와 면접에서 언급한 내용을 골고루 반영 
"""

# 매칭용 프로필 요약 프롬프트
MATCHING_SUMMARY_PROMPT = """
다음 통합 프로필을 매칭 알고리즘용으로 간단히 요약해주세요:

{profile}

다음 형식으로 요약해주세요:
- 선호 업무환경: (한 줄로 요약)
- 핵심 역량: (기술 + 소프트 스킬 조합, 쉼표로 구분)
"""

# 일반적인 시스템 프롬프트들
SYSTEM_PROMPTS = {
    "professional": "당신은 채용 및 인사 전문가입니다. 객관적이고 전문적으로 분석해주세요.",
    "analyst": "당신은 데이터 분석 전문가입니다. 제공된 정보를 체계적으로 분석해주세요.",
    "interviewer": "당신은 경험이 풍부한 면접관입니다. 면접 내용을 면밀히 분석해주세요."
}

# 프롬프트 빌더 함수들
def build_interview_analysis_messages(interview_text: str) -> list:
    """면접 분석용 메시지 구성"""
    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPTS["interviewer"]
        },
        {
            "role": "user",
            "content": f"{INTERVIEW_ANALYSIS_PROMPT}\n\n면접 내용:\n{interview_text}"
        }
    ]

def build_integration_messages(db_profile: Dict[str, Any], interview_analysis: Dict[str, Any]) -> list:
    """통합 분석용 메시지 구성"""
    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPTS["professional"]
        },
        {
            "role": "user",
            "content": create_integration_prompt(db_profile, interview_analysis)
        }
    ]

def build_matching_summary_messages(profile: Dict[str, Any]) -> list:
    """매칭 요약용 메시지 구성"""
    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPTS["analyst"]
        },
        {
            "role": "user",
            "content": MATCHING_SUMMARY_PROMPT.format(profile=profile)
        }
    ]

# 프롬프트 버전 관리
PROMPT_VERSION = "1.0.0"
PROMPT_METADATA = {
    "version": PROMPT_VERSION,
    "last_updated": "2024-01-01",
    "description": "FitConnect 면접 분석 및 프로필 통합 프롬프트"
}