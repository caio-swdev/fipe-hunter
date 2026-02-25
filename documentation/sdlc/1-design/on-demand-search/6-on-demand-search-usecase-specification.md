# Use Case Specification: On-Demand Vehicle Search

## Overview

The **On-Demand Vehicle Search** feature enables users to search for specific vehicles in real-time by providing brand, model, and optional year. The system then:

1. Looks up the FIPE reference price for that vehicle
2. Scrapes OLX listings matching the search criteria
3. Compares listing prices against FIPE reference price
4. Calculates opportunity scores
5. Returns results immediately (10-30 seconds) in the opportunity table format
6. Persists results to the database like bulk-scraped opportunities

This is the "pull" complement to the existing "push" model (scheduled bulk scraping).

---

## Use Cases

### UC1: Parse Search Query

**Goal:** Normalize and validate user search input (brand, model, year)

**Actors:** User

**Preconditions:**
- User is on the Opportunity Browser page
- Search input form is displayed

**Main Flow:**
1. User enters brand name (e.g., "Honda", "VW", "Toyota")
2. User enters model name (e.g., "Civic", "Golf", "Corolla")
3. User optionally enters year (e.g., 2020)
4. User clicks "Search Now" button
5. System validates input:
   - Brand: required, non-empty string
   - Model: required, non-empty string
   - Year: optional, integer 1950 to current year if provided
6. System normalizes brand/model names:
   - "VW" → "Volkswagen"
   - "MB" → "Mercedes-Benz"
   - Trim whitespace, lowercase for comparison
7. System formats search query for downstream systems
8. **[UC2]** proceeds with FIPE lookup

**Alternative Flows:**
- A1: User leaves brand empty → Display error "Brand is required" → Stop
- A2: User leaves model empty → Display error "Model is required" → Stop
- A3: User enters invalid year (non-integer) → Display error → Stop
- A4: User enters future year → Display error → Stop
- A5: User enters year before 1950 → Display error → Stop

**Postconditions:**
- Normalized search query ready for FIPE lookup
- User sees "Loading..." indicator

**Non-Functional Requirements:**
- Validation completes within 500ms
- Error messages displayed immediately

---

### UC2: Lookup FIPE Price

**Goal:** Query FIPE reference price for the vehicle

**Actors:** System

**Preconditions:**
- Search query is parsed and validated
- FIPE API is available (or network connectivity exists)
- FIPE price cache is initialized

**Main Flow:**
1. System receives normalized search query (brand, model, year)
2. System checks FIPE price cache:
   - If cached entry exists AND expires_at > now: Use cached price
   - If cached entry missing or expired: Query FIPE API
3. System builds FIPE API request with vehicle params
4. System sends request to FIPE API (parallelum.com.br)
5. System receives FIPE response with reference price
6. System validates price is positive number
7. System stores price in cache (24-hour TTL)
8. System returns price to price comparison step
9. **[UC5]** proceeds with price comparison

**Alternative Flows:**
- A1: FIPE cache lookup succeeds → Skip API call, proceed to UC5
- A2: FIPE API returns 404 (vehicle not found)
  - Log: "FIPE price not found: {brand} {model} {year}"
  - **[UC14]** trigger error handling
  - Do NOT proceed with price comparison
  - Display error to user: "Vehicle not found in FIPE database"
- A3: FIPE API returns 5xx error
  - Log failure with timestamp and error code
  - **[UC14]** trigger error handling
  - Offer user retry option
- A4: FIPE API timeout (>10 seconds)
  - Log timeout
  - **[UC14]** trigger error handling
  - Stop search, display "FIPE lookup timed out"

**Postconditions:**
- FIPE reference price is available in memory
- Price cache may be updated (if API was called)
- System is ready to scrape OLX listings

**Non-Functional Requirements:**
- Cache lookup: <100ms
- API call: <5 seconds
- Exponential backoff on rate limits (FIPE defaults)
- Fallback to manual scoring if FIPE price unavailable

**Dependencies:**
- FIPEClientService (existing infrastructure)
- PriceCacheRepository (existing infrastructure)
- FIPE API (external service)

---

### UC3: Scrape OLX Listings

**Goal:** Extract listings from OLX marketplace matching search criteria

**Actors:** System

**Preconditions:**
- FIPE price lookup is complete (success or fallback)
- OLX marketplace is accessible
- User is on the Opportunity Browser page (UI shows "Loading...")

**Main Flow:**
1. System receives search query (brand, model, optional year)
2. System uses OLXScraperClient to search OLX
   - Builds search URL: https://www.olx.com.br/autos?q={brand}+{model}+{year}
   - Rotates user-agent headers
   - Applies 1-3 second request delays between requests
3. System fetches OLX search results page
4. System parses HTML to extract listing elements
5. For each listing, system extracts:
   - Vehicle: brand, model, year (from listing text + page context)
   - Price: listing_price in BRL
   - Details: mileage, condition (if available in listing)
   - Seller: seller_name, seller_rating (if available)
   - Metadata: listing URL, description, created_at timestamp
6. System validates each extracted listing:
   - Brand/model match search criteria (fuzzy match acceptable)
   - Price > 0
   - URL is valid HTTPS
   - Year matches if specified (or inferred from listing)
7. System collects all valid listings into list
8. **[UC4]** proceeds with deduplication
9. **[UC5]** proceeds with price comparison

**Alternative Flows:**
- A1: OLX returns 0 listings
  - Log: "No listings found: {brand} {model} {year}"
  - Display message: "No listings found on OLX for {brand} {model} {year}"
  - Stop search (do not create zero opportunities)
  - **[UC14]** handle gracefully
- A2: OLX returns blocked request (429 rate limit)
  - Log: "OLX rate limited"
  - **[UC14]** trigger error handling
  - Implement backoff and retry (up to 3 attempts)
- A3: OLX returns HTML parse error (site structure changed)
  - Log: "OLX parsing error"
  - **[UC14]** trigger error handling
  - Notify administrators (OLX structure may have changed)

**Postconditions:**
- List of extracted listings in memory
- All listings validated against schema
- Ready for deduplication

**Non-Functional Requirements:**
- Scraping completes within 30 seconds (max)
- User-agent rotation active
- Request delays enforced (avoid blocking)
- Graceful handling of site structure changes
- Handle 50+ listings per search

**Dependencies:**
- OLXScraperClient (existing, modified for search query)
- ListingValidator (existing)
- User-agent library (existing)

**Notes:**
- Unlike bulk scraping (which browses categories), this searches by query
- Results are likely smaller (relevant to search) than bulk scrape
- Deduplicate against existing bulk-scraped listings

---

### UC4: Deduplicate Results

**Goal:** Identify and handle duplicate listings

**Actors:** System

**Preconditions:**
- OLX listings are extracted
- Listings table in database contains existing listings

**Main Flow:**
1. System receives list of extracted OLX listings
2. For each extracted listing:
   - Query database: find_by_url(listing.url)
   - If listing URL already exists in database:
     - Mark extracted listing as duplicate
     - Check existing opportunity status:
       - If status = "new", keep it (do not overwrite)
       - If status = "purchased" or "archived", update to "new" (re-surface)
   - If listing URL is new:
     - Proceed to create opportunity
3. Return deduplicated listing list (only new URLs)
4. **[UC5]** proceeds with price comparison

**Alternative Flows:**
- A1: All listings are duplicates
  - Log: "All listings are duplicates"
  - Display message: "All results already in database"
  - Stop search gracefully
  - (Do not create duplicate opportunities)

**Postconditions:**
- List contains only new, non-duplicate listings
- Existing opportunities may be updated (re-surfaced)

**Non-Functional Requirements:**
- Deduplication completes within 2 seconds
- URL matching is exact (case-sensitive)

**Dependencies:**
- ListingRepository.find_by_url() (existing)
- OpportunityRepository (existing)

---

### UC5: Compare Prices

**Goal:** Calculate discount between listing price and FIPE reference price

**Actors:** System

**Preconditions:**
- FIPE reference price is available
- Deduplicated OLX listings are available
- Listing prices are validated (positive numbers)

**Main Flow:**
1. System receives FIPE price and deduplicated listings
2. For each listing:
   - Extract listing_price (in BRL)
   - Calculate discount_pct = (FIPE_price - listing_price) / FIPE_price * 100
   - Calculate discount_amount = FIPE_price - listing_price (in BRL)
   - Validate discount is valid (negative = overpriced, flagged for review):
     - If discount_pct < 20%: Filter out (below opportunity threshold)
     - If discount_pct > 50%: Flag for review (suspicious discount)
     - If 20% <= discount_pct <= 50%: VALID OPPORTUNITY
   - Store discount in listing object
3. Filter to keep only valid opportunities (20-50% discount)
4. Return filtered listings with discount data
5. **[UC6]** proceeds with scoring

**Alternative Flows:**
- A1: All listings are overpriced (negative discount)
  - Display message: "No discounted vehicles found"
  - Stop search
  - Do not create opportunities
- A2: Some listings have suspicious discount (>50%)
  - Log: "Suspicious discount found: {listing_url} {discount_pct}%"
  - Include in results but mark as "requires_review"
  - Operator reviews before alerting

**Postconditions:**
- Discounted listings ready for scoring
- All discounts validated and calculated

**Non-Functional Requirements:**
- Price comparison completes within 2 seconds (100 listings)
- Accurate decimal arithmetic (BRL currency)
- Price validation prevents negative/zero values

**Dependencies:**
- PriceComparisonService (existing)
- PriceComparisonOrchestrator (existing)

---

### UC6: Calculate Opportunity Score

**Goal:** Rank opportunities by profit potential (0-100 scale)

**Actors:** System

**Preconditions:**
- Price comparison is complete
- Valid discounted listings are available
- Listing metadata (mileage, condition, vehicle info) is available

**Main Flow:**
1. System receives list of discounted listings
2. For each listing, calculate score components:
   - **Discount Score** (40% weight):
     - Normalize discount_pct to 0-100 scale
     - Higher discount = higher score
   - **Condition Score** (30% weight):
     - Extract condition from listing: "excellent", "good", "fair", "poor"
     - Map to scores: excellent=100, good=75, fair=50, poor=25
   - **Demand Score** (20% weight):
     - Estimate market demand for vehicle (brand, model, year)
     - Common vehicles (Honda, Toyota) = higher demand
     - Rare vehicles = lower demand
     - Query database for historical opportunities (same brand/model)
   - **Recency Score** (10% weight):
     - Calculate based on listing age (created_at timestamp)
     - Newer listings = higher score
     - Formula: 100 - (days_old * 5), min 0, max 100
3. Apply weights to all components:
   - Final Score = (discount_score * 0.40) + (condition_score * 0.30) + (demand_score * 0.20) + (recency_score * 0.10)
4. Validate score in range [0, 100]
5. Sort listings by score (descending)
6. Return scored opportunities
7. **[UC7]** proceeds with opportunity creation

**Postconditions:**
- All listings have calculated scores (0-100)
- Results are sorted by score descending

**Non-Functional Requirements:**
- Scoring completes within 2 seconds (100 listings)
- Weighted average calculation is accurate
- Component scores normalized to 0-100 range

**Dependencies:**
- ScoringOrchestrator (existing)
- ScoringService (existing)
- Demand estimation (database query for historical data)

**Notes:**
- Scoring algorithm is identical to bulk scraping
- Weights are configurable via system_config table

---

### UC7: Create/Update Opportunity

**Goal:** Save opportunities to database and trigger downstream actions

**Actors:** System

**Preconditions:**
- Scored opportunities are available
- Database is initialized

**Main Flow:**
1. System receives scored opportunities list
2. For each scored opportunity:
   - Create Opportunity entity:
     - listing_id (reference to OLX listing)
     - fipe_price (from UC2)
     - discount_pct, discount_amount (from UC5)
     - score (from UC6)
     - status = "new"
     - source = "on_demand_search" (track source for filtering)
     - created_at = now()
   - Save opportunity to database (opportunities table)
   - Create associated Listing entity if not exists:
     - vehicle_id (lookup or create vehicle)
     - marketplace = "OLX"
     - listing_price, mileage, condition, url, description
     - Save to listings table
3. Trigger downstream actions (conditionally):
   - All opportunities: **[UC8]** Log to Google Sheets
   - If score > 75: **[UC9]** Send Telegram Alert
   - If score > 80: **[UC10]** Sync to CarWizard
4. Update UI with search results (display in opportunity table)
5. Return completion status to user

**Alternative Flows:**
- A1: Opportunity with same URL already exists
  - Query opportunities table by listing URL
  - If existing opportunity:
    - Update status to "new" (re-surface if previously archived)
    - Update score if new calculation is higher
    - Log update to opportunity_logs table
    - Do not create duplicate

**Postconditions:**
- Opportunities saved to database
- Listing data persisted
- Downstream actions queued (sheets, alerts, sync)
- User sees results in opportunity table

**Non-Functional Requirements:**
- Database save completes within 5 seconds (100 opportunities)
- Transactional integrity (all-or-nothing per opportunity)
- Deduplication prevents duplicate records

**Dependencies:**
- OpportunityRepository (existing)
- ListingRepository (existing)
- VehicleRepository (existing)

---

### UC8: Log to Google Sheets

**Goal:** Append opportunities to Google Sheets for persistent logging

**Actors:** System

**Preconditions:**
- Opportunities are created/updated
- Google Sheets API is authenticated
- Spreadsheet is configured

**Main Flow:**
1. System receives list of new/updated opportunities
2. For each opportunity:
   - Format data for Google Sheets:
     - Columns: brand, model, year, listing_price, fipe_price, discount_pct, score, url, timestamp, source
     - source = "on_demand_search" (differentiate from bulk scrape)
   - Queue append to Google Sheets
3. **[GoogleSheetsService]** appends rows to spreadsheet
4. Handle Google Sheets quota limits (batch append, retry with backoff)
5. Log success/failure to system

**Preconditions for Execution:**
- sheets_logging_enabled = true (in system_config)
- Google Sheets API token is valid
- Spreadsheet ID is configured

**Alternative Flows:**
- A1: Google Sheets API quota exceeded
  - Queue for retry (up to 3 attempts)
  - Log error
  - Continue with other operations (sheets is non-blocking)
- A2: Google Sheets authentication fails
  - Log error
  - Continue (non-blocking)
  - Alert administrators

**Postconditions:**
- Opportunities logged to spreadsheet
- Sheets tab may be separate for on-demand results (optional)

**Dependencies:**
- GoogleSheetsService (existing)
- GoogleSheetsClient (existing)

**Non-Functional Requirements:**
- Sheets logging is asynchronous (non-blocking)
- Append completes within 10 seconds

---

### UC9: Send Telegram Alert

**Goal:** Send real-time notifications for high-scoring opportunities

**Actors:** System, TelegramBot

**Preconditions:**
- Opportunities with score > 75 exist
- Telegram Bot API is configured
- User has Telegram chat_id registered

**Main Flow:**
1. System receives opportunities with score > 75
2. For each qualifying opportunity:
   - Format Telegram message:
     - Example: "🚗 **Honda Civic 2020** | Listing: R$45k | FIPE: R$60k | -25% discount | Score: 82 | [Link](url)"
   - Queue alert (TelegramBotService message queue)
3. **[Scheduler]** processes message queue periodically:
   - Respects Telegram rate limit (30 msg/second)
   - Sends message to chat_id
   - Marks alert as "sent" in database
   - Logs to alert_history table
4. Handle failures:
   - If send fails: Mark alert as "failed", log error_message
   - Retry with exponential backoff (up to 3 attempts)

**Preconditions for Execution:**
- telegram_alert_threshold = 75 (configurable in system_config)
- User has subscribed to Telegram alerts
- User has registered chat_id

**Alternative Flows:**
- A1: User has not enabled Telegram
  - Skip alerts
- A2: Telegram API rate limit hit
  - Queue for retry (scheduler retries periodically)
- A3: Telegram API returns error
  - Log error
  - Mark alert as "failed"
  - Continue with next alert

**Postconditions:**
- Alert queued (or sent immediately if not rate-limited)
- Alert record created in database

**Dependencies:**
- TelegramBotService (existing)
- TelegramAPIClient (existing)
- AlertRepository (existing)

**Non-Functional Requirements:**
- Alert queueing completes within 1 second
- Message format includes clickable link
- Rate limiting enforced (30 msg/second)

---

### UC10: Sync to CarWizard

**Goal:** Send qualified opportunities to CarWizard system

**Actors:** System, CarWizard

**Preconditions:**
- Opportunities with score > 80 exist
- CarWizard API is available
- CarWizard integration is enabled

**Main Flow:**
1. System receives opportunities with score > 80
2. For each qualifying opportunity:
   - Prepare CarWizard payload:
     - Vehicle: brand, model, year, version
     - Listing: price, mileage, condition, url, marketplace
     - Opportunity: fipe_price, discount_pct, score
     - Source: "on_demand_search"
   - Send to CarWizard API
3. CarWizard returns opportunity_id (cw_id)
4. System stores cw_id in opportunities table (carwizard_id field)
5. System logs sync_status to opportunity_logs table
6. **[Scheduler]** periodically queries CarWizard for status updates:
   - Get updated opportunity status (e.g., "inspection_scheduled")
   - Update opportunity table with latest status
   - Log updates to opportunity_logs

**Preconditions for Execution:**
- carwizard_sync_threshold = 80 (configurable in system_config)
- CarWizard API is configured and authenticated

**Alternative Flows:**
- A1: CarWizard API returns error
  - Log error
  - Mark for manual review
  - Retry up to 3 times
- A2: CarWizard API timeout
  - Queue for retry
  - Continue with other operations (non-blocking)

**Postconditions:**
- Opportunity sent to CarWizard
- cw_id stored in database
- Bidirectional sync initiated

**Dependencies:**
- CarWizardService (existing)
- CarWizardAPIClient (existing)
- CarWizardSyncOrchestrator (existing)

**Non-Functional Requirements:**
- CarWizard sync is asynchronous (non-blocking)
- API call completes within 5 seconds

---

### UC14: Handle Errors

**Goal:** Gracefully handle failures throughout the search pipeline

**Actors:** System

**Preconditions:**
- Error occurred in any step (UC1-UC10)

**Main Flow:**
1. System catches exception
2. System logs error with full context:
   - Timestamp, operation (UC_X), error message, stack trace
   - User search parameters (if available)
3. System determines impact:
   - **Critical errors** (stop search):
     - FIPE price not found → Stop, display error to user
     - OLX scraping completely failed → Stop, display error
   - **Non-critical errors** (continue):
     - Google Sheets append failed → Log, continue with results
     - Telegram alert failed → Log, continue with other alerts
4. System notifies user:
   - Display error message on search results page
   - Offer retry option if appropriate
   - Log error reference for support investigation
5. System proceeds or stops based on error severity

**Error Handling Examples:**

| Error | Severity | Action |
|-------|----------|--------|
| FIPE price not found | Critical | Stop, display "Vehicle not found" |
| FIPE API timeout | Critical | Stop, offer retry |
| OLX scraping failed | Critical | Stop, display "Cannot reach OLX" |
| OLX parse error | Critical | Stop, log, notify admins |
| All listings are duplicates | Non-critical | Display "No new results" |
| Sheets API quota exceeded | Non-critical | Log, retry later |
| Telegram rate limit | Non-critical | Queue for retry |
| CarWizard sync failed | Non-critical | Log, retry later |
| Database save failed | Critical | Stop, display error, rollback |

**Postconditions:**
- Error is logged and tracked
- User is informed (critical errors)
- System state is consistent
- Operations continue or stop based on severity

**Non-Functional Requirements:**
- Error handling completes within 500ms
- All errors logged with full context
- User-facing messages are clear and actionable

---

## Integration with Existing System

### Reused Components

1. **FIPEClientService** (existing)
   - No changes needed
   - Used by UC2 (Lookup FIPE Price)

2. **OLXScraperClient** (existing)
   - Minor modification: Add search query parameter
   - Instead of browsing categories, send search query to OLX
   - Used by UC3 (Scrape OLX Listings)

3. **ListingValidator** (existing)
   - No changes needed
   - Used by UC3 (validation)

4. **PriceComparisonService** (existing)
   - No changes needed
   - Used by UC5 (Compare Prices)

5. **ScoringOrchestrator** (existing)
   - No changes needed
   - Used by UC6 (Calculate Score)

6. **GoogleSheetsService** (existing)
   - No changes needed
   - Used by UC8 (Log to Sheets)

7. **TelegramBotService** (existing)
   - No changes needed
   - Used by UC9 (Send Alerts)

8. **CarWizardService** (existing)
   - No changes needed
   - Used by UC10 (Sync to CarWizard)

### New Components Required

1. **OnDemandSearchOrchestrator** (new)
   - Orchestrates the full search pipeline (UC_MAIN)
   - Composes: UC1, UC2, UC3, UC4, UC5, UC6, UC7, UC8, UC9, UC10, UC14
   - Entry point for search requests
   - Handles error propagation and recovery

2. **SearchQueryValidator** (new)
   - Validates brand, model, year input
   - Normalizes brand/model names (VW -> Volkswagen, etc.)
   - Used by UC1 (Parse Search Query)

3. **SearchQueryParser** (new)
   - Formats search query for downstream systems
   - Handles fuzzy matching preparation
   - Used by UC1 (Parse Search Query)

### New API Endpoint

- **POST /api/search/vehicle**
  - Request body: `{ "brand": string, "model": string, "year": int (optional) }`
  - Response: `{ "status": "processing", "search_id": uuid, "estimated_time": int }`
  - Asynchronous: Returns immediately, search continues in background
  - User can poll for results via search_id

### Database Changes

**No schema changes** — all tables already exist:

- `vehicles` table: Store vehicle metadata
- `listings` table: Store OLX listings (new source = "on_demand_search")
- `opportunities` table: Store opportunities (new source field value)
- `price_cache` table: Leverage existing FIPE cache
- `alerts` table: Track alert delivery
- `alert_history` table: Audit trail

New column consideration:
- Add `source` field to `listings` table to track: "bulk_scrape" vs "on_demand_search"
- Or add `source` to `opportunities` table to mark search origin

### Frontend Changes

**Add to Opportunity Browser:**

1. Search input section (top of page)
   - Brand input field (autocomplete from vehicles table)
   - Model input field (populate based on brand)
   - Year input field (optional, numeric)
   - "Search Now" button
   - "Clear" button to reset form

2. Loading indicator during search
   - Progress bar showing: FIPE lookup → OLX scraping → Processing
   - Estimated time remaining
   - Cancel button to stop search

3. Results display (same table format as bulk scrapes)
   - Include "Source" column (or badge): "On-Demand" vs "Bulk Scrape"
   - All existing columns: score, discount, price, url, etc.

---

## API Design

### Search Request

```
POST /api/search/vehicle
Content-Type: application/json

{
  "brand": "Honda",
  "model": "Civic",
  "year": 2020
}
```

### Search Response (immediate)

```
200 OK
Content-Type: application/json

{
  "status": "processing",
  "search_id": "550e8400-e29b-41d4-a716-446655440000",
  "estimated_time_seconds": 25,
  "created_at": "2025-02-06T10:30:00Z"
}
```

### Results Polling Endpoint (optional)

```
GET /api/search/{search_id}/results

200 OK
{
  "search_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "opportunities_count": 12,
  "results": [
    {
      "id": "opp_id",
      "listing": { ... },
      "fipe_price": 60000,
      "discount_pct": 25,
      "score": 82,
      ...
    }
  ]
}
```

---

## Performance Targets

| Operation | Target | Max |
|-----------|--------|-----|
| Input validation | 500ms | 1s |
| FIPE lookup (cache hit) | 100ms | 500ms |
| FIPE lookup (API call) | 2-4 seconds | 5s |
| OLX scraping | 15-20 seconds | 30s |
| Deduplication | 1-2 seconds | 5s |
| Price comparison | 500ms | 2s |
| Score calculation | 1-2 seconds | 5s |
| Database save | 2-3 seconds | 5s |
| **Total search-to-display** | **20-30 seconds** | **40s** |

---

## Error Scenarios

| Scenario | Handling |
|----------|----------|
| FIPE price not found | Log, stop, display "Vehicle not found" |
| FIPE API timeout | Log, stop, offer retry |
| OLX inaccessible | Log, stop, display "Cannot reach OLX" |
| No listings found | Log, stop, display "No results" |
| All listings are duplicates | Log, stop, display "All results already in DB" |
| Sheets API quota | Log, queue retry, continue |
| Telegram rate limit | Queue retry, continue |
| CarWizard API error | Log, queue retry, continue |
| Database constraint violation | Log, skip, continue |

---

## Security & Compliance

1. **Input validation:** All user inputs validated (brand, model, year)
2. **Authentication:** API endpoint requires JWT token
3. **Rate limiting:** Max 5 concurrent searches per user
4. **API keys:** FIPE, Google Sheets, Telegram, CarWizard tokens in env vars
5. **Logging:** No sensitive data logged (prices OK, tokens NOT OK)
6. **Error messages:** User-facing messages don't leak technical details

---

## Testing Strategy

### Unit Tests
- SearchQueryValidator (all validation scenarios)
- SearchQueryParser (normalization)
- Price comparison logic
- Score calculation

### Integration Tests
- Full pipeline: Query → FIPE → Scrape → Score → Save
- Error handling (FIPE failure, scraping failure, etc.)
- Database deduplication
- Downstream actions (Sheets, Telegram, CarWizard)

### E2E Tests
- User search flow (frontend)
- API endpoint validation
- Concurrent searches
- Results appear in dashboard

### Performance Tests
- Scraping time <30 seconds
- Total pipeline <40 seconds
- Database transactions (<5s)

---

## Future Enhancements

1. **Multi-marketplace:** Extend to WebMotors, Mercado Livre
2. **Search history:** Save user searches for reuse
3. **Smart alerts:** ML-based price anomaly detection
4. **Scheduled searches:** User can set up recurring searches
5. **Telegram bot search:** Search directly from Telegram bot
6. **Export results:** CSV/Excel export of search results
7. **Comparison:** Side-by-side comparison of results
