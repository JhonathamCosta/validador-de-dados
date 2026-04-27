from typing import Any, Dict, List

from core.contracts import RuleOutput


class CheckMissingCodeRule:
    name = "missing_code"
    rule_id = "missing_code"

    def run(self, bundle: Dict[str, Any], context: Dict[str, Any]) -> RuleOutput:
        rows: List[Dict[str, Any]] = bundle.get("dados", [])
        references: List[Dict[str, Any]] = bundle.get("referencias", [])
        valid_codes = {str(row.get("codigo")).strip() for row in references if row.get("codigo")}

        missing = []
        for row in rows:
            code = row.get("codigo")
            normalized_code = str(code).strip() if code is not None else ""
            if not normalized_code:
                missing.append(row)
                continue
            if valid_codes and normalized_code not in valid_codes:
                missing.append(row)

        return {
            "count": len(missing),
            "details": missing,
            "severity": "MEDIUM",
            "message": "Codigo ausente ou fora da base de referencias." if missing else None,
        }
