# Coding Conventions: FIPE Hunter

## General Principles

### Code Style
- Use **Black** for formatting (line length: 88 characters)
- Use **Ruff** for linting
- Use **mypy** for type checking
- Follow **PEP 8** style guide
- Write **self-documenting code** (clear names over comments)

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Files/Modules | snake_case | `listing_repository.py` |
| Classes | PascalCase | `ListingRepository` |
| Functions/Methods | snake_case | `scrape_listings()` |
| Variables | snake_case | `listing_count` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_RETRIES` |
| Private | _leading_underscore | `_parse_html()` |
| Interfaces/Protocols | IPascalCase | `IListingRepository` |

### File Organization

```
module.py
├── Imports (grouped: stdlib, third-party, local)
├── Constants
├── Type definitions
├── Classes
└── Functions
```

**Import Order:**
```python
# Standard library
import os
from datetime import datetime
from typing import Protocol, Optional

# Third-party
from fastapi import APIRouter
from sqlalchemy import Column, String

# Local
from src.domain.entities import Listing
from src.domain.ports import IListingRepository
```

---

## Python Conventions

### Type Hints
Always use type hints for function signatures:

```python
# ✅ Good
def scrape_listings(marketplace: str) -> list[Listing]:
    pass

# ❌ Bad
def scrape_listings(marketplace):
    pass
```

### Docstrings (Google Style)
```python
def calculate_score(listing: Listing, fipe_price: float) -> float:
    """Calculate opportunity score based on discount and other factors.

    Args:
        listing: The vehicle listing entity.
        fipe_price: FIPE reference price in BRL.

    Returns:
        Score between 0-100 (float).

    Raises:
        ValueError: If fipe_price is not positive.
    """
    pass
```

### Error Handling
- Use specific exceptions, not generic `Exception`
- Create custom exceptions for domain errors
- Log errors with context

```python
# ✅ Good
class FIPELookupError(Exception):
    """Raised when FIPE API lookup fails."""

def lookup_price(brand: str, model: str) -> float:
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.HTTPError as e:
        logger.error(f"FIPE lookup failed for {brand} {model}: {e}")
        raise FIPELookupError(f"Could not lookup price for {brand} {model}") from e

# ❌ Bad
def lookup_price(brand, model):
    try:
        response = requests.get(url)
    except Exception:
        pass  # Silent failure
```

### Constants
Define constants at module level:

```python
# constants.py
MAX_RETRIES = 3
REQUEST_TIMEOUT_SECONDS = 10
FIPE_API_BASE_URL = "https://parallelum.com.br/fipe/api/v1"
DISCOUNT_THRESHOLD_MIN = 0.20  # 20%
DISCOUNT_THRESHOLD_MAX = 0.50  # 50%
```

---

## Clean Architecture Conventions

### Layer Dependencies

```
Domain (no deps)
   ↑
Application (depends on Domain)
   ↑
Adapters (depends on Domain + Application)
   ↑
Infrastructure (depends on Domain interfaces only)
```

### Domain Layer Rules
- **No external dependencies** (no FastAPI, SQLAlchemy, requests)
- Pure Python dataclasses or Pydantic models
- Interfaces defined as Protocols

```python
# ✅ Good - Pure domain
from dataclasses import dataclass
from typing import Protocol

@dataclass
class Listing:
    brand: str
    model: str
    year: int
    price: float

class IListingRepository(Protocol):
    def save(self, listing: Listing) -> None: ...

# ❌ Bad - Framework dependency in domain
from sqlalchemy import Column, String

class Listing(Base):  # ❌ Don't use ORM in domain
    __tablename__ = "listings"
```

### Application Layer Rules
- Use cases depend on domain interfaces (ports)
- No direct adapter/infrastructure imports
- Return domain entities

```python
# ✅ Good - Use case with ports
class ScrapeListingsUseCase:
    def __init__(
        self,
        scraper: IScraper,
        repository: IListingRepository
    ):
        self._scraper = scraper
        self._repository = repository

    def execute(self) -> list[Listing]:
        listings = self._scraper.scrape()
        for listing in listings:
            self._repository.save(listing)
        return listings

# ❌ Bad - Direct adapter dependency
from src.adapters.scrapers import OLXScraper

class ScrapeListingsUseCase:
    def __init__(self):
        self._scraper = OLXScraper()  # ❌ Concrete implementation
```

### Dependency Injection
Wire dependencies in composition root (`main.py`):

```python
# src/main.py
from src.adapters.scrapers.olx_scraper import OLXScraper
from src.infrastructure.repositories.listing_repository import SQLAlchemyListingRepository
from src.application.scrape_listings import ScrapeListingsUseCase

# Composition root
scraper = OLXScraper()
repository = SQLAlchemyListingRepository(db_session)
use_case = ScrapeListingsUseCase(scraper, repository)
```

---

## Testing Conventions

### Test File Naming
- Unit tests: `test_{module}.py`
- Integration tests: `test_{module}_integration.py`
- E2E tests: `test_{feature}_e2e.py`

### Test Function Naming
```python
def test_{method}_{scenario}_{expected_outcome}():
    pass

# Examples
def test_scrape_listings_with_valid_html_returns_listings():
    pass

def test_calculate_score_with_zero_discount_returns_zero():
    pass
```

### AAA Pattern (Arrange-Act-Assert)
```python
def test_example():
    # Arrange - Set up test data
    listing = Listing(brand="VW", model="Gol", year=2020, price=30000)

    # Act - Execute code under test
    score = calculate_score(listing, fipe_price=50000)

    # Assert - Verify outcome
    assert score > 75
```

### Fixtures and Factories
```python
# conftest.py
@pytest.fixture
def sample_listing():
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

---

## API Conventions

### REST Endpoint Naming
```
GET    /api/v1/{resource}       # List all
GET    /api/v1/{resource}/{id}  # Get one
POST   /api/v1/{resource}       # Create
PUT    /api/v1/{resource}/{id}  # Update (full)
PATCH  /api/v1/{resource}/{id}  # Update (partial)
DELETE /api/v1/{resource}/{id}  # Delete
```

**Examples:**
```
GET    /api/v1/opportunities
GET    /api/v1/opportunities/123
POST   /api/v1/scrape/olx
```

### Response Format (JSON)
```json
{
  "data": { ... },
  "meta": {
    "page": 1,
    "total": 100
  }
}
```

### Error Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
      {"field": "brand", "message": "Brand is required"}
    ]
  }
}
```

### FastAPI Router Organization
```python
# src/adapters/controllers/scrape_controller.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/scrape", tags=["scraping"])

@router.post("/olx")
def scrape_olx():
    """Trigger OLX marketplace scrape."""
    pass
```

---

## Git Conventions

### Branch Naming
```
feature/{ticket}-{description}
bugfix/{ticket}-{description}
hotfix/{ticket}-{description}

Examples:
feature/FIPE-123-web-scraping
bugfix/FIPE-456-fix-scoring-calculation
```

### Commit Messages (Conventional Commits)
```
type(scope): description

feat(scraping): add OLX marketplace scraper
fix(scoring): correct discount percentage calculation
docs(readme): update setup instructions
test(fipe): add unit tests for FIPE lookup
refactor(db): simplify repository implementation
chore(deps): upgrade FastAPI to 0.104.0
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `test` - Tests
- `refactor` - Code refactoring
- `chore` - Maintenance tasks

### Pull Requests
**Title:** Same format as commit messages

**Description Template:**
```markdown
## What
Brief description of changes.

## Why
Why this change is needed.

## How
How it was implemented.

## Testing
- [ ] Unit tests added
- [ ] Integration tests added
- [ ] Manual testing completed

## Related
Closes #123
```

---

## Documentation Conventions

### Code Comments
- Explain **why**, not **what**
- Use comments for complex logic only
- No commented-out code (use git history)

```python
# ✅ Good - Explains why
# Use exponential backoff to avoid overwhelming FIPE API during rate limiting
delay = min(2 ** retry_count, 60)

# ❌ Bad - Explains what (obvious from code)
# Set delay to 2 raised to retry_count
delay = 2 ** retry_count
```

### README Files
Each significant module should have a README:

```markdown
# Module Name

## Purpose
What this module does.

## Key Components
- `Component1` - Description
- `Component2` - Description

## Usage
```python
from module import Component1

component = Component1()
result = component.do_thing()
```
```

---

## Security Conventions

### Secrets
- **Never commit secrets** to git
- Use environment variables
- Use `.env.example` for documentation (no real values)

```python
# ✅ Good
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ❌ Bad
TELEGRAM_BOT_TOKEN = "123456:ABC-DEF"  # ❌ Hardcoded secret
```

### Input Validation
- Validate all external input (API requests, scraped data)
- Use Pydantic models for validation

```python
from pydantic import BaseModel, field_validator

class ListingCreate(BaseModel):
    brand: str
    model: str
    year: int
    price: float

    @field_validator('year')
    def validate_year(cls, v):
        if v < 1950 or v > 2025:
            raise ValueError('Year must be between 1950 and 2025')
        return v
```

### Logging
- **Never log secrets** (tokens, passwords)
- Use structured logging
- Log at appropriate levels (DEBUG, INFO, WARNING, ERROR)

```python
# ✅ Good
logger.info(f"Scraped {count} listings from OLX")

# ❌ Bad
logger.info(f"Using Telegram token: {token}")  # ❌ Logs secret
```

---

## Performance Conventions

### Database Queries
- Use indexes on frequently queried fields
- Avoid N+1 queries (use joins or eager loading)
- Limit result sets with pagination

### Caching
- Cache FIPE prices for 24 hours
- Use in-memory cache for MVP (dict with TTL)
- Future: Redis for distributed caching

### Scraping
- Randomize request delays (1-3 seconds)
- Use connection pooling
- Implement exponential backoff on errors

---

## Code Review Checklist

- [ ] Code follows naming conventions
- [ ] Type hints present
- [ ] Tests added (unit + integration)
- [ ] Docstrings for public APIs
- [ ] No hardcoded secrets
- [ ] Error handling implemented
- [ ] Logging added
- [ ] Clean Architecture layers respected
- [ ] No commented-out code
- [ ] PR description complete

---

## Related Documentation
- [Architecture](architecture.md) - System design
- [Folder Structure](folder-structure.md) - Code organization
- [Testing Strategy](testing-strategy.md) - Test conventions
- [Tech Stack](tech-stack.md) - Tools and frameworks
