import importlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterable, List

from core.contracts import DomainDefinition

KERNEL_CONTRACT_VERSION = "1.0.0"
MANIFEST_FILE = "domain.json"


def _major(version: str) -> int:
    match = re.match(r"^(\d+)", version)
    if not match:
        raise ValueError(f"Invalid version: {version}")
    return int(match.group(1))


def _is_compatible(requirement: str, kernel_version: str = KERNEL_CONTRACT_VERSION) -> bool:
    normalized = requirement.strip()
    if normalized in ["*", ""]:
        return True
    if normalized.startswith("^"):
        return _major(normalized[1:]) == _major(kernel_version)
    return normalized == kernel_version


def _read_manifest(domain_path: Path) -> Dict[str, Any]:
    manifest_path = domain_path / MANIFEST_FILE
    if not manifest_path.exists():
        raise FileNotFoundError(f"Domain manifest not found: {manifest_path}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid domain manifest JSON: {manifest_path}") from exc

    required_fields = ["domain_id", "version", "kernel_compatibility", "entrypoint"]
    missing = [field for field in required_fields if not manifest.get(field)]
    if missing:
        raise ValueError(f"Domain manifest missing fields: {', '.join(missing)}")

    if not _is_compatible(manifest["kernel_compatibility"]):
        raise ValueError(
            f"Domain {manifest['domain_id']} requires kernel "
            f"{manifest['kernel_compatibility']}, current is {KERNEL_CONTRACT_VERSION}"
        )

    return manifest


def _load_module(module_path: Path, module_name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load domain entrypoint: {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_entrypoint(domain_path: Path, entrypoint: Path, domain_id: str) -> ModuleType:
    if (domain_path / "__init__.py").exists():
        parent = str(domain_path.parent)
        if parent not in sys.path:
            sys.path.insert(0, parent)

        module_name = f"{domain_path.name}.{entrypoint.stem}"
        return importlib.import_module(module_name)

    module_name = f"_validator_domain_{domain_id}_{abs(hash(str(domain_path)))}"
    return _load_module(entrypoint, module_name)


def load_domain_from_path(path: str | Path) -> DomainDefinition:
    domain_path = Path(path).resolve()
    manifest = _read_manifest(domain_path)
    entrypoint = (domain_path / manifest["entrypoint"]).resolve()
    if not entrypoint.exists():
        raise FileNotFoundError(f"Domain entrypoint not found: {entrypoint}")

    module = _load_entrypoint(domain_path, entrypoint, manifest["domain_id"])
    if not hasattr(module, "get_rules"):
        raise AttributeError(f"Domain {manifest['domain_id']} must expose get_rules()")

    get_input_specs = getattr(module, "get_input_specs", None)
    if get_input_specs is not None and not callable(get_input_specs):
        raise TypeError(f"Domain {manifest['domain_id']} get_input_specs must be callable")

    return DomainDefinition(
        domain_id=manifest["domain_id"],
        version=manifest["version"],
        name=manifest.get("name"),
        metadata=manifest.get("metadata") or {},
        get_rules=module.get_rules,
        get_input_specs=get_input_specs,
    )


def _candidate_domain_paths(path: Path) -> Iterable[Path]:
    if (path / MANIFEST_FILE).exists():
        yield path
        return

    if not path.exists() or not path.is_dir():
        return

    for child in sorted(path.iterdir()):
        if child.is_dir() and (child / MANIFEST_FILE).exists():
            yield child


def load_domains_from_paths(paths: Iterable[str | Path]) -> List[DomainDefinition]:
    domains: List[DomainDefinition] = []
    for raw_path in paths:
        if not raw_path:
            continue
        for domain_path in _candidate_domain_paths(Path(raw_path).expanduser().resolve()):
            domains.append(load_domain_from_path(domain_path))
    return domains


def get_domain_search_paths(env_value: str | None = None) -> List[str]:
    value = env_value if env_value is not None else os.getenv("VALIDATOR_DOMAIN_PATHS", "")
    return [item for item in value.split(os.pathsep) if item]
