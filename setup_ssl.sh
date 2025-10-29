#!/bin/bash

# SSL Certificate Setup for FitConnect Backend
# EC2에서 실행하세요

echo "🔐 SSL 인증서 설정 시작..."

# certbot 설치 (Ubuntu)
sudo apt update
sudo apt install -y certbot

# SSL 인증서 디렉토리 생성
mkdir -p /home/ubuntu/apps/fitconnect-backend/ssl

# Let's Encrypt 인증서 발급 (standalone 모드)
# 주의: 포트 80이 열려있어야 합니다
sudo certbot certonly --standalone -d fitconnectai.duckdns.org --non-interactive --agree-tos -m dltkddn2313@gmail.com

# 인증서를 앱 디렉토리로 복사 (읽기 권한 필요)
sudo cp /etc/letsencrypt/live/fitconnectai.duckdns.org/fullchain.pem /home/ubuntu/apps/fitconnect-backend/ssl/
sudo cp /etc/letsencrypt/live/fitconnectai.duckdns.org/privkey.pem /home/ubuntu/apps/fitconnect-backend/ssl/

# 권한 설정
sudo chown ubuntu:ubuntu /home/ubuntu/apps/fitconnect-backend/ssl/*.pem
sudo chmod 644 /home/ubuntu/apps/fitconnect-backend/ssl/fullchain.pem
sudo chmod 600 /home/ubuntu/apps/fitconnect-backend/ssl/privkey.pem

echo "✅ SSL 인증서 설정 완료!"
echo "📁 인증서 위치: /home/ubuntu/apps/fitconnect-backend/ssl/"
echo ""
echo "⚠️  인증서는 90일마다 갱신이 필요합니다"
echo "갱신 명령어: sudo certbot renew"
