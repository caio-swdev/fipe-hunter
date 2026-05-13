# ADR-0007: FIPE Catalog Caching Strategy

**Status**: Accepted

**Date**: 2026-02-26

**Deciders**: Tech Lead, Development Team

**Related ADRs**:
- [ADR-0001: Use Clean Architecture](./0001-clean-architecture.md)
- [ADR-0002: Use SQLite for Database](./0002-sqlite-database.md)
- [ADR-0003: Use FastAPI Framework](./0003-fastapi-framework.md)

---

## Context

FIPE Hunter calls the public FIPE API (parallelum.com.br) to resolve vehicle prices during both scheduled scraping jobs and user-triggered on-demand searches. Each price lookup requires up to four sequential API calls (brands → models → years → price). The catalog endpoints (brands, models, years) rarely change — the FIPE table is updated once per month — but they can be hit dozens of times per minute during high-traffic periods or when scanning many listings.

Without caching, every lookup triggers 3–4 outbound API calls to an uncontrolled third-party endpoint. This creates three concrete problems:

1. **Rate limiting**: The FIPE API is an unofficial free service with no published SLA. Hitting it on every request risks 429 responses during concurrent workloads.
2. **Latency**: Each API round-trip adds 300–800 ms. A lookup requiring brands + models + years + price over a slow connection can take 2–4 seconds.
3. **Availability coupling**: If FIPE API degrades temporarily, all lookups fail with no fallback.

A caching strategy that covers in-process, cross-request, and client-side layers was needed to address all three problems without introducing managed caching infrastructure (Redis, Memcached) at MVP scale.

---

## Decision Drivers

- **Rate limit protection**: Reduce outbound FIPE API calls to stay well below any implicit rate cap
- **Latency**: Catalog data (brands, models, years) should be served from memory or DB, not from a third-party API
- **Resilience**: Cache entries should survive process restarts (Render free-tier spins down on inactivity)
- **Zero infrastructure cost**: No Redis/Memcached; app runs as a single Render free-tier instance with no horizontal scaling
- **Correctness on stale data**: Graceful degradation is acceptable (serve last-known data); catalog changes are low-frequency (monthly FIPE table updates)
- **CDN readiness**: Headers should be compatible with a future CDN layer without code changes
- **Partial-result safety**: Versions endpoint can time out mid-fan-out; corrupted partial results must never be cached

---

## Considered Options

### Option A: Single in-memory dict (module-level) only
Cache catalog data in a Python module-level dict with a fixed TTL. Simple, zero latency on hit. Lost on process restart; Render's free-tier instances spin down after 15 min of inactivity, so every cold start re-fetches all catalog data.

### Option B: Redis
Standard distributed cache. Survives restarts, supports horizontal scaling. Requires a managed Redis instance (Render Redis starts at $10/month, adds operational overhead). Overkill for a single-instance MVP.

### Option C: In-memory dict + DB-backed adaptive-TTL cache + HTTP Cache-Control headers (chosen)
Three-layer approach: fast in-process dict for hot paths within a process lifetime, a PostgreSQL/SQLite-backed repository that survives restarts with an adaptive TTL that lengthens as data proves stable, and `Cache-Control` headers that offload repeat browser requests entirely to the browser cache.

---

## Decision

**Chosen**: Option C — Three-layer caching (in-memory dict + DB adaptive TTL + HTTP Cache-Control)

**Rationale**:
The three layers attack different failure modes at different cost points:

- **Layer 1 (in-memory dict)** eliminates FIPE API calls entirely for hot catalog keys within a single process lifetime. Since FIPEClient is instantiated per request, the cache is module-level (not instance-level) so it is shared across all requests in the same worker process. TTL is fixed at 1 hour as a conservative floor; if the process is long-lived this prevents serving data that is hours or days old.
- **Layer 2 (DB adaptive TTL)** survives process restarts and cold starts. The adaptive TTL ladder rewards stability: a cache key whose item count is consistent across successive fetches earns progressively longer TTLs (1h → 6h → 1 day → 7 days → 30 days). A count change (possible API inconsistency or partial response) resets the streak to 0 and TTL back to 1 hour. This means a stable brands list (rarely changes) can reach a 30-day TTL, while a volatile endpoint stays at short TTLs automatically.
- **Layer 3 (Cache-Control headers)** prevents the browser from making repeat API calls at all for the same session. `public, max-age=3600` tells the browser to cache the response for 1 hour. `stale-while-revalidate=86400` lets the browser serve the cached response immediately and revalidate in the background, eliminating perceived latency on stale data for up to 24 hours. Using `public` (not `private`) allows a future CDN to cache responses at the edge without any code changes.

The versions endpoint (`/catalog/versions`) is excluded from DB caching when the fan-out times out. A 20-second timeout gates concurrent year-checks for all model variants (up to 40+ for a popular model like Toyota Corolla). If any tasks are still pending when the timeout fires, results are returned to the caller but are NOT written to the DB cache. This prevents a partial result set from being served as authoritative on the next request.

Redis was rejected because the app runs as a single process on Render free-tier. Redis adds $10+/month and operational overhead. The module-level dict plus DB cache achieves the same correctness guarantees for a single-instance deployment at zero marginal cost.

---

## Consequences

### Positive
- FIPE API call volume is dramatically reduced; hot catalog keys (brands, popular brand models) are served from the in-memory dict within the same process lifetime
- DB cache survives Render cold starts; catalog data is available immediately without waiting for a FIPE API round-trip
- Adaptive TTL self-tunes: stable data converges to a 30-day TTL, reducing DB reads for the most common keys
- Browser cache eliminates repeat network requests entirely for the same user session
- `public` Cache-Control header enables CDN caching if one is added (Cloudflare, Render's CDN layer) without any backend changes
- Partial timeout in versions endpoint never corrupts the DB cache

### Negative
- In-memory dict is not shared across multiple worker processes (if concurrency is increased beyond one Uvicorn worker, each process has its own dict). This is acceptable for the current single-worker Render deployment.
- Two cache stores must be kept coherent. If a DB cache entry is manually deleted, the in-memory dict may serve the old value until TTL expires (up to 1 hour).
- Cache-busting on FIPE table update (monthly) requires waiting for in-memory TTL expiry plus browser cache TTL — up to 25 hours of stale data visible to a browser that cached the response just before the update.

### Risks
- **Risk**: Multiple worker processes diverge on cache state if concurrency is scaled up
  - **Mitigation**: The DB cache layer is always the source of truth after a restart. Promote to Redis if the deployment scales beyond a single Uvicorn worker.
- **Risk**: Partial timeout in versions endpoint serves an incomplete list to the user
  - **Mitigation**: The result IS returned to the caller on timeout (best-effort); only DB persistence is skipped. Users see fewer versions than expected but never a stale partial list from a previous request.
- **Risk**: FIPE API changes its catalog (new brand added) but stale data is served for up to 30 days for high-streak keys
  - **Mitigation**: TTL ladder is seeded conservatively (1h on first hit). Operator can purge the `catalog_cache` DB table to force a fresh fetch if a catalog update is known.

---

## Implementation Notes

### Layer 1: Module-level in-memory dict

Location: `src/libs/infra-py/fipe_infra/clients/fipe_client.py`, line 25.

```python
# Module-level — shared across all FIPEClient instances in the same process.
_catalog_cache: dict = {}
_FALLBACK_TTL_SECONDS = 3600  # 1h

def _dict_cache_get(key: str):
    entry = _catalog_cache.get(key)
    if entry and time.time() < entry[1]:
        return entry[0]
    return None

def _dict_cache_set(key: str, data) -> None:
    _catalog_cache[key] = (data, time.time() + _FALLBACK_TTL_SECONDS)
```

The `FIPEClient._cache_get` / `_cache_set` methods delegate to the DB repo when injected, otherwise fall through to the dict. The dict acts as a read-through L1 cache in front of the DB.

### Layer 2: DB adaptive-TTL cache

Location: `src/libs/infra-py/fipe_infra/repos/catalog_cache_repository.py`

TTL ladder (stable_streak thresholds):

| Streak | TTL |
|--------|-----|
| 0 | 1 hour |
| >= 1 | 6 hours |
| >= 3 | 1 day |
| >= 6 | 7 days |
| >= 10 | 30 days |

The `count` parameter on `set()` is the item count returned by the FIPE API (e.g., number of brands, number of models for a brand). A consistent count increments the streak; a divergent count resets it.

### Layer 3: HTTP Cache-Control headers

Location: `src/apps/api/app/routes/fipe_routes.py`, line 14.

```python
_CATALOG_CACHE_HEADERS = {
    "Cache-Control": "public, max-age=3600, stale-while-revalidate=86400"
}
```

Applied to three catalog routes: `GET /fipe/catalog/models`, `GET /fipe/catalog/versions`, `GET /fipe/catalog/years`. NOT applied to `GET /fipe/lookup` (price lookups are user-specific and must always hit the server).

### Versions endpoint partial-timeout guard

```python
# Only cache when ALL tasks completed (no pending tasks means no partial timeout)
if not pending:
    self._cache_set(versions_key, results, count=len(results))
return results
```

---

## Validation

**Success Criteria**:
- Cache hit rate (`get_cache_stats()`) exceeds 80% for catalog endpoints after warm-up in a single session
- FIPE API outbound call count drops by >= 90% across a 10-search session (verified via `ApiHitRepository`)
- Cold-start lookup (after Render spin-down) completes in < 5 seconds by serving from DB cache instead of live FIPE API
- Browser DevTools shows `Cache-Control: public, max-age=3600, stale-while-revalidate=86400` on catalog responses
- Versions endpoint returns partial results (not empty list) when FIPE API times out for some variants

**Review Date**: 2026-08-26 (reassess if deployment scales beyond one Uvicorn worker, or if Render adds native Redis as a free-tier add-on)

---

## References
- [FIPE API (unofficial, parallelum.com.br)](https://deividfortuna.github.io/fipe/)
- [MDN: Cache-Control — stale-while-revalidate](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control#stale-while-revalidate)
- [RFC 5861: HTTP Cache-Control Extensions for Stale Content](https://www.rfc-editor.org/rfc/rfc5861)
- [ADR-0002: SQLite Database](./0002-sqlite-database.md) — DB layer used by CatalogCacheRepository
- [fipe_client.py](../../../../src/libs/infra-py/fipe_infra/clients/fipe_client.py) — Layer 1 implementation
- [catalog_cache_repository.py](../../../../src/libs/infra-py/fipe_infra/repos/catalog_cache_repository.py) — Layer 2 implementation
- [fipe_routes.py](../../../../src/apps/api/app/routes/fipe_routes.py) — Layer 3 Cache-Control headers
