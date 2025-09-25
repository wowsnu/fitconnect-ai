"""
FastAPI routes for AI Interview functionality
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse

from .service import ai_interview_service
from .models import (
    StartInterviewRequest,
    InterviewSessionResponse,
    NextQuestionResponse,
    ResponseAnalysisResponse,
    FollowUpQuestionRequest,
    SessionSummary,
    DetailedSessionSummary,
    CompletionReport,
    InterviewHealthResponse,
    InterviewType,
    InterviewPhase
)

logger = logging.getLogger(__name__)

interview_router = APIRouter()


@interview_router.post("/start", response_model=InterviewSessionResponse)
async def start_interview(request: StartInterviewRequest):
    """
    Start a new AI interview session

    - **participant_id**: ID of the participant
    - **interview_type**: Type of interview (candidate_competency, job_requirement, general)
    - **metadata**: Additional metadata for the session
    """
    try:
        session = await ai_interview_service.start_interview(
            participant_id=request.participant_id,
            interview_type=request.interview_type,
            metadata=request.metadata
        )

        # Get first question
        first_question = await ai_interview_service.get_next_question(session.session_id)

        return InterviewSessionResponse(
            session_id=session.session_id,
            interview_type=session.interview_type,
            current_phase=session.current_phase,
            participant_id=session.participant_id,
            created_at=session.created_at,
            first_question=first_question
        )

    except Exception as e:
        logger.error(f"Error starting interview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")


@interview_router.get("/{session_id}/question", response_model=NextQuestionResponse)
async def get_next_question(session_id: str):
    """
    Get the next question for an interview session

    - **session_id**: Interview session ID
    """
    try:
        question = await ai_interview_service.get_next_question(session_id)

        session = ai_interview_service.active_sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get the question ID from the most recent question
        question_id = ""
        if session.questions:
            question_id = session.questions[-1].get("question_id", "")

        return NextQuestionResponse(
            question=question,
            question_id=question_id,
            phase=session.current_phase,
            is_completed=(question is None)
        )

    except ValueError as e:
        logger.error(f"Error getting next question: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting next question: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@interview_router.post("/{session_id}/response", response_model=ResponseAnalysisResponse)
async def process_audio_response(
    session_id: str,
    audio_file: UploadFile = File(..., description="Audio response file"),
    question_id: str = Form(None, description="Question ID (optional)")
):
    """
    Process audio response for an interview session

    - **session_id**: Interview session ID
    - **audio_file**: Audio file containing the response
    - **question_id**: ID of the question being answered (optional)
    """
    try:
        # Process the audio response
        result = await ai_interview_service.process_audio_response(
            session_id=session_id,
            audio_file=audio_file,
            question_id=question_id
        )

        # Try to get the next question automatically
        next_question = None
        try:
            next_question = await ai_interview_service.get_next_question(session_id)
        except Exception as e:
            logger.warning(f"Could not get next question: {e}")

        return ResponseAnalysisResponse(
            transcription=result["transcription"],
            analysis=result["analysis"],
            metadata=result["metadata"],
            next_question=next_question
        )

    except ValueError as e:
        logger.error(f"Error processing audio response: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error processing audio response: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@interview_router.post("/{session_id}/follow-up", response_model=Dict[str, str])
async def generate_follow_up_question(session_id: str, request: FollowUpQuestionRequest):
    """
    Generate an AI-powered follow-up question

    - **session_id**: Interview session ID
    - **context**: Additional context for question generation
    """
    try:
        follow_up_question = await ai_interview_service.generate_follow_up_question(
            session_id=request.session_id,
            context=request.context
        )

        if not follow_up_question:
            return {"message": "No follow-up question generated"}

        return {
            "question": follow_up_question,
            "type": "ai_generated"
        }

    except ValueError as e:
        logger.error(f"Error generating follow-up question: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error generating follow-up question: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@interview_router.get("/{session_id}/summary", response_model=SessionSummary)
async def get_session_summary(session_id: str):
    """
    Get interview session summary

    - **session_id**: Interview session ID
    """
    try:
        summary = ai_interview_service.get_session_summary(session_id)
        return SessionSummary(**summary)

    except ValueError as e:
        logger.error(f"Error getting session summary: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting session summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@interview_router.get("/{session_id}/detailed", response_model=DetailedSessionSummary)
async def get_detailed_session(session_id: str):
    """
    Get detailed interview session with all questions and responses

    - **session_id**: Interview session ID
    """
    try:
        session = ai_interview_service.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        summary = ai_interview_service.get_session_summary(session_id)

        return DetailedSessionSummary(
            **summary,
            questions=session.questions,
            responses=session.responses
        )

    except ValueError as e:
        logger.error(f"Error getting detailed session: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting detailed session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@interview_router.post("/{session_id}/end", response_model=CompletionReport)
async def end_interview(session_id: str):
    """
    End an interview session and generate completion report

    - **session_id**: Interview session ID
    """
    try:
        summary = ai_interview_service.end_interview(session_id)

        # Generate transcript
        session = ai_interview_service.active_sessions.get(session_id)
        transcript = []

        if session:
            for i, question in enumerate(session.questions):
                transcript.append({
                    "type": "question",
                    "content": question["question"],
                    "timestamp": question["asked_at"].isoformat()
                })

                # Find corresponding response
                if i < len(session.responses):
                    response = session.responses[i]
                    transcript.append({
                        "type": "response",
                        "content": response["transcription"],
                        "timestamp": response["responded_at"].isoformat()
                    })

        return CompletionReport(
            session_summary=SessionSummary(**summary),
            analytics=None,  # TODO: Implement analytics
            transcript=transcript,
            next_steps=["Review interview analysis", "Schedule follow-up if needed"]
        )

    except ValueError as e:
        logger.error(f"Error ending interview: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error ending interview: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@interview_router.get("/health", response_model=InterviewHealthResponse)
async def interview_health_check():
    """
    Check AI interview service health
    """
    try:
        active_sessions = len(ai_interview_service.active_sessions)
        templates_loaded = len(ai_interview_service.interview_templates) > 0

        # Check dependencies
        from ai.stt.service import stt_service
        from ai.llm.service import llm_service

        dependencies = {
            "stt_service": stt_service.model is not None,
            "llm_service": (llm_service.openai_client is not None or
                           llm_service.anthropic_client is not None)
        }

        service_status = "healthy"
        if not any(dependencies.values()):
            service_status = "dependencies_unavailable"
        elif not templates_loaded:
            service_status = "templates_not_loaded"

        return InterviewHealthResponse(
            service_status=service_status,
            active_sessions=active_sessions,
            dependencies=dependencies,
            templates_loaded=templates_loaded
        )

    except Exception as e:
        logger.error(f"Interview health check error: {e}")
        return InterviewHealthResponse(
            service_status="error",
            active_sessions=0,
            dependencies={"stt_service": False, "llm_service": False},
            templates_loaded=False
        )


@interview_router.get("/")
async def interview_info():
    """
    AI Interview module information
    """
    return {
        "module": "AI Interview System",
        "description": "Conduct AI-powered interviews integrating STT and LLM",
        "supported_types": [t.value for t in InterviewType],
        "phases": [p.value for p in InterviewPhase],
        "endpoints": {
            "POST /start": "Start new interview session",
            "GET /{session_id}/question": "Get next question",
            "POST /{session_id}/response": "Process audio response",
            "POST /{session_id}/follow-up": "Generate follow-up question",
            "GET /{session_id}/summary": "Get session summary",
            "GET /{session_id}/detailed": "Get detailed session",
            "POST /{session_id}/end": "End interview session",
            "GET /health": "Check service health"
        }
    }