# ADR-0002: Use SQLite for Database

**Status**: Accepted

**Date**: 2026-02-05

**Deciders**: Tech Lead

**Related ADRs**: [ADR-0001: Clean Architecture](0001-clean-architecture.md)

---

## Context

FIPE Hunter needs persistent storage for:
- Scraped vehicle listings
- Calculated opportunities
- Scrape logs and audit trail
- User subscription preferences

MVP requires simple, low-maintenance database suitable for single-instance deployment.

---

## Decision Drivers

- **Simplicity**: No server setup, minimal configuration
- **MVP Scope**: Small data volume (< 10,000 listings expected)
- **Single Instance**: No need for multi-instance coordination
- **Development Speed**: Fast iteration, no deployment overhead
- **Zero Cost**: No database server licensing or hosting

---

## Considered Options

1. **SQLite** - File-based, embedded database
2. **PostgreSQL** - Full-featured relational database
3. **MongoDB** - NoSQL document database

---

## Decision

**Chosen**: Option 1 - SQLite

**Rationale**:
SQLite is perfect for MVP because:
- No server setup (file-based, embedded)
- Sufficient performance for MVP volume (< 10k records)
- ACID compliant (reliable transactions)
- Zero operational overhead
- Easy migration path to PostgreSQL when needed

Clean Architecture allows easy migration to PostgreSQL in Phase 2 without changing domain or use cases.

---

## Consequences

### Positive
- **Zero setup**: Works out of the box
- **Fast development**: No database server configuration
- **Portable**: Single file, easy to backup/restore
- **Sufficient performance**: Fast for < 100k rows
- **Standard SQL**: Compatible with SQLAlchemy ORM

### Negative
- **Single writer**: No concurrent writes (acceptable for MVP)
- **No remote access**: File-based only
- **Limited scalability**: Not suitable for horizontal scaling

### Risks
- **Risk**: Data volume exceeds SQLite capacity
  - **Mitigation**: Migrate to PostgreSQL when > 100k listings (Clean Architecture makes this easy)
- **Risk**: Concurrent write conflicts
  - **Mitigation**: Single scraper instance only in MVP

---

## Implementation Notes

**Database File Location:**
```bash
./data/fipe_hunter.db
```

**SQLAlchemy Configuration:**
```python
# src/infrastructure/database/connection.py
from sqlalchemy import create_engine

DATABASE_URL = "sqlite:///./data/fipe_hunter.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
```

**Migration Path:**
When migrating to PostgreSQL:
1. Change `DATABASE_URL` environment variable
2. Run Alembic migrations
3. No changes to domain or use cases (thanks to Clean Architecture)

---

## Validation

**Success Criteria**:
- Database operations < 100ms for < 10k records
- Zero operational issues in MVP
- Easy migration to PostgreSQL when needed

**Review Date**: 2026-06-05 (when listing count approaches 50k)

---

## References
- [SQLite Official Docs](https://www.sqlite.org/index.html)
- [When to use SQLite](https://www.sqlite.org/whentouse.html)
