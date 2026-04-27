import json
from typing import Any, Dict

from .base import BaseInputAdapter


class JsonInputAdapter(BaseInputAdapter):
    def __init__(self, bundle_key: str = "dados") -> None:
        self.bundle_key = bundle_key

    def load(self, source: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        with open(source, "r", encoding="utf-8") as file:
            payload = json.load(file)

        if isinstance(payload, list):
            return {self.bundle_key: payload}

        if isinstance(payload, dict) and self.bundle_key in payload:
            return payload

        return {self.bundle_key: [payload]}
