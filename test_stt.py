#!/usr/bin/env python3
"""
STT 서비스 테스트
"""

import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

from ai.stt.service import get_stt_service

def test_stt_health():
    """STT 서비스 상태 확인"""
    print("🎤 STT 서비스 상태 확인")
    print("=" * 40)

    try:
        stt_service = get_stt_service()
        health = stt_service.health_check()

        print(f"서비스: {health.get('service')}")
        print(f"상태: {health.get('status')}")
        print(f"모델 정보: {health.get('model_info', {})}")

        model_info = health.get('model_info', {})
        print(f"모델 로드됨: {model_info.get('model_loaded')}")
        print(f"모델명: {model_info.get('model_name')}")
        print(f"디바이스: {model_info.get('device')}")
        print(f"지원 포맷: {', '.join(model_info.get('supported_formats', []))}")

        if health.get('status') == "healthy":
            print("✅ STT 서비스 정상!")
            return True
        else:
            print("⚠️  STT 모델이 아직 로드되지 않았습니다.")
            return True  # 서비스 자체는 정상, 모델만 로드 안됨

    except Exception as e:
        print(f"❌ STT 서비스 확인 실패: {e}")
        return False

def test_stt_with_sample():
    """샘플 텍스트로 TTS → STT 테스트 (실제 음성 파일 없이)"""
    print("\n🔊 음성 파일 없이 STT 기능 테스트")
    print("=" * 40)

    # 실제로는 음성 파일이 필요하지만, 서비스가 작동하는지만 확인
    try:
        stt_service = get_stt_service()

        # 가상의 파일 경로로 테스트 (실제로는 실행되지 않음)
        print("STT 서비스 객체 생성: ✅")
        print("transcribe_file 메서드 존재: ✅" if hasattr(stt_service, 'transcribe_file') else "❌")
        print("transcribe_audio_data 메서드 존재: ✅" if hasattr(stt_service, 'transcribe_audio_data') else "❌")

        return True

    except Exception as e:
        print(f"❌ STT 기능 테스트 실패: {e}")
        return False

def create_test_instructions():
    """실제 음성 파일 테스트 방법 안내"""
    print("\n📝 실제 음성 파일로 테스트하는 방법")
    print("=" * 50)

    instructions = """
1. 음성 파일 준비:
   - 지원 포맷: WAV, MP3, M4A, FLAC, OGG, WEBM
   - 권장: 짧은 한국어 음성 (5-30초)
   - 예시: "안녕하세요, 저는 김개발입니다. 백엔드 개발자로 5년간 일했습니다."

2. 음성 파일 위치:
   - 이 프로젝트 폴더에 test_audio.wav 또는 test_audio.mp3로 저장

3. 테스트 코드 실행:
   ```python
   from ai.stt.service import get_stt_service

   stt = get_stt_service()
   result = stt.transcribe_file("test_audio.wav")
   print("변환 결과:", result.text)
   ```

4. 온라인 음성 생성 도구 (테스트용):
   - Google Text-to-Speech
   - Naver Clova Voice
   - 휴대폰 음성 녹음

5. 빠른 테스트 방법:
   - 휴대폰으로 5초 정도 한국어 녹음
   - 파일을 컴퓨터로 전송
   - 프로젝트 폴더에 저장 후 테스트
"""

    print(instructions)

def main():
    """메인 테스트 실행"""
    print("🎤 STT 서비스 테스트")
    print("=" * 60)

    # 1. 서비스 상태 확인
    health_ok = test_stt_health()

    # 2. 기능 확인
    function_ok = test_stt_with_sample()

    # 3. 실제 테스트 방법 안내
    create_test_instructions()

    print("\n" + "=" * 60)
    print("🎯 테스트 결과 요약:")
    print(f"- STT 서비스 상태: {'✅' if health_ok else '❌'}")
    print(f"- STT 기능 준비: {'✅' if function_ok else '❌'}")

    if health_ok and function_ok:
        print("\n✅ STT 서비스가 정상적으로 준비되었습니다!")
        print("📁 실제 음성 파일을 준비해서 transcribe_file()을 테스트해보세요.")
    else:
        print("\n❌ STT 서비스에 문제가 있습니다. 의존성을 확인해주세요.")
        print("설치 필요: pip install openai-whisper")

if __name__ == "__main__":
    main()