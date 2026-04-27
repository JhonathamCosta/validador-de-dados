from .exemplo.registry import get_input_specs as get_exemplo_input_specs
from .exemplo.registry import get_rules as get_exemplo_rules

DOMAIN_REGISTRY = {
    "exemplo": get_exemplo_rules,
}

DOMAIN_INPUT_SPECS = {
    "exemplo": get_exemplo_input_specs,
}


def get_domain_rules(domain_id: str):
    if domain_id not in DOMAIN_REGISTRY:
        raise ValueError(f"Unknown domain: {domain_id}")
    return DOMAIN_REGISTRY[domain_id]()


def get_domain_input_specs(domain_id: str):
    if domain_id not in DOMAIN_REGISTRY:
        raise ValueError(f"Unknown domain: {domain_id}")
    if domain_id in DOMAIN_INPUT_SPECS:
        return DOMAIN_INPUT_SPECS[domain_id]()
    return [
        {
            "key": "dados",
            "label": "Arquivo de entrada",
            "required": True,
            "formats": ["csv", "json", "xlsx", "xlsm"],
        }
    ]


__all__ = ["DOMAIN_REGISTRY", "DOMAIN_INPUT_SPECS", "get_domain_rules", "get_domain_input_specs"]
