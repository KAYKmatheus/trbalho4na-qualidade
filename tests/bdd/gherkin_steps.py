"""Leitura dos cenários e passos Gherkin usados pela verificação de cobertura."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

CT_MARKER = re.compile(r"^\s*#\s*Equivale a:\s*(CT-\d{2})\s*$")
TEST_MARKER = re.compile(r"^\s*#\s*Teste:\s*(.+?)\s*$")
SCENARIO = re.compile(r"^\s*Cenário(?:\s+de\s+fundo)?:\s*(.+)$")
STEP = re.compile(r"^\s*(Dado|Quando|Então|E|Mas)\s+(.+)$")
PYTEST_BDD_KEYWORDS = {
    "Funcionalidade": "Feature",
    "Cenário": "Scenario",
    "Dado": "Given",
    "Quando": "When",
    "Então": "Then",
    "E": "And",
    "Mas": "But",
}


@dataclass
class Scenario:
    """Cenário com seu caso de teste de origem e passos Gherkin."""

    name: str
    feature_file: Path
    line: int
    case_id: str | None = None
    test_ids: list[str] = field(default_factory=list)
    steps: list[tuple[str, str]] = field(default_factory=list)


def translate_for_pytest_bdd(feature_text: str) -> str:
    """Translate only Portuguese Gherkin keywords; preserve scenario and step text."""
    translated_lines = []
    for line in feature_text.splitlines():
        if line.strip() == "# language: pt":
            translated_lines.append(line.replace("# language: pt", "# language: en"))
            continue
        match = re.match(r"^(\s*)(Funcionalidade|Cenário|Dado|Quando|Então|E|Mas)(?=[:\s])", line)
        if match:
            keyword = match.group(2)
            line = f"{match.group(1)}{PYTEST_BDD_KEYWORDS[keyword]}{line[match.end(2):]}"
        translated_lines.append(line)
    return "\n".join(translated_lines) + "\n"


def read_scenarios(features_dir: Path) -> list[Scenario]:
    """Extrai marcadores, cenários e passos dos arquivos feature."""
    scenarios: list[Scenario] = []
    pending_case_id: str | None = None
    pending_test_ids: list[str] = []
    current: Scenario | None = None

    for feature_file in sorted(features_dir.rglob("*.feature")):
        for line_number, line in enumerate(feature_file.read_text(encoding="utf-8").splitlines(), start=1):
            marker = CT_MARKER.match(line)
            if marker:
                if pending_case_id is not None:
                    raise ValueError(f"{feature_file}:{line_number}: marcador CT sem cenário.")
                pending_case_id = marker.group(1)
                continue

            test_marker = TEST_MARKER.match(line)
            if test_marker:
                if pending_test_ids:
                    raise ValueError(f"{feature_file}:{line_number}: mais de um marcador '# Teste:'.")
                pending_test_ids = [test_id.strip() for test_id in test_marker.group(1).split(",")]
                if not all(pending_test_ids):
                    raise ValueError(f"{feature_file}:{line_number}: marcador '# Teste:' vazio.")
                continue

            scenario_match = SCENARIO.match(line)
            if scenario_match:
                current = Scenario(
                    name=scenario_match.group(1),
                    feature_file=feature_file,
                    line=line_number,
                    case_id=pending_case_id,
                    test_ids=pending_test_ids,
                )
                scenarios.append(current)
                pending_case_id = None
                pending_test_ids = []
                continue

            if pending_case_id is not None and line.strip() and not line.strip().startswith("@"):
                raise ValueError(
                    f"{feature_file}:{line_number}: '# Equivale a' deve preceder o cenário."
                )
            if pending_test_ids and line.strip() and not line.strip().startswith("@"):
                raise ValueError(
                    f"{feature_file}:{line_number}: '# Teste:' deve preceder o cenário."
                )

            if current is not None:
                step_match = STEP.match(line)
                if step_match:
                    current.steps.append((step_match.group(1), step_match.group(2)))

        if pending_case_id is not None or pending_test_ids:
            raise ValueError(f"{feature_file}: marcador sem cenário.")

    return scenarios
