"""
Company General Interview (기업 면접 - General 단계)

- 고정 질문 5개
- 순차 진행
- HR 관점: 회사 가치, 팀 문화, 이상적 인재상 파악
"""

from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ai.interview.company.models import CompanyGeneralAnalysis
from config.settings import get_settings


# General 고정 질문 (5개)
COMPANY_GENERAL_QUESTIONS = [
    "우리 팀/회사의 핵심 가치는 무엇인가요?",
    "어떤 인재를 채용하고 싶으신가요? (3-5가지 특징)",
    "팀의 업무 방식과 문화를 설명해주세요",
    "이번 채용을 통해 해결하고 싶은 문제는 무엇인가요?",
    "이 포지션에서 가장 중요하게 생각하는 인재상이나 가치관은 무엇인가요?"
]


class CompanyGeneralInterview:
    """기업 General 면접 관리 클래스"""

    def __init__(self, questions: Optional[List[str]] = None):
        """
        Args:
            questions: 커스텀 질문 리스트 (없으면 기본 질문 사용)
        """
        self.questions = questions or COMPANY_GENERAL_QUESTIONS
        self.current_index = 0
        self.answers = []

    def get_next_question(self) -> Optional[str]:
        """다음 질문 반환"""
        if self.current_index < len(self.questions):
            question = self.questions[self.current_index]
            self.current_index += 1
            return question
        return None

    def submit_answer(self, answer: str) -> dict:
        """답변 제출"""
        if self.current_index == 0:
            raise ValueError("질문을 먼저 받아야 합니다.")

        question = self.questions[self.current_index - 1]
        self.answers.append({
            "question": question,
            "answer": answer
        })

        # 다음 질문 가져오기
        next_q = self.get_next_question()

        return {
            "submitted": True,
            "question_number": self.current_index,
            "total_questions": len(self.questions),
            "next_question": next_q
        }

    def is_finished(self) -> bool:
        """모든 질문 완료 여부"""
        return self.current_index >= len(self.questions)

    def get_answers(self) -> List[dict]:
        """모든 Q&A 반환"""
        return self.answers


def analyze_company_general_interview(answers: List[dict]) -> CompanyGeneralAnalysis:
    """
    General 면접 답변 분석 (HR 관점)

    Args:
        answers: [{"question": str, "answer": str}, ...]

    Returns:
        CompanyGeneralAnalysis
    """
    # 모든 Q&A를 하나의 텍스트로 결합
    all_qa = "\n\n".join([
        f"질문: {a['question']}\n답변: {a['answer']}"
        for a in answers
    ])

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 HR 채용 전문가입니다.

기업 담당자의 면접 답변을 분석하여, 회사가 원하는 인재상과 팀 문화를 파악하세요.

**분석 목표:**
1. **core_values**: 회사/팀의 핵심 가치 (최대 5개)
2. **ideal_candidate_traits**: 이상적인 인재 특징 (3-5가지)
3. **team_culture**: 팀 문화 설명 (간결하게 2-3문장)
4. **work_style**: 팀의 업무 방식 (간결하게 2-3문장)
5. **hiring_reason**: 채용 이유/목적 (간결하게 2-3문장)

**중요:**
- 실제 답변에 있는 내용만 추출
- 추측하거나 과장하지 말 것
- 구체적이고 명확한 표현만 사용
- 다음 단계(Technical, Situational)에서 활용할 수 있도록 명확하게 작성
"""),
        ("user", all_qa)
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(CompanyGeneralAnalysis)

    return (prompt | llm).invoke({})
