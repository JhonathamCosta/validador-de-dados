import os
import shutil
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest

os.environ.setdefault("VALIDATOR_ENABLE_BUILTIN_DOMAINS", "true")

from core.application.validate import run_validation_job
from core.kernel.domain_loader import load_domain_from_path


class FakeAdapter:
    def __init__(self, bundle):
        self.bundle = bundle

    def load(self, source, context=None):
        return self.bundle


class InvalidAdapter:
    pass


def test_runs_end_to_end_for_registered_domain():
    adapter = {
        "dados": FakeAdapter(
            {
                "dados": [
                    {"codigo": ""},
                    {"codigo": "A001"},
                    {"codigo": "A999"},
                ]
            }
        ),
        "referencias": FakeAdapter(
            {
                "referencias": [
                    {"codigo": "A001"},
                    {"codigo": "A002"},
                ]
            }
        ),
    }

    report = run_validation_job(
        domain_id="exemplo",
        source={"dados": "dados.csv", "referencias": "referencias.csv"},
        adapter=adapter,
        context={"user": "tester"},
    )

    assert report.template_id == "exemplo"
    assert report.total_rules == 1
    assert report.total_fail == 1
    assert report.results[0].rule_id == "missing_code"
    assert report.results[0].status == "FAIL"
    assert report.results[0].count == 2


def test_raises_for_unknown_domain():
    adapter = FakeAdapter({"dados": []})
    with pytest.raises(ValueError):
        run_validation_job(
            domain_id="dominio_inexistente",
            source="fake.csv",
            adapter=adapter,
        )


def test_raises_for_invalid_adapter():
    with pytest.raises(TypeError):
        run_validation_job(
            domain_id="exemplo",
            source={"dados": "fake.csv"},
            adapter=InvalidAdapter(),
        )


def test_raises_when_adapter_returns_non_dict():
    adapter = {"dados": FakeAdapter(bundle=["not", "a", "dict"])}
    with pytest.raises(TypeError):
        run_validation_job(
            domain_id="exemplo",
            source={"dados": "fake.csv"},
            adapter=adapter,
        )


def test_raises_when_source_key_has_no_adapter():
    with pytest.raises(ValueError):
        run_validation_job(
            domain_id="exemplo",
            source={"dados": "dados.csv", "referencias": "referencias.csv"},
            adapter={"dados": FakeAdapter({"dados": []})},
        )


def test_loads_external_domain_package_from_manifest():
    temp_root = Path(".runtime_uploads") / f"pytest_domain_{uuid4().hex}"
    domain_path = temp_root / "custom_domain"
    rules_path = domain_path / "rules"
    try:
        rules_path.mkdir(parents=True)
        (domain_path / "__init__.py").write_text("", encoding="utf-8")
        (rules_path / "__init__.py").write_text(
            "from .always_fail import AlwaysFailRule\n",
            encoding="utf-8",
        )
        (rules_path / "always_fail.py").write_text(
            "\n".join(
                [
                    "class AlwaysFailRule:",
                    "    name = 'always_fail'",
                    "    rule_id = 'always_fail'",
                    "    def run(self, bundle, context):",
                    "        return {'count': 1, 'details': [], 'severity': 'HIGH'}",
                ]
            ),
            encoding="utf-8",
        )
        (domain_path / "registry.py").write_text(
            "\n".join(
                [
                    "from .rules import AlwaysFailRule",
                    "",
                    "def get_rules():",
                    "    return [AlwaysFailRule()]",
                    "",
                    "def get_input_specs():",
                    "    return [{'key': 'dados', 'label': 'Dados', 'required': True, 'formats': ['json']}]",
                ]
            ),
            encoding="utf-8",
        )
        (domain_path / "domain.json").write_text(
            "\n".join(
                [
                    "{",
                    '  "domain_id": "custom",',
                    '  "name": "Custom Domain",',
                    '  "version": "1.0.0",',
                    '  "kernel_compatibility": "^1.0.0",',
                    '  "entrypoint": "registry.py"',
                    "}",
                ]
            ),
            encoding="utf-8",
        )

        domain = load_domain_from_path(domain_path)

        assert domain.domain_id == "custom"
        assert domain.name == "Custom Domain"
        assert domain.get_rules()[0].rule_id == "always_fail"
        assert domain.get_input_specs()[0]["formats"] == ["json"]
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def test_domains_package_loads_external_domain_from_dotenv():
    temp_root = Path(".runtime_uploads") / f"pytest_dotenv_{uuid4().hex}"
    domain_path = temp_root / "dotenv_domain"
    rules_path = domain_path / "rules"
    env_path = Path(".env")
    previous_env = env_path.read_text(encoding="utf-8") if env_path.exists() else None
    try:
        rules_path.mkdir(parents=True)
        (domain_path / "__init__.py").write_text("", encoding="utf-8")
        (rules_path / "__init__.py").write_text(
            "from .always_pass import AlwaysPassRule\n",
            encoding="utf-8",
        )
        (rules_path / "always_pass.py").write_text(
            "\n".join(
                [
                    "class AlwaysPassRule:",
                    "    name = 'always_pass'",
                    "    rule_id = 'always_pass'",
                    "    def run(self, bundle, context):",
                    "        return {'count': 0, 'details': [], 'severity': 'LOW'}",
                ]
            ),
            encoding="utf-8",
        )
        (domain_path / "registry.py").write_text(
            "\n".join(
                [
                    "from .rules import AlwaysPassRule",
                    "",
                    "def get_rules():",
                    "    return [AlwaysPassRule()]",
                ]
            ),
            encoding="utf-8",
        )
        (domain_path / "domain.json").write_text(
            "\n".join(
                [
                    "{",
                    '  "domain_id": "dotenv_domain",',
                    '  "version": "1.0.0",',
                    '  "kernel_compatibility": "^1.0.0",',
                    '  "entrypoint": "registry.py"',
                    "}",
                ]
            ),
            encoding="utf-8",
        )
        env_path.write_text(f"VALIDATOR_DOMAIN_PATHS={temp_root}\n", encoding="utf-8")

        child_env = os.environ.copy()
        child_env.pop("VALIDATOR_DOMAIN_PATHS", None)
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from domains import get_registered_domain_ids; print('|'.join(get_registered_domain_ids()))",
            ],
            check=True,
            capture_output=True,
            env=child_env,
            text=True,
        )

        assert "dotenv_domain" in result.stdout.strip().split("|")
    finally:
        if previous_env is None:
            env_path.unlink(missing_ok=True)
        else:
            env_path.write_text(previous_env, encoding="utf-8")
        shutil.rmtree(temp_root, ignore_errors=True)


def test_builtin_domains_can_be_disabled_from_dotenv():
    env_path = Path(".env")
    previous_env = env_path.read_text(encoding="utf-8") if env_path.exists() else None
    try:
        env_path.write_text("VALIDATOR_ENABLE_BUILTIN_DOMAINS=false\n", encoding="utf-8")

        child_env = os.environ.copy()
        child_env.pop("VALIDATOR_DOMAIN_PATHS", None)
        child_env.pop("VALIDATOR_ENABLE_BUILTIN_DOMAINS", None)
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from domains import get_registered_domain_ids; print('|'.join(get_registered_domain_ids()))",
            ],
            check=True,
            capture_output=True,
            env=child_env,
            text=True,
        )

        assert "exemplo" not in result.stdout.split("|")
    finally:
        if previous_env is None:
            env_path.unlink(missing_ok=True)
        else:
            env_path.write_text(previous_env, encoding="utf-8")
