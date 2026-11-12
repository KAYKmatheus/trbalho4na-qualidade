"""Gera o relatório de cobertura a partir da saída JSON real do coverage.py."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from tests.bdd.gherkin_steps import read_scenarios
from tests.bdd.test_cobertura_bdd import _collect_test_ids

ROOT = Path(__file__).resolve().parents[2]
COVERAGE_FILE = ROOT / "coverage.json"
REPORT_FILE = ROOT / "docs" / "qualidade" / "relatorio-cobertura.md"
LINE_TARGET = 80.0
BRANCH_TARGET = 70.0
COMMAND = "pytest --cov=app --cov-branch --cov-report=json:coverage.json"


def _percentage(covered: int, total: int) -> float:
    return covered / total * 100 if total else 100.0


def _summary(summary: dict) -> tuple[int, int, float, int, int, float]:
    covered_lines = int(summary.get("covered_lines", 0))
    line_total = int(summary.get("num_statements", 0))
    covered_branches = int(summary.get("covered_branches", 0))
    branch_total = int(summary.get("num_branches", 0))
    return (
        covered_lines,
        line_total,
        _percentage(covered_lines, line_total),
        covered_branches,
        branch_total,
        _percentage(covered_branches, branch_total),
    )


def build_report(data: dict) -> str:
    totals = data["totals"]
    lines_covered, line_total, line_pct, branches_covered, branch_total, branch_pct = _summary(totals)

    tests = _collect_test_ids()
    scenarios = read_scenarios(ROOT / "tests" / "bdd" / "features")
    mapped_tests = {
        test_id for scenario in scenarios for test_id in scenario.test_ids if test_id in tests
    }
    tests_with_scenario = len(mapped_tests)
    tests_without_scenario = len(tests - mapped_tests)
    unmapped_scenarios = [
        f"{scenario.case_id or 'sem CT'} — {scenario.name}"
        for scenario in scenarios
        if not scenario.test_ids
    ]

    rows = []
    gaps = []
    for path, file_data in sorted(data["files"].items()):
        module = Path(path).as_posix()
        if module.startswith("app/"):
            module = module.removeprefix("app/")
        summary = _summary(file_data["summary"])
        file_lines, file_line_total, file_line_pct, file_branches, file_branch_total, file_branch_pct = summary
        rows.append(
            f"| `app/{module}` | {file_lines}/{file_line_total} ({file_line_pct:.2f}%) "
            f"| {file_branches}/{file_branch_total} ({file_branch_pct:.2f}%) |"
        )
        if file_line_pct < LINE_TARGET or file_branch_pct < BRANCH_TARGET:
            reasons = []
            if file_line_pct < LINE_TARGET:
                reasons.append(f"linhas {file_line_pct:.2f}% < {LINE_TARGET:.0f}%")
            if file_branch_pct < BRANCH_TARGET:
                reasons.append(f"ramos {file_branch_pct:.2f}% < {BRANCH_TARGET:.0f}%")
            gaps.append(f"- `app/{module}`: {', '.join(reasons)}.")

    scenario_section = (
        "\n".join(f"- {scenario}" for scenario in unmapped_scenarios)
        if unmapped_scenarios
        else "- Nenhum cenário sem teste mapeado."
    )
    gap_section = "\n".join(gaps) if gaps else "- Nenhum módulo abaixo das metas."
    line_result = (
        f"{line_pct:.2f}% ({lines_covered}/{line_total}); meta: {LINE_TARGET:.0f}% — "
        f"{'atingida' if line_pct >= LINE_TARGET else 'não atingida'}."
    )
    branch_result = (
        f"{branch_pct:.2f}% ({branches_covered}/{branch_total}); meta: {BRANCH_TARGET:.0f}% — "
        f"{'atingida' if branch_pct >= BRANCH_TARGET else 'não atingida'}."
    )
    return f"""# Relatório de cobertura

- Data: {date.today().isoformat()}
- Comando: `{COMMAND}`
- Linhas: {line_result}
- Ramos: {branch_result}
- Testes pytest: {len(tests)}
- Testes com cenário: {tests_with_scenario}
- Testes sem cenário: {tests_without_scenario}

## Cobertura por módulo

| Módulo | Linhas cobertas | Ramos cobertos |
|---|---:|---:|
{chr(10).join(rows)}

## Lacunas conhecidas

{gap_section}

## Cenários sem teste mapeado

{scenario_section}

## Como reproduzir

Na raiz do repositório, gere os dados e o relatório:

```text
{COMMAND}
python tests/bdd/gerar_relatorio.py
```
"""


def main() -> None:
    if not COVERAGE_FILE.is_file():
        raise FileNotFoundError(
            f"{COVERAGE_FILE} não existe. Execute primeiro: {COMMAND}"
        )
    report = build_report(json.loads(COVERAGE_FILE.read_text(encoding="utf-8")))
    REPORT_FILE.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
