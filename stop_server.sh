#!/bin/bash

# FitConnect Backend - Stop Server
# 실행 중인 서버를 중단합니다

cd /home/ubuntu/apps/fitconnect-backend

if [ -f logs/server.pid ]; then
    PID=$(cat logs/server.pid)
    echo "🛑 서버 중단 중... (PID: $PID)"
    kill $PID 2>/dev/null || echo "⚠️  프로세스가 이미 종료되었습니다"
    rm logs/server.pid
    echo "✅ 서버가 중단되었습니다"
else
    echo "⚠️  실행 중인 서버를 찾을 수 없습니다"
    echo "수동으로 중단: pkill -f 'python main.py'"
fi
