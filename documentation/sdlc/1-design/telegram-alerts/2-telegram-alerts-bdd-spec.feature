Feature: Telegram Alerts
  As a notification system
  I want to send real-time alerts for high-scoring opportunities
  So that users are immediately notified of good deals

  Scenario: Send alert for qualified opportunity
    Given an opportunity with score >= 75
    And Telegram bot is configured
    When the opportunity is scored
    Then the system should:
      - Format alert message with vehicle summary
      - Include discount percentage
      - Include score
      - Include direct marketplace link
      - Send via Telegram API
      - Complete within 30 seconds

  Scenario: Format alert message for readability
    Given opportunity:
      | brand     | Volkswagen      |
      | model     | Gol             |
      | year      | 2015            |
      | discount  | 25%             |
      | score     | 82              |
      | url       | https://olx/... |
    When formatting alert
    Then message should include:
      - "Volkswagen Gol 2015"
      - "Desconto: 25%"
      - "Score: 82/100"
      - "https://olx/..." (clickable link)
      - Professional formatting

  Scenario: Handle different score thresholds
    Given opportunities with scores: 60, 74, 75, 85, 95
    When evaluating alert eligibility
    Then alerts should be sent only for:
      - Score 75: eligible (>= threshold)
      - Score 85: eligible
      - Score 95: eligible
    And NO alerts for scores < 75

  Scenario: Validate Telegram bot token
    Given Telegram bot configured with token "1234567890:ABCDefg..."
    When system starts
    Then it should:
      - Test bot token with /getMe API call
      - Verify bot is active
      - Log bot identity
      - Fail startup if bot invalid

  Scenario: Queue alerts for rate limiting
    Given 100 opportunities qualified in rapid sequence
    When sending alerts
    Then the system should:
      - Queue all 100 alerts
      - Send at max 30 messages/second (Telegram limit)
      - Respect rate limit gracefully
      - Complete all sends within 4 seconds

  Scenario: Retry failed message sends
    Given Telegram API returns error (connection timeout)
    When sending alert
    Then the system should:
      - Detect failure
      - Retry up to 3 times
      - Use exponential backoff (10s, 20s, 40s)
      - Log all retry attempts
      - If final fail: alert admin

  Scenario: Continue on message send failure
    Given Telegram API is completely unavailable
    When attempting to send alert
    Then the system should:
      - Attempt to send (fail)
      - Log detailed error
      - NOT crash pipeline
      - Continue processing other opportunities
      - Queue failed message for manual retry

  Scenario: Support user subscriptions/filters
    Given users can subscribe to alerts
    When opportunity is qualified
    Then system should (future feature):
      - Check user subscription preferences
      - Send only if user interested in brand/model/region
      - Support unsubscribe via Telegram reply
      - Allow user to set score threshold

  Scenario: Record alert delivery history
    Given alert sent to Telegram
    When alert completes
    Then system should:
      - Record message_id from Telegram API
      - Record status: sent
      - Record timestamp
      - Log for audit trail

  Scenario: Handle Telegram user not available
    Given chat_id for user who hasn't started bot
    When attempting to send alert
    Then Telegram API returns error (403 Forbidden)
    And system should:
      - Log the error
      - Mark chat_id as inactive
      - Alert administrator of inactive user
      - Continue processing

  Scenario: Deduplicate alerts for same opportunity
    Given an opportunity that's been processed twice
    When sending alerts
    Then the system should:
      - Not send duplicate alerts
      - Check if already alerted
      - Send only if first time
      - Log deduplication

  Scenario: Format prices in BRL
    Given opportunity with prices in BRL
    When formatting alert
    Then prices should display as:
      - "R$ 20.000,00" (formatted)
      - OR "20000.00" (numeric)
      - Consistent across all alerts
      - Human-readable

  Scenario: Time-zone aware timestamps
    Given alert created at 2024-01-15 10:30:00 (UTC)
    When formatting for user in Rio (UTC-3)
    Then alert should show:
      - Time in user's local timezone
      - OR UTC with timezone indicator
      - Clear to user when opportunity found

  Scenario: Support multiple chat IDs
    Given users can receive alerts on multiple chats
    When opportunity is qualified
    Then system should:
      - Send alert to all subscribed chat IDs
      - Handle partial failures (some succeed, some fail)
      - Log results per chat_id
      - Retry failed sends with backoff
