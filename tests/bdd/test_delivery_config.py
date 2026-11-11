"""Static checks for container, CI, and SonarCloud delivery configuration."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_container_uses_python_312_nonroot_and_healthcheck() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "python:3.12-slim" in dockerfile
    assert "USER " in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "/v1/health" in dockerfile
    assert "AUTH_SECRET_KEY" not in dockerfile


def test_ci_runs_quality_gates_for_pull_requests_and_principal() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "pull_request:" in workflow
    assert "principal" in workflow
    assert "ruff check ." in workflow
    assert "pytest" in workflow
    assert "covered_branches" in workflow
    assert "covered_lines" in workflow
    assert "num_statements" in workflow
    assert "SONAR_TOKEN" in workflow
    assert "postgres:" in workflow


def test_sonar_properties_do_not_embed_a_token() -> None:
    properties = (ROOT / "sonar-project.properties").read_text(encoding="utf-8")

    assert "sonar.projectKey=" in properties
    assert "sonar.sources=app" in properties
    assert "sonar.tests=tests" in properties
    assert "sonar.token=" not in properties
