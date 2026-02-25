# Tech Stack: FIPE Hunter

## Core Technologies

| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| Language | Python | 3.9+ | Team expertise, rich ecosystem for web scraping and data processing |
| Web Framework | FastAPI | 0.104+ | Modern async framework, auto-generated docs, type safety via Pydantic |
| Database | SQLite | 3.x | Simplicity, no server setup, sufficient for MVP volume |
| ORM | SQLAlchemy | 2.0+ | Industry standard, type hints support, migration tooling |
| Migration Tool | Alembic | 1.12+ | Standard migration tool for SQLAlchemy |

## Web Scraping

Each marketplace requires a different scraping strategy due to different bot-protection systems.

| Purpose | Technology | Version | Rationale |
|---------|------------|---------|-----------|
| OLX HTTP Client | curl_cffi | 0.7+ | TLS fingerprint impersonation to bypass Cloudflare |
| OLX HTML Parsing | BeautifulSoup4 | 4.12+ | Lightweight static HTML parsing |
| WebMotors Browser | nodriver | 0.48+ | Undetected Chrome (CDP) to bypass PerimeterX |
| WebMotors Runtime | Chromium | system | Headless browser binary installed via apt in Docker |
| User-Agent Rotation | fake-useragent | 1.4+ | Anti-bot measure (OLX fallback) |

**Scraping strategy by marketplace:**

| Marketplace | Bot Protection | Library | Technique |
|-------------|---------------|---------|-----------|
| OLX | Cloudflare | curl_cffi + BeautifulSoup4 | HTTP + TLS fingerprint impersonation |
| WebMotors | PerimeterX | nodriver + Chromium (headless) | Real headless browser via CDP |

**Why two different approaches?**
- OLX is protected by Cloudflare and can be bypassed with `curl_cffi` TLS impersonation — no browser binary needed
- WebMotors is protected by PerimeterX (HUMAN Security) which blocks all pure HTTP clients; a real Chrome instance via `nodriver` is required
- Adding Chromium to Docker increases image size by approximately 200 MB but avoids paid scraping proxies

## External API Integrations

| Service | Technology | Version | Rationale |
|---------|------------|---------|-----------|
| FIPE API Client | requests | 2.31+ | Simple REST API, no official SDK needed |
| Telegram Bot | python-telegram-bot | 20.7+ | Mature library, async support, actively maintained |
| Google Sheets | gspread | 5.12+ | OAuth 2.0 support, simple API, widely used |
| CarWizard API | requests | 2.31+ | Custom REST API integration |

## Data Processing

| Purpose | Technology | Version | Rationale |
|---------|------------|---------|-----------|
| Data Validation | Pydantic | 2.5+ | Type validation, JSON schema generation, FastAPI integration |
| Date/Time Handling | python-dateutil | 2.8+ | Timezone-aware datetime parsing |
| String Matching | fuzzywuzzy | 0.18+ | Fuzzy matching for brand/model name variations |

## Background Jobs

| Purpose | Technology | Version | Rationale |
|---------|------------|---------|-----------|
| Scheduler | APScheduler | 3.10+ | Simple cron-like scheduling, in-process, no broker needed |

**Why not Celery?**
- APScheduler is simpler for MVP
- No message broker setup required (Redis/RabbitMQ)
- Sufficient for hourly/daily scraping jobs
- Can migrate to Celery if distributed task queue becomes necessary

## Testing

| Purpose | Technology | Version | Rationale |
|---------|------------|---------|-----------|
| Test Framework | pytest | 7.4+ | Modern, fixtures, parametrization, extensive plugin ecosystem |
| Test Coverage | pytest-cov | 4.1+ | Coverage reporting integrated with pytest |
| HTTP Mocking | responses | 0.24+ | Mock external HTTP requests for integration tests |
| API Testing | httpx | 0.25+ | Async HTTP client for testing FastAPI endpoints |

## Code Quality

| Purpose | Technology | Version | Rationale |
|---------|------------|---------|-----------|
| Linting | ruff | 0.1+ | Fast, comprehensive linter (replaces flake8, isort, pylint) |
| Formatting | black | 23.12+ | Opinionated formatter, no configuration needed |
| Type Checking | mypy | 1.7+ | Static type checking for Python |
| Pre-commit Hooks | pre-commit | 3.6+ | Automated checks before commit |

## Dependency Management

| Purpose | Technology | Version | Rationale |
|---------|------------|---------|-----------|
| Package Manager | Poetry | 1.7+ | Modern dependency resolver, lock file, virtual env management |

**Dependencies File:**
```toml
# pyproject.toml
[tool.poetry.dependencies]
python = "^3.9"
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
sqlalchemy = "^2.0.0"
alembic = "^1.12.0"
pydantic = "^2.5.0"
requests = "^2.31.0"
beautifulsoup4 = "^4.12.0"
lxml = "^4.9.0"
fake-useragent = "^1.4.0"
python-telegram-bot = "^20.7.0"
gspread = "^5.12.0"
oauth2client = "^4.1.3"
apscheduler = "^3.10.0"
fuzzywuzzy = "^0.18.0"
python-Levenshtein = "^0.23.0"
python-dateutil = "^2.8.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
pytest-asyncio = "^0.21.0"
responses = "^0.24.0"
httpx = "^0.25.0"
ruff = "^0.1.0"
black = "^23.12.0"
mypy = "^1.7.0"
pre-commit = "^3.6.0"
```

## Development Tools

| Purpose | Technology | Version | Rationale |
|---------|------------|---------|-----------|
| ASGI Server | Uvicorn | 0.24+ | Fast ASGI server for FastAPI |
| API Documentation | Swagger UI | (built-in FastAPI) | Auto-generated, interactive API docs |
| Database Browser | sqlite-web | 0.6+ | Web-based SQLite browser for debugging |

## Production Deployment

| Purpose | Technology | Rationale |
|---------|------------|-----------|
| Hosting | Render | PaaS — zero-ops deployment, free tier available |
| Container | Docker | Portable deployment, controls runtime dependencies |
| Orchestration | Docker Compose | Multi-container coordination for local dev |
| Reverse Proxy | Nginx | Static file serving, SSL termination (future) |

**Docker runtime note:** The production Docker image installs `chromium` and `chromium-driver` via `apt-get` in the runtime stage. This is required by `nodriver` for WebMotors scraping. It adds approximately 200 MB to the image size but eliminates the need for external Chromium management or Xvfb (virtual display). The `headless=True` mode runs without a display server.

## Environment Configuration

```bash
# .env.example
DATABASE_URL=sqlite:///./fipe_hunter.db
FIPE_API_URL=https://parallelum.com.br/fipe/api/v1
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
GOOGLE_SHEETS_CREDENTIALS_FILE=./credentials/google_sheets_credentials.json
GOOGLE_SHEET_ID=your_sheet_id_here
CARWIZARD_API_URL=https://api.carwizard.example.com
CARWIZARD_API_KEY=your_api_key_here
SCRAPE_SCHEDULE_HOURS=1  # Scrape every N hours
LOG_LEVEL=INFO
```

## ADR References

- [ADR-0001: Clean Architecture](adr/0001-clean-architecture.md)
- [ADR-0002: SQLite Database](adr/0002-sqlite-database.md)
- [ADR-0003: FastAPI Framework](adr/0003-fastapi-framework.md)
- [ADR-0004: BeautifulSoup for Scraping (OLX)](adr/0004-beautifulsoup-scraping.md)
- [ADR-0005: APScheduler for Jobs](adr/0005-apscheduler-jobs.md)
- [ADR-0006: nodriver + Headless Chromium for WebMotors](adr/0006-nodriver-headless-chromium.md)

## Version Pinning Strategy

- **Production dependencies:** Pin to minor version (`^x.y.0`) for security updates
- **Dev dependencies:** Pin to major version (`^x.0.0`) for flexibility
- **Lock file:** Use `poetry.lock` for reproducible builds
- **Security updates:** Monthly review of dependency vulnerabilities

## Technology Upgrade Path

### Phase 1 (MVP - Current)
- SQLite, APScheduler
- OLX: curl_cffi + BeautifulSoup4
- WebMotors: nodriver + Chromium headless (implemented 2026-02-23)

### Phase 2 (Scaling)
- Migrate to PostgreSQL (multi-instance support)
- Add Redis for distributed caching
- Add Celery for distributed task queue
- Evaluate Playwright as an alternative to nodriver if PerimeterX detection improves

### Phase 3 (Production)
- Docker containerization
- Kubernetes orchestration
- Distributed tracing (OpenTelemetry)
- Metrics (Prometheus/Grafana)

## Related Documentation
- [Architecture](architecture.md) - System design
- [Folder Structure](folder-structure.md) - Code organization
- [ADR Index](adr/README.md) - Technology decisions
