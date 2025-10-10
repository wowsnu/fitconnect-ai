"""
Company Interview API Test

FastAPI 엔드포인트 테스트:
- POST /api/company-interview/general/start
- POST /api/company-interview/general/answer
- GET /api/company-interview/general/analysis/{session_id}
- POST /api/company-interview/technical/start
- POST /api/company-interview/technical/answer
- POST /api/company-interview/situational/start
- POST /api/company-interview/situational/answer
- GET /api/company-interview/job-posting/{session_id}
"""

import asyncio
import httpx
from typing import Optional

BASE_URL = "http://localhost:8000/api/company-interview"


class CompanyInterviewAPITest:
    """기업 면접 API 테스트 클래스"""

    def __init__(self):
        self.session_id: Optional[str] = None
        self.company_name = "FitConnect"

    async def test_full_flow(self):
        """전체 플로우 테스트"""

        print("=" * 70)
        print("기업 면접 API 테스트 시작")
        print("=" * 70)

        # 타임아웃 설정 (LLM 호출 시간 고려)
        timeout = httpx.Timeout(120.0, connect=10.0)  # 120초로 증가
        async with httpx.AsyncClient(timeout=timeout) as client:
            # ==================== 1. General Interview ====================
            await self._test_general_interview(client)

            # ==================== 2. Technical Interview ====================
            await self._test_technical_interview(client)

            # ==================== 3. Situational Interview ====================
            await self._test_situational_interview(client)

            # ==================== 4. Job Posting Card ====================
            await self._test_job_posting(client)

            # ==================== 5. Session Info ====================
            await self._test_session_info(client)

        print("\n" + "=" * 70)
        print("✅ 전체 API 테스트 완료!")
        print("=" * 70)

    async def _test_general_interview(self, client: httpx.AsyncClient):
        """General Interview 테스트"""

        print("\n[1단계] General Interview API 테스트")
        print("-" * 70)

        # 1-1. Start General Interview
        print("\n1-1. POST /general/start")
        response = await client.post(
            f"{BASE_URL}/general/start",
            json={
                "company_name": self.company_name,
                "existing_jd": None
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        self.session_id = data["session_id"]

        print(f"✅ Session ID: {self.session_id}")
        print(f"   첫 질문: {data['question']}")
        print(f"   진행도: {data['question_number']}/{data['total_questions']}")

        # 1-2. Submit Answers (5개)
        answers = [
            "저희는 투명성, 협력, 혁신을 가장 중요하게 생각합니다.",
            "빠른 학습 능력, 적극적 커뮤니케이션, 주도성, 팀워크를 중시하는 분입니다.",
            "애자일 방식으로 2주 스프린트로 일하고, 재택과 사무실 근무를 자유롭게 선택할 수 있습니다.",
            "백엔드 팀원이 부족해서 업무 부담이 큽니다. 한 분이 합류하시면 팀이 안정화될 것 같습니다.",
            "주인의식을 가지고 능동적으로 개선점을 찾는 분을 찾습니다."
        ]

        print("\n1-2. POST /general/answer (5회)")
        for i, answer in enumerate(answers, 1):
            response = await client.post(
                f"{BASE_URL}/general/answer",
                json={
                    "session_id": self.session_id,
                    "answer": answer
                }
            )
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            data = response.json()
            print(f"   [{i}/5] ✅ 답변 제출 완료")

            if data["next_question"]:
                print(f"         다음 질문: {data['next_question'][:50]}...")
            else:
                print(f"         완료!")

        # 1-3. Get Analysis
        print("\n1-3. GET /general/analysis/{session_id}")
        response = await client.get(f"{BASE_URL}/general/analysis/{self.session_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        print("✅ General 분석 완료")
        print(f"   - 핵심 가치: {', '.join(data['core_values'])}")
        print(f"   - 이상적 인재: {', '.join(data['ideal_candidate_traits'][:2])}...")

    async def _test_technical_interview(self, client: httpx.AsyncClient):
        """Technical Interview 테스트"""

        print("\n\n[2단계] Technical Interview API 테스트")
        print("-" * 70)

        # 2-1. Start Technical Interview
        print("\n2-1. POST /technical/start")
        response = await client.post(
            f"{BASE_URL}/technical/start?session_id={self.session_id}"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        print(f"✅ Technical 면접 시작")
        print(f"   첫 질문: {data['next_question']['question'][:50]}...")

        # 2-2. Submit Answers (고정 5개)
        fixed_answers = [
            "RESTful API 설계 및 개발, 데이터베이스 스키마 설계, 서버 성능 최적화, 레거시 코드 리팩토링입니다.",
            "Python 3년 이상, FastAPI 또는 Django 경험, PostgreSQL 사용 경험, Git 협업 경험이 필수입니다.",
            "Docker, Kubernetes 경험, AWS 인프라 경험, Redis 캐싱 경험, 테스트 코드 작성 경험을 우대합니다.",
            "새로 만들어진 포지션입니다. 팀이 커지면서 미들급 개발자를 추가로 채용하게 되었습니다.",
            "레거시 코드 파악에 시간이 걸리고, 사용자가 빠르게 늘면서 스케일링 이슈를 경험하게 될 것입니다."
        ]

        print("\n2-2. POST /technical/answer (고정 5개)")
        for i, answer in enumerate(fixed_answers, 1):
            response = await client.post(
                f"{BASE_URL}/technical/answer",
                json={
                    "session_id": self.session_id,
                    "answer": answer
                }
            )
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            data = response.json()
            print(f"   [{i}/5] ✅ 답변 제출 완료")

        # 2-3. Submit Dynamic Answers (실시간 추천 질문)
        print("\n2-3. 실시간 추천 질문 답변")

        # 마지막 응답에서 is_finished가 False면 동적 질문이 생성됨
        while not data["is_finished"]:
            if data["next_question"]:
                next_q = data["next_question"]

                # dict인 경우 (동적 질문)
                if isinstance(next_q, dict):
                    print(f"   🤖 동적 질문: {next_q['question'][:50]}...")
                    print(f"      목적: {next_q.get('purpose', 'N/A')[:40]}...")

                # 간단한 답변
                dummy_answer = "네, 그렇습니다. 구체적으로는 실무 경험을 통해 익힐 수 있을 것으로 기대합니다."

                response = await client.post(
                    f"{BASE_URL}/technical/answer",
                    json={
                        "session_id": self.session_id,
                        "answer": dummy_answer
                    }
                )
                assert response.status_code == 200, f"Expected 200, got {response.status_code}"

                data = response.json()
                print(f"      ✅ 답변 제출 완료")
            else:
                break

        print("\n2-4. GET /technical/analysis/{session_id}")
        response = await client.get(f"{BASE_URL}/technical/analysis/{self.session_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        print("✅ Technical 분석 완료")
        print(f"   - 직무명: {data['job_title']}")
        print(f"   - 주요 업무: {len(data['main_responsibilities'])}개")
        print(f"   - 필수 역량: {len(data['required_skills'])}개")

    async def _test_situational_interview(self, client: httpx.AsyncClient):
        """Situational Interview 테스트"""

        print("\n\n[3단계] Situational Interview API 테스트")
        print("-" * 70)

        # 3-1. Start Situational Interview
        print("\n3-1. POST /situational/start")
        response = await client.post(
            f"{BASE_URL}/situational/start?session_id={self.session_id}"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        print(f"✅ Situational 면접 시작")
        print(f"   첫 질문: {data['next_question']['question'][:50]}...")

        # 3-2. Submit Answers (고정 5개)
        fixed_answers = [
            "명확히 성장기입니다. 사용자가 매달 2배씩 늘고 있고, 팀도 계속 커지고 있습니다.",
            "적극적으로 질문하고 의견을 나누는 분이 잘 맞아요. 주니어라도 좋은 아이디어가 있으면 바로 실행해봅니다.",
            "데이터와 사용자 피드백을 기준으로 결정합니다. A/B 테스트나 작은 실험을 통해 판단합니다.",
            "완전히 빠르게 변화하는 환경이에요. 우선순위가 주마다 바뀔 수 있습니다.",
            "협업이 더 중요합니다. 팀이 작아서 서로 의존도가 높습니다."
        ]

        print("\n3-2. POST /situational/answer (고정 5개)")
        for i, answer in enumerate(fixed_answers, 1):
            response = await client.post(
                f"{BASE_URL}/situational/answer",
                json={
                    "session_id": self.session_id,
                    "answer": answer
                }
            )
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            data = response.json()
            print(f"   [{i}/5] ✅ 답변 제출 완료")

        # 3-3. Submit Dynamic Answers
        print("\n3-3. 실시간 추천 질문 답변")

        while not data["is_finished"]:
            if data["next_question"]:
                next_q = data["next_question"]

                if isinstance(next_q, dict):
                    print(f"   🤖 동적 질문: {next_q['question'][:50]}...")
                    print(f"      목적: {next_q.get('purpose', 'N/A')[:40]}...")

                dummy_answer = "네, 그렇게 생각합니다. 팀에 잘 맞는 분을 찾고 있습니다."

                response = await client.post(
                    f"{BASE_URL}/situational/answer",
                    json={
                        "session_id": self.session_id,
                        "answer": dummy_answer
                    }
                )
                assert response.status_code == 200, f"Expected 200, got {response.status_code}"

                data = response.json()
                print(f"      ✅ 답변 제출 완료")
            else:
                break

        print("\n3-4. GET /situational/analysis/{session_id}")
        response = await client.get(f"{BASE_URL}/situational/analysis/{self.session_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        print("✅ Situational 분석 완료")
        print(f"   - 팀 현황: {data['team_situation'][:50]}...")
        print(f"   - 협업 스타일: {data['collaboration_style'][:50]}...")

    async def _test_job_posting(self, client: httpx.AsyncClient):
        """Job Posting Card 테스트"""

        print("\n\n[최종] Job Posting Card 생성")
        print("=" * 70)

        print("\nGET /job-posting/{session_id}")
        response = await client.get(
            f"{BASE_URL}/job-posting/{self.session_id}?deadline=2025-12-31"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()

        print("\n✅ 채용 공고 카드 생성 완료")
        print("-" * 70)
        print(f"📄 {data['company_name']} - {data['position_title']}")
        print(f"📅 마감일: {data['deadline']}")
        print()
        print(f"[공고 정보]")
        print(f"  - 경력: {data['experience_level']}")
        print(f"  - 부서: {data['department']}")
        print(f"  - 고용: {data['employment_type']}")
        print()
        print(f"[주요 업무] {len(data['main_responsibilities'])}개")
        for i, item in enumerate(data['main_responsibilities'], 1):
            print(f"  {i}. {item}")
        print()
        print(f"[필수 역량] {len(data['required_skills'])}개")
        for i, item in enumerate(data['required_skills'], 1):
            print(f"  {i}. {item}")
        print()
        print(f"[우대 역량] {len(data['preferred_skills'])}개")
        for i, item in enumerate(data['preferred_skills'], 1):
            print(f"  {i}. {item}")
        print()
        print(f"[인재상]")
        print(f"  {data['personality_fit'][:100]}...")
        print()
        print(f"[도전 과제]")
        print(f"  {data['challenges'][:100]}...")

    async def _test_session_info(self, client: httpx.AsyncClient):
        """세션 정보 조회 테스트"""

        print("\n\n[추가] 세션 정보 조회")
        print("-" * 70)

        print(f"\nGET /session/{self.session_id}")
        response = await client.get(f"{BASE_URL}/session/{self.session_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        print("✅ 세션 정보:")
        print(f"   - 회사명: {data['company_name']}")
        print(f"   - General: {data['general']['finished']}")
        print(f"   - Technical: {data['technical']['finished']}")
        print(f"   - Situational: {data['situational']['finished']}")


async def main():
    """메인 실행 함수"""
    tester = CompanyInterviewAPITest()

    try:
        await tester.test_full_flow()
    except httpx.ConnectError:
        print("\n❌ 오류: 서버에 연결할 수 없습니다.")
        print("   서버를 먼저 실행해주세요:")
        print("   $ source .venv/bin/activate")
        print("   $ python main.py")
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
