# Use Case Specification: CarWizard Integration

## 1. Use Case Name
CarWizard Integration (Send & Sync Opportunities)

## 2. Brief Description
Send high-scoring opportunities (score >= 80) to external CarWizard system for vehicle history lookup and additional analysis. Receive and process status updates from CarWizard.

## 3. Actors
- **Opportunity Scorer:** Sends scored opportunities
- **CarWizard API:** External vehicle analysis system
- **CarWizard System:** Receives opportunities and provides updates

## 4. Preconditions
- CarWizard API URL and credentials are configured
- Opportunity has score >= 80
- Network connectivity to CarWizard available
- CarWizard API authentication working

## 5. Basic Flow of Events

1. Receive opportunity: Listing + Score >= 80
2. Prepare payload:
   - Vehicle: brand, model, year, version
   - Market data: listing_price, fipe_price, discount_pct, score
   - Marketplace: source (OLX, WebMotors)
   - Timestamp: when opportunity was found
3. Authenticate with CarWizard API (using API key from environment)
4. Send POST request to CarWizard:
   - Endpoint: /api/opportunities (or equivalent)
   - Body: serialized payload
   - Timeout: 20 seconds
5. Handle response:
   - If success (HTTP 200): extract CarWizard ID
   - If failure: retry with backoff or mark for review
6. Store CarWizard ID in opportunity record:
   - UPDATE opportunities SET carwizard_id = "CW123456"
   - This links opportunity to CarWizard system for future updates
7. Return result to caller

## 6. Alternative Flows

**6a. Request Timeout**
- If request doesn't complete in 20 seconds:
  - Abort request
  - Retry once with fresh connection
  - If still times out: log error, mark for manual review
  - Do not crash pipeline

**6b. API Error (HTTP 5xx)**
- If CarWizard returns 500 or similar:
  - Implement exponential backoff (30s, 60s, 120s)
  - Retry up to 3 times
  - If all fail: queue for manual review
  - Log detailed error

**6c. Vehicle Not Recognized**
- If CarWizard can't identify vehicle:
  - API returns error (400, 422, etc.)
  - Log error with vehicle details
  - Mark opportunity for manual review
  - Do not retry

**6d. Receive Status Update from CarWizard**
- CarWizard sends webhook or we poll for updates
- Webhook includes CarWizard ID and status
- Match opportunity by carwizard_id
- Update opportunity record with new status
- Log sync event

## 7. Postconditions
- Opportunity linked to CarWizard system (carwizard_id stored)
- Opportunity status available for sync updates
- Vehicle history accessible through CarWizard

## 8. Special Requirements

### Payload Format
- JSON with vehicle and opportunity details
- Fields: brand, model, year, mileage, listing_price, fipe_price, discount_pct, score, url, timestamp
- Must be compatible with CarWizard API schema (TBD: pending client clarification)

### Performance
- Send request: < 20 seconds timeout
- Batch send: 5+ opportunities < 30 seconds total
- Retry: transparent to pipeline

### Score Threshold
- Only send opportunities with score >= 80 (configurable)
- Lower scores: do not send to CarWizard

### Error Handling
- Transient errors: retry with exponential backoff
- Persistent errors: mark for manual review, log details
- API changes: log and alert administrators
- Never crash pipeline

### Logging
- Log all sends with opportunity_id and CarWizard ID
- Log failures with error codes
- Log status updates and syncs
- Track API issues for troubleshooting

### Future Enhancements
- Bidirectional sync: receive vehicle history from CarWizard
- Status polling: periodically check opportunity status in CarWizard
- Callback webhooks: receive real-time updates from CarWizard
- Inspection scheduling: allow CarWizard to schedule inspections
