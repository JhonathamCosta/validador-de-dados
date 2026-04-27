from typing import Any, Dict

from core.engine.runner import run_validation
from domains import get_domain_rules


def _load_single_bundle(adapter: Any, source: str, context: Dict[str, Any]) -> Dict[str, Any]:
    if not hasattr(adapter, "load"):
        raise TypeError("adapter must implement a load(source, context) method")

    bundle = adapter.load(source, context=context)
    if not isinstance(bundle, dict):
        raise TypeError("adapter.load must return a dict bundle")
    return bundle


def _load_bundle(source: Any, adapter: Any, context: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(source, dict):
        if not isinstance(adapter, dict):
            raise TypeError("adapter must be a dict when source is a dict")

        merged_bundle: Dict[str, Any] = {}
        for source_key, source_value in source.items():
            if source_key not in adapter:
                raise ValueError(f"Missing adapter for source key: {source_key}")

            partial_bundle = _load_single_bundle(adapter[source_key], source_value, context)
            overlapping_keys = set(merged_bundle).intersection(partial_bundle)
            if overlapping_keys:
                duplicated = ", ".join(sorted(overlapping_keys))
                raise ValueError(f"Duplicate bundle keys returned by adapters: {duplicated}")
            merged_bundle.update(partial_bundle)
        return merged_bundle

    return _load_single_bundle(adapter, source, context)


def run_validation_job(
    domain_id: str,
    source: Any,
    adapter: Any,
    context: Dict[str, Any] | None = None,
):
    """Runs a full validation job from source ingestion to final report."""
    job_context = dict(context or {})
    job_context.setdefault("domain_id", domain_id)
    job_context.setdefault("source", source)

    bundle = _load_bundle(source, adapter, job_context)

    rules = get_domain_rules(domain_id)
    if not rules:
        raise ValueError(f"No rules registered for domain: {domain_id}")

    return run_validation(
        bundle=bundle,
        rules=rules,
        context=job_context,
        template_id=domain_id,
    )
