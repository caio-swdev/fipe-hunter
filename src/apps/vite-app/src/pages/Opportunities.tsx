import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useOpportunities } from '../hooks/useOpportunities'
import { FilterBar } from '../components/FilterBar'
import { OpportunityTable } from '../components/OpportunityTable'
import { SearchForm } from '../components/SearchForm'
import { searchVehicle } from '../services/api'
import type { SearchResponse, SearchRequest } from '../services/api'
import type { Opportunity } from '../types/opportunity'
import { Loader2, SlidersHorizontal, Car } from 'lucide-react'
import { useTheme } from '@packages/design-system-engine'
import { useBreakpoint } from '../hooks/useBreakpoint'
import { FipeReferenceCard } from '../components/FipeReferenceCard'

export function Opportunities() {
  const { data: opportunities, isLoading, error } = useOpportunities()
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null)
  const [isSearching, setIsSearching] = useState(false)
  const [filterSheetOpen, setFilterSheetOpen] = useState(false)
  const [searchParams, setSearchParams] = useSearchParams()

  useEffect(() => {
    const brand = searchParams.get('brand')
    const model = searchParams.get('model')
    const version = searchParams.get('version')
    const model_id = searchParams.get('model_id')
    if (!brand || !model || !version || !model_id) return

    setIsSearching(true)
    searchVehicle({
      brand,
      model,
      version,
      model_id: Number(model_id),
      brand_id: searchParams.get('brand_id') ?? undefined,
      year: searchParams.get('year') ? Number(searchParams.get('year')) : undefined,
      year_code: searchParams.get('year_code') ?? undefined,
    })
      .then(handleSearchResults)
      .catch(() => setIsSearching(false))
  }, []) // run once on mount

  function handleSearchStart() {
    setSearchResponse(null)
    setIsSearching(true)
  }

  function handleSearchResults(response: SearchResponse) {
    setSearchResponse(response)
    setIsSearching(false)
  }

  function handleSearchError() {
    setIsSearching(false)
  }

  function handleSearchParams(params: SearchRequest) {
    const p: Record<string, string> = {
      brand: params.brand,
      model: params.model,
      version: params.version ?? '',
      model_id: String(params.model_id ?? ''),
    }
    if (params.brand_id) p.brand_id = params.brand_id
    if (params.year) p.year = String(params.year)
    if (params.year_code) p.year_code = params.year_code
    setSearchParams(p, { replace: true })
  }

  const { theme } = useTheme()
  const { colors, glass, spacing, borders, transitions } = theme
  const { isMobile, isDesktop } = useBreakpoint()

  const displayOpportunities: Opportunity[] = searchResponse
    ? searchResponse.results
    : []

  const fipe = searchResponse?.fipe

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.lg }}>
      <style>{`
        @keyframes slideInUp {
          from { transform: translateY(100%); }
          to { transform: translateY(0); }
        }
      `}</style>

      {/* Page Header */}
      <div>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: colors.neutral.text }}>Explorar Oportunidades</h2>
        <p style={{ fontSize: '0.875rem', color: colors.neutral.textMuted, marginTop: '0.125rem' }}>
          Busque veículos e encontre as melhores ofertas abaixo da FIPE
        </p>
      </div>

      {/* Search Bar */}
      <SearchForm onResults={handleSearchResults} onSearchStart={handleSearchStart} onSearchError={handleSearchError} onSearchParams={handleSearchParams} />

      {/* FIPE Reference Card */}
      {fipe && <FipeReferenceCard fipe={fipe} />}

      {/* FIPE Error */}
      {searchResponse?.fipe_error && (
        <div style={{
          borderRadius: borders.radius['2xl'],
          border: `1px solid ${colors.feedback.warning}`,
          background: colors.feedback.warningLight,
          padding: `${spacing.sm} ${spacing.md}`,
          fontSize: '0.875rem',
          color: colors.feedback.warning,
        }}>
          Consulta FIPE falhou: {searchResponse.fipe_error}
        </div>
      )}

      {/* No Results Message */}
      {searchResponse && searchResponse.total_results === 0 && !fipe && (
        <div style={{
          borderRadius: borders.radius['2xl'],
          border: glass.border,
          background: glass.background,
          padding: spacing.xl,
          textAlign: 'center',
          color: colors.neutral.textMuted,
        }}>
          Nenhum anúncio encontrado. Tente outra marca/modelo ou verifique se a API FIPE está acessível.
        </div>
      )}

      {/* 2-Column Layout: Sidebar + Results */}
      <div style={{ display: 'flex', gap: spacing.lg }}>
        {/* Sidebar — desktop/tablet only */}
        {!isMobile && (
          <div style={{
            width: isDesktop ? '280px' : '240px',
            flexShrink: 0,
            position: 'sticky',
            top: spacing.lg,
            alignSelf: 'flex-start',
          }}>
            <FilterBar />
          </div>
        )}

        {/* Results column */}
        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: spacing.lg }}>
          {/* Results Header */}
          {(isMobile || (searchResponse && searchResponse.total_results > 0)) && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                {searchResponse && searchResponse.total_results > 0 && (
                  <p style={{ fontSize: '0.875rem', color: colors.neutral.textSecondary }}>
                    Exibindo{' '}
                    <span style={{ fontWeight: 600, color: colors.neutral.text }}>{searchResponse.total_results}</span>{' '}
                    {searchResponse.total_results !== 1 ? 'resultados' : 'resultado'}
                  </p>
                )}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm }}>
                {isMobile && (
                  <button
                    onClick={() => setFilterSheetOpen(true)}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: spacing.xs,
                      borderRadius: borders.radius.lg,
                      border: `1px solid ${colors.neutral.border}`,
                      background: glass.background,
                      backdropFilter: `blur(${glass.blur})`,
                      padding: `${spacing.xs} ${spacing.sm}`,
                      fontSize: '0.75rem',
                      fontWeight: 500,
                      color: colors.neutral.textSecondary,
                      cursor: 'pointer',
                    }}
                  >
                    <SlidersHorizontal size={14} />
                    Filtros
                  </button>
                )}
                {searchResponse && searchResponse.total_results > 0 && (
                  <button
                    onClick={() => {
                      setSearchResponse(null)
                      setSearchParams({}, { replace: true })
                    }}
                    style={{
                      borderRadius: borders.radius.lg,
                      padding: `${spacing.xs} ${spacing.sm}`,
                      fontSize: '0.75rem',
                      fontWeight: 500,
                      color: colors.brand.primary,
                      background: 'transparent',
                      border: 'none',
                      cursor: 'pointer',
                      transition: `background ${transitions.duration.fast} ${transitions.timing.ease}`,
                    }}
                    onMouseOver={(e) => e.currentTarget.style.background = colors.neutral.backgroundLight}
                    onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
                  >
                    Limpar busca
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Results Content */}
          {isSearching ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: `${spacing['4xl']} 0`, color: colors.neutral.textMuted }}>
              <Loader2 size={28} className="animate-spin" style={{ marginBottom: spacing.md }} />
              <p style={{ fontSize: '0.875rem' }}>Buscando anúncios...</p>
            </div>
          ) : !searchResponse ? (
            <div style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              padding: `${spacing['4xl']} 0`, textAlign: 'center',
            }}>
              <Car size={48} strokeWidth={1} style={{ color: colors.neutral.textSecondary, marginBottom: spacing.md }} />
              <p style={{ fontSize: '0.875rem', fontWeight: 500, color: colors.neutral.textSecondary }}>
                Busque por marca e modelo acima
              </p>
              <p style={{ fontSize: '0.75rem', color: colors.neutral.textMuted, marginTop: spacing.xs }}>
                Os resultados aparecerão aqui
              </p>
            </div>
          ) : (
            <OpportunityTable opportunities={displayOpportunities} />
          )}
        </div>
      </div>

      {/* Mobile Bottom Sheet */}
      {isMobile && filterSheetOpen && (
        <>
          {/* Backdrop */}
          <div
            onClick={() => setFilterSheetOpen(false)}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0, 0, 0, 0.5)',
              zIndex: 50,
            }}
          />
          {/* Sheet */}
          <div style={{
            position: 'fixed',
            bottom: 0,
            left: 0,
            right: 0,
            maxHeight: '85vh',
            overflowY: 'auto',
            zIndex: 51,
            background: colors.neutral.background,
            borderRadius: `${borders.radius['2xl']} ${borders.radius['2xl']} 0 0`,
            animation: 'slideInUp 0.3s ease-out',
          }}>
            {/* Drag Handle */}
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              padding: `${spacing.sm} 0`,
              position: 'sticky',
              top: 0,
              background: colors.neutral.background,
              borderRadius: `${borders.radius['2xl']} ${borders.radius['2xl']} 0 0`,
              zIndex: 1,
            }}>
              <div style={{
                width: '2rem',
                height: '0.25rem',
                borderRadius: borders.radius.full,
                background: colors.neutral.borderMuted,
              }} />
            </div>
            <div style={{ padding: `0 ${spacing.lg} ${spacing.lg}` }}>
              <FilterBar onApply={() => setFilterSheetOpen(false)} />
            </div>
          </div>
        </>
      )}
    </div>
  )
}
