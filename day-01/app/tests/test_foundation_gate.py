"""Execute real Ruff and architecture checks; test gate aggregation on fixtures."""

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path) -> ModuleType:
    """Load a local check without executing its CLI entry point."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ruff_fixture(source: str) -> subprocess.CompletedProcess[str]:
    """Use actual configuration on a synthetic test-module input."""
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--config",
            str(ROOT / "pyproject.toml"),
            "--no-cache",
            "--stdin-filename",
            "tests/test_annotation_fixture.py",
            "-",
        ],
        input=source,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_annotations_positive() -> None:
    result = ruff_fixture("def test_example(value: int) -> None:\n    pass\n")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("source", "rule"),
    [
        ("def test_example(value: int):\n    pass\n", "ANN201"),
        ("def test_example(value) -> None:\n    pass\n", "ANN001"),
    ],
)
def test_annotations_negative(source: str, rule: str) -> None:
    result = ruff_fixture(source)
    assert result.returncode != 0 and rule in result.stdout


def test_architecture_positive_and_negative(tmp_path: Path) -> None:
    architecture = load("foundation_architecture", ROOT / "tests/test_architecture.py")
    domain = tmp_path / "bublik/domain"
    domain.mkdir(parents=True)
    file = domain / "task.py"
    with patch.object(architecture, "SOURCE_ROOT", domain.parent):
        file.write_text("from uuid import UUID\n", encoding="utf-8")
        architecture.test_layer_does_not_import_forbidden_dependencies("domain")
        file.write_text("from fastapi import FastAPI\n", encoding="utf-8")
        with pytest.raises(AssertionError, match="fastapi"):
            architecture.test_layer_does_not_import_forbidden_dependencies("domain")


def fixture_gate(tmp_path: Path) -> tuple[ModuleType, Path, str]:
    """Create isolated synthetic inputs without modifying protected project files."""
    gate = load("foundation_checks", ROOT / "scripts/run_checks.py")
    app = tmp_path / "app"
    file = app / "src/value.py"
    file.parent.mkdir(parents=True)
    file.write_text("value = 1\n", encoding="utf-8")
    gate.ROOT = app
    manifest = tmp_path / "protected.json"
    manifest.write_text(
        json.dumps({"files": {"app/src/value.py": hashlib.sha256(file.read_bytes()).hexdigest()}}),
        encoding="utf-8",
    )
    return gate, manifest, hashlib.sha256(manifest.read_bytes()).hexdigest()


def test_protected_positive_and_modified_negative(tmp_path: Path) -> None:
    gate, manifest, sha = fixture_gate(tmp_path)
    gate.verify_protected(manifest, sha)
    (gate.ROOT / "src/value.py").write_text("value = 2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="PROTECTED_INPUT_CHANGED"):
        gate.verify_protected(manifest, sha)


def test_new_source_cannot_evade_protection(tmp_path: Path) -> None:
    gate, manifest, sha = fixture_gate(tmp_path)
    (gate.ROOT / "src/extra.py").write_text("value = 2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="PROTECTED_SOURCE_INVENTORY_CHANGED"):
        gate.verify_protected(manifest, sha)


def test_manifest_tampering_blocks_before_subprocesses(tmp_path: Path) -> None:
    gate, manifest, sha = fixture_gate(tmp_path)
    manifest.write_text('{"files": {}}', encoding="utf-8")
    output = gate.ROOT / "local-evidence/blocked.json"
    with patch.object(gate.subprocess, "run") as run:
        assert (
            gate.main(
                [
                    "--output",
                    str(output),
                    "--protected-manifest",
                    str(manifest),
                    "--protected-sha256",
                    sha,
                ]
            )
            == 1
        )
        run.assert_not_called()
    assert json.loads(output.read_text())["status"] == "BLOCKED"


@pytest.mark.parametrize("failed_index", range(7))
def test_each_mandatory_failure_prevents_pass(tmp_path: Path, failed_index: int) -> None:
    """Aggregation unit test: synthetic returns are not check execution evidence."""
    gate, manifest, sha = fixture_gate(tmp_path)
    passed = "\n".join(f"test.py::test_{i} PASSED" for i in range(17)) + "\n17 passed"
    returns = [
        subprocess.CompletedProcess([], 1 if i == failed_index else 0, passed if i == 5 else "", "")
        for i in range(7)
    ]
    output = gate.ROOT / "local-evidence/failed.json"
    with patch.object(gate.subprocess, "run", side_effect=returns):
        assert (
            gate.main(
                [
                    "--output",
                    str(output),
                    "--protected-manifest",
                    str(manifest),
                    "--protected-sha256",
                    sha,
                ]
            )
            == 1
        )
    assert json.loads(output.read_text())["status"] == "FAIL"


def test_acceptance_requires_distinct_cases() -> None:
    gate = load("foundation_acceptance", ROOT / "scripts/run_checks.py")
    duplicate = "test.py::test_same PASSED\n" * 17 + "17 passed"
    assert not gate.acceptance_ok(0, duplicate)


def test_protected_after_failure_prevents_pass(tmp_path: Path) -> None:
    gate, manifest, sha = fixture_gate(tmp_path)
    output = gate.ROOT / "local-evidence/changed.json"
    with (
        patch.object(gate, "commands", return_value=()),
        patch.object(gate, "verify_protected", side_effect=[None, ValueError("POSTCHECK_CHANGED")]),
    ):
        assert (
            gate.main(
                [
                    "--output",
                    str(output),
                    "--protected-manifest",
                    str(manifest),
                    "--protected-sha256",
                    sha,
                ]
            )
            == 1
        )
    assert json.loads(output.read_text())["status"] == "BLOCKED"
