⏺ 🎯 4단계 구현 계획

  1단계: 필터 시스템 ⚡ (빠른 효과)

  # 새로 만들어야 할 것
  class RequirementFilter:
      def filter_candidates(self, candidates, job_requirements):
          # 지역, 근무형태, 연차, 급여, 언어 필터
          return filtered_candidates

  2단계: 필드별 벡터 매칭 🎯 (현재 시스템 확장)

  # 현재 single vector → multiple vectors
  {
      "skills_vector": [...],      # 기술 스킬만
      "title_vector": [...],       # 직무명만  
      "experience_vector": [...],  # 경력 요약만
      "general_vector": [...]      # 전체 프로필
  }

  3단계: 가중치 점수 조합 📊 (비즈니스 로직)

  final_score = (
      skills_similarity * 0.5 +
      title_similarity * 0.2 +
      experience_similarity * 0.2 +
      location_salary_bonus * 0.1
  )

  4단계: 리랭커 🧠 (고도화)

  # GPT로 "이 사람 ↔ 이 공고" 세밀 평가
  reranker_prompt = f"Rate match quality: {candidate_summary} vs {job_summary}"
