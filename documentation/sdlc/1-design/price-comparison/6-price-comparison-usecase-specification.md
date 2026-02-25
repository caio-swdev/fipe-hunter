# Use Case Specification: Price Comparison

## 1. Use Case Name
Price Comparison

## 2. Brief Description
Compare marketplace listing prices against FIPE reference prices to identify underpriced vehicles with discount opportunities (20-50% discount range). Flag suspicious discounts (>50%) for manual review.

## 3. Actors
- **Scoring Engine:** Internal component requesting price comparisons
- **Opportunity Identifier:** Results feed into opportunity creation

## 4. Preconditions
- Listing price is available and valid (positive number)
- FIPE reference price has been obtained (or marked unavailable)
- Discount thresholds are configured (default: 20-50%)

## 5. Basic Flow of Events

1. Receive comparison request: Listing(brand, model, year, price) + FIPE_price
2. Validate price data:
   - Listing price must be positive
   - FIPE price must be positive
   - Both must be numeric
3. Calculate discount:
   - discount_pct = (FIPE_price - listing_price) / FIPE_price * 100
   - discount_amount = FIPE_price - listing_price
4. Evaluate discount against thresholds:
   - If discount_pct < 20%: Exclude (below threshold)
   - If 20% <= discount_pct <= 50%: Mark as OPPORTUNITY
   - If discount_pct > 50%: Mark as SUSPICIOUS (fraud risk)
5. Store comparison result:
   - Record discount_pct, discount_amount, status
   - Link to listing and FIPE price
6. Return result to caller (Opportunity or Excluded)

## 6. Alternative Flows

**6a. Missing FIPE Price**
- If FIPE price is NULL/unavailable:
  - Skip comparison entirely
  - Log as uncompared
  - Do not create opportunity

**6b. Invalid Price Data**
- If listing_price <= 0 or FIPE_price <= 0:
  - Detect invalid data
  - Log data quality issue
  - Alert administrators
  - Skip comparison

**6c. Suspicious High Discount (>50%)**
- If discount_pct > 50%:
  - Flag as potential fraud
  - Create opportunity with status='suspicious'
  - Require manual review before alerting
  - Log forensic details

**6d. Zero Discount (Market Rate)**
- If discount_pct = 0% (within rounding):
  - Log as market-rate (educational)
  - Do not create opportunity

## 7. Postconditions
- Price comparison is recorded in database
- Opportunity created (if discount in 20-50% range)
- Suspicious opportunities flagged for review
- Results available for downstream use cases

## 8. Special Requirements

### Calculation Precision
- Store discount_pct with 2 decimal places
- Use 4 decimal places for rounding decisions
- Round correctly: 19.998% → 20.00%

### Threshold Configuration
- **Minimum:** 20% discount (configurable)
- **Maximum:** 50% discount (configurable)
- **Suspicious:** > 50% (not configurable in MVP)
- **Impact:** Marketplace-specific thresholds in future

### Performance
- Compare 100 listings: < 5 seconds
- Per-comparison: < 50ms

### Error Handling
- Invalid prices: Log and skip
- Missing FIPE: Log and skip
- Calculations: Never crash, always log
