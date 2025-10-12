"""
Technical Interview (직무 적합성 면접)

- 3개 기술 × 3질문 = 9개 질문
- 구조화 면접 분석 결과 활용
- 개인화된 질문 생성
- 이전 답변 기반으로 자연스럽게 깊이 파고들기
- 점수 없음, 피드백만
"""

from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ai.interview.models import (
    CandidateProfile,
    GeneralInterviewAnalysis,
    InterviewQuestion,
    AnswerFeedback
)
from config.settings import get_settings


def generate_personalized_question(
    skill: str,
    question_number: int,  # 1, 2, 3 (해당 기술의 몇 번째 질문인지)
    profile: CandidateProfile,
    general_analysis: GeneralInterviewAnalysis,
    previous_skill_answers: List[dict] = None
) -> InterviewQuestion:
    """
    프로필 + 구조화 면접 분석 + 이전 답변을 조합한 개인화 질문 생성

    Args:
        skill: 평가할 기술 (예: "FastAPI", "PostgreSQL")
        question_number: 해당 기술의 몇 번째 질문인지 (1, 2, 3)
        profile: 지원자 프로필
        general_analysis: 구조화 면접 분석 결과
        previous_skill_answers: 현재 기술의 이전 답변들

    Returns:
        InterviewQuestion
    """
    previous_skill_answers = previous_skill_answers or []

    # 이전 답변 정리
    prev_context = ""
    if previous_skill_answers:
        prev_context = "\n\n**이전 질문과 답변:**\n"
        for i, ans in enumerate(previous_skill_answers, 1):
            prev_context += f"\n[질문 {i}] {ans['question']}\n"
            prev_context += f"[답변] {ans['answer']}\n"
            if ans.get('feedback'):
                depth_areas = ans['feedback'].get('depth_areas', [])
                if depth_areas:
                    prev_context += f"[파고들 포인트] {', '.join(depth_areas)}\n"

    # 질문 번호에 따른 가이드
    if question_number == 1:
        depth_guide = """**1번째 질문 (도입):**
- 구조화 면접에서 언급한 내용을 자연스럽게 연결
- 예: "아까 성능 최적화에 관심이 많다고 하셨는데, 이 기술에서는 어떤 경험이 있나요?"
- 전반적인 경험과 사용 사례 탐색"""
    elif question_number == 2:
        depth_guide = """**2번째 질문 (심화):**
- 1번째 답변에서 언급한 구체적인 기술/경험을 파고들기
- 예: 1번에서 "Redis 캐싱"을 언급했다면 → "Redis 캐싱 전략을 구체적으로 어떻게 설계하셨나요?"
- 실무 적용 방법, 문제 해결 과정 파악"""
    else:  # question_number == 3
        depth_guide = """**3번째 질문 (종합):**
- 1, 2번 답변을 종합하여 또 다른 주제로
- 아키텍처, 성능 최적화, 트레이드오프, 설계 결정
- 대규모 환경, 엣지 케이스, 실제 프로덕션 경험"""

    # 프로필에서 정보 추출
    job_category = profile.basic.tagline if profile.basic else "개발자"

    # 경력 정보에서 기술 스택 추출
    skills: List[str] = []
    for exp in profile.experiences:
        if exp.summary:
            # summary에서 기술 키워드 추출 (간단한 방식)
            skills.extend([kw.strip() for kw in exp.summary.split(',') if kw.strip()])

    # 자격증에서도 기술 추가
    skills.extend([cert.name for cert in profile.certifications])

    # 중복 제거 및 길이 제한
    unique_skills = sorted({skill for skill in skills if skill})
    skills = unique_skills[:10]

    # 총 경력 계산 (미기입 시 0으로 처리)
    total_experience = sum((exp.duration_years or 0) for exp in profile.experiences)

    # 경력사항 요약
    experience_entries = []
    for exp in profile.experiences:
        duration_text = f"{exp.duration_years}년" if exp.duration_years is not None else "기간 정보 없음"
        experience_entries.append(f"- {exp.company_name} / {exp.title} ({duration_text})")
    experience_summary = "\n".join(experience_entries)

    # 활동 요약
    activities_summary = "\n".join([
        f"- {act.name} ({act.category}): {act.description or ''}"
        for act in profile.activities
    ])

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""당신은 {job_category} 기술 면접관입니다.

**지원자 프로필:**
- 이름: {profile.basic.name if profile.basic else "지원자"}
- 직무: {job_category}
- 총 경력: {total_experience}년

**경력사항:**
{experience_summary}

**활동/프로젝트:**
{activities_summary}

**추출된 기술 키워드:**
{", ".join(skills) if skills else "정보 없음"}

**구조화 면접에서 파악된 특성:**
- 주요 테마: {", ".join(general_analysis.key_themes)}
- 관심 분야: {", ".join(general_analysis.interests)}
- 강조한 경험: {", ".join(general_analysis.emphasized_experiences)}
- 업무 스타일: {", ".join(general_analysis.work_style_hints)}
- 언급한 기술: {", ".join(general_analysis.technical_keywords)}

**질문 생성 전략:**

{depth_guide}

**중요 원칙:**
- 이전 답변에서 언급된 내용을 반드시 활용하여 자연스럽게 깊이 더하기
- 구체적이고 실무 중심
- 예/아니오로 답할 수 없는 열린 질문
- 지원자가 실제 경험을 말할 수 있도록 유도
"""),
        ("user", f"""
현재 평가 기술: {skill}
질문 번호: {question_number}/3
{prev_context}

{skill}에 대한 {question_number}번째 질문을 생성하세요.
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(InterviewQuestion)

    return (prompt | llm).invoke({})


def analyze_answer(
    question: str,
    answer: str,
    skill: str
) -> AnswerFeedback:
    """
    답변 분석 (점수 없음, 피드백만)

    Args:
        question: 질문
        answer: 답변
        skill: 기술

    Returns:
        AnswerFeedback
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""당신은 {skill} 기술 면접 분석 전문가입니다.

답변을 분석하여 다음 질문을 위한 인사이트를 제공하세요.

**분석 목표:**
1. 답변에서 언급된 주요 포인트 추출
2. 사용한 기술/도구 파악
3. 더 깊이 파고들 수 있는 영역 식별
4. 다음 질문 방향 제시

**중요:**
- 점수를 매기지 마세요
- 다음 질문이 무엇을 집중해야 할지 명확히 제시
- 답변에서 애매하거나 더 알아볼 부분 찾기
"""),
        ("user", f"""
질문: {question}
답변: {answer}

답변을 분석하고 피드백을 제공하세요.
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(AnswerFeedback)

    return (prompt | llm).invoke({})


class TechnicalInterview:
    """직무 적합성 면접 관리 클래스"""

    def __init__(
        self,
        profile: CandidateProfile,
        general_analysis: GeneralInterviewAnalysis,
        num_skills: int = 3,
        questions_per_skill: int = 3
    ):
        """
        Args:
            profile: 지원자 프로필
            general_analysis: 구조화 면접 분석 결과
            num_skills: 평가할 기술 개수 (기본 3개)
            questions_per_skill: 기술당 질문 수 (기본 3개)
        """
        self.profile = profile
        self.general_analysis = general_analysis
        self.questions_per_skill = questions_per_skill

        # 평가할 기술 선정
        self.skills = self._select_skills(num_skills)

        # 상태 관리
        self.current_skill_idx = 0
        self.current_question_num = 1  # 1, 2, 3

        # 결과 저장
        self.results = {skill: [] for skill in self.skills}
        self.current_question = None

    def _select_skills(self, num_skills: int) -> List[str]:
        """
        평가할 기술 선정

        우선순위:
        1. 구조화 면접에서 언급 + 프로필에 있는 기술
        2. 프로필에만 있는 기술
        """
        mentioned_skills = set(self.general_analysis.technical_keywords)

        # 프로필에서 기술 추출
        profile_skills = []

        # 경력 summary에서 추출
        for exp in self.profile.experiences:
            if exp.summary:
                profile_skills.extend([kw.strip() for kw in exp.summary.split(',') if kw.strip()])

        # 직무명(title)도 추가
        profile_skills.extend([exp.title for exp in self.profile.experiences])

        # 자격증도 추가
        profile_skills.extend([cert.name for cert in self.profile.certifications])

        # 중복 제거
        profile_skills = list(set(profile_skills))

        # 1순위: 언급된 기술
        priority_skills = [s for s in profile_skills if s in mentioned_skills]

        # 2순위: 프로필에만 있는 기술
        other_skills = [s for s in profile_skills if s not in mentioned_skills]

        # 합쳐서 num_skills개 선택
        selected = (priority_skills + other_skills)[:num_skills]

        # 만약 추출된 기술이 없으면 기본값
        if not selected:
            default_skills = ["직무 전반", "프로젝트 경험", "문제 해결 능력"]
            selected = default_skills[:num_skills]
        return selected

    def get_next_question(self) -> Optional[dict]:
        """
        다음 질문 생성

        Returns:
            {
                "skill": str,
                "question_number": int,
                "question": str,
                "why": str,
                "progress": str
            }
        """
        if self.is_finished():
            return None

        skill = self.skills[self.current_skill_idx]

        # 현재 기술의 이전 답변들
        previous_answers = self.results[skill]

        # LLM으로 개인화된 질문 생성
        question_obj = generate_personalized_question(
            skill=skill,
            question_number=self.current_question_num,
            profile=self.profile,
            general_analysis=self.general_analysis,
            previous_skill_answers=previous_answers
        )

        self.current_question = {
            "skill": skill,
            "question_number": self.current_question_num,
            "question": question_obj.question,
            "why": question_obj.why
        }

        total_questions = len(self.skills) * self.questions_per_skill
        return {
            **self.current_question,
            "progress": f"{self.get_total_answered() + 1}/{total_questions}"
        }

    def submit_answer(self, answer: str) -> dict:
        """
        답변 제출 및 분석

        Args:
            answer: 답변 텍스트

        Returns:
            {
                "feedback": dict,
                "next_question": dict or None
            }
        """
        if not self.current_question:
            raise ValueError("질문을 먼저 받아야 합니다.")

        skill = self.current_question["skill"]
        question = self.current_question["question"]

        # LLM 분석 (점수 없음)
        feedback = analyze_answer(
            question=question,
            answer=answer,
            skill=skill
        )

        # 결과 저장
        self.results[skill].append({
            "question_number": self.current_question_num,
            "question": question,
            "answer": answer,
            "feedback": {
                "key_points": feedback.key_points,
                "mentioned_technologies": feedback.mentioned_technologies,
                "depth_areas": feedback.depth_areas,
                "follow_up_direction": feedback.follow_up_direction
            }
        })

        # 다음 상태로 이동
        self._move_next()

        return {
            "feedback": {
                "key_points": feedback.key_points,
                "depth_areas": feedback.depth_areas
            },
            "next_question": self.get_next_question()
        }

    def _move_next(self):
        """다음 질문으로 상태 이동"""
        self.current_question_num += 1

        # 한 기술의 질문 완료?
        if self.current_question_num > self.questions_per_skill:
            self.current_question_num = 1
            self.current_skill_idx += 1

        self.current_question = None

    def is_finished(self) -> bool:
        """모든 면접 완료 여부"""
        return self.current_skill_idx >= len(self.skills)

    def get_total_answered(self) -> int:
        """총 답변 개수"""
        return sum(len(answers) for answers in self.results.values())

    def get_results(self) -> dict:
        """최종 결과 반환 (점수 없음)"""
        return {
            "skills_evaluated": self.skills,
            "results": self.results,
            "total_questions": self.get_total_answered()
        }
