from typing import Any, Dict, List, Literal, TypedDict


class RuleOutput(TypedDict, total=False):
    count: int
    status: Literal["PASS", "FAIL", "WARNING", "ERROR"]
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    message: str | None
    details: List[Dict[str, Any]]
