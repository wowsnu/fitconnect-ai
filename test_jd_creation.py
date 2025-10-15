#!/usr/bin/env python3
"""
면접 결과 → JD 생성 통합 테스트
"""

import asyncio
import httpx

BASE_URL = "http://localhost:8000"
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxOCIsImVtYWlsIjoic2FuZzFAbmF2ZXIuY29tIiwicm9sZSI6ImNvbXBhbnkiLCJleHAiOjE3NjA0NjEzODl9.BG4MXVP6FVQzNabyVQtdbFZLamlSJKoAJzZo8uViQ_Q"


async def test_full_interview_to_jd():
    """전체 플로우 테스트: 면접 → JD 생성"""

    print("=" * 60)
    print("🎯 기업 면접 → JD 생성 통합 테스트")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=60.0) as client:

        # 1. General 면접 시작
        print("\n📝 1단계: General 면접 시작")
        response = await client.post(
            f"{BASE_URL}/api/company-interview/general/start",
            json={
                "access_token": ACCESS_TOKEN,
                "company_name": "테스트컴퍼니"
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"❌ 에러 응답: {response.text}")
            return
        data = response.json()
        print(f"응답 데이터: {data}")
        session_id = data.get("session_id")
        if not session_id:
            print(f"❌ session_id를 찾을 수 없습니다: {data}")
            return
        print(f"✅ Session ID: {session_id}")

        # 2. General 답변 제출 (5개)
        print("\n📝 2단계: General 답변 제출")
        general_answers = [
            "백엔드 개발자를 채용하려고 합니다. 시니어급 개발자가 필요합니다.",
            "Python과 FastAPI를 사용하여 API 서버를 개발하고 운영할 수 있는 분을 찾습니다.",
            "협업을 중요시하고 빠르게 성장하는 스타트업 문화를 추구합니다.",
            "서울 강남구에 위치한 오피스에서 주 5일 근무합니다. 하이브리드 근무 가능합니다.",
            "RDBMS 설계 경험과 AWS 인프라 운영 경험이 있으면 좋습니다."
        ]

        for i, answer in enumerate(general_answers, 1):
            response = await client.post(
                f"{BASE_URL}/api/company-interview/general/answer",
                json={
                    "session_id": session_id,
                    "answer": answer
                }
            )
            data = response.json()
            print(f"  Q{i}: {data.get('message', 'OK')}")

        # 3. Technical 면접 시작
        print("\n📝 3단계: Technical 면접 시작")
        response = await client.post(
            f"{BASE_URL}/api/company-interview/technical/start",
            json={
                "session_id": session_id,
                "access_token": ACCESS_TOKEN
            }
        )
        print(f"Status: {response.status_code}")

        # 4. Technical 답변 제출 (5개 고정 + 동적)
        print("\n📝 4단계: Technical 답변 제출")
        technical_answers = [
            "RESTful API 설계 및 개발, 데이터베이스 최적화, 성능 모니터링",
            "Python 5년, FastAPI 3년, PostgreSQL 4년 경험",
            "개발팀 리더 역할, 코드 리뷰 및 멘토링 경험",
            "대용량 트래픽 처리, 실시간 데이터 파이프라인 구축 경험",
            "시스템 설계 능력, 문제 해결 능력, 커뮤니케이션 능력"
        ]

        answer_idx = 0
        max_questions = 10
        while answer_idx < max_questions:
            if answer_idx < len(technical_answers):
                answer = technical_answers[answer_idx]
            else:
                answer = "네, 충분한 경험이 있습니다. 관련 프로젝트를 여러 번 수행했습니다."

            response = await client.post(
                f"{BASE_URL}/api/company-interview/technical/answer",
                json={
                    "session_id": session_id,
                    "answer": answer
                }
            )
            data = response.json()
            print(f"  Q{answer_idx+1}: 답변 완료")

            if data.get("is_finished"):
                print(f"  완료: Technical 면접 종료 (총 {answer_idx+1}개 답변)")
                break

            answer_idx += 1

        # 5. Situational 면접 시작
        print("\n📝 5단계: Situational 면접 시작")
        response = await client.post(
            f"{BASE_URL}/api/company-interview/situational/start",
            params={"session_id": session_id}
        )
        print(f"Status: {response.status_code}")

        # 6. Situational 답변 제출 (고정 + 동적 모두)
        print("\n📝 6단계: Situational 답변 제출")
        situational_answers = [
            "팀원들과 충분히 소통하고 서로의 의견을 존중합니다. 갈등이 생기면 대화를 통해 해결합니다.",
            "우선순위를 정하고 효율적으로 업무를 분배합니다. 필요하면 팀에 도움을 요청합니다.",
            "기술 블로그를 읽고 온라인 강의를 듣습니다. 사이드 프로젝트를 통해 실습합니다.",
            "빠르게 변화하는 환경을 선호합니다. 새로운 기술과 도전을 좋아합니다.",
            "정기적인 회고를 통해 개선점을 찾고, 지속적으로 학습합니다."
        ]

        answer_idx = 0
        max_questions = 10
        while answer_idx < max_questions:
            if answer_idx < len(situational_answers):
                answer = situational_answers[answer_idx]
            else:
                answer = "네, 충분히 준비되어 있고 적극적으로 협력하겠습니다."

            response = await client.post(
                f"{BASE_URL}/api/company-interview/situational/answer",
                json={
                    "session_id": session_id,
                    "answer": answer
                }
            )
            data = response.json()
            print(f"  Q{answer_idx+1}: 답변 완료")

            if data.get("is_finished"):
                print(f"  완료: Situational 면접 종료 (총 {answer_idx+1}개 답변)")
                break

            answer_idx += 1

        # 7. JD 생성 및 백엔드 저장
        print("\n📝 7단계: JD 생성 및 백엔드 저장")
        response = await client.post(
            f"{BASE_URL}/api/company-interview/job-posting",
            params={
                "session_id": session_id,
                "access_token": ACCESS_TOKEN
            }
        )
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ JD + 카드 생성 성공!")
            print(f"Job Posting ID: {data.get('job_posting_id')}")
            print(f"Card ID: {data.get('card_id')}")
            print(f"\n전체 응답:")
            import json
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ JD 생성 실패: {response.text}")

    print("\n" + "=" * 60)
    print("✅ 테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_full_interview_to_jd())
