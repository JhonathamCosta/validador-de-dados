from typing import Any, Dict, Protocol

from .rule_output import RuleOutput


class ValidationRule(Protocol):
    name: str
    rule_id: str

    def run(self, bundle: Dict[str, Any], context: Dict[str, Any]) -> RuleOutput:
        """Runs validation and returns a normalized payload used by the executor."""
        ...
