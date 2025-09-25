"""
AI Interview service integrating STT and LLM
"""

import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from ai.stt.service import stt_service
from ai.llm.service import llm_service
from ai.llm.models import ChatMessage

logger = logging.getLogger(__name__)


class InterviewType(str, Enum):
    """Types of AI interviews"""
    CANDIDATE_COMPETENCY = "candidate_competency"
    JOB_REQUIREMENT = "job_requirement"
    GENERAL = "general"


class InterviewPhase(str, Enum):
    """Interview phases"""
    INTRODUCTION = "introduction"
    MAIN_QUESTIONS = "main_questions"
    FOLLOW_UP = "follow_up"
    CLOSING = "closing"
    COMPLETED = "completed"


class InterviewSession(BaseModel):
    """Interview session model"""
    session_id: str
    interview_type: InterviewType
    participant_id: str
    current_phase: InterviewPhase
    questions: List[Dict[str, Any]]
    responses: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = {}


class AIInterviewService:
    """AI Interview service integrating STT and LLM"""

    def __init__(self):
        self.active_sessions: Dict[str, InterviewSession] = {}
        self.interview_templates = self._load_interview_templates()

    def _load_interview_templates(self) -> Dict[InterviewType, Dict[str, Any]]:
        """Load interview templates and question flows"""
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
            }
        }

    async def start_interview(
        self,
        participant_id: str,
        interview_type: InterviewType,
        metadata: Dict[str, Any] = None
    ) -> InterviewSession:
        """
        Start a new AI interview session

        Args:
            participant_id: ID of the participant
            interview_type: Type of interview to conduct
            metadata: Additional metadata

        Returns:
            InterviewSession object
        """
        session_id = str(uuid.uuid4())

        session = InterviewSession(
            session_id=session_id,
            interview_type=interview_type,
            participant_id=participant_id,
            current_phase=InterviewPhase.INTRODUCTION,
            questions=[],
            responses=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=metadata or {}
        )

        self.active_sessions[session_id] = session

        logger.info(f"Started interview session {session_id} for participant {participant_id}")
        return session

    async def get_next_question(self, session_id: str) -> Optional[str]:
        """
        Get the next question for the interview session

        Args:
            session_id: Interview session ID

        Returns:
            Next question string or None if interview is complete
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        template = self.interview_templates[session.interview_type]

        # Get current phase questions
        current_phase_questions = []
        for phase_config in template["phases"]:
            if phase_config["phase"] == session.current_phase.value:
                current_phase_questions = phase_config["questions"]
                break

        # Check if we need to move to next phase
        answered_in_current_phase = len([
            q for q in session.questions
            if q.get("phase") == session.current_phase.value
        ])

        if answered_in_current_phase >= len(current_phase_questions):
            # Move to next phase
            if session.current_phase == InterviewPhase.INTRODUCTION:
                session.current_phase = InterviewPhase.MAIN_QUESTIONS
            elif session.current_phase == InterviewPhase.MAIN_QUESTIONS:
                session.current_phase = InterviewPhase.FOLLOW_UP
            elif session.current_phase == InterviewPhase.FOLLOW_UP:
                session.current_phase = InterviewPhase.CLOSING
            else:
                session.current_phase = InterviewPhase.COMPLETED
                return None

            # Get questions for new phase
            for phase_config in template["phases"]:
                if phase_config["phase"] == session.current_phase.value:
                    current_phase_questions = phase_config["questions"]
                    break
            answered_in_current_phase = 0

        if answered_in_current_phase < len(current_phase_questions):
            next_question = current_phase_questions[answered_in_current_phase]

            # Add question to session
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

    async def process_audio_response(
        self,
        session_id: str,
        audio_file,
        question_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process audio response using STT and analyze with LLM

        Args:
            session_id: Interview session ID
            audio_file: Audio file from user
            question_id: Optional question ID to link response

        Returns:
            Dictionary containing transcription and analysis
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        try:
            # Transcribe audio
            transcription, stt_metadata = await stt_service.transcribe_audio(audio_file)

            # Find the most recent question if question_id not provided
            if not question_id and session.questions:
                question_id = session.questions[-1].get("question_id")

            # Analyze response with LLM
            analysis = await self._analyze_response(
                transcription,
                session.interview_type,
                session.current_phase
            )

            # Store response
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
            logger.error(f"Error processing audio response for session {session_id}: {e}")
            raise

    async def _analyze_response(
        self,
        response_text: str,
        interview_type: InterviewType,
        phase: InterviewPhase
    ) -> Dict[str, Any]:
        """
        Analyze interview response using LLM

        Args:
            response_text: Transcribed response text
            interview_type: Type of interview
            phase: Current interview phase

        Returns:
            Analysis results
        """
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
            llm_response = await llm_service.generate_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )

            # Try to parse as JSON
            try:
                import json
                analysis = json.loads(llm_response.content)
            except json.JSONDecodeError:
                analysis = {"summary": llm_response.content}

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing response: {e}")
            return {"error": "분석 중 오류가 발생했습니다.", "raw_content": response_text}

    async def generate_follow_up_question(
        self,
        session_id: str,
        context: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a follow-up question based on previous responses

        Args:
            session_id: Interview session ID
            context: Additional context for question generation

        Returns:
            Generated follow-up question or None
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if not session.responses:
            return None

        # Get recent responses for context
        recent_responses = session.responses[-3:]  # Last 3 responses
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
            response = await llm_service.generate_completion(
                messages=messages,
                temperature=0.8,
                max_tokens=200
            )

            follow_up_question = response.content.strip()

            # Add to session questions
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
        """
        Get interview session summary

        Args:
            session_id: Interview session ID

        Returns:
            Session summary
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        return {
            "session_id": session.session_id,
            "interview_type": session.interview_type,
            "current_phase": session.current_phase,
            "questions_count": len(session.questions),
            "responses_count": len(session.responses),
            "duration_minutes": (session.updated_at - session.created_at).total_seconds() / 60,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "metadata": session.metadata
        }

    def end_interview(self, session_id: str) -> Dict[str, Any]:
        """
        End interview session and return final summary

        Args:
            session_id: Interview session ID

        Returns:
            Final interview summary
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.current_phase = InterviewPhase.COMPLETED
        session.updated_at = datetime.now()

        summary = self.get_session_summary(session_id)

        # Move to completed sessions (in production, save to database)
        logger.info(f"Interview session {session_id} completed")

        return summary


# Global AI interview service instance
ai_interview_service = AIInterviewService()