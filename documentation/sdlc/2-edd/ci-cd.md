# CI/CD Pipeline: FIPE Hunter

## Overview

FIPE Hunter uses GitHub Actions for continuous integration and continuous deployment. The pipeline validates code quality, runs tests, and prepares deployment artifacts.

## Environments

| Environment | Branch | Trigger | Purpose |
|-------------|--------|---------|---------|
| Development | feature/* | Push | Developer testing, rapid iteration |
| Staging | develop | Merge to develop | Integration testing, QA |
| Production | main | Tag (v*) | Live system |

## Pipeline Stages

### Stage 1: Lint and Format
**Duration:** ~30 seconds

**Steps:**
1. Check code formatting (black --check)
2. Run linter (ruff)
3. Check type hints (mypy)
4. Verify no syntax errors

**Fail Conditions:**
- Formatting violations
- Linting errors
- Type errors

```yaml
# .github/workflows/lint.yml
name: Lint

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install poetry
      - run: poetry install --only dev
      - run: poetry run black --check src/ tests/
      - run: poetry run ruff check src/ tests/
      - run: poetry run mypy src/
```

### Stage 2: Unit Tests
**Duration:** ~1 minute

**Steps:**
1. Install dependencies
2. Run unit tests
3. Generate coverage report
4. Upload coverage to Codecov

**Fail Conditions:**
- Any test failure
- Coverage below 80%

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install poetry
      - run: poetry install
      - run: poetry run pytest tests/unit/ --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Stage 3: Integration Tests
**Duration:** ~2 minutes

**Steps:**
1. Install dependencies
2. Run integration tests (mocked external services)
3. Verify adapters work correctly

**Fail Conditions:**
- Any test failure
- Timeout after 5 minutes

```yaml
# .github/workflows/test.yml (continued)
  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install poetry
      - run: poetry install
      - run: poetry run pytest tests/integration/ --timeout=300
```

### Stage 4: E2E Tests
**Duration:** ~3 minutes

**Steps:**
1. Install dependencies
2. Set up test database
3. Run end-to-end tests
4. Verify full user flows

**Fail Conditions:**
- Any test failure
- Timeout after 10 minutes

```yaml
# .github/workflows/test.yml (continued)
  e2e-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install poetry
      - run: poetry install
      - run: poetry run alembic upgrade head
      - run: poetry run pytest tests/e2e/ --timeout=600
```

### Stage 5: Build
**Duration:** ~1 minute

**Steps:**
1. Build Python package
2. Generate requirements.txt
3. Verify package integrity

**Fail Conditions:**
- Build errors
- Missing dependencies

```yaml
# .github/workflows/build.yml
name: Build

on:
  push:
    branches: [main, develop]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install poetry
      - run: poetry build
      - run: poetry export -f requirements.txt --output requirements.txt
      - uses: actions/upload-artifact@v3
        with:
          name: dist
          path: dist/
```

### Stage 6: Deploy (Future)
**Duration:** ~2 minutes

**Steps:**
1. Download build artifacts
2. Build Docker image
3. Push to container registry
4. Deploy to target environment

**Trigger:** Manual approval for production

**Note:** Deployment not in MVP scope.

## Workflow Files

### Complete CI Pipeline
```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install poetry
      - run: poetry install --only dev
      - run: poetry run black --check src/ tests/
      - run: poetry run ruff check src/ tests/
      - run: poetry run mypy src/

  test:
    runs-on: ubuntu-latest
    needs: lint
    strategy:
      matrix:
        test-type: [unit, integration, e2e]
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install poetry
      - run: poetry install
      - run: poetry run pytest tests/${{ matrix.test-type }}/ --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v3
        if: matrix.test-type == 'unit'

  build:
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push'
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install poetry
      - run: poetry build
      - uses: actions/upload-artifact@v3
        with:
          name: dist
          path: dist/
```

## Branch Protection Rules

### main (Production)
- Require pull request reviews (1+ approver)
- Require status checks to pass:
  - lint
  - unit-tests
  - integration-tests
  - e2e-tests
- Require branches to be up to date
- Require signed commits
- No force pushes
- No deletions

### develop (Staging)
- Require status checks to pass:
  - lint
  - unit-tests
  - integration-tests
- No force pushes

### feature/* (Development)
- No restrictions
- Recommended: run CI locally before push

## Pre-commit Hooks

### Local Development
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        language_version: python3.9

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

### Setup
```bash
pip install pre-commit
pre-commit install
```

**Benefits:**
- Catch formatting issues before commit
- Faster feedback loop
- Reduce CI failures

## Secrets Management

### GitHub Secrets (for CI/CD)
```
TELEGRAM_BOT_TOKEN
GOOGLE_SHEETS_CREDENTIALS_JSON
CARWIZARD_API_KEY
CODECOV_TOKEN
```

### Environment Variables (per environment)
```bash
# Development (.env.development)
DATABASE_URL=sqlite:///./fipe_hunter_dev.db
LOG_LEVEL=DEBUG

# Staging (.env.staging)
DATABASE_URL=sqlite:///./fipe_hunter_staging.db
LOG_LEVEL=INFO

# Production (.env.production)
DATABASE_URL=sqlite:///./fipe_hunter.db
LOG_LEVEL=WARNING
```

## Deployment Strategy (Future)

### Docker Image Build
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (Local)
```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
```

### Deployment Workflow (Future)
```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: docker/build-push-action@v4
        with:
          push: true
          tags: fipe-hunter:${{ github.ref_name }}
```

**Note:** Deployment automation not in MVP scope.

## Monitoring and Alerts

### Health Check Endpoint
```python
# src/adapters/controllers/health_controller.py
@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow()
    }
```

### CI Status Badge
```markdown
[![CI](https://github.com/user/fipe-hunter/actions/workflows/ci.yml/badge.svg)](https://github.com/user/fipe-hunter/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/user/fipe-hunter/branch/main/graph/badge.svg)](https://codecov.io/gh/user/fipe-hunter)
```

## Pipeline Performance

| Stage | Target Duration | Timeout |
|-------|-----------------|---------|
| Lint | < 30s | 2 min |
| Unit Tests | < 1 min | 5 min |
| Integration Tests | < 2 min | 10 min |
| E2E Tests | < 3 min | 15 min |
| Build | < 1 min | 5 min |
| **Total** | **< 8 min** | **30 min** |

## Failure Handling

### Test Failures
- Notify PR author via GitHub
- Block merge until resolved
- Provide failure logs and stack traces

### Transient Failures
- Retry up to 3 times for network issues
- Use cached dependencies to speed up retries

### Coverage Drops
- Fail if coverage drops below 80%
- Require coverage increase for new code

## Local CI Simulation

### Run All Checks Locally
```bash
#!/bin/bash
# scripts/run_ci_locally.sh

set -e

echo "Running lint..."
poetry run black --check src/ tests/
poetry run ruff check src/ tests/
poetry run mypy src/

echo "Running tests..."
poetry run pytest tests/unit/ --cov=src --cov-report=term
poetry run pytest tests/integration/
poetry run pytest tests/e2e/

echo "Building..."
poetry build

echo "All checks passed!"
```

**Usage:**
```bash
chmod +x scripts/run_ci_locally.sh
./scripts/run_ci_locally.sh
```

## Related Documentation
- [Testing Strategy](testing-strategy.md) - Test details
- [Tech Stack](tech-stack.md) - Tools and versions
- [Folder Structure](folder-structure.md) - Project layout
