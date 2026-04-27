from core.models.validation_report import ValidationReport
from core.models.rule_result import RuleResult
from typing import List

def build_report(
        template_id: str, 
        results: List[RuleResult], 
        duration_ms: float
) -> ValidationReport:
    total_rules = len(results)

    total_pass = sum(1 for r in results if r.status == "PASS")
    total_fail = sum(1 for r in results if r.status == "FAIL")
    total_warning = sum(1 for r in results if r.status == "WARNING")
    total_error = sum(1 for r in results if r.status == "ERROR")

    return ValidationReport(
        template_id=template_id,
        total_rules=total_rules,
        total_pass=total_pass,
        total_fail=total_fail,
        total_warning=total_warning,
        total_error=total_error,
        results=results,
        duration_ms=duration_ms
    )