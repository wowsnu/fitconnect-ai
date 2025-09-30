# FitConnect AI Services API 명세서

백엔드 개발자를 위한 AI 서비스 사용 가이드

## 개요

AI 서비스들은 순수 Python 라이브러리로 제공됩니다. HTTP API가 아닌 직접 import하여 사용합니다.

**⚠️ 중요**: `ai_service.py` 파일은 제거되었습니다. 독립적인 AI 서비스가 아닌 백엔드 내장 라이브러리로 사용합니다.

## 1. STT (Speech-to-Text) 서비스

### Import
```python
from ai.stt.service import get_stt_service
```

### 주요 함수

#### `transcribe_file(file_path, language="ko")`
**설명**: 파일 경로로 음성 파일 전사
**입력**:
- `file_path` (str): 오디오 파일 경로
- `language` (str, optional): 언어 코드 ("ko", "en", "auto")

**출력**: `(text, metadata)` 튜플
- `text` (str): 전사된 텍스트
- `metadata` (dict): 메타데이터
  - `language` (str): 감지된 언어
  - `duration` (float): 음성 길이(초)
  - `segments_count` (int): 세그먼트 수
  - `confidence` (float): 신뢰도 점수

**예시**:
```python
stt_service = get_stt_service()
text, metadata = stt_service.transcribe_file("interview.wav", "ko")
print(f"전사 결과: {text}")
print(f"신뢰도: {metadata['confidence']}")
```

#### `transcribe_bytes(audio_data, filename, language="ko")`
**설명**: 바이트 데이터로 음성 전사 (파일 업로드 처리용)
**입력**:
- `audio_data` (bytes): 오디오 파일 바이트 데이터
- `filename` (str): 원본 파일명 (확장자 확인용)
- `language` (str, optional): 언어 코드

**출력**: `(text, metadata)` 튜플

**예시**:
```python
# FastAPI 파일 업로드 처리
async def upload_audio(audio_file: UploadFile):
    audio_data = await audio_file.read()
    stt_service = get_stt_service()
    text, metadata = stt_service.transcribe_bytes(
        audio_data,
        audio_file.filename,
        "ko"
    )
    return {"text": text, "metadata": metadata}
```

#### 지원 포맷
`.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`, `.webm`

---

## 2. LLM (Large Language Model) 서비스

### Import
```python
from ai.llm.service import get_llm_service
```

### 주요 함수

#### `generate_completion(messages, provider="openai", model=None, temperature=0.7, max_tokens=1000)`
**설명**: 텍스트 생성/완성
**입력**:
- `messages` (list): 대화 메시지 리스트
- `provider` (str): LLM 제공자 ("openai", "anthropic")
- `model` (str, optional): 모델명
- `temperature` (float): 창의성 (0.0~2.0)
- `max_tokens` (int): 최대 토큰 수

**출력**: `CompletionResponse` 객체
- `content` (str): 생성된 텍스트
- `model` (str): 사용된 모델
- `usage` (dict): 토큰 사용량

**예시**:
```python
llm_service = get_llm_service()
messages = [
    {"role": "system", "content": "당신은 채용 전문가입니다."},
    {"role": "user", "content": "이 자기소개서를 분석해주세요: ..."}
]
response = await llm_service.generate_completion(messages)
print(response.content)
```

#### `analyze_candidate_profile(profile_text)`
**설명**: 지원자 프로필 분석 및 핵심 역량 추출
**입력**:
- `profile_text` (str): 자기소개서, 이력서 텍스트

**출력**: 분석 결과 딕셔너리
- `technical_skills` (list): 기술 스킬
- `soft_skills` (list): 소프트 스킬
- `experience_level` (str): 경력 수준
- `strengths` (list): 강점
- `areas_for_improvement` (list): 개선 영역

**예시**:
```python
llm_service = get_llm_service()
analysis = await llm_service.analyze_candidate_profile(
    "저는 3년간 Python 개발을 해왔으며..."
)
print(f"기술스킬: {analysis['technical_skills']}")
```

#### `analyze_job_posting(job_posting_text)`
**설명**: 채용공고 분석 및 요구사항 추출
**입력**:
- `job_posting_text` (str): 채용공고 텍스트

**출력**: 분석 결과 딕셔너리
- `required_skills` (list): 필수 스킬
- `preferred_skills` (list): 우대 스킬
- `experience_requirements` (str): 경력 요구사항
- `education_requirements` (str): 학력 요구사항

---

## 3. Embedding 서비스

### Import
```python
from ai.embedding.service import get_embedding_service
```

### 주요 함수

#### `get_embedding(text, model_name="ko-sbert")`
**설명**: 텍스트를 벡터로 변환
**입력**:
- `text` (str): 임베딩할 텍스트
- `model_name` (str): 모델명 ("ko-sbert", "bge-m3-korean", "ko-sentence-bert")

**출력**: `numpy.ndarray` - 임베딩 벡터

#### `create_job_vector(company_info, required_skills, model_name="ko-sbert")`
**설명**: 채용공고 벡터 생성
**입력**:
- `company_info` (str): 회사 및 공고 일반 정보
- `required_skills` (str): 요구 역량 및 스킬
- `model_name` (str): 임베딩 모델

**출력**: `VectorResult` 객체
- `general_vector` (list): 일반 정보 벡터
- `skills_vector` (list): 스킬 벡터
- `combined_vector` (list): 결합 벡터
- `model` (str): 사용된 모델
- `dimension` (int): 벡터 차원

**예시**:
```python
embedding_service = get_embedding_service()
job_vector = embedding_service.create_job_vector(
    company_info="IT 스타트업, 50명 규모, 수평적 조직문화, 원격근무 가능",
    required_skills="Python, FastAPI, PostgreSQL, AWS, 3년 이상 경력"
)
```

#### `create_applicant_vector(preferences, skills, model_name="ko-sbert")`
**설명**: 지원자 벡터 생성
**입력**:
- `preferences` (str): 선호 회사/공고 정보
- `skills` (str): 보유 역량 및 스킬
- `model_name` (str): 임베딩 모델

**출력**: `VectorResult` 객체

**예시**:
```python
applicant_vector = embedding_service.create_applicant_vector(
    preferences="스타트업 선호, 원격근무 희망, 성장 가능성 중시",
    skills="Python 5년, Django, React, 팀 리딩 경험, 요구분석 능력"
)
```

---

## 4. Matching 서비스

### Import
```python
from ai.matching.service import get_matching_service
```

### 주요 함수

#### `match_single(job_vector, applicant_vector, job_id, applicant_id, alpha=0.7, beta=0.3)`
**설명**: 단일 매칭 점수 계산
**입력**:
- `job_vector` (list): 채용공고 벡터
- `applicant_vector` (list): 지원자 벡터
- `job_id` (str): 공고 ID
- `applicant_id` (str): 지원자 ID
- `alpha` (float): 코사인 유사도 가중치
- `beta` (float): 유클리드 거리 가중치

**출력**: `MatchingResult` 객체
- `score` (float): 최종 매칭 점수
- `cosine_similarity` (float): 코사인 유사도
- `euclidean_distance` (float): 유클리드 거리
- `rank` (int): 순위

**매칭 공식**: `Score = α × cosine(u,v) − β × ||u−v||`

#### `match_batch(job_vectors, applicant_vector, job_ids, applicant_id, top_n=10)`
**설명**: 지원자 한 명을 여러 공고와 매칭
**입력**:
- `job_vectors` (list): 채용공고 벡터 리스트
- `applicant_vector` (list): 지원자 벡터
- `job_ids` (list): 공고 ID 리스트
- `applicant_id` (str): 지원자 ID
- `top_n` (int): 상위 N개 추천

**출력**: `RecommendationResult` 객체
- `matches` (list): 매칭 결과 리스트 (점수 순 정렬)
- `total_candidates` (int): 전체 후보 수

**예시**:
```python
matching_service = get_matching_service()

# 단일 매칭
result = matching_service.match_single(
    job_vector=job_vector.combined_vector,
    applicant_vector=applicant_vector.combined_vector,
    job_id="job_001",
    applicant_id="applicant_001"
)
print(f"매칭 점수: {result.score:.3f}")

# 배치 매칭 (추천)
recommendations = matching_service.match_batch(
    job_vectors=[job1.combined_vector, job2.combined_vector, job3.combined_vector],
    applicant_vector=applicant_vector.combined_vector,
    job_ids=["job_001", "job_002", "job_003"],
    applicant_id="applicant_001",
    top_n=5
)

for match in recommendations.matches:
    print(f"공고 {match.job_id}: {match.score:.3f}점")
```

---

## 전체 워크플로우 예시

```python
# 1. 음성 면접 데이터 처리
from ai.stt.service import get_stt_service
from ai.llm.service import get_llm_service
from ai.embedding.service import get_embedding_service
from ai.matching.service import get_matching_service

# STT: 음성 → 텍스트
stt_service = get_stt_service()
interview_text, _ = stt_service.transcribe_file("interview.wav")

# LLM: 텍스트 분석
llm_service = get_llm_service()
candidate_analysis = await llm_service.analyze_candidate_profile(interview_text)
job_analysis = await llm_service.analyze_job_posting(job_posting_text)

# Embedding: 벡터 생성
embedding_service = get_embedding_service()
candidate_vector = embedding_service.create_applicant_vector(
    preferences=candidate_analysis['preferences'],
    skills=candidate_analysis['technical_skills'] + candidate_analysis['soft_skills']
)

job_vector = embedding_service.create_job_vector(
    company_info=job_analysis['company_info'],
    required_skills=job_analysis['required_skills']
)

# Matching: 매칭 점수 계산
matching_service = get_matching_service()
match_result = matching_service.match_single(
    job_vector=job_vector.combined_vector,
    applicant_vector=candidate_vector.combined_vector,
    job_id="job_001",
    applicant_id="candidate_001"
)

print(f"최종 매칭 점수: {match_result.score:.3f}")
```

## 에러 처리

모든 함수는 예외를 발생시킬 수 있으므로 try-catch로 처리하세요:

```python
try:
    result = stt_service.transcribe_file("audio.wav")
except FileNotFoundError:
    # 파일이 없는 경우
except ValueError:
    # 지원하지 않는 포맷
except RuntimeError:
    # 전사 실패
```

## 의존성

```bash
pip install sentence-transformers torch scikit-learn numpy whisper openai anthropic
```