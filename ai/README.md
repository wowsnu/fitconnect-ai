# FitConnect AI Services

백엔드에서 사용할 수 있는 순수 Python AI 라이브러리

## 구조

```
ai/
├── stt/           # Speech-to-Text 서비스
├── llm/           # Large Language Model 서비스
├── embedding/     # 텍스트 임베딩 서비스 (새로 생성)
└── matching/      # 벡터 매칭 서비스 (새로 생성)
```

## 사용법

### 1. STT 서비스
```python
from ai.stt.service import get_stt_service

stt_service = get_stt_service()
# 음성 파일 → 텍스트 변환
```

### 2. LLM 서비스
```python
from ai.llm.service import get_llm_service

llm_service = get_llm_service()
# 텍스트 분석, 구조화, NER
```

### 3. 임베딩 서비스 (NEW)
```python
from ai.embedding.service import get_embedding_service

embedding_service = get_embedding_service()

# Job Vector 생성
job_vector = embedding_service.create_job_vector(
    company_info="IT기업, 스타트업, 50명, 수평적 조직문화",
    required_skills="Python, FastAPI, PostgreSQL, AWS"
)

# Applicant Vector 생성
applicant_vector = embedding_service.create_applicant_vector(
    preferences="스타트업, 원격근무, 성장 가능성",
    skills="Python 3년, Django, React, 요구분석 능력"
)
```

### 4. 매칭 서비스 (NEW)
```python
from ai.matching.service import get_matching_service

matching_service = get_matching_service()

# 단일 매칭
result = matching_service.match_single(
    job_vector=job_vector.combined_vector,
    applicant_vector=applicant_vector.combined_vector,
    job_id="job_001",
    applicant_id="applicant_001"
)

# 배치 매칭 (인재 → 여러 공고)
recommendations = matching_service.match_batch(
    job_vectors=[job1_vector, job2_vector, job3_vector],
    applicant_vector=applicant_vector.combined_vector,
    job_ids=["job_001", "job_002", "job_003"],
    applicant_id="applicant_001",
    top_n=5
)
```

## 매칭 알고리즘

`Score = α × cosine(u,v) − β × ||u−v||`

- **cosine similarity**: 역량별 가중치 반영
- **euclidean distance**: 절대적 역량 크기 반영
- **α**: 코사인 유사도 가중치 (기본값: 0.7)
- **β**: 유클리드 거리 가중치 (기본값: 0.3)

## 설치된 의존성

```bash
pip install sentence-transformers torch scikit-learn numpy
```

## 사용 가능한 임베딩 모델

- `ko-sbert`: 한국어 특화 SBERT
- `bge-m3-korean`: BGE-M3 한국어 모델
- `ko-sentence-bert`: KR-SBERT