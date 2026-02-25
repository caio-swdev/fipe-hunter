# Use Case Specification: Telegram Alerts

## 1. Use Case Name
Telegram Alerts (Send Real-Time Opportunity Notifications)

## 2. Brief Description
Send real-time notifications via Telegram Bot for high-scoring opportunities (score >= 75), including vehicle summary, discount percentage, score, and direct marketplace link.

## 3. Actors
- **Opportunity Scorer:** Sends scored opportunities
- **Telegram Bot API:** External service for sending messages
- **Telegram Users:** Receive alerts via subscribed chat IDs

## 4. Preconditions
- Telegram Bot token is configured and valid
- Bot has been started by users (they've sent /start)
- Chat IDs of subscribers are available
- Opportunity has score >= 75

## 5. Basic Flow of Events

1. Receive opportunity: Listing + Score >= 75
2. Format alert message:
   - Vehicle: "Volkswagen Gol 2015"
   - Discount: "Desconto: 25%"
   - Score: "Score: 82/100"
   - Link: Direct URL to listing
3. Queue alert to message queue (with rate limiting in mind)
4. Process message queue (max 30 messages/second):
   - Dequeue message
   - Send to Telegram API
   - Wait for response
   - Record result
   - Continue to next message
5. Handle response:
   - If success (HTTP 200): record as sent
   - If failure: retry with backoff
   - If bot blocked (403): mark chat_id inactive
6. Record alert history in database

## 6. Alternative Flows

**6a. Rate Limiting**
- If 100+ alerts queued:
  - Send at max 30 messages/second
  - Queue handles backpressure
  - Users see alerts with slight delay (< 10 seconds total)

**6b. Message Send Failure**
- If connection timeout or 5xx error:
  - Retry up to 3 times
  - Exponential backoff: 10s, 20s, 40s
  - If all retries fail: mark for manual review

**6c. Bot Blocked by User (HTTP 403)**
- User blocked bot in Telegram
- System receives 403 Forbidden
- Mark chat_id as inactive
- Alert administrator (user may need to re-enable bot)
- Do not retry

**6d. Subscription Filtering (Future)**
- Check user preferences before sending
- Only send if user interested in brand/model/region
- Skip send if filtered out

## 7. Postconditions
- Alert message delivered to Telegram users
- Alert history recorded
- Message status logged (sent, failed, retried)

## 8. Special Requirements

### Message Format
- Concise and readable (Telegram message limits: 4096 chars)
- Include: vehicle summary, discount %, score, clickable link
- Professional tone
- Portuguese language (for Brazilian users)

### Performance
- Queue to send: < 1 second
- Deliver to Telegram: 1-3 seconds per message
- Process queue: 30 messages/second maximum

### Rate Limiting
- Telegram limit: ~30 messages/second per bot
- MVP: single chat_id, no internal rate limit needed
- Future: multiple chat_ids, implement queue processing

### Error Handling
- Transient errors: retry with exponential backoff
- Bot blocked (403): mark inactive, don't retry
- API errors: log and queue for retry
- Never crash pipeline

### Logging
- Log all sent messages with timestamp
- Log failures with error codes
- Track rate limit events
- Monitor failed sends for manual review

### Deduplication
- Check if alert already sent for this opportunity
- Use opportunity_id as key
- Don't send duplicate alerts
- Log deduplication events
