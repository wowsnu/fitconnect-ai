# 백엔드 매칭 텍스트 저장 요구사항

## 📋 배경 및 목적

**현재 상황:**
- AI 서버에서 6개 차원별로 **500-700자 텍스트 생성** → **1536차원 벡터로 임베딩**
- 백엔드 DB에는 **벡터만 저장**되고 원본 텍스트는 저장되지 않음

**문제점:**
- XAI (설명 가능한 AI) 구현 시 **원본 텍스트 없이는 설명 불가능**
- 매칭 이유를 사용자에게 설명하려면 원본 텍스트 필요

**해결 방안:**
- 벡터와 함께 **원본 텍스트도 DB에 저장** 필요

---

## 🎯 요구사항 요약

### 1. API 수정 사항

#### 현재 AI 서버 → 백엔드 전송 데이터
```json
POST /api/me/matching-vectors
{
  "vector_roles": {
    "vector": [0.123, -0.456, ..., 0.789]  // 1536개 float
  },
  "vector_skills": {
    "vector": [...]
  },
  "vector_growth": {
    "vector": [...]
  },
  "vector_career": {
    "vector": [...]
  },
  "vector_vision": {
    "vector": [...]
  },
  "vector_culture": {
    "vector": [...]
  },
  "role": "talent"  // or "company"
}
```

#### 변경 요청: 텍스트 필드 추가
```json
POST /api/me/matching-vectors
{
  "vector_roles": {
    "vector": [0.123, -0.456, ..., 0.789],
    "text": "백엔드 개발자로 3년간 Python과 Django를 활용한 RESTful API 설계 및 개발 경험을 쌓았습니다. 주요 프로젝트로는 전자상거래 플랫폼의 결제 시스템 개발이 있으며..."  // 500-700자
  },
  "vector_skills": {
    "vector": [...],
    "text": "Python과 FastAPI를 주력 기술로 사용하며, Django, Flask 등 다양한 웹 프레임워크에 대한 실무 경험을 보유하고 있습니다..."
  },
  "vector_growth": {
    "vector": [...],
    "text": "..."
  },
  "vector_career": {
    "vector": [...],
    "text": "..."
  },
  "vector_vision": {
    "vector": [...],
    "text": "..."
  },
  "vector_culture": {
    "vector": [...],
    "text": "..."
  },
  "role": "talent"
}
```

---

### 2. DB 스키마 수정

#### 현재 구조 (추정)
```sql
-- matching_vectors 테이블
CREATE TABLE matching_vectors (
    id SERIAL PRIMARY KEY,
    user_id INT,
    role VARCHAR(10),  -- 'talent' or 'company'
    job_posting_id INT,  -- company인 경우만
    
    -- 벡터 컬럼들 (PostgreSQL pgvector 사용)
    vector_roles vector(1536),
    vector_skills vector(1536),
    vector_growth vector(1536),
    vector_career vector(1536),
    vector_vision vector(1536),
    vector_culture vector(1536),
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### 변경 요청: 텍스트 컬럼 추가
```sql
CREATE TABLE matching_vectors (
    id SERIAL PRIMARY KEY,
    user_id INT,
    role VARCHAR(10),
    job_posting_id INT,
    
    -- 벡터 컬럼들
    vector_roles vector(1536),
    vector_skills vector(1536),
    vector_growth vector(1536),
    vector_career vector(1536),
    vector_vision vector(1536),
    vector_culture vector(1536),
    
    -- 텍스트 컬럼들 추가 (각 500-700자)
    text_roles TEXT,      -- 역할 적합도 텍스트
    text_skills TEXT,     -- 역량 적합도 텍스트
    text_growth TEXT,     -- 성장 가능성 텍스트
    text_career TEXT,     -- 커리어 방향 텍스트
    text_vision TEXT,     -- 비전/협업 텍스트
    text_culture TEXT,    -- 조직/문화 텍스트
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**스토리지 영향:**
- 텍스트 6개 × 평균 600자 = 약 3.6KB per row
- 인재 1000명 = 약 3.6MB (무시 가능한 수준)

---

### 3. API 응답 수정

#### 매칭 결과 조회 API
```json
GET /api/matching/results?talent_id=123&company_id=456

// 응답에 텍스트 포함
{
  "match_score": 0.85,
  "dimension_scores": {
    "roles": 0.88,
    "skills": 0.91,
    "growth": 0.82,
    "career": 0.84,
    "vision": 0.87,
    "culture": 0.79
  },
  "talent_vectors": {
    "vector_roles": {
      "vector": [...],
      "text": "백엔드 개발자로 3년간..."  // ← 추가
    },
    "vector_skills": {
      "vector": [...],
      "text": "Python과 FastAPI를..."  // ← 추가
    },
    // ... 나머지
  },
  "company_vectors": {
    "vector_roles": {
      "vector": [...],
      "text": "시니어 백엔드 개발자를 채용하며..."  // ← 추가
    },
    // ... 나머지
  }
}
```

---

## 🔧 구현 가이드

### Phase 1: DB 마이그레이션
```sql
-- 1단계: 텍스트 컬럼 추가 (NULL 허용)
ALTER TABLE matching_vectors 
ADD COLUMN text_roles TEXT,
ADD COLUMN text_skills TEXT,
ADD COLUMN text_growth TEXT,
ADD COLUMN text_career TEXT,
ADD COLUMN text_vision TEXT,
ADD COLUMN text_culture TEXT;

-- 2단계: 인덱스 추가 (선택사항, 검색 성능 향상)
CREATE INDEX idx_matching_vectors_user_role ON matching_vectors(user_id, role);
CREATE INDEX idx_matching_vectors_job_posting ON matching_vectors(job_posting_id) WHERE role = 'company';
```

### Phase 2: API 코드 수정

#### POST /api/me/matching-vectors
```typescript
// 요청 DTO
interface CreateMatchingVectorDto {
  vector_roles: { vector: number[]; text: string };
  vector_skills: { vector: number[]; text: string };
  vector_growth: { vector: number[]; text: string };
  vector_career: { vector: number[]; text: string };
  vector_vision: { vector: number[]; text: string };
  vector_culture: { vector: number[]; text: string };
  role: 'talent' | 'company';
  job_posting_id?: number;
}

// 저장 로직
async createMatchingVector(dto: CreateMatchingVectorDto, userId: number) {
  return this.matchingVectorRepository.save({
    user_id: userId,
    role: dto.role,
    job_posting_id: dto.job_posting_id,
    
    // 벡터
    vector_roles: dto.vector_roles.vector,
    vector_skills: dto.vector_skills.vector,
    vector_growth: dto.vector_growth.vector,
    vector_career: dto.vector_career.vector,
    vector_vision: dto.vector_vision.vector,
    vector_culture: dto.vector_culture.vector,
    
    // 텍스트 (새로 추가)
    text_roles: dto.vector_roles.text,
    text_skills: dto.vector_skills.text,
    text_growth: dto.vector_growth.text,
    text_career: dto.vector_career.text,
    text_vision: dto.vector_vision.text,
    text_culture: dto.vector_culture.text,
  });
}
```

#### PATCH /api/me/matching-vectors/:id
```typescript
// 업데이트도 동일하게 텍스트 포함
async updateMatchingVector(id: number, dto: UpdateMatchingVectorDto) {
  return this.matchingVectorRepository.update(id, {
    vector_roles: dto.vector_roles.vector,
    text_roles: dto.vector_roles.text,
    // ... 나머지 필드들
  });
}
```

#### GET /api/matching/results
```typescript
// 매칭 결과 조회 시 텍스트 포함
async getMatchingResults(talentId: number, companyId: number) {
  const talent = await this.getTalentVectors(talentId);
  const company = await this.getCompanyVectors(companyId);
  
  return {
    match_score: this.calculateScore(talent, company),
    talent_vectors: {
      vector_roles: {
        vector: talent.vector_roles,
        text: talent.text_roles,  // ← 추가
      },
      // ... 나머지
    },
    company_vectors: {
      vector_roles: {
        vector: company.vector_roles,
        text: company.text_roles,  // ← 추가
      },
      // ... 나머지
    }
  };
}
```

---

## 📊 AI 서버 측 수정 사항

### 현재 코드 (ai/interview/client.py)
```python
# 변경 전
await backend_client.post_matching_vectors(
    vectors_data=result["vectors"],  # 벡터만 전송
    access_token=request.access_token,
    role="talent"
)
```

### 수정할 코드
```python
# 변경 후: 벡터 + 텍스트 함께 전송
vectors_with_texts = {
    "vector_roles": {
        "vector": result["vectors"]["vector_roles"]["vector"],
        "text": result["texts"]["roles_text"]
    },
    "vector_skills": {
        "vector": result["vectors"]["vector_skills"]["vector"],
        "text": result["texts"]["skills_text"]
    },
    "vector_growth": {
        "vector": result["vectors"]["vector_growth"]["vector"],
        "text": result["texts"]["growth_text"]
    },
    "vector_career": {
        "vector": result["vectors"]["vector_career"]["vector"],
        "text": result["texts"]["career_text"]
    },
    "vector_vision": {
        "vector": result["vectors"]["vector_vision"]["vector"],
        "text": result["texts"]["vision_text"]
    },
    "vector_culture": {
        "vector": result["vectors"]["vector_culture"]["vector"],
        "text": result["texts"]["culture_text"]
    }
}

await backend_client.post_matching_vectors(
    vectors_data=vectors_with_texts,
    access_token=request.access_token,
    role="talent"
)
```

---

## ✅ 체크리스트

### 백엔드 팀 작업
- [ ] DB 스키마에 텍스트 컬럼 6개 추가
- [ ] POST /api/me/matching-vectors API 수정 (텍스트 받기)
- [ ] PATCH /api/me/matching-vectors/:id API 수정 (텍스트 업데이트)
- [ ] GET /api/matching/results API 수정 (텍스트 반환)
- [ ] 기존 데이터 마이그레이션 계획 (text 컬럼이 NULL인 경우 처리)

### AI 팀 작업 (우리)
- [ ] client.py의 post_matching_vectors 호출 부분 수정
- [ ] 벡터 + 텍스트 합쳐서 전송하도록 변경
- [ ] XAI API 구현 (텍스트 활용한 설명 생성)

---

## 🎯 XAI 활용 시나리오 (구현 후)

```python
# XAI API 예시
GET /api/matching/explain?talent_id=123&company_id=456&dimension=skills

# 응답
{
  "dimension": "skills",
  "similarity_score": 0.91,
  "explanation": {
    "talent_highlights": [
      "Python과 FastAPI를 주력 기술로 사용",
      "Django, Flask 등 다양한 웹 프레임워크 실무 경험",
      "PostgreSQL, Redis 데이터베이스 최적화"
    ],
    "company_requirements": [
      "Python/FastAPI 기반 API 서버 개발 경험 필수",
      "RESTful API 설계 원칙 준수",
      "대용량 트래픽 처리 경험"
    ],
    "matching_keywords": [
      {"keyword": "Python", "importance": 0.95},
      {"keyword": "FastAPI", "importance": 0.92},
      {"keyword": "API", "importance": 0.88}
    ],
    "summary": "인재의 Python/FastAPI 기반 백엔드 개발 경험이 기업의 요구사항과 매우 높은 일치도를 보입니다."
  }
}
```

---

## 📞 문의사항

- AI 팀 담당: [이름]
- 백엔드 팀 담당: [이름]
- 예상 작업 기간: DB 마이그레이션 1일, API 수정 2일
- 배포 일정: [날짜]

---

## 🚀 우선순위

**P0 (필수):**
- DB 텍스트 컬럼 추가
- POST API 수정 (텍스트 저장)

**P1 (중요):**
- GET API 수정 (텍스트 반환)
- PATCH API 수정 (텍스트 업데이트)

**P2 (선택):**
- 기존 데이터 마이그레이션 (NULL 처리)
- 텍스트 검색/인덱싱
