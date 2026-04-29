from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from .rule import ValidationRule

RuleFactory = Callable[[], List[ValidationRule]]
InputSpecFactory = Callable[[], List[Dict[str, Any]]]


@dataclass(frozen=True)
class DomainDefinition:
    domain_id: str
    version: str
    get_rules: RuleFactory
    get_input_specs: InputSpecFactory | None = None
    name: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)

