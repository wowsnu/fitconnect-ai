"""
Company Situational Interview (기업 면접 - Situational 단계)

- 고정 질문 5개
- 실시간 추천 질문 3개 (답변 분석 후 동적 생성)
- 팀 문화 & 적합 인재상 구체화
"""

from typing import List, Optional, Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ai.interview.company.models import (
    CompanyGeneralAnalysis,
    TechnicalRequirements,
    TeamCultureProfile,
    RecommendedQuestions,
    CompanyInterviewQuestion
)
from config.settings import get_settings


# Situational 고정 질문 (5개)
COMPANY_SITUATIONAL_QUESTIONS = [
    "팀 내 업무 분담과 의사결정 방식은 어떻게 이루어지나요?",
    "팀의 핵심 가치나 업무 철학은 무엇인가요?",
    "팀에서 성과가 뛰어난 구성원은 어떤 특징을 가지고 있나요?",
    "팀 내에서 의견 충돌이나 갈등이 생기면 주로 어떻게 해결되나요?",
    "팀원들에게 기대하는 업무 스타일이나 협업 방식은 무엇인가요?",
]


class CompanySituationalInterview:
    """기업 Situational 면접 관리 클래스"""

    def __init__(
        self,
        general_analysis: CompanyGeneralAnalysis,
        technical_requirements: TechnicalRequirements,
        company_info: Optional[dict] = None,
        questions: Optional[List[str]] = None,
        use_langgraph_for_questions: Optional[bool] = None
    ):
        """
        Args:
            general_analysis: General 면접 분석 결과
            technical_requirements: Technical 면접 분석 결과
            company_info: 기업 기본 정보 (선택) - culture, vision_mission 등
            questions: 커스텀 질문 리스트 (없으면 기본 질문 사용)
        """
        settings = get_settings()
        self.general_analysis = general_analysis
        self.technical_requirements = technical_requirements
        self.company_info = company_info or {}
        self.fixed_questions = questions or COMPANY_SITUATIONAL_QUESTIONS
        self.current_index = 0
        self.answers = []
        self.dynamic_questions = []
        self.use_langgraph_for_questions = (
            use_langgraph_for_questions
            if use_langgraph_for_questions is not None
            else settings.USE_LANGGRAPH_FOR_QUESTIONS
        )

    def get_next_question(self) -> Optional[Dict]:
        """다음 질문 반환 (고정 또는 동적)"""
        # 1. 고정 질문 먼저
        if self.current_index < len(self.fixed_questions):
            question = self.fixed_questions[self.current_index]
            self.current_index += 1
            return {
                "question": question,
                "type": "fixed",
                "number": self.current_index,
                "total_fixed": 8  # 총 8개로 고정
            }

        # 2. 고정 질문 완료 후 동적 질문
        dynamic_index = self.current_index - len(self.fixed_questions)
        if dynamic_index < len(self.dynamic_questions):
            question = self.dynamic_questions[dynamic_index]
            self.current_index += 1
            return {
                "question": question.question,
                "type": "dynamic",
                "purpose": question.purpose,
                "number": self.current_index,
                "total_fixed": 8  # 총 8개로 고정
            }

        return None

    def submit_answer(self, answer: str) -> dict:
        """답변 제출"""
        if self.current_index == 0:
            raise ValueError("질문을 먼저 받아야 합니다.")

        # 현재 답변 저장
        current_question_index = self.current_index - 1

        if current_question_index < len(self.fixed_questions):
            question = self.fixed_questions[current_question_index]
            question_type = "fixed"
        else:
            dynamic_index = current_question_index - len(self.fixed_questions)
            question = self.dynamic_questions[dynamic_index].question
            question_type = "dynamic"

        self.answers.append({
            "question": question,
            "answer": answer,
            "type": question_type
        })

        # 고정 질문 모두 완료 시 실시간 질문 생성
        if self.current_index == len(self.fixed_questions):
            print(f"[INFO] Situational fixed questions completed ({len(self.fixed_questions)}). Generating dynamic questions...")
            self._generate_dynamic_questions()
            print(f"[INFO] Situational generated {len(self.dynamic_questions)} dynamic questions")

        # 다음 질문 가져오기
        next_q = self.get_next_question()

        # 총 질문 수는 항상 8개로 고정 (고정 5 + 동적 3)
        total_q = 8
        # is_finished는 next_q가 None인지로 판단 (더 정확함)
        is_done = next_q is None
        print(f"[DEBUG] Situational - current_index: {self.current_index}, total_questions: {total_q}, is_finished: {is_done}, next_question: {next_q is not None}")

        return {
            "submitted": True,
            "question_number": self.current_index,
            "total_questions": total_q,
            "next_question": next_q,
            "is_finished": is_done  # is_finished 추가
        }

    def _generate_dynamic_questions(self):
        """실시간 추천 질문 생성 (정확히 3개)"""
        # 고정 질문 답변만 사용
        fixed_answers = [a for a in self.answers if a["type"] == "fixed"]

        # LangGraph 사용 여부에 따라 분기
        if self.use_langgraph_for_questions:
            # LangGraph 버전 (Generator → Validator → Conditional Edge)
            from ai.interview.company.situational_graph import generate_situational_dynamic_questions

            questions = generate_situational_dynamic_questions(
                general_analysis=self.general_analysis,
                technical_requirements=self.technical_requirements,
                fixed_answers=fixed_answers,
                company_info=self.company_info
            )
            self.dynamic_questions = questions
        else:
            # 기존 LangChain 버전
            all_qa = "\n\n".join([
                f"질문: {a['question']}\n답변: {a['answer']}"
                for a in fixed_answers
            ])

            # 이전 단계 분석 결과 요약
            context = f"""
[General 면접 분석 결과]
- 핵심 가치: {', '.join(self.general_analysis.core_values)}
- 이상적 인재: {', '.join(self.general_analysis.ideal_candidate_traits)}
- 팀 문화: {self.general_analysis.team_culture}

[Technical 면접 분석 결과]
- 직무: {self.technical_requirements.job_title}
- 필수 역량: {', '.join(self.technical_requirements.required_skills)}
- 예상 도전: {self.technical_requirements.expected_challenges}
"""

            # 기업 정보 추가
            company_context = ""
            if self.company_info:
                company_parts = []
                if self.company_info.get("culture"):
                    company_parts.append(f"- 조직 문화: {self.company_info['culture']}")
                if self.company_info.get("vision_mission"):
                    company_parts.append(f"- 비전/미션: {self.company_info['vision_mission']}")

                if company_parts:
                    company_context = "\n[기업 정보]\n" + "\n".join(company_parts) + "\n"

            prompt = ChatPromptTemplate.from_messages([
                ("system", """당신은 인사팀 채용 담당자로, 공고(포지션)에 대한 정보를 자세히 파악하고자 실무진 부서와 인터뷰 중입니다.

질문과 답변 내용을 분석하여, Culture Fit(팀 핏)을 구체화할 수 있는 follow-up 질문을 정확히 3개 생성하세요.

**목표:**
- **해당 팀**을 위한 질문으로, 팀 문화 이해를 위해 실무진에게 던지는 질문
- 답변에서 언급된 팀 특성을 더 구체화
- 적합한 인재상을 명확히 정의
- General/Technical 결과와 일관성 확인

**질문 예시:**
- "팀에서 주도적으로 아이디어를 제안하고 실행하는 문화가 있나요?"
- "팀이 추구하는 가치나 행동 기준은 무엇이며, 후보자에게 요구되는 성향은 무엇인가요?"
- "팀은 수직적인 보고 구조인가요, 아니면 수평적인 협업 구조인가요?"

**중요:**
- 모든 질문을 한글로만 작성하세요 (영어 질문 금지)
- 실제 답변 내용을 바탕으로 질문 생성
- 팀 문화와 직무 특성을 연결하여 질문
- 정확히 3개의 질문만 생성
"""),
                ("user", f"{context}{company_context}\n[Situational 고정 질문 답변]\n{all_qa}")
            ])

            settings = get_settings()
            llm = ChatOpenAI(
                model="gpt-4.1-mini",
                temperature=0.5,
                api_key=settings.OPENAI_API_KEY
            ).with_structured_output(RecommendedQuestions)

            result = (prompt | llm).invoke({})
            self.dynamic_questions = result.questions

    def is_finished(self) -> bool:
        """모든 질문 완료 여부"""
        # 총 8개 고정 (고정 5 + 동적 3)
        return self.current_index >= 8

    def get_answers(self) -> List[dict]:
        """모든 Q&A 반환"""
        return self.answers


def analyze_company_situational_interview(
    answers: List[dict],
    general_analysis: CompanyGeneralAnalysis,
    technical_requirements: TechnicalRequirements
) -> TeamCultureProfile:
    """
    Situational 면접 답변 분석

    Args:
        answers: [{"question": str, "answer": str, "type": str}, ...]
        general_analysis: General 면접 분석 결과
        technical_requirements: Technical 면접 분석 결과

    Returns:
        TeamCultureProfile
    """
    all_qa = "\n\n".join([
        f"질문: {a['question']}\n답변: {a['answer']}"
        for a in answers
    ])

    context = f"""
[General 면접 분석 결과]
- 핵심 가치: {', '.join(general_analysis.core_values)}
- 이상적 인재: {', '.join(general_analysis.ideal_candidate_traits)}
- 팀 문화: {general_analysis.team_culture}

[Technical 면접 분석 결과]
- 직무: {technical_requirements.job_title}
- 예상 도전: {technical_requirements.expected_challenges}
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 인사팀 채용 담당자로, 공고(포지션)에 대한 정보를 자세히 파악하고자 실무진 부서와 인터뷰를 진행했습니다.

        Situational 면접 답변을 분석하여, 팀 문화와 적합한 인재상을 정의하세요.

        **추출 목표:**
        1. **team_situation**: 팀 현황 (성장기, 안정기 등) - 2-3문장
        2. **collaboration_style**: 선호하는 협업 스타일 - 2-3문장
        3. **conflict_resolution**: 갈등 해결 방식 - 2-3문장
        4. **work_environment**: 업무 환경 특성 - 2-3문장
        5. **preferred_work_style**: 선호하는 업무 스타일 - 2-3문장

        **중요:**
        - 실제 답변에 있는 내용만 추출
        - General/Technical 결과와 일관성 유지
        - 구체적이고 명확한 표현 사용
        - 채용 공고의 "인재상" 섹션에 활용될 내용
        """),
        ("user", f"{context}\n\n[Situational (문화 적합성) 면접 답변]\n{all_qa}")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(TeamCultureProfile)

    return (prompt | llm).invoke({})
