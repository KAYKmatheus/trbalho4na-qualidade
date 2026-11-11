"""Verifica a cobertura entre os CT documentados e os cenários Gherkin."""

from __future__ import annotations

import re
import unittest
from collections import Counter
from pathlib import Path

from tests.bdd.gherkin_steps import read_scenarios

ROOT = Path(__file__).resolve().parents[2]
CASES_FILE = ROOT / "docs" / "qualidade" / "casos-de-teste.md"
FEATURES_DIR = ROOT / "features"
DOCUMENTED_CT = re.compile(r"^\|\s*(CT-\d{2})\s*\|", re.MULTILINE)


class GherkinCoverageTest(unittest.TestCase):
    """Garante que nenhum CT fique sem cenário e nenhum cenário seja órfão."""

    def test_feature_scenarios_cover_all_documented_test_cases(self) -> None:
        documented_cases = set(DOCUMENTED_CT.findall(CASES_FILE.read_text(encoding="utf-8")))
        scenarios = read_scenarios(FEATURES_DIR)
        scenario_cases = [scenario.case_id for scenario in scenarios if scenario.case_id]
        marker_counts = Counter(scenario_cases)

        missing = sorted(documented_cases - set(scenario_cases))
        unknown = sorted(set(scenario_cases) - documented_cases)
        duplicated = sorted(case_id for case_id, count in marker_counts.items() if count > 1)

        self.assertTrue(documented_cases, "Nenhum CT foi encontrado na tabela de casos de teste.")
        self.assertFalse(missing, f"CT sem cenário Gherkin: {', '.join(missing)}")
        self.assertFalse(unknown, f"Cenários apontam para CT inexistente: {', '.join(unknown)}")
        self.assertFalse(duplicated, f"CT mapeado para mais de um cenário: {', '.join(duplicated)}")

    def test_every_scenario_has_a_direct_ct_marker_and_given_when_then(self) -> None:
        scenarios = read_scenarios(FEATURES_DIR)
        self.assertTrue(scenarios, "Nenhum cenário Gherkin foi encontrado em features/.")

        failures = []
        for scenario in scenarios:
            location = f"{scenario.feature_file.relative_to(ROOT)}:{scenario.line}"
            if scenario.case_id is None:
                failures.append(f"{location}: cenário sem '# Equivale a: CT-xx'")

            keywords = {keyword for keyword, _ in scenario.steps}
            missing_keywords = {"Dado", "Quando", "Então"} - keywords
            if missing_keywords:
                failures.append(
                    f"{location}: faltam passos {', '.join(sorted(missing_keywords))}"
                )

        self.assertFalse(failures, "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
