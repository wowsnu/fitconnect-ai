"""
Situational Interview (상황 면접)

- 페르소나 분석 (5개 차원)
- 6개 질문 (탐색 3 + 심화 2 + 검증 1)
- 적응형 질문 생성
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ai.interview.talent.models import (
    CandidateProfile,
    PersonaScores,
    FinalPersonaReport,
    GeneralInterviewCardPart,
    TechnicalInterviewCardPart,
    SituationalInterviewCardPart,
)
from config.settings import get_settings


# 초기 탐색 질문 (고정 3개)
INITIAL_QUESTIONS = [
    {
        "question": "팀에서 중요한 의사결정을 내려야 할 때, 의견이 나뉘면 어떻게 해결하나요?",
        "targets": ["work_style", "communication"]
    },
    {
        "question": "급하게 처리해야 할 일이 갑자기 생겼을 때, 어떻게 대응하나요?",
        "targets": ["problem_solving", "stress_response"]
    },
    {
        "question": "완전히 새로운 분야를 짧은 시간 안에 배워야 할 때, 어떤 방식으로 접근하나요?",
        "targets": ["learning"]
    }
]


class TraitScores(BaseModel):
    """성향별 점수"""
    scores: dict[str, float] = Field(
        description="각 성향별 점수 (0.0~1.0)",
        examples=[{"주도형": 0.8, "협력형": 0.2}]
    )


class AnswerAnalysis(BaseModel):
    """답변 분석 결과"""

    reasoning: str = Field(
        description="분석 근거",
        min_length=30
    )

    work_style: Optional[dict[str, float]] = Field(
        default=None,
        description="업무 스타일 점수"
    )

    problem_solving: Optional[dict[str, float]] = Field(
        default=None,
        description="문제 해결 점수"
    )

    learning: Optional[dict[str, float]] = Field(
        default=None,
        description="학습 성향 점수"
    )

    stress_response: Optional[dict[str, float]] = Field(
        default=None,
        description="스트레스 대응 점수"
    )

    communication: Optional[dict[str, float]] = Field(
        default=None,
        description="커뮤니케이션 점수"
    )


def analyze_situational_answer(
    question: str,
    answer: str,
    target_dimensions: List[str]
) -> AnswerAnalysis:
    """
    상황 면접 답변 분석

    Args:
        question: 질문
        answer: 답변
        target_dimensions: 측정 대상 차원들

    Returns:
        AnswerAnalysis
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 산업심리학 전문가입니다.

**분석 기준:**

1. **work_style** (업무 스타일):
   - 주도형: "내가 제안", "리드", "결정"
   - 협력형: "함께", "논의", "의견 수렴"
   - 독립형: "혼자", "스스로", "자율적"

2. **problem_solving** (문제 해결):
   - 분석형: "원인 분석", "데이터", "체계적"
   - 직관형: "직감", "경험상", "빠르게"
   - 실행형: "일단 시도", "테스트", "실험"

3. **learning** (학습):
   - 체계형: "문서", "강의", "순서대로"
   - 실험형: "직접 만들어보며", "프로젝트"
   - 관찰형: "코드 분석", "다른 사람"

4. **stress_response** (스트레스):
   - 도전형: "기회", "성장", "재미"
   - 안정형: "계획", "준비", "체크리스트"
   - 휴식형: "힘들었다", "도움 요청"

5. **communication** (커뮤니케이션):
   - 논리형: "근거", "데이터", "객관적"
   - 공감형: "이해", "감정", "입장"
   - 간결형: "명확하게", "핵심만"

**점수 규칙:**
- 각 차원별로 0.0 ~ 1.0 점수
- 강한 신호: 0.7~1.0
- 중간 신호: 0.4~0.6
- 약한 신호: 0.0~0.3
- 합이 1.0일 필요 없음 (중복 가능)
"""),
        ("user", f"""
질문: {question}
답변: {answer}
측정 대상: {", ".join(target_dimensions)}

답변을 분석하여 각 차원별 성향 점수를 제공하세요.
실제 답변에서 드러난 내용만 분석하고, 추측하지 마세요.

측정 대상이 아닌 차원은 빈 객체로 반환하세요.
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(AnswerAnalysis)

    return (prompt | llm).invoke({})


def analyze_situational_interview_for_card(
    candidate_profile: CandidateProfile,
    situational_report: FinalPersonaReport,
    qa_history: list[dict],
    general_part: GeneralInterviewCardPart,
    technical_part: TechnicalInterviewCardPart
) -> SituationalInterviewCardPart:
    """
    상황 면접 결과를 프로필 카드용 파트로 변환

    Args:
        candidate_profile: 지원자 기본 프로필
        situational_report: 상황 면접 페르소나 리포트
        qa_history: 상황 면접 원본 Q&A
        general_part: 구조화 면접 카드 파트
        technical_part: 직무 면접 카드 파트

    Returns:
        SituationalInterviewCardPart
    """
    qa_text = "\n\n".join([
        f"질문: {qa['question']}\n답변: {qa['answer'][:150]}..."
        for qa in qa_history
    ])

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 HR 전문가입니다.
상황 면접 결과를 분석하여 **직무 적합성**, **협업 성향**, **성장 가능성**을 요약하세요.
또한 이전 면접에서 부족한 부분이 있다면 보완하세요.

**추출 목표:**

1. **직무 적합성** (한 문장):
   - 페르소나와 업무 스타일을 종합하여 직무 적합도 평가
   - 예: "체계적이고 논리적인 문제 해결로 백엔드 개발에 적합"

2. **협업 성향** (한 문장):
   - 커뮤니케이션과 팀워크 스타일 요약
   - 예: "적극적인 코드 리뷰와 지식 공유로 팀 성장에 기여"

3. **성장 가능성** (한 문장):
   - 학습 성향과 발전 가능성 평가
   - 예: "빠른 학습 능력과 실험적 태도로 신기술 습득에 강점"

4. **부족한 부분 보완** (Optional):
   - 이전 면접에서 충분히 드러나지 않은 경험, 강점, 역량이 있다면 추가
   - 상황 면접 답변에서 새로 발견된 내용 위주

**주의:**
- 각 항목은 한 문장으로 명확하게 작성
- 페르소나 분석 결과와 일관성 유지
- 보완 항목은 실제로 필요한 경우에만 추가
"""),
        ("user", f"""
## 지원자 기본 정보
- 이름: {candidate_profile.basic.name if candidate_profile.basic else "지원자"}
- 직무: {candidate_profile.basic.tagline if candidate_profile.basic else "개발자"}

## 상황 면접 페르소나 분석
- 업무 스타일: {situational_report.work_style}
- 문제 해결: {situational_report.problem_solving}
- 학습 성향: {situational_report.learning}
- 스트레스 대응: {situational_report.stress_response}
- 커뮤니케이션: {situational_report.communication}
- 종합 요약: {situational_report.summary}
- 팀 적합도: {situational_report.team_fit}

## 상황 면접 원본 답변
{qa_text}

## 이전 면접 결과 (부족한 부분 확인용)
- 추출된 주요 경험: {len(general_part.key_experiences)}개
- 추출된 일반 역량: {len(general_part.core_competencies)}개
- 추출된 강점: {len(technical_part.strengths)}개
- 추출된 직무 역량: {len(technical_part.technical_skills)}개

위 정보를 바탕으로:
1. **직무 적합성** 한 문장
2. **협업 성향** 한 문장
3. **성장 가능성** 한 문장
4. 상황 면접 답변에서 이전 면접에서 다루지 못한 경험/강점/역량이 있다면 보완 (없으면 빈 리스트)
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(SituationalInterviewCardPart)

    return (prompt | llm).invoke({})


def generate_deep_dive_question(
    dominant_trait: str,
    dimension: str,
    qa_history: List[dict]
) -> str:
    """
    심화 질문 생성

    Args:
        dominant_trait: 가장 강한 성향 (예: "주도형", "분석형")
        dimension: 해당 차원 (예: "work_style", "problem_solving")
        qa_history: 이전 질문-답변 이력

    Returns:
        심화 질문
    """
    # 이전 답변 요약
    history_text = "\n".join([
        f"Q: {qa['question']}\nA: {qa['answer'][:100]}..."
        for qa in qa_history[-3:]  # 최근 3개만
    ])

    dimension_map = {
        "work_style": "업무 스타일",
        "problem_solving": "문제 해결 방식",
        "learning": "학습 성향",
        "stress_response": "스트레스 대응",
        "communication": "커뮤니케이션"
    }

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""당신은 인재 채용 전문가입니다.

지원자가 [{dominant_trait}] 성향이 강합니다.

이전 답변:
{history_text}

**심화 질문 생성 가이드:**
- {dimension_map[dimension]} 차원에서 [{dominant_trait}] 성향을 더 깊이 확인
- 구체적인 상황을 제시하여 실제 행동 패턴 파악
- 이전 답변에서 애매했던 부분 명확히 하기
- 예/아니오로 답할 수 없는 열린 질문
- 특정 직군에 국한되지 않는 범용적인 상황 질문

**예시:**
- 주도형 → "상사나 리더가 잘못된 결정을 했다고 생각될 때, 어떻게 행동하나요?"
- 분석형 → "시간이 부족한 상황에서도 분석을 먼저 하나요? 아니면 빠르게 실행하나요?"
- 협력형 → "의견이 분분한 상황에서 어떻게 합의를 이끌어내나요?"
"""),
        ("user", f"[{dominant_trait}] 성향을 깊이 파악할 수 있는 구체적인 상황 질문 1개를 생성하세요.")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
        api_key=settings.OPENAI_API_KEY
    )

    result = (prompt | llm).invoke({})
    return result.content


class SituationalInterview:
    """상황 면접 관리 클래스"""

    def __init__(self):
        # 상태
        self.current_question_num = 0  # 0부터 시작
        self.phase: Literal["exploration", "deep_dive", "validation"] = "exploration"

        # 페르소나 점수 초기화
        self.persona_scores = PersonaScores(
            work_style={},
            problem_solving={},
            learning={},
            stress_response={},
            communication={}
        )

        # 질문-답변 이력
        self.qa_history = []

        # 현재 질문
        self.current_question = None

    def get_next_question(self) -> Optional[dict]:
        """
        다음 질문 반환

        Returns:
            {
                "question": str,
                "phase": str,
                "progress": str
            }
        """
        if self.is_finished():
            return None

        # Phase 1: 탐색 (질문 0, 1, 2)
        if self.current_question_num < 3:
            question_data = INITIAL_QUESTIONS[self.current_question_num]
            self.current_question = question_data

            return {
                "question": question_data["question"],
                "phase": "exploration",
                "progress": f"{self.current_question_num + 1}/6"
            }

        # Phase 2: 심화 (질문 3, 4)
        elif self.current_question_num < 5:
            # 가장 강한 성향 찾기
            dominant = self._get_dominant_trait()

            # 심화 질문 생성
            question_text = generate_deep_dive_question(
                dominant_trait=dominant["trait"],
                dimension=dominant["dimension"],
                qa_history=self.qa_history
            )

            self.current_question = {
                "question": question_text,
                "targets": [dominant["dimension"]]
            }

            return {
                "question": question_text,
                "phase": "deep_dive",
                "progress": f"{self.current_question_num + 1}/6"
            }

        # Phase 3: 검증 (질문 5)
        else:
            # 가장 불명확한 차원 찾기
            unclear_dim = self._get_unclear_dimension()

            # 검증 질문 (간단하게 고정)
            validation_questions = {
                "work_style": "마감이 임박했을 때, 혼자 처리할지 팀과 협업할지 어떻게 결정하나요?",
                "problem_solving": "처음 접하는 문제를 만났을 때, 첫 30분 동안 무엇을 하나요?",
                "learning": "시간이 부족할 때, 새로운 지식을 어떻게 습득하나요?",
                "stress_response": "중요한 업무 직전에, 어떤 준비를 하나요?",
                "communication": "동료가 내 의견에 강하게 반대할 때, 어떻게 대응하나요?"
            }

            question_text = validation_questions.get(unclear_dim, validation_questions["work_style"])

            self.current_question = {
                "question": question_text,
                "targets": [unclear_dim]
            }

            return {
                "question": question_text,
                "phase": "validation",
                "progress": "6/6"
            }

    def submit_answer(self, answer: str) -> dict:
        """
        답변 제출 및 분석

        Args:
            answer: 답변 텍스트

        Returns:
            {
                "analysis": dict,
                "next_question": dict or None
            }
        """
        if not self.current_question:
            raise ValueError("질문을 먼저 받아야 합니다.")

        # 답변 분석
        analysis = analyze_situational_answer(
            question=self.current_question["question"],
            answer=answer,
            target_dimensions=self.current_question["targets"]
        )

        # 점수 누적
        detected_traits = {}
        for dimension in ["work_style", "problem_solving", "learning", "stress_response", "communication"]:
            scores = getattr(analysis, dimension)
            if scores is not None and scores:
                detected_traits[dimension] = scores
                current = self.persona_scores.__dict__[dimension]
                for trait, score in scores.items():
                    current[trait] = current.get(trait, 0.0) + score

        # 이력 저장
        self.qa_history.append({
            "question": self.current_question["question"],
            "answer": answer,
            "analysis": analysis.reasoning
        })

        # 다음 단계로
        self.current_question_num += 1

        return {
            "analysis": {
                "reasoning": analysis.reasoning,
                "detected_traits": detected_traits
            },
            "next_question": self.get_next_question()
        }

    def _get_dominant_trait(self) -> dict:
        """가장 강한 성향 찾기"""
        all_traits = {}

        for dimension, scores in self.persona_scores.__dict__.items():
            for trait, score in scores.items():
                all_traits[f"{dimension}:{trait}"] = {
                    "dimension": dimension,
                    "trait": trait,
                    "score": score
                }

        if not all_traits:
            return {"dimension": "work_style", "trait": "협력형", "score": 0.5}

        dominant_key = max(all_traits, key=lambda k: all_traits[k]["score"])
        return all_traits[dominant_key]

    def _get_unclear_dimension(self) -> str:
        """가장 불명확한 차원 찾기"""
        dimension_scores = {}

        for dimension, scores in self.persona_scores.__dict__.items():
            if scores:
                dimension_scores[dimension] = max(scores.values())
            else:
                dimension_scores[dimension] = 0.0

        # 점수가 낮은 차원 = 불명확
        unclear = min(dimension_scores, key=dimension_scores.get)
        return unclear

    def is_finished(self) -> bool:
        """모든 질문 완료 여부"""
        return self.current_question_num >= 6

    def get_final_report(self) -> FinalPersonaReport:
        """
        최종 페르소나 리포트 생성

        Returns:
            FinalPersonaReport
        """
        if not self.is_finished():
            raise ValueError("모든 질문을 완료해야 리포트를 생성할 수 있습니다.")

        # 각 차원별 최고 점수 성향 선택
        final_persona = {}
        for dimension, scores in self.persona_scores.__dict__.items():
            if scores:
                final_persona[dimension] = max(scores, key=scores.get)
            else:
                final_persona[dimension] = "알 수 없음"

        # LLM으로 요약 및 팀 적합도 분석
        qa_summary = "\n".join([
            f"Q: {qa['question']}\nA: {qa['answer'][:100]}...\n"
            for qa in self.qa_history
        ])

        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 인재 분석 전문가입니다.

인터뷰 결과를 바탕으로 지원자의 페르소나를 분석하고, 각 차원별 판단 근거를 제시하세요.

**각 차원별 근거 작성 가이드:**
- 실제 답변 내용을 인용하여 구체적으로 작성
- 왜 해당 성향으로 판단했는지 명확히 설명
- 50자 정도로 간결하게 작성

**요약 예시:**
- "협력적이며 논리적인 분석가형"
- "주도적이고 실행력 있는 리더형"
- "독립적이며 체계적인 학습자형"

**팀 적합도 예시:**
- "애자일 환경, 기술 토론 활발한 팀"
- "빠른 의사결정이 필요한 스타트업"
- "체계적인 프로세스를 갖춘 대기업"
"""),
            ("user", f"""
성향 분석 결과:
- 업무 스타일: {final_persona['work_style']}
- 문제 해결: {final_persona['problem_solving']}
- 학습: {final_persona['learning']}
- 스트레스: {final_persona['stress_response']}
- 커뮤니케이션: {final_persona['communication']}

인터뷰 내용:
{qa_summary}

각 차원별 판단 근거와 함께 요약 및 추천 팀 환경을 작성하세요.
""")
        ])

        settings = get_settings()
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.5,
            api_key=settings.OPENAI_API_KEY
        ).with_structured_output(FinalPersonaReport)

        return (prompt | llm).invoke({})
