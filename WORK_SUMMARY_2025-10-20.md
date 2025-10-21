# 작업 내용 정리 (2025-10-20)

## 목차
1. [기업 면접 질문 수 고정](#1-기업-면접-질문-수-고정-)
2. [중복 엔드포인트 삭제](#2-중복-엔드포인트-삭제-)
3. [JD 메타데이터 하드코딩 문제 해결](#3-jd-메타데이터-하드코딩-문제-해결-)
4. [JD 업데이트 로직 개선 (PATCH)](#4-jd-업데이트-로직-개선-patch-)
5. [/generate 엔드포인트 응답 개선](#5-generate-엔드포인트-응답-개선-)
6. [벡터 생성 가이드 준수](#6-벡터-생성-가이드-준수-)
7. [벡터 409 에러 시 PATCH 업데이트](#7-벡터-409-에러-시-patch-업데이트-)
8. [백엔드 API 요청사항 정리](#8-백엔드-api-요청사항-정리-)
9. [주요 성과 요약](#주요-성과-요약)
10. [수정된 파일 목록](#수정된-파일-목록)

---

## 1. 기업 면접 질문 수 고정 ✅

### 문제
- Technical/Situational 면접이 동적으로 2-3개 질문 생성
- 총 질문 수가 가변적 (7-8개)

### 해결
정확히 **8개로 고정** (고정 5개 + 동적 3개)

### 수정 파일
- `ai/interview/company/technical.py`
- `ai/interview/company/situational.py`

### 변경 내용
```python
# Before
"2-3개의 질문을 생성하세요"
total_questions = len(self.fixed_questions) + len(self.dynamic_questions)  # 가변

# After
"정확히 3개의 질문만 생성 (2개도 4개도 아닌 3개)"
total_questions = 8  # 고정
is_finished(): return self.current_index >= 8
```

### 추가 개선
- **한글 전용 질문 생성**: "모든 질문을 한글로만 작성하세요 (영어 질문 금지)"
- **total_fixed 필드**: 프론트엔드에 `total_fixed: 8` 전달

---

## 2. 중복 엔드포인트 삭제 ✅

### 문제
- `/job-posting` 엔드포인트가 `/generate`와 중복
- 실제로 사용되지 않음

### 해결
전체 삭제 (Line 833-956)

### 수정 파일
- `api/company_interview_routes.py`

### 삭제된 엔드포인트
```python
@company_interview_router.post("/job-posting")
async def create_job_posting_from_interview(...):
    # 전체 삭제됨
```

---

## 3. JD 메타데이터 하드코딩 문제 해결 ✅

### 문제
하드코딩된 필드들:
- `location_city = "서울"`
- `employment_type = "정규직"`
- `career_level = "경력 3년 이상"`
- `education_level = "학력무관"`
- `position = "Backend"`
- `position_group = "Engineering"`
- `department = "Development"`

### 해결
**3-tier 우선순위**로 데이터 추출

### 우선순위
1. **existing_jd** (기존 채용공고 데이터) - 최우선
2. **company_profile** (기업 프로필) - 차선
3. **기본값** (fallback) - 최후

### 수정 파일
- `ai/interview/company/jd_generator.py`

### 코드 예시
```python
if existing_jd:
    # Priority 1: Use existing JD data
    location_city = existing_jd.get("location_city", "서울")
    employment_type = existing_jd.get("employment_type", "정규직")
    position = existing_jd.get("position", "Backend")
    # ...
elif company_profile:
    # Priority 2: Use company profile
    raw_location = basic.get("location_city", "서울")
    location_city = normalize_location_city(raw_location)
    employment_type = basic.get("employment_type", "정규직")
    # ...
else:
    # Priority 3: Use defaults
    location_city = "서울"
    employment_type = "정규직"
    # ...
```

### 추가 기능: Location 정규화
```python
def normalize_location_city(location: str) -> str:
    """기업 프로필의 location을 백엔드 enum에 맞게 변환"""
    # "서울시 마포구" → "서울"
    allowed = ['서울', '경기', '인천', '부산', '대구', '대전', '광주', '울산',
               '강원', '충북', '충남', '전북', '전남', '경북', '경남']

    if location in allowed:
        return location

    for region in allowed:
        if region in location:
            return region

    return "서울"  # default
```

---

## 4. JD 업데이트 로직 개선 (PATCH) ✅

### 문제
- 사용자가 4개 필드만 수정하려 해도
- 전체 JD가 기본값으로 새로 생성됨
- 메타데이터(location, position 등)가 null로 초기화

### 해결
**PATCH 방식**으로 4개 필드만 업데이트

### 수정 파일
- `api/company_interview_routes.py` - `/generate` 엔드포인트
- `ai/interview/client.py` - `update_job_posting()` 메서드 추가

### 로직
```python
if job_posting_id:
    # 기존 JD가 있으면 4개 필드만 PATCH로 업데이트
    updates = {
        "responsibilities": request.responsibilities,
        "requirements_must": request.requirements_must,
        "requirements_nice": request.requirements_nice,
        "competencies": request.competencies
    }
    await backend_client.update_job_posting(
        job_posting_id=job_posting_id,
        access_token=request.access_token,
        updates=updates
    )

    # PATCH 후 최신 JD 데이터를 다시 가져오기 (카드 생성에 사용)
    updated_job_posting = await backend_client.get_job_posting(
        job_posting_id=job_posting_id,
        access_token=request.access_token
    )
    updated_jd_data = updated_job_posting
else:
    # 새로운 JD 생성
    created_job_posting = await backend_client.create_job_posting(
        access_token=request.access_token,
        job_posting_data=updated_jd_data
    )
    job_posting_id = created_job_posting.get("id")
```

### 추가된 메서드 (client.py)
```python
async def update_job_posting(
    self,
    job_posting_id: int,
    access_token: str,
    updates: dict
) -> dict:
    """
    채용공고 부분 업데이트 (PATCH /api/me/company/job-postings/{posting_id})
    """
    url = f"{self.backend_url}/api/me/company/job-postings/{job_posting_id}"
    response = await client.patch(url, headers=headers, json=updates)
    # ...
```

---

## 5. /generate 엔드포인트 응답 개선 ✅

### 문제
프론트엔드가 "응답을 못 받는다" 보고
- 중간에 에러 발생 시 응답이 안 감
- 어디서 실패했는지 알 수 없음

### 해결
모든 단계에 **에러 처리 + 상세 로그 추가**

### 수정 파일
- `api/company_interview_routes.py`

### 개선 사항

#### 1. JD 생성/업데이트 에러 처리
```python
try:
    if job_posting_id:
        await backend_client.update_job_posting(...)
    else:
        created_job_posting = await backend_client.create_job_posting(...)
except Exception as e:
    print(f"[ERROR] Failed to create/update job posting: {e}")
    raise HTTPException(status_code=500, detail=f"Failed to create/update job posting: {str(e)}")
```

#### 2. 카드 생성 에러 처리
```python
try:
    created_card = await backend_client.create_job_posting_card(...)
    print(f"[INFO] Job posting card created successfully: id={created_card.get('id')}")
except ValueError as e:
    if "409" in str(e):
        created_card = await backend_client.update_job_posting_card(...)
    else:
        raise HTTPException(status_code=500, detail=f"Failed to create job posting card: {str(e)}")
```

#### 3. 벡터 생성 에러 처리 ⭐ (새로 추가)
```python
try:
    matching_result = generate_company_matching_vectors(...)
    print(f"[INFO] Matching vectors generated successfully")
except Exception as e:
    print(f"[ERROR] Failed to generate matching vectors (OpenAI embedding): {e}")
    # 벡터 생성 실패해도 카드는 생성되었으므로 부분 성공으로 응답
    return {
        "success": True,
        "job_posting_id": job_posting_id,
        "card_id": created_card.get("id"),
        "matching_vector_id": None,
        "warning": "Matching vectors generation failed (OpenAI API error)"
    }
```

#### 4. 벡터 POST 에러 처리
```python
try:
    created_vectors = await backend_client.post_matching_vectors(...)
    print(f"[INFO] Matching vectors posted successfully: id={created_vectors.get('id')}")
except Exception as e:
    print(f"[ERROR] Failed to post matching vectors to backend: {e}")
    return {
        "success": True,
        "job_posting_id": job_posting_id,
        "card_id": created_card.get("id"),
        "matching_vector_id": None,
        "warning": "Matching vectors post failed (Backend API error)"
    }
```

### 부분 성공 응답 예시
```json
{
  "success": true,
  "job_posting_id": 3,
  "card_id": 12,
  "matching_vector_id": null,
  "card": {...},
  "matching_texts": {...},
  "warning": "Matching vectors generation failed (OpenAI API error)"
}
```

### 로그 출력 예시
```
[INFO] Updating existing job posting 3 with 4 fields...
[INFO] Updated job posting 3
[INFO] Creating job posting card for job_posting_id=3...
[INFO] Posting job posting card to backend...
[INFO] Job posting card created successfully: id=12
[INFO] Generating matching vectors for job_posting_id=3...
[INFO] Matching vectors generated successfully
[INFO] Posting matching vectors to backend for job_posting_id=3...
[INFO] Adding job_posting_id=3 for company role
[INFO] Matching vectors posted successfully: id=5
[INFO] All operations completed successfully. Returning response...
[DEBUG] Response data: success=True, job_posting_id=3, card_id=12
```

---

## 6. 벡터 생성 가이드 준수 ✅

### 문제
벡터 형식이 `VECTOR_CREATION_GUIDE.md`와 불일치

### 해결
가이드 스펙에 맞춰 수정

### 수정 파일
- `ai/matching/embedding.py`
- `ai/interview/client.py`
- `api/company_interview_routes.py`
- `api/interview_routes.py`

### 변경 사항

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| **벡터 키** | `{"embedding": [...]}` | `{"vector": [...]}` ✅ |
| **Company role** | `"company"` | `"company"` + `job_posting_id` ✅ |
| **Talent role** | `"talent"` | `"talent"` (job_posting_id 없음) ✅ |

### Company 벡터 예시
```json
{
  "role": "company",
  "job_posting_id": 789,
  "vector_roles": {"vector": [0.9, 0.8, 0.7, 0.6, 0.5]},
  "vector_skills": {"vector": [0.95, 0.9, 0.85, 0.8, 0.75]},
  "vector_growth": {"vector": [0.8, 0.7, 0.75, 0.85, 0.7]},
  "vector_career": {"vector": [0.7, 0.8, 0.6, 0.75, 0.85]},
  "vector_vision": {"vector": [0.85, 0.8, 0.75, 0.7, 0.8]},
  "vector_culture": {"vector": [0.8, 0.85, 0.7, 0.75, 0.9]}
}
```

### Talent 벡터 예시
```json
{
  "role": "talent",
  "vector_roles": {"vector": [0.9, 0.8, 0.7, 0.6, 0.5]},
  "vector_skills": {"vector": [0.95, 0.9, 0.85, 0.8, 0.75]},
  "vector_growth": {"vector": [0.8, 0.7, 0.75, 0.85, 0.7]},
  "vector_career": {"vector": [0.7, 0.8, 0.6, 0.75, 0.85]},
  "vector_vision": {"vector": [0.85, 0.8, 0.75, 0.7, 0.8]},
  "vector_culture": {"vector": [0.8, 0.85, 0.7, 0.75, 0.9]}
}
```

### 코드 변경 (embedding.py)
```python
# Before
return {
    "vector_roles": {"embedding": vectors[0]},
    "vector_skills": {"embedding": vectors[1]},
    # ...
}

# After
return {
    "vector_roles": {"vector": vectors[0]},
    "vector_skills": {"vector": vectors[1]},
    # ...
}
```

### 코드 변경 (client.py)
```python
async def post_matching_vectors(
    self,
    vectors_data: dict,
    access_token: str,
    role: str = "talent",
    job_posting_id: int = None  # ← 추가
) -> dict:
    payload = {**vectors_data, "role": role}

    # company인 경우 job_posting_id 필수
    if role == "company":
        if not job_posting_id:
            raise ValueError("job_posting_id is required for company role")
        payload["job_posting_id"] = job_posting_id
    # ...
```

### 호출부 변경
```python
# Company (company_interview_routes.py)
created_vectors = await backend_client.post_matching_vectors(
    vectors_data=matching_result["vectors"],
    access_token=request.access_token,
    role="company",
    job_posting_id=job_posting_id  # ✅ 추가
)

# Talent (interview_routes.py)
backend_response = await backend_client.post_matching_vectors(
    vectors_data=result["vectors"],
    access_token=request.access_token,
    role="talent"  # ✅ 명시
)
```

---

## 7. 벡터 409 에러 시 PATCH 업데이트 ✅

### 문제
- 409 에러 발생 시 기존 벡터를 그냥 사용
- 재면접 시 벡터가 업데이트되지 않음

### 해결
409 발생 시 자동으로 **PATCH로 업데이트**

### 수정 파일
- `ai/interview/client.py`

### 추가된 메서드

#### 1. `update_matching_vectors()` (183-222라인)
```python
async def update_matching_vectors(
    self,
    matching_vector_id: int,
    vectors_data: dict,
    access_token: str
) -> dict:
    """
    매칭 벡터 업데이트 (PATCH /api/me/matching-vectors/{matching_vector_id})
    """
    url = f"{self.backend_url}/api/me/matching-vectors/{matching_vector_id}"
    response = await client.patch(url, headers=headers, json=vectors_data)
    # ...
```

#### 2. `_get_matching_vector_id()` (224-271라인)
```python
async def _get_matching_vector_id(
    self,
    access_token: str,
    role: str,
    job_posting_id: int = None
) -> int:
    """
    사용자의 매칭 벡터 ID 조회 (내부 헬퍼 메서드)
    """
    # GET /api/me/matching-vectors로 내 벡터 목록 조회
    response = await client.get(f"{backend_url}/api/me/matching-vectors", ...)
    vectors = data.get("data", [])

    # role과 job_posting_id로 필터링
    for vector in vectors:
        if vector.get("role") == role:
            if role == "company":
                if vector.get("job_posting_id") == job_posting_id:
                    return vector.get("id")
            else:  # talent
                return vector.get("id")

    return None
```

### 전체 로직 흐름
```
1. POST /api/me/matching-vectors 시도
   ↓
2. 응답 체크
   ├─ 201 Created → ✅ 성공, 생성된 벡터 반환
   │
   └─ 409 Conflict → 이미 존재
      ↓
3. 409 응답에서 기존 벡터 ID 확인
   ├─ ID 있음 → 바로 5번으로
   │
   └─ ID 없음 → 4번 실행
      ↓
4. GET /api/me/matching-vectors 호출
   - role과 job_posting_id로 필터링
   - 기존 벡터 ID 찾기
   ↓
5. PATCH /api/me/matching-vectors/{id}
   - 새로운 벡터 데이터로 업데이트
   ↓
   ✅ 업데이트된 벡터 반환
```

### 409 처리 코드 (client.py)
```python
if response.status_code == 409:
    print(f"[INFO] Matching vector already exists. Attempting to update with PATCH...")

    # 409 응답에서 기존 벡터 ID를 받을 수 있는지 확인
    conflict_data = response.json()
    existing_vector_id = None

    # 백엔드가 기존 벡터 정보를 반환하는 경우
    if conflict_data.get("data") and conflict_data["data"].get("id"):
        existing_vector_id = conflict_data["data"]["id"]
        print(f"[INFO] Found existing vector ID from 409 response: {existing_vector_id}")
    else:
        # 벡터 ID를 찾기 위해 GET 요청
        print(f"[INFO] Getting existing vector ID from GET request...")
        existing_vector_id = await self._get_matching_vector_id(access_token, role, job_posting_id)

    if existing_vector_id:
        # PATCH로 업데이트
        return await self.update_matching_vectors(
            matching_vector_id=existing_vector_id,
            vectors_data=vectors_data,
            access_token=access_token
        )
```

### 로그 출력
```
[INFO] Matching vector already exists. Attempting to update with PATCH...
[INFO] Found existing vector ID from 409 response: 123
[INFO] Matching vector 123 updated successfully
```

또는

```
[INFO] Matching vector already exists. Attempting to update with PATCH...
[INFO] Getting existing vector ID from GET request...
[INFO] Matching vector 123 updated successfully
```

---

## 8. 백엔드 API 요청사항 정리 📝

### 신규 API 요청

#### GET /api/me/matching-vectors

**목적:** 현재 로그인한 사용자의 모든 매칭 벡터 목록 조회

**엔드포인트:**
```
GET /api/me/matching-vectors
Authorization: Bearer {access_token}
```

**응답 (Talent - 벡터 1개):**
```json
{
  "ok": true,
  "data": [
    {
      "id": 123,
      "user_id": 456,
      "role": "talent",
      "job_posting_id": null,
      "vector_roles": {"vector": [0.9, 0.8, ...]},
      "vector_skills": {"vector": [0.95, 0.9, ...]},
      "vector_growth": {"vector": [0.8, 0.7, ...]},
      "vector_career": {"vector": [0.7, 0.8, ...]},
      "vector_vision": {"vector": [0.85, 0.8, ...]},
      "vector_culture": {"vector": [0.8, 0.85, ...]},
      "updated_at": "2025-10-19T12:34:56"
    }
  ]
}
```

**응답 (Company - 벡터 여러 개):**
```json
{
  "ok": true,
  "data": [
    {
      "id": 124,
      "user_id": 457,
      "role": "company",
      "job_posting_id": 789,
      "vector_roles": {"vector": [0.85, 0.9, ...]},
      "vector_skills": {"vector": [0.9, 0.95, ...]},
      "vector_growth": {"vector": [0.9, 0.85, ...]},
      "vector_career": {"vector": [0.8, 0.85, ...]},
      "vector_vision": {"vector": [0.88, 0.82, ...]},
      "vector_culture": {"vector": [0.75, 0.8, ...]},
      "updated_at": "2025-10-19T12:35:00"
    },
    {
      "id": 125,
      "user_id": 457,
      "role": "company",
      "job_posting_id": 790,
      "vector_roles": {"vector": [0.88, 0.92, ...]},
      "vector_skills": {"vector": [0.91, 0.93, ...]},
      "vector_growth": {"vector": [0.87, 0.89, ...]},
      "vector_career": {"vector": [0.83, 0.88, ...]},
      "vector_vision": {"vector": [0.86, 0.84, ...]},
      "vector_culture": {"vector": [0.78, 0.82, ...]},
      "updated_at": "2025-10-19T13:20:00"
    }
  ]
}
```

**응답 (벡터 없음):**
```json
{
  "ok": true,
  "data": []
}
```

**비즈니스 로직:**
1. JWT에서 user_id 추출
2. DB 쿼리: `SELECT * FROM matching_vectors WHERE user_id = {user_id}`
3. 정렬: `updated_at DESC` (최신순)
4. 반환: 모든 벡터를 배열로 반환

**필수 필드:**
- `id` (int) - 매칭 벡터 ID (PK)
- `user_id` (int) - 사용자 ID
- `role` (string) - "talent" 또는 "company"
- `job_posting_id` (int|null) - 채용공고 ID (company만, talent는 null)
- `vector_roles` ~ `vector_culture` (object) - 6개 벡터 필드
- `updated_at` (string) - ISO 8601 날짜 형식

---

### 개선 요청 (선택사항)

#### 409 Conflict 응답에 기존 데이터 포함

**현재 (추측):**
```json
{
  "ok": false,
  "error": {
    "code": "MATCHING_VECTOR_EXISTS",
    "message": "Matching vector already exists"
  }
}
```

**개선 요청:**
```json
{
  "ok": false,
  "error": {
    "code": "MATCHING_VECTOR_EXISTS",
    "message": "Matching vector already exists"
  },
  "data": {
    "id": 123,
    "user_id": 456,
    "role": "company",
    "job_posting_id": 789,
    "vector_roles": {"vector": [...]},
    "vector_skills": {"vector": [...]},
    "vector_growth": {"vector": [...]},
    "vector_career": {"vector": [...]},
    "vector_vision": {"vector": [...]},
    "vector_culture": {"vector": [...]}
  }
}
```

**이유:**
- AI 서버에서 409 발생 시 PATCH로 업데이트하려면 기존 벡터 ID가 필요
- `data.id`를 포함시켜주면 **GET 요청 없이 바로 PATCH 가능** (API 호출 1회 절약)

---

## 주요 성과 요약

✅ **면접 질문 수 고정**: 8개 (5 고정 + 3 동적), 한글 전용
✅ **JD 업데이트 개선**: PATCH로 4개 필드만 수정, 메타데이터 보존
✅ **응답 안정성**: 모든 단계 에러 처리 + 부분 성공 지원 + 상세 로그
✅ **벡터 가이드 준수**: `{"vector": [...]}` + role + job_posting_id
✅ **재면접 지원**: 409 에러 시 자동 PATCH 업데이트
✅ **메타데이터 추출**: 하드코딩 제거, 3-tier 우선순위 (existing_jd → company_profile → defaults)
✅ **Location 정규화**: "서울시 마포구" → "서울"
✅ **중복 코드 제거**: 미사용 엔드포인트 삭제

---

## 수정된 파일 목록

### AI 로직
1. **ai/interview/company/technical.py**
   - 질문 8개 고정 (5 고정 + 3 동적)
   - 한글 전용 질문 생성

2. **ai/interview/company/situational.py**
   - 질문 8개 고정 (5 고정 + 3 동적)
   - 한글 전용 질문 생성

3. **ai/interview/company/jd_generator.py**
   - 메타데이터 3-tier 우선순위 추출
   - `normalize_location_city()` 함수 추가

4. **ai/matching/embedding.py**
   - 벡터 키 `embedding` → `vector` 변경

### API 라우터
5. **api/company_interview_routes.py**
   - `/job-posting` 엔드포인트 삭제
   - `/generate` 엔드포인트 PATCH 로직 추가
   - 모든 단계 에러 처리 + 로그 추가
   - 벡터 POST 시 `job_posting_id` 전달

6. **api/interview_routes.py**
   - Talent 벡터 POST 시 `role="talent"` 명시

### 백엔드 클라이언트
7. **ai/interview/client.py**
   - `update_job_posting()` 메서드 추가 (PATCH JD)
   - `update_matching_vectors()` 메서드 추가 (PATCH 벡터)
   - `_get_matching_vector_id()` 헬퍼 메서드 추가 (GET 벡터 목록)
   - `post_matching_vectors()` 메서드 개선 (409 자동 PATCH 처리)
   - `job_posting_id` 파라미터 추가

---

## 다음 단계

### 테스트 필요 사항
1. ✅ 면접 8개 질문 생성 확인
2. ✅ JD PATCH 업데이트 확인 (4개 필드만)
3. ✅ `/generate` 엔드포인트 응답 확인
4. ✅ 벡터 생성 확인 (가이드 준수)
5. ⏳ 재면접 시 벡터 PATCH 업데이트 확인 (GET API 구현 후)

### 백엔드 팀 요청사항
1. **GET /api/me/matching-vectors** API 구현
2. (선택) 409 응답에 기존 데이터 포함

---

**작성자**: AI Team
**작성일**: 2025-10-20
**버전**: 1.0.0

Situational 완료 → generate 플로우

프론트(Situational 마지막 질문 저장)

Interview.tsx에서 상황 면접 POST /api/company-interview/situational/answer 호출.
응답의 is_finished가 true면 session_id, token, 선택적 job_posting_id(URL query)로 /api/company-interview/situational/analysis 호출.
AI 서버 /situational/analysis

세션과 세 단계 완료 여부 확인.
General/Technical 답변 분석 결과 미존재 시 재계산.
반드시 job_posting_id로 기존 JD를 백엔드에서 조회(불가 시 404).
create_job_posting_from_interview가 responsibilities/requirements/competencies 네 필드 제안.
기존 JD 사본에 네 필드만 덮어쓰고 session.generated_jd에 캐싱.
프론트로 { responsibilities, requirements_must, requirements_nice, competencies, is_new:false } 반환.
프론트 화면 전환

응답 받으면 네 필드를 additionalInfo에 넣고 수정 UI 표시.
“공고 저장하기” 클릭 시

POST /api/company-interview/generate 호출(session_id, token, 동일 job_posting_id, 수정한 네 필드).
AI 서버 /generate

세션 분석 데이터 존재 확인.
session.generated_jd에서 네 필드 덮은 JD 로컬 변수 조합.
job_posting_id 필수 확인 → 없으면 400.
update_job_posting으로 기존 공고에 네 필드만 PATCH.
최신 JD 재조회 → 카드/벡터 생성용으로 사용.
create_job_posting_card_from_interview로 카드 텍스트 생성 후 /api/job_posting_cards/{id} 새로 생성(409 시 PATCH로 덮어쓰기).
generate_company_matching_vectors 결과 /api/me/matching-vectors로 POST.
응답 { success: true, job_posting_id, card, card_id, matching_vector_id, matching_texts }.
프론트 후속 처리

콘솔에 결과 출력, job_posting_id를 localStorage에 저장(lastJobPostingId).
finished 상태 true 설정 → 완료 화면.
“분석 결과 확인하기” → /assessment/result?job=<id>로 이동.
Result 페이지

job 파라미터 또는 localStorage에서 ID 확보.
/api/me/company/job-postings, /api/job_posting_cards/{id}, /api/me/company 호출.
JD 기본 메타(term_months 등)는 공고 리스트 응답에서, 카드 본문은 최신 카드 데이터 배열 마지막 요소에서 가져와 화면에 표시.