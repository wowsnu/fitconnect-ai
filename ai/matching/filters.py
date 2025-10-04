"""
필수조건 필터 시스템
지역, 근무형태, 연차, 급여, 언어 등 하드 조건으로 후보 필터링
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FilterOperator(str, Enum):
    """필터 연산자"""
    EQUALS = "equals"
    GREATER_THAN = "gt"
    GREATER_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    RANGE = "range"


@dataclass
class FilterRule:
    """개별 필터 규칙"""
    field: str                    # 필터링할 필드명
    operator: FilterOperator      # 연산자
    value: Any                   # 비교값
    required: bool = True        # 필수 조건 여부


@dataclass
class FilterResult:
    """필터링 결과"""
    passed: bool                 # 통과 여부
    failed_rules: List[str]      # 실패한 규칙들
    reason: str                  # 실패 이유


class RequirementFilter:
    """필수조건 필터 클래스"""

    def __init__(self):
        """필터 초기화"""
        self.default_rules = self._get_default_rules()
        logger.info("RequirementFilter initialized")

    def _get_default_rules(self) -> Dict[str, List[FilterRule]]:
        """기본 필터 규칙들"""
        return {
            "location": [
                FilterRule("work_location", FilterOperator.IN, [], required=True),
                FilterRule("remote_work", FilterOperator.EQUALS, True, required=False)
            ],
            "experience": [
                FilterRule("years_experience", FilterOperator.GREATER_EQUAL, 0, required=True),
                FilterRule("relevant_experience", FilterOperator.GREATER_EQUAL, 0, required=False)
            ],
            "salary": [
                FilterRule("salary_min", FilterOperator.GREATER_EQUAL, 0, required=False),
                FilterRule("salary_max", FilterOperator.LESS_EQUAL, 999999, required=False)
            ],
            "employment": [
                FilterRule("employment_type", FilterOperator.IN, [], required=True)
            ],
            "language": [
                FilterRule("korean_level", FilterOperator.GREATER_EQUAL, 1, required=False),
                FilterRule("english_level", FilterOperator.GREATER_EQUAL, 1, required=False)
            ],
            "visa": [
                FilterRule("visa_status", FilterOperator.IN, [], required=False),
                FilterRule("work_permit", FilterOperator.EQUALS, True, required=False)
            ]
        }

    def filter_candidates(
        self,
        candidates: List[Dict[str, Any]],
        job_requirements: Dict[str, Any],
        custom_rules: Optional[List[FilterRule]] = None
    ) -> List[Dict[str, Any]]:
        """
        구직자 후보들을 필수조건으로 필터링

        Args:
            candidates: 구직자 후보 리스트
            job_requirements: 채용공고 요구사항
            custom_rules: 커스텀 필터 규칙들

        Returns:
            필터링된 구직자 리스트
        """
        try:
            # 필터 규칙 생성
            filter_rules = self._build_filter_rules(job_requirements, custom_rules)

            filtered_candidates = []

            for candidate in candidates:
                filter_result = self._apply_filters(candidate, filter_rules)

                if filter_result.passed:
                    # 필터 통과한 후보만 추가
                    candidate["filter_passed"] = True
                    candidate["filter_reason"] = "All requirements met"
                    filtered_candidates.append(candidate)
                else:
                    # 디버깅용 로그
                    logger.debug(f"Candidate {candidate.get('id', 'unknown')} filtered out: {filter_result.reason}")

                    # 선택적으로 실패 이유도 포함 (디버깅용)
                    candidate["filter_passed"] = False
                    candidate["filter_reason"] = filter_result.reason

            logger.info(f"Filtered {len(candidates)} → {len(filtered_candidates)} candidates")
            return filtered_candidates

        except Exception as e:
            logger.error(f"Failed to filter candidates: {e}")
            # 에러 시 원본 반환 (안전장치)
            return candidates

    def filter_jobs(
        self,
        jobs: List[Dict[str, Any]],
        applicant_preferences: Dict[str, Any],
        custom_rules: Optional[List[FilterRule]] = None
    ) -> List[Dict[str, Any]]:
        """
        채용공고를 지원자 선호조건으로 필터링

        Args:
            jobs: 채용공고 리스트
            applicant_preferences: 지원자 선호조건
            custom_rules: 커스텀 필터 규칙들

        Returns:
            필터링된 채용공고 리스트
        """
        try:
            # 역방향 필터 규칙 생성 (지원자 관점)
            filter_rules = self._build_reverse_filter_rules(applicant_preferences, custom_rules)

            filtered_jobs = []

            for job in jobs:
                filter_result = self._apply_filters(job, filter_rules)

                if filter_result.passed:
                    job["filter_passed"] = True
                    job["filter_reason"] = "Matches preferences"
                    filtered_jobs.append(job)
                else:
                    logger.debug(f"Job {job.get('id', 'unknown')} filtered out: {filter_result.reason}")
                    job["filter_passed"] = False
                    job["filter_reason"] = filter_result.reason

            logger.info(f"Filtered {len(jobs)} → {len(filtered_jobs)} jobs")
            return filtered_jobs

        except Exception as e:
            logger.error(f"Failed to filter jobs: {e}")
            return jobs

    def _build_filter_rules(
        self,
        job_requirements: Dict[str, Any],
        custom_rules: Optional[List[FilterRule]] = None
    ) -> List[FilterRule]:
        """채용공고 요구사항을 기반으로 필터 규칙 구성"""
        rules = []

        # 1. 근무지 필터
        if "work_locations" in job_requirements:
            rules.append(FilterRule(
                "preferred_locations",
                FilterOperator.IN,
                job_requirements["work_locations"],
                required=True
            ))

        # 2. 경력 필터
        if "min_experience_years" in job_requirements:
            rules.append(FilterRule(
                "years_experience",
                FilterOperator.GREATER_EQUAL,
                job_requirements["min_experience_years"],
                required=True
            ))

        # 3. 급여 필터
        if "salary_range" in job_requirements:
            salary_range = job_requirements["salary_range"]
            if "min" in salary_range:
                rules.append(FilterRule(
                    "salary_expectation_max",
                    FilterOperator.GREATER_EQUAL,
                    salary_range["min"],
                    required=False
                ))

        # 4. 고용형태 필터
        if "employment_types" in job_requirements:
            rules.append(FilterRule(
                "preferred_employment_types",
                FilterOperator.IN,
                job_requirements["employment_types"],
                required=True
            ))

        # 5. 언어 요구사항
        if "language_requirements" in job_requirements:
            lang_req = job_requirements["language_requirements"]
            if "korean_level" in lang_req:
                rules.append(FilterRule(
                    "korean_level",
                    FilterOperator.GREATER_EQUAL,
                    lang_req["korean_level"],
                    required=True
                ))
            if "english_level" in lang_req:
                rules.append(FilterRule(
                    "english_level",
                    FilterOperator.GREATER_EQUAL,
                    lang_req["english_level"],
                    required=False
                ))

        # 6. 비자/취업허가
        if "visa_requirements" in job_requirements:
            rules.append(FilterRule(
                "visa_status",
                FilterOperator.IN,
                job_requirements["visa_requirements"],
                required=True
            ))

        # 커스텀 규칙 추가
        if custom_rules:
            rules.extend(custom_rules)

        logger.debug(f"Built {len(rules)} filter rules")
        return rules

    def _build_reverse_filter_rules(
        self,
        applicant_preferences: Dict[str, Any],
        custom_rules: Optional[List[FilterRule]] = None
    ) -> List[FilterRule]:
        """지원자 선호조건을 기반으로 역방향 필터 규칙 구성"""
        rules = []

        # 1. 선호 근무지
        if "preferred_locations" in applicant_preferences:
            rules.append(FilterRule(
                "work_locations",
                FilterOperator.IN,
                applicant_preferences["preferred_locations"],
                required=True
            ))

        # 2. 희망 급여
        if "salary_expectations" in applicant_preferences:
            salary_exp = applicant_preferences["salary_expectations"]
            if "min" in salary_exp:
                rules.append(FilterRule(
                    "salary_range_max",
                    FilterOperator.GREATER_EQUAL,
                    salary_exp["min"],
                    required=False
                ))

        # 3. 고용형태 선호
        if "preferred_employment_types" in applicant_preferences:
            rules.append(FilterRule(
                "employment_types",
                FilterOperator.IN,
                applicant_preferences["preferred_employment_types"],
                required=True
            ))

        # 커스텀 규칙 추가
        if custom_rules:
            rules.extend(custom_rules)

        return rules

    def _apply_filters(self, candidate: Dict[str, Any], rules: List[FilterRule]) -> FilterResult:
        """개별 후보에 필터 규칙들 적용"""
        failed_rules = []

        for rule in rules:
            if not self._check_rule(candidate, rule):
                if rule.required:
                    # 필수 조건 실패 시 즉시 탈락
                    return FilterResult(
                        passed=False,
                        failed_rules=[rule.field],
                        reason=f"Required condition failed: {rule.field}"
                    )
                else:
                    # 선택 조건 실패는 기록만
                    failed_rules.append(rule.field)

        # 모든 필수 조건 통과
        return FilterResult(
            passed=True,
            failed_rules=failed_rules,
            reason="All required conditions met"
        )

    def _check_rule(self, data: Dict[str, Any], rule: FilterRule) -> bool:
        """개별 필터 규칙 체크"""
        try:
            field_value = data.get(rule.field)

            # 필드가 없는 경우
            if field_value is None:
                return not rule.required  # 선택 조건이면 통과

            # 연산자별 체크
            if rule.operator == FilterOperator.EQUALS:
                return field_value == rule.value

            elif rule.operator == FilterOperator.GREATER_THAN:
                return field_value > rule.value

            elif rule.operator == FilterOperator.GREATER_EQUAL:
                return field_value >= rule.value

            elif rule.operator == FilterOperator.LESS_THAN:
                return field_value < rule.value

            elif rule.operator == FilterOperator.LESS_EQUAL:
                return field_value <= rule.value

            elif rule.operator == FilterOperator.IN:
                if isinstance(field_value, list):
                    # 교집합이 있으면 통과
                    return bool(set(field_value) & set(rule.value))
                else:
                    # 단일 값이 리스트에 포함되면 통과
                    return field_value in rule.value

            elif rule.operator == FilterOperator.NOT_IN:
                return field_value not in rule.value

            elif rule.operator == FilterOperator.CONTAINS:
                if isinstance(field_value, str):
                    return rule.value in field_value
                elif isinstance(field_value, list):
                    return rule.value in field_value

            elif rule.operator == FilterOperator.RANGE:
                if isinstance(rule.value, dict) and "min" in rule.value and "max" in rule.value:
                    return rule.value["min"] <= field_value <= rule.value["max"]

            return False

        except Exception as e:
            logger.warning(f"Failed to check rule {rule.field}: {e}")
            return not rule.required  # 에러 시 선택조건은 통과

    def get_filter_summary(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """필터링 결과 요약"""
        total = len(candidates)
        passed = len([c for c in candidates if c.get("filter_passed", False)])

        return {
            "total_candidates": total,
            "passed_filter": passed,
            "filtered_out": total - passed,
            "pass_rate": passed / total if total > 0 else 0
        }


# 편의를 위한 전역 인스턴스
_filter_service = None

def get_filter_service() -> RequirementFilter:
    """필터 서비스 싱글톤 인스턴스 반환"""
    global _filter_service
    if _filter_service is None:
        _filter_service = RequirementFilter()
    return _filter_service