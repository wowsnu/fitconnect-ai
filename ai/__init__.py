"""
FitConnect AI Module - 백엔드팀을 위한 AI 인터페이스

순수 Python 모듈로 FastAPI나 다른 웹 프레임워크에 의존하지 않습니다.
"""

from typing import Dict, List, Optional, Tuple, Any

# 버전 정보
__version__ = "1.0.0"
__author__ = "FitConnect AI Team"

def get_ai_info() -> Dict[str, Any]:
    """AI 모듈 정보 반환"""
    return {
        "module": "FitConnect AI",
        "version": __version__,
        "author": __author__,
        "description": "순수 Python AI 서비스 모듈",
        "framework_independent": True
    }

# 간단한 테스트를 위한 함수들
def stt_health_check() -> Dict[str, Any]:
    """STT 서비스 상태 확인 (간단 버전)"""
    try:
        from ai.stt.pure_service import get_stt_service
        service = get_stt_service()
        return service.health_check()
    except Exception as e:
        return {"status": "error", "message": str(e)}

def ai_system_health_check() -> Dict[str, Any]:
    """전체 AI 시스템 상태 확인"""
    stt_status = stt_health_check()

    return {
        "overall_status": "healthy",
        "services": {
            "stt": stt_status
        },
        "version": __version__
    }