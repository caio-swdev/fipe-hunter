Feature: Price Comparison
  As an opportunity identifier
  I want to compare marketplace listing prices against FIPE reference prices
  So that I can identify underpriced vehicles with discount potential

  Background:
    Given the discount threshold is 20-50%
    And FIPE reference prices are available
    And marketplace listings are available
    And suspicious discounts are flagged (>50% below FIPE)

  Scenario: Identify opportunity with valid discount
    Given a vehicle listing:
      | marketplace_price | R$ 20.000,00 |
      | fipe_reference    | R$ 25.000,00 |
      | discount_pct      | 20%          |
    When I compare prices
    Then the system should:
      - Calculate discount: (25000 - 20000) / 25000 = 20%
      - Mark as opportunity (discount >= 20%)
      - Calculate raw discount: R$ 5.000,00
      - Create opportunity record

  Scenario: Exclude overpriced vehicles
    Given a vehicle listing:
      | marketplace_price | R$ 28.000,00 |
      | fipe_reference    | R$ 25.000,00 |
      | discount_pct      | -12% (premium) |
    When I compare prices
    Then the system should:
      - Calculate discount: (25000 - 28000) / 25000 = -12%
      - NOT mark as opportunity (negative discount)
      - Log as excluded (overpriced)

  Scenario: Identify high-value opportunity
    Given a vehicle listing:
      | marketplace_price | R$ 12.000,00 |
      | fipe_reference    | R$ 25.000,00 |
      | discount_pct      | 52%          |
    When I compare prices
    Then the system should:
      - Calculate discount: 52%
      - Mark as opportunity (52% > 20%)
      - Flag as SUSPICIOUS (>50% discount)
      - Require manual review before alerting
      - Log potential fraud risk

  Scenario: Handle exact FIPE price match
    Given a vehicle listing:
      | marketplace_price | R$ 25.000,00 |
      | fipe_reference    | R$ 25.000,00 |
      | discount_pct      | 0%           |
    When I compare prices
    Then the system should:
      - Calculate discount: 0%
      - NOT mark as opportunity (no discount)
      - Log as market rate (educational)

  Scenario: Minimum discount threshold
    Given a vehicle listing:
      | marketplace_price | R$ 20.100,00 |
      | fipe_reference    | R$ 25.000,00 |
      | discount_pct      | 19.6%        |
    When I compare prices
    Then the system should:
      - Calculate discount: 19.6%
      - NOT mark as opportunity (19.6% < 20% threshold)
      - Log as below-threshold

  Scenario: Maximum discount threshold (fraud detection)
    Given a vehicle listing:
      | marketplace_price | R$ 5.000,00  |
      | fipe_reference    | R$ 25.000,00 |
      | discount_pct      | 80%          |
    When I compare prices
    Then the system should:
      - Calculate discount: 80%
      - Flag as HIGH FRAUD RISK (>50%)
      - Require administrator approval before alerting
      - Log with forensic details

  Scenario: Handle missing FIPE price
    Given a listing for vehicle without FIPE reference
    When I attempt price comparison
    Then the system should:
      - Skip comparison (can't compare without reference)
      - Log as uncompared
      - Mark for manual review if high marketplace activity
      - Don't create opportunity

  Scenario: Round discount calculation appropriately
    Given discount calculation results: 19.998%
    When rounding to 2 decimal places
    Then the system should store: 20.00%
    And compare to threshold: 20.00% >= 20% = TRUE (opportunity)

  Scenario: Handle very small price differences
    Given a vehicle listing:
      | marketplace_price | R$ 24.990,00 |
      | fipe_reference    | R$ 25.000,00 |
      | discount_pct      | 0.04%        |
    When I compare prices
    Then the system should:
      - Calculate accurately to 4 decimal places
      - Store raw amount: R$ 10,00
      - NOT mark as opportunity (0.04% < 20%)

  Scenario: Currency validation (all BRL)
    Given listings in Brazilian marketplace (all prices in BRL)
    And FIPE prices in BRL
    When I compare prices
    Then the system should:
      - Use BRL for all calculations
      - Not attempt currency conversion
      - Assume BRL currency throughout

  Scenario: Record discount details for analytics
    Given price comparison resulting in 35% discount
    When creating opportunity record
    Then the system should store:
      - discount_pct: 35.00
      - discount_amount: R$ 8.750,00 (calculated)
      - fipe_price: R$ 25.000,00 (reference)
      - marketplace_price: R$ 16.250,00 (listing)

  Scenario: Batch comparison for efficiency
    Given 50 new listings to compare
    When running batch comparison
    Then the system should:
      - Load all 50 listings at once
      - Load all corresponding FIPE prices at once
      - Perform 50 comparisons sequentially
      - Create opportunities for qualified listings
      - Complete within 10 seconds

  Scenario: Marketplace-specific discount thresholds (future)
    Given different discount thresholds per marketplace:
      | OLX       | 20-50% |
      | WebMotors | 15-50% |
    When comparing OLX listing with 18% discount
    Then the system should:
      - Use OLX threshold (20%)
      - NOT mark as opportunity (18% < 20%)
    When comparing WebMotors listing with 18% discount
    Then the system should:
      - Use WebMotors threshold (15%)
      - Mark as opportunity (18% >= 15%)

  Scenario: Handle zero or negative FIPE price (invalid data)
    Given FIPE price is zero or negative (data error)
    When attempting comparison
    Then the system should:
      - Detect invalid data
      - Log as data quality issue
      - Skip comparison
      - Mark for manual review
      - Alert administrators
