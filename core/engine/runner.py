from time import perf_counter

from .rule_executor import execute_rule
from core.services.build_result import build_report


def run_validation(bundle, rules, context, template_id="default"):
    start = perf_counter()
    results = []

    for rule in rules:
        result = execute_rule(rule, bundle, context)
        results.append(result)

    duration_ms = (perf_counter() - start) * 1000
    return build_report(template_id=template_id, results=results, duration_ms=duration_ms)
