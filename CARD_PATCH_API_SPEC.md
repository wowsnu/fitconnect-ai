# 카드 PATCH API 스펙 요청

## 개요
현재 카드 POST 시 409 에러가 발생하면 AI 서버에서 자동으로 PATCH로 업데이트하도록 구현했습니다.
백엔드에서 PATCH 엔드포인트를 아래 스펙에 맞춰 구현해주세요.

---

## 1. Talent Card (인재 카드) PATCH

### 엔드포인트
```
PATCH /api/talent_cards/{user_id}
```

### 인증
- **Required**: JWT Bearer Token
- `Authorization: Bearer {access_token}`

### Path Parameter
- `user_id` (int): 사용자 ID (인재 카드의 식별자)

### Request Body
```json
{
  "user_id": 123,
  "header_title": "5년차 백엔드 개발자",
  "key_strengths": [
    "Python/FastAPI 전문",
    "대규모 시스템 설계 경험",
    "팀 리딩 경험"
  ],
  "experience_summary": "스타트업과 대기업에서 백엔드 개발 경력 5년...",
  "growth_potential": "MSA 아키텍처 전환 프로젝트 리딩 경험...",
  "ideal_role": "테크 리드 또는 시니어 백엔드 개발자...",
  "work_style": "애자일 환경에서 자율적이고 책임감 있게..."
}
```

### 비즈니스 로직
1. JWT에서 user_id 추출
2. Path의 user_id와 JWT user_id가 일치하는지 확인 (본인 카드만 수정 가능)
3. Body의 user_id는 선택적 (있어도 무시하고 Path user_id 사용)
4. **모든 필드를 덮어쓰기** (전체 업데이트)
5. updated_at 자동 갱신

### Response (200 OK)
```json
{
  "ok": true,
  "data": {
    "id": 456,
    "user_id": 123,
    "header_title": "5년차 백엔드 개발자",
    "key_strengths": ["Python/FastAPI 전문", "대규모 시스템 설계 경험", "팀 리딩 경험"],
    "experience_summary": "스타트업과 대기업에서 백엔드 개발 경력 5년...",
    "growth_potential": "MSA 아키텍처 전환 프로젝트 리딩 경험...",
    "ideal_role": "테크 리드 또는 시니어 백엔드 개발자...",
    "work_style": "애자일 환경에서 자율적이고 책임감 있게...",
    "updated_at": "2025-10-20T15:30:00"
  }
}
```

### Error Responses

#### 403 Forbidden (다른 사용자의 카드 수정 시도)
```json
{
  "ok": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "You can only update your own talent card"
  }
}
```

#### 404 Not Found (카드가 존재하지 않음)
```json
{
  "ok": false,
  "error": {
    "code": "CARD_NOT_FOUND",
    "message": "Talent card not found for user_id 123"
  }
}
```

### 참고사항
- **POST와 동일한 Body 구조** 사용 가능
- 부분 업데이트가 아닌 **전체 덮어쓰기**
- user_id는 talent_cards 테이블의 unique key

---

## 2. Job Posting Card (채용공고 카드) PATCH

### 엔드포인트
```
PATCH /api/job_posting_cards/{job_posting_id}
```

### 인증
- **Required**: JWT Bearer Token
- `Authorization: Bearer {access_token}`

### Path Parameter
- `job_posting_id` (int): 채용공고 ID (카드와 1:1 매핑)

### Request Body
```json
{
  "job_posting_id": 789,
  "header_title": "시니어 백엔드 개발자",
  "responsibilities": "API 설계 및 개발, 대규모 트래픽 처리...",
  "key_qualifications": [
    "Python/FastAPI 5년 이상",
    "MSA 아키텍처 설계 경험",
    "대규모 시스템 운영 경험"
  ],
  "preferred_qualifications": [
    "Kubernetes, Docker 경험",
    "팀 리딩 경험"
  ],
  "growth_opportunities": "테크 리드로 성장 기회 제공...",
  "team_culture": "수평적 문화, 애자일 개발..."
}
```

### 비즈니스 로직
1. JWT에서 user_id 추출
2. job_posting_id에 해당하는 채용공고가 해당 user의 회사 소유인지 확인
3. Body의 job_posting_id는 선택적 (있어도 무시하고 Path job_posting_id 사용)
4. **모든 필드를 덮어쓰기** (전체 업데이트)
5. updated_at 자동 갱신

### Response (200 OK)
```json
{
  "ok": true,
  "data": {
    "id": 890,
    "job_posting_id": 789,
    "header_title": "시니어 백엔드 개발자",
    "responsibilities": "API 설계 및 개발, 대규모 트래픽 처리...",
    "key_qualifications": ["Python/FastAPI 5년 이상", "MSA 아키텍처 설계 경험", "대규모 시스템 운영 경험"],
    "preferred_qualifications": ["Kubernetes, Docker 경험", "팀 리딩 경험"],
    "growth_opportunities": "테크 리드로 성장 기회 제공...",
    "team_culture": "수평적 문화, 애자일 개발...",
    "updated_at": "2025-10-20T15:30:00"
  }
}
```

### Error Responses

#### 403 Forbidden (다른 회사의 채용공고 카드 수정 시도)
```json
{
  "ok": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "You can only update your company's job posting cards"
  }
}
```

#### 404 Not Found (카드가 존재하지 않음)
```json
{
  "ok": false,
  "error": {
    "code": "CARD_NOT_FOUND",
    "message": "Job posting card not found for job_posting_id 789"
  }
}
```

### 참고사항
- **POST와 동일한 Body 구조** 사용 가능
- 부분 업데이트가 아닌 **전체 덮어쓰기**
- job_posting_id는 job_posting_cards 테이블의 unique key (1:1 관계)

---

## 공통 요구사항

### 1. 전체 덮어쓰기 vs 부분 업데이트
- **전체 덮어쓰기 방식** 권장 (POST와 동일한 Body 사용 가능)
- 모든 필드를 새로운 값으로 교체
- 누락된 필드는 null로 처리하지 말고, 필수 검증 수행

### 2. Body 구조
- **POST와 동일한 구조** 사용
- 추가 필드나 다른 필드 불필요
- AI 서버에서 POST 실패 시 동일한 데이터로 PATCH 호출

### 3. 권한 검증
- **Talent Card**: JWT user_id와 path user_id 일치 확인
- **Job Posting Card**: JWT user의 회사가 job_posting 소유 확인

### 4. 응답 형식
- POST와 동일한 응답 형식
- `updated_at` 필드 자동 갱신

---

## AI 서버 사용 예시

### Talent Card
```python
# POST 시도
response = await client.post("/api/talent_cards", json=card_data)

# 409 발생 시 자동으로 PATCH
if response.status_code == 409:
    user_id = card_data["user_id"]
    response = await client.patch(f"/api/talent_cards/{user_id}", json=card_data)
```

### Job Posting Card
```python
# POST 시도
response = await client.post("/api/job_posting_cards", json=card_data)

# 409 발생 시 자동으로 PATCH
if response.status_code == 409:
    job_posting_id = card_data["job_posting_id"]
    response = await client.patch(f"/api/job_posting_cards/{job_posting_id}", json=card_data)
```

---

## 기존 API와의 관계

| API | 용도 | 상태 |
|-----|------|------|
| `POST /api/talent_cards` | 인재 카드 생성 | ✅ 기존 |
| `PATCH /api/talent_cards/{user_id}` | 인재 카드 업데이트 | ⭐ 신규 요청 |
| `POST /api/job_posting_cards` | 채용공고 카드 생성 | ✅ 기존 |
| `PATCH /api/job_posting_cards/{job_posting_id}` | 채용공고 카드 업데이트 | ⭐ 신규 요청 |

---

## 테스트 시나리오

### Talent Card
1. **정상 케이스**: 본인 카드 PATCH → 200 OK
2. **권한 오류**: 다른 사용자 카드 PATCH → 403 Forbidden
3. **존재하지 않음**: 존재하지 않는 user_id PATCH → 404 Not Found

### Job Posting Card
1. **정상 케이스**: 본인 회사 채용공고 카드 PATCH → 200 OK
2. **권한 오류**: 다른 회사 채용공고 카드 PATCH → 403 Forbidden
3. **존재하지 않음**: 존재하지 않는 job_posting_id PATCH → 404 Not Found

---

## SQL 예시 (참고)

### Talent Card PATCH
```sql
UPDATE talent_cards
SET
  header_title = :header_title,
  key_strengths = :key_strengths,
  experience_summary = :experience_summary,
  growth_potential = :growth_potential,
  ideal_role = :ideal_role,
  work_style = :work_style,
  updated_at = CURRENT_TIMESTAMP
WHERE user_id = :user_id;
```

### Job Posting Card PATCH
```sql
UPDATE job_posting_cards
SET
  header_title = :header_title,
  responsibilities = :responsibilities,
  key_qualifications = :key_qualifications,
  preferred_qualifications = :preferred_qualifications,
  growth_opportunities = :growth_opportunities,
  team_culture = :team_culture,
  updated_at = CURRENT_TIMESTAMP
WHERE job_posting_id = :job_posting_id;
```

---

**작성자**: AI Team
**작성일**: 2025-10-20
**우선순위**: High (409 에러 발생 시 자동 PATCH 기능을 위해 필수)
