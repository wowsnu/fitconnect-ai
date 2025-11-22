# Multi-Agent Debate 방식 설계 문서

## 📋 목차
1. [개요](#개요)
2. [핵심 아이디어](#핵심-아이디어)
3. [구현 단계](#구현-단계)
4. [장점 분석](#장점-분석)
5. [실제 사용 예시](#실제-사용-예시)
6. [구현 코드](#구현-코드)

---

## 개요

**목적**: 단일 세션에서 여러 팀원의 답변을 수집하고, 이를 기술적으로 종합하여 채용 공고를 생성

**배경**:
- 각 팀원이 동일한 질문에 개별적으로 답변
- 팀장, 개발자A, 개발자B 등 여러 관점을 하나로 종합 필요
- 백엔드 복잡도를 낮추기 위해 단일 세션 사용

---

## 핵심 아이디어

각 팀원의 답변을 **독립적인 관점(perspective)**으로 보고, LLM이 이 관점들을 **토론하듯 종합**하는 방식

```
팀장 관점 ──┐
개발자A 관점 ──┤──→ [중재자 LLM] ──→ 종합된 분석
개발자B 관점 ──┘
```

---

## 구현 단계

### Step 1: 각 팀원의 답변을 "관점(Perspective)" 으로 구조화

```python
def build_perspective(member_name: str, answer: str, question: str) -> str:
    """
    각 팀원의 답변을 하나의 '관점'으로 재구성
    """
    return f"""
[{member_name}의 관점]
질문: {question}
답변: {answer}

이 답변에서 읽을 수 있는 것:
- 핵심 키워드: [LLM이 추출할 영역]
- 강조하는 가치: [LLM이 추출할 영역]
- 우선순위: [LLM이 추출할 영역]
"""
```

### Step 2: 중재자 프롬프트 설계 (핵심!)

#### 프롬프트 구조

```
당신은 **중재자(Moderator)**입니다.

여러 팀원들이 같은 질문에 대해 각자의 관점에서 답변했습니다.
당신의 역할은 이 답변들을 **공정하게 종합**하여 하나의 일관된 분석을 만드는 것입니다.
```

#### 종합 원칙

1. **공통 합의 우선**: 2명 이상이 언급한 내용은 핵심으로 간주
2. **소수 의견 존중**: 1명만 언급했어도 중요하다면 "일부 의견" 형태로 포함
3. **상충 시 조정**: 의견이 충돌하면 양측을 모두 언급하고 균형점 제시
4. **직급/역할 고려**: 질문 성격에 따라 특정 관점에 더 큰 비중 부여
   - 문화/가치 질문 → 팀장/리더 의견 중시
   - 기술/실무 질문 → 실무자 의견 중시
   - 협업/팀워크 질문 → 모든 의견 균등

#### 출력 형식

```
1. 공통 합의 사항 (Consensus)
   - 모든 팀원이 동의하거나 2명 이상이 언급한 내용
   - 예: "팀원 전체가 '혁신'을 핵심 가치로 강조함"

2. 다수 의견 (Majority View)
   - 2명 이상이 언급했지만 전체 합의는 아닌 내용
   - 예: "팀장과 개발자A는 '빠른 실행력'을 중시"

3. 소수 의견 (Minority View)
   - 1명만 언급했지만 중요한 인사이트
   - 예: "개발자B는 '기술 부채 해결'도 중요하다고 언급"

4. 상충 의견 (Conflicts)
   - 서로 모순되거나 다른 방향을 제시하는 내용
   - 예:
     * 팀장: "공격적 성장"
     * 개발자: "안정적 운영"
     * → 조정: "성장과 안정의 균형 추구"

5. 최종 종합 (Final Synthesis)
   - 위 내용을 바탕으로 **하나의 일관된 답변** 생성
   - 모든 관점을 반영하되 우선순위를 명확히
   - 이 답변은 단일 응답자가 답한 것처럼 자연스러워야 함
```

#### 예시

**질문**: "회사의 핵심 가치는 무엇인가요?"

**팀원 답변**:
- 팀장: "혁신과 도전을 중시합니다. 실패를 두려워하지 않는 문화죠."
- 개발자A: "협업과 투명성이 중요해요. 모든 결정은 공개적으로 논의됩니다."
- 개발자B: "기술 우수성을 추구합니다. 최신 기술을 적극 도입하려 노력해요."

**종합 결과**:

```
1. 공통 합의
   - 혁신/기술 우수성: 팀장의 "혁신", 개발자B의 "기술 우수성" → 기술 혁신 지향

2. 다수 의견
   - 없음 (모든 의견이 고유함)

3. 소수 의견
   - 협업/투명성 (개발자A만 언급, 하지만 조직문화에 중요)
   - 도전 정신 (팀장만 언급)

4. 상충 의견
   - 없음 (모두 보완적 관계)

5. 최종 종합
   "우리 회사는 **기술 혁신**을 핵심 가치로 삼습니다. 최신 기술 도입을 통한 도전을
   두려워하지 않으며, 이 과정에서 **투명한 협업**을 중시합니다. 실패를 성장의 기회로
   보며, 모든 의사결정은 팀 내 공개적으로 논의됩니다."

   → 핵심 키워드: ["기술 혁신", "도전 정신", "투명한 협업", "실패 허용"]
   → 우선순위: 1) 기술 혁신 (2명 언급), 2) 협업/투명성, 3) 도전 정신
```

### Step 3: 데이터 구조

#### 세션 시작 시
```json
{
    "access_token": "...",
    "num_members": 3,
    "members": ["김팀장", "박개발", "이개발"]
}
```

#### 답변 수집
```json
{
    "session_id": "...",
    "member_name": "김팀장",
    "answer": "혁신과 도전을 중시합니다"
}
```

#### 내부 저장 구조
```python
{
    "question": "회사의 핵심 가치는?",
    "responses": [
        {"member": "김팀장", "answer": "혁신과 도전을 중시합니다"},
        {"member": "박개발", "answer": "협업이 가장 중요합니다"},
        {"member": "이개발", "answer": "기술 우수성을 추구합니다"}
    ]
}
```

---

## 장점 분석

### ✅ 맥락 보존

```
팀장: "우리는 빠른 실행을 중시합니다"
개발자: "하지만 코드 품질도 놓칠 수 없어요"

→ 종합: "빠른 실행력을 중시하되, 코드 품질을 유지하는 균형 추구"
```

### ✅ 상충 의견 처리

```
팀장: "공격적 성장"
개발자: "안정적 운영"

→ Conflicts에 명시 + 조정안 제시
→ 공고에 "성장과 안정의 균형" 같은 표현 반영
```

### ✅ 소수 의견 보존

```
2명: "협업 중시"
1명: "개인 성과도 중요"

→ "협업 중심이지만, 개인의 기여도 인정하는 문화"
```

### ✅ 직급별 가중치 적용

```
문화/가치 질문 → 팀장 의견에 더 큰 비중
기술/실무 질문 → 실무 개발자 의견에 더 큰 비중
협업 질문 → 모든 의견 균등
```

---

## 실제 사용 예시

### API 플로우

```
1. POST /company-interview/general/start
   {
       "access_token": "...",
       "num_members": 3,
       "members": ["김팀장", "박개발", "이개발"]
   }
   → session_id, 첫 질문 반환

2. POST /company-interview/general/answer (3번 호출)
   {
       "session_id": "...",
       "member_name": "김팀장",
       "answer": "..."
   }
   → 3명 모두 답변하면 자동으로 다음 질문으로 이동

3. GET /company-interview/general/analysis/{session_id}
   → Multi-Perspective Synthesis 수행 후 CompanyGeneralAnalysis 반환
```

### 분석 처리 흐름

```
종합 단계 1: Multi-Perspective Synthesis (각 질문별)
→ consensus: ["혁신 지향"]
→ majority_view: []
→ minority_view: ["협업 중시", "도전 정신", "기술 우수성"]
→ conflicts: []
→ final_synthesis: "기술 혁신을 추구하며, 협업을 통한 도전을 중시하는 문화"

종합 단계 2: CompanyGeneralAnalysis (전체 질문 종합)
→ core_values: ["기술 혁신", "협업", "도전 정신"]
→ ideal_candidate_traits: ["기술 전문성", "협업 능력", "도전 정신"]
→ team_culture: "기술 혁신을 추구하며 투명한 협업을 중시하는 문화"
→ work_style: "빠른 실행과 품질의 균형을 추구"
→ hiring_reason: "팀 확장 및 신규 프로젝트 추진"
```

---

## 구현 코드

### 1. Pydantic 모델

```python
from pydantic import BaseModel, Field
from typing import List, Dict

class PerspectiveSynthesis(BaseModel):
    """관점 종합 결과"""
    consensus: List[str] = Field(description="공통 합의 사항")
    majority_view: List[str] = Field(description="다수 의견")
    minority_view: List[str] = Field(description="소수 의견")
    conflicts: List[Dict[str, str]] = Field(
        description="상충 의견 목록 [{'issue': '...', 'perspectives': '...', 'resolution': '...'}]"
    )
    final_synthesis: str = Field(description="최종 종합 답변")
    extracted_keywords: List[str] = Field(description="추출된 핵심 키워드")
    priority_order: List[str] = Field(description="우선순위 순서")
```

### 2. CompanyGeneralInterview 클래스 수정

```python
class CompanyGeneralInterview:
    """기업 General 면접 관리 클래스 (다중 팀원 지원)"""

    def __init__(
        self,
        questions: Optional[List[str]] = None,
        num_members: int = 1,
        member_names: Optional[List[str]] = None
    ):
        """
        Args:
            questions: 커스텀 질문 리스트 (없으면 기본 질문 사용)
            num_members: 참여 팀원 수
            member_names: 팀원 이름 리스트
        """
        self.questions = questions or COMPANY_GENERAL_QUESTIONS
        self.num_members = num_members
        self.member_names = member_names or [f"팀원{i+1}" for i in range(num_members)]
        self.current_index = 0
        self.answers = [
            {
                "question": q,
                "responses": []  # num_members 만큼 채워질 배열
            }
            for q in self.questions
        ]

    def get_next_question(self) -> Optional[str]:
        """다음 질문 반환"""
        if self.current_index < len(self.questions):
            return self.questions[self.current_index]
        return None

    def submit_answer(self, answer: str, member_name: str) -> dict:
        """
        답변 제출

        Args:
            answer: 답변 텍스트
            member_name: 답변자 이름

        Returns:
            제출 결과 (다음 질문 또는 완료 상태)
        """
        if self.current_index >= len(self.questions):
            raise ValueError("모든 질문이 완료되었습니다.")

        current_q = self.answers[self.current_index]

        # 답변 추가
        current_q["responses"].append({
            "member": member_name,
            "answer": answer
        })

        # 모든 팀원이 답변했는지 확인
        all_answered = len(current_q["responses"]) >= self.num_members

        if all_answered:
            # 다음 질문으로 이동
            self.current_index += 1
            next_q = self.get_next_question()
        else:
            # 같은 질문 유지 (다른 팀원 대기)
            next_q = current_q["question"]

        return {
            "submitted": True,
            "question_number": self.current_index if all_answered else self.current_index + 1,
            "total_questions": len(self.questions),
            "next_question": next_q,
            "waiting_for": self.num_members - len(current_q["responses"]) if not all_answered else 0
        }

    def is_finished(self) -> bool:
        """모든 질문 완료 여부"""
        return self.current_index >= len(self.questions)

    def get_answers(self) -> List[dict]:
        """모든 Q&A 반환"""
        return self.answers
```

### 3. 질문 유형 분류

```python
def classify_question_type(question: str) -> str:
    """
    질문 유형 자동 분류 (간단한 키워드 기반)

    Returns:
        "cultural" | "technical" | "general"
    """
    question_lower = question.lower()

    if any(kw in question_lower for kw in ["문화", "가치", "비전", "미션"]):
        return "cultural"
    elif any(kw in question_lower for kw in ["기술", "역량", "스택", "경험", "프로젝트"]):
        return "technical"
    else:
        return "general"
```

### 4. Multi-Perspective Synthesis 함수

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

DEBATE_SYNTHESIS_PROMPT = """당신은 **중재자(Moderator)**입니다.

여러 팀원들이 같은 질문에 대해 각자의 관점에서 답변했습니다.
당신의 역할은 이 답변들을 **공정하게 종합**하여 하나의 일관된 분석을 만드는 것입니다.

---

## 종합 원칙

1. **공통 합의 우선**: 2명 이상이 언급한 내용은 핵심으로 간주
2. **소수 의견 존중**: 1명만 언급했어도 중요하다면 "일부 의견" 형태로 포함
3. **상충 시 조정**: 의견이 충돌하면 양측을 모두 언급하고 균형점 제시
4. **직급/역할 고려**: 질문 성격에 따라 특정 관점에 더 큰 비중 부여
   - 문화/가치 질문 → 팀장/리더 의견 중시
   - 기술/실무 질문 → 실무자 의견 중시
   - 협업/팀워크 질문 → 모든 의견 균등

---

## 출력 형식

당신은 아래 형식으로 종합해야 합니다:

### 1. 공통 합의 사항 (Consensus)
- 모든 팀원이 동의하거나 2명 이상이 언급한 내용
- 예: "팀원 전체가 '혁신'을 핵심 가치로 강조함"

### 2. 다수 의견 (Majority View)
- 2명 이상이 언급했지만 전체 합의는 아닌 내용
- 예: "팀장과 개발자A는 '빠른 실행력'을 중시"

### 3. 소수 의견 (Minority View)
- 1명만 언급했지만 중요한 인사이트
- 예: "개발자B는 '기술 부채 해결'도 중요하다고 언급"

### 4. 상충 의견 (Conflicts)
- 서로 모순되거나 다른 방향을 제시하는 내용
- 예:
  * 팀장: "공격적 성장"
  * 개발자: "안정적 운영"
  * → 조정: "성장과 안정의 균형 추구"

### 5. 최종 종합 (Final Synthesis)
- 위 내용을 바탕으로 **하나의 일관된 답변** 생성
- 모든 관점을 반영하되 우선순위를 명확히
- 이 답변은 단일 응답자가 답한 것처럼 자연스러워야 함

### 6. 핵심 키워드 추출 (Extracted Keywords)
- 최종 종합에서 중요한 키워드 5-10개 추출

### 7. 우선순위 순서 (Priority Order)
- 언급 빈도와 중요도를 고려한 우선순위 리스트

---

이제 실제 답변들을 종합하세요.
"""


def synthesize_multi_perspective(
    question: str,
    responses: List[Dict[str, str]],
    question_type: str = "general"
) -> PerspectiveSynthesis:
    """
    Multi-Agent Debate 방식으로 여러 답변 종합

    Args:
        question: 질문
        responses: [{"member": "팀장", "answer": "..."}, ...]
        question_type: 질문 유형 (가중치 조정용)

    Returns:
        PerspectiveSynthesis
    """

    # 1. 각 응답자의 관점 구조화
    perspectives_text = "\n\n".join([
        f"""[{resp['member']}의 관점]
답변: {resp['answer']}
"""
        for resp in responses
    ])

    # 2. 질문 유형에 따른 가중치 가이드 추가
    weight_guide = ""
    if question_type == "cultural":
        weight_guide = "이 질문은 조직 문화에 관한 것이므로, 팀장/리더의 의견에 더 큰 비중을 두세요."
    elif question_type == "technical":
        weight_guide = "이 질문은 기술/실무에 관한 것이므로, 실무 개발자의 의견에 더 큰 비중을 두세요."
    else:
        weight_guide = "모든 팀원의 의견을 균등하게 고려하세요."

    # 3. LLM 호출
    prompt = ChatPromptTemplate.from_messages([
        ("system", DEBATE_SYNTHESIS_PROMPT),
        ("user", f"""
질문: {question}

{perspectives_text}

가중치 가이드: {weight_guide}

위 관점들을 종합하여 분석하세요.
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",  # 복잡한 추론이므로 강력한 모델 사용
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(PerspectiveSynthesis)

    return (prompt | llm).invoke({})
```

### 5. 최종 분석 함수

```python
def analyze_company_general_interview_multi_member(
    answers: List[dict]
) -> CompanyGeneralAnalysis:
    """
    다중 팀원 답변을 종합하여 General 분석

    Args:
        answers: [
            {
                "question": "질문1",
                "responses": [
                    {"member": "팀장", "answer": "..."},
                    {"member": "개발자A", "answer": "..."}
                ]
            },
            ...
        ]

    Returns:
        CompanyGeneralAnalysis
    """

    # 1. 각 질문별로 Multi-Perspective Synthesis 수행
    synthesized_qa = []

    for qa in answers:
        question = qa["question"]
        responses = qa["responses"]

        # 질문 유형 자동 판단
        question_type = classify_question_type(question)

        # 관점 종합
        synthesis = synthesize_multi_perspective(
            question=question,
            responses=responses,
            question_type=question_type
        )

        synthesized_qa.append({
            "question": question,
            "answer": synthesis.final_synthesis,  # 종합된 답변
            "metadata": {
                "consensus": synthesis.consensus,
                "majority_view": synthesis.majority_view,
                "minority_view": synthesis.minority_view,
                "conflicts": synthesis.conflicts,
                "keywords": synthesis.extracted_keywords,
                "priority": synthesis.priority_order
            }
        })

    # 2. 종합된 Q&A로 기존 분석 로직 수행
    all_qa_text = "\n\n".join([
        f"질문: {qa['question']}\n답변: {qa['answer']}"
        for qa in synthesized_qa
    ])

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 기업 HR 담당자입니다.

여러 팀원의 의견을 종합한 면접 답변을 분석하여, 채용 공고를 만들기 위한 정보를 추출하세요.

**분석 목표:**
1. core_values: 회사/팀의 핵심 가치 (최대 5개)
2. ideal_candidate_traits: 이상적인 인재 특징 (3-5개)
3. team_culture: 팀 문화 설명 (2-3문장)
4. work_style: 팀의 업무 방식 (2-3문장)
5. hiring_reason: 채용 이유/목적 (2-3문장)
6. hiring_reason_reasoning: 채용 이유에 대한 심층 분석

**중요**: 이미 종합된 답변이므로, 답변 내용을 그대로 신뢰하고 분석하세요.
"""),
        ("user", all_qa_text)
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(CompanyGeneralAnalysis)

    return (prompt | llm).invoke({})
```

---

## 다음 단계

1. **API 라우트 수정**: `company_interview_routes.py`에서 `num_members`, `member_names` 파라미터 추가
2. **세션 관리**: `CompanyInterviewSession`에 팀원 정보 추가
3. **Technical/Situational 면접**: 동일한 Multi-Perspective 방식 적용
4. **테스트**: 3명의 팀원 시나리오로 E2E 테스트

---

## 참고 사항

- **LLM 비용**: Multi-Perspective Synthesis는 질문당 1회 추가 LLM 호출이 발생 (총 질문 수 × 1회)
- **모델 선택**: 복잡한 추론이 필요하므로 `gpt-4o` 사용 권장 (최종 분석은 `gpt-4o-mini`로 충분)
- **확장성**: Technical, Situational 면접에도 동일한 패턴 적용 가능

---

## ⚖️ Multi-Agent Debate vs 단일 LLM 종합 비교

### 적용 시나리오별 효과성 분석

#### ❌ Multi-Agent Debate가 **비효율적인 경우**

**케이스: 질문 2개 + 긴 서술형 답변 (직무적합성, 문화적합성)**

이 경우 Multi-Agent Debate의 장점이 희석됩니다.

**이유:**

1. **중복 처리 오버헤드**
   ```
   단일 LLM: 3명의 긴 답변 → 1번 종합
   Multi-Agent: 3명의 긴 답변 → 중간 종합 → 다시 종합 (2번 처리)
   ```
   긴 텍스트를 2번 처리하면 정보 손실 가능성 증가

2. **맥락 단절 위험**
   ```
   직무적합성 답변 (500자):
   팀장: "우리는 백엔드 개발자가 필요한데, Python 경험이 필수이고,
         AWS 인프라도 다룰 줄 알아야 하며, 팀 리딩 경험도 있으면 좋고..."

   Multi-Agent 중간 종합:
   "백엔드 개발, Python, AWS, 리더십"

   → 원문의 뉘앙스("필수" vs "있으면 좋고")가 사라질 수 있음
   ```

3. **비용 대비 효과**
   - 질문 2개 × LLM 호출 2번 = 총 4번 LLM 호출
   - 단일 LLM은 1번만 호출
   - 2배 비용인데 효과는 크지 않을 수 있음

---

#### ✅ Multi-Agent Debate가 **효과적인 경우**

**케이스: 질문 5개 이상 + 짧은 답변**

#### 1. **의견 충돌이 명확한 경우**

```
직무적합성:
팀장: "시니어급 개발자가 필요합니다. 최소 5년 이상 경력에 팀 리딩 경험 필수"
개발자A: "주니어도 괜찮아요. 배울 의지만 있으면 됩니다"

→ 단일 LLM: 이런 충돌을 놓칠 수 있음 (하나로 뭉개버림)
→ Multi-Agent: "상충 의견" 섹션에서 명시적으로 처리
```

#### 2. **직급별 관점 차이가 중요한 경우**

```
문화적합성:
팀장: "수평적 문화, 자율성 중시"
실무자들: "실제로는 의사결정이 위에서 내려옴, 자율성 제한적"

→ Multi-Agent가 이런 괴리를 더 잘 포착
```

#### 3. **우선순위 파악이 중요한 경우**

```
직무적합성:
3명 모두 언급: "Python, FastAPI"
2명 언급: "AWS"
1명 언급: "Kubernetes"

→ Multi-Agent: 빈도 기반 우선순위 자동 추출
→ 단일 LLM: 모든 키워드를 동등하게 취급할 수 있음
```

---

### 🔬 실험적 비교

#### 시나리오: 직무적합성 답변 3개

**팀장 답변 (400자)**:
```
백엔드 개발자가 필요합니다. Python과 Django 경험이 필수이고,
대규모 트래픽 처리 경험이 있으면 좋습니다. 팀 리딩 경험도 우대합니다.
```

**개발자A 답변 (350자)**:
```
Python은 필수이고 FastAPI를 쓸 줄 알면 더 좋아요.
AWS 경험이 있어야 하고, 코드 리뷰 문화에 익숙한 분이면 좋겠어요.
```

**개발자B 답변 (300자)**:
```
Python 필수, PostgreSQL 다룰 줄 알아야 하고,
테스트 코드 작성에 익숙한 분이 필요해요. Kubernetes도 알면 좋습니다.
```

---

#### 방법 1: 단일 LLM 종합

```python
prompt = f"""
다음은 3명의 팀원이 직무적합성에 대해 답변한 내용입니다:

팀장: {답변1}
개발자A: {답변2}
개발자B: {답변3}

이를 종합하여 채용공고의 "필수요건"과 "우대사항"을 추출하세요.
"""
```

**예상 결과**:
```
필수요건:
- Python 개발 경험
- Django 또는 FastAPI 경험
- AWS 경험
- PostgreSQL 경험

우대사항:
- 대규모 트래픽 처리 경험
- 팀 리딩 경험
- 테스트 코드 작성
- Kubernetes 경험
```

**문제점**:
- Django vs FastAPI 중 뭐가 더 중요한지 불명확
- AWS가 필수인지 우대인지 애매 (팀장은 안 언급, 개발자A만 필수로 언급)

---

#### 방법 2: Multi-Agent Debate

```python
# Step 1: 각 답변 분석
synthesis = synthesize_multi_perspective(
    question="직무적합성",
    responses=[
        {"member": "팀장", "answer": 답변1},
        {"member": "개발자A", "answer": 답변2},
        {"member": "개발자B", "answer": 답변3}
    ]
)
```

**예상 결과**:
```
공통 합의 (3명 모두 언급):
- Python: 필수

다수 의견 (2명 이상):
- 없음

소수 의견:
- Django (팀장만)
- FastAPI (개발자A만)
- AWS (개발자A만 필수로 언급)
- PostgreSQL (개발자B만)

상충 의견:
- 프레임워크: Django vs FastAPI
  → 조정: 둘 중 하나 경험 필수, 둘 다 가능하면 우대

최종 종합:
필수요건:
- Python 개발 경험 (전원 합의)
- Django 또는 FastAPI 프레임워크 경험 (팀장/개발자A 언급)

우대사항:
- AWS 경험 (개발자A 강조)
- PostgreSQL 경험 (개발자B 언급)
- 대규모 트래픽 처리 (팀장 언급)
- 팀 리딩 경험 (팀장 언급)
```

**장점**:
- 우선순위가 더 명확 (빈도 기반)
- Django/FastAPI 선택 사항임을 명시
- 누가 무엇을 강조했는지 추적 가능

---

### 📊 정량적 비교

| 측면 | 단일 LLM | Multi-Agent Debate |
|------|----------|-------------------|
| **비용** | 1x | 2-3x |
| **처리 시간** | 빠름 | 느림 |
| **우선순위 정확도** | 중간 | 높음 |
| **의견 충돌 감지** | 낮음 | 높음 |
| **정보 손실** | 낮음 | 중간 |
| **구현 복잡도** | 낮음 | 높음 |
| **적합한 케이스** | 긴 답변 2-3개 | 짧은 답변 5개 이상 |

---

### 💡 최종 추천

#### 질문 2개 + 긴 서술형 답변 케이스

**→ 단일 LLM 종합 + 구조화된 프롬프트 추천**

**이유:**
1. 질문이 2개뿐이라 Multi-Agent의 장점이 크지 않음
2. 긴 서술형 답변이므로 정보 손실 리스크가 더 큼
3. 비용 대비 효과가 불명확

**대신 프롬프트를 개선하는 방향으로:**

```python
prompt = f"""
다음은 3명의 팀원이 직무적합성에 대해 답변한 내용입니다:

[팀장 (리더 관점)]
{답변1}

[개발자A (실무자 관점)]
{답변2}

[개발자B (실무자 관점)]
{답변3}

---

**분석 지침:**
1. **빈도 분석**: 2명 이상이 언급한 내용을 우선순위 높게 처리
2. **충돌 감지**: 서로 모순되는 의견이 있으면 명시
3. **직급 고려**: 직무 내용은 모든 의견 균등, 문화는 팀장 의견 중시
4. **필수 vs 우대**:
   - 2명 이상 언급 → 필수
   - 1명만 언급 → 우대
   - 팀장이 "필수"라고 명시 → 필수

출력:
- 필수요건: (빈도순으로 나열)
- 우대사항: (중요도순으로 나열)
- 의견 충돌: (있다면)
- 분석 근거: (어떤 의견을 왜 우선했는지)
"""
```

이 방식이 **비용 효율적이면서도 충분히 정교한 결과**를 낼 것으로 예상됩니다.

---

#### 질문 5개 이상 + 짧은 답변 케이스

**→ Multi-Agent Debate 추천**

**이유:**
1. 짧은 답변 여러 개 → 맥락 손실 위험 적음
2. 빈도 기반 우선순위 자동 추출 효과적
3. 의견 충돌 감지 및 조정 가능
4. 질문이 많아서 종합 효과가 누적됨

---

### 🎯 결론

**현재 프로젝트 상황 (질문 2개: 직무적합성, 문화적합성)**

→ **단일 LLM + 구조화된 프롬프트**가 더 적합합니다.

Multi-Agent Debate는 질문이 많고(10개 이상), 짧은 답변이 많을 때 효과적입니다.
긴 서술형 2개 질문이면 단일 LLM + 좋은 프롬프트가 더 나은 선택입니다.

---

## 🎨 대안 종합 방식들

### 방법 4: Embedding-based Clustering (임베딩 기반 군집화)

**핵심 아이디어**: 각 팀원의 답변을 임베딩하고, 유사도 기반으로 군집화 후 종합

```python
# 1. 각 답변을 임베딩
embeddings = [
    embed(팀장_답변),
    embed(개발자A_답변),
    embed(개발자B_답변)
]

# 2. 의미적 유사도 계산
similarity_matrix = cosine_similarity(embeddings)

# 3. 군집화
# 예: 팀장과 개발자B가 유사 (0.85), 개발자A는 다름 (0.45)
clusters = {
    "group1": [팀장, 개발자B],  # 유사 답변
    "group2": [개발자A]  # 다른 관점
}

# 4. 각 군집별로 종합 + 군집 간 비교
prompt = f"""
유사한 의견 그룹:
- 그룹1 (팀장, 개발자B): {group1_답변}
- 그룹2 (개발자A): {group2_답변}

유사도: 그룹1 내부 0.85, 그룹 간 0.45

→ 다수 의견은 그룹1, 소수 의견은 그룹2로 자동 분류
"""
```

**장점:**
- 의미적 유사성을 정량적으로 측정
- 다수/소수 의견 자동 분류
- 암묵적 의견 충돌 감지

**단점:**
- 임베딩 비용 추가
- 짧은 텍스트에서는 유사도가 부정확할 수 있음
- 해석이 어려움

---

### 방법 5: Incremental Synthesis (점진적 종합)

**핵심 아이디어**: 답변을 순차적으로 누적하면서 종합

```python
# 1단계: 팀장 답변으로 초기 분석
base_analysis = analyze(팀장_답변)

# 2단계: 개발자A 답변 추가하며 업데이트
prompt = f"""
기존 분석:
{base_analysis}

새로운 관점 (개발자A):
{개발자A_답변}

위 새로운 관점을 기존 분석에 통합하세요:
- 일치하는 부분: 강화
- 새로운 부분: 추가
- 충돌하는 부분: 명시
"""
updated_analysis = integrate(base_analysis, 개발자A_답변)

# 3단계: 개발자B 답변 추가
final_analysis = integrate(updated_analysis, 개발자B_답변)
```

**장점:**
- 답변 순서에 따른 가중치 자연스럽게 적용 (팀장 → 실무자 순)
- 각 단계에서 어떤 의견이 추가/변경됐는지 추적 가능
- LLM이 점진적으로 맥락 이해

**단점:**
- LLM 호출 횟수 많음 (n명이면 n-1번)
- 순서 의존성 (A→B→C와 C→B→A 결과가 다를 수 있음)

---

### 방법 6: Role-based Weighted Voting (역할 기반 가중 투표)

**핵심 아이디어**: 각 답변에서 키워드 추출 → 역할별 가중치 투표

```python
# 1. 각 답변에서 구조화된 정보 추출
팀장_keywords = extract_keywords(팀장_답변)
# {"필수": ["Python", "Django"], "우대": ["팀 리딩"], "weight": 1.5}

개발자A_keywords = extract_keywords(개발자A_답변)
# {"필수": ["Python", "FastAPI"], "우대": ["AWS"], "weight": 1.0}

# 2. 키워드별 투표
votes = {
    "Python": {"필수": 3명 * 1.0 = 3.0},  # 전원 필수
    "Django": {"필수": 1명 * 1.5 = 1.5},  # 팀장만
    "FastAPI": {"필수": 1명 * 1.0 = 1.0},  # 개발자A만
    "AWS": {"우대": 1명 * 1.0 = 1.0}
}

# 3. 투표 결과로 우선순위 결정
필수요건 = [kw for kw, v in votes.items() if v["필수"] >= 2.0]
# → Python (3.0), Django (1.5는 미달)

우대사항 = [kw for kw, v in votes.items() if 1.0 <= v < 2.0]
# → Django, FastAPI, AWS
```

**장점:**
- 명확한 정량적 기준
- 투명한 의사결정 (왜 이게 필수인지 설명 가능)
- 직급별 가중치 쉽게 조정

**단점:**
- 키워드 추출이 정확해야 함
- 뉘앙스 손실 (맥락 없이 키워드만)
- LLM 없이도 가능하지만, 추출 자체는 LLM 필요

---

### 방법 7: Consensus Building with Negotiation (협상 기반 합의)

**핵심 아이디어**: 에이전트들이 여러 라운드 협상하며 합의 도출

```python
# Round 1: 각자 초안 제시
팀장_제안 = "Python + Django 필수"
개발자A_제안 = "Python + FastAPI 필수"
개발자B_제안 = "Python + PostgreSQL 필수"

# Round 2: 상호 피드백
팀장_피드백 = "FastAPI도 괜찮지만 Django 경험이 더 중요"
개발자A_피드백 = "Django든 FastAPI든 하나는 필요"
개발자B_피드백 = "프레임워크보다 DB 경험이 중요"

# Round 3: 합의안 도출
compromise = """
- Python 필수 (전원 합의)
- Django 또는 FastAPI 중 하나 필수 (2명 합의)
- PostgreSQL 우대 (1명 의견, 반대 없음)
"""

# LLM이 각 라운드 중재
prompt = f"""
Round 1 제안들:
{제안들}

Round 2 피드백들:
{피드백들}

최종 합의안을 도출하세요.
- 전원 동의 항목은 필수
- 2명 이상 동의는 필수 또는 우대
- 강한 반대가 없는 1명 의견은 우대
"""
```

**장점:**
- 실제 회의와 유사한 프로세스
- 반대 의견 명시적 처리
- 합의 과정 투명

**단점:**
- 라운드 수만큼 LLM 호출 (비용↑)
- 구현 복잡
- 수렴 보장 안 됨 (계속 의견 충돌 가능)

---

### 방법 8: Hierarchical Attention Merging (계층적 어텐션 병합)

**핵심 아이디어**: Transformer의 Attention 메커니즘처럼, 중요한 부분에 집중

```python
# 1. 각 답변의 중요 부분 추출 (attention score)
팀장_답변_scored = {
    "Python 필수": 0.9,
    "Django 경험": 0.8,
    "팀 리딩": 0.6
}

개발자A_답변_scored = {
    "Python 필수": 0.95,
    "FastAPI": 0.85,
    "AWS": 0.7
}

# 2. 교차 어텐션 계산
cross_attention = {
    "Python": (0.9 + 0.95 + 0.9) / 3 = 0.92,  # 높은 합의
    "Django vs FastAPI": conflict_detected,
    "AWS": 0.7 (단일 의견)
}

# 3. 어텐션 가중치로 병합
final = weighted_merge(answers, cross_attention)
```

**장점:**
- 중요도를 자동으로 학습
- Transformer 기반이라 LLM과 호환성 좋음
- 세밀한 제어 가능

**단점:**
- 구현 매우 복잡
- 커스텀 모델 학습 필요할 수 있음
- 해석 어려움

---

### 방법 9: Two-Phase Synthesis (2단계 종합) ⭐ 추천

**핵심 철학**: "정보를 먼저 모으고(Gather), 나중에 판단한다(Judge)"

- Phase 1: **무손실 병합** - 모든 의견을 있는 그대로 수집, 판단 보류
- Phase 2: **지능적 판단** - 수집된 정보를 바탕으로 우선순위, 충돌, 분류 결정

이 방식의 장점은 **정보 손실을 최소화**하면서도 **복잡도를 분산**시킨다는 것입니다.

#### Phase 1: Structured Aggregation (구조화된 집계)

**목표:**
- 각 팀원의 답변에서 **구조화된 정보 추출**
- **판단 없이** 모든 정보를 평등하게 나열
- 메타데이터 추가 (누가, 어떤 강도로 언급했는지)

**Pydantic 모델:**

```python
from pydantic import BaseModel, Field
from typing import List, Literal

class ExtractedRequirement(BaseModel):
    """추출된 요구사항"""
    keyword: str = Field(description="핵심 키워드 (예: Python, AWS)")
    category: Literal["기술스택", "경험", "역량", "자격"] = Field(description="카테고리")
    importance: Literal["필수", "우대", "선택", "불명확"] = Field(description="중요도")
    context: str = Field(description="원문에서 언급된 맥락 (1문장)")
    mentioned_by: str = Field(description="언급한 사람")

class Phase1Output(BaseModel):
    """Phase 1 출력"""
    requirements: List[ExtractedRequirement] = Field(description="추출된 모든 요구사항")
    raw_texts: List[dict] = Field(description="원문 보존 (참조용)")
```

**구현 코드:**

```python
def phase1_extract(question: str, responses: List[dict]) -> Phase1Output:
    """
    Phase 1: 각 답변에서 구조화된 정보 추출

    Args:
        question: 질문 (예: "직무적합성")
        responses: [{"member": "팀장", "answer": "..."}, ...]

    Returns:
        Phase1Output (모든 요구사항 구조화)
    """

    all_requirements = []

    for resp in responses:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 정보 추출 전문가입니다.

주어진 답변에서 **채용 요구사항**을 추출하되, **판단하지 마세요**.

추출 규칙:
1. 기술스택, 경험, 역량, 자격 등 모든 요구사항 추출
2. 중요도는 원문의 표현 그대로 파악
   - "필수", "반드시" → 필수
   - "우대", "있으면 좋음" → 우대
   - 언급만 됨 → 선택
   - 애매함 → 불명확
3. 맥락 보존: 원문의 1문장을 그대로 인용
4. 추측하지 말 것

예시:
원문: "Python 경험이 필수이고, AWS를 다룰 줄 알면 더 좋습니다"
→
- keyword: "Python", importance: "필수", context: "Python 경험이 필수이고"
- keyword: "AWS", importance: "우대", context: "AWS를 다룰 줄 알면 더 좋습니다"
"""),
            ("user", f"""
질문: {question}
답변자: {resp['member']}
답변: {resp['answer']}

위 답변에서 모든 요구사항을 추출하세요.
""")
        ])

        settings = get_settings()
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,  # 추출은 정확해야 하므로 0
            api_key=settings.OPENAI_API_KEY
        ).with_structured_output(List[ExtractedRequirement])

        requirements = (prompt | llm).invoke({})
        all_requirements.extend(requirements)

    return Phase1Output(
        requirements=all_requirements,
        raw_texts=responses
    )
```

**Phase 1 출력 예시:**

```python
Phase1Output(
    requirements=[
        ExtractedRequirement(
            keyword="Python",
            category="기술스택",
            importance="필수",
            context="Python과 Django 경험이 필수이고",
            mentioned_by="팀장"
        ),
        ExtractedRequirement(
            keyword="Django",
            category="기술스택",
            importance="필수",
            context="Python과 Django 경험이 필수이고",
            mentioned_by="팀장"
        ),
        ExtractedRequirement(
            keyword="FastAPI",
            category="기술스택",
            importance="우대",
            context="FastAPI를 쓸 줄 알면 더 좋아요",
            mentioned_by="개발자A"
        ),
        # ... 더 많은 항목들
    ],
    raw_texts=[...]
)
```

---

#### Phase 2: Intelligent Synthesis (지능적 종합)

**목표:**
- Phase 1의 구조화된 데이터를 **분석**
- **빈도, 중요도, 충돌** 파악
- 최종 공고용 **필수/우대 분류**

**Pydantic 모델:**

```python
class ConflictItem(BaseModel):
    """충돌 항목"""
    issue: str = Field(description="충돌 이슈 (예: 프레임워크 선택)")
    options: List[str] = Field(description="충돌하는 옵션들 (예: ['Django', 'FastAPI'])")
    mentions: dict = Field(description="각 옵션별 언급자")
    resolution: str = Field(description="해결 방안")

class FinalRequirements(BaseModel):
    """최종 요구사항"""
    required_skills: List[str] = Field(description="필수 역량", max_length=8)
    preferred_skills: List[str] = Field(description="우대 사항", max_length=8)
    conflict_resolutions: List[str] = Field(description="충돌 해결 내역")
    reasoning: str = Field(description="판단 근거")
```

**구현 코드:**

```python
from collections import Counter, defaultdict

def phase2_synthesize(phase1_output: Phase1Output) -> FinalRequirements:
    """
    Phase 2: 구조화된 정보를 종합하여 최종 요구사항 도출
    """

    # 1. 빈도 분석
    keyword_mentions = defaultdict(list)

    for req in phase1_output.requirements:
        keyword_mentions[req.keyword].append({
            "member": req.mentioned_by,
            "importance": req.importance,
            "context": req.context
        })

    # 2. 통계 생성
    stats = {}
    for keyword, mentions in keyword_mentions.items():
        num_mentions = len(mentions)
        importance_counts = Counter([m["importance"] for m in mentions])

        stats[keyword] = {
            "count": num_mentions,
            "members": [m["member"] for m in mentions],
            "importance_dist": dict(importance_counts),
            "contexts": [m["context"] for m in mentions]
        }

    # 3. LLM에게 종합 요청 (통계 기반)
    stats_summary = format_stats_for_llm(stats)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 채용 요구사항 종합 전문가입니다.

Phase 1에서 추출된 구조화된 정보를 바탕으로 최종 요구사항을 결정하세요.

**판단 기준:**

1. **필수 역량 (Required Skills)**:
   - 2명 이상이 "필수"로 언급
   - 또는 팀장이 "필수"로 명시 + 반대 없음
   - 예: Python (3명 언급, 모두 필수)

2. **우대 사항 (Preferred Skills)**:
   - 2명 이상 언급했지만 "우대" 또는 중요도 혼재
   - 1명만 언급했지만 중요도 높음 (필수 or 우대)
   - 예: AWS (1명만 필수로 언급 → 우대로 완화)

3. **충돌 처리 (Conflicts)**:
   - 같은 카테고리에서 서로 다른 옵션 제시
   - 예: Django vs FastAPI
   - 해결: "Django 또는 FastAPI 중 하나 경험 필수"

4. **제외 항목**:
   - 1명만 언급 + 중요도 "선택" 또는 "불명확"

**중요**: 원문 맥락(context)을 참고하여 판단하세요.
"""),
        ("user", f"""
## Phase 1 통계 분석

{stats_summary}

## 원문 참조
{format_raw_texts(phase1_output.raw_texts)}

---

위 정보를 바탕으로 최종 요구사항을 결정하세요.
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",  # Phase 2는 판단이 필요하므로 강력한 모델
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(FinalRequirements)

    return (prompt | llm).invoke({})


def format_stats_for_llm(stats: dict) -> str:
    """통계를 LLM이 읽기 좋은 형식으로 변환"""
    lines = []

    # 빈도순 정렬
    sorted_keywords = sorted(stats.items(), key=lambda x: x[1]["count"], reverse=True)

    for keyword, data in sorted_keywords:
        lines.append(f"### {keyword}")
        lines.append(f"- 언급 횟수: {data['count']}명")
        lines.append(f"- 언급자: {', '.join(data['members'])}")
        lines.append(f"- 중요도 분포: {data['importance_dist']}")
        lines.append(f"- 맥락:")
        for ctx in data['contexts']:
            lines.append(f"  * \"{ctx}\"")
        lines.append("")

    return "\n".join(lines)
```

**Phase 2 입력 예시 (LLM에게 전달되는 내용):**

```
## Phase 1 통계 분석

### Python
- 언급 횟수: 3명
- 언급자: 팀장, 개발자A, 개발자B
- 중요도 분포: {'필수': 3}
- 맥락:
  * "Python과 Django 경험이 필수이고"
  * "Python은 필수이고"
  * "Python 필수, PostgreSQL 다룰 줄 알아야 하고"

### Django
- 언급 횟수: 1명
- 언급자: 팀장
- 중요도 분포: {'필수': 1}
- 맥락:
  * "Python과 Django 경험이 필수이고"

### FastAPI
- 언급 횟수: 1명
- 언급자: 개발자A
- 중요도 분포: {'우대': 1}
- 맥락:
  * "FastAPI를 쓸 줄 알면 더 좋아요"

---

충돌 감지:
- Django (팀장, 필수) vs FastAPI (개발자A, 우대)
  → 같은 카테고리 "프레임워크"
```

**Phase 2 출력 예시:**

```python
FinalRequirements(
    required_skills=[
        "Python 개발 경험 3년 이상",
        "Django 또는 FastAPI 프레임워크 경험"
    ],
    preferred_skills=[
        "AWS 클라우드 인프라 경험",
        "PostgreSQL 데이터베이스 경험",
        "대규모 트래픽 처리 경험",
        "팀 리딩 또는 멘토링 경험"
    ],
    conflict_resolutions=[
        "프레임워크: 팀장은 Django를 필수로, 개발자A는 FastAPI를 우대로 언급. 둘 중 하나 경험을 필수로 통합"
    ],
    reasoning="""
    필수 역량 선정 근거:
    - Python: 3명 모두 필수로 언급 (만장일치)
    - Django/FastAPI: 팀장이 Django 필수, 개발자A가 FastAPI 우대 언급.
      프레임워크 경험이 중요하다는 점에서는 합의. 선택권 부여.

    우대 사항 선정 근거:
    - AWS: 개발자A만 필수로 언급했으나, 다른 팀원 반대 없음. 우대로 완화.
    - PostgreSQL: 개발자B만 언급. 데이터베이스 경험은 중요하므로 우대 포함.
    """
)
```

---

#### 전체 플로우 통합

```python
def two_phase_synthesis(
    question: str,
    responses: List[dict]
) -> FinalRequirements:
    """
    Two-Phase Synthesis 전체 플로우

    Args:
        question: 질문 (예: "직무적합성")
        responses: [{"member": "팀장", "answer": "..."}, ...]

    Returns:
        FinalRequirements (최종 요구사항)
    """

    print("[Phase 1] 구조화된 정보 추출 중...")
    phase1_output = phase1_extract(question, responses)

    print(f"  → {len(phase1_output.requirements)}개 요구사항 추출 완료")

    print("[Phase 2] 지능적 종합 중...")
    final_requirements = phase2_synthesize(phase1_output)

    print("  → 최종 요구사항 도출 완료")
    print(f"     필수: {len(final_requirements.required_skills)}개")
    print(f"     우대: {len(final_requirements.preferred_skills)}개")

    return final_requirements
```

---

#### 장단점 분석

**✅ 장점:**

1. **정보 손실 최소화**
   - Phase 1에서 원문 맥락을 모두 보존
   - Phase 2에서 필요하면 원문 참조 가능

2. **판단과 추출 분리**
   - Phase 1: 사실 추출 (temperature=0.0, 정확성 우선)
   - Phase 2: 판단 및 종합 (temperature=0.3, 창의성 필요)

3. **디버깅 용이**
   - Phase 1 출력을 보면 어떤 정보가 추출됐는지 확인 가능
   - Phase 2에서 잘못 판단했다면 프롬프트만 수정

4. **투명성**
   - 최종 결과에 "reasoning" 포함
   - 왜 이렇게 판단했는지 설명 가능

5. **확장성**
   - Phase 1 출력을 DB에 저장하면
   - 나중에 Phase 2만 재실행 가능 (프롬프트 개선 시)

**❌ 단점:**

1. **LLM 호출 횟수**
   - Phase 1: 응답자 수만큼 (3명이면 3번)
   - Phase 2: 1번
   - 총 4번 (단일 LLM은 1번)

2. **구현 복잡도**
   - Pydantic 모델 여러 개 정의
   - 통계 처리 로직 필요

3. **Phase 1의 추출 오류**
   - Phase 1에서 잘못 추출하면 Phase 2도 영향
   - (Garbage In, Garbage Out)

---

#### 최적화 버전 ⭐⭐ 실용적 추천

**Phase 1을 간소화**하면 비용 절감 가능:

```python
def phase1_simple_aggregate(responses: List[dict]) -> str:
    """
    Phase 1 간소화: LLM 없이 단순 집계
    """
    aggregated = []

    for resp in responses:
        aggregated.append(f"""
[{resp['member']}의 답변]
{resp['answer']}
""")

    return "\n\n".join(aggregated)

def two_phase_synthesis_optimized(
    question: str,
    responses: List[dict]
) -> FinalRequirements:
    """
    최적화된 Two-Phase Synthesis
    Phase 1: LLM 없이 단순 집계
    Phase 2: 구조화된 프롬프트로 종합
    """

    # Phase 1: 단순 집계 (LLM 호출 없음)
    aggregated = phase1_simple_aggregate(responses)

    # Phase 2: 종합 (LLM 1번만 호출)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 채용 요구사항 종합 전문가입니다.

**2단계 사고 프로세스:**

Step 1 (마음속으로): 각 답변에서 요구사항 추출
- 키워드와 중요도 파악
- 빈도 계산
- 충돌 감지

Step 2 (출력): 최종 요구사항 결정
- 필수: 2명 이상 언급 또는 팀장 명시
- 우대: 1명 언급 또는 중요도 낮음
- 충돌: 조정안 제시

**판단 기준은 명확히, 근거는 상세히 작성하세요.**
"""),
        ("user", f"""
질문: {question}

{aggregated}

---

위 답변들을 종합하여 최종 요구사항을 도출하세요.
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(FinalRequirements)

    return (prompt | llm).invoke({})
```

**최적화 버전의 장점:**
- **LLM 1번만 호출** (단일 LLM과 동일한 비용)
- 하지만 **2단계 사고 프로세스를 프롬프트에 명시**
- 구현 간단, 비용 효율적
- 단일 LLM보다 구조화된 사고 유도

---

### 방법 10: Hybrid (하이브리드)

**핵심 아이디어**: 여러 방법의 장점 결합

```python
# Step 1: 키워드 투표 (방법 6)
keyword_votes = weighted_voting(all_answers)
# → 정량적 기준 확보

# Step 2: 단일 LLM 종합 + 키워드 힌트
prompt = f"""
다음은 3명의 답변입니다:
[팀장] {답변1}
[개발자A] {답변2}
[개발자B] {답변3}

**키워드 빈도 분석 (참고용)**:
{keyword_votes}

위 정보를 바탕으로:
1. 빈도 높은 키워드 우선
2. 하지만 맥락도 고려 (답변 원문 참조)
3. 충돌 감지 시 명시

출력: 필수요건, 우대사항, 충돌사항
"""
```

**장점:**
- 정량적 + 정성적 분석 결합
- 단일 LLM보다 정확, Multi-Agent보다 효율적
- 구현 적당히 복잡

**단점:**
- 여전히 비용 있음 (키워드 추출 + 종합)

---

## 📊 모든 방법 종합 비교

| 방법 | 비용 | 구현 난이도 | 정확도 | 해석성 | 적합 케이스 |
|------|------|-------------|--------|--------|-------------|
| 단일 LLM | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | 긴 답변 2-3개 |
| Multi-Agent | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 짧은 답변 5개+ |
| Embedding 군집 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | 답변 많을 때 |
| 점진적 종합 | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | 순서가 중요할 때 |
| 가중 투표 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 명확한 기준 필요 |
| 협상 기반 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 강한 충돌 예상 |
| 어텐션 병합 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ | 연구용 |
| **Two-Phase (최적화)** | ⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **대부분 케이스** |
| 하이브리드 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 정량+정성 필요 |

---

## 💡 현재 프로젝트 최종 추천

### 1순위: **Two-Phase Synthesis 최적화 버전**

**이유:**
- 질문 2개 + 긴 답변에 적합
- LLM 1번만 호출 (비용 = 단일 LLM과 동일)
- 2단계 사고 프로세스로 더 정교한 판단
- 구현 간단 (Pydantic 모델 1개만 필요)
- 투명성 높음 (reasoning 필드로 판단 근거 제공)

### 2순위: **단일 LLM + 구조화된 프롬프트**

**이유:**
- 가장 간단하고 비용 효율적
- 프롬프트 엔지니어링만으로 해결

### 3순위: **하이브리드 (키워드 투표 + LLM 종합)**

**이유:**
- 정량적 기준이 중요한 경우
- 의사결정 근거를 명확히 해야 할 때
