from typing import Any, Dict


class BaseInputAdapter:
    def load(self, source: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        raise NotImplementedError
