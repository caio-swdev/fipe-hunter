export interface Opportunity {
  id: string
  brand: string
  model: string
  year: number
  listing_price: number
  fipe_price: number
  discount_percent: number
  score: number
  mileage_km: number
  source: string
  url: string
  image_url: string | null
  found_at: string
}

export interface DashboardSummary {
  total_opportunities: number
  avg_discount: number
  avg_score: number
  best_deal: Opportunity | null
}
