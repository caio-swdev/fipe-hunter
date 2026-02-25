Feature: CarWizard Integration
  As an external system connector
  I want to send high-scoring opportunities to CarWizard
  So that vehicle history and additional analysis are available

  Scenario: Send qualified opportunity to CarWizard
    Given an opportunity with score >= 80
    And CarWizard API is configured
    When the opportunity is qualified
    Then the system should:
      - Prepare payload with vehicle details
      - Send to CarWizard API
      - Store CarWizard ID in opportunity record
      - Complete within 30 seconds

  Scenario: Include vehicle details in payload
    Given opportunity:
      | brand        | Volkswagen      |
      | model        | Gol             |
      | year         | 2015            |
      | mileage      | 80000           |
      | listing_price| R$ 20.000,00    |
      | fipe_price   | R$ 25.000,00    |
      | discount     | 20%             |
      | score        | 82              |
    When sending to CarWizard
    Then payload should include all vehicle details
    And CarWizard can identify vehicle
    And CarWizard can perform history lookup

  Scenario: Store CarWizard reference ID
    Given CarWizard API returns ID "CW123456"
    When response is received
    Then the system should:
      - Store CW ID in opportunities table (carwizard_id column)
      - Link opportunities to CarWizard system
      - Enable status updates from CarWizard

  Scenario: Handle CarWizard API timeout
    Given CarWizard API slow to respond
    When sending opportunity
    Then the system should:
      - Wait up to 20 seconds for response
      - If timeout: retry once
      - If still fails: log error, mark for manual review
      - Do not crash pipeline

  Scenario: Continue if CarWizard fails
    Given CarWizard API returns 500 error
    When sending opportunity
    Then the system should:
      - Log the error
      - Queue for retry
      - NOT crash pipeline
      - Continue processing other opportunities

  Scenario: Support bidirectional sync
    Given opportunity sent to CarWizard with CW ID
    When CarWizard sends status update
    Then the system should:
      - Receive status update (webhook or polling)
      - Match by CW ID
      - Update opportunity record
      - Log status change

  Scenario: Score threshold for CarWizard
    Given opportunities with scores: 75, 80, 85, 90
    When evaluating CarWizard eligibility
    Then only send opportunities with score >= 80:
      - Score 75: NOT sent
      - Score 80: sent
      - Score 85: sent
      - Score 90: sent

  Scenario: Handle vehicle not recognized by CarWizard
    Given vehicle "Unknown Brand XYZ"
    When sending to CarWizard
    Then CarWizard may return error
    And system should:
      - Log the error
      - Mark for manual review
      - Not crash
      - Continue processing

  Scenario: Authenticate with CarWizard API
    Given CarWizard API key is configured
    When sending opportunity
    Then request should:
      - Include authentication headers
      - Use API key from environment
      - Validate connection before operation

  Scenario: Batch send opportunities to CarWizard
    Given 5 opportunities with score >= 80
    When all qualified at same time
    Then system should:
      - Send each separately (or batch if API supports)
      - Track each response
      - Handle partial failures
      - Complete within 30 seconds total

  Scenario: Update opportunity with vehicle history
    Given CarWizard returns vehicle history data
    When status update received
    Then system should:
      - Store history reference
      - Update opportunity record
      - Make history available for review
      - Log update event

  Scenario: Handle CarWizard API version changes
    Given CarWizard API endpoint changes
    When response structure doesn't match
    Then system should:
      - Detect parsing error
      - Log detailed error
      - Fall back gracefully
      - Alert administrators
      - Require manual update to parser

  Scenario: Retry failed CarWizard sends
    Given send to CarWizard failed (connection timeout)
    When retry occurs
    Then system should:
      - Retry up to 3 times
      - Use exponential backoff (30s, 60s, 120s)
      - Log each attempt
      - If all fail: mark for manual review
