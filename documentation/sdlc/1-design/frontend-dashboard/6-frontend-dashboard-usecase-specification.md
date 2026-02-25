# Use Case Specification: Frontend Dashboard

## 1. Use Case Name

Frontend Dashboard

## 2. Brief Description

A comprehensive web-based dashboard that provides users with visualization and analysis of vehicle opportunities identified by the FIPE Hunter backend system. Users can browse filtered opportunity lists, view analytics and market trends, configure system settings, and monitor system health.

## 3. Actors

- **User:** Regular user viewing opportunities and market analytics
- **Administrator:** System administrator configuring scraping schedules, alert thresholds, and monitoring system health
- **System:** FIPE Hunter backend API providing opportunity data, metrics, and status information

## 4. Preconditions

- User is authenticated (browser session valid, JWT token stored)
- FIPE Hunter backend API is operational and accessible
- Frontend application is deployed and accessible via HTTPS
- Backend has opportunity data (from previous scraping/processing)
- User has appropriate permissions (standard user vs admin role)

## 5. Basic Flow of Events

### Primary Flow: View Dashboard Home

1. User navigates to dashboard home page
2. Frontend loads layout shell (header, navigation, sidebar)
3. Frontend renders empty state or loading skeletons for dashboard sections
4. Frontend makes API request to `/api/opportunities/summary` for metrics
5. Backend returns: total_found, new_today, high_score_count, top_score
6. Frontend renders metrics in overview section
7. Frontend makes API request to `/api/opportunities/top` for best deals (top 5)
8. Backend returns list of top 5 opportunities with full details
9. Frontend renders best deals widget with vehicle info, prices, discount, score
10. Frontend makes API request to `/api/opportunities/trends?days=30` for price trends
11. Backend returns daily aggregated discount % data for last 30 days
12. Frontend renders line chart showing price trend evolution
13. All data is displayed with last refresh timestamp
14. Dashboard auto-refreshes metrics every 5 minutes
15. Use case completes successfully

### Primary Flow: Browse Opportunities with Filters

1. User navigates to Opportunity Browser page
2. Frontend loads opportunity table with pagination controls
3. Frontend makes API request to `/api/opportunities?page=1&limit=25&sort=score_desc`
4. Backend returns paginated list with total count and has_more flag
5. Frontend renders table with all opportunities
6. User sets filters (score range, marketplace, discount range)
7. Frontend validates filter values on client
8. Frontend makes API request: `/api/opportunities/filter?score_min=75&score_max=100&marketplaces=olx,webmotors&discount_min=20&discount_max=40&page=1`
9. Backend applies filters and returns filtered results
10. Frontend updates table to show filtered results and updated count
11. User clicks on table row or "View Details" button
12. Frontend opens detail panel/modal with full opportunity information
13. Detail view displays: vehicle specs, listing price, FIPE price, score breakdown, status
14. User can click "Open Listing" to visit original marketplace
15. User can mark opportunity as purchased or archive it
16. Frontend makes API request to update opportunity status
17. Detail panel closes and table is refreshed
18. Use case completes

### Primary Flow: View Analytics

1. User navigates to Analytics page
2. Frontend loads analytics layout with placeholder charts
3. Frontend makes concurrent API requests:
   - `/api/analytics/discount-distribution?days=30`
   - `/api/analytics/market-trends?days=30`
   - `/api/analytics/brands?days=30&limit=10`
   - `/api/analytics/marketplace-comparison?days=30`
4. Backend returns aggregated analytics data for each request
5. Frontend renders histogram for discount distribution
6. Frontend renders multi-line chart for market trends (discount %, score, listings/day)
7. Frontend renders bar chart for top brands (by opportunities, avg score, avg discount)
8. Frontend renders comparison table for marketplace performance
9. Each chart displays statistics: mean, median, min, max where applicable
10. User can interact with charts (hover for details, filter by date range)
11. Charts are responsive and resize on viewport changes
12. User can click "Export" to download chart data as CSV
13. Frontend makes API request to `/api/analytics/export?format=csv`
14. Backend generates CSV file with analytics data
15. Browser downloads file
16. Use case completes

### Primary Flow: Configure Settings

1. Administrator navigates to Settings page
2. Frontend loads settings form with current configuration values
3. Frontend makes API request to `/api/config/all` to fetch current settings
4. Backend returns: scraping_schedule, alert_thresholds, marketplace_sources, discount_filters
5. Frontend populates form fields with current values
6. Administrator modifies scraping schedule (frequency: hourly/daily, enabled sources, time)
7. Administrator modifies alert thresholds (Telegram: score > 75, CarWizard: score > 80)
8. Administrator modifies marketplace toggles (OLX enabled, WebMotors enabled)
9. Administrator modifies discount filters (min: 20%, max: 50%)
10. Administrator clicks "Save changes"
11. Frontend validates all form fields on client
12. Frontend makes API request POST `/api/config/update` with new settings
13. Backend validates settings against constraints
14. Backend persists new settings to database
15. Backend returns success response with updated config
16. Frontend displays success notification "Settings saved successfully"
17. Frontend updates form to show new values
18. New settings take effect on next scheduled scrape
19. Use case completes

### Primary Flow: View Monitoring Dashboard

1. Administrator navigates to Monitoring page
2. Frontend loads monitoring dashboard with metric cards
3. Frontend makes API request to `/api/monitoring/status` for system status
4. Backend returns: last_scrape_time, next_scrape_time, success_rate, api_health, queue_status
5. Frontend renders metric cards with values
6. Frontend displays status indicators (green/yellow/red)
7. Dashboard auto-refreshes metrics every 30 seconds via `/api/monitoring/status`
8. Administrator clicks on "Last scrape" metric to see details
9. Frontend makes API request to `/api/scrape-logs/latest`
10. Backend returns detailed last scrape log: start_time, end_time, listings_found, saved, errors
11. Frontend renders detail panel with scrape statistics
12. Administrator clicks "View full log" link
13. Frontend navigates to detailed scrape log view
14. Administrator views API health section
15. Frontend makes API request to `/api/health/services`
16. Backend performs health checks and returns status for each service
17. Frontend displays status cards for FIPE API, Telegram, Sheets, CarWizard
18. Each service shows: status (healthy/warning/error), response time, last check
19. Administrator clicks on "Retry failed" in message queue section
20. Frontend makes API request POST `/api/alerts/retry-failed`
21. Backend re-queues failed alert messages
22. Frontend displays success notification
23. Use case completes

## 6. Alternative Flows

### 6a. Search Opportunities

1. User is in Opportunity Browser page
2. User enters search term (e.g., "Volkswagen Gol") in search field
3. Frontend makes API request: `/api/opportunities/search?q=volkswagen+gol&page=1`
4. Backend performs full-text search across brand, model, description
5. Backend returns matching opportunities
6. Frontend updates table with search results and highlights matches
7. Frontend displays "Clear search" button
8. Result count updates to show matches found
9. If no results found:
   - Frontend displays "No opportunities found for 'volkswagen gol'"
   - Frontend shows "Try a different search term" suggestion
   - Table remains empty with empty state message

### 6b. Export Opportunities

1. User has filtered the opportunity table
2. User clicks "Export" button
3. Frontend displays export format dialog with options: CSV, Excel, PDF
4. User selects format (e.g., CSV)
5. Frontend makes API request POST `/api/opportunities/export?format=csv`
6. Backend generates file with filtered results
7. Frontend receives file blob
8. Browser triggers download with filename: `opportunities-{timestamp}.csv`
9. User receives file on local machine
10. Notification displays: "Export completed successfully"

### 6c. Responsive Mobile View

1. User accesses dashboard on mobile device (viewport < 768px)
2. Frontend CSS media queries adapt layout:
   - Tables stack vertically or scroll horizontally
   - Sidebar collapses to hamburger menu
   - Charts resize to fit viewport width
   - Buttons increase to minimum 44px touch target
   - Form inputs expand to full width
3. Navigation items move to bottom sheet or hamburger menu
4. Modals/panels display fullscreen on mobile
5. All interactions remain functional
6. Touch gestures supported for navigation and interactions

### 6d. Offline/Cached Data

1. User has accessed dashboard previously
2. Service worker has cached critical static assets and initial data
3. Network connection is lost
4. User accesses dashboard
5. Frontend loads from cache for:
   - Static HTML, CSS, JavaScript
   - Last known opportunity data
   - Last known metrics and charts
6. Frontend displays data with "Offline - showing cached data" indicator
7. Backend API requests fail gracefully
8. Frontend shows "Unable to refresh - offline mode" notice
9. When network returns, frontend automatically refreshes data
10. Offline indicator is hidden

### 6e. Handle API Error (Service Unavailable)

1. User accesses dashboard
2. Backend API is temporarily unavailable (5xx error)
3. Frontend makes API requests that timeout or receive error responses
4. Frontend displays non-blocking error messages:
   - For critical data: "Service temporarily unavailable. Showing cached data."
   - For secondary data: Skip rendering that section
5. Frontend displays last refresh timestamp
6. Frontend shows "Retry" button to attempt reload
7. User clicks "Retry"
8. Frontend makes API requests again
9. If API recovers, data loads and error message clears
10. If API still down, error persists with updated retry timestamp

### 6f. No Data State

1. System has not yet completed any scraping
2. User accesses dashboard
3. Frontend checks if data exists via `/api/opportunities/summary`
4. Backend returns empty results
5. Frontend displays empty state:
   - Friendly message: "No opportunities found yet"
   - Illustration of empty state
   - CTA button: "Scrape Now" to trigger manual scrape
   - Help text: "Start by triggering a scrape to find vehicle opportunities"
6. User clicks "Scrape Now"
7. Frontend makes API request POST `/api/scrape/trigger?marketplaces=olx,webmotors`
8. Backend starts background scraping job
9. Frontend navigates to Monitoring page
10. Frontend auto-refreshes scrape status
11. As scraping completes, opportunities appear on dashboard

### 6g. Admin Creates Custom View

1. Administrator wants to save a filtered view for repeated use
2. Administrator applies filters (score > 80, marketplace = OLX, discount 20-30%)
3. Administrator clicks "Save view"
4. Frontend displays modal with input field: "View name"
5. Administrator enters name: "High-scoring OLX deals"
6. Administrator clicks "Save"
7. Frontend makes API request POST `/api/views/create` with filter configuration
8. Backend creates saved view record
9. Frontend displays success notification
10. Frontend adds view to sidebar under "Saved Views"
11. Future access: Administrator can load view in one click

### 6h. Chart Data Refresh

1. Charts on dashboard display analytics data
2. User has dashboard open for extended period
3. Frontend has scheduled chart refresh every 1 hour
4. Frontend makes API request to refresh analytics data
5. Backend returns updated aggregated data
6. Frontend updates charts with new data
7. Charts animate smooth transitions
8. Timestamp displays: "Updated 5 minutes ago"

## 7. Postconditions

- Dashboard displays current opportunity metrics and data
- User can navigate between dashboard sections
- Filters and searches are applied correctly
- Settings changes are persisted and take effect
- All API requests complete successfully or fail gracefully
- User data is displayed with appropriate privacy/permissions
- Session remains active for subsequent actions

## 8. Special Requirements

### Performance

- Dashboard home page loads initial layout within 2 seconds
- Critical metrics load within 3 seconds
- Table pagination responds within 500ms
- Search returns results within 500ms
- Charts render within 1 second
- Auto-refresh operations don't block UI
- All API calls complete within 10 seconds timeout

### User Experience

- Loading states displayed for async operations
- Error messages non-blocking and dismissible
- Responsive design for mobile (< 768px), tablet, desktop
- Touch-friendly buttons (min 44x44px)
- Keyboard navigation supported
- Focus management for accessibility
- WCAG 2.1 AA compliance for accessibility

### Data Consistency

- Metrics match backend calculated values
- Filters reflect exact backend filtering logic
- Sort order matches backend ordering
- Pagination handles large datasets (10,000+ opportunities)
- Concurrent requests don't cause race conditions

### Caching & Optimization

- Static assets cached (images, CSS, JavaScript)
- API responses cached where appropriate (30min for metrics, 5min for opportunities)
- Service worker caches critical resources
- Images lazy-loaded
- Charts use virtual scrolling for large datasets
- API requests debounced (search, filter changes)

### Security

- HTTPS enforced for all communications
- JWT token validated for API requests
- CSRF tokens included in POST requests
- Input validation on all forms
- No sensitive data exposed in frontend code
- API keys never stored locally
- Session timeout after 30 minutes inactivity

### Analytics & Monitoring

- Page view events tracked (Google Analytics)
- Error events logged for debugging
- Performance metrics captured (Core Web Vitals)
- User interaction tracked (filter usage, export, etc.)
- API error rates monitored
- Backend health status reflected in UI

## 9. Extension Points

### Future Enhancements

- **Real-time Updates:** WebSocket integration for live data updates
- **Saved Filters:** Named filter presets users can apply quickly
- **Custom Alerts:** User-defined threshold notifications
- **Email Reports:** Scheduled opportunity reports emailed to user
- **Mobile App:** Native mobile application mirroring dashboard
- **Advanced Analytics:** Predictive pricing, ML-based recommendations
- **Collaboration:** Share opportunities with team members
- **Bookmarks:** Save favorite opportunities for later review
- **Price Notifications:** Alert user when opportunity drops in price
- **Comparison Tool:** Compare multiple opportunities side-by-side

### Configuration Options

- Theme preferences (dark mode, light mode)
- Preferred currency and number formatting
- Default sort order and filters per view
- Number of rows per page
- Chart type preferences (bar, line, pie)
- Auto-refresh intervals
- Notification preferences
- Timezone settings

## 10. Error Handling & Logging

### Frontend Error Handling

- **HTTP 400:** Display validation error message to user
- **HTTP 401:** Redirect to login, clear session
- **HTTP 403:** Display "Unauthorized" message
- **HTTP 404:** Display "Not found" message
- **HTTP 5xx:** Display "Service unavailable" with retry option
- **Network timeout:** Display "Connection timeout" with retry option
- **JSON parse error:** Display "Error loading data" message
- **Missing required fields:** Highlight form field with error

### Logging

- All errors logged to browser console (dev mode)
- Critical errors sent to error tracking service (e.g., Sentry)
- User actions tracked for debugging (optional)
- Performance metrics captured (timing data)
- API request/response logging in dev mode

## 11. Constraints & Compliance

### Technical Constraints

- Frontend built with modern browser (Chrome 90+, Firefox 88+, Safari 14+)
- Responsive design: mobile (320px), tablet (768px), desktop (1024px+)
- No external analytics tracking without user consent
- Total bundle size < 500KB (gzipped)
- Server-side rendering or pre-rendering for SEO

### Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Mobile: iOS Safari 12+, Chrome Mobile 90+

### Data Retention

- Session data: 30 minutes inactivity timeout
- Cached data: Clear on logout
- Local storage: Used only for non-sensitive settings
- API tokens: Refresh before expiration

### Accessibility

- WCAG 2.1 AA standard
- Color contrast 4.5:1 for text
- Focus indicators on interactive elements
- Alt text for images
- Semantic HTML structure
- Screen reader support
- Keyboard navigation (Tab, Enter, Escape)

## 12. API Endpoints Required

### Opportunity Endpoints

- `GET /api/opportunities/summary` - Overview metrics
- `GET /api/opportunities?page=1&limit=25&sort=score_desc` - Paginated list
- `GET /api/opportunities/top?limit=5` - Top scoring opportunities
- `GET /api/opportunities/filter` - Filtered opportunities with query params
- `GET /api/opportunities/search?q=query` - Full-text search
- `GET /api/opportunities/{id}` - Specific opportunity details
- `GET /api/opportunities/trends?days=30` - Price trends data
- `POST /api/opportunities/{id}/status` - Update opportunity status
- `POST /api/opportunities/export?format=csv` - Export opportunities

### Analytics Endpoints

- `GET /api/analytics/discount-distribution?days=30` - Histogram data
- `GET /api/analytics/market-trends?days=30` - Multi-line chart data
- `GET /api/analytics/brands?days=30&limit=10` - Top brands data
- `GET /api/analytics/marketplace-comparison?days=30` - Marketplace stats
- `GET /api/analytics/export?format=csv` - Export analytics data

### Settings Endpoints

- `GET /api/config/all` - Get all configuration
- `POST /api/config/update` - Update configuration
- `POST /api/scrape/trigger` - Trigger manual scrape

### Monitoring Endpoints

- `GET /api/monitoring/status` - System status metrics
- `GET /api/scrape-logs/latest` - Latest scrape log
- `GET /api/health/services` - Service health status
- `POST /api/alerts/retry-failed` - Retry failed alerts

### Authentication Endpoints

- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh JWT token
- `GET /api/auth/me` - Get current user info

## 13. Data Model (Frontend)

### Opportunity Entity

```
{
  id: UUID,
  vehicle: {
    brand: string,
    model: string,
    year: integer,
    transmission?: string,
    fuel_type?: string
  },
  listing_price: number (R$),
  fipe_price: number (R$),
  discount_pct: number (%),
  discount_amount: number (R$),
  score: integer (0-100),
  marketplace: string (olx|webmotors),
  condition: string (excellent|good|fair|poor),
  mileage?: integer (km),
  url: string,
  status: string (new|contacted|purchased|archived),
  created_at: datetime,
  updated_at: datetime
}
```

### Analytics Data

```
{
  discount_distribution: {
    buckets: [
      { range: "0-10%", count: 10 },
      { range: "10-20%", count: 25 },
      ...
    ]
  },
  market_trends: [
    { date: "2024-01-15", discount_pct: 28.5, score: 72.3, listings: 42 },
    ...
  ],
  brands: [
    { brand: "Volkswagen", opportunities: 42, avg_score: 75.2, avg_discount: 28.5 },
    ...
  ]
}
```

## 14. State Management Strategy

### Global State

- User authentication (logged in, user role, permissions)
- Notifications (success, error, warning messages)
- Loading states (for async operations)
- Theme preferences (dark/light mode)

### Page/Component State

- Current filters applied
- Current sort order
- Pagination state (current page, page size)
- Modal/drawer open states
- Form field values
- Selected opportunities

### Cache Layer

- Opportunity list cache (5 minute TTL)
- Metrics cache (1 hour TTL)
- Analytics cache (1 hour TTL)
- Configuration cache (1 hour TTL)

## 15. Testing Strategy

### Unit Tests

- Component rendering with various props/states
- Form validation logic
- Filter/sort logic
- Data formatting and calculations

### Integration Tests

- API request/response handling
- Filter application and data updates
- Modal opening/closing flows
- Settings save and apply

### E2E Tests

- Complete user journeys (login → filter → export)
- Search and filter workflows
- Settings configuration and persistence
- Error handling and recovery

### Performance Tests

- Page load time < 3 seconds
- Filter response < 500ms
- Chart rendering < 1 second
- Bundle size < 500KB gzipped
