# Functional Specification: FIPE Hunter

## Overview

This document outlines the functional requirements for FIPE Hunter, an automated vehicle opportunity finder that identifies underpriced vehicles in Brazilian marketplaces by comparing listing prices against official FIPE reference valuations.

## Functional Requirements

### Web Scraping Module

- [x] System can scrape vehicle listings from OLX Rio marketplace
- [x] System can scrape vehicle listings from WebMotors marketplace
- [x] System extracts brand, model, year, price, mileage, condition from listings
- [x] System rotates user-agents to avoid blocking
- [x] System implements request delays (1-3 seconds) between requests
- [x] System handles HTTP errors gracefully with retry logic
- [x] System gracefully handles site structure changes
- [ ] System supports additional marketplace sources (Mercado Livre, Compre & Venda)

### FIPE Lookup Module

- [x] System queries FIPE public API for reference prices
- [x] System accepts vehicle brand/model/year as input
- [x] System performs fuzzy string matching for brand variations (e.g., "VW" → "Volkswagen")
- [x] System handles model name variations and abbreviations
- [x] System implements exponential backoff for API rate limiting
- [x] System caches FIPE results for 24 hours
- [x] System logs failed lookups for manual review
- [ ] System integrates with CarWizard for enhanced pricing data

### Price Comparison Module

- [x] System compares listing price vs FIPE reference price
- [x] System calculates discount percentage: (FIPE - listing) / FIPE * 100
- [x] System identifies opportunities with 20-50% discount threshold
- [x] System filters out negative discounts (overpriced vehicles)
- [x] System tracks raw price delta (in R$)
- [x] System supports configurable discount thresholds per marketplace
- [x] System validates price data integrity

### Opportunity Scoring

- [x] System ranks opportunities on 0-100 scale
- [x] System considers discount percentage (weight: 40%)
- [x] System considers vehicle mileage/condition (weight: 30%)
- [x] System considers market demand factors (weight: 20%)
- [x] System considers listing recency (weight: 10%)
- [x] System sorts results by score (descending)
- [x] System allows score filtering (e.g., show only opportunities > 75 score)
- [ ] System supports custom scoring algorithms per user

### Google Sheets Integration

- [x] System authenticates with Google Sheets API (OAuth 2.0)
- [x] System creates/appends to spreadsheet with opportunity data
- [x] System creates separate sheets per marketplace source
- [x] System includes columns: brand, model, year, listing_price, fipe_price, discount_pct, score, url, timestamp
- [x] System supports batch appends (multiple rows per API call)
- [x] System handles API quota limits gracefully
- [x] System logs sync errors for retry
- [ ] System supports custom column configurations

### Telegram Alerts

- [x] System sends real-time notifications for high-scoring opportunities (score > 75)
- [x] System formats alerts: vehicle summary + discount % + score
- [x] System includes direct marketplace link in alert
- [x] System validates Telegram Bot token before operation
- [x] System implements message queue to respect rate limits (30 msg/second)
- [x] System retries failed messages with exponential backoff
- [x] System logs all sent alerts for audit trail
- [x] System supports user subscription filters by vehicle type
- [ ] System supports reply-based filtering/subscriptions

### CarWizard Integration

- [x] System sends qualified opportunities (score > 80) to CarWizard
- [x] System includes all vehicle metadata in CarWizard payload
- [x] System receives opportunity status updates from CarWizard
- [x] System stores CarWizard reference ID for opportunity tracking
- [ ] System supports vehicle inspection scheduling
- [ ] System integrates CarWizard pricing data into scoring

### Frontend Dashboard Module

- [x] Dashboard displays opportunity overview with key metrics (total found, new today, high-score count, top score)
- [x] Dashboard shows best deals widget with top 5 opportunities sorted by score
- [x] Dashboard displays price trends chart showing average discount evolution over 30 days
- [x] Opportunity browser displays paginated table with all opportunities (25 rows per page)
- [x] Opportunity browser supports multi-column sorting (score, discount, price, date, etc.)
- [x] Users can search opportunities by text (brand, model, description)
- [x] Users can filter opportunities by score range (e.g., 75-100)
- [x] Users can filter opportunities by marketplace (OLX, WebMotors, etc.)
- [x] Users can filter opportunities by discount range (e.g., 20-40%)
- [x] Detail panel shows full opportunity information (vehicle specs, pricing, score breakdown, status)
- [x] Users can mark opportunities as purchased or archived
- [x] Users can export filtered opportunities as CSV/Excel/PDF
- [x] Analytics page displays discount distribution histogram
- [x] Analytics page displays market trends chart (discount %, score, listings per day)
- [x] Analytics page displays top brands analysis (by opportunities, avg score, avg discount)
- [x] Analytics page displays marketplace performance comparison
- [x] Settings page allows configuring scraping schedule (frequency, enabled sources, time)
- [x] Settings page allows configuring alert thresholds (Telegram, CarWizard)
- [x] Settings page allows toggling marketplace sources on/off
- [x] Settings page allows configuring discount filter ranges
- [x] Monitoring page displays system metrics (last scrape time, next scrape, success rate, queue status)
- [x] Monitoring page shows detailed scrape log with listings found, saved, errors
- [x] Monitoring page displays API health status for each external service
- [x] Monitoring page displays message queue status with retry functionality
- [x] Historical view shows archived/purchased opportunities
- [x] Historical view displays price evolution chart for specific vehicles
- [x] Users can export all historical data
- [x] Dashboard is responsive and works on mobile devices (< 768px)
- [x] Dashboard loads initial layout within 2 seconds
- [x] Dashboard loads critical data within 3 seconds
- [x] Dashboard handles missing data gracefully with empty states
- [x] Dashboard displays error messages for service unavailability
- [ ] Dashboard supports real-time data updates via WebSocket
- [ ] Dashboard supports saved filter presets
- [ ] Dashboard supports custom user alerts and notifications

### On-Demand Vehicle Search

- [x] User can search for specific vehicle (brand + model + optional year)
- [x] Search input displayed in Opportunity Browser page
- [x] System validates search inputs (required fields, valid year range)
- [x] System normalizes brand/model names (VW -> Volkswagen, MB -> Mercedes-Benz)
- [x] System queries FIPE API for reference price (with 24-hour cache)
- [x] System scrapes OLX listings matching search query (not browsing categories)
- [x] System extracts listing data: brand, model, year, price, mileage, condition, url
- [x] System deduplicates results against existing bulk-scraped listings by URL
- [x] System handles duplicate updates (re-surface if previously archived)
- [x] System compares listing prices against FIPE price
- [x] System calculates discount percentage (20-50% threshold)
- [x] System flags suspicious discounts (>50%) for manual review
- [x] System calculates opportunity scores (0-100 scale, identical to bulk scraping)
- [x] System sorts results by score descending
- [x] System saves results to opportunities table with source="on_demand_search"
- [x] System displays results in same opportunity table format as bulk scrapes
- [x] System shows FIPE price alongside each listing for instant comparison
- [x] System returns results within 10-40 seconds (SLA: 40 seconds max)
- [x] System displays loading indicator with progress (FIPE → OLX → Processing)
- [x] User can cancel search in progress
- [x] System triggers downstream actions for high-scoring results:
  - [x] Log all results to Google Sheets with source="on_demand_search"
  - [x] Send Telegram alerts for opportunities with score > 75
  - [x] Sync to CarWizard for opportunities with score > 80
- [x] System handles FIPE lookup failure gracefully (log error, display message)
- [x] System handles OLX scraping failure gracefully (log error, display message)
- [x] System handles no results scenario (display message, don't create opportunities)
- [x] System supports concurrent searches (no blocking between users)
- [x] System respects rate limiting on external APIs (FIPE, OLX, Telegram)
- [x] System logs all search attempts with parameters and results

## Business Rules

- All listings must be validated against FIPE API before scoring
- Opportunities with 20% discount are minimum threshold
- Opportunities with > 50% discount are flagged for manual review (potential fraud)
- FIPE prices are cached for 24 hours to reduce API calls
- Telegram alerts only sent for opportunities scoring > 75/100
- CarWizard sync only for opportunities scoring > 80/100
- Google Sheets updates occur within 1 minute of opportunity discovery
- Duplicate listings (same vehicle, same marketplace) are deduplicated by URL

## Validation Rules

**Listing Data:**
- Brand: required, non-empty string
- Model: required, non-empty string
- Year: required, integer between 1950 and current year
- Price: required, positive number
- Mileage: optional, non-negative integer
- Condition: required, one of [excellent, good, fair, poor]
- URL: required, valid HTTPS URL

**FIPE Data:**
- Reference price must be positive number
- Lookup must complete within 10 seconds
- API responses must include price and availability status

**Score Calculation:**
- All input values normalized to 0-100 range
- Negative discounts result in score 0
- Final score is weighted average of components
- Score must be between 0-100 inclusive

## Non-Functional Requirements

**Performance:**
- Marketplace scraping: Complete 20-50 listings within 2 minutes
- FIPE lookup: Single price query within 1 second (with caching)
- Score calculation: Process 100 opportunities within 5 seconds
- Telegram alert dispatch: Send within 30 seconds of discovery
- Google Sheets update: Complete append within 10 seconds

**Availability:**
- System handles missing FIPE data (fallback to manual scoring)
- System handles Telegram API outages (queue messages for retry)
- System handles Google Sheets quota limits (implement backoff)
- System continues scraping even if downstream services fail

**Reliability:**
- All database transactions logged
- Failed API calls logged with full context
- Retry logic for transient failures (up to 3 attempts)
- Health check endpoint for monitoring

**Security:**
- API keys stored in environment variables (never in code)
- Google OAuth tokens refreshed automatically
- Telegram bot token validated at startup
- No sensitive data logged (prices OK, credentials NOT OK)
- HTTPS enforced for all external API calls

## API Endpoints

### Scraping Control
- **POST /api/scrape/olx** - Trigger OLX scrape manually
- **POST /api/scrape/webmotors** - Trigger WebMotors scrape manually
- **GET /api/scrape/status** - Get current scrape status

### On-Demand Search
- **POST /api/search/vehicle** - Search for specific vehicle (brand, model, optional year)
  - Request: `{brand: string, model: string, year?: int}`
  - Response: `{status: "processing", search_id: uuid, estimated_time: int}`
  - Async execution: Returns immediately, search continues in background
- **GET /api/search/{search_id}/results** - Poll for search results by search_id (optional)

### Opportunity Queries
- **GET /api/opportunities** - List all opportunities (paginated)
- **GET /api/opportunities/top** - Get top 10 scoring opportunities
- **GET /api/opportunities/filter** - Filter by score, discount, brand, model, source
- **GET /api/opportunities/{id}** - Get specific opportunity details

### Configuration
- **GET /api/config/scoring** - Get scoring algorithm parameters
- **POST /api/config/scoring** - Update scoring weights
- **GET /api/config/telegram** - Get Telegram chat IDs
- **POST /api/config/telegram** - Register/unregister chat ID

### Health & Status
- **GET /api/health** - System health check
- **GET /api/stats** - System statistics (listings scraped, opportunities found, etc.)

### Dashboard-Specific Requirements

- [x] Dashboard API endpoints return data within 10 second timeout
- [x] Dashboard caches opportunity data (5 minute TTL) to reduce API load
- [x] Dashboard caches metrics (1 hour TTL)
- [x] Dashboard caches analytics data (1 hour TTL)
- [x] Dashboard auto-refreshes metrics every 5 minutes
- [x] Dashboard auto-refreshes monitoring status every 30 seconds
- [x] Dashboard displays loading indicators for async operations
- [x] Dashboard debounces search and filter inputs (300ms)
- [x] Dashboard applies filters on both client and server
- [x] Dashboard pagination uses limit/offset pattern
- [x] Dashboard supports sorting by multiple columns
- [x] Dashboard validates JWT token on session load
- [x] Dashboard redirects to login if session invalid
- [x] Dashboard logs all user actions (filters, exports, settings changes)
- [x] Dashboard implements CSRF protection on POST requests
- [x] Dashboard enforces HTTPS for all communications
- [ ] Dashboard supports real-time updates via WebSocket
- [ ] Dashboard supports saved view presets
- [ ] Dashboard supports user-specific configurations

## Current Limitations

The following features are **NOT YET IMPLEMENTED**:

- Multi-user support with permission management
- Real-time WebSocket updates
- Email notifications and scheduled reports
- Multiple geographic regions
- Advanced filtering (e.g., by seller rating)
- Automatic inspection scheduling
- Mobile app
- Vehicle history integration
- Custom scoring algorithms per user
- Opportunity expiration tracking
- AI-based recommendations
- Team collaboration and opportunity sharing
