# ADR-0003: Use FastAPI Framework

**Status**: Accepted

**Date**: 2026-02-05

**Deciders**: Tech Lead

**Related ADRs**: [ADR-0001: Clean Architecture](0001-clean-architecture.md)

---

## Context

FIPE Hunter needs a web framework for:
- REST API endpoints (manual scrape triggers, opportunity queries)
- Health check endpoint
- Auto-generated API documentation
- Background job integration

---

## Decision Drivers

- **Type Safety**: Python type hints for validation
- **Performance**: Async support for concurrent operations
- **Documentation**: Auto-generated interactive API docs
- **Team Expertise**: Team familiar with FastAPI
- **Modern Stack**: Python 3.9+ with Pydantic integration

---

## Considered Options

1. **FastAPI** - Modern async framework with auto-docs
2. **Flask** - Lightweight, traditional WSGI framework
3. **Django** - Full-featured batteries-included framework

---

## Decision

**Chosen**: Option 1 - FastAPI

**Rationale**:
FastAPI provides the best balance for FIPE Hunter:
- **Async support**: Handle multiple scraping jobs efficiently
- **Type validation**: Pydantic models prevent runtime errors
- **Auto-documentation**: Swagger UI out of the box (critical for API testing)
- **Performance**: Faster than Flask/Django for async operations
- **Developer experience**: Clear error messages, fast development

---

## Consequences

### Positive
- **Auto-generated docs**: Swagger UI at `/docs`, Redoc at `/redoc`
- **Type validation**: Request/response validation via Pydantic
- **Async support**: Efficient handling of I/O-bound operations
- **Fast development**: Less boilerplate than Flask/Django
- **Modern**: Python 3.9+ type hints, async/await

### Negative
- **Younger ecosystem**: Less mature than Flask/Django
- **Async complexity**: Developers need to understand async/await
- **Fewer plugins**: Smaller ecosystem than Django

### Risks
- **Risk**: Team unfamiliar with async programming
  - **Mitigation**: Training session, code review focus on async patterns

---

## Implementation Notes

**Entry Point:**
```python
# src/main.py
from fastapi import FastAPI
from src.adapters.controllers import scrape_controller, opportunity_controller

app = FastAPI(
    title="FIPE Hunter API",
    description="Automated vehicle opportunity finder",
    version="1.0.0"
)

app.include_router(scrape_controller.router)
app.include_router(opportunity_controller.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**Running:**
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Validation

**Success Criteria**:
- API endpoints respond < 200ms for simple queries
- Auto-generated docs accurate and useful
- Type validation catches errors before runtime

**Review Date**: 2026-08-05

---

## References
- [FastAPI Official Docs](https://fastapi.tiangolo.com/)
- [Async Programming in Python](https://realpython.com/async-io-python/)
