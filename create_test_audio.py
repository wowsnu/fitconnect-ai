#!/usr/bin/env python3
"""
테스트용 음성 파일 생성
TTS로 간단한 한국어 음성을 생성해서 STT 테스트용으로 사용
"""

import os
import requests
from pathlib import Path

def create_sample_audio_with_tts():
    """온라인 TTS를 이용해 테스트 음성 파일 생성"""
    print("🔊 테스트용 음성 파일 생성 중...")

    # 테스트할 텍스트들
    test_texts = [
        "안녕하세요. 저는 김개발입니다. 백엔드 개발자로 5년간 일했습니다.",
        "저는 파이썬과 자바스크립트를 주로 사용합니다.",
        "팀워크를 중시하고 새로운 기술 학습을 좋아합니다."
    ]

    print("⚠️  실제 TTS 서비스가 필요합니다.")
    print("다음 방법들로 테스트 음성 파일을 준비할 수 있습니다:")
    print("\n📱 간단한 방법:")
    print("1. 휴대폰 음성 녹음 앱 사용")
    print("2. 다음 텍스트 중 하나를 읽어서 녹음:")

    for i, text in enumerate(test_texts, 1):
        print(f"   {i}. \"{text}\"")

    print("\n💾 파일 저장:")
    print("- 파일명: test_audio.wav 또는 test_audio.mp3")
    print(f"- 저장 위치: {Path.cwd()}")
    print("- 권장 길이: 5-10초")

    print("\n🌐 온라인 TTS 도구:")
    print("- Google Translate (번역 후 스피커 아이콘 클릭)")
    print("- Naver Papago (음성 듣기 기능)")
    print("- Windows: 내레이터 설정")
    print("- Mac: 말하기 기능 (시스템 환경설정 > 손쉬운 사용)")

def download_sample_if_available():
    """공개 샘플 오디오가 있다면 다운로드"""
    print("\n🔍 공개 테스트 오디오 샘플 확인 중...")

    # 무료 샘플 오디오 URL들 (실제로는 작동하지 않을 수 있음)
    sample_urls = [
        "https://www2.cs.uic.edu/~i101/SoundFiles/BabyElephantWalk60.wav",
        "https://samplelib.com/lib/preview/wav/sample-15s.wav"
    ]

    for url in sample_urls:
        try:
            print(f"시도 중: {url}")
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                filename = "sample_" + url.split("/")[-1]
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"✅ 샘플 다운로드 완료: {filename}")
                return filename
        except Exception as e:
            print(f"❌ 다운로드 실패: {e}")

    return None

def check_existing_audio():
    """현재 디렉토리에 오디오 파일이 있는지 확인"""
    print("\n📁 현재 디렉토리의 오디오 파일 확인:")

    audio_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.webm']
    current_dir = Path.cwd()

    found_files = []
    for ext in audio_extensions:
        files = list(current_dir.glob(f"*{ext}"))
        found_files.extend(files)

    if found_files:
        print("✅ 발견된 오디오 파일들:")
        for file in found_files:
            file_size = file.stat().st_size / 1024  # KB
            print(f"  - {file.name} ({file_size:.1f} KB)")
        return found_files[0]  # 첫 번째 파일 반환
    else:
        print("❌ 오디오 파일을 찾을 수 없습니다.")
        return None

def create_test_script():
    """실제 STT 테스트를 위한 스크립트 생성"""
    script_content = '''#!/usr/bin/env python3
"""
실제 음성 파일로 STT 테스트
"""

from ai.stt.service import get_stt_service
import sys
import os

def test_stt_with_file(audio_file):
    """실제 음성 파일로 STT 테스트"""
    if not os.path.exists(audio_file):
        print(f"❌ 파일을 찾을 수 없습니다: {audio_file}")
        return

    print(f"🎤 STT 테스트: {audio_file}")
    print("=" * 50)

    try:
        stt_service = get_stt_service()

        # 모델이 로드되지 않았다면 자동 로드
        if stt_service.model is None:
            print("📥 Whisper 모델 로딩 중... (처음에는 시간이 걸릴 수 있습니다)")
            stt_service.load_model()

        print("🔄 음성 인식 중...")
        text, metadata = stt_service.transcribe_file(audio_file)

        print("✅ 음성 인식 완료!")
        print(f"📝 인식된 텍스트: {text}")
        print(f"🌐 언어: {metadata.get('language')}")
        print(f"⏰ 길이: {metadata.get('duration', 0):.2f}초")
        print(f"📊 신뢰도: {metadata.get('confidence', 0):.2f}")

    except Exception as e:
        print(f"❌ STT 테스트 실패: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        test_stt_with_file(audio_file)
    else:
        print("사용법: python test_stt_real.py <음성파일>")
        print("예시: python test_stt_real.py test_audio.wav")
'''

    with open("test_stt_real.py", "w", encoding="utf-8") as f:
        f.write(script_content)

    print(f"\n📝 실제 STT 테스트 스크립트 생성됨: test_stt_real.py")

def main():
    """메인 실행 함수"""
    print("🎵 STT 테스트용 음성 파일 준비")
    print("=" * 50)

    # 1. 기존 오디오 파일 확인
    existing_file = check_existing_audio()

    # 2. 샘플 다운로드 시도
    if not existing_file:
        downloaded_file = download_sample_if_available()
        if downloaded_file:
            existing_file = downloaded_file

    # 3. 수동 생성 안내
    if not existing_file:
        create_sample_audio_with_tts()

    # 4. 테스트 스크립트 생성
    create_test_script()

    print("\n" + "=" * 50)
    print("🎯 다음 단계:")

    if existing_file:
        print(f"✅ 오디오 파일 준비됨: {existing_file}")
        print(f"▶️  테스트 실행: python test_stt_real.py {existing_file}")
    else:
        print("📱 음성 파일을 준비한 후:")
        print("▶️  테스트 실행: python test_stt_real.py <파일명>")

if __name__ == "__main__":
    main()