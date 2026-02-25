import type { Opportunity, DashboardSummary } from '../types/opportunity'

const BASE_URL = '/api'

export async function fetchOpportunities(): Promise<Opportunity[]> {
  const res = await fetch(`${BASE_URL}/dashboard/opportunities`, { credentials: 'include' })
  if (!res.ok) throw new Error('Falha ao buscar oportunidades')
  const json = await res.json()
  const items = json.data ?? json
  return items.map((item: Record<string, unknown>) => ({
    id: item.id ?? item.listing_id ?? '',
    brand: item.brand,
    model: item.model,
    year: item.year,
    listing_price: item.listing_price,
    fipe_price: item.fipe_price,
    discount_percent: item.discount_percent ?? 0,
    score: item.score ?? 0,
    mileage_km: item.mileage ?? 0,
    source: item.marketplace ?? item.source ?? '',
    url: item.listing_url ?? item.url ?? '',
    image_url: (item.image_url as string) ?? null,
    found_at: item.created_at ?? item.found_at ?? '',
  }))
}

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const res = await fetch(`${BASE_URL}/dashboard/summary`, { credentials: 'include' })
  if (!res.ok) throw new Error('Falha ao buscar resumo')
  const json = await res.json()
  const data = json.data ?? json
  return {
    total_opportunities: data.total_opportunities ?? 0,
    avg_discount: data.avg_discount ?? 0,
    avg_score: data.best_score ?? data.avg_score ?? 0,
    best_deal: null,
  }
}

export interface FipeModel {
  id: number
  name: string
}

export interface FipeYear {
  code: string
  name: string
}

export async function fetchFipeModels(brandName: string): Promise<{ brand_id: string; models: FipeModel[] }> {
  const res = await fetch(`/api/v1/fipe/catalog/models?brand_name=${encodeURIComponent(brandName)}`, { credentials: 'include' })
  if (!res.ok) throw new Error('Marca não encontrada na FIPE')
  return res.json()
}

export interface FipeVersion {
  id: number
  name: string
  year_code: string
}

export async function fetchFipeVersions(brandId: string, modelBase: string, year: number): Promise<FipeVersion[]> {
  const res = await fetch(
    `/api/v1/fipe/catalog/versions?brand_id=${brandId}&model_base=${encodeURIComponent(modelBase)}&year=${year}`,
    { credentials: 'include' }
  )
  if (!res.ok) throw new Error('Falha ao buscar versões')
  const json = await res.json()
  return json.versions
}

export async function fetchFipeYears(brandId: string, modelId: number): Promise<FipeYear[]> {
  const res = await fetch(`/api/v1/fipe/catalog/years?brand_id=${brandId}&model_id=${modelId}`, { credentials: 'include' })
  if (!res.ok) throw new Error('Falha ao buscar anos')
  const json = await res.json()
  return json.years
}

export interface SearchRequest {
  brand: string
  model: string
  year?: number
  brand_id?: string
  model_id?: number
  year_code?: string
  version?: string
}

export interface SearchResponse {
  status: string
  fipe: {
    brand: string
    model: string
    year: number
    reference_price: number
    fipe_code: string
    reference_month: string
  } | null
  fipe_error: string | null
  results: Opportunity[]
  total_results: number
}

export async function searchVehicle(params: SearchRequest): Promise<SearchResponse> {
  const res = await fetch(`${BASE_URL}/search/vehicle`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
    credentials: 'include',
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Busca falhou' }))
    throw new Error(err.detail ?? 'Busca falhou')
  }
  return res.json()
}

export async function fetchFavorites(): Promise<Opportunity[]> {
  const res = await fetch(`${BASE_URL}/favorites`, { credentials: 'include' })
  if (!res.ok) throw new Error('Falha ao buscar favoritos')
  const json = await res.json()
  const items = json.data ?? []
  return items.map((item: Record<string, unknown>) => ({
    id: item.id ?? '',
    brand: item.brand,
    model: item.model,
    year: item.year,
    listing_price: item.listing_price,
    fipe_price: item.fipe_price,
    discount_percent: item.discount_percent ?? 0,
    score: item.score ?? 0,
    mileage_km: item.mileage_km ?? 0,
    source: item.source ?? '',
    url: item.url ?? '',
    image_url: (item.image_url as string) ?? null,
    found_at: item.found_at ?? '',
  }))
}

export async function addFavorite(opportunityId: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/favorites/${opportunityId}`, {
    method: 'POST',
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Falha ao adicionar favorito')
}

export async function removeFavorite(opportunityId: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/favorites/${opportunityId}`, {
    method: 'DELETE',
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Falha ao remover favorito')
}

export interface ServiceHealth {
  status: 'ok' | 'rate_limited'
  last_429_at: string | null
  count_24h: number
}

export interface AdminHealth {
  services: {
    fipe: ServiceHealth
    olx: ServiceHealth
    webmotors: ServiceHealth
  }
  alerts: {
    pending: number
    failed: number
    sent_today: number
  }
  scraping: {
    opportunities_today: number
    listings_today: number
  }
  cache: {
    total: number
    active: number
    expired: number
  }
  search_cache: {
    total: number
    active: number
    expired: number
  }
  api_hits: {
    fipe: { total_24h: number; series: { hour: string; count: number }[] }
    olx: { total_24h: number; series: { hour: string; count: number }[] }
    webmotors: { total_24h: number; series: { hour: string; count: number }[] }
  }
  catalog_cache: {
    total: number
    active: number
    expired: number
    avg_streak: number
    max_streak: number
  }
  cache_stats: {
    requests: number
    hits: number
    hit_rate_pct: number
  }
}

export async function adminLogin(username: string, password: string): Promise<{ access_token: string }> {
  const res = await fetch(`${BASE_URL}/admin/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Credenciais inválidas' }))
    throw new Error(err.detail ?? 'Credenciais inválidas')
  }
  return res.json()
}

export async function fetchAdminHealth(token: string): Promise<AdminHealth> {
  const res = await fetch(`${BASE_URL}/admin/health`, {
    credentials: 'include',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error('Falha ao buscar saúde do sistema')
  return res.json()
}
