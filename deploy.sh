#!/bin/bash

# FitConnect Backend Deployment Script
# EC2 서버로 자동 배포

set -e  # 에러 발생 시 스크립트 중단

# 설정
EC2_IP="3.80.100.103"
EC2_USER="ubuntu"
KEY_PATH="~/Downloads/fit_ai-key.pem"
REMOTE_DIR="/home/ubuntu/apps/fitconnect-backend"

echo "🚀 FitConnect Backend Deployment Starting..."

# 1. Git push (GitHub 사용 시)
# echo "📤 Pushing to GitHub..."
# git add .
# git commit -m "Deploy: $(date '+%Y-%m-%d %H:%M:%S')"
# git push origin main

# 2. 서버에 파일 복사
echo "📦 Uploading files to EC2..."
rsync -avz --exclude='.git' \
           --exclude='.venv' \
           --exclude='__pycache__' \
           --exclude='*.pyc' \
           --exclude='.DS_Store' \
           --exclude='uploads/*' \
           --exclude='data/*' \
           -e "ssh -i $KEY_PATH" \
           ./ ${EC2_USER}@${EC2_IP}:${REMOTE_DIR}/

# 3. 서버에서 배포 스크립트 실행
echo "🔧 Running deployment on EC2..."
ssh -i $KEY_PATH ${EC2_USER}@${EC2_IP} << 'ENDSSH'
cd /home/ubuntu/apps/fitconnect-backend

# 가상환경 활성화
source venv/bin/activate

# 의존성 업데이트
pip install -r requirements.txt --upgrade

# 디렉토리 확인
mkdir -p ./data/chroma
mkdir -p ./uploads

# 서비스 재시작
sudo systemctl restart fitconnect

# 상태 확인
sleep 2
sudo systemctl status fitconnect --no-pager

echo "✅ Deployment completed!"
ENDSSH

echo "✅ Deployment successful! Server is running at http://${EC2_IP}:8000"
echo "📊 Check logs: ssh -i $KEY_PATH ${EC2_USER}@${EC2_IP} 'sudo journalctl -u fitconnect -f'"
