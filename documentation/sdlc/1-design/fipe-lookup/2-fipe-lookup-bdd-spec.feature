Feature: FIPE Lookup
  As a comparison engine
  I want to look up official FIPE reference prices for vehicles
  So that I can identify price discrepancies and opportunities

  Background:
    Given the FIPE public API is available
    And the FIPE API base URL is "https://parallelum.com.br/fipe/api/v1/"
    And the price cache is configured with 24-hour TTL
    And the system has fuzzy matching configured for brand/model variations

  Scenario: Look up vehicle price from FIPE API
    Given a vehicle with:
      | brand       | Volkswagen |
      | model       | Gol        |
      | year        | 2015       |
    When I request the FIPE price
    Then the system should query the FIPE API
    And the response should include a price in BRL
    And the price should be a positive number
    And the system should cache the result for 24 hours

  Scenario: Cache FIPE price to reduce API calls
    Given a previously looked-up vehicle (Volkswagen Gol 2015)
    And the cache entry is still valid (< 24 hours old)
    When I request the FIPE price again
    Then the system should return cached price
    And should NOT call the FIPE API
    And response time should be < 100ms (vs ~1 second API call)

  Scenario: Expire cache after 24 hours
    Given a cached FIPE price that is 24+ hours old
    When I request the price
    Then the system should ignore the stale cache
    And should query the FIPE API for current price
    And update the cache with new price

  Scenario: Handle fuzzy brand name matching
    Given a listing with brand = "VW" (abbreviation)
    When I lookup FIPE price
    Then the system should normalize "VW" to "Volkswagen"
    And query FIPE with correct brand name
    And return the price for Volkswagen

  Scenario: Handle fuzzy model name matching
    Given a listing with model = "Gol 1.0" (includes engine size)
    When I lookup FIPE price
    Then the system should normalize "Gol 1.0" to "Gol"
    And query FIPE with correct model name
    And return the price for Gol

  Scenario: Handle vehicle not in FIPE database
    Given a listing with brand = "BrandX" (unknown brand)
    When I lookup FIPE price
    Then the system should:
      - Query the FIPE API
      - Receive 404 or no results
      - Return null/error indication
      - Log the lookup failure
      - Not crash the system

  Scenario: Retry on FIPE API timeout
    Given the FIPE API is slow to respond (> 5 seconds)
    When I lookup a vehicle price
    Then the system should:
      - Wait up to 10 seconds for response
      - If timeout, retry once with fresh connection
      - If still fails, return error and log failure

  Scenario: Handle FIPE API rate limiting
    Given I make 100+ requests to FIPE API in short time
    When the API returns HTTP 429 (Too Many Requests)
    Then the system should:
      - Detect rate limit response
      - Implement exponential backoff
      - Wait 60 seconds before next request
      - Resume requests after delay
      - Log rate limit events

  Scenario: Cache miss with concurrent requests
    Given two concurrent requests for same vehicle (Fiat Uno 2010)
    And the vehicle is not in cache
    When both requests are processed
    Then the system should:
      - First request queries FIPE API
      - Second request waits for first to complete
      - Both return same cached price
      - Only 1 API call made (no duplicate requests)

  Scenario: Request complete FIPE lookup sequence
    Given a vehicle without cached price
    When I request FIPE price
    Then the system should:
      1. Normalize vehicle data (brand, model)
      2. Query FIPE API for brands list
      3. Match vehicle brand against list
      4. Query FIPE API for models in brand
      5. Match vehicle model against list
      6. Query FIPE API for years
      7. Match vehicle year
      8. Query FIPE API for final price
      9. Cache the price (24 hours)
      10. Return price to caller

  Scenario: Handle multiple vehicle years
    Given vehicle brand/model has multiple years available
    When I request price for specific year (2015)
    Then the system should return price for 2015
    And not return prices for other years (2014, 2016)

  Scenario: Log FIPE lookup failures for manual review
    Given a lookup that fails (vehicle not found, API error, etc)
    When the failure occurs
    Then the system should:
      - Record failure in application logs
      - Include full context (brand, model, year)
      - Mark opportunity for manual review
      - Continue processing other opportunities

  Scenario: Handle FIPE API schema changes
    Given the FIPE API response format has changed
    When parsing the response
    Then the system should:
      - Detect unexpected response structure
      - Log detailed error
      - Fall back to manual/cached price if available
      - Notify administrators of API change

  Scenario: Timezone-aware cache expiration
    Given cache entry created at 2024-01-01 10:00:00 UTC
    And cache TTL is 24 hours
    When checking cache at 2024-01-02 11:00:00 UTC (25 hours later)
    Then cache should be expired
    And fresh FIPE lookup should occur
