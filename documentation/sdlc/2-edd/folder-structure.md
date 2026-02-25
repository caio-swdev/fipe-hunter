# Folder Structure: FIPE Hunter

## Overview

FIPE Hunter follows Clean Architecture with clear layer separation. The project structure reflects the dependency rule: domain → use cases → adapters → infrastructure.

## Project Tree

```
demo-fipe-hunter/
├── src/
│   ├── domain/                      # Domain layer (entities, interfaces)
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   ├── listing.py           # Listing entity
│   │   │   ├── opportunity.py       # Opportunity entity
│   │   │   └── scrape_log.py        # ScrapeLog entity
│   │   └── ports/
│   │       ├── __init__.py
│   │       ├── listing_repository.py     # IListingRepository
│   │       ├── opportunity_repository.py # IOpportunityRepository
│   │       ├── scraper.py                # IScraper
│   │       ├── fipe_client.py            # IFIPEClient
│   │       ├── alert_service.py          # IAlertService
│   │       ├── sheets_service.py         # ISheetsService
│   │       └── carwizard_service.py      # ICarWizardService
│   │
│   ├── application/                 # Use cases layer
│   │   ├── __init__.py
│   │   ├── scrape_listings.py       # ScrapeListingsUseCase
│   │   ├── lookup_fipe_price.py     # LookupFIPEPriceUseCase
│   │   ├── calculate_score.py       # CalculateOpportunityScoreUseCase
│   │   ├── send_alert.py            # SendTelegramAlertUseCase
│   │   ├── log_to_sheets.py         # LogToSheetsUseCase
│   │   └── sync_carwizard.py        # SyncCarWizardUseCase
│   │
│   ├── adapters/                    # Adapters layer (external integrations)
│   │   ├── __init__.py
│   │   ├── scrapers/
│   │   │   ├── __init__.py
│   │   │   ├── olx_scraper.py       # OLXScraper
│   │   │   └── webmotors_scraper.py # WebMotorsScraper
│   │   ├── clients/
│   │   │   ├── __init__.py
│   │   │   ├── fipe_api_client.py   # FIPEAPIClient
│   │   │   └── carwizard_client.py  # CarWizardAPIClient
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── telegram_service.py  # TelegramBotAdapter
│   │   │   └── sheets_service.py    # GoogleSheetsAdapter
│   │   └── controllers/
│   │       ├── __init__.py
│   │       ├── scrape_controller.py     # ScrapeController
│   │       ├── opportunity_controller.py # OpportunityController
│   │       └── config_controller.py     # ConfigController
│   │
│   ├── infrastructure/              # Infrastructure layer (persistence, config)
│   │   ├── __init__.py
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── models.py            # SQLAlchemy models
│   │   │   ├── connection.py        # Database connection
│   │   │   └── migrations/          # Alembic migrations
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── listing_repository.py     # SQLAlchemy ListingRepository
│   │   │   └── opportunity_repository.py # SQLAlchemy OpportunityRepository
│   │   ├── cache/
│   │   │   ├── __init__.py
│   │   │   └── fipe_cache.py        # InMemoryFIPECache
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   └── settings.py          # Environment variables, config
│   │   └── scheduler/
│   │       ├── __init__.py
│   │       └── jobs.py              # APScheduler job definitions
│   │
│   └── main.py                      # FastAPI application entry point
│
├── tests/
│   ├── unit/                        # Unit tests (domain, use cases)
│   │   ├── domain/
│   │   │   ├── test_listing_entity.py
│   │   │   └── test_opportunity_entity.py
│   │   └── application/
│   │       ├── test_scrape_listings.py
│   │       └── test_calculate_score.py
│   ├── integration/                 # Integration tests (adapters, repos)
│   │   ├── test_olx_scraper.py
│   │   ├── test_fipe_api_client.py
│   │   └── test_listing_repository.py
│   └── e2e/                         # End-to-end tests (full flow)
│       ├── test_scraping_flow.py
│       └── test_alert_flow.py
│
├── scripts/
│   ├── seed_database.py             # Seed test data
│   └── run_scrape.py                # Manual scrape trigger script
│
├── alembic/                         # Alembic migrations
│   ├── versions/
│   └── env.py
│
├── documentation/                   # Project documentation
│   ├── ea/                          # Enterprise Architecture (if applicable)
│   └── sdlc/
│       ├── 1-design/                # Design phase outputs
│       └── 2-edd/                   # Engineering Design Document (this)
│
├── .env.example                     # Environment variables template
├── .gitignore
├── alembic.ini                      # Alembic configuration
├── pyproject.toml                   # Poetry dependencies and config
├── pytest.ini                       # pytest configuration
├── README.md                        # Project overview
└── requirements.txt                 # pip dependencies (generated from poetry)
```

## Layer Responsibilities

### Domain (`src/domain/`)
**Purpose:** Core business logic and rules

**What goes here:**
- Entities (Listing, Opportunity, ScrapeLog)
- Domain interfaces (ports)
- Business validation rules
- Value objects (if needed)

**What does NOT go here:**
- Framework imports (FastAPI, SQLAlchemy)
- External API clients
- HTTP requests
- Database queries

**Dependencies:** None (pure Python)

### Application (`src/application/`)
**Purpose:** Orchestrate business use cases

**What goes here:**
- Use case classes (one per feature)
- Coordination between domain and adapters
- Transaction boundaries
- Application-level error handling

**What does NOT go here:**
- HTTP request handling
- Database implementation
- External API calls (use ports instead)

**Dependencies:** Domain layer only

### Adapters (`src/adapters/`)
**Purpose:** Connect external systems to domain

**What goes here:**
- Scrapers (OLX, WebMotors)
- API clients (FIPE, CarWizard)
- Service adapters (Telegram, Sheets)
- Controllers (FastAPI routers)

**What does NOT go here:**
- Business logic (belongs in use cases)
- Database models (belongs in infrastructure)

**Dependencies:** Domain, Application

### Infrastructure (`src/infrastructure/`)
**Purpose:** Technical implementation details

**What goes here:**
- SQLAlchemy models
- Database repositories (implement domain ports)
- Configuration loading
- Scheduler setup
- Migrations (Alembic)
- Caching implementation

**What does NOT go here:**
- Business logic
- Use case orchestration

**Dependencies:** Domain (interfaces only), Application (for dependency injection)

## Import Rules

### Domain Layer
```python
# ✅ Allowed
from dataclasses import dataclass
from typing import Protocol, Optional
from datetime import datetime

# ❌ NOT allowed
from fastapi import FastAPI
from sqlalchemy import Column
import requests
```

### Application Layer
```python
# ✅ Allowed
from src.domain.entities import Listing
from src.domain.ports import IListingRepository

# ❌ NOT allowed
from src.infrastructure.database.models import ListingModel
from src.adapters.scrapers import OLXScraper
```

### Adapters Layer
```python
# ✅ Allowed
from src.domain.ports import IScraper
from src.application.scrape_listings import ScrapeListingsUseCase
import requests
from bs4 import BeautifulSoup

# ❌ NOT allowed
from src.infrastructure.repositories import ListingRepository  # Use ports instead
```

### Infrastructure Layer
```python
# ✅ Allowed
from sqlalchemy import Column, String, Integer
from src.domain.entities import Listing
from src.domain.ports import IListingRepository
from src.infrastructure.config.settings import Settings

# ✅ Also allowed (implementing interface)
from src.domain.ports import IListingRepository

class SQLAlchemyListingRepository(IListingRepository):
    # Implementation
```

## File Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Entities | snake_case.py | `listing.py` |
| Interfaces/Ports | snake_case.py | `listing_repository.py` |
| Use Cases | snake_case.py | `scrape_listings.py` |
| Adapters | snake_case.py | `olx_scraper.py` |
| Controllers | {feature}_controller.py | `scrape_controller.py` |
| Tests | test_{feature}.py | `test_listing_entity.py` |
| Models (DB) | models.py | `models.py` |

## Class Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Entity | PascalCase | `Listing` |
| Interface/Port | IPascalCase | `IListingRepository` |
| Use Case | PascalCaseUseCase | `ScrapeListingsUseCase` |
| Adapter | PascalCaseAdapter | `OLXScraper` |
| Controller | PascalCaseController | `ScrapeController` |
| Repository Impl | SQLAlchemyPascalCaseRepository | `SQLAlchemyListingRepository` |

## Module Organization

### Feature-Based (Domain, Use Cases)
Organize by business feature:
- `listing.py` - Listing entity
- `opportunity.py` - Opportunity entity
- `scrape_listings.py` - Scrape use case
- `calculate_score.py` - Scoring use case

### Type-Based (Adapters, Infrastructure)
Organize by technical type:
- `scrapers/` - All scrapers
- `clients/` - All API clients
- `services/` - All external services
- `repositories/` - All database repos

## Testing Structure

### Unit Tests (`tests/unit/`)
- Test domain entities in isolation
- Test use cases with mocked ports
- No database, no HTTP calls
- Fast, independent tests

### Integration Tests (`tests/integration/`)
- Test adapters with real external services (or mocked APIs)
- Test repositories with test database
- HTTP mocking (responses library)
- Slower, may have external dependencies

### E2E Tests (`tests/e2e/`)
- Test full user flows
- Real database (test DB)
- External APIs mocked (VCR.py)
- Slowest, most comprehensive

## Configuration Management

```
.env                     # Local development (gitignored)
.env.example             # Template for required vars
src/infrastructure/config/settings.py  # Settings loader
```

**Environment Variables:**
- `DATABASE_URL` - SQLite file path
- `FIPE_API_URL` - FIPE API base URL
- `TELEGRAM_BOT_TOKEN` - Telegram bot token
- `GOOGLE_SHEETS_CREDENTIALS_FILE` - Path to OAuth JSON
- `CARWIZARD_API_URL` - CarWizard API base URL
- `CARWIZARD_API_KEY` - CarWizard API key

## Scripts

### `scripts/seed_database.py`
Populate database with sample listings for testing.

### `scripts/run_scrape.py`
Manually trigger a scrape (useful for debugging).

**Usage:**
```bash
python scripts/run_scrape.py --marketplace olx
python scripts/run_scrape.py --marketplace webmotors
```

## Database Migrations

### Creating a migration
```bash
alembic revision --autogenerate -m "Add opportunity table"
```

### Applying migrations
```bash
alembic upgrade head
```

### Rollback
```bash
alembic downgrade -1
```

## Related Documentation
- [Architecture](architecture.md) - System design and C4 diagrams
- [Tech Stack](tech-stack.md) - Technologies and versions
- [Coding Conventions](conventions.md) - Python coding standards
