"""
Company Technical Interview (기업 면접 - Technical 단계)

- 고정 질문 5개
- 실시간 추천 질문 2-3개 (답변 분석 후 동적 생성)
- 직무 적합성: 필수/우대 역량, 주요 업무 정의
"""

from typing import List, Optional, Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ai.interview.company_models import (
    CompanyGeneralAnalysis,
    TechnicalRequirements,
    RecommendedQuestions,
    CompanyInterviewQuestion
)
from config.settings import get_settings


# Technical 고정 질문 (5개)
COMPANY_TECHNICAL_QUESTIONS = [
    "이 포지션에서 수행할 주요 업무는 무엇인가요?",
    "필수로 갖춰야 할 기술/역량은 무엇인가요?",
    "우대하는 기술/역량이 있다면 무엇인가요?",
    "이 포지션에서 뛰어난 성과를 낸 직원은 어떤 특징을 가지고 있었나요? (새롭게 만들어진 포지션이라면, 해당 포지션이 만들어진 이유를 알려주세요.)",
    "이 포지션에서 예상되는 어려움이나 도전 과제는 무엇인가요?"
]


class CompanyTechnicalInterview:
    """기업 Technical 면접 관리 클래스"""

    def __init__(
        self,
        general_analysis: CompanyGeneralAnalysis,
        existing_jd: Optional[str] = None,
        questions: Optional[List[str]] = None
    ):
        """
        Args:
            general_analysis: General 면접 분석 결과
            existing_jd: 기존 Job Description (선택)
            questions: 커스텀 질문 리스트 (없으면 기본 질문 사용)
        """
        self.general_analysis = general_analysis
        self.existing_jd = existing_jd
        self.fixed_questions = questions or COMPANY_TECHNICAL_QUESTIONS
        self.current_index = 0
        self.answers = []
        self.dynamic_questions = []  # 실시간 생성된 질문들

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

        # General 분석 결과 요약
        general_summary = f"""
[General 면접 분석 결과]
- 핵심 가치: {', '.join(self.general_analysis.core_values)}
- 이상적 인재: {', '.join(self.general_analysis.ideal_candidate_traits)}
- 팀 문화: {self.general_analysis.team_culture}
- 업무 방식: {self.general_analysis.work_style}
"""

        # 기존 JD가 있으면 추가
        jd_context = ""
        if self.existing_jd:
            jd_context = f"\n[기존 Job Description]\n{self.existing_jd}\n"

        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 HR 채용 전문가입니다.

Technical 면접의 고정 질문 답변을 분석하여, 더 구체적으로 파고들 수 있는 follow-up 질문을 2-3개 생성하세요.

**목표:**
- 답변이 모호하거나 추상적인 부분을 구체화
- 필수 역량의 수준을 명확히 파악
- 기대 성과나 업무 범위를 더 명확히 정의
- General 분석 결과와 연결하여 일관성 확인

**질문 예시:**
- "React를 어느 정도 수준까지 다룰 수 있어야 하나요?"
- "신입 팀원이 익혀야 할 기술 스택은 얼마나 되나요?"
- "온보딩 기간은 어느 정도 예상하시나요?"

**중요:**
- 실제 답변 내용을 바탕으로 질문 생성
- 추측하지 말고, 명확히 할 필요가 있는 부분만 질문
- 2-3개의 질문만 생성 (너무 많으면 부담)
"""),
            ("user", f"{general_summary}\n{jd_context}\n[Technical 고정 질문 답변]\n{all_qa}")
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


def analyze_company_technical_interview(
    answers: List[dict],
    general_analysis: CompanyGeneralAnalysis
) -> TechnicalRequirements:
    """
    Technical 면접 답변 분석

    Args:
        answers: [{"question": str, "answer": str, "type": str}, ...]
        general_analysis: General 면접 분석 결과

    Returns:
        TechnicalRequirements
    """
    all_qa = "\n\n".join([
        f"질문: {a['question']}\n답변: {a['answer']}"
        for a in answers
    ])

    general_summary = f"""
[General 면접 분석 결과]
- 핵심 가치: {', '.join(general_analysis.core_values)}
- 이상적 인재: {', '.join(general_analysis.ideal_candidate_traits)}
- 채용 이유: {general_analysis.hiring_reason}
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 HR 채용 전문가입니다.

Technical 면접 답변을 분석하여, 채용 공고에 들어갈 직무 정보를 추출하세요.

**추출 목표:**
1. **job_title**: 직무명 (명확하게)
2. **main_responsibilities**: 주요 업무 **정확히 4개** (구체적으로)
3. **required_skills**: 필수 역량 **정확히 4개** (명확한 수준 포함)
4. **preferred_skills**: 우대 역량 **정확히 4개** (우대 사항)
5. **expected_challenges**: 예상되는 어려움/도전 과제 (2-3문장)

**중요:**
- 실제 답변에 있는 내용만 추출
- main_responsibilities, required_skills, preferred_skills는 **반드시 정확히 4개씩**
- 구체적이고 명확한 표현 사용
- General 면접 결과와 일관성 유지
"""),
        ("user", f"{general_summary}\n\n[Technical 면접 답변]\n{all_qa}")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(TechnicalRequirements)

    return (prompt | llm).invoke({})
