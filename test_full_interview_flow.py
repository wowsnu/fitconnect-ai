"""
전체 인터뷰 플로우 테스트 (카드 생성까지)
General -> Technical -> Situational -> Profile Card -> Matching Vectors
"""

import asyncio
import httpx
import sys

# 설정
AI_URL = "http://127.0.0.1:8000"
BACKEND_URL = "http://54.89.71.175:8000"

# 테스트용 답변들
GENERAL_ANSWERS = [
    "네이버에서 HRD 담당자로 2년간 근무했고, 카카오뱅크에서 인재영입 어시스턴트로 1년 근무했습니다. 주로 채용 프로세스 운영과 교육 프로그램 기획을 담당했습니다.",
    "채용 프로세스를 최적화해서 지원자 경험을 개선한 것과, 맞춤형 교육 프로그램을 설계해서 실행한 경험이 있습니다. 특히 데이터 기반으로 의사결정하는 것을 중요하게 생각합니다.",
    "최근 6개월간 채용 브랜딩 프로젝트에 몰입했습니다. 회사의 인재상과 문화를 효과적으로 전달하기 위한 콘텐츠를 기획하고 실행했습니다.",
    "신입 사원 온보딩 프로그램을 처음부터 설계하고 운영한 경험이 가장 의미있었습니다. 많은 부서와 협업하면서 실질적인 도움이 되는 프로그램을 만들었습니다.",
    "일과 삶의 균형을 중요하게 생각하며, 효율적으로 일해서 성과를 내되 개인 시간도 충분히 가지려고 노력합니다. 또한 지속적인 학습과 성장을 추구합니다."
]

TECHNICAL_ANSWERS = [
    "채용 프로세스 운영에서는 지원자 추적 시스템을 활용하고, 각 단계별 전환율을 모니터링했습니다. 병목 구간을 발견하면 즉시 개선했습니다.",
    "면접관 교육 프로그램을 만들어서 일관된 평가 기준을 수립했고, 평가 품질을 크게 향상시켰습니다.",
    "채용 공고 작성 시 직무 분석을 먼저 진행하고, 실제 업무 내용을 명확히 기술해서 적합한 지원자를 모집했습니다.",
    "교육 프로그램은 먼저 교육 니즈 분석을 하고, 목표를 명확히 설정한 후 커리큘럼을 설계했습니다.",
    "교육 효과성 측정을 위해 사전-사후 평가를 진행하고, 참여자 피드백을 수집해서 지속적으로 개선했습니다.",
    "다양한 학습 방식(강의, 워크샵, 멘토링)을 혼합해서 학습 효과를 극대화했습니다.",
    "채용 브랜딩을 위해 임직원 인터뷰 콘텐츠를 제작하고, 소셜 미디어를 통해 회사 문화를 알렸습니다.",
    "데이터 분석을 통해 어떤 채널에서 우수 인재가 많이 지원하는지 파악하고, 그쪽에 리소스를 집중했습니다.",
    "HRD 프로젝트 관리 시 이해관계자와 긴밀히 소통하고, 일정과 예산을 철저히 관리했습니다."
]

SITUATIONAL_ANSWERS = [
    """먼저 각 팀원의 의견을 충분히 듣고 정리합니다. 그리고 각 의견의 장단점을
    데이터나 과거 사례를 바탕으로 객관적으로 분석합니다. 저는 팀 전체가
    납득할 수 있는 방향으로 합의를 이끌어내는 것을 중요하게 생각합니다.""",

    """먼저 상황을 빠르게 파악하고 우선순위를 정합니다. 가장 중요하고
    긴급한 것부터 처리하되, 완벽하게 하기보다는 최소한으로 동작하는
    버전을 먼저 만드는 것을 선호합니다. 필요하면 동료에게 도움을 요청합니다.""",

    """공식 문서를 먼저 빠르게 읽고, 전체적인 개념과 구조를 파악합니다.
    그 다음 간단한 예제를 직접 만들어보면서 실습합니다. 막히는 부분이 있으면
    경험 있는 동료에게 조언을 구합니다.""",

    """제 경험상 이런 상황에서는 먼저 상황을 정확히 이해하고, 가능한
    옵션들을 빠르게 정리합니다. 그리고 팀과 논의하면서 최선의 방법을 찾습니다.""",

    """저는 새로운 도전을 긍정적으로 받아들이는 편입니다. 처음에는
    부담스럽더라도 이것이 성장의 기회라고 생각하고 적극적으로 접근합니다.""",

    """의견 차이가 있을 때는 먼저 상대방의 입장을 충분히 이해하려고 노력합니다.
    그리고 저의 생각을 논리적으로, 데이터나 근거를 들어 설명합니다."""
]


async def run_full_interview(access_token: str):
    """전체 인터뷰 플로우 실행"""

    print("\n" + "=" * 80)
    print("🚀 전체 인터뷰 플로우 테스트 시작")
    print("=" * 80)

    session_id = None

    async with httpx.AsyncClient(timeout=120.0) as client:

        # ==================== 1. General Interview ====================
        print("\n" + "=" * 80)
        print("📝 [1/5] 구조화 면접 (General Interview)")
        print("=" * 80)

        # 1-1. 시작
        print("\n[1-1] 구조화 면접 시작...")
        try:
            response = await client.post(f"{AI_URL}/api/interview/general/start")
            response.raise_for_status()
            data = response.json()
            session_id = data["session_id"]
            print(f"✅ 세션 생성 완료: {session_id}")
            print(f"첫 질문: {data['question'][:50]}...")
        except Exception as e:
            print(f"❌ 실패: {e}")
            return

        # 1-2. 5개 답변 제출
        for idx, answer in enumerate(GENERAL_ANSWERS, 1):
            print(f"\n[1-{idx+1}] {idx}번째 답변 제출...")
            try:
                response = await client.post(
                    f"{AI_URL}/api/interview/general/answer/text",
                    json={"session_id": session_id, "answer": answer}
                )
                response.raise_for_status()
                data = response.json()
                print(f"✅ 답변 제출 완료 ({idx}/5)")
                if data.get("next_question"):
                    print(f"다음 질문: {data['next_question'][:50]}...")
            except Exception as e:
                print(f"❌ {idx}번째 답변 실패: {e}")
                return

        # 1-3. 분석 결과
        print("\n[1-7] 구조화 면접 분석...")
        try:
            response = await client.get(f"{AI_URL}/api/interview/general/analysis/{session_id}")
            response.raise_for_status()
            analysis = response.json()
            print(f"✅ 분석 완료")
            print(f"   - 주요 테마: {', '.join(analysis.get('key_themes', [])[:3])}")
            print(f"   - 관심 분야: {', '.join(analysis.get('interests', [])[:3])}")
        except Exception as e:
            print(f"❌ 분석 실패: {e}")
            return

        # ==================== 2. Technical Interview ====================
        print("\n" + "=" * 80)
        print("💼 [2/5] 직무 적합성 면접 (Technical Interview)")
        print("=" * 80)

        # 2-1. 시작
        print("\n[2-1] 직무 면접 시작...")
        try:
            response = await client.post(
                f"{AI_URL}/api/interview/technical/start",
                json={"session_id": session_id, "access_token": access_token}
            )
            response.raise_for_status()
            data = response.json()
            print(f"✅ 기술 선정 완료: {', '.join(data.get('selected_skills', []))}")
            print(f"첫 질문: {data['question'][:50]}...")
        except Exception as e:
            print(f"❌ 실패: {e}")
            return

        # 2-2. 9개 답변 제출
        for idx, answer in enumerate(TECHNICAL_ANSWERS, 1):
            print(f"\n[2-{idx+1}] {idx}번째 답변 제출...")
            try:
                response = await client.post(
                    f"{AI_URL}/api/interview/technical/answer",
                    json={"session_id": session_id, "answer": answer}
                )
                response.raise_for_status()
                data = response.json()
                print(f"✅ 답변 제출 완료 ({idx}/9)")

                if data.get("next_question"):
                    next_q = data["next_question"]
                    print(f"다음 질문 ({next_q.get('progress', '')}): {next_q.get('question', '')[:50]}...")
                else:
                    print("✅ 직무 면접 완료!")
                    break
            except Exception as e:
                print(f"❌ {idx}번째 답변 실패: {e}")
                return

        # 2-3. 결과 조회
        print("\n[2-11] 직무 면접 결과...")
        try:
            response = await client.get(f"{AI_URL}/api/interview/technical/results/{session_id}")
            response.raise_for_status()
            results = response.json()
            print(f"✅ 평가 완료")
            print(f"   - 평가된 기술: {', '.join(results.get('skills_evaluated', []))}")
        except Exception as e:
            print(f"❌ 결과 조회 실패: {e}")
            return

        # ==================== 3. Situational Interview ====================
        print("\n" + "=" * 80)
        print("🎭 [3/5] 상황 면접 (Situational Interview)")
        print("=" * 80)

        # 3-1. 시작
        print("\n[3-1] 상황 면접 시작...")
        try:
            response = await client.post(
                f"{AI_URL}/api/interview/situational/start",
                params={"session_id": session_id}
            )
            response.raise_for_status()
            data = response.json()
            print(f"✅ 상황 면접 시작")
            print(f"첫 질문: {data['question'][:50]}...")
        except Exception as e:
            print(f"❌ 실패: {e}")
            return

        # 3-2. 6개 답변 제출
        for idx, answer in enumerate(SITUATIONAL_ANSWERS, 1):
            print(f"\n[3-{idx+1}] {idx}번째 답변 제출...")
            try:
                response = await client.post(
                    f"{AI_URL}/api/interview/situational/answer",
                    json={"session_id": session_id, "answer": answer.strip()}
                )
                response.raise_for_status()
                data = response.json()
                print(f"✅ 답변 제출 완료 ({idx}/6)")

                if data.get("next_question"):
                    next_q = data["next_question"]
                    print(f"다음 질문: {next_q.get('question', '')[:50]}...")
                else:
                    print("✅ 상황 면접 완료!")
                    break
            except Exception as e:
                print(f"❌ {idx}번째 답변 실패: {e}")
                return

        # 3-3. 페르소나 리포트
        print("\n[3-8] 페르소나 리포트 조회...")
        try:
            response = await client.get(f"{AI_URL}/api/interview/situational/report/{session_id}")
            response.raise_for_status()
            report = response.json()
            persona = report.get("persona", {})
            print(f"✅ 페르소나 분석 완료")
            print(f"   - 업무 스타일: {persona.get('work_style', '알 수 없음')}")
            print(f"   - 문제 해결: {persona.get('problem_solving', '알 수 없음')}")
            print(f"   - 학습 성향: {persona.get('learning', '알 수 없음')}")
            print(f"   - 요약: {report.get('summary', '')}")
        except Exception as e:
            print(f"❌ 리포트 조회 실패: {e}")
            return

        # ==================== 4. Profile Card Generation ====================
        print("\n" + "=" * 80)
        print("🎴 [4/5] 프로필 카드 생성 (Profile Card)")
        print("=" * 80)

        print("\n[4-1] 프로필 카드 생성 및 백엔드 전송...")
        try:
            response = await client.post(
                f"{AI_URL}/api/interview/profile-card/generate-and-post",
                json={"session_id": session_id, "access_token": access_token},
                timeout=120.0
            )
            response.raise_for_status()
            card_data = response.json()

            card = card_data.get("card", {})
            backend_resp = card_data.get("backend_response", {})

            print(f"✅ 프로필 카드 생성 완료!")
            print(f"\n📊 카드 미리보기:")
            print(f"   - 헤드라인: {card.get('headline', '')[:60]}...")
            print(f"   - 주요 경험: {len(card.get('key_experiences', []))}개")
            print(f"   - 핵심 역량: {len(card.get('core_competencies', []))}개")
            print(f"   - 강점: {len(card.get('strengths', []))}개")
            print(f"   - 직무 수행: {card.get('performance_summary', '')[:60]}...")
            print(f"   - 협업 성향: {card.get('collaboration_style', '')[:60]}...")
            print(f"   - 성장 가능성: {card.get('growth_potential', '')[:60]}...")

            if backend_resp.get("status") == "conflict":
                print(f"\n⚠️  백엔드: 기존 카드 사용 (409 Conflict)")
            else:
                print(f"\n✅ 백엔드: 카드 저장 완료")

        except Exception as e:
            print(f"❌ 카드 생성 실패: {e}")
            if hasattr(e, 'response'):
                print(f"   응답: {e.response.text if hasattr(e.response, 'text') else e.response}")
            return

        # ==================== 5. Matching Vectors ====================
        print("\n" + "=" * 80)
        print("🎯 [5/5] 매칭 벡터 생성 (Matching Vectors)")
        print("=" * 80)

        print("\n[5-1] 매칭 벡터 생성 및 백엔드 전송...")
        try:
            response = await client.post(
                f"{AI_URL}/api/interview/matching-vectors/generate",
                json={"session_id": session_id, "access_token": access_token},
                timeout=120.0
            )
            response.raise_for_status()
            vector_data = response.json()

            texts = vector_data.get("texts", {})
            vectors = vector_data.get("vectors", {})
            backend_resp = vector_data.get("backend_response", {})

            print(f"✅ 매칭 벡터 생성 완료!")
            print(f"\n🎯 생성된 벡터:")
            for key in ["vector_roles", "vector_skills", "vector_growth",
                       "vector_career", "vector_vision", "vector_culture"]:
                if key in vectors:
                    text_key = key.replace("vector_", "")
                    print(f"   - {text_key}: {texts.get(text_key, '')[:60]}...")

            if backend_resp.get("status") == "conflict":
                print(f"\n⚠️  백엔드: 기존 벡터 사용 (409 Conflict)")
            else:
                print(f"\n✅ 백엔드: 벡터 저장 완료")

        except Exception as e:
            print(f"❌ 벡터 생성 실패: {e}")
            if hasattr(e, 'response'):
                print(f"   응답: {e.response.text if hasattr(e.response, 'text') else e.response}")
            return

        # ==================== 완료! ====================
        print("\n" + "=" * 80)
        print("✅ 전체 인터뷰 플로우 완료!")
        print("=" * 80)
        print(f"\n세션 ID: {session_id}")
        print(f"총 단계: 5단계 (General → Technical → Situational → Card → Vectors)")
        print(f"총 답변: {len(GENERAL_ANSWERS) + len(TECHNICAL_ANSWERS) + len(SITUATIONAL_ANSWERS)}개")
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🎤 전체 인터뷰 플로우 테스트")
    print("=" * 80)

    # JWT 토큰 입력 받기
    if len(sys.argv) > 1:
        access_token = sys.argv[1]
        print(f"\n✅ JWT 토큰이 인자로 제공되었습니다.")
    else:
        print("\n💡 JWT 액세스 토큰을 입력해주세요.")
        print("   (브라우저 개발자도구 > Application > Local Storage에서 확인)")
        access_token = input("\n토큰: ").strip()

        if not access_token:
            print("\n❌ 토큰이 입력되지 않았습니다. 종료합니다.")
            sys.exit(1)

    print(f"\nAI 서버: {AI_URL}")
    print(f"백엔드 서버: {BACKEND_URL}")
    print(f"토큰 길이: {len(access_token)} 문자")
    print("\n전체 플로우를 자동으로 실행합니다...\n")

    try:
        asyncio.run(run_full_interview(access_token))
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자가 중단했습니다.")
    except Exception as e:
        print(f"\n\n❌ 예외 발생: {e}")
        import traceback
        traceback.print_exc()
