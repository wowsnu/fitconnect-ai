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
        "question": "팀 프로젝트에서 의견 충돌이 있었을 때, 어떤 방식으로 해결하시나요? 구체적인 상황과 행동을 함께 답해주세요.",
        "targets": ["work_style", "communication"]
    },
    {
        "question": "예상치 못한 업무 변경이나 마감기한이 단축되었을 때, 어떻게 대응하시나요? 구체적 사례를 들어 설명해주세요.",
        "targets": ["problem_solving", "stress_response"]
    },
    {
        "question": "완전히 새로운 분야나 업무를 맡게 되어, 짧은 시간 안에 배워서 적용한 경험을 들려주세요. 구체적으로 어떤 방식으로 학습하고 성과를 냈나요?",
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
        ("system", """당신은 HR 전문가입니다.
         
         지원자의 Culture-Fit 성향을 판단하기 위해 아래 분석 기준을 활용해주세요.

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

        **중요:**
        - 각 차원(work_style, problem_solving 등)의 값은 반드시 dictionary 형태로 반환해야 합니다.
        - 각 차원의 값은 하위 유형과 점수를 포함하는 dict 객체여야 합니다 (예: 주도형 0.8, 협력형 0.2).
        - 측정 대상이 아닌 차원은 null로 반환하거나 포함하지 마세요.
        - 절대로 float 값만 단독으로 반환하지 마세요. 반드시 dict 안에 키-값 쌍으로 반환하세요.
        """)
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(AnswerAnalysis)

    try:
        print(f"[DEBUG] analyze_situational_answer called for dimensions: {target_dimensions}")
        result = (prompt | llm).invoke({})
        print(f"[DEBUG] LLM response: work_style={type(result.work_style)}, communication={type(result.communication)}")
        return result
    except Exception as e:
        print(f"[ERROR] Failed to analyze situational answer: {type(e).__name__}: {str(e)}")
        print(f"[ERROR] Question: {question[:100]}...")
        print(f"[ERROR] Answer: {answer[:100]}...")
        raise


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
        문화 적합성 면접 결과를 분석하여 지원자의 **직무 적합성**, **협업 성향**, **성장 가능성**을 요약하고, 
        이전 면접에서 충분히 드러나지 않은 부분이 있다면 보완하세요.

        **분석 목표:**
        1. **직무 적합성** (한 문장)
        - 지원자의 페르소나, 업무 스타일, 경험을 종합하여 직무 적합도를 평가
        - 예시: "체계적이고 논리적인 문제 해결 능력으로 백엔드 개발 직무에 적합"
        - 예시: "데이터 기반 분석과 전략적 사고를 바탕으로 마케팅 기획 직무에 적합"

        2. **협업 성향** (한 문장)
        - 커뮤니케이션 스타일과 팀워크 방식을 요약
        - 예시: "코드 리뷰와 지식 공유를 적극적으로 수행하며 팀 성장에 기여"
        - 예시: "팀원 의견을 경청하고 조율하여 프로젝트 목표 달성에 기여"

        3. **성장 가능성** (한 문장)
        - 학습 태도와 발전 가능성을 평가
        - 예시: "빠른 학습 능력과 실험적 접근으로 신기술 습득에 강점"
        - 예시: "시장 트렌드와 고객 데이터를 빠르게 학습하여 전략적 기획 능력을 향상시킬 잠재력"

        4. **부족한 부분 보완** (Optional)
        - 이전 면접에서 충분히 드러나지 않은 경험, 강점, 역량이 있다면 추가
        - 상황 면접 답변에서 새로 발견된 내용 위주로 작성
        - 예시: "프로젝트 관리 경험이 면접에서 충분히 강조되지 않아, 해당 역량을 추가"

        **작성 지침:**
        - 각 항목은 반드시 **한 문장으로 명확하게 작성**
        - 페르소나와 이전 분석 결과와 일관성 유지
        - 실제 답변과 사례에 기반하여 평가, 추측 금지
        - 보완 항목은 **필요할 때만** 추가
        - 기술 직군/비기술 직군 모두 적용 가능하도록 사례와 표현을 유연하게 선택
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
        model="gpt-4.1-mini",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(SituationalInterviewCardPart)

    return (prompt | llm).invoke({})


def generate_deep_dive_question(
    dominant_trait: str,
    dimension: str,
    qa_history: List[dict],
    use_langgraph_for_questions: Optional[bool] = None
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
    settings = get_settings()
    use_langgraph = (
        use_langgraph_for_questions
        if use_langgraph_for_questions is not None
        else settings.USE_LANGGRAPH_FOR_QUESTIONS
    )

    # LangGraph 사용 여부에 따라 분기
    if use_langgraph:
        # LangGraph 버전 (Generator → Validator → Conditional Edge)
        from ai.interview.talent.situational_graph import generate_deep_dive_question_with_graph

        return generate_deep_dive_question_with_graph(
            dominant_trait=dominant_trait,
            dimension=dimension,
            qa_history=qa_history
        )

    # 기존 LangChain 버전
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
        ("system", f"""당신은 인사팀 채용 담당자입니다.

        지원자의 [{dominant_trait}] 성향을 깊이 파악하기 위한 구체적인 심층 질문 1개를 생성하세요.

        이전 답변:
        {history_text}

        **심화 질문 생성 가이드:**
        - {dimension_map[dimension]} 차원에서 [{dominant_trait}] 성향을 더 깊이 확인
        - **실제 경험했던 구체적인 상황을 물어보기** (가정 질문이 아니라 과거 경험 질문)
        - 이전 답변에서 애매했던 부분을 명확히 하되, 이전과 비슷한 내용을 묻지 않기
        - **경험에서 어떤 고민을 했고, 왜 그렇게 행동했는지 의사결정 배경을 드러내도록 질문**
        - 예/아니오로 답할 수 없는 열린 질문
        - 특정 직군에 국한되지 않는 범용적인 경험 질문
        - 인터뷰 대상자가 이해하기 쉽고 자연스러운 질문
        - **질문 길이는 130자 이내로 간결하게 작성** 
        
        **예시:**
        - 주도형 → "팀이나 리더의 결정이 조직 목표와 맞지 않다고 느낄 때 어떻게 행동하시나요? 구체적인 사례를 들어 말씀해주세요."
        - 분석형 → "새로운 프로젝트나 문제를 맡았을 때, 문제의 원인을 분석하고 해결책을 설계한 경험이 있나요? 과정과 결과를 중심으로 말씀해주세요."
        - 협력형 → "팀 내 의견이 갈렸을 때, 다양한 관점을 조율하여 합의를 도출한 경험이 있나요? 실제 행동과 결과 중심으로 설명해주세요."
"""),
        ("user", f"[{dominant_trait}] 성향을 깊이 파악할 수 있는 '구체적인' 상황 질문 1개를 생성하세요.")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.5,
        api_key=settings.OPENAI_API_KEY
    )

    result = (prompt | llm).invoke({})
    return result.content


class SituationalInterview:
    """상황 면접 관리 클래스"""

    def __init__(self, use_langgraph_for_questions: Optional[bool] = None):
        # 상태
        self.current_question_num = 0  # 0부터 시작
        self.phase: Literal["exploration", "deep_dive", "validation"] = "exploration"
        settings = get_settings()
        self.use_langgraph_for_questions = (
            use_langgraph_for_questions
            if use_langgraph_for_questions is not None
            else settings.USE_LANGGRAPH_FOR_QUESTIONS
        )

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
                qa_history=self.qa_history,
                use_langgraph_for_questions=self.use_langgraph_for_questions
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
                "work_style": "우선순위가 다른 업무가 동시에 발생했을 때, 팀원들과 어떤 식으로 대응하는지 알려주세요.",
                "problem_solving": "처음 접하는 문제를 맞닥뜨릴 때, 문제 해결을 위해 어떤 방식으로 접근하시나요? 구체적인 사례를 중심으로 말씀해주세요.",
                "learning": "새로운 업무 방식이나 도구를 팀에 처음 도입해본 적이 있나요? 본인이 어떻게 조직에 기여했는지를 중심으로 설명해주세요.",
                "stress_response": "중요한 업무 직전에 예상치 못한 어려움이 발생한 적이 있나요? 어떻게 대응했는지 행동을 중심으로 설명해주세요.",
                "communication": "동료가 내 의견에 강하게 반대할 때 어떤 식으로 행동하시나요? 구체적인 행동과 결과 중심으로 말씀해주세요."
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
            model="gpt-4.1-mini",
            temperature=0.5,
            api_key=settings.OPENAI_API_KEY
        ).with_structured_output(FinalPersonaReport)

        return (prompt | llm).invoke({})
