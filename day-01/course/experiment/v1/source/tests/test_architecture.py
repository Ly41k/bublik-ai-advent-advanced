"""Enforce the small project's dependency boundaries using Python's AST."""

import ast
from pathlib import Path

import pytest

SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src" / "bublik"
FORBIDDEN = {
    "domain": (
        "fastapi",
        "pydantic",
        "bublik.api",
        "bublik.application",
        "bublik.infrastructure",
        "bublik.main",
    ),
    "application": ("fastapi", "pydantic", "bublik.api", "bublik.infrastructure", "bublik.main"),
    "api": ("bublik.infrastructure", "bublik.main"),
    "infrastructure": ("fastapi", "bublik.api", "bublik.main"),
}


@pytest.mark.parametrize("layer", FORBIDDEN)
def test_layer_does_not_import_forbidden_dependencies(layer: str):
    violations: list[str] = []
    for path in sorted((SOURCE_ROOT / layer).rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                assert node.level == 0, f"Use absolute imports: {path.name}:{node.lineno}"
                module = node.module or ""
                imports = [module, *(f"{module}.{alias.name}" for alias in node.names)]
            else:
                continue
            for imported in imports:
                if any(
                    imported == prefix or imported.startswith(prefix + ".")
                    for prefix in FORBIDDEN[layer]
                ):
                    violations.append(f"{path.name}:{node.lineno}: {imported}")
    assert not violations, "\n".join(violations)
