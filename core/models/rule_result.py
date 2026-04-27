from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class RuleResult:
    rule_id: str
    rule_name: str

    status: str  # PASS | FAIL | WARNING | ERROR
    severity: str  # LOW | MEDIUM | HIGH | CRITICAL

    count: int = 0  # quantidade de ocorrências

    message: Optional[str] = None  # resumo
    details: List[Dict[str, Any]] = field(default_factory=list)  # evidência

    duration_ms: Optional[float] = None

    def is_failure(self) -> bool:
        return self.status in ["FAIL", "ERROR"]

    def is_warning(self) -> bool:
        return self.status == "WARNING"