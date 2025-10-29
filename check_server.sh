#!/bin/bash

# FitConnect Backend - Check Server Status
# 서버 상태 및 최근 로그를 확인합니다

cd /home/ubuntu/apps/fitconnect-backend

echo "=== 서버 상태 확인 ==="
echo ""

# 프로세스 확인
if [ -f logs/server.pid ]; then
    PID=$(cat logs/server.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ 서버 실행 중 (PID: $PID)"
    else
        echo "❌ 서버가 중단되었습니다 (PID 파일은 존재하지만 프로세스 없음)"
    fi
else
    echo "⚠️  PID 파일 없음"
fi

echo ""
echo "🔍 Python 프로세스 확인:"
ps aux | grep "python main.py" | grep -v grep || echo "실행 중인 프로세스 없음"

echo ""
echo "📊 포트 8000 확인:"
netstat -tuln | grep :8000 || echo "8000번 포트 사용 중이 아님"

echo ""
echo "📝 최근 로그 (마지막 20줄):"
if [ -f logs/server.log ]; then
    tail -20 logs/server.log
else
    echo "로그 파일 없음"
fi
