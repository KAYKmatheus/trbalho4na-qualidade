"""Static checks for container, CI, and SonarCloud delivery configuration."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


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
    assert "fetch-depth: 0" in workflow
    assert 'python -c "import app.main"' in workflow
    assert "ruff check ." in workflow
    assert "python -m pytest" in workflow
    assert "--cov-fail-under=80" in workflow
    assert "Python tests and coverage" in workflow
    assert "covered_branches" in workflow
    assert "covered_lines" in workflow
    assert "num_statements" in workflow
    integration_job = workflow.split("\n  integration:\n", 1)[1]
    assert "image: postgres:16" in integration_job
    assert "DATABASE_URL:" in integration_job
    assert "AUTH_SECRET_KEY:" in integration_job
    assert 'python -m pytest -o addopts="" -m integration' in integration_job
    assert "SONAR_TOKEN" in workflow
    assert "-Dsonar.coverage.exclusions=tests/**" in workflow
    assert "sonar.qualitygate.wait=true" in workflow
    quality_job = workflow.split("\n  container:\n", 1)[0]
    assert '-o addopts=""' not in quality_job
    assert "--cov-fail-under=80" in quality_job
    assert "actions/setup-node@v4" in quality_job
    assert 'node-version: "22"' in quality_job
    assert "npm ci --ignore-scripts" in quality_job
    assert "npm run test:coverage" in quality_job
    assert "POSTGRES_PASSWORD: postgres" not in workflow
    assert "secrets.CI_POSTGRES_PASSWORD" in workflow
    assert workflow.count("${{ secrets.CI_POSTGRES_PASSWORD }}") == 6
    assert "postgres:postgres@" not in workflow
    assert "docker build -t alocasenac ." in workflow
    assert "docker inspect --format='{{.State.Health.Status}}'" in workflow
    assert "curl --fail --silent --show-error http://127.0.0.1:8000/v1/health" in workflow
    assert "AUTH_SECRET_KEY: ci-test-secret-key-not-for-production" in workflow
    assert "postgres:" in workflow


def test_ci_installs_hash_locked_binary_dependencies() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    lockfile = (ROOT / "requirements.lock").read_text(encoding="utf-8")

    install_command = "python -m pip install --only-binary=:all: --require-hashes -r requirements.lock"
    assert workflow.count(install_command) == 2
    assert workflow.count("cache-dependency-path: requirements.lock") == 2
    assert "--hash=sha256:" in lockfile


def test_sonar_properties_do_not_embed_a_token() -> None:
    properties = (ROOT / "sonar-project.properties").read_text(encoding="utf-8")

    assert "sonar.projectKey=" in properties
    assert "sonar.sources=app" in properties
    assert "sonar.tests=tests" in properties
    assert "sonar.javascript.lcov.reportPaths=coverage-js/lcov.info" in properties
    assert "sonar.coverage.exclusions=tests/**" in properties
    assert "sonar.token=" not in properties


def test_compose_app_waits_for_healthy_postgres_and_docker_context_is_filtered() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()

    assert "  app:" in compose
    assert "condition: service_healthy" in compose
    assert "postgres:5432/alocasenac_test" in compose
    assert "AUTH_SECRET_KEY: ${AUTH_SECRET_KEY:" in compose
    assert {
        ".git",
        ".aiox-core",
        ".claude",
        "tests",
        "docs",
        "__pycache__",
        ".env",
        "htmlcov",
    }.issubset(dockerignore)
