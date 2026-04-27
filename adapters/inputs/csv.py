import csv
from typing import Any, Dict

from .base import BaseInputAdapter


class CsvInputAdapter(BaseInputAdapter):
    def __init__(self, bundle_key: str = "dados") -> None:
        self.bundle_key = bundle_key

    def load(self, source: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        with open(source, "r", encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))
        return {self.bundle_key: rows}
