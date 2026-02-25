# Architecture Decision Records - FIPE Hunter

> Project-level technical decisions for FIPE Hunter.
> For enterprise-wide decisions, see [EA ADRs](../../ea/ADR/).

## Active ADRs

| ADR | Title | Status | Date | Category |
|-----|-------|--------|------|----------|
| [0001](0001-clean-architecture.md) | Use Clean Architecture | Accepted | 2026-02-05 | Architecture |
| [0002](0002-sqlite-database.md) | Use SQLite for Database | Accepted | 2026-02-05 | Data |
| [0003](0003-fastapi-framework.md) | Use FastAPI Framework | Accepted | 2026-02-05 | Infrastructure |
| [0004](0004-beautifulsoup-scraping.md) | Use BeautifulSoup4 for Web Scraping | Accepted | 2026-02-05 | Integration |
| [0005](0005-apscheduler-jobs.md) | Use APScheduler for Background Jobs | Accepted | 2026-02-05 | Infrastructure |
| [0006](0006-nodriver-headless-chromium.md) | Use nodriver + Headless Chromium for WebMotors | Accepted | 2026-02-23 | Integration |

## Categories

- **Architecture**: System design patterns, layer organization
- **Data**: Database, caching, storage strategies
- **Integration**: External APIs, scraping, third-party services
- **Infrastructure**: Frameworks, servers, deployment
- **Testing**: Test strategies, tools, coverage
- **Security**: Authentication, encryption, compliance

## Deprecated/Superseded

| ADR | Title | Superseded By |
|-----|-------|---------------|
| - | - | - |

## Creating New ADRs

Use the template:

```bash
cp template.md 0006-new-decision.md
```

Update the index (this file) when adding new ADRs.

## Related Documentation
- [Architecture](../architecture.md) - C4 diagrams and system design
- [Tech Stack](../tech-stack.md) - Technologies used
