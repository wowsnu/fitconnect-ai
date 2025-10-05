# AI 인터뷰 시스템 설계 문서

FitConnect 인재-기업 매칭 플랫폼의 AI 기반 인터뷰 시스템 설계

## 📝 요약

**총 질문 수: 20-24개**
- 구조화 면접: 5-7개 (고정)
- 직무 적합성 면접: **9개** (3개 기술 × 3단계)
- 상황 면접: 6개 (탐색 3 + 심화 2 + 검증 1)

**핵심 특징:**
- ✅ **구조화 면접 답변 분석** → 직무 면접 개인화
- ✅ **프로필 + 구조화 분석 조합** → 맞춤형 질문 생성
- ✅ **3개 기술 × 3단계** → 기술별 깊이있는 평가
- ✅ **적응형 질문 플로우** → 이전 답변 반영
- ✅ **LangChain + 클래스 기반 상태 관리** 활용

**예상 소요 시간:**
- 인터뷰: 30-40분
- LLM 처리: 2-3분

---

## 📋 목차

1. [전체 구조](#전체-구조)
2. [구조화 면접 (General)](#1-구조화-면접-general)
3. [직무 적합성 면접](#2-직무-적합성-면접)
4. [상황 면접](#3-상황-면접)
5. [기술 스택](#기술-스택)
6. [데이터 플로우](#데이터-플로우)

---

## 전체 구조

인재는 총 **3가지 유형의 인터뷰**를 진행:

```
[지원자]
   ↓
1. 구조화 면접 (General)
   → 고정 질문 5-7개
   → 답변 분석 (LLM) → 테마/관심사/업무스타일 추출
   ↓
2. 직무 적합성 면접
   → 프로필 + 구조화 면접 분석 결과 조합
   → 주요 기술 3개 선정
   → 각 기술별 3단계 질문 (기본 → 실무 → 심화)
   → 총 9개 질문, 개인화된 맞춤형 질문
   ↓
3. 상황 면접
   → AI 적응형 생성 (페르소나 분석)
   → 6개 질문 (탐색 3 + 심화 2 + 검증 1)
   ↓
[프로필 완성] → STT → LLM 분석 → 임베딩 → 매칭
```

---

## 1. 구조화 면접 (General)

### 개요
- **목적**: 기본적인 태도, 동기, 경험 파악 + 직무 면접 개인화를 위한 정보 수집
- **질문 수**: 5-7개 (고정)
- **AI 사용**:
  - 질문 제시: 없음 (단순 순차 진행)
  - 답변 분석: **있음 (직무 면접 개인화를 위한 분석)**

### 질문 예시

```python
general_questions = [
    "간단한 자기소개와 함께, 최근 6개월 동안 가장 몰입했던 경험을 이야기해 주세요.",
    "가장 의미 있었던 프로젝트나 업무 경험을 말씀해 주세요. 맡으신 역할과 결과도 함께 알려주세요.",
    "팀원들과 협업할 때 본인만의 강점은 무엇이라고 생각하시나요?",
    "일을 할 때 가장 중요하게 생각하는 가치는 무엇인가요?",
    "앞으로 어떤 커리어를 그리고 계신가요?"
]
```

### 구현 방식

```python
# 단순 순차 진행
class GeneralInterview:
    def __init__(self):
        self.questions = general_questions
        self.current_index = 0

    def get_next_question(self):
        if self.current_index < len(self.questions):
            q = self.questions[self.current_index]
            self.current_index += 1
            return q
        return None
```

### 답변 분석 (직무 면접 연동)

구조화 면접 완료 후, 모든 답변을 종합 분석하여 **직무 적합성 면접 개인화**에 활용합니다.

```python
from pydantic import BaseModel, Field
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

class GeneralInterviewAnalysis(BaseModel):
    """구조화 면접 답변 종합 분석 결과"""

    key_themes: List[str] = Field(
        description="답변에서 자주 언급된 주요 테마/키워드",
        max_items=5,
        examples=[["성능 최적화", "팀 협업", "문제 해결", "데이터 분석"]]
    )

    interests: List[str] = Field(
        description="지원자가 관심있어하는 기술 분야",
        max_items=5,
        examples=[["백엔드 아키텍처", "데이터베이스 최적화", "CI/CD 자동화"]]
    )

    work_style_hints: List[str] = Field(
        description="답변에서 드러난 업무 스타일",
        max_items=5,
        examples=[["주도적", "분석적", "협업 지향", "결과 중심"]]
    )

    emphasized_experiences: List[str] = Field(
        description="지원자가 자주 언급하거나 강조한 경험",
        max_items=5,
        examples=[["대용량 트래픽 처리", "레거시 리팩토링", "성능 개선"]]
    )

    technical_keywords: List[str] = Field(
        description="답변에서 언급된 기술 키워드",
        max_items=10,
        examples=[["Docker", "Kubernetes", "Redis", "PostgreSQL"]]
    )

def analyze_general_interview(answers: List[dict]) -> GeneralInterviewAnalysis:
    """구조화 면접 답변들을 종합 분석"""

    # 모든 Q&A를 하나의 텍스트로 결합
    all_qa = "\n\n".join([
        f"질문: {a['question']}\n답변: {a['answer']}"
        for a in answers
    ])

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 채용 전문가입니다.

        구조화 면접 답변들을 분석하여, 직무 적합성 면접을 개인화하는데 필요한 정보를 추출하세요.

        **분석 목표:**
        1. 지원자가 자주 언급하는 테마/키워드 찾기
        2. 관심있어 하는 기술 분야 파악
        3. 업무 스타일 힌트 추출
        4. 강조하는 경험 식별
        5. 언급된 기술 키워드 수집

        **중요:**
        - 실제 답변에 있는 내용만 추출
        - 추측하거나 과장하지 말 것
        - 구체적이고 명확한 키워드만
        """),
        ("user", all_qa)
    ])

    llm = ChatOpenAI(model="gpt-4o", temperature=0.3).with_structured_output(GeneralInterviewAnalysis)
    return (prompt | llm).invoke({})

# 사용 예시
general_answers = [
    {
        "question": "가장 의미 있었던 프로젝트는?",
        "answer": "FastAPI로 E-commerce API를 만들었는데, Redis 캐싱으로 응답속도를 50% 개선했어요..."
    },
    # ... 더 많은 답변
]

analysis = analyze_general_interview(general_answers)
print(analysis.key_themes)  # ["성능 최적화", "API 개발"]
print(analysis.technical_keywords)  # ["FastAPI", "Redis", "E-commerce"]
print(analysis.emphasized_experiences)  # ["응답속도 개선"]
```

**이 분석 결과는 직무 적합성 면접에서 활용됩니다:**

```
구조화 면접 답변: "Redis로 응답속도 50% 개선"
    ↓
분석 결과: emphasized_experiences = ["응답속도 개선"]
            technical_keywords = ["Redis"]
    ↓
직무 면접 질문 (개인화):
"아까 Redis로 응답속도를 50% 개선했다고 하셨는데,
 구체적으로 어떤 캐싱 전략을 사용하셨나요?"
```

---

## 2. 직무 적합성 면접

### 개요
- **목적**: 기술별 깊이있는 평가, 실무 경험 검증
- **질문 수**: **9개** (주요 기술 3개 × 3단계)
- **질문 난이도**: 각 기술당 [기본 → 실무 → 심화]
- **AI 사용**: **Few-shot + Structured Output + 클래스 기반 상태 관리**
- **개인화**: 프로필 + **구조화 면접 분석 결과** 조합

### 핵심 기술

#### 2.1 Few-shot Prompting (범용 예시 3-5개)

```python
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate

# 직무 무관 패턴 예시 (3-5개만 준비)
universal_examples = [
    {
        "profile": "기술: FastAPI 2년, 프로젝트: E-commerce API",
        "question": "[기본] FastAPI에서 비동기 처리를 사용한 경험이 있나요? 어떤 상황에서 사용했나요?"
    },
    {
        "profile": "스킬: Figma 3년, 프로젝트: 모바일 뱅킹 앱 리뉴얼",
        "question": "[실무] 모바일 뱅킹 앱 리뉴얼에서 UX 개선을 위해 어떤 디자인 결정을 내렸나요?"
    },
    {
        "profile": "경험: 퍼포먼스 마케팅 1.5년, 프로젝트: D2C 브랜드 런칭",
        "question": "[기본] D2C 브랜드 런칭 시 주요 성과 지표(KPI)는 무엇이었고, 어떻게 달성했나요?"
    }
]

example_prompt = ChatPromptTemplate.from_messages([
    ("human", "{profile}"),
    ("ai", "{question}")
])

few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=universal_examples
)
```

#### 2.2 Structured Output (질문 품질 보장)

```python
from pydantic import BaseModel, Field
from typing import Literal, List

class InterviewQuestion(BaseModel):
    question: str = Field(
        description="면접 질문 (가능한 구체적이어야 함, 그리고 프로필과 구조화 분석 내용에 있는 것을 바탕으로 질문해야함)",
        min_length=20,
        max_length=200,
        examples=["FastAPI에서 비동기 처리를 사용한 경험이 있나요?"]
    )

    level: Literal["기본", "실무", "심화"] = Field(
        description="난이도 - 기본: 개념, 실무: 경험, 심화: 최적화"
    )

    skill: str = Field(
        description="평가 대상 기술 (프로필의 skills 리스트에와 구조화 분석 내용에 있는 것만)",
        examples=["FastAPI", "PostgreSQL", "Docker"]
    )

    why: str = Field(
        description="이 질문을 하는 이유 (채용 담당자용)",
        min_length=10
    )

class Evaluation(BaseModel):
    score: int = Field(
        description="답변 점수 0-100",
        ge=0,
        le=100
    )

    reasoning: str = Field(
        description="평가 근거 (구체적으로 어떤 부분이 좋았는지/부족한지)",
        min_length=30
    )

    # 다음 질문 생성을 위한 인사이트
    key_points: List[str] = Field(
        description="답변에서 발견된 주요 포인트 (다음 질문에 활용)",
        max_items=3,
        examples=[["비동기 처리 경험 있음", "성능 최적화에 관심 많음"]]
    )

    follow_up_direction: str = Field(
        description="다음 질문이 파고들어야 할 방향",
        examples=["Redis 캐싱 전략에 대해 더 깊이 물어보기"]
    )
```

#### 2.3 개인화된 질문 생성 (프로필 + 구조화 면접 분석)

```python
from langchain_openai import ChatOpenAI

# 지원자 프로필 구조
class CandidateProfile(BaseModel):
    skills: List[str]  # ["FastAPI", "PostgreSQL", "Redis", "Docker"]
    years_of_experience: float  # 2.5
    projects: List[dict]  # [{"name": "채팅서버", "tech": ["WebSocket", "FastAPI"]}]
    job_category: str  # "Backend", "Frontend"

# 개인화된 질문 생성 함수
def generate_personalized_question(
    skill: str,
    level: Literal["기본", "실무", "심화"],
    profile: CandidateProfile,
    general_analysis: GeneralInterviewAnalysis,  # 구조화 면접 분석 결과
    previous_skill_answers: List[dict] = []  # 현재 기술의 이전 답변들
) -> InterviewQuestion:
    """프로필 + 구조화 면접 분석 + 이전 답변을 조합한 개인화 질문 생성"""

    # 프롬프트 구성
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""당신은 {profile.job_category} 기술 면접관입니다.

        **지원자 프로필:**
        - 기술 스택: {", ".join(profile.skills)}
        - 경력: {profile.years_of_experience}년
        - 프로젝트: {profile.projects}

        **구조화 면접에서 파악된 특성:**
        - 주요 테마: {", ".join(general_analysis.key_themes)}
        - 관심 분야: {", ".join(general_analysis.interests)}
        - 강조한 경험: {", ".join(general_analysis.emphasized_experiences)}
        - 업무 스타일: {", ".join(general_analysis.work_style_hints)}
        - 언급한 기술: {", ".join(general_analysis.technical_keywords)}

        **질문 생성 가이드:**
        1. 구조화 면접에서 언급한 내용을 자연스럽게 연결하세요
        2. 예: "아까 성능 최적화에 관심이 많다고 하셨는데, {{skill}}에서는..."
        3. 강조한 경험과 관련된 질문을 우선하세요
        4. [{level}] 레벨에 맞는 깊이로 질문하세요
           - 기본: 개념 이해, 기초 경험
           - 실무: 프로젝트 적용, 실전 활용
           - 심화: 최적화, 문제 해결, 설계
        """),
        ("user", f"""
        현재 평가 기술: {skill}
        난이도: [{level}]

        {"이전 답변: " + str(previous_skill_answers) if previous_skill_answers else "첫 질문입니다."}

        {skill}에 대한 [{level}] 레벨 질문 1개를 생성하세요.
        """)
    ])

    llm = ChatOpenAI(model="gpt-4o", temperature=0.7).with_structured_output(InterviewQuestion)
    return (prompt | llm).invoke({})
```

#### 2.4 클래스 기반 인터뷰 관리

```python
from typing import List, Optional
from langchain_openai import ChatOpenAI

class TechnicalInterview:
    """직무 적합성 면접 관리 클래스"""

    def __init__(self, profile: CandidateProfile, general_analysis: GeneralInterviewAnalysis):
        self.profile = profile
        self.general_analysis = general_analysis

        # 평가할 기술 3개 선택 (구조화 면접 분석 결과 반영)
        mentioned_skills = set(general_analysis.technical_keywords)
        profile_skills = profile.skills

        # 1순위: 구조화 면접에서 언급 + 프로필에 있는 기술
        priority_skills = [s for s in profile_skills if s in mentioned_skills]

        # 2순위: 프로필에만 있는 기술
        other_skills = [s for s in profile_skills if s not in mentioned_skills]

        # 합쳐서 3개 선택
        self.skills = (priority_skills + other_skills)[:3]
        self.current_skill_idx = 0
        self.current_level_idx = 0  # 0:기본, 1:실무, 2:심화

        # 결과 저장
        self.results = {skill: [] for skill in self.skills}
        self.current_question = None

    def get_next_question(self) -> Optional[dict]:
        """다음 질문 반환"""
        if self.is_finished():
            return None

        skill = self.skills[self.current_skill_idx]
        levels = ["기본", "실무", "심화"]
        level = levels[self.current_level_idx]

        # 현재 기술의 이전 답변들
        previous_answers = self.results[skill]

        # LLM으로 개인화된 질문 생성
        question = generate_personalized_question(
            skill=skill,
            level=level,
            profile=self.profile,
            general_analysis=self.general_analysis,
            previous_skill_answers=previous_answers
        )

        self.current_question = question.question

        return {
            "skill": skill,
            "level": level,
            "question": question.question,
            "why": question.why,
            "progress": f"{self.get_total_answered() + 1}/9"
        }

    async def submit_answer(self, answer: str) -> dict:
        """답변 제출 및 평가"""
        if not self.current_question:
            raise ValueError("No active question")

        skill = self.skills[self.current_skill_idx]
        level = ["기본", "실무", "심화"][self.current_level_idx]

        # LLM 평가
        eval_prompt = ChatPromptTemplate.from_messages([
            ("system", """답변을 평가하세요.

            평가 기준:
            - 기술 이해도
            - 실무 경험 깊이
            - 문제 해결 능력

            다음 질문을 위한 인사이트:
            - 답변에서 발견된 주요 포인트
            - 더 깊이 파고들 부분
            """),
            ("user", "질문: {question}\n답변: {answer}")
        ])

        llm = ChatOpenAI(model="gpt-4o").with_structured_output(Evaluation)
        evaluation = (eval_prompt | llm).invoke({
            "question": self.current_question,
            "answer": answer
        })

        # 저장
        self.results[skill].append({
            "level": level,
            "question": self.current_question,
            "answer": answer,
            "score": evaluation.score,
            "key_points": evaluation.key_points,
            "follow_up_direction": evaluation.follow_up_direction,
            "reasoning": evaluation.reasoning
        })

        # 다음 상태로 이동
        self._move_next()

        return {
            "evaluation": {
                "score": evaluation.score,
                "reasoning": evaluation.reasoning
            },
            "next_question": self.get_next_question()
        }

    def _move_next(self):
        """다음 질문으로 상태 이동"""
        self.current_level_idx += 1

        # 한 기술의 3단계 완료?
        if self.current_level_idx >= 3:
            self.current_level_idx = 0
            self.current_skill_idx += 1

        self.current_question = None

    def is_finished(self) -> bool:
        """모든 면접 완료 여부"""
        return self.current_skill_idx >= len(self.skills)

    def get_total_answered(self) -> int:
        """총 답변 개수"""
        return sum(len(answers) for answers in self.results.values())

    def get_results(self) -> dict:
        """최종 결과 반환"""
        return {
            "skills_evaluated": self.skills,
            "results": self.results,
            "total_questions": self.get_total_answered()
        }
```

**사용 예시:**

```python
# 1. 인터뷰 초기화
interview = TechnicalInterview(profile, general_analysis)
# 구조화 면접에서 언급된 기술 우선 선택
# 예: profile.skills = ["FastAPI", "PostgreSQL", "Redis", "Docker"]
#     general_analysis.technical_keywords = ["Redis", "Docker"]
#     → self.skills = ["Redis", "Docker", "FastAPI"]  # 언급된 기술 우선!

# 2. 첫 질문 받기
q1 = interview.get_next_question()
print(q1["question"])  # "아까 응답속도를 50% 개선했다고 하셨는데..."
print(q1["progress"])  # "1/9"

# 3. 답변 제출
result = await interview.submit_answer("비동기 처리와 Redis 캐싱을 조합했어요...")
print(result["evaluation"]["score"])  # 85
print(result["next_question"]["question"])  # 다음 질문

# 4. 반복
while not interview.is_finished():
    question = interview.get_next_question()
    # ... 사용자 답변 받기
    result = await interview.submit_answer(answer)

# 5. 최종 결과
final_results = interview.get_results()
```
```

### 실행 플로우

```
[구조화 면접 완료]
   ↓
답변 분석 (LLM) → 테마, 관심사, 강조 경험 추출
   ↓
┌─────────────────────────────────────┐
│ 기술 1 (FastAPI)                     │
│   ├─ [기본] 질문 (프로필 + 구조화 분석) │
│   ├─ [실무] 질문 (기본 답변 반영)      │
│   └─ [심화] 질문 (기본+실무 종합)      │
└─────────────────────────────────────┘
   ↓
┌─────────────────────────────────────┐
│ 기술 2 (PostgreSQL)                  │
│   ├─ [기본] 질문                      │
│   ├─ [실무] 질문                      │
│   └─ [심화] 질문                      │
└─────────────────────────────────────┘
   ↓
┌─────────────────────────────────────┐
│ 기술 3 (Redis)                       │
│   ├─ [기본] 질문                      │
│   ├─ [실무] 질문                      │
│   └─ [심화] 질문                      │
└─────────────────────────────────────┘
   
```

### 사용 예시

```python
# 1. 구조화 면접 분석 결과
general_analysis = GeneralInterviewAnalysis(
    key_themes=["성능 최적화", "팀 협업", "문제 해결"],
    interests=["백엔드 아키텍처", "데이터베이스"],
    emphasized_experiences=["응답속도 50% 개선", "대용량 트래픽"],
    work_style_hints=["주도적", "분석적"],
    technical_keywords=["FastAPI", "Redis", "PostgreSQL", "Docker"]
)

# 2. 프로필
profile = CandidateProfile(
    skills=["FastAPI", "PostgreSQL", "Redis", "Docker"],
    years_of_experience=2.5,
    projects=[
        {"name": "E-commerce API", "tech": ["FastAPI", "PostgreSQL"]},
        {"name": "실시간 채팅", "tech": ["FastAPI", "Redis", "WebSocket"]}
    ],
    job_category="Backend"
)

# 3. 초기 상태
initial_state = {
    "profile": profile,
    "general_analysis": general_analysis,
    "selected_skills": [],
    "all_skill_evaluations": {}
}

# 4. 실행
result = app.invoke(initial_state)

# [1회차: FastAPI 기본 질문]
print(result["current_question"])
# → "아까 응답속도를 50% 개선했다고 하셨는데,
#    FastAPI의 어떤 기능을 활용해 최적화하셨나요?"

# 답변 입력
result["answer"] = "비동기 처리와 Redis 캐싱을 조합했어요..."
result = app.invoke(result)

# [1회차: FastAPI 실무 질문]
print(result["current_question"])
# → "Redis 캐싱 전략을 말씀해주셨는데,
#    TTL은 어떻게 설정하셨나요? 캐시 무효화는 어떻게 처리했나요?"

# ... 9번 반복

# 5. 최종 결과
print(result["all_skill_evaluations"])
# {
#   "FastAPI": [
#     {"level": "기본", "score": 85, ...},
#     {"level": "실무", "score": 80, ...},
#     {"level": "심화", "score": 75, ...}
#   ],
#   "PostgreSQL": [...],
#   "Redis": [...]
# }
```

**핵심 특징:**
- ✅ **9개 질문** (3개 기술 × 3단계)
- ✅ **구조화 면접 답변 활용** (개인화)
- ✅ **이전 답변 반영** (적응형)
- ✅ **기술별 깊이있는 평가** (3단계 난이도 진행)
- ✅ **공정성** (모든 지원자 동일 질문 수)

---

## 3. 상황 면접

### 개요
- **목적**: 인성, 성향, 가치관, 팀 적합도 파악
- **질문 수**: 6개 (탐색 3 + 심화 2 + 검증 1)
- **AI 사용**: **LangGraph 적응형 + 페르소나 분류**

### 페르소나 체계 (5개 차원)

```python
from pydantic import BaseModel
from typing import Literal

class PersonaDimensions(BaseModel):
    # 1. 업무 스타일
    work_style: Literal["주도형", "협력형", "독립형"]

    # 2. 문제 해결 방식
    problem_solving: Literal["분석형", "직관형", "실행형"]

    # 3. 학습 성향
    learning: Literal["체계형", "실험형", "관찰형"]

    # 4. 스트레스 대응
    stress_response: Literal["도전형", "안정형", "휴식형"]

    # 5. 커뮤니케이션
    communication: Literal["논리형", "공감형", "간결형"]

class PersonaScores(BaseModel):
    work_style: dict[str, float]  # {"주도형": 0.7, "협력형": 0.2, ...}
    problem_solving: dict[str, float]
    learning: dict[str, float]
    stress_response: dict[str, float]
    communication: dict[str, float]
```

### 3단계 질문 전략

#### Phase 1: 탐색 (3개 질문, 현재는 그냥 예시)

```python
initial_questions = [
    {
        "question": "팀 프로젝트에서 기술적 의견 충돌이 생겼을 때, 어떻게 해결했나요?",
        "targets": ["work_style", "communication"]
    },
    {
        "question": "예상치 못한 버그가 프로덕션에서 발생했을 때, 첫 번째로 하는 행동은 무엇인가요?",
        "targets": ["problem_solving", "stress_response"]
    },
    {
        "question": "새로운 프레임워크를 1주일 안에 배워야 할 때, 어떤 방식으로 학습하나요?",
        "targets": ["learning"]
    }
]
```

#### Phase 2: 심화 (2개 질문)

```python
def get_dominant_trait(persona_scores: PersonaScores) -> str:
    """탐색 단계에서 가장 점수가 높은 성향 반환"""

    all_traits = {}

    # 5개 차원의 모든 성향 점수 수집
    for dimension, scores in persona_scores.__dict__.items():
        for trait, score in scores.items():
            all_traits[trait] = score

    # 가장 높은 점수의 성향 반환
    dominant = max(all_traits, key=all_traits.get)
    return dominant  # 예: "주도형", "분석형", "협력형" 등


def generate_deep_dive_question(dominant_trait: str, history: List[dict]):
    """가장 강한 성향에 대한 심화 질문"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""지원자가 [{dominant_trait}] 성향이 강합니다.

        이전 답변:
        {history}

        이 성향을 더 깊이 확인할 수 있는 구체적인 상황 질문을 만드세요.
        예: "팀 리더가 잘못된 결정을 했다고 생각될 때, 어떻게 행동하나요?"
        """),
        ("user", "질문을 생성하세요.")
    ])

    llm = ChatOpenAI(model="gpt-4o")
    result = (prompt | llm).invoke({})

    return result.content
```

#### Phase 3: 검증 (1개 질문) 지금은 예시

```python
validation_questions = {
    "work_style": "프로젝트 마감이 임박했을 때, 혼자 처리할지 팀과 협업할지 어떻게 결정하나요?",
    "problem_solving": "처음 보는 에러를 만났을 때, 첫 30분 동안 무엇을 하나요?",
    "learning": "시간이 부족할 때, 새로운 기술을 어떻게 학습하나요?",
    "stress_response": "중요한 기능 배포 전날, 어떤 준비를 하나요?",
    "communication": "팀원이 내 의견에 강하게 반대할 때, 어떻게 설득하나요?"
}
```

### 답변 분석 시스템

```python
class AnswerAnalysis(BaseModel):
    detected_traits: dict[str, dict[str, float]]
    # 예: {"work_style": {"주도형": 0.8, "협력형": 0.2}}
    reasoning: str
    unclear_dimension: str  # "stress_response"

def analyze_situational_answer(question: str, answer: str, targets: List[str]):
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 산업심리학 전문가입니다.

        **분석 기준:**

        1. work_style (업무 스타일):
           - 주도형: "내가 제안", "리드", "결정"
           - 협력형: "함께", "논의", "의견 수렴"
           - 독립형: "혼자", "스스로", "자율적"

        2. problem_solving (문제 해결):
           - 분석형: "원인 분석", "데이터", "체계적"
           - 직관형: "직감", "경험상", "빠르게"
           - 실행형: "일단 시도", "테스트", "실험"

        3. learning (학습):
           - 체계형: "문서", "강의", "순서대로"
           - 실험형: "직접 만들어보며", "프로젝트"
           - 관찰형: "코드 분석", "다른 사람"

        4. stress_response (스트레스):
           - 도전형: "기회", "성장", "재미"
           - 안정형: "계획", "준비", "체크리스트"
           - 회피형: "힘들었다", "도움 요청"

        5. communication (커뮤니케이션):
           - 논리형: "근거", "데이터", "객관적"
           - 공감형: "이해", "감정", "입장"
           - 간결형: "명확하게", "핵심만"
        """),
        ("user", """
        질문: {question}
        답변: {answer}
        측정 대상: {targets}

        답변을 분석해 각 차원별 점수(0-1)를 반환하세요.
        """)
    ])

    llm = ChatOpenAI(model="gpt-4o").with_structured_output(AnswerAnalysis)
    return (prompt | llm).invoke({
        "question": question,
        "answer": answer,
        "targets": ", ".join(targets)
    })
```

### LangGraph 플로우

```python
class SituationInterviewState(TypedDict):
    phase: Literal["exploration", "deep_dive", "validation"]
    question_count: int
    current_question: dict
    answer: str
    persona_scores: PersonaScores
    qa_history: List[dict]
    unclear_dimensions: List[str]

# 노드 1: 초기 질문
def start_exploration(state):
    first_q = initial_questions[0]
    return {
        **state,
        "phase": "exploration",
        "current_question": first_q,
        "question_count": 1
    }

# 노드 2: 답변 분석
def analyze_answer(state):
    q = state["current_question"]
    answer = state["answer"]

    analysis = analyze_situational_answer(
        question=q["question"],
        answer=answer,
        target_dimensions=q["targets"]
    )

    # 점수 누적
    current_scores = state["persona_scores"]
    for dimension, scores in analysis.detected_traits.items():
        for trait, score in scores.items():
            current_scores.__dict__[dimension][trait] = \
                current_scores.__dict__[dimension].get(trait, 0) + score

    return {
        **state,
        "persona_scores": current_scores,
        "qa_history": state["qa_history"] + [{
            "question": q["question"],
            "answer": answer,
            "analysis": analysis.reasoning
        }]
    }

# 노드 3: 다음 질문 결정
def decide_next_question(state):
    count = state["question_count"]

    # Phase 1: 탐색 (3개)
    if count < 3:
        next_q = initial_questions[count]
        return {**state, "current_question": next_q, "question_count": count + 1}

    # Phase 2: 심화 (2개)
    elif count < 5:
        top_trait = get_dominant_trait(state["persona_scores"])
        deep_q = generate_deep_dive_question(top_trait, state["qa_history"])
        return {**state, "current_question": deep_q, "question_count": count + 1, "phase": "deep_dive"}

    # Phase 3: 검증 (1개)
    elif count < 6:
        if state["unclear_dimensions"]:
            unclear_dim = state["unclear_dimensions"][0]
            validation_q = {"question": validation_questions[unclear_dim], "targets": [unclear_dim]}
            return {**state, "current_question": validation_q, "question_count": count + 1, "phase": "validation"}

    return state

# 그래프 구성
workflow = StateGraph(SituationInterviewState)
workflow.add_node("start", start_exploration)
workflow.add_node("analyze", analyze_answer)
workflow.add_node("next_question", decide_next_question)

workflow.set_entry_point("start")
workflow.add_edge("start", "analyze")
workflow.add_edge("analyze", "next_question")
workflow.add_conditional_edges(
    "next_question",
    lambda s: "end" if s["question_count"] >= 6 else "continue",
    {"continue": "analyze", "end": END}
)

app = workflow.compile()
```

### 최종 리포트 생성

```python
class FinalPersonaReport(BaseModel):
    work_style: str
    problem_solving: str
    learning: str
    stress_response: str
    communication: str
    confidence: float  # 0-1
    summary: str  # "협력적이며 논리적인 분석가형"
    team_fit: str  # "애자일 환경, 기술 토론 활발한 팀"

def generate_final_report(state: SituationInterviewState):
    scores = state["persona_scores"]

    # 각 차원별 최고 점수 선택
    final_persona = {
        dimension: max(traits, key=traits.get)
        for dimension, traits in scores.__dict__.items()
    }

    prompt = ChatPromptTemplate.from_messages([
        ("system", "인터뷰 결과를 요약하고 팀 적합도를 분석하세요."),
        ("user", """
        성향 분석 결과:
        - 업무 스타일: {work_style}
        - 문제 해결: {problem_solving}
        - 학습: {learning}
        - 스트레스: {stress_response}
        - 커뮤니케이션: {communication}

        인터뷰 내용: {history}

        요약과 추천 팀 환경을 작성하세요.
        """)
    ])

    llm = ChatOpenAI(model="gpt-4o").with_structured_output(FinalPersonaReport)
    return (prompt | llm).invoke({**final_persona, "history": state["qa_history"]})
```

---

## 기술 스택

### 필수 패키지

```bash
pip install langchain langchain-openai langgraph pydantic
```

### 환경 변수

```bash
OPENAI_API_KEY=your-api-key
```

### 모델 선택

- **질문 생성**: `gpt-4o` (temperature=0.7)
- **답변 분석**: `gpt-4o` (temperature=0.3)
- **Structured Output**: `with_structured_output()` 사용

---

## 데이터 플로우

```
[지원자 입력]
    ↓
┌──────────────────────────────────────────────────┐
│ 1. 구조화 면접 (General)                          │
│    - 고정 질문 5-7개                              │
│    - 순차 진행 (답변 녹음 → STT)                  │
└──────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────┐
│ 구조화 면접 답변 분석 (LLM)                        │
│    - 주요 테마/키워드 추출                         │
│    - 관심 분야 파악                                │
│    - 강조한 경험 식별                              │
│    - 업무 스타일 힌트 추출                         │
│    → GeneralInterviewAnalysis 생성                │
└──────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────┐
│ 2. 직무 적합성 면접 (Technical)                    │
│    - 프로필 + 구조화 분석 결과 조합                 │
│    - 주요 기술 3개 선정                            │
│                                                   │
│    [기술 1 - FastAPI]                             │
│      ├─ [기본] 개인화 질문 (프로필+구조화 분석)     │
│      ├─ [실무] 질문 (기본 답변 반영)               │
│      └─ [심화] 질문 (기본+실무 종합)               │
│                                                   │
│    [기술 2 - PostgreSQL]                          │
│      ├─ [기본] 질문                                │
│      ├─ [실무] 질문                                │
│      └─ [심화] 질문                                │
│                                                   │
│    [기술 3 - Redis]                               │
│      ├─ [기본] 질문                                │
│      ├─ [실무] 질문                                │
│      └─ [심화] 질문                                │
│                                                   │
│    → 총 9개 질문, 각 답변 평가 저장                │
└──────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────┐
│ 3. 상황 면접 (Situational)                        │
│    - 탐색 (3) → 심화 (2) → 검증 (1)               │
│    - 페르소나 5개 차원 점수 누적                    │
│    - 최종 리포트 생성                              │
└──────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────┐
│ 통합 프로필 생성                                   │
│    - 기술별 평가 데이터 (FastAPI: 85,80,75 등)     │
│    - 페르소나 (협력형, 분석형, 도전형)             │
│    - 구조화 면접 인사이트                          │
│    - 임베딩 벡터 생성 준비                         │
└──────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────┐
│ STT → LLM 최종 분석 → 임베딩                       │
└──────────────────────────────────────────────────┘
    ↓
[매칭 시스템]
```

---

## 구현 순서 (권장)

1. **구조화 면접** (1-2일)
   - 고정 질문 DB 구축 (5-7개)
   - 순차 API 구현
   - **답변 분석 LLM 프롬프트 작성**
   - GeneralInterviewAnalysis 스키마 구현

2. **직무 적합성 면접** (3-4일)
   - Few-shot 예시 작성 (직무 무관 3-5개)
   - Structured Output 스키마 (InterviewQuestion, Evaluation)
   - **개인화 질문 생성 함수 구현** (프로필 + 구조화 분석 활용)
   - **클래스 기반 인터뷰 관리 구현**
     - TechnicalInterview 클래스 구현
     - 질문 생성 메서드
     - 답변 평가 로직
     - 상태 관리 및 진행 제어
   - 프로필 연동 및 전체 플로우 테스트

3. **상황 면접** (4-5일)
   - 페르소나 체계 설계
   - 초기 질문 작성 (3개)
   - 답변 분석 프롬프트
   - LangGraph 적응형 플로우
   - 최종 리포트 생성

4. **통합 테스트** (2일)
   - 전체 플로우 연결
   - STT 연동
   - 임베딩 파이프라인

---

## 참고 사항

- **토큰 비용**:
  - 구조화 면접 분석: ~1,000 토큰
  - 직무 적합성 면접 (9개 질문): ~8,000-12,000 토큰
  - 상황 면접 (6개 질문): ~5,000-8,000 토큰
  - **총 1회당: 약 15,000-20,000 토큰**
- **응답 시간**:
  - 질문 생성: 2-3초
  - 답변 분석: 3-5초
  - 구조화 면접 분석: 5-7초
- **에러 처리**: LLM 실패 시 fallback 질문 준비 필수
- **프라이버시**: 인터뷰 데이터 암호화 저장
- **확장성**: 평가 기술 개수 조정 가능 (3개 → 2개 or 4개)

---

## 다음 단계

### 구현
- [ ] 구조화 면접 고정 질문 5-7개 확정
- [ ] GeneralInterviewAnalysis 분석 프롬프트 작성 및 테스트
- [ ] Few-shot 예시 작성 (직무 무관 3-5개)
- [ ] 개인화 질문 생성 프롬프트 구현
- [ ] LangGraph 3×3 플로우 구현
- [ ] 상황면접 초기 질문 3개 확정
- [ ] 페르소나 분류 기준 세부 조정

### 연동
- [ ] 프로필 스키마 DB 설계
- [ ] 프로필 DB와 연동
- [ ] STT 서비스와 통합 테스트
- [ ] 임베딩 파이프라인 연결

### 최적화
- [ ] 토큰 비용 최적화 (프롬프트 압축)
- [ ] 캐싱 전략 (Few-shot 예시, 프로필 정보)
- [ ] 에러 핸들링 및 fallback 로직
