# 프론트엔드 STT 연동 가이드

## 📋 개요
FitConnect 백엔드의 STT(Speech-to-Text) 서비스를 프론트엔드에서 사용하는 방법입니다.

## 🎤 지원 음성 파일 형식

### ✅ 지원 포맷
- **WAV** (권장)
- **MP3**
- **M4A** (iOS 녹음 기본 포맷)
- **FLAC**
- **OGG**
- **WEBM** (브라우저 MediaRecorder API 기본 포맷)

### 📏 파일 제한사항
- **최대 파일 크기**: 25MB (추후 조정 가능)
- **최대 길이**: 10분 (추후 조정 가능)
- **언어**: 한국어, 영어 (기본: 한국어)

## 🔌 백엔드 사용 방법

### Python 함수 직접 호출 (백엔드에서)
```python
from ai.stt.service import get_stt_service

# 서비스 인스턴스 생성
stt = get_stt_service()

# 파일 경로로 음성 인식
text, metadata = stt.transcribe_file("audio.wav", language="ko")

# 바이트 데이터로 음성 인식 (파일 업로드 처리)
with open("audio.wav", "rb") as f:
    audio_bytes = f.read()
text, metadata = stt.transcribe_bytes(audio_bytes, "audio.wav", language="ko")

print(f"인식된 텍스트: {text}")
print(f"메타데이터: {metadata}")
```

### 응답 형식
```python
# text (str): 인식된 텍스트
"안녕하세요. 저는 김개발입니다. 백엔드 개발자로 5년간 일했습니다."

# metadata (dict): 메타데이터
{
    "language": "ko",           # 인식된 언어
    "duration": 8.5,           # 오디오 길이 (초)
    "segments_count": 3,       # 음성 구간 수
    "confidence": 0.89,        # 신뢰도 (0-1)
    "file_path": "audio.wav"   # 파일 경로
}
```

## 🌐 HTTP API 방식 (향후 구현 예정)

### 엔드포인트
```
POST /api/ai/stt/transcribe
Content-Type: multipart/form-data
```

### 요청 형식
```javascript
const formData = new FormData();
formData.append('audio', audioFile);      // 음성 파일
formData.append('language', 'ko');        // 언어 (옵션)

fetch('/api/ai/stt/transcribe', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('인식된 텍스트:', data.text);
    console.log('메타데이터:', data.metadata);
});
```

### 응답 형식
```json
{
    "success": true,
    "text": "안녕하세요. 저는 김개발입니다.",
    "metadata": {
        "language": "ko",
        "duration": 8.5,
        "segments_count": 3,
        "confidence": 0.89
    }
}
```

## 📱 프론트엔드 구현 예시

### 1. 파일 업로드 방식
```html
<input type="file" id="audioFile" accept=".wav,.mp3,.m4a,.webm">
<button onclick="uploadAudio()">음성 인식</button>
```

```javascript
function uploadAudio() {
    const fileInput = document.getElementById('audioFile');
    const file = fileInput.files[0];

    if (!file) {
        alert('음성 파일을 선택해주세요.');
        return;
    }

    // 파일 형식 확인
    const supportedFormats = ['.wav', '.mp3', '.m4a', '.webm', '.flac', '.ogg'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

    if (!supportedFormats.includes(fileExtension)) {
        alert('지원하지 않는 파일 형식입니다.');
        return;
    }

    // 백엔드로 전송 (구현 필요)
    sendToBackend(file);
}
```

### 2. 실시간 녹음 방식 (WebRTC)
```javascript
let mediaRecorder;
let audioChunks = [];

// 녹음 시작
async function startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm' // STT에서 지원하는 형식
    });

    mediaRecorder.ondataavailable = event => {
        audioChunks.push(event.data);
    };

    mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        await sendAudioToSTT(audioBlob);
        audioChunks = [];
    };

    mediaRecorder.start();
}

// 녹음 중지
function stopRecording() {
    mediaRecorder.stop();
}

// STT로 전송
async function sendAudioToSTT(audioBlob) {
    // 백엔드 API 호출 (구현 필요)
    console.log('음성 데이터 크기:', audioBlob.size);
}
```

## 🧪 테스트 방법

### 1. 테스트용 음성 파일 준비
```bash
# 프로젝트 폴더에 테스트 파일 저장
# 예시: test_audio.wav, test_audio.mp3
```

### 2. 백엔드 테스트
```python
# 백엔드에서 직접 테스트
python test_stt_real.py test_audio.wav
```

### 3. 프론트엔드 연동 테스트
- 파일 업로드 UI 구현
- 백엔드 STT 함수 호출 API 구현
- 실제 음성 파일로 end-to-end 테스트

## 📝 샘플 음성 텍스트

테스트용으로 다음 텍스트를 5-10초 정도 녹음해보세요:

```
"안녕하세요. 저는 김개발입니다. 백엔드 개발자로 5년간 일했습니다."

"저는 파이썬과 자바스크립트를 주로 사용합니다. 팀워크를 중시합니다."

"새로운 기술 학습을 좋아하고 문제 해결에 관심이 많습니다."
```

## 🔧 백엔드 설정 확인

STT 서비스가 정상 작동하는지 확인:

```python
from ai.stt.service import get_stt_service

stt = get_stt_service()
health = stt.health_check()
print("STT 상태:", health)
```

## 📞 지원 및 문의

- STT 관련 이슈: AI 개발팀
- API 연동 이슈: 백엔드 개발팀
- 테스트 결과 공유 및 피드백 환영

---

**참고**: 현재는 백엔드에서 Python 함수 직접 호출 방식만 구현되어 있습니다. HTTP API는 필요시 추가 구현 예정입니다.