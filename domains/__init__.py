import os
from pathlib import Path

from dotenv import load_dotenv

from core.kernel.domain_loader import get_domain_search_paths, load_domain_from_path, load_domains_from_paths
from core.kernel.domain_registry import DomainRegistry

load_dotenv()

_REGISTRY = DomainRegistry()


def _env_flag_enabled(name: str, default: bool = True) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _register_builtin_domains() -> None:
    if not _env_flag_enabled("VALIDATOR_ENABLE_BUILTIN_DOMAINS", default=True):
        return

    builtin_domain_path = Path(__file__).resolve().parent / "exemplo"
    if not (builtin_domain_path / "domain.json").exists():
        return

    domain = load_domain_from_path(builtin_domain_path)
    if not _REGISTRY.has(domain.domain_id):
        _REGISTRY.register(domain)


def _register_external_domains() -> None:
    for domain in load_domains_from_paths(get_domain_search_paths()):
        _REGISTRY.register(domain)


_register_external_domains()
_register_builtin_domains()


DOMAIN_REGISTRY = {domain_id: _REGISTRY.get(domain_id).get_rules for domain_id in _REGISTRY.ids()}
DOMAIN_INPUT_SPECS = {
    domain_id: _REGISTRY.get(domain_id).get_input_specs
    for domain_id in _REGISTRY.ids()
    if _REGISTRY.get(domain_id).get_input_specs is not None
}


def get_domain_rules(domain_id: str):
    return _REGISTRY.get_rules(domain_id)


def get_domain_input_specs(domain_id: str):
    return _REGISTRY.get_input_specs(domain_id)


def get_registered_domain_ids():
    return _REGISTRY.ids()


__all__ = [
    "DOMAIN_REGISTRY",
    "DOMAIN_INPUT_SPECS",
    "get_domain_rules",
    "get_domain_input_specs",
    "get_registered_domain_ids",
]
