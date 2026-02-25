# ADR-0005: Use APScheduler for Background Jobs

**Status**: Accepted

**Date**: 2026-02-05

**Deciders**: Tech Lead

**Related ADRs**: [ADR-0001: Clean Architecture](0001-clean-architecture.md)

---

## Context

FIPE Hunter needs to run periodic background jobs:
- Hourly marketplace scraping
- Daily FIPE price cache refresh
- Periodic Telegram alert dispatch

MVP requires simple job scheduling without distributed task queue complexity.

---

## Decision Drivers

- **Simplicity**: No message broker setup (Redis/RabbitMQ)
- **MVP Scope**: Single instance deployment
- **Integration**: Easy integration with FastAPI
- **Flexibility**: Cron-like scheduling syntax
- **Low Overhead**: In-process scheduler

---

## Considered Options

1. **APScheduler** - In-process job scheduler
2. **Celery** - Distributed task queue
3. **Cron + Script** - System-level cron jobs

---

## Decision

**Chosen**: Option 1 - APScheduler

**Rationale**:
APScheduler is ideal for MVP because:
- No external dependencies (no Redis/RabbitMQ)
- Simple cron-like syntax for scheduling
- Runs in-process with FastAPI
- Sufficient for single-instance deployment
- Can migrate to Celery when horizontal scaling needed

---

## Consequences

### Positive
- **Simple setup**: No message broker infrastructure
- **Easy integration**: Runs within FastAPI application
- **Flexible scheduling**: Cron, interval, and date-based triggers
- **Low overhead**: In-process, no network calls
- **Fast development**: Immediate iteration

### Negative
- **Single instance**: Cannot distribute jobs across workers
- **No persistence**: Jobs lost on restart (acceptable for MVP)
- **No retry UI**: Limited job monitoring compared to Celery

### Risks
- **Risk**: Need distributed task queue for scaling
  - **Mitigation**: Migrate to Celery in Phase 2 (when multi-instance deployment required)
- **Risk**: Jobs lost on application restart
  - **Mitigation**: Acceptable for MVP; manual re-trigger available via API

---

## Implementation Notes

**Scheduler Setup:**
```python
# src/infrastructure/scheduler/jobs.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.application.scrape_listings import ScrapeListingsUseCase

scheduler = AsyncIOScheduler()

def schedule_jobs(scrape_use_case: ScrapeListingsUseCase):
    # Scrape OLX every hour
    scheduler.add_job(
        lambda: scrape_use_case.execute("olx"),
        "cron",
        hour="*",
        id="scrape_olx_hourly"
    )

    # Scrape WebMotors every hour (offset by 30 minutes)
    scheduler.add_job(
        lambda: scrape_use_case.execute("webmotors"),
        "cron",
        hour="*",
        minute="30",
        id="scrape_webmotors_hourly"
    )

    scheduler.start()
```

**FastAPI Integration:**
```python
# src/main.py
from fastapi import FastAPI
from src.infrastructure.scheduler.jobs import schedule_jobs, scheduler

app = FastAPI()

@app.on_event("startup")
def startup_event():
    schedule_jobs(scrape_use_case)

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
```

**Migration Path to Celery:**
When horizontal scaling required:
1. Set up Redis/RabbitMQ message broker
2. Create Celery tasks from use cases
3. Replace APScheduler with Celery Beat
4. No changes to domain or use cases

---

## Validation

**Success Criteria**:
- Hourly scrapes execute reliably
- Jobs trigger within 1 second of scheduled time
- No memory leaks after 24+ hours

**Review Date**: 2026-06-05 (when multi-instance deployment considered)

---

## References
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
