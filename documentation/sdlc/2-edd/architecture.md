# Architecture: FIPE Hunter

## Overview

FIPE Hunter follows Clean Architecture principles with clear separation between domain logic, application layer, and infrastructure concerns.

## C4 Level 1: System Context

```plantuml
@startuml c4-context
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml

title System Context - FIPE Hunter

Person(admin, "Administrator", "Monitors and controls scraping operations")
Person(user, "Telegram User", "Receives vehicle opportunity alerts")

System(fipe_hunter, "FIPE Hunter", "Automated vehicle opportunity finder that identifies underpriced vehicles in Brazilian marketplaces")

System_Ext(olx, "OLX Marketplace", "Brazilian vehicle listings platform")
System_Ext(webmotors, "WebMotors", "Brazilian vehicle listings platform")
System_Ext(fipe_api, "FIPE API", "Official vehicle reference prices (parallelum.com.br)")
System_Ext(telegram, "Telegram Bot API", "Real-time messaging platform")
System_Ext(sheets, "Google Sheets API", "Cloud spreadsheet service")
System_Ext(carwizard, "CarWizard System", "Vehicle inspection and analysis platform")

Rel(admin, fipe_hunter, "Triggers scrapes, monitors status", "HTTP/REST")
Rel(user, telegram, "Receives alerts", "Telegram Bot")
Rel(fipe_hunter, olx, "Scrapes vehicle listings", "HTTP")
Rel(fipe_hunter, webmotors, "Scrapes vehicle listings", "HTTP")
Rel(fipe_hunter, fipe_api, "Queries reference prices", "REST API")
Rel(fipe_hunter, telegram, "Sends alerts", "Bot API")
Rel(fipe_hunter, sheets, "Logs opportunities", "REST API")
Rel(fipe_hunter, carwizard, "Sends qualified opportunities", "REST API")

@enduml
```

## C4 Level 2: Container Diagram

```plantuml
@startuml c4-container
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml

title Container Diagram - FIPE Hunter

Person(admin, "Administrator")
Person(user, "Telegram User")

System_Boundary(fipe_hunter, "FIPE Hunter") {
    Container(api, "FastAPI Application", "Python 3.9+, FastAPI", "REST API for scraping control and opportunity queries")
    Container(scheduler, "Background Scheduler", "Python APScheduler", "Automated periodic scraping jobs")
    Container(db, "SQLite Database", "SQLite", "Stores listings, opportunities, scrape logs")
    ContainerDb(cache, "In-Memory Cache", "Python dict", "FIPE price cache (24h TTL)")
}

System_Ext(olx, "OLX Marketplace")
System_Ext(webmotors, "WebMotors")
System_Ext(fipe_api, "FIPE API")
System_Ext(telegram, "Telegram Bot API")
System_Ext(sheets, "Google Sheets API")
System_Ext(carwizard, "CarWizard System")

Rel(admin, api, "Triggers scrapes, queries opportunities", "HTTPS/JSON")
Rel(scheduler, api, "Triggers scheduled scrapes", "Internal call")
Rel(api, db, "Reads/writes listings and opportunities", "SQLite")
Rel(api, cache, "Reads/writes FIPE prices", "In-memory")
Rel(api, olx, "Scrapes listings", "HTTP")
Rel(api, webmotors, "Scrapes listings", "HTTP")
Rel(api, fipe_api, "Queries reference prices", "REST")
Rel(api, telegram, "Sends alerts", "Bot API")
Rel(api, sheets, "Appends opportunities", "REST")
Rel(api, carwizard, "Sends qualified opportunities", "REST")
Rel(telegram, user, "Delivers alerts")

@enduml
```

## C4 Level 3: Component Diagram

```plantuml
@startuml c4-component
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml

title Component Diagram - FIPE Hunter Core

Container_Boundary(api, "FastAPI Application") {
    Component(scrape_controller, "Scrape Controller", "FastAPI Router", "Handles scraping API endpoints")
    Component(opportunity_controller, "Opportunity Controller", "FastAPI Router", "Handles opportunity queries")
    Component(config_controller, "Config Controller", "FastAPI Router", "Manages system configuration")

    Component(scrape_usecase, "Scrape Use Case", "Python Class", "Orchestrates marketplace scraping")
    Component(fipe_usecase, "FIPE Lookup Use Case", "Python Class", "Retrieves reference prices")
    Component(scoring_usecase, "Scoring Use Case", "Python Class", "Calculates opportunity scores")
    Component(alert_usecase, "Alert Use Case", "Python Class", "Sends Telegram notifications")
    Component(sheets_usecase, "Sheets Use Case", "Python Class", "Logs to Google Sheets")

    Component(listing_entity, "Listing Entity", "Python Dataclass", "Vehicle listing domain model")
    Component(opportunity_entity, "Opportunity Entity", "Python Dataclass", "Scored opportunity domain model")

    Component(scraper_adapter, "Scraper Adapter", "BeautifulSoup4", "HTML parsing and extraction")
    Component(fipe_adapter, "FIPE API Adapter", "requests", "HTTP client for FIPE API")
    Component(telegram_adapter, "Telegram Adapter", "python-telegram-bot", "Telegram Bot API client")
    Component(sheets_adapter, "Sheets Adapter", "gspread", "Google Sheets API client")
    Component(carwizard_adapter, "CarWizard Adapter", "requests", "HTTP client for CarWizard")

    Component(listing_repo, "Listing Repository", "SQLAlchemy", "Listing persistence")
    Component(opportunity_repo, "Opportunity Repository", "SQLAlchemy", "Opportunity persistence")
    Component(cache_service, "Cache Service", "dict", "In-memory FIPE cache")
}

ContainerDb(db, "SQLite Database")

Rel(scrape_controller, scrape_usecase, "Calls")
Rel(opportunity_controller, scoring_usecase, "Calls")
Rel(scrape_usecase, scraper_adapter, "Uses")
Rel(scrape_usecase, listing_repo, "Saves to")
Rel(fipe_usecase, fipe_adapter, "Uses")
Rel(fipe_usecase, cache_service, "Caches in")
Rel(scoring_usecase, opportunity_repo, "Saves to")
Rel(alert_usecase, telegram_adapter, "Uses")
Rel(sheets_usecase, sheets_adapter, "Uses")
Rel(listing_repo, db, "Queries")
Rel(opportunity_repo, db, "Queries")

@enduml
```

## Architecture Layers

### Domain Layer
**Purpose:** Core business logic, entities, and interfaces

**Components:**
- `Listing` - Vehicle listing entity
- `Opportunity` - Scored opportunity entity
- `IListingRepository` - Repository interface
- `IOpportunityRepository` - Repository interface
- `IScraper` - Scraper interface
- `IFIPEClient` - FIPE API interface
- `IAlertService` - Alert service interface

**Rules:**
- No dependencies on external frameworks
- Pure Python dataclasses and protocols
- Business rules encapsulated in entities
- Interfaces for external services

### Application Layer (Use Cases)
**Purpose:** Orchestrate domain logic and coordinate between layers

**Components:**
- `ScrapeListingsUseCase` - Scrape marketplaces
- `LookupFIPEPriceUseCase` - Get reference prices
- `CalculateOpportunityScoreUseCase` - Score opportunities
- `SendTelegramAlertUseCase` - Dispatch alerts
- `LogToSheetsUseCase` - Record to spreadsheet
- `SyncCarWizardUseCase` - Integrate with CarWizard

**Rules:**
- Depends on domain interfaces
- Coordinates multiple repositories/services
- No framework-specific code
- Returns domain entities

### Adapters Layer (Integration)
**Purpose:** Connect external systems to domain

**Components:**
- `OLXScraper` - Implements `IScraper` for OLX
- `WebMotorsScraper` - Implements `IScraper` for WebMotors
- `FIPEAPIClient` - Implements `IFIPEClient`
- `TelegramBotAdapter` - Implements `IAlertService`
- `GoogleSheetsAdapter` - Implements `ISheetsService`
- `CarWizardAPIClient` - Implements `ICarWizardService`

**Rules:**
- Implements domain interfaces
- Handles external API communication
- Translates between domain models and external formats
- Error handling and retry logic

### Infrastructure Layer
**Purpose:** Persistence, frameworks, and technical details

**Components:**
- `SQLAlchemyListingRepository` - Database persistence
- `SQLAlchemyOpportunityRepository` - Database persistence
- `InMemoryFIPECache` - Caching service
- FastAPI routers and controllers
- Database migrations (Alembic)
- Configuration management

**Rules:**
- Framework-specific implementations
- Database access and ORM
- HTTP server setup
- Dependency injection

## Data Flow

### Scraping Flow
```
Scheduler → ScrapeController → ScrapeListingsUseCase
    → OLXScraper (extract HTML)
    → Listing Entity (validate)
    → ListingRepository (persist)
    → LookupFIPEPriceUseCase
    → FIPEAPIClient (get reference price)
    → CalculateOpportunityScoreUseCase
    → OpportunityRepository (persist)
    → SendTelegramAlertUseCase (if score > 75)
    → LogToSheetsUseCase
```

### Manual Query Flow
```
Admin → OpportunityController → OpportunityRepository
    → Opportunity Entity (filter by score)
    → JSON Response
```

## Key Architectural Decisions

### Clean Architecture
- **Why:** Separation of concerns, testability, maintainability
- **ADR:** [ADR-0001](adr/0001-clean-architecture.md)

### SQLite Database
- **Why:** Simplicity, no server needed, sufficient for MVP
- **ADR:** [ADR-0002](adr/0002-sqlite-database.md)

### FastAPI Framework
- **Why:** Modern, async, auto-generated docs, type hints
- **ADR:** [ADR-0003](adr/0003-fastapi-framework.md)

### BeautifulSoup4 for Scraping
- **Why:** Lightweight, sufficient for static HTML
- **ADR:** [ADR-0004](adr/0004-beautifulsoup-scraping.md)

## Security Architecture

### API Security
- Environment variables for secrets (no hardcoded credentials)
- HTTPS enforced for all external APIs
- Input validation on all endpoints
- Rate limiting on scraping endpoints

### Data Security
- No personally identifiable information (PII) stored
- Google OAuth tokens refreshed automatically
- Telegram bot token validated at startup
- Database file permissions restricted (chmod 600)

### Operational Security
- Structured logging (no secrets in logs)
- Health check endpoint for monitoring
- Graceful error handling (no stack traces to clients)
- Audit trail for all scrape operations

## Scalability Considerations

### Current MVP
- Single-threaded scraping (sufficient for 50-100 listings/hour)
- In-memory cache (simple, fast)
- SQLite database (file-based, no server)
- Single FastAPI instance

### Future Scaling
- **Horizontal scaling:** Add worker processes for parallel scraping
- **Database migration:** PostgreSQL for multi-instance support
- **Distributed cache:** Redis for shared cache across instances
- **Message queue:** Celery for background job processing
- **Load balancing:** Multiple FastAPI instances behind Nginx

## Technology Choices Rationale

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| Python 3.9+ | Language | Team expertise, rich ecosystem for web scraping |
| FastAPI | Web Framework | Modern, async, auto-docs, type safety |
| SQLAlchemy | ORM | Standard Python ORM, supports migrations |
| SQLite | Database | Simplicity, no server, sufficient for MVP |
| BeautifulSoup4 | HTML Parsing | Lightweight, robust, simple API |
| requests | HTTP Client | Standard, reliable, well-documented |
| python-telegram-bot | Telegram SDK | Official-like library, async support |
| gspread | Google Sheets | Mature, OAuth support, simple API |
| Alembic | Migrations | Standard with SQLAlchemy |
| pytest | Testing | Modern, fixtures, parametrization |
| APScheduler | Job Scheduling | Simple, cron-like, in-process |

## Related Documentation
- [Folder Structure](folder-structure.md) - Code organization
- [Tech Stack](tech-stack.md) - Detailed technology listing
- [ADR Index](adr/README.md) - Architectural decisions
