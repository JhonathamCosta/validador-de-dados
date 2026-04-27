from typing import Any, Dict, Protocol


class InputAdapter(Protocol):
    def load(self, source: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Loads data from a source and returns a canonical bundle."""
        ...
