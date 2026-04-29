from typing import Any, Dict, List

from core.contracts import DomainDefinition, ValidationRule

DEFAULT_INPUT_SPECS = [
    {
        "key": "dados",
        "label": "Arquivo de entrada",
        "required": True,
        "formats": ["csv", "json", "xlsx", "xlsm"],
    }
]


class DomainRegistry:
    def __init__(self) -> None:
        self._domains: Dict[str, DomainDefinition] = {}

    def register(self, domain: DomainDefinition) -> None:
        if not domain.domain_id:
            raise ValueError("domain_id is required")
        if domain.domain_id in self._domains:
            raise ValueError(f"Domain already registered: {domain.domain_id}")
        self._domains[domain.domain_id] = domain

    def ids(self) -> List[str]:
        return sorted(self._domains)

    def has(self, domain_id: str) -> bool:
        return domain_id in self._domains

    def get(self, domain_id: str) -> DomainDefinition:
        if domain_id not in self._domains:
            raise ValueError(f"Unknown domain: {domain_id}")
        return self._domains[domain_id]

    def get_rules(self, domain_id: str) -> List[ValidationRule]:
        rules = self.get(domain_id).get_rules()
        if not isinstance(rules, list):
            raise TypeError(f"Domain {domain_id} get_rules() must return a list")
        return rules

    def get_input_specs(self, domain_id: str) -> List[Dict[str, Any]]:
        domain = self.get(domain_id)
        if domain.get_input_specs is None:
            return list(DEFAULT_INPUT_SPECS)

        specs = domain.get_input_specs()
        if not isinstance(specs, list):
            raise TypeError(f"Domain {domain_id} get_input_specs() must return a list")
        return specs

