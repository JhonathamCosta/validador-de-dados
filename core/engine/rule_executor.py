from time import perf_counter

from core.contracts import RuleOutput
from core.models.rule_result import RuleResult


def execute_rule(rule, bundle, context) -> RuleResult:
    start = perf_counter()

    rule_name = getattr(rule, "name", rule.__class__.__name__)
    rule_id = getattr(rule, "rule_id", rule_name)

    try:
        raw: RuleOutput = rule.run(bundle, context) or {}

        count = int(raw.get("count", 0))
        status = raw.get("status", "PASS" if count == 0 else "FAIL")

        return RuleResult(
            rule_id=rule_id,
            rule_name=rule_name,
            status=status,
            severity=raw.get("severity", "MEDIUM"),
            count=count,
            message=raw.get("message"),
            details=raw.get("details", []),
            duration_ms=(perf_counter() - start) * 1000,
        )

    except Exception as exc:
        return RuleResult(
            rule_id=rule_id,
            rule_name=rule_name,
            status="ERROR",
            severity="CRITICAL",
            count=0,
            message=str(exc),
            details=[],
            duration_ms=(perf_counter() - start) * 1000,
        )
