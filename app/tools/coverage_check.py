"""Mede a cobertura de testes da lib usando só a stdlib (módulo `trace`).

Roda a suíte `unittest` sob o tracer, calcula a porcentagem de linhas
executáveis cobertas no pacote `anatomapa` e falha se ficar abaixo do
limite. Zero dependências externas: usado apenas como ferramenta de CI,
não faz parte do pacote publicado.

Uso:
    python tools/coverage_check.py [--min 90]
"""

from __future__ import annotations

import argparse
import ast
import importlib
import os
import sys
import trace
import unittest

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG_DIR = os.path.join(APP_DIR, "anatomapa")
TESTS_DIR = os.path.join(APP_DIR, "tests")


def _package_sources() -> list[str]:
    sources = []
    for dirpath, _, files in os.walk(PKG_DIR):
        for name in files:
            if name.endswith(".py"):
                sources.append(os.path.abspath(os.path.join(dirpath, name)))
    return sorted(sources)


def _non_coverable_lines(path: str) -> set[int]:
    """Linhas que o `trace` marca como executáveis mas nenhum teste cobre.

    Dois casos:
    - Continuação de assinatura de `def` multi-linha: o `trace` conta cada
      linha de parâmetro, mas a criação da função é atribuída à linha do `def`,
      então elas nunca disparam evento próprio.
    - Corpo `...` (Ellipsis) de métodos `Protocol`: stub abstrato que não
      executa (mesmo critério do `coverage.py`).
    """
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=path)
    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            lines.update(range(node.lineno + 1, node.body[0].lineno))
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and node.value.value is Ellipsis
        ):
            lines.add(node.lineno)
    return lines


def _module_name(path: str) -> str:
    rel = os.path.relpath(path, APP_DIR)
    parts = rel[: -len(".py")].split(os.sep)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _import_all_package_modules() -> None:
    """Importa todos os módulos do pacote sob o tracer.

    Sem isso, o `Ignore` do `trace` cacheia a primeira importação feita
    pelo discover como "ignorar" e zera a contagem de módulos como o
    `model/loader.py`.
    """
    for path in _package_sources():
        importlib.import_module(_module_name(path))


def _run_suite_under_trace() -> tuple[trace.CoverageResults, bool]:
    sys.path.insert(0, APP_DIR)
    # Sem ignoredirs: o `trace` cacheia a decisão de ignorar pelo basename
    # do arquivo, então qualquer `__init__.py` de diretório ignorado envenena
    # todos os `__init__.py` do pacote. A agregação já filtra só os fontes da lib.
    tracer = trace.Trace(count=1, trace=0)
    outcome: dict[str, bool] = {}

    # Imports e descoberta acontecem dentro da região traçada para que as
    # linhas de topo e de `def` do pacote contem como executadas.
    def run() -> None:
        _import_all_package_modules()
        suite = unittest.TestLoader().discover(
            start_dir=TESTS_DIR, top_level_dir=APP_DIR
        )
        runner = unittest.TextTestRunner(verbosity=0, stream=sys.stderr)
        outcome["ok"] = runner.run(suite).wasSuccessful()

    tracer.runfunc(run)
    return tracer.results(), outcome.get("ok", False)


def _covered_lines(results: trace.CoverageResults) -> dict[str, set[int]]:
    covered: dict[str, set[int]] = {}
    for (filename, lineno), count in results.counts.items():
        if count > 0:
            covered.setdefault(os.path.abspath(filename), set()).add(lineno)
    return covered


def main() -> int:
    parser = argparse.ArgumentParser(description="Cobertura via stdlib trace")
    parser.add_argument("--min", type=float, default=90.0)
    args = parser.parse_args()

    results, tests_ok = _run_suite_under_trace()
    if not tests_ok:
        print("FALHA: a suíte de testes não passou sob o tracer.")
        return 1

    covered = _covered_lines(results)

    total_exec = 0
    total_hit = 0
    rows: list[tuple[float, int, int, str, list[int]]] = []
    for path in _package_sources():
        find_lines = getattr(trace, "_find_executable_linenos")
        executable = {n for n in find_lines(path) if n}
        hit = covered.get(path, set()) & executable
        # Remove linhas não-cobríveis (assinaturas multi-linha, stubs `...`).
        executable -= _non_coverable_lines(path) - hit
        if not executable:
            continue
        missing = sorted(executable - hit)
        pct = 100.0 * len(hit) / len(executable)
        total_exec += len(executable)
        total_hit += len(hit)
        rows.append((pct, len(hit), len(executable), os.path.relpath(path, APP_DIR), missing))

    overall = 100.0 * total_hit / total_exec if total_exec else 100.0

    rows.sort(key=lambda r: r[0])
    print("\nCobertura por arquivo (menor primeiro):")
    for pct, hit, ex, rel, missing in rows:
        print(f"  {pct:6.2f}%  {hit:4d}/{ex:<4d}  {rel}")
        if pct < args.min and missing:
            shown = ", ".join(str(n) for n in missing[:20])
            extra = "..." if len(missing) > 20 else ""
            print(f"            linhas descobertas: {shown}{extra}")

    print(f"\nCobertura total: {overall:.2f}%  (mínimo exigido: {args.min:.2f}%)")
    if overall + 1e-9 < args.min:
        print("FALHA: cobertura abaixo do mínimo.")
        return 1
    print("OK: cobertura dentro do exigido.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
