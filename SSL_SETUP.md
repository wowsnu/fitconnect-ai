# SSL 설정 가이드

## EC2에서 SSL 인증서 설정하기

### 1. setup_ssl.sh 수정
```bash
nano setup_ssl.sh
# your-email@example.com을 실제 이메일로 변경
```

### 2. 서버 중지 (포트 80을 certbot이 사용해야 함)
```bash
./stop_server.sh
```

### 3. EC2 보안 그룹에서 포트 80 열기
- AWS 콘솔에서 EC2 보안 그룹 설정
- 인바운드 규칙 추가: HTTP (포트 80) 허용
- 인증서 발급 후 닫아도 됨

### 4. SSL 인증서 발급
```bash
chmod +x setup_ssl.sh
./setup_ssl.sh
```

### 5. 서버 재시작
```bash
./start_server.sh
```

### 6. 확인
```bash
# 로그 확인 - "🔐 HTTPS 모드로 서버 시작..." 메시지가 보여야 함
tail -f logs/server.log

# HTTPS 테스트
curl https://fitconnectai.duckdns.org:8000/health
```

## 인증서 갱신 (90일마다)

```bash
# 서버 중지
./stop_server.sh

# 인증서 갱신
sudo certbot renew

# 인증서 복사
sudo cp /etc/letsencrypt/live/fitconnectai.duckdns.org/fullchain.pem /home/ubuntu/apps/fitconnect-backend/ssl/
sudo cp /etc/letsencrypt/live/fitconnectai.duckdns.org/privkey.pem /home/ubuntu/apps/fitconnect-backend/ssl/
sudo chown ubuntu:ubuntu /home/ubuntu/apps/fitconnect-backend/ssl/*.pem

# 서버 재시작
./start_server.sh
```

## 문제 해결

### "ERR_SSL_PROTOCOL_ERROR" 여전히 발생
- 로그 확인: `tail -f logs/server.log`
- HTTPS 모드로 시작했는지 확인
- 인증서 파일 권한 확인: `ls -la ssl/`

### Certbot 에러
- 포트 80이 열려있는지 확인
- 다른 프로세스가 포트 80을 사용 중인지 확인: `sudo lsof -i :80`
- DuckDNS 도메인이 제대로 연결되었는지 확인: `nslookup fitconnectai.duckdns.org`
