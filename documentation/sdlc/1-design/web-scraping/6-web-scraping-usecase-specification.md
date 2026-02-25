# Use Case Specification: Web Scraping

## 1. Use Case Name
Web Scraping

## 2. Brief Description
Automated extraction of vehicle listings from Brazilian online marketplaces (OLX, WebMotors) to gather up-to-date marketplace data for price comparison and opportunity identification.

## 3. Actors
- **Scheduler:** Automated job scheduler that triggers scrapes on a schedule (hourly)
- **Administrator:** Human operator who can manually trigger scrapes or monitor scraping status

## 4. Preconditions
- OLX and WebMotors marketplaces are accessible and available
- Scraper is configured with valid user-agent rotation list
- Request delays (1-3 seconds) are configured
- Database connection is available
- Marketplace HTML structure is known and documented

## 5. Basic Flow of Events

### Primary Flow: Automated Hourly Scrape

1. Scheduler triggers scraping job at configured interval (hourly)
2. System starts scrape_log entry with 'running' status
3. For each marketplace (OLX, WebMotors):
   a. Initialize HTTP session with random user-agent
   b. Request marketplace homepage/search results
   c. Wait 1-3 seconds (random delay)
   d. Parse HTML response
   e. Extract listing elements from page
   f. For each listing element:
      - Parse vehicle details (brand, model, year, price, mileage, condition)
      - Extract seller information if available
      - Extract direct URL to listing
      - Create Listing entity
      - Validate listing data
      - If valid: add to listings batch
      - If invalid: log validation error, skip
   g. Save batch of listings to database
   h. Process next page if more listings available (pagination)
4. Deduplicate listings by URL:
   a. Check each listing URL against database
   b. If URL exists: mark as duplicate, don't save new record
   c. If URL new: save as normal
5. Log scraping completion:
   a. Record total listings found
   b. Record listings successfully saved
   c. Record any errors encountered
   d. Set scrape_log status to 'completed'
6. Trigger downstream use case: Query FIPE API for prices

### Alternative Flows

**5a. Marketplace Service Unavailable (HTTP 5xx)**
- Detect HTTP 5xx response (503, 502, etc.)
- Implement exponential backoff: retry after 60 seconds
- Maximum 3 retry attempts
- If all retries fail:
  - Log error to scrape_logs with 'failed' status
  - Send alert to administrators
  - Abort scrape, do not save partial data
- Resume on next scheduled scrape

**5b. Rate Limiting Detected (HTTP 429)**
- Detect HTTP 429 (Too Many Requests)
- Increase request delay to 5-10 seconds
- Implement exponential backoff: start with 60 second delay
- Double delay with each retry (60s → 120s → 240s)
- Continue scraping once rate limit window expires
- Log rate limit event with timestamp
- Reduce delay gradually over subsequent requests (adaptive backoff)

**5c. Incomplete Listing Data**
- If listing missing optional fields (mileage, seller_rating):
  - Fill with default/empty values
  - Mark in log as having missing field
  - Still save the listing (don't discard)
- If listing missing required fields (brand, model, year, price):
  - Reject the listing entirely
  - Log as validation error
  - Continue processing next listing

**5d. HTML Structure Changed**
- If scraper encounters unrecognized HTML element format:
  - Catch parsing exception
  - Log detailed error with HTML snippet
  - Skip that element (don't crash entire scrape)
  - Continue processing remaining listings
  - Notify administrators of potential maintenance needed
  - Suggest manual review of marketplace structure

**5e. Network Timeout**
- If marketplace connection times out (>10 seconds):
  - Abort current request
  - Log timeout error
  - Retry with exponential backoff (3 max attempts)
  - Wait 30 seconds, then 60 seconds, then 120 seconds
  - If all retries fail, record as failed in scrape_logs
  - Resume on next scheduled scrape

**5f. Manual Trigger (Administrator)**
- Administrator clicks "Scrape Now" button
- Same flow as primary (automated), but:
  - Timestamp reflects manual trigger
  - No waiting for next scheduled interval
  - Results returned synchronously to administrator
  - Option to trigger both or individual marketplace

## 6. Alternative Flows - Deduplication Details

**6a. Deduplication Process**
1. After all listings scraped from marketplace
2. For each listing with URL:
   a. Query listings table: SELECT * FROM listings WHERE url = ?
   b. If found:
      - Set is_duplicate = TRUE
      - Don't create new database record
      - Log deduplication event with URL and count of occurrences
   c. If not found:
      - Save normally to listings table
      - Set is_duplicate = FALSE
3. Generate deduplication summary:
   - Total new unique listings added
   - Total duplicates found and marked
   - URLs that were duplicated

## 7. Postconditions
- All successfully scraped and validated listings are persisted to listings table
- Duplicate listings are marked with is_duplicate = TRUE
- Scrape log entry is created with completion status and statistics
- System is ready to proceed with FIPE price lookup for new listings
- Web scraping data is available for downstream use cases (price comparison, scoring)

## 8. Special Requirements

### Performance
- Complete scrape of OLX (20-50 listings): < 2 minutes
- Complete scrape of WebMotors (20-50 listings): < 2 minutes
- Parse and validate each listing: < 100ms
- Database save of batch (50 listings): < 5 seconds

### Reliability
- Handle 429 rate limits without data loss
- Handle 5xx errors with automatic retry
- Handle partial HTML parsing failures gracefully
- Maximum 3 retries before giving up
- Timeout after 10 seconds per HTTP request

### User Agent Rotation
- Maintain list of 10+ diverse user-agent strings
- Randomly select user-agent for each request
- Support mobile, desktop, and crawler variants
- Rotate within same session to avoid detection

### Request Delays
- Randomize delays between 1-3 seconds
- Increase during rate limiting (5-10 seconds)
- Document delays in scrape logs for troubleshooting
- Allow configuration adjustment without code changes

### Data Validation
- Brand: required, non-empty string, length 2-100
- Model: required, non-empty string, length 2-100
- Year: required, integer 1950 to current year
- Price: required, positive number
- Mileage: optional, non-negative integer
- Condition: required, one of [excellent, good, fair, poor]
- URL: required, valid HTTPS URL, unique in database

### Marketplace-Specific Logic
- OLX Rio: Use search filter for Rio de Janeiro region
- WebMotors: Use location/region filter for Rio de Janeiro
- Parse different HTML structures for each marketplace
- Handle marketplace-specific field names and formats

### Deduplication Strategy
- Primary key: URL (must be unique per listing)
- Check for exact URL matches (case-sensitive)
- Mark duplicates with is_duplicate flag
- Don't delete duplicates (keep for audit trail)
- Future optimization: fuzzy matching for URL variations

## 9. Extension Points

### Future Enhancements
- **Additional Marketplaces:** Extend scraper to Mercado Livre, Compre & Venda
- **Advanced Filtering:** Support filtering by seller rating, vehicle condition, price range
- **Headless Browser:** Replace simple HTTP requests with Selenium/Puppeteer for JavaScript-heavy sites
- **Machine Learning:** Detect anomalous listings (spam, fraud) using ML classifier
- **Vehicle Photo Extraction:** Capture and store vehicle images from listings
- **Geographic Expansion:** Support scraping beyond Rio de Janeiro
- **Real-time Updates:** Event-driven scraping when marketplace has new listings (webhooks, RSS feeds)

### Configuration Options
- Scraping schedule (hourly, daily, custom cron)
- Request delays (min/max seconds)
- User-agent list (configurable)
- Marketplace sources to scrape
- Region/city filter
- Deduplication time window (e.g., don't deduplicate listings older than 7 days)
- Retry policy (max attempts, backoff strategy)

## 10. Error Handling & Logging

### Logging Levels
- **INFO:** Scrape started, listings found, duplicates marked, scrape completed
- **WARN:** Missing optional fields, slow response times, rate limits detected
- **ERROR:** HTTP 5xx errors, validation failures, database save failures
- **DEBUG:** HTML parsing details, user-agent rotation, request/response headers

### Log Destinations
- Application logs: INFO, WARN, ERROR, DEBUG
- Database: scrape_logs table for scrape summaries
- Opportunity_logs table for individual listing events
- Administrator alerts: on failures or anomalies

### Error Recovery
- Transient errors (HTTP 429, timeouts): automatic retry with backoff
- Persistent errors (invalid HTML, db connection): fail scrape, alert admins
- Partial failures (1 invalid listing): log and continue, don't stop entire scrape
- Recovery strategy: automatic retry on next scheduled scrape

## 11. Constraints & Compliance

### Terms of Service
- Respect marketplace robots.txt
- Use reasonable request rates (not aggressive)
- Identify scraper in user-agent string
- Do not scrape private/contact information
- Do not overload marketplace servers

### Technical Constraints
- Single-threaded scraping (no parallel requests to avoid blocking)
- HTTP requests limited to HTTPS only
- Connection timeout: 10 seconds per request
- Response timeout: 30 seconds total per request
- Storage: SQLite local database (no remote database)

### Data Retention
- Keep listing records indefinitely
- Keep scrape_logs for 90 days (then archive)
- Keep alert_history indefinitely (audit trail)
- Implement cleanup jobs for old cache entries (24-hour TTL)
