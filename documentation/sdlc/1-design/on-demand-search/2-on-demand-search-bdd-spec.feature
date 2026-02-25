Feature: On-Demand Vehicle Search
  As a user
  I want to search for a specific vehicle in real-time
  So that I can find the best deals for exactly what I'm looking for

  Background:
    Given the FIPE API is available
    And the OLX marketplace is accessible
    And the database is initialized
    And the FIPE price cache is working

  Scenario: User searches for a vehicle with complete specifications
    Given the user is on the Opportunity Browser page
    When the user enters "Honda" as brand
    And the user enters "Civic" as model
    And the user enters "2020" as year
    And the user clicks "Search Now" button
    Then the system should query FIPE for "Honda Civic 2020"
    And the FIPE price lookup should complete within 5 seconds
    And the system should scrape OLX for matching listings
    And the system should display "Loading..." indicator
    And OLX scraping should complete within 30 seconds
    And the system should calculate discounts for each listing
    And the system should calculate opportunity scores
    And the system should display results in the opportunity table
    And each result should show:
      | listing_price | fipe_price | discount_pct | score | url |
    And results should be sorted by score descending
    And the system should save results to database as opportunities
    And the system should mark results as "on_demand_search" source

  Scenario: User searches without specifying year (fuzzy matching)
    Given the user is on the Opportunity Browser page
    When the user enters "Toyota" as brand
    And the user enters "Corolla" as model
    And the user leaves year empty
    And the user clicks "Search Now" button
    Then the system should query FIPE for recent Toyota Corolla models
    And the system should search OLX for "Toyota Corolla" without year filter
    And the system should return results for multiple years
    And results should be grouped/sorted by score regardless of year

  Scenario: FIPE lookup fails but system continues
    Given the user searches for "BMW X5"
    And the FIPE API returns an error (5xx or timeout)
    When the system attempts FIPE price lookup
    Then the system should not crash
    And the system should log the FIPE lookup failure
    And the system should attempt to continue with OLX scraping
    And the system should display error message to user
    And the system should offer to retry FIPE lookup
    But the search results should not be saved without FIPE price

  Scenario: OLX scraping returns no results
    Given the user searches for "RollsRoyce Phantom 2025"
    And OLX has no listings matching this vehicle
    When the system completes the search
    Then the system should display "No listings found" message
    And the system should suggest checking marketplace status
    And no opportunities should be created for this search
    And the search attempt should be logged

  Scenario: User searches for vehicle already found in bulk scrape
    Given OLX listings for "Honda Civic 2020" exist in database from bulk scrape
    And the user searches for "Honda Civic 2020"
    When the search completes
    Then the system should return both bulk-scraped and on-demand results
    And results should be deduplicated by URL
    And duplicate URLs should only appear once in results
    And the system should update opportunity status if already exists

  Scenario: Search results include high-scoring opportunities
    Given the user searches for "Volkswagen Gol 2018"
    And OLX listings include vehicles with >30% discount
    When the search completes
    And opportunities with score >75 are identified
    Then the system should trigger alerts for high-scoring results
    And Telegram alerts should be sent (if configured)
    And Google Sheets should be updated with results
    And CarWizard should be notified of opportunities >80 score

  Scenario: Multiple concurrent searches
    Given User A searches for "Honda Civic 2020"
    And User B searches for "Toyota Corolla 2019" simultaneously
    When both searches are processed
    Then the system should handle both searches concurrently
    And neither search should block the other
    And results should be returned independently
    And database integrity should be maintained

  Scenario: Search response time SLA
    Given the user searches for a vehicle
    When the search is triggered
    Then the FIPE lookup should complete within 5 seconds
    And the OLX scraping should complete within 30 seconds
    And the discount calculation should complete within 2 seconds
    And the score calculation should complete within 2 seconds
    And the database save should complete within 5 seconds
    And total search-to-display should be 10-40 seconds

  Scenario: Search query validation
    Given the user attempts to search
    When the user enters an empty brand field
    Then the system should display error "Brand is required"
    And the search should not be submitted

    When the user enters an empty model field
    Then the system should display error "Model is required"
    And the search should not be submitted

    When the user enters invalid year "abc"
    Then the system should display error "Year must be a valid integer"
    And the search should not be submitted

    When the user enters year "2050" (future year)
    Then the system should display error "Year cannot be in the future"
    And the search should not be submitted

    When the user enters year "1800" (too old)
    Then the system should display error "Year must be between 1950 and current year"
    And the search should not be submitted

  Scenario: FIPE price cache reduces API calls
    Given the user searches for "Honda Civic 2020"
    And the FIPE price for "Honda Civic 2020" is cached (less than 24 hours old)
    When the system looks up FIPE price
    Then the system should retrieve price from cache
    And no API call to FIPE should be made
    And the cached price should be used for discount calculation

  Scenario: Results persist and appear in dashboard
    Given the user completes search for "Hyundai HB20 2021"
    And the search returns 5 opportunities
    And results are saved to database
    When the user navigates to Dashboard Home
    Then the new opportunities should appear in "Best Deals" widget (if high-scoring)
    And the metrics should include the new search results
    And the opportunity browser should show all results
    And filtering and sorting should work on search results

  Scenario: API endpoint validation
    Given the search API endpoint is POST /api/search/vehicle
    When a client sends a request with valid JSON:
      | brand | Honda |
      | model | Civic |
      | year  | 2020  |
    Then the system should return 200 OK
    And the response should include status "processing"
    And the response should include a search_id for tracking

    When a client sends invalid JSON
    Then the system should return 400 Bad Request
    And the error message should explain the validation error

    When a client sends request without authentication token
    Then the system should return 401 Unauthorized

    When the system is rate-limited (>5 concurrent searches)
    Then the system should queue the 6th search
    And the response should include estimated_wait_time

  Scenario: Search cancellation
    Given a search is in progress
    And 15 seconds have elapsed
    When the user clicks "Cancel Search" button
    Then the system should stop OLX scraping gracefully
    And partial results should not be saved
    And the loading indicator should disappear
    And a cancellation message should be displayed

  Scenario: Brand/model fuzzy matching
    Given the user searches for "VW Golf 2019"
    When the system normalizes the search query
    Then "VW" should be converted to "Volkswagen"
    And the system should search FIPE for "Volkswagen Golf 2019"
    And OLX scraping should also accept "VW" as valid brand name
