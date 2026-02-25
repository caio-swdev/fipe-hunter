# Testing Strategy: FIPE Hunter

## Overview

FIPE Hunter employs a multi-layered testing approach aligned with Clean Architecture principles. Tests focus on business logic isolation, external service mocking, and end-to-end validation.

## Test Pyramid

```
         /\
        /E2E\        - Few (5-10 tests)
       /------\      - Full system flow
      /Integr.\     - Moderate (30-50 tests)
     /----------\    - Adapter + real/mocked services
    /   Unit     \   - Many (100+ tests)
   /--------------\  - Domain + use cases in isolation
```

## Test Layers

### Unit Tests (Domain + Use Cases)
**Location:** `tests/unit/`

**Purpose:** Test business logic in isolation

**Coverage Target:** 90%+

**What to test:**
- Domain entities (Listing, Opportunity)
- Use cases with mocked dependencies
- Business validation rules
- Score calculation algorithms

**Tools:**
- pytest
- unittest.mock (for ports/interfaces)

**Example:**
```python
# tests/unit/application/test_calculate_score.py
from unittest.mock import Mock
from src.application.calculate_score import CalculateOpportunityScoreUseCase
from src.domain.entities import Listing, Opportunity

def test_calculate_score_high_discount():
    # Arrange
    listing = Listing(
        brand="Volkswagen",
        model="Gol",
        year=2020,
        price=30000,
        fipe_price=50000
    )

    use_case = CalculateOpportunityScoreUseCase()

    # Act
    score = use_case.execute(listing)

    # Assert
    assert score >= 75  # 40% discount should score high
```

### Integration Tests (Adapters + External Services)
**Location:** `tests/integration/`

**Purpose:** Test adapters with real or mocked external services

**Coverage Target:** 70%+

**What to test:**
- Scrapers with mocked HTML responses
- API clients with mocked HTTP responses
- Repositories with test database
- Service adapters (Telegram, Sheets) with mocked APIs

**Tools:**
- pytest
- responses (HTTP mocking)
- sqlite (in-memory test database)

**Example:**
```python
# tests/integration/test_olx_scraper.py
import responses
from src.adapters.scrapers.olx_scraper import OLXScraper

@responses.activate
def test_scrape_olx_listings():
    # Arrange
    responses.add(
        responses.GET,
        'https://olx.com.br/autos-e-pecas/carros-vans-e-utilitarios',
        body=open('tests/fixtures/olx_response.html').read(),
        status=200
    )

    scraper = OLXScraper()

    # Act
    listings = scraper.scrape()

    # Assert
    assert len(listings) > 0
    assert listings[0].brand is not None
```

### E2E Tests (Full Flow)
**Location:** `tests/e2e/`

**Purpose:** Test complete user flows

**Coverage Target:** Critical paths only

**What to test:**
- Scrape → FIPE lookup → Scoring → Alert flow
- Manual API triggers
- Scheduled job execution
- Error recovery scenarios

**Tools:**
- pytest
- httpx (FastAPI TestClient)
- VCR.py (record/replay external APIs)

**Example:**
```python
# tests/e2e/test_scraping_flow.py
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_full_scraping_flow():
    # Act
    response = client.post('/api/scrape/olx')

    # Assert
    assert response.status_code == 200
    assert response.json()['listings_found'] > 0

    # Verify opportunities created
    opportunities = client.get('/api/opportunities/top').json()
    assert len(opportunities) > 0
    assert opportunities[0]['score'] > 75
```

## Test Organization

### Directory Structure
```
tests/
├── unit/
│   ├── domain/
│   │   ├── test_listing_entity.py
│   │   └── test_opportunity_entity.py
│   └── application/
│       ├── test_scrape_listings.py
│       ├── test_calculate_score.py
│       └── test_send_alert.py
├── integration/
│   ├── test_olx_scraper.py
│   ├── test_webmotors_scraper.py
│   ├── test_fipe_api_client.py
│   ├── test_listing_repository.py
│   └── test_telegram_service.py
├── e2e/
│   ├── test_scraping_flow.py
│   └── test_alert_flow.py
├── fixtures/
│   ├── olx_response.html
│   ├── webmotors_response.html
│   └── fipe_api_response.json
└── conftest.py  # Shared pytest fixtures
```

## Fixtures and Mocks

### Shared Fixtures (`conftest.py`)
```python
import pytest
from src.infrastructure.database.connection import get_test_db

@pytest.fixture
def test_db():
    """In-memory SQLite database for testing."""
    db = get_test_db()
    yield db
    db.close()

@pytest.fixture
def sample_listing():
    """Sample listing entity for tests."""
    from src.domain.entities import Listing
    return Listing(
        brand="Volkswagen",
        model="Gol",
        year=2020,
        price=30000,
        mileage=50000,
        condition="good",
        url="https://olx.com.br/listing/123"
    )
```

### HTTP Mocking Strategy
- Use `responses` library for HTTP mocking
- Store sample HTML responses in `tests/fixtures/`
- Use VCR.py for recording real API responses (then replay)

## Test Naming Convention

### File Naming
```
test_{component}.py
test_{component}_integration.py
test_{feature}_e2e.py
```

### Function Naming
```python
def test_{method}_{scenario}_{expected_outcome}():
    # AAA pattern: Arrange, Act, Assert
```

**Examples:**
- `test_scrape_listings_with_valid_html_returns_listings()`
- `test_calculate_score_with_high_discount_returns_high_score()`
- `test_send_alert_with_failed_telegram_api_retries_three_times()`

## AAA Pattern (Arrange-Act-Assert)

All tests follow the AAA pattern:

```python
def test_example():
    # Arrange - Set up test data and dependencies
    listing = create_sample_listing()
    use_case = ScrapeListingsUseCase(mock_scraper, mock_repo)

    # Act - Execute the code under test
    result = use_case.execute()

    # Assert - Verify expected outcomes
    assert result.success is True
    assert len(result.listings) > 0
```

## Mocking Strategy

### Domain Layer (Pure Functions)
- No mocking needed
- Test with real data

### Application Layer (Use Cases)
- Mock all dependencies (ports/interfaces)
- Test orchestration logic

```python
from unittest.mock import Mock

def test_scrape_listings_use_case():
    # Mock dependencies
    mock_scraper = Mock()
    mock_scraper.scrape.return_value = [sample_listing]
    mock_repo = Mock()

    # Test use case
    use_case = ScrapeListingsUseCase(mock_scraper, mock_repo)
    result = use_case.execute()

    # Verify interactions
    mock_scraper.scrape.assert_called_once()
    mock_repo.save.assert_called()
```

### Adapters Layer
- Mock external HTTP requests (responses library)
- Use test database for repositories

### Infrastructure Layer
- Use in-memory SQLite for database tests
- Mock external service credentials

## Coverage Targets

| Layer | Target | Rationale |
|-------|--------|-----------|
| Domain | 95%+ | Critical business logic |
| Application | 90%+ | Use case orchestration |
| Adapters | 70%+ | External integration, harder to test |
| Infrastructure | 60%+ | Configuration, boilerplate |

## Running Tests

### All Tests
```bash
pytest
```

### Unit Tests Only
```bash
pytest tests/unit/
```

### Integration Tests Only
```bash
pytest tests/integration/
```

### E2E Tests Only
```bash
pytest tests/e2e/
```

### With Coverage Report
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Watch Mode (Continuous)
```bash
pytest-watch
```

## CI/CD Integration

### GitHub Actions Pipeline
```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install poetry
      - run: poetry install
      - run: poetry run pytest --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v3
```

### Pipeline Stages
1. **Lint** (ruff, black --check)
2. **Type Check** (mypy)
3. **Unit Tests** (fast, no external deps)
4. **Integration Tests** (mocked external services)
5. **E2E Tests** (full flow, test database)

## Test Data Management

### Fixtures (Static)
- Store sample HTML in `tests/fixtures/`
- Store sample JSON API responses
- Version control fixtures

### Factories (Dynamic)
```python
# tests/factories.py
from src.domain.entities import Listing

def create_listing(**kwargs):
    defaults = {
        "brand": "Volkswagen",
        "model": "Gol",
        "year": 2020,
        "price": 30000,
        "mileage": 50000,
        "condition": "good",
        "url": "https://olx.com.br/listing/123"
    }
    defaults.update(kwargs)
    return Listing(**defaults)
```

## Database Testing Strategy

### In-Memory SQLite
```python
# src/infrastructure/database/connection.py
def get_test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine
```

### Test Database Lifecycle
1. **Setup:** Create in-memory database
2. **Test:** Run test with isolated database
3. **Teardown:** Close connection (automatic cleanup)

## External Service Mocking

### HTTP Mocking (responses library)
```python
import responses

@responses.activate
def test_fipe_api_client():
    responses.add(
        responses.GET,
        'https://parallelum.com.br/fipe/api/v1/carros/marcas',
        json={'marcas': [{'nome': 'Volkswagen', 'codigo': '59'}]},
        status=200
    )

    client = FIPEAPIClient()
    result = client.get_brands()

    assert len(result) > 0
```

### VCR.py (Record/Replay)
```python
import vcr

@vcr.use_cassette('tests/cassettes/fipe_lookup.yaml')
def test_fipe_lookup_integration():
    # First run: Records real API response
    # Subsequent runs: Replays from cassette
    client = FIPEAPIClient()
    result = client.lookup_price('Volkswagen', 'Gol', 2020)
    assert result > 0
```

## Performance Testing (Future)

### Load Testing (Locust)
- Test API endpoints under load
- Measure scraping throughput
- Identify bottlenecks

### Profiling
- Use cProfile for Python profiling
- Identify slow database queries
- Optimize scraping performance

**Note:** Performance testing not in MVP scope.

## Related Documentation
- [Architecture](architecture.md) - System design
- [Folder Structure](folder-structure.md) - Test file locations
- [CI/CD](ci-cd.md) - Pipeline integration
