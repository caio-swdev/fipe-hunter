Feature: Web Scraping
  As a system operator
  I want to automatically extract vehicle listings from Brazilian marketplaces
  So that I have up-to-date data for price comparison and opportunity identification

  Background:
    Given the OLX marketplace is available
    And the WebMotors marketplace is available
    And the scraper has valid user-agent rotation configured
    And request delays are set to 1-3 seconds between requests

  Scenario: Scrape OLX listings successfully
    When I trigger a scrape of OLX Rio marketplace
    Then the system should extract 20-50 vehicle listings
    And each listing should have brand, model, year, price, mileage, condition
    And each listing should have a valid URL
    And the system should save listings to database
    And a scrape log entry should be created with 'completed' status

  Scenario: Handle OLX anti-bot measures
    Given OLX has detected previous rapid requests from this IP
    When I trigger a scrape of OLX
    Then the system should rotate user-agent headers
    And the system should apply 2-3 second delays between requests
    And the system should use different request patterns (mobile, desktop, bot)
    And the scrape should eventually complete successfully

  Scenario: Parse vehicle listing details correctly
    Given a raw HTML listing element from OLX
    When the scraper parses the listing
    Then it should extract:
      | field     | example value              |
      | brand     | Volkswagen                 |
      | model     | Gol                        |
      | year      | 2015                       |
      | price     | R$ 25.000                  |
      | mileage   | 120.000 km                 |
      | condition | Bom                        |
      | url       | https://rj.olx.com.br/... |

  Scenario: Handle missing listing data gracefully
    Given a listing with incomplete data (missing mileage or condition)
    When the scraper processes it
    Then it should fill missing fields with default values
    And the listing should still be saved
    And an info log should note the missing field

  Scenario: Scrape WebMotors listings successfully
    When I trigger a scrape of WebMotors marketplace
    Then the system should extract 20-50 vehicle listings
    And each listing should have brand, model, year, price, mileage, condition
    And each listing should have a valid URL
    And the system should save listings to database
    And a scrape log entry should be created with 'completed' status

  Scenario: Handle marketplace unavailability
    Given OLX marketplace returns HTTP 503 (Service Unavailable)
    When I trigger a scrape
    Then the system should retry up to 3 times with exponential backoff
    And if all retries fail, the scrape log should record 'failed' status
    And the error message should be logged for manual review

  Scenario: Respect marketplace Terms of Service
    When the scraper operates
    Then it should:
      - Use reasonable request delays (1-3 seconds)
      - Rotate user-agent headers
      - Identify itself in requests
      - Not scrape private/contact information

  Scenario: Deduplicate listings within same scrape
    Given I scrape 50 listings
    And 5 of them are duplicates (same URL)
    When the deduplication runs
    Then the system should keep 1 copy of each URL
    And mark the duplicate entries with is_duplicate=true
    And save only 45 unique listings to opportunities table

  Scenario: Handle HTML structure changes
    Given the OLX website has updated its HTML structure
    When the scraper encounters unrecognized element formats
    Then it should log a warning with the failing element
    And skip that element (don't crash)
    And continue processing remaining listings
    And notify administrators of potential maintenance needed

  Scenario: Rate limit handling
    Given the scraper has reached the OLX request rate limit
    When attempting to fetch the next page
    Then the system should:
      - Detect the rate limit response (HTTP 429)
      - Implement exponential backoff (retry after 60 seconds)
      - Resume scraping once rate limit window expires
      - Log the rate limit event

  Scenario: Scrape job scheduling
    Given the system is configured with hourly scraping schedule
    When the scheduled scrape time arrives
    Then the system should automatically trigger scraping
    And scrape both OLX and WebMotors
    And log results to scrape_logs table
    And proceed to opportunity creation if listings found

  Scenario: Validate listing data before saving
    Given a scraped listing with invalid data (negative price, year out of range)
    When the listing validation runs
    Then it should reject the listing
    And log validation error
    And not save invalid data to database
    And continue processing other listings

  Scenario: Handle request timeout gracefully
    Given the marketplace server is slow to respond
    When the scraper's timeout threshold (10 seconds) is exceeded
    Then the system should:
      - Abort the request
      - Log timeout error
      - Retry with backoff
      - Move on to next request after max retries

  Scenario: Extract seller information
    Given a listing with seller details available
    When the scraper parses the listing
    Then it should extract seller_name and seller_rating (if available)
    And save to listing record
    And handle cases where seller info is not displayed
