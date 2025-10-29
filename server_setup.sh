#!/bin/bash

# FitConnect Backend - EC2 서버 초기 설정 스크립트
# EC2에서 한 번만 실행하면 됩니다

set -e

echo "🔧 FitConnect Backend Server Setup Starting..."

# 1. 시스템 업데이트
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# 2. Python 설치
echo "🐍 Installing Python 3.11..."
sudo apt install -y python3.11 python3.11-venv python3-pip

# 3. 필수 도구 설치
echo "🛠️ Installing essential tools..."
sudo apt install -y git curl wget vim htop ffmpeg

# 4. MySQL 설치 (선택사항)
read -p "Install MySQL locally? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "💾 Installing MySQL..."
    sudo apt install -y mysql-server
    sudo mysql_secure_installation

    echo "📝 Creating database..."
    sudo mysql <<EOF
CREATE DATABASE IF NOT EXISTS fitconnect CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'fitconnect_user'@'localhost' IDENTIFIED BY 'fitconnect2024!';
GRANT ALL PRIVILEGES ON fitconnect.* TO 'fitconnect_user'@'localhost';
FLUSH PRIVILEGES;
EOF
    echo "✅ MySQL setup completed!"
fi

# 5. 프로젝트 디렉토리 생성
echo "📁 Creating project directory..."
mkdir -p /home/ubuntu/apps/fitconnect-backend
cd /home/ubuntu/apps/fitconnect-backend

# 6. Python 가상환경 생성
echo "🔨 Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# 7. pip 업그레이드
pip install --upgrade pip

echo "✅ Server setup completed!"
echo ""
echo "Next steps:"
echo "1. Upload your code: scp -i key.pem -r ./fitconnect-backend ubuntu@YOUR_IP:/home/ubuntu/apps/"
echo "2. Install dependencies: pip install -r requirements.txt"
echo "3. Configure .env file"
echo "4. Setup systemd service"
