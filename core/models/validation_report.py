from dataclasses import dataclass, field
from typing import List
from .rule_result import RuleResult

@dataclass
class ValidationReport:
    template_id: str

    total_rules: int
    total_pass: int
    total_fail: int
    total_warning: int
    total_error: int

    results: List[RuleResult] = field(default_factory=list)

    duration_ms: float = 0.0

    def success_rate(self) -> float:
        if self.total_rules == 0:
            return 0.0
        return self.total_pass / self.total_rules

    def has_failures(self) -> bool:
        return self.total_fail > 0 or self.total_error > 0