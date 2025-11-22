# FitConnect 채용 매칭 인터뷰 시스템 전체 흐름 요약

## 1. 인재(Talent) 면접 플로우

### ① General Interview (구조화 면접) - 5문항
- **고정 질문**:
  - 최근 6개월 동안 가장 몰입했던 일
  - 가장 성과를 냈다고 생각하는 프로젝트
  - 팀원들과 협업할 때 본인만의 강점
  - 일을 할 때 가장 중요하게 생각하는 가치
  - 앞으로 발전시키고 싶은 역량과 커리어 계획

- **분석 결과** (`GeneralInterviewAnalysis`):
  - `key_themes`: 답변에서 자주 언급된 주요 테마/키워드
  - `interests`: 지원자가 관심있어하는 기술 분야
  - `work_style_hints`: 답변에서 드러난 업무 스타일
  - `emphasized_experiences`: 지원자가 자주 언급하거나 강조한 경험
  - `technical_keywords`: 답변에서 언급된 기술 키워드

- **API 엔드포인트**:
  - `POST /api/interview/general/start` → 첫 질문 반환
  - `POST /api/interview/general/answer/audio` → 음성 답변 제출 (STT 처리)
  - `POST /api/interview/general/answer/text` → 텍스트 답변 제출
  - `GET /api/interview/general/analysis/{session_id}` → 분석 결과 조회

---

### ② Technical Interview (직무 적합성 면접) - 9문항
- **프로필 기반 개인화**:
  - 백엔드 API에서 사용자 프로필 가져오기 (`GET /api/talents/profile`)
  - General 분석 결과 + 프로필 정보 → 기술 스택 기반 질문 생성
  - 3개 기술 선정 → 각 기술당 3문항

- **피드백 제공** (점수 없음):
  - `key_points`: 답변에서 발견된 주요 포인트
  - `mentioned_technologies`: 답변에서 언급된 기술/도구
  - `depth_areas`: 더 깊이 파고들 수 있는 영역
  - `follow_up_direction`: 다음 질문에서 집중할 방향

- **API 엔드포인트**:
  - `POST /api/interview/technical/start` → access_token으로 프로필 가져와서 첫 질문 생성
  - `POST /api/interview/technical/answer` → 답변 제출 (텍스트)
  - `POST /api/interview/technical/answer/audio` → 답변 제출 (음성)
  - `GET /api/interview/technical/results/{session_id}` → 결과 조회

---

### ③ Situational Interview (상황 면접) - 6문항
- **5가지 차원 평가**:
  1. `work_style`: 주도형 / 협력형 / 독립형
  2. `problem_solving`: 분석형 / 직관형 / 실행형
  3. `learning`: 체계형 / 실험형 / 관찰형
  4. `stress_response`: 도전형 / 안정형 / 휴식형
  5. `communication`: 논리형 / 공감형 / 간결형

- **최종 페르소나 리포트** (`FinalPersonaReport`):
  - 각 차원별 성향 + 판단 근거
  - `confidence`: 신뢰도 (0-1)
  - `summary`: 요약 (예: "협력적이며 논리적인 분석가형")
  - `team_fit`: 적합한 팀 환경

- **API 엔드포인트**:
  - `POST /api/interview/situational/start` → 첫 질문 반환
  - `POST /api/interview/situational/answer` → 답변 제출 (텍스트)
  - `POST /api/interview/situational/answer/audio` → 답변 제출 (음성)
  - `GET /api/interview/situational/report/{session_id}` → 페르소나 리포트 조회

---

### ④ Profile Card 생성
- **3가지 면접 통합 카드 생성** (`CandidateProfileCard`):
  1. **General Interview** → `key_experiences` (4개) + `core_competencies` (4개)
  2. **Technical Interview** → `strengths` (4개) + `technical_skills` (4개)
  3. **Situational Interview** → `job_fit`, `team_fit`, `growth_potential` + 보완

- **최종 카드 구성**:
  - `candidate_name`, `role`, `experience_years`, `company`
  - `key_experiences`: 주요 경험/경력 (4개)
  - `strengths`: 강점 (4개)
  - `core_competencies`: 핵심 일반 역량 (4개, name + level)
  - `technical_skills`: 핵심 직무 역량/기술 (4개, name + level)
  - `job_fit`: 직무 적합성 요약
  - `team_fit`: 협업 성향 요약
  - `growth_potential`: 성장 가능성 요약

- **백엔드 API POST**: `POST /api/talent_cards/`

- **API 엔드포인트**:
  - `POST /api/interview/profile-card/generate-and-post` → 카드 생성 및 백엔드 전송

---

### ⑤ Matching Vectors 생성
- **6가지 벡터 생성** (각 1536차원, OpenAI text-embedding-ada-002):
  1. `vector_roles` + `text_roles`: 역할 적합도/역할 수행력
  2. `vector_skills` + `text_skills`: 역량 적합도
  3. `vector_growth` + `text_growth`: 성장 가능성
  4. `vector_career` + `text_career`: 커리어 방향
  5. `vector_vision` + `text_vision`: 비전/협업 기여도
  6. `vector_culture` + `text_culture`: 조직/문화 적합도

- **생성 프로세스**:
  1. LLM으로 6가지 텍스트 생성 (프로필 + 면접 결과 종합)
  2. OpenAI Embeddings API로 벡터화
  3. 백엔드 POST → `POST /api/matching-vectors/`

- **API 엔드포인트**:
  - `POST /api/interview/matching-vectors/generate` → 벡터 생성 및 백엔드 전송

---

## 2. 기업(Company) 면접 플로우

### ① General Interview - 5문항
- **고정 질문**:
  - 이 포지션에서 수행할 주요 업무
  - 가장 중요하게 생각하는 인재상
  - 채용을 통해 해결하고자 하는 구체적인 문제/프로젝트
  - 기존 팀에서 부족한 역량이나 기술 스택
  - 팀/회사의 핵심 가치와 문화

- **분석 결과** (`CompanyGeneralAnalysis`):
  - `core_values`: 회사/팀의 핵심 가치 (최대 5개)
  - `ideal_candidate_traits`: 이상적인 인재 특징 (3-5가지)
  - `team_culture`: 팀 문화 설명 (2-3문장)
  - `work_style`: 팀의 업무 방식 (2-3문장)
  - `hiring_reason`: 채용 이유/목적 (2-3문장)

- **API 엔드포인트**:
  - `POST /api/company-interview/general/start` → access_token으로 회사명 로드, 첫 질문
  - `POST /api/company-interview/general/answer` → 답변 제출 (텍스트)
  - `POST /api/company-interview/general/answer/audio` → 답변 제출 (음성)
  - `GET /api/company-interview/general/analysis/{session_id}` → 분석 결과 조회

---

### ② Technical Interview - 8문항 (고정 5 + 동적 3)
- **고정 질문 5개**:
  - 필수 기술 스택, 선호 경험/역량, 기술 난이도, 우대 스킬, 담당 업무 범위

- **동적 질문 3개** (LangGraph 사용):
  - 고정 5개 답변 기반 → 실시간 추천 질문 생성
  - 기업 프로필 + 기존 JD 활용

- **분석 결과** (`TechnicalRequirements`):
  - 기술 요구사항, 우선순위, 깊이 수준 등

- **API 엔드포인트**:
  - `POST /api/company-interview/technical/start` → job_posting_id (optional) 로드, 첫 질문
  - `POST /api/company-interview/technical/answer` → 답변 제출 (동적 질문 자동 생성)
  - `GET /api/company-interview/technical/analysis/{session_id}` → 분석 결과 조회

---

### ③ Situational Interview - 8문항 (고정 5 + 동적 3)
- **고정 질문 5개**:
  - 팀 구성/협업 방식, 의사결정 스타일, 성장 기회, 업무 속도/일정, 리더십/멘토링

- **동적 질문 3개** (LangGraph 사용):
  - 고정 5개 답변 기반 → 실시간 추천 질문 생성

- **분석 결과** (`TeamCultureProfile`):
  - 팀 핏, 문화 핏, 리더십 스타일 등

- **API 엔드포인트**:
  - `POST /api/company-interview/situational/start` → 첫 질문
  - `POST /api/company-interview/situational/answer` → 답변 제출 (동적 질문 자동 생성)
  - `GET /api/company-interview/situational/analysis/{session_id}` → 분석 결과 조회

---

### ④ JD 생성/업데이트
- **3가지 면접 결과 통합** → JD 생성:
  - `responsibilities`: 담당 업무
  - `requirements_must`: 필수 요건
  - `requirements_nice`: 우대 사항
  - `competencies`: 핵심 역량

- **기존 JD 처리**:
  - 기존 JD가 있으면 4개 필드만 업데이트
  - 나머지 필드 (location_city, employment_type 등)는 유지

- **API 엔드포인트**:
  - `POST /api/company-interview/situational/analysis` → JD 데이터 생성 (백엔드 POST 안 함, response만)

---

### ⑤ Card & Matching Vectors 생성
- **Job Posting Card 생성**:
  - 3가지 면접 분석 통합
  - 기업 프로필 + JD 데이터
  - 백엔드 POST → `POST /api/job_posting_cards/` (409 발생 시 자동 PATCH)

- **6가지 매칭 벡터 생성**:
  - 인재와 동일한 6가지 차원
  - OpenAI Embeddings → 백엔드 POST → `POST /api/matching-vectors/`

- **API 엔드포인트**:
  - `POST /api/company-interview/generate` → 수정된 JD로 카드 및 벡터 생성
    - job_posting_id 필수
    - responsibilities, requirements_must, requirements_nice, competencies 받아서 PATCH
    - 카드 생성 → 백엔드 POST
    - 벡터 생성 → 백엔드 POST

---

## 3. 핵심 기술 스택

### Backend Framework
- **FastAPI**: 웹 프레임워크
- **Uvicorn**: ASGI 서버
- **Pydantic**: 데이터 검증 및 설정 관리

### AI/LLM
- **LangChain**: LLM 오케스트레이션
- **LangGraph**: 동적 질문 생성 (회사 Technical/Situational)
- **OpenAI GPT-4o**: 면접 분석, 질문 생성, 카드 생성
- **OpenAI GPT-4.1-mini**: 일부 간단한 분석 (Company General)
- **OpenAI Whisper**: STT (Speech-to-Text)
- **OpenAI Embeddings**: 벡터 생성 (text-embedding-ada-002, 1536차원)

### Vector Database
- **ChromaDB**: 벡터 임베딩 저장 및 검색

### Session Management
- **In-memory Dictionary**: 현재 세션 저장소
- **TODO**: Redis 또는 PostgreSQL로 마이그레이션 예정

---

## 4. 세션 관리

### Talent 세션 (`InterviewSession`)
- `session_id`: UUID
- `interview`: GeneralInterview 인스턴스
- `general_analysis`: GeneralInterviewAnalysis (캐싱)
- `technical_interview`: TechnicalInterview 인스턴스
- `situational_interview`: SituationalInterview 인스턴스
- `created_at`, `updated_at`: 타임스탬프

### Company 세션 (`CompanyInterviewSession`)
- `session_id`: UUID
- `company_name`: 회사명
- `existing_jd`: 기존 JD (optional)
- `company_info`: 기업 정보 (Technical에서 로드)
- `general_interview`: CompanyGeneralInterview 인스턴스
- `technical_interview`: CompanyTechnicalInterview 인스턴스
- `situational_interview`: CompanySituationalInterview 인스턴스
- `general_analysis`, `technical_requirements`, `situational_profile`: 분석 결과 (캐싱)
- `generated_jd`: 생성된 JD 데이터 (캐싱)
- `created_at`, `updated_at`: 타임스탬프

### 세션 API
- `GET /api/interview/general/session/{session_id}` → 인재 세션 정보 조회
- `DELETE /api/interview/general/session/{session_id}` → 인재 세션 삭제
- `GET /api/company-interview/session/{session_id}` → 기업 세션 정보 조회
- `DELETE /api/company-interview/session/{session_id}` → 기업 세션 삭제

---

## 5. 주요 데이터 모델

### Talent 모델
- `CandidateProfile`: 전체 프로필 (basic, experiences, educations, activities, certifications, documents)
- `GeneralInterviewAnalysis`: 구조화 면접 분석
- `TechnicalInterviewAnalysis`: 직무 면접 분석
- `FinalPersonaReport`: 상황 면접 페르소나 리포트
- `CandidateProfileCard`: 최종 프로필 카드

### Company 모델
- `CompanyGeneralAnalysis`: General 면접 분석
- `TechnicalRequirements`: Technical 면접 분석
- `TeamCultureProfile`: Situational 면접 분석
- `JobPostingCard`: 최종 채용공고 카드

### 공통 모델
- `CompetencyItem`: 역량 항목 (name, level)
- `InterviewQuestion`: 면접 질문
- `AnswerFeedback`: 답변 피드백

---

## 6. 백엔드 API 통합

### Client (`ai/interview/client.py`)
- `get_talent_profile(access_token)`: 인재 프로필 가져오기
- `get_company_profile(access_token)`: 기업 프로필 가져오기
- `get_job_posting(job_posting_id, access_token)`: 채용공고 가져오기
- `update_job_posting(job_posting_id, access_token, updates)`: 채용공고 업데이트 (PATCH)
- `post_talent_card(card_data, access_token)`: 인재 카드 POST
- `create_job_posting_card(access_token, card_data)`: 채용공고 카드 POST/PATCH
- `post_matching_vectors(vectors_data, access_token, role, job_posting_id)`: 매칭 벡터 POST

---

## 7. 디렉토리 구조

```
fitconnect-backend/
├── main.py                          # FastAPI 앱 진입점
├── config/
│   └── settings.py                  # 환경 설정
├── api/
│   ├── routes.py                    # 기본 API 라우트
│   ├── interview_routes.py          # 인재 면접 API
│   └── company_interview_routes.py  # 기업 면접 API
├── ai/
│   ├── interview/
│   │   ├── client.py                # 백엔드 API 클라이언트
│   │   ├── talent/
│   │   │   ├── general.py           # 구조화 면접
│   │   │   ├── technical.py         # 직무 면접
│   │   │   ├── situational.py       # 상황 면접
│   │   │   ├── models.py            # 데이터 모델
│   │   │   └── card_generator.py    # 카드 생성
│   │   └── company/
│   │       ├── general.py           # General 면접
│   │       ├── technical.py         # Technical 면접
│   │       ├── technical_graph.py   # LangGraph (동적 질문)
│   │       ├── situational.py       # Situational 면접
│   │       ├── situational_graph.py # LangGraph (동적 질문)
│   │       ├── models.py            # 데이터 모델
│   │       └── jd_generator.py      # JD 생성
│   ├── matching/
│   │   ├── vector_generator.py      # 인재 벡터 생성
│   │   ├── company_vector_generator.py # 기업 벡터 생성
│   │   └── embedding.py             # 임베딩 유틸
│   └── stt/
│       └── service.py               # STT 서비스 (Whisper)
└── data/
    └── chroma/                      # ChromaDB 저장소
```

---

## 8. 환경 변수 (.env)

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic (Optional)
ANTHROPIC_API_KEY=sk-ant-...

# Backend API
BACKEND_API_URL=http://52.91.24.1:8000

# CORS Origins
BACKEND_CORS_ORIGINS=["http://localhost:3000","https://fitconnect-frontend.vercel.app"]

# LangGraph 설정
USE_LANGGRAPH_FOR_QUESTIONS=True

# Whisper Model
WHISPER_MODEL=base

# ChromaDB
CHROMA_PERSIST_DIRECTORY=./data/chroma

# File Upload
MAX_FILE_SIZE=10485760
UPLOAD_DIRECTORY=./uploads
```

---

## 9. 주요 플로우 시퀀스

### 인재 면접 전체 플로우
```
1. POST /interview/general/start
   → session_id, 첫 질문

2. POST /interview/general/answer/audio (x5)
   → STT → 답변 저장 → 다음 질문

3. GET /interview/general/analysis/{session_id}
   → GeneralInterviewAnalysis

4. POST /interview/technical/start (access_token)
   → 백엔드에서 프로필 로드 → 기술 선정 → 첫 질문

5. POST /interview/technical/answer (x9)
   → 피드백 + 다음 질문

6. GET /interview/technical/results/{session_id}
   → TechnicalInterviewAnalysis

7. POST /interview/situational/start
   → 첫 질문

8. POST /interview/situational/answer (x6)
   → 분석 + 다음 질문

9. GET /interview/situational/report/{session_id}
   → FinalPersonaReport

10. POST /interview/profile-card/generate-and-post
    → 카드 생성 → 백엔드 POST

11. POST /interview/matching-vectors/generate
    → 벡터 생성 → 백엔드 POST
```

### 기업 면접 전체 플로우
```
1. POST /company-interview/general/start (access_token)
   → 회사명 로드 → session_id, 첫 질문

2. POST /company-interview/general/answer (x5)
   → 답변 저장 → 다음 질문

3. GET /company-interview/general/analysis/{session_id}
   → CompanyGeneralAnalysis

4. POST /company-interview/technical/start (job_posting_id optional)
   → 기업 정보 + JD 로드 → 첫 질문 (고정)

5. POST /company-interview/technical/answer (x8)
   → 고정 5개 완료 후 동적 3개 자동 생성 (LangGraph)

6. GET /company-interview/technical/analysis/{session_id}
   → TechnicalRequirements

7. POST /company-interview/situational/start
   → 첫 질문 (고정)

8. POST /company-interview/situational/answer (x8)
   → 고정 5개 완료 후 동적 3개 자동 생성 (LangGraph)

9. GET /company-interview/situational/analysis/{session_id}
   → TeamCultureProfile

10. POST /company-interview/situational/analysis (job_posting_id)
    → JD 4개 필드 생성 → response 반환 (POST 안 함)

11. POST /company-interview/generate (수정된 4개 필드 + job_posting_id)
    → JD PATCH → 카드 생성 → 벡터 생성 → 백엔드 POST
```

---

## 10. 주요 특징

### 개인화된 면접
- **인재**: General 분석 + 프로필 → 기술 스택 맞춤형 질문
- **기업**: General 분석 + 기업 정보 + JD → 동적 질문 생성 (LangGraph)

### 실시간 피드백
- **인재 Technical**: 답변마다 피드백 제공 (점수 없음)
- **기업 Technical/Situational**: 고정 5개 완료 후 동적 질문 실시간 생성

### 통합 카드 생성
- 3가지 면접 결과 통합 → 단일 카드 생성
- 부족한 항목 자동 보완 (Situational에서)

### 매칭 벡터
- 6가지 차원 벡터 생성 → 정밀한 매칭 가능
- 인재 ↔ 기업 벡터 유사도 계산으로 매칭

---

이 문서는 FitConnect 인터뷰 시스템의 전체 플로우와 구조를 설명합니다.
