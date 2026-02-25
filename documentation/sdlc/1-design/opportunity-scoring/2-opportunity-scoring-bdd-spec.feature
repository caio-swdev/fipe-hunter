Feature: Opportunity Scoring
  As a priority system
  I want to rank opportunities by profit potential
  So that the best deals are identified first

  Scenario: Calculate opportunity score (0-100 scale)
    Given an opportunity with:
      | discount_pct | 30%    |
      | mileage      | 80000  |
      | condition    | Good   |
      | created_at   | Today  |
    When I calculate score
    Then score should be between 0-100
    And score should reflect profit potential
    And score should be reproducible

  Scenario: Discount score weight (40%)
    Given discount_pct = 40%
    When calculating score components
    Then discount_score = 80 (normalized to 0-100)
    And discount contributes 40% to final score

  Scenario: Condition score weight (30%)
    Given condition = "Good"
    When calculating score components
    Then condition_score = 75 (Good maps to 75/100)
    And condition contributes 30% to final score

  Scenario: Market demand score weight (20%)
    Given brand = "Volkswagen", model = "Gol"
    When calculating demand score
    Then demand_score = 85 (high demand model)
    And demand contributes 20% to final score

  Scenario: Recency score weight (10%)
    Given created_at = Today
    When calculating recency score
    Then recency_score = 100 (fresh listing)
    And recency contributes 10% to final score

  Scenario: Weighted average calculation
    Given scores: discount=80, condition=75, demand=85, recency=100
    When applying weights: 0.40, 0.30, 0.20, 0.10
    Then final_score = (80*0.40 + 75*0.30 + 85*0.20 + 100*0.10) = 82

  Scenario: Excellent condition boost
    Given condition = "Excellent"
    When calculating condition score
    Then condition_score = 95 (excellent condition)

  Scenario: Poor condition penalty
    Given condition = "Poor"
    When calculating condition score
    Then condition_score = 40 (poor condition)

  Scenario: Very high mileage penalty
    Given mileage = 250000 km
    When calculating condition score impact
    Then mileage_factor reduces condition_score by 15-20%

  Scenario: Negative or zero discount (edge case)
    Given discount_pct = 0% (market rate)
    When calculating score
    Then discount_score = 0
    And final_score is very low (< 30)

  Scenario: High discount opportunity
    Given discount_pct = 45%
    When calculating score
    Then discount_score = 90
    And final_score is high (> 75)

  Scenario: Suspicious opportunity (>50% discount)
    Given discount_pct = 60%
    When calculating score
    Then final_score is NOT inflated
    And score treated normally (don't penalize high discounts)
    And actual alert governed by suspicion flag, not score

  Scenario: Sort opportunities by score descending
    Given 10 opportunities with scores: 85, 60, 92, 45, 78, 88, 55, 90, 70, 65
    When sorting by score
    Then order should be: 92, 90, 88, 85, 78, 70, 65, 60, 55, 45

  Scenario: Score at threshold boundaries
    Given opportunities with scores: 74, 75, 76 (alert threshold = 75)
    When evaluating alert eligibility
    Then score 74: not eligible (< 75)
    And score 75: eligible (>= 75)
    And score 76: eligible (> 75)

  Scenario: Consistency across identical inputs
    Given same opportunity processed twice
    When calculating score both times
    Then both scores should be identical

  Scenario: Demand score for less common vehicles
    Given brand = "Lada", model = "Niva" (uncommon in Brazil)
    When calculating demand score
    Then demand_score = 40 (low demand)
    And overall score is lower than common vehicles

  Scenario: Listing age impact on recency
    Given listing created 1 day ago
    When calculating recency score
    Then recency_score = 90 (recent but not today)
    When listing created 7 days ago
    Then recency_score = 60 (week old)
    When listing created 30 days ago
    Then recency_score = 20 (stale)
