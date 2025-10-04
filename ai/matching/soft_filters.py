"""
소프트 필터링 시스템 (가중치 기반)
조건 불일치 시 탈락이 아닌 점수 페널티 적용
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math

logger = logging.getLogger(__name__)


class CompatibilityLevel(str, Enum):
    """호환성 레벨"""
    PERFECT = "perfect"      # 1.0
    EXCELLENT = "excellent"  # 0.9-0.99
    GOOD = "good"           # 0.7-0.89
    FAIR = "fair"           # 0.5-0.69
    POOR = "poor"           # 0.2-0.49
    INCOMPATIBLE = "incompatible"  # 0.0-0.19


@dataclass
class FilterWeight:
    """필터 가중치 설정"""
    field: str              # 필터 필드명
    importance: float       # 중요도 (0.0 ~ 1.0)
    enabled: bool = True    # 필터 활성화 여부


@dataclass
class CompatibilityScore:
    """호환성 점수 결과"""
    field: str              # 필터 필드
    score: float           # 호환성 점수 (0.0 ~ 1.0)
    level: CompatibilityLevel  # 호환성 레벨
    reason: str            # 점수 산출 이유
    penalty: float         # 적용된 페널티 (1.0 - score)


@dataclass
class SoftFilterResult:
    """소프트 필터링 결과"""
    overall_score: float                    # 전체 호환성 점수
    field_scores: List[CompatibilityScore]  # 필드별 점수들
    applied_weights: Dict[str, float]       # 적용된 가중치들
    summary: str                           # 결과 요약


class SoftFilterService:
    """가중치 기반 소프트 필터링 서비스"""

    def __init__(self):
        """필터 서비스 초기화"""
        self.default_weights = self._get_default_weights()
        self.compatibility_calculators = self._setup_calculators()
        logger.info("SoftFilterService initialized")

    def _get_default_weights(self) -> Dict[str, FilterWeight]:
        """기본 필터 가중치 설정"""
        return {
            "location": FilterWeight("location", importance=0.8),      # 지역 80% 중요
            "experience": FilterWeight("experience", importance=0.9),  # 경력 90% 중요
            "salary": FilterWeight("salary", importance=0.7),          # 급여 70% 중요
            "employment": FilterWeight("employment", importance=0.6),   # 고용형태 60% 중요
            "language": FilterWeight("language", importance=0.5),      # 언어 50% 중요
            "company_culture": FilterWeight("company_culture", importance=0.4),  # 문화 40% 중요
            "remote_work": FilterWeight("remote_work", importance=0.3) # 원격근무 30% 중요
        }

    def _setup_calculators(self) -> Dict[str, callable]:
        """필드별 호환성 계산 함수들"""
        return {
            "location": self._calculate_location_compatibility,
            "experience": self._calculate_experience_compatibility,
            "salary": self._calculate_salary_compatibility,
            "employment": self._calculate_employment_compatibility,
            "language": self._calculate_language_compatibility,
            "remote_work": self._calculate_remote_work_compatibility
        }

    def calculate_compatibility(
        self,
        candidate_data: Dict[str, Any],
        requirements: Dict[str, Any],
        custom_weights: Optional[Dict[str, float]] = None
    ) -> SoftFilterResult:
        """
        후보와 요구사항 간 전체 호환성 계산

        Args:
            candidate_data: 후보자 데이터
            requirements: 요구사항 데이터
            custom_weights: 커스텀 가중치

        Returns:
            SoftFilterResult with overall compatibility score
        """
        try:
            # 가중치 설정
            weights = self._merge_weights(custom_weights)

            field_scores = []
            weighted_sum = 0.0
            total_weight = 0.0

            # 필드별 호환성 계산
            for field_name, weight_config in weights.items():
                if not weight_config.enabled:
                    continue

                calculator = self.compatibility_calculators.get(field_name)
                if not calculator:
                    continue

                try:
                    compatibility = calculator(candidate_data, requirements)
                    field_scores.append(compatibility)

                    # 가중 평균 계산
                    weighted_sum += compatibility.score * weight_config.importance
                    total_weight += weight_config.importance

                except Exception as e:
                    logger.warning(f"Failed to calculate {field_name} compatibility: {e}")
                    # 에러 시 중립 점수 (0.5) 사용
                    neutral_score = CompatibilityScore(
                        field=field_name,
                        score=0.5,
                        level=CompatibilityLevel.FAIR,
                        reason=f"Calculation error: {str(e)}",
                        penalty=0.5
                    )
                    field_scores.append(neutral_score)
                    weighted_sum += 0.5 * weight_config.importance
                    total_weight += weight_config.importance

            # 전체 호환성 점수 계산
            overall_score = weighted_sum / total_weight if total_weight > 0 else 0.5

            # 적용된 가중치 정보
            applied_weights = {
                name: config.importance
                for name, config in weights.items()
                if config.enabled
            }

            # 결과 요약
            summary = self._generate_summary(overall_score, field_scores)

            return SoftFilterResult(
                overall_score=overall_score,
                field_scores=field_scores,
                applied_weights=applied_weights,
                summary=summary
            )

        except Exception as e:
            logger.error(f"Failed to calculate compatibility: {e}")
            # 에러 시 중립 결과 반환
            return SoftFilterResult(
                overall_score=0.5,
                field_scores=[],
                applied_weights={},
                summary="Error occurred during compatibility calculation"
            )

    def _calculate_location_compatibility(
        self,
        candidate_data: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> CompatibilityScore:
        """지역 호환성 계산"""
        candidate_locations = candidate_data.get("preferred_locations", [])
        required_locations = requirements.get("work_locations", [])
        remote_allowed = requirements.get("remote_work_allowed", False)

        # 완전 일치
        if set(candidate_locations) & set(required_locations):
            return CompatibilityScore(
                field="location",
                score=1.0,
                level=CompatibilityLevel.PERFECT,
                reason="Location preferences match exactly",
                penalty=0.0
            )

        # 원격근무 가능
        if remote_allowed and "원격" in candidate_locations:
            return CompatibilityScore(
                field="location",
                score=0.9,
                level=CompatibilityLevel.EXCELLENT,
                reason="Remote work available and preferred",
                penalty=0.1
            )

        # 같은 도시권 (서울-경기 등)
        if self._is_nearby_area(candidate_locations, required_locations):
            return CompatibilityScore(
                field="location",
                score=0.7,
                level=CompatibilityLevel.GOOD,
                reason="Nearby area, commuting possible",
                penalty=0.3
            )

        # 완전 불일치
        return CompatibilityScore(
            field="location",
            score=0.2,
            level=CompatibilityLevel.POOR,
            reason="Location mismatch, relocation required",
            penalty=0.8
        )

    def _calculate_experience_compatibility(
        self,
        candidate_data: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> CompatibilityScore:
        """경력 호환성 계산"""
        candidate_exp = candidate_data.get("years_experience", 0)
        required_min = requirements.get("min_experience_years", 0)
        required_max = requirements.get("max_experience_years", 999)

        # 요구 범위 내
        if required_min <= candidate_exp <= required_max:
            if candidate_exp >= required_min * 1.5:  # 50% 이상 초과
                return CompatibilityScore(
                    field="experience",
                    score=1.0,
                    level=CompatibilityLevel.PERFECT,
                    reason=f"Experience exceeds requirement ({candidate_exp}y >= {required_min}y)",
                    penalty=0.0
                )
            else:
                return CompatibilityScore(
                    field="experience",
                    score=0.9,
                    level=CompatibilityLevel.EXCELLENT,
                    reason=f"Experience meets requirement ({candidate_exp}y >= {required_min}y)",
                    penalty=0.1
                )

        # 경력 부족
        if candidate_exp < required_min:
            gap = required_min - candidate_exp
            score = max(0.1, 1.0 - (gap / required_min) * 0.8)  # 부족할수록 점수 감소

            if score >= 0.6:
                level = CompatibilityLevel.FAIR
                reason = f"Slightly below requirement ({candidate_exp}y < {required_min}y)"
            else:
                level = CompatibilityLevel.POOR
                reason = f"Significantly below requirement ({candidate_exp}y << {required_min}y)"

            return CompatibilityScore(
                field="experience",
                score=score,
                level=level,
                reason=reason,
                penalty=1.0 - score
            )

        # 경력 과다 (오버스펙)
        if candidate_exp > required_max:
            return CompatibilityScore(
                field="experience",
                score=0.7,
                level=CompatibilityLevel.GOOD,
                reason=f"Overqualified ({candidate_exp}y > {required_max}y)",
                penalty=0.3
            )

    def _calculate_salary_compatibility(
        self,
        candidate_data: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> CompatibilityScore:
        """급여 호환성 계산"""
        candidate_min = candidate_data.get("salary_expectation_min", 0)
        candidate_max = candidate_data.get("salary_expectation_max", 999999)
        offer_min = requirements.get("salary_range", {}).get("min", 0)
        offer_max = requirements.get("salary_range", {}).get("max", 999999)

        # 범위 겹침 계산
        overlap_min = max(candidate_min, offer_min)
        overlap_max = min(candidate_max, offer_max)

        if overlap_min <= overlap_max:
            # 겹치는 범위가 있음
            overlap_ratio = (overlap_max - overlap_min) / (candidate_max - candidate_min + 1)
            score = 0.7 + overlap_ratio * 0.3  # 0.7 ~ 1.0

            return CompatibilityScore(
                field="salary",
                score=score,
                level=CompatibilityLevel.EXCELLENT if score >= 0.9 else CompatibilityLevel.GOOD,
                reason=f"Salary ranges overlap ({overlap_ratio:.1%} match)",
                penalty=1.0 - score
            )

        # 후보 희망이 더 높음
        if candidate_min > offer_max:
            gap_ratio = (candidate_min - offer_max) / offer_max
            score = max(0.2, 1.0 - gap_ratio)

            return CompatibilityScore(
                field="salary",
                score=score,
                level=CompatibilityLevel.FAIR if score >= 0.5 else CompatibilityLevel.POOR,
                reason=f"Candidate expects higher salary ({gap_ratio:.1%} gap)",
                penalty=1.0 - score
            )

        # 후보 희망이 더 낮음 (문제없음)
        return CompatibilityScore(
            field="salary",
            score=0.9,
            level=CompatibilityLevel.EXCELLENT,
            reason="Candidate salary expectation is within budget",
            penalty=0.1
        )

    def _calculate_employment_compatibility(
        self,
        candidate_data: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> CompatibilityScore:
        """고용형태 호환성 계산"""
        candidate_types = candidate_data.get("preferred_employment_types", [])
        required_types = requirements.get("employment_types", [])

        # 일치하는 고용형태가 있음
        if set(candidate_types) & set(required_types):
            return CompatibilityScore(
                field="employment",
                score=1.0,
                level=CompatibilityLevel.PERFECT,
                reason="Employment type preferences match",
                penalty=0.0
            )

        # 유사한 고용형태 (정규직-계약직 등)
        if self._is_similar_employment_type(candidate_types, required_types):
            return CompatibilityScore(
                field="employment",
                score=0.7,
                level=CompatibilityLevel.GOOD,
                reason="Similar employment types available",
                penalty=0.3
            )

        # 불일치
        return CompatibilityScore(
            field="employment",
            score=0.3,
            level=CompatibilityLevel.POOR,
            reason="Employment type mismatch",
            penalty=0.7
        )

    def _calculate_language_compatibility(
        self,
        candidate_data: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> CompatibilityScore:
        """언어 호환성 계산"""
        candidate_korean = candidate_data.get("korean_level", 1)
        candidate_english = candidate_data.get("english_level", 1)
        required_korean = requirements.get("language_requirements", {}).get("korean_level", 1)
        required_english = requirements.get("language_requirements", {}).get("english_level", 1)

        korean_score = min(1.0, candidate_korean / required_korean) if required_korean > 0 else 1.0
        english_score = min(1.0, candidate_english / required_english) if required_english > 0 else 1.0

        # 평균 점수
        overall_score = (korean_score + english_score) / 2

        if overall_score >= 0.9:
            level = CompatibilityLevel.PERFECT
            reason = "Language requirements fully met"
        elif overall_score >= 0.7:
            level = CompatibilityLevel.GOOD
            reason = "Language requirements mostly met"
        elif overall_score >= 0.5:
            level = CompatibilityLevel.FAIR
            reason = "Language requirements partially met"
        else:
            level = CompatibilityLevel.POOR
            reason = "Language requirements not met"

        return CompatibilityScore(
            field="language",
            score=overall_score,
            level=level,
            reason=reason,
            penalty=1.0 - overall_score
        )

    def _calculate_remote_work_compatibility(
        self,
        candidate_data: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> CompatibilityScore:
        """원격근무 호환성 계산"""
        candidate_remote_ok = candidate_data.get("remote_work_ok", False)
        job_remote_allowed = requirements.get("remote_work_allowed", False)

        if candidate_remote_ok and job_remote_allowed:
            return CompatibilityScore(
                field="remote_work",
                score=1.0,
                level=CompatibilityLevel.PERFECT,
                reason="Remote work preferred and available",
                penalty=0.0
            )
        elif not candidate_remote_ok and not job_remote_allowed:
            return CompatibilityScore(
                field="remote_work",
                score=1.0,
                level=CompatibilityLevel.PERFECT,
                reason="Both prefer office work",
                penalty=0.0
            )
        elif candidate_remote_ok and not job_remote_allowed:
            return CompatibilityScore(
                field="remote_work",
                score=0.6,
                level=CompatibilityLevel.FAIR,
                reason="Candidate prefers remote but office required",
                penalty=0.4
            )
        else:  # job allows remote but candidate doesn't prefer
            return CompatibilityScore(
                field="remote_work",
                score=0.8,
                level=CompatibilityLevel.GOOD,
                reason="Remote work available as option",
                penalty=0.2
            )

    def _merge_weights(self, custom_weights: Optional[Dict[str, float]]) -> Dict[str, FilterWeight]:
        """기본 가중치와 커스텀 가중치 병합"""
        weights = self.default_weights.copy()

        if custom_weights:
            for field, importance in custom_weights.items():
                if field in weights:
                    weights[field].importance = importance
                else:
                    weights[field] = FilterWeight(field, importance)

        return weights

    def _is_nearby_area(self, locations1: List[str], locations2: List[str]) -> bool:
        """인근 지역 여부 판단"""
        nearby_groups = [
            {"서울", "경기", "인천"},
            {"부산", "울산", "경남"},
            {"대구", "경북"},
            {"대전", "충남", "충북"},
            {"광주", "전남", "전북"}
        ]

        for group in nearby_groups:
            if any(loc in group for loc in locations1) and any(loc in group for loc in locations2):
                return True
        return False

    def _is_similar_employment_type(self, types1: List[str], types2: List[str]) -> bool:
        """유사한 고용형태 여부 판단"""
        similar_groups = [
            {"정규직", "계약직"},
            {"프리랜서", "외주", "계약직"},
            {"인턴", "계약직"}
        ]

        for group in similar_groups:
            if any(t in group for t in types1) and any(t in group for t in types2):
                return True
        return False

    def _generate_summary(self, overall_score: float, field_scores: List[CompatibilityScore]) -> str:
        """호환성 결과 요약 생성"""
        if overall_score >= 0.9:
            return "Excellent match - highly compatible"
        elif overall_score >= 0.7:
            return "Good match - mostly compatible with minor gaps"
        elif overall_score >= 0.5:
            return "Fair match - some compatibility issues"
        elif overall_score >= 0.3:
            return "Poor match - significant compatibility issues"
        else:
            return "Incompatible - major mismatches"


# 편의를 위한 전역 인스턴스
_soft_filter_service = None

def get_soft_filter_service() -> SoftFilterService:
    """소프트 필터 서비스 싱글톤 인스턴스 반환"""
    global _soft_filter_service
    if _soft_filter_service is None:
        _soft_filter_service = SoftFilterService()
    return _soft_filter_service