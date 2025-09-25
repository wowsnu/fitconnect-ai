"""
Pure Python AI Interview service - 완전 독립적인 AI 모듈
STT + LLM을 통합한 인터뷰 시스템
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import json

# 순수 AI 서비스들 import
from ai.stt.pure_service import get_stt_service, PureSTTService
from ai.llm.pure_service import get_llm_service, PureLLMService, ChatMessage

logger = logging.getLogger(__name__)


class InterviewType(str, Enum):
    """인터뷰 유형"""
    CANDIDATE_COMPETENCY = "candidate_competency"
    JOB_REQUIREMENT = "job_requirement"
    GENERAL = "general"


class InterviewPhase(str, Enum):
    """인터뷰 진행 단계"""
    INTRODUCTION = "introduction"
    MAIN_QUESTIONS = "main_questions"
    FOLLOW_UP = "follow_up"
    CLOSING = "closing"
    COMPLETED = "completed"


@dataclass
class InterviewSession:
    """인터뷰 세션"""
    session_id: str
    interview_type: InterviewType
    participant_id: str
    current_phase: InterviewPhase
    questions: List[Dict[str, Any]] = field(default_factory=list)
    responses: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PureInterviewService:
    """순수 Python AI 인터뷰 서비스"""

    def __init__(self, stt_service: Optional[PureSTTService] = None, llm_service: Optional[PureLLMService] = None):
        """
        Args:
            stt_service: STT 서비스 (None이면 기본 서비스)
            llm_service: LLM 서비스 (None이면 기본 서비스)
        """
        self.stt_service = stt_service or get_stt_service()
        self.llm_service = llm_service or get_llm_service()
        self.active_sessions: Dict[str, InterviewSession] = {}
        self.interview_templates = self._load_interview_templates()

    def _load_interview_templates(self) -> Dict[InterviewType, Dict[str, Any]]:
        """인터뷰 템플릿 로드"""
        return {
            InterviewType.CANDIDATE_COMPETENCY: {
                "introduction": "안녕하세요! 지금부터 역량 분석을 위한 AI 인터뷰를 시작하겠습니다. 편안하게 답변해 주세요.",
                "phases": [
                    {
                        "phase": "introduction",
                        "questions": [
                            "먼저 간단한 자기소개를 부탁드립니다.",
                            "현재 어떤 분야에서 일하고 계신가요?"
                        ]
                    },
                    {
                        "phase": "main_questions",
                        "questions": [
                            "지금까지 가장 기억에 남는 프로젝트나 업무 경험을 자세히 설명해 주세요.",
                            "그 프로젝트에서 어떤 어려움이 있었고, 어떻게 해결하셨나요?",
                            "팀워크가 중요했던 상황에서의 경험을 말씀해 주세요.",
                            "앞으로 어떤 분야에서 성장하고 싶으신가요?"
                        ]
                    },
                    {
                        "phase": "follow_up",
                        "questions": [
                            "추가로 궁금한 점이 있다면 자유롭게 말씀해 주세요."
                        ]
                    }
                ]
            },
            InterviewType.JOB_REQUIREMENT: {
                "introduction": "안녕하세요! 채용 공고 분석을 위한 AI 인터뷰를 시작하겠습니다.",
                "phases": [
                    {
                        "phase": "introduction",
                        "questions": [
                            "회사와 해당 포지션에 대해 간단히 소개해 주세요.",
                            "이번에 채용하고자 하는 역할의 주요 업무는 무엇인가요?"
                        ]
                    },
                    {
                        "phase": "main_questions",
                        "questions": [
                            "이상적인 지원자는 어떤 기술적 역량을 가져야 한다고 생각하시나요?",
                            "팀에서 선호하는 업무 스타일이나 소통 방식이 있나요?",
                            "신입사원과 경력직 중 어느 쪽을 우선시하는지, 그 이유는 무엇인가요?",
                            "회사의 문화나 가치관 중에서 특히 중요하게 생각하는 부분은 무엇인가요?"
                        ]
                    }
                ]
            },
            InterviewType.GENERAL: {
                "introduction": "안녕하세요! 일반 인터뷰를 시작하겠습니다.",
                "phases": [
                    {
                        "phase": "introduction",
                        "questions": ["간단한 자기소개 부탁드립니다."]
                    },
                    {
                        "phase": "main_questions",
                        "questions": [
                            "본인의 강점은 무엇이라고 생각하시나요?",
                            "가장 자랑스러운 성취는 무엇인가요?",
                            "앞으로의 목표는 무엇인가요?"
                        ]
                    }
                ]
            }
        }

    def start_interview(
        self,
        participant_id: str,
        interview_type: Union[InterviewType, str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> InterviewSession:
        """
        인터뷰 세션 시작

        Args:
            participant_id: 참가자 ID
            interview_type: 인터뷰 유형
            metadata: 추가 메타데이터

        Returns:
            InterviewSession 객체
        """
        session_id = str(uuid.uuid4())

        # InterviewType 변환
        if isinstance(interview_type, str):
            interview_type = InterviewType(interview_type)

        session = InterviewSession(
            session_id=session_id,
            interview_type=interview_type,
            participant_id=participant_id,
            current_phase=InterviewPhase.INTRODUCTION,
            metadata=metadata or {}
        )

        self.active_sessions[session_id] = session

        logger.info(f"Started interview session {session_id} for participant {participant_id}")
        return session

    def get_next_question(self, session_id: str) -> Optional[str]:
        """
        다음 질문 가져오기

        Args:
            session_id: 인터뷰 세션 ID

        Returns:
            다음 질문 또는 None (인터뷰 완료시)
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        template = self.interview_templates[session.interview_type]

        # 현재 단계의 질문들 가져오기
        current_phase_questions = []
        for phase_config in template["phases"]:
            if phase_config["phase"] == session.current_phase.value:
                current_phase_questions = phase_config["questions"]
                break

        # 현재 단계에서 답변한 질문 수
        answered_in_current_phase = len([
            q for q in session.questions
            if q.get("phase") == session.current_phase.value
        ])

        # 단계 전환 필요시
        if answered_in_current_phase >= len(current_phase_questions):
            session = self._advance_phase(session)
            if session.current_phase == InterviewPhase.COMPLETED:
                return None

            # 새 단계의 질문들 가져오기
            for phase_config in template["phases"]:
                if phase_config["phase"] == session.current_phase.value:
                    current_phase_questions = phase_config["questions"]
                    break
            answered_in_current_phase = 0

        # 다음 질문 반환
        if answered_in_current_phase < len(current_phase_questions):
            next_question = current_phase_questions[answered_in_current_phase]

            # 질문을 세션에 추가
            question_data = {
                "question": next_question,
                "phase": session.current_phase.value,
                "asked_at": datetime.now(),
                "question_id": str(uuid.uuid4())
            }
            session.questions.append(question_data)
            session.updated_at = datetime.now()

            return next_question

        return None

    def _advance_phase(self, session: InterviewSession) -> InterviewSession:
        """인터뷰 단계 진행"""
        if session.current_phase == InterviewPhase.INTRODUCTION:
            session.current_phase = InterviewPhase.MAIN_QUESTIONS
        elif session.current_phase == InterviewPhase.MAIN_QUESTIONS:
            session.current_phase = InterviewPhase.FOLLOW_UP
        elif session.current_phase == InterviewPhase.FOLLOW_UP:
            session.current_phase = InterviewPhase.CLOSING
        else:
            session.current_phase = InterviewPhase.COMPLETED

        return session

    def process_audio_response(
        self,
        session_id: str,
        audio_data: bytes,
        filename: str = "response.wav",
        question_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        오디오 응답 처리 (STT + LLM 분석)

        Args:
            session_id: 인터뷰 세션 ID
            audio_data: 오디오 데이터 바이트
            filename: 파일명 (확장자 확인용)
            question_id: 질문 ID (옵션)

        Returns:
            처리 결과 딕셔너리
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        try:
            # STT로 음성 인식
            transcription, stt_metadata = self.stt_service.transcribe_bytes(
                audio_data, filename
            )

            # 질문 ID 찾기
            if not question_id and session.questions:
                question_id = session.questions[-1].get("question_id")

            # LLM으로 응답 분석
            analysis = self._analyze_response(
                transcription,
                session.interview_type,
                session.current_phase
            )

            # 응답 저장
            response_data = {
                "response_id": str(uuid.uuid4()),
                "question_id": question_id,
                "transcription": transcription,
                "analysis": analysis,
                "stt_metadata": stt_metadata,
                "responded_at": datetime.now(),
                "phase": session.current_phase.value
            }

            session.responses.append(response_data)
            session.updated_at = datetime.now()

            logger.info(f"Processed audio response for session {session_id}")

            return {
                "transcription": transcription,
                "analysis": analysis,
                "metadata": stt_metadata
            }

        except Exception as e:
            logger.error(f"Error processing audio response: {e}")
            raise RuntimeError(f"Failed to process audio response: {str(e)}")

    def process_text_response(
        self,
        session_id: str,
        response_text: str,
        question_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        텍스트 응답 처리 (LLM 분석만)

        Args:
            session_id: 인터뷰 세션 ID
            response_text: 응답 텍스트
            question_id: 질문 ID (옵션)

        Returns:
            분석 결과 딕셔너리
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        try:
            # 질문 ID 찾기
            if not question_id and session.questions:
                question_id = session.questions[-1].get("question_id")

            # LLM으로 응답 분석
            analysis = self._analyze_response(
                response_text,
                session.interview_type,
                session.current_phase
            )

            # 응답 저장
            response_data = {
                "response_id": str(uuid.uuid4()),
                "question_id": question_id,
                "transcription": response_text,
                "analysis": analysis,
                "responded_at": datetime.now(),
                "phase": session.current_phase.value,
                "input_type": "text"
            }

            session.responses.append(response_data)
            session.updated_at = datetime.now()

            return {
                "transcription": response_text,
                "analysis": analysis
            }

        except Exception as e:
            logger.error(f"Error processing text response: {e}")
            raise RuntimeError(f"Failed to process text response: {str(e)}")

    def _analyze_response(
        self,
        response_text: str,
        interview_type: InterviewType,
        phase: InterviewPhase
    ) -> Dict[str, Any]:
        """응답 분석 (LLM 사용)"""
        if interview_type == InterviewType.CANDIDATE_COMPETENCY:
            system_prompt = """
            당신은 채용 전문가입니다. 지원자의 답변을 분석하여 다음 항목을 평가해주세요:
            1. 기술적 역량
            2. 소프트 스킬
            3. 문제해결 능력
            4. 커뮤니케이션 스킬
            5. 성장 잠재력

            JSON 형식으로 구조화된 분석 결과를 제공해주세요.
            """
        elif interview_type == InterviewType.JOB_REQUIREMENT:
            system_prompt = """
            당신은 채용 컨설턴트입니다. 기업 담당자의 답변을 분석하여 다음을 추출해주세요:
            1. 필요한 기술 스킬
            2. 경력 요구사항
            3. 선호하는 인재상
            4. 회사 문화
            5. 업무 환경

            JSON 형식으로 구조화된 분석 결과를 제공해주세요.
            """
        else:
            system_prompt = "답변을 분석하고 요약해주세요."

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"분석할 답변: {response_text}")
        ]

        try:
            llm_response = self.llm_service.generate_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )

            # JSON 파싱 시도
            try:
                analysis = json.loads(llm_response.content)
            except json.JSONDecodeError:
                analysis = {"summary": llm_response.content}

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing response: {e}")
            return {"error": "분석 중 오류가 발생했습니다.", "raw_content": response_text}

    def generate_follow_up_question(
        self,
        session_id: str,
        context: Optional[str] = None
    ) -> Optional[str]:
        """
        후속 질문 생성

        Args:
            session_id: 인터뷰 세션 ID
            context: 추가 컨텍스트

        Returns:
            생성된 후속 질문
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if not session.responses:
            return None

        # 최근 응답들 가져오기
        recent_responses = session.responses[-3:]
        response_texts = [r["transcription"] for r in recent_responses]

        system_prompt = f"""
        당신은 면접관입니다. 지원자의 이전 답변들을 바탕으로 더 깊이 있는 후속 질문을 하나 생성해주세요.

        인터뷰 유형: {session.interview_type.value}
        현재 단계: {session.current_phase.value}

        질문은 구체적이고 통찰력 있어야 하며, 한국어로 작성해주세요.
        """

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"이전 답변들: {' | '.join(response_texts)}")
        ]

        if context:
            messages.append(ChatMessage(role="user", content=f"추가 컨텍스트: {context}"))

        try:
            response = self.llm_service.generate_completion(
                messages=messages,
                temperature=0.8,
                max_tokens=200
            )

            follow_up_question = response.content.strip()

            # 세션에 질문 추가
            question_data = {
                "question": follow_up_question,
                "phase": "follow_up",
                "asked_at": datetime.now(),
                "question_id": str(uuid.uuid4()),
                "type": "ai_generated"
            }
            session.questions.append(question_data)
            session.updated_at = datetime.now()

            return follow_up_question

        except Exception as e:
            logger.error(f"Error generating follow-up question: {e}")
            return None

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """세션 요약 정보"""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        return {
            "session_id": session.session_id,
            "interview_type": session.interview_type.value,
            "current_phase": session.current_phase.value,
            "participant_id": session.participant_id,
            "questions_count": len(session.questions),
            "responses_count": len(session.responses),
            "duration_minutes": (session.updated_at - session.created_at).total_seconds() / 60,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "metadata": session.metadata
        }

    def end_interview(self, session_id: str) -> Dict[str, Any]:
        """인터뷰 종료"""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.current_phase = InterviewPhase.COMPLETED
        session.updated_at = datetime.now()

        summary = self.get_session_summary(session_id)

        logger.info(f"Interview session {session_id} completed")
        return summary

    def health_check(self) -> Dict[str, Any]:
        """서비스 상태 확인"""
        return {
            "service": "Interview",
            "status": "healthy",
            "active_sessions": len(self.active_sessions),
            "dependencies": {
                "stt_service": self.stt_service.health_check()["status"] == "healthy",
                "llm_service": self.llm_service.health_check()["status"] == "healthy"
            },
            "templates_loaded": len(self.interview_templates) > 0,
            "supported_types": [t.value for t in InterviewType]
        }


# 편의 함수들
_default_interview_service = None

def get_interview_service() -> PureInterviewService:
    """기본 인터뷰 서비스 인스턴스 반환"""
    global _default_interview_service
    if _default_interview_service is None:
        _default_interview_service = PureInterviewService()
    return _default_interview_service


if __name__ == "__main__":
    # 테스트 코드
    service = get_interview_service()
    print(service.health_check())