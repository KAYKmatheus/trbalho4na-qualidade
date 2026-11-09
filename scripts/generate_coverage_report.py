"""Generate the BDD traceability report from documented CTs and feature files."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.bdd.gherkin_steps import read_scenarios


CASES_FILE = ROOT / "docs" / "qualidade" / "casos-de-teste.md"
FEATURES_DIR = ROOT / "features"
REPORT_FILE = ROOT / "docs" / "qualidade" / "relatorio-cobertura.md"
DOCUMENTED_CT = re.compile(r"^\|\s*(CT-\d{2})\s*\|", re.MULTILINE)


def build_report() -> str:
    documented = set(DOCUMENTED_CT.findall(CASES_FILE.read_text(encoding="utf-8")))
    scenarios = read_scenarios(FEATURES_DIR)
    mapped_ids = [scenario.case_id for scenario in scenarios if scenario.case_id]
    mapped = set(mapped_ids)
    counts = Counter(mapped_ids)
    by_module: dict[str, list[str]] = defaultdict(list)

    for scenario in scenarios:
        if scenario.case_id:
            by_module[scenario.feature_file.name].append(scenario.case_id)

    missing = sorted(documented - mapped)
    unknown = sorted(mapped - documented)
    duplicated = sorted(case_id for case_id, count in counts.items() if count > 1)
    unmarked = sum(scenario.case_id is None for scenario in scenarios)
    coverage = (len(mapped & documented) / len(documented) * 100) if documented else 0

    lines = [
        "# Relatório de cobertura BDD",
        "",
        "Gerado por `python scripts/generate_coverage_report.py` a partir de ",
        "`docs/qualidade/casos-de-teste.md` e dos arquivos `features/*.feature`.",
        "",
        "## Resumo",
        "",
        f"- Casos documentados: **{len(documented)}**",
        f"- Cenários Gherkin: **{len(scenarios)}**",
        f"- CTs documentados mapeados: **{len(mapped & documented)} de {len(documented)} ({coverage:.1f}%)**",
        "",
        "## Cobertura por módulo",
        "",
        "| Módulo (arquivo feature) | Cenários/CTs mapeados |",
        "|---|---:|",
    ]

    for module, case_ids in sorted(by_module.items()):
        lines.append(f"| `{module}` | {len(case_ids)} |")

    lines.extend(["", "## Lacunas declaradas", ""])
    gaps = []
    if missing:
        gaps.append(f"- CTs sem cenário: {', '.join(missing)}.")
    if unknown:
        gaps.append(f"- Marcadores para CT inexistente: {', '.join(unknown)}.")
    if duplicated:
        gaps.append(f"- CTs mapeados em mais de um cenário: {', '.join(duplicated)}.")
    if unmarked:
        gaps.append(f"- Cenários sem marcador `# Equivale a: CT-xx`: {unmarked}.")
    if not gaps:
        gaps.append("- Nenhuma lacuna de rastreabilidade entre os CTs e os cenários.")
    lines.extend(gaps)
    lines.extend(
        [
            "",
            "> Esta métrica verifica rastreabilidade estrutural BDD, não cobertura de linhas de código nem execução dos passos contra a aplicação.",
            "> CT-19 e CT-20 têm testes PostgreSQL em `tests/test_postgres_concurrency.py`; o resultado de execução deve ser consultado nos artefatos do workflow.",
            "",
            "## Como reproduzir",
            "",
            "```bash",
            "python scripts/generate_coverage_report.py",
            "pytest -q tests/bdd/test_gherkin_coverage.py",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    REPORT_FILE.write_text(build_report(), encoding="utf-8")
    print(f"Relatório gerado: {REPORT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()