#!/bin/bash

# FitConnect Backend - Start Server with nohup
# 백그라운드에서 서버를 실행하고 로그를 파일로 저장합니다

cd /home/ubuntu/apps/fitconnect-backend

# 가상환경 활성화
source venv/bin/activate

# 기존 프로세스 종료 (있다면)
pkill -f "python main.py" || true

# nohup으로 백그라운드 실행
# 로그는 logs/server.log에 저장됨
mkdir -p logs
nohup python main.py > logs/server.log 2>&1 &

# 프로세스 ID 저장
echo $! > logs/server.pid

echo "✅ 서버가 백그라운드에서 실행 중입니다"
echo "📝 로그 확인: tail -f /home/ubuntu/apps/fitconnect-backend/logs/server.log"
echo "🔢 프로세스 ID: $(cat logs/server.pid)"
echo "⏹️  서버 중단: ./stop_server.sh"
