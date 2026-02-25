# Use Case Specification: FIPE Lookup

## 1. Use Case Name
FIPE Lookup (Lookup Official Vehicle Reference Price)

## 2. Brief Description
Query the official FIPE (Tabela FIPE) Brazilian vehicle pricing database to obtain current reference prices for vehicles identified in marketplace listings. Includes caching strategy to optimize API usage and performance.

## 3. Actors
- **Price Comparison Engine:** Internal system component that needs vehicle reference prices
- **FIPE Public API:** External REST API providing vehicle pricing data

## 4. Preconditions
- FIPE public API is accessible at https://parallelum.com.br/fipe/api/v1/
- Cache storage (Redis or in-memory) is available
- Network connectivity to FIPE API exists
- Vehicle brand and model have been normalized

## 5. Basic Flow of Events

### Primary Flow: Successful Price Lookup with Cache Hit

1. Price comparison engine requests FIPE price for: Vehicle(Volkswagen, Gol, 2015)
2. System generates cache key: "volkswagen-gol-2015"
3. System queries cache repository for key
4. Cache hit found and entry not expired (< 24 hours old)
5. Return cached price (R$ 25,000) to caller
6. End use case (< 100ms response time)

### Alternative Flow: Cache Miss - API Lookup Required

1. Price comparison engine requests FIPE price
2. System generates cache key and queries cache
3. Cache miss OR cache entry expired
4. System normalizes vehicle data:
   a. Brand: trim, uppercase, handle abbreviations (VW → Volkswagen)
   b. Model: trim, remove engine size suffix (Gol 1.0 → Gol)
   c. Year: validate is integer in valid range
5. System queries FIPE API endpoint: /marcas (brands list)
   a. Request: GET /marcas
   b. Response: List of brand IDs and names
6. System performs fuzzy matching on brand name
   a. Calculate string similarity (Levenshtein distance)
   b. Find best match (>85% similarity)
   c. Return FIPE brand ID
7. System queries FIPE API endpoint: /marcas/{id}/modelos (models list)
   a. Request: GET /marcas/23/modelos (example: Volkswagen)
   b. Response: List of model IDs and names
8. System performs fuzzy matching on model name
   a. Calculate string similarity
   b. Find best match (>85% similarity)
   c. Return FIPE model ID
9. System queries FIPE API endpoint: /marcas/{id}/modelos/{id}/anos (years list)
   a. Request: GET /marcas/23/modelos/2/anos
   b. Response: List of years available
10. System finds exact year match from list
11. System queries FIPE API endpoint: /marcas/{id}/modelos/{id}/anos/{ano} (final price)
    a. Request: GET /marcas/23/modelos/2/anos/2015-1 (2015 first generation)
    b. Response: { "nome": "Volkswagen Gol 1.0", "valor": "R$ 25.000,00", ... }
12. System parses response:
    a. Extract price: 25000.00
    b. Extract version/name: "Gol 1.0"
    c. Extract timestamp: current FIPE table date
13. System caches result:
    a. Key: "volkswagen-gol-2015"
    b. Value: { price: 25000.00, version: "Gol 1.0", cached_at: now, expires_at: now+24h }
    c. Store in cache repository with 24-hour TTL
14. Return price (R$ 25,000) to caller

### Alternative Flow: Vehicle Not Found in FIPE

1. System queries FIPE API for vehicle (brand/model/year not in database)
2. API returns HTTP 404 or empty results
3. System logs lookup failure:
   a. Vehicle: Volkswagen/Unknown Model/2015
   b. Timestamp: 2024-01-15 10:30:00
   c. Error: "Model not found in FIPE database"
4. System returns NULL price to caller
5. Price comparison engine marks opportunity for manual review
6. System does not crash or fail entire pipeline

### Alternative Flow: Cache Entry Expired

1. System queries cache for vehicle key
2. Cache entry found BUT expires_at timestamp is in past
3. System invalidates cache entry
4. System treats as cache miss and queries FIPE API (see Alternative Flow 2)
5. Returns fresh price

### Alternative Flow: FIPE API Timeout

1. System initiates HTTP request to FIPE API
2. Request does not complete within 10 seconds
3. System detects timeout
4. System retries request with fresh HTTP connection (1 retry maximum)
5. If retry succeeds:
   a. Process response normally
   b. Cache result
   c. Return price
6. If retry fails:
   a. Log error with full context
   b. Mark opportunity for manual review
   c. Return NULL price
   d. Alert administrators of FIPE API connectivity issue

### Alternative Flow: FIPE API Rate Limiting (HTTP 429)

1. System submits request to FIPE API
2. API responds with HTTP 429 (Too Many Requests)
3. System detects rate limit response
4. System implements exponential backoff:
   a. Initial wait: 60 seconds
   b. If retry fails: wait 120 seconds
   c. If still fails: wait 240 seconds (max 3 retries)
5. System resumes requests after backoff period
6. All subsequent requests subject to adaptive delay (start with 2 seconds)
7. Log rate limit events with timestamps
8. Monitor rate limit frequency to inform batch size decisions

### Alternative Flow: API Response Parsing Error

1. System receives response from FIPE API
2. Response JSON structure doesn't match expected schema
3. System logs parsing error with full response body
4. System detects API version change or data format change
5. System falls back to cached price if available
6. If no cache available:
   a. Mark opportunity for manual review
   b. Return NULL price
   c. Alert administrators of API schema change
7. Engineers review and update parser logic

### Alternative Flow: Network Error (No Connectivity)

1. System attempts to establish connection to FIPE API
2. Network error occurs (DNS failure, connection refused, etc.)
3. System detects network error
4. System retries up to 3 times with exponential backoff
5. If all retries fail:
   a. Log detailed error (DNS timeout, connection refused, etc.)
   b. Return NULL price
   c. Alert administrators of network connectivity issue
   d. System continues processing (don't crash pipeline)

## 6. Postconditions
- FIPE reference price is obtained or marked as unavailable
- Price is cached for future lookups (24-hour TTL)
- If lookup failed, opportunity is marked for manual review
- System is ready to proceed with price comparison
- All lookups (successful or failed) are logged

## 7. Special Requirements

### Performance
- Successful cache hit: < 100ms response time
- FIPE API lookup (cache miss): 1-5 seconds (depending on network)
- Maximum timeout per request: 10 seconds
- Concurrent lookups: support multiple simultaneous requests without blocking

### Caching Strategy
- **Cache Key:** "brand-model-year" (lowercase, normalized)
- **Cache Duration:** 24 hours from lookup time
- **Cache Storage:** Redis or in-memory dictionary
- **Concurrent Requests:** If 2+ requests for same vehicle while API call in progress, second request should wait for first to complete and use same result (lock/semaphore pattern)
- **Cache Invalidation:** Automatic (TTL), no manual invalidation in MVP

### Fuzzy Matching
- **Similarity Threshold:** >= 85% (Levenshtein distance)
- **Brand Examples:**
  - "VW" → "Volkswagen" (abbreviation)
  - "BMW" → "BMW" (exact)
  - "Hiundai" → "Hyundai" (typo)
  - "FIAT" → "Fiat" (case variation)
- **Model Examples:**
  - "Gol 1.0" → "Gol" (remove engine size)
  - "Civic EX" → "Civic" (remove trim)
  - "Corolla 2.0" → "Corolla" (remove engine size)
  - "Civic " → "Civic" (trim whitespace)

### Error Handling & Fallback
- **Transient Errors (timeout, 429):** Retry with backoff
- **Persistent Errors (vehicle not found, 404):** Return NULL, mark for review
- **API Schema Changes:** Fall back to cache if available, alert admins
- **Network Errors:** Return NULL, mark for review, don't crash pipeline

### Data Validation
- Brand: required, non-empty string
- Model: required, non-empty string
- Year: required, integer 1950 to current year
- Price (response): must be positive number

### Logging & Monitoring
- Log all API requests with timestamp and parameters
- Log all cache hits/misses with decision rationale
- Log all failures with full context (vehicle, error type, error message)
- Alert on repeated failures (e.g., brand/model consistently not found)
- Track FIPE API response times for performance monitoring

### Rate Limiting Strategy
- **Batch Processing:** If processing 100 listings, spread FIPE requests over time
- **Adaptive Delays:** Start with 1-2 second delay, increase if rate limit detected
- **Max Concurrent Requests:** 5 simultaneous requests maximum
- **Recovery:** Resume at 1-2 second delay after rate limit window expires

## 8. Extension Points

### Future Enhancements
- **Multiple FIPE Data Versions:** Support historical FIPE tables for trend analysis
- **Manual Price Override:** Allow administrators to manually set prices for vehicles not in FIPE
- **Alternative Price Sources:** Fallback to other APIs (Compra Certa, etc.) if FIPE unavailable
- **Vehicle Variations:** Support multiple versions/trims per brand/model/year
- **Used Vehicle Price Adjustment:** Apply depreciation adjustments for older vehicles
- **Regional Price Variations:** Support regional FIPE price differences if available
- **API Webhook:** Real-time notifications when FIPE prices update

## 9. Constraints

### API Limitations
- FIPE API is free (no authentication required)
- Rate limit: ~30-60 requests per minute (typical free APIs)
- No SLA (not guaranteed uptime)
- Occasional maintenance windows

### Technical Constraints
- Must support offline operation if cache populated
- Cache storage must support key expiration (TTL)
- Must handle geographic constraints (FIPE is Brazil-specific, some regions may not have all vehicles)

### Compliance
- Use official FIPE data source only
- Respect FIPE API terms of service
- Implement reasonable request rates
- Cache results to minimize API calls
