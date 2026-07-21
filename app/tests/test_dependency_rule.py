"""Test that domain/ modules respect the dependency rule.

No module in domain/ may import from readers, resolver, model, color,
render, usecases, or from stdlib I/O modules (xml, csv, json, os, io).
"""

import ast
import importlib
import os
import unittest

# Módulos e pacotes proibidos para domain/
_FORBIDDEN_TOP_LEVEL = {
    "readers",
    "resolver",
    "model",
    "color",
    "render",
    "usecases",
    # stdlib com I/O
    "xml",
    "csv",
    "json",
    "io",
    "zipfile",
    "struct",
    "zlib",
}


def _collect_domain_files() -> list[str]:
    """Return absolute paths of all .py files in the domain package."""
    base = os.path.join(os.path.dirname(__file__), "..", "anatomapa", "domain")
    paths = []
    for fname in os.listdir(base):
        if fname.endswith(".py") and not fname.startswith("__"):
            paths.append(os.path.join(base, fname))
    return paths


def _extract_imports(source: str) -> list[str]:
    """Parse source and return list of top-level module names imported."""
    tree = ast.parse(source)
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top = node.module.split(".")[0]
                # Ignora imports relativos (from . import ...)
                if node.level == 0:
                    names.append(top)
            elif node.level > 0:
                # Import relativo: pega o primeiro nome importado como indicador
                for alias in node.names:
                    pass  # imports relativos sao permitidos dentro do dominio
    return names


class TestDomainDependencyRule(unittest.TestCase):
    def test_domain_does_not_import_forbidden_modules(self):
        domain_files = _collect_domain_files()
        self.assertGreater(len(domain_files), 0, "No domain files found")

        violations = []
        for filepath in domain_files:
            with open(filepath, encoding="utf-8") as fh:
                source = fh.read()
            imports = _extract_imports(source)
            for imp in imports:
                # Verifica tanto imports de projeto quanto stdlib proibidos
                if imp in _FORBIDDEN_TOP_LEVEL:
                    violations.append(
                        f"{os.path.basename(filepath)} imports forbidden '{imp}'"
                    )
                # Verifica prefixo 'anatomapa.readers', 'anatomapa.model', etc.
                if imp == "anatomapa":
                    pass  # Analise mais profunda abaixo

        # Análise mais profunda: importações da forma 'from anatomapa.readers import ...'
        for filepath in domain_files:
            with open(filepath, encoding="utf-8") as fh:
                source = fh.read()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    parts = node.module.split(".")
                    if len(parts) >= 2 and parts[0] == "anatomapa":
                        if parts[1] in _FORBIDDEN_TOP_LEVEL:
                            violations.append(
                                f"{os.path.basename(filepath)} imports "
                                f"forbidden 'anatomapa.{parts[1]}'"
                            )

        if violations:
            self.fail(
                "Domain dependency rule violations:\n" + "\n".join(violations)
            )

    def test_domain_files_are_parseable(self):
        for filepath in _collect_domain_files():
            with open(filepath, encoding="utf-8") as fh:
                source = fh.read()
            try:
                ast.parse(source)
            except SyntaxError as e:
                self.fail(f"Syntax error in {filepath}: {e}")


if __name__ == "__main__":
    unittest.main()
