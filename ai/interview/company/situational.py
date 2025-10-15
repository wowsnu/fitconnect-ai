"""
Company Situational Interview (기업 면접 - Situational 단계)

- 고정 질문 5개
- 실시간 추천 질문 2-3개 (답변 분석 후 동적 생성)
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
    "현재 팀의 상황은 어떤가요? (성장기, 안정기 등)",
    "팀에서 잘 맞는 성향이나 협업 스타일은 어떤 것인가요?",
    "팀 내에서 의견 충돌이 있을 때 어떻게 해결하나요?",
    "빠르게 변화하는 환경 vs 안정적인 환경, 우리 팀은?",
    "독립적으로 일하는 사람 vs 협업하는 사람, 어떤 게 더 필요한가요?"
]


class CompanySituationalInterview:
    """기업 Situational 면접 관리 클래스"""

    def __init__(
        self,
        general_analysis: CompanyGeneralAnalysis,
        technical_requirements: TechnicalRequirements,
        company_info: Optional[dict] = None,
        questions: Optional[List[str]] = None
    ):
        """
        Args:
            general_analysis: General 면접 분석 결과
            technical_requirements: Technical 면접 분석 결과
            company_info: 기업 기본 정보 (선택) - culture, vision_mission 등
            questions: 커스텀 질문 리스트 (없으면 기본 질문 사용)
        """
        self.general_analysis = general_analysis
        self.technical_requirements = technical_requirements
        self.company_info = company_info or {}
        self.fixed_questions = questions or COMPANY_SITUATIONAL_QUESTIONS
        self.current_index = 0
        self.answers = []
        self.dynamic_questions = []

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
                "total_fixed": len(self.fixed_questions)
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
                "total_fixed": len(self.fixed_questions)
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
            self._generate_dynamic_questions()

        # 다음 질문 가져오기
        next_q = self.get_next_question()

        return {
            "submitted": True,
            "question_number": self.current_index,
            "total_questions": len(self.fixed_questions) + len(self.dynamic_questions),
            "next_question": next_q
        }

    def _generate_dynamic_questions(self):
        """실시간 추천 질문 생성 (2-3개)"""
        # 고정 질문 답변만 사용
        fixed_answers = [a for a in self.answers if a["type"] == "fixed"]

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
            ("system", """당신은 HR 채용 전문가입니다.

Situational 면접의 고정 질문 답변을 분석하여, 팀 핏을 더 구체화할 수 있는 follow-up 질문을 2-3개 생성하세요.

**목표:**
- 답변에서 언급된 팀 특성을 더 구체화
- 적합한 인재상을 명확히 정의
- General/Technical 결과와 일관성 확인

**질문 예시:**
- "빠른 변화에 적응하는 능력이 중요할까요?"
- "주니어가 시니어에게 의견을 제시하는 것을 환영하시나요?"
- "원격 근무 상황에서도 협업이 원활한 사람을 찾으시나요?"

**중요:**
- 실제 답변 내용을 바탕으로 질문 생성
- 팀 문화와 직무 특성을 연결하여 질문
- 2-3개의 질문만 생성
"""),
            ("user", f"{context}{company_context}\n[Situational 고정 질문 답변]\n{all_qa}")
        ])

        settings = get_settings()
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.5,
            api_key=settings.OPENAI_API_KEY
        ).with_structured_output(RecommendedQuestions)

        result = (prompt | llm).invoke({})
        self.dynamic_questions = result.questions

    def is_finished(self) -> bool:
        """모든 질문 완료 여부"""
        total_questions = len(self.fixed_questions) + len(self.dynamic_questions)
        return self.current_index >= total_questions

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
        ("system", """당신은 HR 채용 전문가입니다.

Situational 면접 답변을 분석하여, 팀 문화와 적합한 인재상을 정의하세요.

**추출 목표:**
1. **team_situation**: 팀 현황 (성장기, 안정기 등) - 2-3문장
2. **collaboration_style**: 선호하는 협업 스타일 - 2-3문장
3. **conflict_resolution**: 갈등 해결 방식 - 2-3문장
4. **work_environment**: 업무 환경 특성 (변화 vs 안정) - 2-3문장
5. **preferred_work_style**: 선호하는 업무 스타일 (독립 vs 협업) - 2-3문장

**중요:**
- 실제 답변에 있는 내용만 추출
- General/Technical 결과와 일관성 유지
- 구체적이고 명확한 표현 사용
- 채용 공고의 "인재상" 섹션에 활용될 내용
"""),
        ("user", f"{context}\n\n[Situational 면접 답변]\n{all_qa}")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(TeamCultureProfile)

    return (prompt | llm).invoke({})
