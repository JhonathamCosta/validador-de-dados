from typing import Any, Dict, List

from core.contracts import ValidationRule

from .rules import CheckMissingCodeRule


def get_rules() -> List[ValidationRule]:
    return [CheckMissingCodeRule()]


def get_input_specs() -> List[Dict[str, Any]]:
    return [
        {
            "key": "dados",
            "label": "Dados principais",
            "required": True,
            "formats": ["csv", "json", "xlsx", "xlsm"],
        },
        {
            "key": "referencias",
            "label": "Base de referencias",
            "required": True,
            "formats": ["csv", "json", "xlsx", "xlsm"],
        },
    ]
