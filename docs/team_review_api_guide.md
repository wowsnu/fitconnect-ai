# Team Review API 가이드

기업 팀원 리뷰 방식의 인터뷰 및 채용공고 생성 API

## 개요

**기존 방식 vs Team Review 방식**

| 구분 | 기존 방식 | Team Review 방식 |
|------|----------|------------------|
| 응답자 | 1명 (대표/채용담당자) | 여러 명 (구조화 1명 + 팀원 N명) |
| 질문 수 | General 5개 + Technical 8개 + Situational 8개 | 구조화 1개 + 팀원별 2개 |
| 답변 형식 | 질문별 개별 답변 | 하나의 긴 텍스트 답변 |
| 분석 방식 | Q&A 분석 | 여러 팀원 의견 종합 분석 |
| JD 생성 | 동일 | 동일 (기존 API 재사용) |

## API 플로우

```
1. POST /company-interview/team-review/start
   → session_id 생성

2. POST /company-interview/team-review/general
   → 구조화 질문 답변 (1명)
   → CompanyGeneralAnalysis 생성

3. POST /company-interview/team-review/members
   → 팀원 리뷰 답변 (N명)
   → TechnicalRequirements + TeamCultureProfile 생성

4. POST /company-interview/situational/analysis
   → JD 생성 (기존 API 재사용)

5. POST /company-interview/generate
   → 카드 및 벡터 생성 (기존 API 재사용)
```

## API 상세

### 1. 팀원 리뷰 세션 시작

**요청:**
```http
POST /company-interview/team-review/start
Content-Type: application/json

{
  "access_token": "...",
  "company_name": "테크플로우" (선택)
}
```

**응답:**
```json
{
  "session_id": "uuid...",
  "company_name": "테크플로우",
  "message": "팀원 리뷰 세션이 시작되었습니다...",
  "next_step": "POST /team-review/general"
}
```

---

### 2. 구조화 질문 답변 제출

**질문 내용 (프론트에서 제공):**
> "회사의 핵심 가치, 팀 문화, 이상적인 인재상, 채용 이유, 업무 방식을 종합적으로 말씀해주세요."

**요청:**
```http
POST /company-interview/team-review/general
Content-Type: application/json

{
  "session_id": "uuid...",
  "general_answer": "우리 회사는 혁신과 도전을 핵심 가치로... (긴 텍스트)"
}
```

**응답:**
```json
{
  "success": true,
  "session_id": "uuid...",
  "general_analysis": {
    "core_values": ["혁신", "도전", "협업"],
    "ideal_candidate_traits": ["주도적", "학습 지향적"],
    "team_culture": "수평적 소통...",
    "work_style": "애자일 방식...",
    "hiring_reason": "신규 프로젝트..."
  },
  "message": "구조화 질문 분석이 완료되었습니다...",
  "next_step": "POST /team-review/members"
}
```

---

### 3. 팀원 리뷰 답변 제출

**질문 내용 (프론트에서 제공):**

**직무적합성 질문:**
> "이 포지션의 직무 요구사항, 필수 역량, 우대 역량, 예상되는 도전 과제를 구체적으로 말씀해주세요."

**문화적합성 질문:**
> "팀의 현재 상황, 협업 스타일, 갈등 해결 방식, 업무 환경, 선호하는 업무 스타일을 구체적으로 말씀해주세요."

**요청:**
```http
POST /company-interview/team-review/members
Content-Type: application/json

{
  "session_id": "uuid...",
  "member_reviews": [
    {
      "member_name": "김철수",
      "role": "시니어 백엔드 개발자",
      "job_fit_answer": "이 포지션은 마이크로서비스 아키텍처... (긴 텍스트)",
      "culture_fit_answer": "우리 팀은 현재 성장기에 있으며... (긴 텍스트)"
    },
    {
      "member_name": "이영희",
      "role": "팀 리더",
      "job_fit_answer": "필수 역량으로는 Python과 Django... (긴 텍스트)",
      "culture_fit_answer": "협업은 주로 페어 프로그래밍... (긴 텍스트)"
    },
    {
      "member_name": "박민수",
      "role": "주니어 개발자",
      "job_fit_answer": "신입이 오면 주로 API 개발부터... (긴 텍스트)",
      "culture_fit_answer": "팀 분위기는 자유롭고 질문하기 편해요... (긴 텍스트)"
    }
  ]
}
```

**응답:**
```json
{
  "success": true,
  "session_id": "uuid...",
  "member_count": 3,
  "technical_requirements": {
    "job_title": "백엔드 개발자",
    "main_responsibilities": [
      "마이크로서비스 아키텍처 설계 및 구현",
      "RESTful API 개발"
    ],
    "required_skills": [
      "Python 3년 이상",
      "Django/FastAPI 실무 경험"
    ],
    "preferred_skills": [
      "Kubernetes 경험",
      "MSA 구축 경험"
    ],
    "expected_challenges": "레거시 시스템을 마이크로서비스로 전환..."
  },
  "team_culture_profile": {
    "team_situation": "현재 성장기에 있으며...",
    "collaboration_style": "페어 프로그래밍과 코드 리뷰...",
    "conflict_resolution": "투명한 소통과 데이터 기반...",
    "work_environment": "자유롭고 수평적인 분위기...",
    "preferred_work_style": "자율성과 책임감..."
  },
  "message": "팀원 리뷰 분석이 완료되었습니다...",
  "next_step": "POST /situational/analysis (기존 API 재사용)"
}
```

---

### 4. JD 생성 (기존 API 재사용)

**요청:**
```http
POST /company-interview/situational/analysis
Content-Type: application/json

{
  "session_id": "uuid...",
  "access_token": "...",
  "job_posting_id": 123
}
```

**응답:** (기존과 동일)
```json
{
  "success": true,
  "job_posting_data": {
    "responsibilities": "- 마이크로서비스...\n- API 개발...",
    "requirements_must": "- Python 3년 이상\n- Django 실무...",
    "requirements_nice": "- Kubernetes 경험\n- MSA 구축...",
    "competencies": "Python, Django, FastAPI, Docker, Kubernetes"
  }
}
```

---

### 5. 카드 및 벡터 생성 (기존 API 재사용)

**요청:**
```http
POST /company-interview/generate
Content-Type: application/json

{
  "session_id": "uuid...",
  "access_token": "...",
  "job_posting_id": 123,
  "responsibilities": "- 수정된 내용...",
  "requirements_must": "- 수정된 내용...",
  "requirements_nice": "- 수정된 내용...",
  "competencies": "Python, Django, ..."
}
```

**응답:** (기존과 동일)

---

## 핵심 구현 사항

### 1. 세션 모드 구분

```python
class CompanyInterviewSession:
    def __init__(self, ..., is_team_review_mode: bool = False):
        self.is_team_review_mode = is_team_review_mode
        # 팀원 리뷰 모드에서는 면접 객체 생성 안함
        self.general_interview = None if is_team_review_mode else CompanyGeneralInterview()
```

### 2. 팀원 리뷰 분석 함수

**직무적합성 분석:**
```python
def analyze_team_review_technical(
    member_reviews: List[Dict[str, str]],
    general_analysis: CompanyGeneralAnalysis
) -> TechnicalRequirements:
    """
    여러 팀원의 직무적합성 답변을 종합 분석

    종합 원칙:
    - 대다수(50% 이상) 팀원이 언급 → 필수 역량
    - 일부 팀원만 언급 → 우대 역량
    - 의견 차이 → 포괄적으로 표현
    - 맥락 유지하면서 종합
    """
```

**문화적합성 분석:**
```python
def analyze_team_review_culture(
    member_reviews: List[Dict[str, str]],
    general_analysis: CompanyGeneralAnalysis,
    technical_requirements: TechnicalRequirements
) -> TeamCultureProfile:
    """
    여러 팀원의 문화적합성 답변을 종합 분석

    종합 원칙:
    - 공통적으로 강조한 문화적 특성 우선 반영
    - 팀원들 간 의견 차이는 포괄적으로 표현
    - 실제 업무 방식과 문화를 솔직하게 반영
    """
```

### 3. 기존 API 재사용

```python
@company_interview_router.post("/situational/analysis")
async def create_situational_analysis_with_jd(request):
    session = company_sessions[request.session_id]

    # 모드별 분기
    if session.is_team_review_mode:
        # 팀원 리뷰: 이미 분석 결과 있음 → 확인만
        if not session.general_analysis:
            raise HTTPException(...)
    else:
        # 기존 면접: 면접 완료 확인 → 분석 수행
        if not session.general_interview.is_finished():
            raise HTTPException(...)

    # 이후 JD 생성 로직은 동일
    job_posting_data = create_job_posting_from_interview(
        general_analysis=session.general_analysis,
        technical_requirements=session.technical_requirements,
        team_fit_analysis=session.situational_profile,
        ...
    )
```

---

## 장점

1. **기존 코드 최대한 재사용**
   - JD 생성: `create_job_posting_from_interview()` 그대로 사용
   - 카드 생성: `create_job_posting_card_from_interview()` 그대로 사용
   - 벡터 생성: `generate_company_matching_vectors()` 그대로 사용

2. **맥락 손실 최소화**
   - Single-Pass 분석 (Two-Phase 구조화 안함)
   - 여러 팀원의 답변을 한번에 LLM에 입력
   - 팀원들 간의 관계성 유지

3. **유연한 확장**
   - 팀원 수 제한 없음
   - 질문 추가/수정 용이
   - 기존 시스템과 완전 분리

---

## 테스트 시나리오

```bash
# 1. 세션 시작
curl -X POST http://localhost:8000/company-interview/team-review/start \
  -H "Content-Type: application/json" \
  -d '{"access_token": "..."}'

# 2. 구조화 질문 답변
curl -X POST http://localhost:8000/company-interview/team-review/general \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "...",
    "general_answer": "우리 회사는..."
  }'

# 3. 팀원 리뷰 답변
curl -X POST http://localhost:8000/company-interview/team-review/members \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "...",
    "member_reviews": [...]
  }'

# 4. JD 생성
curl -X POST http://localhost:8000/company-interview/situational/analysis \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "...",
    "access_token": "...",
    "job_posting_id": 123
  }'

# 5. 세션 정보 확인
curl http://localhost:8000/company-interview/session/{session_id}
```

---

## 주의사항

1. **팀원 리뷰는 최소 1명 이상** 필요
2. **구조화 질문을 먼저** 제출해야 팀원 리뷰 가능
3. **기존 job_posting_id 필수** (JD 생성 시)
4. 세션은 in-memory 저장 (서버 재시작 시 삭제됨)

---

## 파일 구조

```
ai/interview/company/
├── general.py                    # 기존 General 분석
├── technical.py                  # 기존 Technical 분석
├── situational.py                # 기존 Situational 분석
├── jd_generator.py               # JD/카드 생성 (재사용)
└── team_review_analyzer.py       # ✨ 새로 추가: 팀원 리뷰 분석

api/
└── company_interview_routes.py   # 기존 API + 팀원 리뷰 API 추가
```
