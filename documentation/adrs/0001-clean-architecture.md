# ADR-0001: Use Clean Architecture

**Status**: Accepted

**Date**: 2026-02-05

**Deciders**: Tech Lead, Development Team

**Related ADRs**: None

**Related EA ADRs**:
- EA ADR may exist for organization-wide Clean Architecture adoption

---

## Context

FIPE Hunter needs a maintainable architecture that:
- Separates business logic from external dependencies
- Enables easy testing and mocking
- Supports future technology changes (e.g., database migration)
- Enforces clear boundaries between layers

The MVP involves integrating multiple external services (OLX, WebMotors, FIPE API, Telegram, Google Sheets). We need an architecture that isolates these integrations from core business logic.

---

## Decision Drivers

- **Testability**: Need to unit test business logic without external services
- **Maintainability**: Team needs clear structure for long-term maintenance
- **Flexibility**: External APIs may change; need to isolate impact
- **Team Expertise**: Team familiar with Clean Architecture from previous projects
- **Complexity**: MVP scope justifies architectural investment

---

## Considered Options

1. **Clean Architecture (Hexagonal/Ports & Adapters)** - Layered with dependency inversion
2. **MVC Pattern** - Simple model-view-controller
3. **Transaction Script** - Procedural scripts per use case

---

## Decision

**Chosen**: Option 1 - Clean Architecture

**Rationale**:
Clean Architecture provides the right balance of structure and flexibility for FIPE Hunter. The system has:
- Complex business logic (scoring algorithm, price comparison)
- Multiple external integrations (scrapers, APIs, notifications)
- Need for comprehensive testing
- Future scaling requirements (PostgreSQL migration, distributed caching)

The dependency inversion principle allows us to:
- Define domain interfaces (ports) independent of implementation
- Swap scrapers or APIs without changing use cases
- Test use cases with mocked dependencies
- Migrate infrastructure (SQLite → PostgreSQL) without domain changes

---

## Consequences

### Positive
- **High testability**: Domain and use cases can be tested in complete isolation
- **Clear boundaries**: Each layer has well-defined responsibilities
- **Technology agnostic**: Easy to swap frameworks, databases, or external services
- **Future-proof**: Supports migration to PostgreSQL, Redis, Celery without major refactoring
- **Team clarity**: Developers know where to add new features

### Negative
- **Learning curve**: New team members need to understand layer boundaries
- **Boilerplate**: More files and interfaces than simpler architectures
- **Initial overhead**: Takes longer to set up than MVC or transaction script

### Risks
- **Risk**: Over-engineering for simple MVP
  - **Mitigation**: Start with core features only; add complexity as needed
- **Risk**: Team doesn't follow layer rules (e.g., domain imports infrastructure)
  - **Mitigation**: Code reviews, linting rules, clear documentation

---

## Implementation Notes

### Layer Structure
```
src/
├── domain/          # Entities, interfaces (no external deps)
├── application/     # Use cases (depends on domain)
├── adapters/        # Controllers, scrapers, API clients
└── infrastructure/  # Database, config, frameworks
```

### Dependency Rule
Dependencies point inward:
- Domain has no dependencies
- Application depends on Domain
- Adapters depend on Domain + Application
- Infrastructure depends on Domain (interfaces only)

### Example: Listing Repository

**Domain Interface:**
```python
# src/domain/ports/listing_repository.py
from typing import Protocol
from src.domain.entities import Listing

class IListingRepository(Protocol):
    def save(self, listing: Listing) -> None: ...
    def find_by_url(self, url: str) -> Listing | None: ...
```

**Infrastructure Implementation:**
```python
# src/infrastructure/repositories/listing_repository.py
from src.domain.ports import IListingRepository
from src.domain.entities import Listing
from sqlalchemy import select

class SQLAlchemyListingRepository(IListingRepository):
    def save(self, listing: Listing) -> None:
        # SQLAlchemy implementation
        pass
```

**Composition Root:**
```python
# src/main.py
from src.infrastructure.repositories.listing_repository import SQLAlchemyListingRepository
from src.application.scrape_listings import ScrapeListingsUseCase

# Wire dependencies
repository = SQLAlchemyListingRepository(db_session)
use_case = ScrapeListingsUseCase(scraper, repository)
```

---

## Validation

**Success Criteria**:
- All use cases can be unit tested without database or HTTP calls
- External API changes only require adapter layer updates
- Database migration (SQLite → PostgreSQL) requires only infrastructure changes
- New developers can navigate codebase within 1 week

**Review Date**: 2026-08-05 (6 months) - Assess if architecture overhead is justified

---

## References
- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture (Alistair Cockburn)](https://alistair.cockburn.us/hexagonal-architecture/)
- [Folder Structure](../folder-structure.md) - Implementation details
