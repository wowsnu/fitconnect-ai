"""
General Interview (구조화 면접)

- 고정 질문 5-7개
- 순차 진행
- 답변 분석으로 직무 면접 개인화
"""

from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ai.interview.models import GeneralInterviewAnalysis
from config.settings import get_settings


# 구조화 면접 고정 질문
GENERAL_QUESTIONS = [
    "간단한 자기소개와 함께, 최근 6개월 동안 가장 몰입했던 경험을 이야기해 주세요.",
    "가장 의미 있었던 프로젝트나 업무 경험을 말씀해 주세요. 맡으신 역할과 결과도 함께 알려주세요.",
    "팀원들과 협업할 때 본인만의 강점은 무엇이라고 생각하시나요?",
    "일을 할 때 가장 중요하게 생각하는 가치는 무엇인가요?",
    "앞으로 어떤 커리어를 그리고 계신가요?"
]


class GeneralInterview:
    """구조화 면접 관리 클래스"""

    def __init__(self, questions: Optional[List[str]] = None):
        """
        Args:
            questions: 커스텀 질문 리스트 (없으면 기본 질문 사용)
        """
        self.questions = questions or GENERAL_QUESTIONS
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

        # 다음 질문 가져오기 (current_index 증가됨)
        next_q = self.get_next_question()

        return {
            "submitted": True,
            "question_number": self.current_index,  # 이미 증가된 상태
            "total_questions": len(self.questions),
            "next_question": next_q
        }

    def is_finished(self) -> bool:
        """모든 질문 완료 여부"""
        return self.current_index >= len(self.questions)

    def get_answers(self) -> List[dict]:
        """모든 Q&A 반환"""
        return self.answers


def analyze_general_interview(answers: List[dict]) -> GeneralInterviewAnalysis:
    """
    구조화 면접 답변들을 종합 분석

    Args:
        answers: [{"question": str, "answer": str}, ...]

    Returns:
        GeneralInterviewAnalysis
    """
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

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(GeneralInterviewAnalysis)

    return (prompt | llm).invoke({})
