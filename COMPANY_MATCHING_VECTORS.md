# 기업 매칭 벡터 생성 시스템

## 개요

기업 면접 결과를 바탕으로 **6가지 매칭 기준별 텍스트**를 LLM으로 생성하고, 이를 임베딩하여 인재 매칭에 활용합니다.

## 6가지 매칭 기준

### 1. 역할 제공/역할 요구사항 (vector_roles)
**목적**: 기업이 제공하는 역할과 요구하는 실무 경험을 명확히 합니다.

**포함 내용**:
- 제공하는 역할과 책임 범위
- 요구되는 경력 연차와 포지션 수준
- 담당할 주요 업무와 프로젝트
- 기대하는 성과와 결과물

**예시**:
```
시니어 백엔드 개발자로서 AI 추천 시스템 API 설계 및 개발을 주도.
Redis 기반 캐싱 전략 수립과 성능 최적화 담당.
실시간 처리 시스템 아키텍처 설계 및 구현.
주니어 개발자 멘토링과 코드 리뷰 리드.
월 1억 이상 트래픽 처리하는 확장 가능한 백엔드 시스템 구축 기대.
```

### 2. 역량 요구사항 (vector_skills)
**목적**: 직무 수행에 필요한 기술 스택과 역량을 명확히 합니다.

**포함 내용**:
- 필수 기술 스택과 수준
- 필수 일반 역량 (협업, 커뮤니케이션, 문제 해결 등)
- 우대 기술 스택
- 실무에서 사용할 도구와 프레임워크

**예시**:
```
필수 기술: Python/FastAPI 실무 5년 이상, PostgreSQL 쿼리 최적화 경험,
Redis 캐싱 전략 수립 경험, AWS 인프라 운영 경험.
필수 역량: 협업 능력(높음), 문제 해결 능력(높음), 커뮤니케이션(높음).
우대 기술: Kubernetes, Kafka, Elasticsearch, MSA 아키텍처 설계 경험.
```

### 3. 성장 기회 제공 (vector_growth)
**목적**: 기업이 제공하는 학습 환경과 성장 기회를 명확히 합니다.

**포함 내용**:
- 제공하는 학습 기회 (교육, 컨퍼런스, 스터디 등)
- 새로운 기술/프로젝트 도전 기회
- 멘토링 및 성장 지원 체계
- 경력 발전 경로

**예시**:
```
분산 시스템과 MSA 전환 프로젝트 참여 기회.
대규모 트래픽 처리 경험 축적 가능.
시니어 엔지니어의 1:1 멘토링 제공.
컨퍼런스 참가 및 기술 블로그 작성 지원.
새로운 기술 스택 도입 시 주도적 역할 부여.
테크 리드/아키텍트로 성장 경로 제공.
```

### 4. 커리어 방향 (vector_career)
**목적**: 기업이 제공하는 커리어 경로와 방향성을 명확히 합니다.

**포함 내용**:
- 제공하는 커리어 경로 (IC track, Management track)
- 성장 가능한 포지션과 역할
- 조직 내 발전 기회
- 장기적인 커리어 비전

**예시**:
```
시니어 백엔드 개발자에서 시작하여 테크 리드로 성장 가능.
IC track으로 Staff Engineer, Principal Engineer까지 커리어 패스 제공.
대규모 시스템 아키텍처 설계 경험 축적.
신규 서비스 런칭 시 테크 리딩 기회.
조직 확장에 따른 팀 리드 포지션 기회.
```

### 5. 비전/협업 환경 (vector_vision)
**목적**: 기업의 비전과 팀 협업 환경을 명확히 합니다.

**포함 내용**:
- 기업/팀의 비전과 미션
- 협업 문화와 방식
- 의사결정 구조
- 팀 내 기여 방식

**예시**:
```
AI 기술로 금융의 미래를 만드는 비전 추구.
데이터 기반 의사결정과 논리적 토론 문화.
코드 리뷰와 페어 프로그래밍 일상화.
2주 스프린트 애자일 개발.
팀원 모두가 의사결정에 참여하는 수평적 문화.
기술 블로그와 사내 세미나를 통한 지식 공유 활성화.
```

### 6. 조직/문화 적합도 (vector_culture)
**목적**: 기업의 조직 문화와 일하는 방식을 명확히 합니다.

**포함 내용**:
- 조직의 핵심 가치관
- 선호하는 업무 스타일
- 문제 해결 방식
- 커뮤니케이션 스타일

**예시**:
```
핵심 가치: 혁신, 도전, 투명성, 협력.
자율적이고 책임감 있는 업무 문화.
실패를 학습의 기회로 보는 도전적 환경.
데이터와 논리 기반의 분석적 문제 해결 선호.
직급보다 전문성을 존중하는 수평적 소통.
빠른 의사결정과 실행력 중시.
애자일하고 유연한 조직 문화.
```

## 아키텍처

### 1. 데이터 흐름

```
면접 결과 (General + Technical + Situational)
    ↓
생성된 채용공고 데이터 (JD)
    ↓
LLM 프롬프트 (모든 컨텍스트 포함)
    ↓
6가지 매칭 텍스트 생성
    ↓
OpenAI Embedding API (text-embedding-3-small)
    ↓
6개 벡터 (각 1536 차원)
    ↓
백엔드 DB 저장 (matching_vectors 테이블)
```

### 2. 구현 파일

#### `ai/matching/company_vector_generator.py`
- **역할**: 기업 매칭 텍스트 및 벡터 생성 (인재용 `vector_generator.py`와 동일 구조)
- **주요 함수**:
  - `generate_company_matching_texts()`: LLM으로 6가지 텍스트 생성
  - `generate_company_matching_vectors()`: 텍스트 + 임베딩 통합 처리

#### `ai/matching/embedding.py`
- **역할**: 텍스트 임베딩 처리 (인재/기업 공통)
- **주요 함수**:
  - `embed_matching_texts()`: 6개 텍스트를 한 번에 임베딩

#### `ai/interview/client.py`
- **역할**: 백엔드 API 통신
- **주요 메서드**:
  - `post_matching_vectors()`: 매칭 벡터 POST

#### `api/company_interview_routes.py`
- **엔드포인트**: `POST /api/company-interview/job-posting`
- **역할**: JD + Card + Matching Vector 한 번에 생성

## LLM 프롬프트 구조

### 입력 컨텍스트

```
[회사 정보]
- 회사명

[생성된 채용공고 (JD)]
- 직무명, 주요 업무, 필수 요건, 우대 요건, 필요 역량

[General 면접 분석]
- 핵심 가치
- 이상적 인재
- 팀 문화
- 업무 방식
- 채용 이유 (+ reasoning)

[Technical 면접 분석]
- 직무명
- 주요 업무
- 필수 역량
- 우대 역량
- 예상 도전 과제 (+ reasoning)

[Situational 면접 분석]
- 팀 현황 (+ reasoning)
- 협업 스타일 (+ reasoning)
- 갈등 해결 (+ reasoning)
- 업무 환경 (+ reasoning)
- 선호 업무 스타일 (+ reasoning)
```

### 출력 스키마

```python
class CompanyMatchingTexts(BaseModel):
    roles_text: str = Field(min_length=50)
    skills_text: str = Field(min_length=50)
    growth_text: str = Field(min_length=50)
    career_text: str = Field(min_length=50)
    vision_text: str = Field(min_length=50)
    culture_text: str = Field(min_length=50)
```

## 백엔드 통합

### API 엔드포인트

#### POST `/api/company-interview/job-posting`
**요청**:
```json
{
  "session_id": "uuid",
  "access_token": "jwt_token"
}
```

**응답**:
```json
{
  "success": true,
  "job_posting_id": 123,
  "card_id": 456,
  "matching_vector_id": 789,
  "job_posting": { ... },
  "card": { ... },
  "matching_texts": {
    "roles_text": "...",
    "skills_text": "...",
    "growth_text": "...",
    "career_text": "...",
    "vision_text": "...",
    "culture_text": "..."
  }
}
```

### 데이터베이스 스키마

#### `matching_vectors` 테이블
```sql
CREATE TABLE matching_vectors (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    role ENUM('talent', 'company') NOT NULL,
    vector_roles JSONB,  -- {"embedding": [float, ...]}
    vector_skills JSONB,
    vector_growth JSONB,
    vector_career JSONB,
    vector_vision JSONB,
    vector_culture JSONB,
    updated_at TIMESTAMP,
    INDEX(user_id),
    INDEX(role)
);
```

## 사용 예시

### 1. 전체 플로우 테스트

```bash
# 테스트 실행
python test_company_matching_vectors.py
```

### 2. 코드에서 직접 호출

```python
from ai.matching.company_vector_generator import generate_company_matching_vectors

# ��칭 벡터 생성
result = generate_company_matching_vectors(
    general_analysis=general_analysis,
    technical_requirements=technical_requirements,
    team_fit_analysis=team_fit_analysis,
    company_name="회사명",
    job_posting_data=job_posting_data
)

# 결과
print(result["texts"]["roles_text"])  # 역할 적합도 텍스트
print(result["vectors"]["vector_roles"])  # {"embedding": [1536 floats]}
```

## 성능 고려사항

### 1. LLM 호출 시간
- **예상 시간**: 2-4초
- **모델**: GPT-4o (temperature=0.3)
- **구조화 출력**: Pydantic 모델로 검증

### 2. 임베딩 시간
- **예상 시간**: 1-2초
- **모델**: text-embedding-3-small (1536 차원)
- **배치 처리**: 6개 텍스트를 한 번에 임베딩

### 3. 총 소요 시간
- **JD 생성**: 2-4초
- **Card 생성**: 2-4초
- **Matching Vector 생성**: 3-6초
- **백엔드 POST**: 1-2초
- **총합**: 약 8-16초

## 품질 관리

### 1. 텍스트 최소 길이
- 각 텍스트는 최소 50자 이상
- 프롬프트에서 50-400자 범위 지정

### 2. 일관성 유지
- 생성된 JD 데이터와 일관성 유지
- 면접 결과에서 드러난 실제 내용만 사용
- 추측이나 과장 금지

### 3. 구체성
- 수치, 사례, 키워드 포함
- 명확하고 간결한 표현

## 향후 개선 사항

1. **캐싱**: 동일 세션에서 재생성 방지
2. **비동기 처리**: JD/Card/Vector 병렬 생성으로 시간 단축
3. **벡터 품질 검증**: 임베딩 품질 자동 검증 로직
4. **A/B 테스트**: 프롬프트 개선을 위한 실험
5. **모니터링**: 생성 품질 및 매칭 성능 추적

## 참고 자료

- **기업 매칭 벡터**: `ai/matching/company_vector_generator.py`
- **인재 매칭 벡터**: `ai/matching/vector_generator.py`
- **임베딩 서비스**: `ai/matching/embedding.py`
- **백엔드 스키마**: `app/models/matching_vector.py`
- **테스트 스크립트**: `test_company_matching_vectors.py`
