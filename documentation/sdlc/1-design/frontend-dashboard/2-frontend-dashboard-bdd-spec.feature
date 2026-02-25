Feature: Frontend Dashboard
  As a user
  I want to view a comprehensive dashboard with vehicle opportunities and market insights
  So that I can quickly identify and analyze the best investment opportunities

  Background:
    Given the system has imported vehicle listings from marketplaces
    And the system has calculated opportunity scores
    And the user is logged into the dashboard
    And the dashboard backend API is operational

  # === OPPORTUNITY OVERVIEW SECTION ===

  Scenario: Display opportunity overview on dashboard
    When I access the dashboard home page
    Then I should see the opportunity overview section with:
      | metric          | example |
      | Total found     | 342     |
      | New today       | 18      |
      | High score (>75)| 45      |
      | Top score       | 92      |
    And the metrics should be updated within the last 5 minutes
    And the section should display a status indicator (OK/Warning/Error)

  Scenario: View best deals list
    When I access the dashboard home page
    Then I should see a "Best Deals" widget showing top 5 opportunities
    And each deal should display:
      | field            | example         |
      | Vehicle          | 2015 Volkswagen Gol |
      | Listing price    | R$ 25.000       |
      | FIPE price       | R$ 30.000       |
      | Discount         | 16.7%           |
      | Score            | 92/100          |
      | Marketplace      | OLX             |
    And each deal should link to the full opportunity details

  Scenario: View price trends chart
    When I access the dashboard and scroll to price trends section
    Then I should see a line chart showing:
      | axis       | label                          |
      | X-axis     | Last 30 days (daily intervals) |
      | Y-axis     | Average discount percentage    |
    And the chart should display trend line for discount evolution
    And I should see statistics: min discount, max discount, average discount
    And I should be able to export chart data as CSV

  # === OPPORTUNITY BROWSER ===

  Scenario: Browse filtered opportunity table
    When I navigate to the Opportunity Browser page
    Then I should see a paginated table with columns:
      | column            | type     | sortable | width  |
      | Vehicle           | text     | Yes      | 150px  |
      | Brand             | text     | Yes      | 100px  |
      | Year              | number   | Yes      | 80px   |
      | Listing Price     | currency | Yes      | 120px  |
      | FIPE Price        | currency | Yes      | 120px  |
      | Discount %        | percent  | Yes      | 100px  |
      | Score             | number   | Yes      | 80px   |
      | Marketplace       | text     | Yes      | 100px  |
      | Listed date       | date     | Yes      | 100px  |
      | Actions           | buttons  | No       | 100px  |
    And the table should show 25 rows per page
    And pagination controls should be visible at bottom

  Scenario: Search opportunities by text
    Given I am on the Opportunity Browser page
    When I enter "Volkswagen Gol" in the search field
    And I click the search button
    Then the table should filter to show only opportunities with:
      | criteria |
      | Brand matching "Volkswagen" |
      | Model matching "Gol" |
    And the search should complete within 500ms
    And the result count should update dynamically
    And I should see a "Clear search" button to reset

  Scenario: Filter opportunities by score range
    Given I am on the Opportunity Browser page
    When I set the score filter minimum to 75
    And I set the score filter maximum to 100
    And I click "Apply filters"
    Then the table should show only opportunities with score between 75-100
    And the filter status should be displayed above the table
    And the filtered result count should be shown

  Scenario: Filter opportunities by marketplace
    Given I am on the Opportunity Browser page
    When I select "OLX" from the marketplace dropdown
    And I select "WebMotors" from the marketplace dropdown
    And I click "Apply filters"
    Then the table should show only opportunities from OLX and WebMotors
    And the count for each marketplace should be displayed
    And I should see a "Clear all filters" option

  Scenario: Filter opportunities by discount range
    Given I am on the Opportunity Browser page
    When I set minimum discount to 20%
    And I set maximum discount to 40%
    And I click "Apply filters"
    Then the table should show only opportunities within discount range
    And I should see statistics: count, average discount, average score

  Scenario: Sort table by column
    Given I am on the Opportunity Browser page
    When I click the "Score" column header
    Then the table should sort by score in descending order
    And I should see a down arrow icon on the Score column
    When I click the "Score" column header again
    Then the table should sort by score in ascending order
    And I should see an up arrow icon on the Score column

  Scenario: View opportunity details
    Given I am on the Opportunity Browser page
    When I click on an opportunity row or click the "View Details" button
    Then I should see a detail panel/modal with:
      | field              | content |
      | Vehicle details    | brand, model, year, transmission, fuel type |
      | Listing details    | price, mileage, condition, marketplace link |
      | FIPE comparison    | FIPE price, discount %, discount amount (R$) |
      | Score breakdown    | component scores, weights, calculation details |
      | Status             | new, contacted, purchased, etc. |
      | CarWizard status   | if sent to CarWizard, show status |
    And I should see buttons: Open Listing, Mark as Purchased, Archive

  Scenario: Export filtered opportunities
    Given I have filtered the opportunity table
    When I click the "Export" button
    Then I should see export format options: CSV, Excel, PDF
    When I select "CSV"
    Then the browser should download a CSV file
    And the file should contain all visible columns from the table
    And the file should be named "opportunities-{timestamp}.csv"

  # === ANALYTICS SECTION ===

  Scenario: View discount distribution chart
    When I navigate to Analytics page
    Then I should see a histogram showing discount distribution
    And the chart should display:
      | axis   | label                              |
      | X-axis | Discount percentage (buckets)      |
      | Y-axis | Number of opportunities           |
    And buckets should be: 0-10%, 10-20%, 20-30%, 30-40%, 40-50%, 50%+
    And I should see statistics: mean, median, standard deviation
    And I should be able to filter by marketplace or date range

  Scenario: View market trends over time
    When I navigate to Analytics page
    Then I should see a multi-line chart showing market trends
    And the chart should display trends for:
      | metric                    | color |
      | Average discount %        | Blue  |
      | Average score             | Green |
      | Listings found per day    | Orange|
    And the chart should cover the last 30 days with daily granularity
    And I should see statistics for each metric

  Scenario: View best brands analytics
    When I navigate to Analytics page and scroll to brands section
    Then I should see a bar chart showing top 10 brands by:
      | option          | shows                                |
      | Opportunities   | Count of opportunities per brand     |
      | Average score   | Mean score for opportunities         |
      | Average discount| Mean discount % for opportunities    |
    And I should see a toggle to switch between these views
    And the chart should show brand names and statistics

  Scenario: View marketplace performance comparison
    When I navigate to Analytics page
    Then I should see a comparison section with metrics per marketplace:
      | metric              | type    |
      | Total opportunities | number  |
      | Average discount %  | percent |
      | Average score       | number  |
      | Success rate        | percent |
    And data should be displayed as a table or card layout
    And I should be able to compare two marketplaces side-by-side

  # === SETTINGS PAGE ===

  Scenario: Configure scraping schedule
    When I navigate to Settings > Scraping Schedule
    Then I should see options to configure:
      | setting             | type         | default |
      | Scraping frequency  | dropdown     | Hourly  |
      | OLX enabled         | toggle       | ON      |
      | WebMotors enabled   | toggle       | ON      |
      | Start time          | time picker  | 08:00   |
      | Days of week        | checkboxes   | All     |
    And I should see a "Save changes" button
    And I should see a "Test scrape" button to trigger immediate scrape
    When I change scraping frequency to "Daily"
    And I click "Save changes"
    Then the system should display "Settings saved successfully"
    And the new schedule should take effect on next interval

  Scenario: Configure alert thresholds
    When I navigate to Settings > Alert Thresholds
    Then I should see options to configure:
      | setting                  | type    | default |
      | Telegram alert threshold | slider  | Score > 75 |
      | Sheets logging enabled   | toggle  | ON      |
      | CarWizard sync threshold | slider  | Score > 80 |
    And I should see current values and descriptions for each setting
    When I change Telegram threshold to Score > 85
    And I click "Save changes"
    Then the system should update threshold immediately
    And I should see confirmation message

  Scenario: Toggle marketplace sources
    When I navigate to Settings > Marketplace Sources
    Then I should see toggles for each marketplace:
      | marketplace   | enabled |
      | OLX           | Yes     |
      | WebMotors     | Yes     |
    And I should see additional options for each enabled marketplace
    When I disable "WebMotors"
    And I click "Save changes"
    Then WebMotors should no longer appear in future scrapes
    And dashboard metrics should reflect this change

  Scenario: Configure discount filter range
    When I navigate to Settings > Discount Filters
    Then I should see options for:
      | setting              | type           | default |
      | Minimum discount     | number input   | 20%     |
      | Maximum discount     | number input   | 50%     |
    And I should see a "suspicious" flag for discounts > 50%
    When I set minimum to 15% and maximum to 45%
    And I click "Save changes"
    Then the system should apply new filters to scoring

  # === MONITORING SECTION ===

  Scenario: View system monitoring dashboard
    When I navigate to Monitoring page
    Then I should see a monitoring dashboard with:
      | metric            | display           |
      | Last scrape       | "2 hours ago"     |
      | Next scrape       | "In 1 hour"       |
      | Scrape success %  | "95%"             |
      | API health        | Green/Yellow/Red  |
      | Queue status      | "12 pending msgs" |
    And metrics should auto-refresh every 30 seconds

  Scenario: View last scrape details
    Given I am on the Monitoring page
    When I click on "Last scrape" metric
    Then I should see a detail view showing:
      | field              | example             |
      | Scrape start       | 2024-01-15 10:00:00 |
      | Scrape end         | 2024-01-15 10:45:00 |
      | Duration           | 45 minutes          |
      | Listings found     | 120                 |
      | Listings saved     | 115                 |
      | Duplicates         | 5                   |
      | Validation errors  | 2                   |
      | Status             | Completed           |
    And I should see a "View full log" link

  Scenario: View API health status
    Given I am on the Monitoring page
    When I view the API health section
    Then I should see status for each service:
      | service           | status | last_check      |
      | FIPE API          | Healthy| 2 mins ago      |
      | Telegram Bot      | Healthy| 5 mins ago      |
      | Google Sheets     | Healthy| 2 mins ago      |
      | CarWizard API     | Warning| 8 mins ago      |
    And services with warning/error should be highlighted
    And I should see response times for each service

  Scenario: View message queue status
    Given I am on the Monitoring page
    When I view the message queue section
    Then I should see:
      | metric                    | display |
      | Pending messages          | 12      |
      | Failed messages (retry)   | 2       |
      | Messages sent today       | 156     |
      | Queue processing rate     | "5 msg/s"|
    And I should see a "Retry failed" button
    And I should see a "Clear queue" button (with confirmation)

  # === HISTORICAL VIEW ===

  Scenario: View archived opportunities
    When I navigate to Historical > Archived Opportunities
    Then I should see a list of archived/purchased opportunities
    And each entry should display:
      | field           | example              |
      | Vehicle         | 2015 Volkswagen Gol  |
      | Status          | Purchased            |
      | Date archived   | 2024-01-10           |
      | Notes           | "Great deal"         |
    And the list should be sortable and filterable by status/date
    And I should be able to unarchive an opportunity

  Scenario: View price evolution chart
    When I navigate to Historical > Price Evolution
    And I search for a specific vehicle (e.g., "2015 Volkswagen Gol")
    Then I should see a line chart showing:
      | axis       | label                    |
      | X-axis     | Date (last 90 days)      |
      | Y-axis     | Average listing price    |
    And the chart should show price trend for this vehicle
    And statistics should display: current avg, highest, lowest, trend direction
    And I should see how many listings per day contributed to average

  Scenario: Export historical data
    When I navigate to Historical section
    And I click "Export all data"
    Then I should see export options:
      | format | includes                    |
      | CSV    | All opportunities, any date |
      | Excel  | With multiple sheets        |
      | PDF    | Summary report              |
    When I select "CSV"
    Then the system should download all historical data

  # === RESPONSIVE & UX ===

  Scenario: Dashboard works on mobile
    Given I am on a mobile device (viewport < 768px)
    When I access the dashboard
    Then the layout should adapt to mobile:
      - Tables should stack vertically or scroll horizontally
      - Charts should resize to fit viewport
      - Navigation should collapse to hamburger menu
      - Touch-friendly button sizes (min 44px)

  Scenario: Dashboard loads quickly
    When I access any page on the dashboard
    Then the page should:
      - Display initial layout within 2 seconds
      - Load critical data within 3 seconds
      - Load additional data progressively
      - Show loading indicators for async data
      - Support offline caching of static content

  Scenario: Handle no data gracefully
    Given the system has no opportunities or scrape history
    When I access the dashboard
    Then I should see:
      - Friendly message: "No opportunities found yet"
      - Empty state illustrations
      - Suggestions: "Click 'Scrape Now' to get started"
      - Link to trigger manual scrape

  Scenario: Display error messages appropriately
    Given a service (FIPE API, Telegram) becomes unavailable
    When I access the dashboard
    Then I should see:
      - Non-blocking error messages
      - "Service temporarily unavailable" notices
      - Fallback data (cached results)
      - Timestamp of last successful data refresh
      - "Retry" button to attempt reload
