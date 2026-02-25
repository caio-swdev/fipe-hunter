# Feature List: FIPE Hunter

## MVP Features (Phase 1)

### 1. Web Scraping
   - Extract vehicle listings from OLX Rio marketplace
   - Extract vehicle listings from WebMotors marketplace
   - Support anti-bot measures (user-agent rotation, request delays)
   - Parse listing data: brand, model, year, price, mileage, condition
   - Handle site structure changes gracefully

### 2. FIPE Lookup
   - Integration with FIPE public API (parallelum.com.br)
   - Retrieve reference prices for vehicle brand/model/year combinations
   - Fuzzy matching for brand and model name variations
   - Handle API rate limiting and errors

### 3. Price Comparison
   - Compare listing price vs FIPE reference price
   - Identify discount percentage (actual vs reference)
   - Filter opportunities with 20-50% discount threshold
   - Track price delta for scoring purposes

### 4. Opportunity Scoring
   - Rank opportunities by profit potential
   - Score algorithm: 0-100 scale
   - Consider: discount percentage, mileage, condition, market demand
   - Sort results by score in descending order

### 5. Telegram Alerts

   - Real-time bot notifications for high-scoring opportunities
   - Message format: vehicle summary + discount + score + link
   - Support user subscriptions/filters by vehicle type
   - Queue messages to prevent rate limiting

### 6. CarWizard Integration
   - Send qualified opportunities to CarWizard system
   - Bidirectional data sync (opportunity status updates)
   - Vehicle history lookup via CarWizard
   - Support for vehicle inspection scheduling

### 7. Frontend Dashboard
   - Web-based dashboard with opportunity overview and metrics
   - Opportunity browser with advanced filtering, search, and sorting
   - Analytics section with discount distribution, market trends, brand analysis
   - Settings page for scraping schedule, alert thresholds, and marketplace toggles
   - Monitoring page showing system health, API status, and message queue
   - Historical view with archived opportunities and price evolution charts
   - Responsive design supporting mobile, tablet, and desktop viewports
   - Real-time data refresh with caching and error handling

### 8. On-Demand Vehicle Search
   - User can search for specific vehicles in real-time (brand + model + optional year)
   - Query FIPE reference price with cache lookup
   - Scrape OLX listings matching the search query (not browsing all listings)
   - Compare listing prices against FIPE price and calculate discounts
   - Calculate opportunity scores using existing scoring algorithm
   - Return results immediately (10-30 second processing time)
   - Persist results to database like bulk-scraped opportunities
   - Display results in same opportunity table format as bulk scrapes
   - FIPE price shown alongside each listing for instant arbitrage comparison

## Technical Infrastructure

- FastAPI REST endpoints for:
  - Manual scrape triggers
  - Score filtering queries
  - Status and health checks
  - Dashboard data APIs (opportunities, analytics, monitoring)
- Scheduled background jobs for:
  - Periodic marketplace scraping (hourly/daily)
  - FIPE price updates
  - Telegram alert dispatch
- Database schema for:
  - Scraped listings
  - Opportunities (with scores)
  - Alert history
  - User subscriptions
  - Scrape logs and monitoring data
- Frontend application:
  - Modern React/Vue single-page application
  - REST API client with caching
  - Responsive charts and data visualization
  - Session management and authentication

## Current Limitations

- Scrapers tied to specific marketplace HTML structures (fragile to updates)
- FIPE matching relies on fuzzy string matching (may have false negatives)
- Telegram alerts are one-way (no conversation history)
- CarWizard integration details undefined (pending client clarification)
- Single-region focus (Rio de Janeiro only)
- No WebSocket support for real-time updates (polling-based)
- No email notifications or report scheduling
- No multi-user collaboration or team sharing
- No advanced ML-based recommendations
