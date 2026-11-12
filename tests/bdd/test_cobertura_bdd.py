"""Compara testes pytest reais com os mapeamentos dos cenários Gherkin."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from tests.bdd.gherkin_steps import read_scenarios

ROOT = Path(__file__).resolve().parents[2]
TESTS_DIR = ROOT / "tests"

SEM_CENARIO = {
    "tests/bdd/test_api_errors.py::test_admin_resource_and_scope_errors_are_explicit": (
        "Teste de erros transversais da API sem cenário Gherkin próprio."
    ),
    "tests/bdd/test_api_errors.py::test_scope_conflicts_and_missing_resource_routes": (
        "Teste de erros de rotas e escopos sem cenário Gherkin próprio."
    ),
    "tests/bdd/test_api_errors.py::test_search_approval_material_and_report_errors": (
        "Teste de respostas de erro combinadas sem cenário Gherkin próprio."
    ),
    "tests/bdd/test_api_errors.py::test_reservation_not_found_transitions_are_404": (
        "Teste de rotas com identificadores inexistentes sem cenário Gherkin próprio."
    ),
    "tests/bdd/test_cobertura_bdd.py::test_every_pytest_test_has_scenario_or_explicit_reason": (
        "Verifica a própria cobertura AST."
    ),
    "tests/bdd/test_cobertura_bdd.py::test_every_scenario_test_reference_exists": (
        "Verifica a validade dos node IDs referenciados."
    ),
    "tests/bdd/test_database.py::test_split_sql_statements_preserves_quoted_semicolons": (
        "Teste unitário do utilitário de migrações."
    ),
    "tests/bdd/test_database.py::test_split_sql_statements_skips_empty_parts_and_keeps_tail": (
        "Teste unitário do utilitário de migrações."
    ),
    "tests/bdd/test_database.py::test_migrations_are_skipped_for_non_postgres": (
        "Teste unitário de configuração de banco."
    ),
    "tests/bdd/test_database.py::test_migrations_execute_each_postgres_statement": (
        "Teste unitário de configuração de banco."
    ),
    "tests/bdd/test_database.py::test_migration_set_is_three_idempotent_subject_migrations": (
        "Teste estrutural das migrações."
    ),
    "tests/bdd/test_database.py::test_init_db_creates_models_then_applies_migrations": (
        "Teste unitário de inicialização do banco."
    ),
    "tests/bdd/test_database.py::test_init_db_uses_supplied_engine": (
        "Teste unitário de inicialização do banco."
    ),
    "tests/bdd/test_database.py::test_get_db_closes_request_session": (
        "Teste unitário do ciclo de vida da sessão."
    ),
    "tests/bdd/test_delivery_config.py::test_container_uses_python_312_nonroot_and_healthcheck": (
        "Teste de configuração de contêiner."
    ),
    "tests/bdd/test_delivery_config.py::test_ci_runs_quality_gates_for_pull_requests_and_principal": (
        "Teste de configuração do CI."
    ),
    "tests/bdd/test_delivery_config.py::test_compose_app_waits_for_healthy_postgres_and_docker_context_is_filtered": (
        "Verifica a infraestrutura Docker sem cenário Gherkin próprio."
    ),
    "tests/bdd/test_delivery_config.py::test_sonar_properties_do_not_embed_a_token": (
        "Teste de configuração do Sonar."
    ),
    "tests/bdd/test_gherkin_coverage.py::GherkinCoverageTest::test_feature_scenarios_cover_all_documented_test_cases": (
        "Verifica a ligação dos CTs documentados aos cenários."
    ),
    (
        "tests/bdd/test_gherkin_coverage.py::GherkinCoverageTest::"
        "test_every_scenario_has_a_direct_ct_marker_and_given_when_then"
    ): (
        "Verifica a estrutura e os passos dos cenários."
    ),
    "tests/bdd/test_main.py::test_import_does_not_start_uvicorn": (
        "Teste de comportamento de importação do ponto de entrada."
    ),
    "tests/bdd/test_main.py::test_module_entrypoint_starts_uvicorn": (
        "Teste do ponto de entrada da aplicação."
    ),
    "tests/test_concorrencia.py::test_postgres_schema_has_exclusion_and_immutable_triggers": (
        "Verificação de esquema e reaplicação de migrações no PostgreSQL."
    ),
    "tests/test_regras_dominio.py::test_permission_denied_exception_does_not_shadow_builtin": (
        "Teste de regressão de nome de exceção."
    ),
    "tests/test_regras_dominio.py::test_interval_overlap_rule_detects_conflict": (
        "Teste unitário da regra de intervalos."
    ),
    "tests/test_regras_dominio.py::test_reservation_status_transition_follows_the_confirmed_lifecycle": (
        "Teste unitário das transições de estado."
    ),
    "tests/test_regras_dominio.py::test_final_reservation_status_cannot_transition": (
        "Teste unitário de estado final."
    ),
    "tests/test_reservas.py::test_home_page_renders_reservation_dashboard": (
        "Teste de renderização da página inicial."
    ),
}

SCENARIO_PATTERN = re.compile(r"^\s*Cenário(?:\s+de\s+fundo)?:\s*(.+)$")


def _node_id(path: Path, function: str, classes: tuple[str, ...]) -> str:
    suffix = "::".join((*classes, function))
    return f"{path.relative_to(ROOT).as_posix()}::{suffix}"


def _scenario_test_name(name: str) -> str:
    python_name = re.sub(r"\W", "", name.replace(" ", "_"))
    python_name = re.sub(r"^\d+_*", "", python_name)
    return f"test_{python_name.lower()}"


def _collect_test_ids() -> set[str]:
    test_ids: set[str] = set()
    generated_features: list[tuple[Path, Path]] = []

    class TestVisitor(ast.NodeVisitor):
        def __init__(self, path: Path, feature_constants: dict[str, tuple[str, ...]]) -> None:
            self.path = path
            self.feature_constants = feature_constants
            self.classes: list[str] = []

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self.classes.append(node.name)
            self.generic_visit(node)
            self.classes.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            if node.name.startswith("test_"):
                test_ids.add(_node_id(self.path, node.name, tuple(self.classes)))
            self.generic_visit(node)

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Call(self, node: ast.Call) -> None:
            function_name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else None
            )
            if function_name == "scenarios":
                for argument in node.args:
                    if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                        generated_features.append((self.path, self.path.parent / argument.value))
                    elif isinstance(argument, ast.Starred) and isinstance(argument.value, ast.Name):
                        for feature_path in self.feature_constants.get(argument.value.id, ()):
                            generated_features.append(
                                (self.path, self.path.parent / feature_path)
                            )
            self.generic_visit(node)

    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        feature_constants = {}
        for node in tree.body:
            if not isinstance(node, ast.Assign) or not isinstance(node.value, (ast.List, ast.Tuple)):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    feature_constants[target.id] = tuple(
                        element.value
                        for element in node.value.elts
                        if isinstance(element, ast.Constant) and isinstance(element.value, str)
                    )
        TestVisitor(path, feature_constants).visit(tree)

    for module_path, feature_path in generated_features:
        if not feature_path.is_file():
            continue
        for line in feature_path.read_text(encoding="utf-8").splitlines():
            match = SCENARIO_PATTERN.match(line)
            if match:
                test_ids.add(
                    f"{module_path.relative_to(ROOT).as_posix()}::{_scenario_test_name(match.group(1))}"
                )
    return test_ids


def test_every_pytest_test_has_scenario_or_explicit_reason() -> None:
    discovered = _collect_test_ids()
    mapped = {
        test_id
        for scenario in read_scenarios(TESTS_DIR / "bdd" / "features")
        for test_id in scenario.test_ids
    }
    unexplained = sorted(discovered - mapped - SEM_CENARIO.keys())
    stale_reasons = sorted(SEM_CENARIO.keys() - discovered)

    assert not unexplained, f"Testes sem cenário ou motivo: {unexplained}"
    assert not stale_reasons, f"Motivos para testes inexistentes: {stale_reasons}"
    assert all(reason.strip() for reason in SEM_CENARIO.values())


def test_every_scenario_test_reference_exists() -> None:
    discovered = _collect_test_ids()
    referenced = {
        test_id
        for scenario in read_scenarios(TESTS_DIR / "bdd" / "features")
        for test_id in scenario.test_ids
    }
    missing = sorted(referenced - discovered)
    assert not missing, f"Node IDs inexistentes nos cenários: {missing}"
