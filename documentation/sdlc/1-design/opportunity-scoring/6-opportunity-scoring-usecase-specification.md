# Use Case Specification: Opportunity Scoring

## 1. Use Case Name
Opportunity Scoring

## 2. Brief Description
Calculate profit potential scores (0-100 scale) for qualified opportunities using weighted components: discount percentage (40%), vehicle condition (30%), market demand (20%), and listing recency (10%).

## 3. Actors
- **Opportunity Comparator:** Sends opportunities needing scores
- **Scoring Algorithm:** Calculates and ranks scores

## 4. Preconditions
- Opportunity has valid discount (20-50%)
- Listing contains condition and mileage data
- Market demand reference data available

## 5. Basic Flow of Events

1. Receive opportunity: Listing + discount_pct
2. Calculate score components:

   **Discount Score (40% weight):**
   - Map discount_pct to 0-100 scale
   - 0% discount → score 0
   - 20% discount → score 40
   - 50% discount → score 100
   - Linear interpolation between points

   **Condition Score (30% weight):**
   - Excellent → 95
   - Good → 75
   - Fair → 50
   - Poor → 40
   - Apply mileage penalty (reduce score 5-10% per 50k km over baseline)

   **Demand Score (20% weight):**
   - Query market demand data (brands/models with high search activity)
   - High demand (Volkswagen Gol) → score 85
   - Medium demand (Fiat Uno) → score 70
   - Low demand (Lada Niva) → score 40

   **Recency Score (10% weight):**
   - Today → 100
   - 1-7 days → 90-60
   - 8-30 days → 59-20
   - >30 days → 20

3. Apply weighted average:
   - final_score = (discount_score × 0.40) + (condition_score × 0.30) + (demand_score × 0.20) + (recency_score × 0.10)

4. Round to integer (0-100)

5. Store score in opportunity record

6. Return scored opportunity

## 6. Postconditions
- Opportunity has calculated score (0-100)
- Score is stored in database
- Opportunity ready for ranking and alerts

## 7. Special Requirements

### Scoring Weights (Configurable)
- Discount: 40% (profit potential)
- Condition: 30% (vehicle quality)
- Demand: 20% (market viability)
- Recency: 10% (listing freshness)

### Performance
- Score 100 opportunities: < 5 seconds
- Per-opportunity: < 50ms

### Data Consistency
- Same inputs always produce same score
- Score calculation deterministic and reproducible

### Edge Cases
- Negative discount: score will be very low (acceptable)
- Missing demand data: use default (70) and log warning
- Very old listing: low recency score but doesn't exclude opportunity
