"""Leitura dos cenários e passos Gherkin usados pela verificação de cobertura."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

CT_MARKER = re.compile(r"^\s*#\s*Equivale a:\s*(CT-\d{2})\s*$")
SCENARIO = re.compile(r"^\s*Cenário(?:\s+de\s+fundo)?:\s*(.+)$")
STEP = re.compile(r"^\s*(Dado|Quando|Então|E|Mas)\s+(.+)$")


@dataclass
class Scenario:
    """Cenário com seu caso de teste de origem e passos Gherkin."""

    name: str
    feature_file: Path
    line: int
    case_id: str | None = None
    steps: list[tuple[str, str]] = field(default_factory=list)


def read_scenarios(features_dir: Path) -> list[Scenario]:
    """Extrai marcadores, cenários e passos dos arquivos feature."""
    scenarios: list[Scenario] = []
    pending_case_id: str | None = None
    current: Scenario | None = None

    for feature_file in sorted(features_dir.rglob("*.feature")):
        for line_number, line in enumerate(feature_file.read_text(encoding="utf-8").splitlines(), start=1):
            marker = CT_MARKER.match(line)
            if marker:
                if pending_case_id is not None:
                    raise ValueError(f"{feature_file}:{line_number}: marcador CT sem cenário.")
                pending_case_id = marker.group(1)
                continue

            scenario_match = SCENARIO.match(line)
            if scenario_match:
                current = Scenario(
                    name=scenario_match.group(1),
                    feature_file=feature_file,
                    line=line_number,
                    case_id=pending_case_id,
                )
                scenarios.append(current)
                pending_case_id = None
                continue

            if pending_case_id is not None and line.strip():
                raise ValueError(
                    f"{feature_file}:{line_number}: '# Equivale a' deve ficar imediatamente antes do cenário."
                )

            if current is not None:
                step_match = STEP.match(line)
                if step_match:
                    current.steps.append((step_match.group(1), step_match.group(2)))

        if pending_case_id is not None:
            raise ValueError(f"{feature_file}: marcador {pending_case_id} sem cenário.")

    return scenarios
