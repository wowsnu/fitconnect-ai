# FitConnect 통합 프로필 생성 플로우

## 개요
기본 프로필 데이터(DB) + 면접 분석 → 완성된 구직자 프로필

## 전체 플로우 (개선됨)

### 1. DB 프로필 데이터 조회 (구조화된 데이터, 분석 불필요)
```python
def get_structured_db_profile(user_id: int):
    # DB에서 이미 구조화된 데이터 직접 조회
    return {
        "profile": get_talent_profile(user_id),
        "educations": get_educations(user_id),
        "experiences": get_experiences(user_id),
        "activities": get_activities(user_id),
        "certifications": get_certifications(user_id)
    }
    # LLM 분석 없음 - 이미 구조화된 데이터
```

### 2. 면접 분석
```python
def analyze_interview(audio_file):
    # STT: 음성 → 텍스트
    stt_service = get_stt_service()
    transcript, _ = stt_service.transcribe_bytes(audio_file)

    # LLM: 면접 분석
    llm_service = get_llm_service()
    interview_analysis = await llm_service.analyze_candidate_profile(transcript)

    return transcript, interview_analysis
```

### 3. 통합 분석 API (개선됨 - LLM 호출 1회만)
```python
@app.post("/api/talent/{user_id}/complete-analysis")
async def create_complete_profile(user_id: int, audio_file: UploadFile):
    # 1. DB 구조화된 데이터 직접 조회 (LLM 분석 없음)
    db_profile = get_structured_db_profile(user_id)

    # 2. 면접만 STT + LLM 분석
    transcript, interview_analysis = await analyze_interview(audio_file)

    # 3. DB + 면접 통합 분석 (LLM 1회만 호출)
    llm_service = get_llm_service()

    integration_prompt = f"""
    구조화된 DB 프로필 데이터와 면접 분석을 통합해서 완전한 구직자 프로필을 생성해주세요:

    [DB 구조화 데이터 (이미 정확함)]
    학력: {db_profile['educations']}
    경력: {db_profile['experiences']}
    활동: {db_profile['activities']}
    자격: {db_profile['certifications']}

    [면접 분석 결과]
    {json.dumps(interview_analysis, ensure_ascii=False)}

    다음 JSON 형식으로 통합 결과를 생성해주세요:
    {{
        "technical_skills": ["DB 경력 + 면접에서 언급된 기술"],
        "soft_skills": ["면접에서 드러난 소프트 스킬"],
        "experience_level": "DB 경력 기준으로 정확히 계산",
        "strengths": ["DB + 면접 종합 강점"],
        "personality": "면접에서 파악된 성격/업무 스타일",
        "career_goals": "면접에서 언급된 목표",
        "work_preferences": "선호하는 업무 환경/조건"
    }}
    """

    messages = [{"role": "user", "content": integration_prompt}]
    integrated_result = await llm_service.generate_completion(messages)

    # 4. 임베딩 벡터 생성
    embedding_service = get_embedding_service()
    complete_vector = embedding_service.create_applicant_vector(
        preferences=integrated_result.get('work_preferences', ''),
        skills=', '.join(
            integrated_result.get('technical_skills', []) +
            integrated_result.get('soft_skills', [])
        )
    )

    # 5. DB에 완전한 프로필 저장
    complete_profile = {
        "user_id": user_id,
        "db_profile": db_profile,  # 구조화된 원본 데이터
        "interview_transcript": transcript,
        "interview_analysis": interview_analysis,
        "integrated_analysis": integrated_result,
        "embedding_vector": complete_vector.combined_vector,
        "completion_date": datetime.now()
    }

    save_complete_profile(complete_profile)

    return {
        "success": True,
        "complete_profile": complete_profile,
        "next_step": "matching_ready"
    }
```
새로운 플로우:
  DB 구조화 데이터 (분석 없음) ─┐
                             ├→ LLM 통합 → 임베딩 벡터
  면접 → STT → LLM 분석 ─────┘
## 필요한 DB 테이블

```sql
-- 완성된 구직자 프로필
CREATE TABLE talent_complete_profiles (
  user_id             BIGINT UNSIGNED PRIMARY KEY,
  db_analysis         JSON,           -- 기본 프로필 분석
  interview_transcript TEXT,          -- 면접 텍스트
  interview_analysis  JSON,           -- 면접 분석
  integrated_analysis JSON,           -- 통합 분석 (최종)
  embedding_vector    JSON,           -- 매칭용 벡터
  completion_date     DATETIME,
  updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  CONSTRAINT fk_complete_profile_user FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE RESTRICT
);
```

## 단계별 구현 순서

1. ✅ **기본 AI 서비스 테스트** (embedding, matching, llm)
2. 🔄 **STT 기능 테스트** (음성 → 텍스트)
3. ⏳ **LLM 프로필 분석 테스트** (텍스트 → 구조화된 분석)
4. ⏳ **DB 더미 데이터로 기본 프로필 분석 테스트**
5. ⏳ **면접 분석 테스트** (STT + LLM)
6. ⏳ **통합 분석 테스트** (두 결과 합성)
7. ⏳ **전체 플로우 통합 테스트**

## 테스트 데이터 예시

### 기본 프로필 데이터
```json
{
  "educations": [
    {
      "school_name": "서울대학교",
      "major": "컴퓨터공학",
      "status": "졸업",
      "start_ym": "2018-03",
      "end_ym": "2022-02"
    }
  ],
  "experiences": [
    {
      "company_name": "네이버",
      "title": "백엔드 개발자",
      "start_ym": "2022-03",
      "end_ym": "2024-12",
      "summary": "대용량 API 서버 개발 및 운영"
    }
  ]
}
```

### 면접 예시 텍스트
```
"안녕하세요. 저는 3년간 백엔드 개발을 해온 개발자입니다.
네이버에서 대용량 트래픽을 처리하는 API 서버를 개발하고 운영해왔습니다.
Python과 Java를 주로 사용하며, 최근에는 클라우드 아키텍처에 관심이 많습니다.
팀워크를 중시하고, 문제 해결에 집착하는 성격입니다."
```

### 기대 통합 결과
```json
{
  "technical_skills": ["Python", "Java", "API 개발", "대용량 처리", "클라우드"],
  "soft_skills": ["팀워크", "문제해결능력", "집중력"],
  "experience_level": "중급 (3년)",
  "personality": "문제 해결 집착형, 팀워크 중시",
  "career_goals": "클라우드 아키텍처 전문가",
  "work_preferences": "대용량 시스템, 기술적 도전"
}
```