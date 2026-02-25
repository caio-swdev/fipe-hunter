import { useOpportunities, useDashboardSummary } from '../hooks/useOpportunities'
import { SummaryCards } from '../components/SummaryCards'
import { Link } from 'react-router-dom'
import { ArrowRight, ExternalLink } from 'lucide-react'
import { useTheme } from '@packages/design-system-engine'
import { formatBRL } from '@packages/automotive-ui'
import { useBreakpoint } from '../hooks/useBreakpoint'

export function Dashboard() {
  const { data: opportunities, isLoading: loadingOps } = useOpportunities()
  const { data: summary, isLoading: loadingSummary } = useDashboardSummary()
  const { theme } = useTheme()
  const { colors, glass, spacing, borders, transitions } = theme
  const { isMobile } = useBreakpoint()

  if (loadingOps || loadingSummary) {
    return (
      <div style={{
        padding: `${spacing.xl} 0`,
        textAlign: 'center',
        color: colors.neutral.textSecondary
      }}>
        Carregando painel...
      </div>
    )
  }

  const topDeals = (opportunities ?? [])
    .slice()
    .sort((a, b) => b.discount_percent - a.discount_percent)
    .slice(0, 5)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.lg }}>
      <div style={{
        display: 'flex',
        flexDirection: isMobile ? 'column' : 'row',
        alignItems: isMobile ? 'flex-start' : 'center',
        justifyContent: 'space-between',
        gap: isMobile ? spacing.sm : 0,
      }}>
        <div>
          <h2 style={{
            fontSize: '1.125rem',
            fontWeight: 600,
            color: colors.neutral.text
          }}>Painel</h2>
          <p style={{
            fontSize: '0.875rem',
            color: colors.neutral.textSecondary
          }}>Visão geral das oportunidades de veículos</p>
        </div>
        <Link
          to="/opportunities"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: spacing.xs,
            borderRadius: borders.radius.md,
            background: colors.brand.primary,
            padding: `${spacing.sm} ${spacing.md}`,
            fontSize: '0.875rem',
            color: colors.neutral.textInverse,
            textDecoration: 'none',
            transition: `background ${transitions.duration.fast} ${transitions.timing.ease}`,
            alignSelf: isMobile ? 'stretch' : 'auto',
            justifyContent: isMobile ? 'center' : 'flex-start',
          }}
          onMouseOver={(e) => e.currentTarget.style.background = colors.brand.primaryHover}
          onMouseOut={(e) => e.currentTarget.style.background = colors.brand.primary}
        >
          Ver Todas <ArrowRight size={14} />
        </Link>
      </div>

      {summary && <SummaryCards summary={{ ...summary, best_deal: topDeals[0] ?? null }} />}

      {/* Best Deals */}
      <div style={{
        background: glass.background,
        backdropFilter: glass.blur,
        borderRadius: glass.borderRadius,
        border: glass.border,
        boxShadow: glass.shadow,
      }}>
        <div style={{
          borderBottom: `1px solid ${colors.neutral.borderMuted}`,
          padding: `${spacing.md} ${spacing.lg}`
        }}>
          <h3 style={{
            fontSize: '0.875rem',
            fontWeight: 500,
            color: colors.neutral.text
          }}>Melhores Ofertas</h3>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {topDeals.length === 0 ? (
            <div style={{
              padding: `${spacing.xl} ${spacing.lg}`,
              textAlign: 'center',
              fontSize: '0.875rem',
              color: colors.neutral.textSecondary
            }}>
              Nenhuma oportunidade ainda. Execute uma busca para encontrar ofertas.
            </div>
          ) : (
            topDeals.map((o, idx) => (
              <div
                key={o.id}
                style={{
                  display: 'flex',
                  flexDirection: isMobile ? 'column' : 'row',
                  alignItems: isMobile ? 'flex-start' : 'center',
                  justifyContent: 'space-between',
                  gap: isMobile ? spacing.xs : 0,
                  padding: `${spacing.md} ${isMobile ? spacing.md : spacing.lg}`,
                  borderTop: idx > 0 ? `1px solid ${colors.neutral.borderMuted}` : 'none',
                  transition: `background ${transitions.duration.fast} ${transitions.timing.ease}`
                }}
                onMouseOver={(e) => e.currentTarget.style.background = colors.neutral.surfaceHover}
                onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <div>
                  <p style={{
                    fontSize: '0.875rem',
                    fontWeight: 500,
                    color: colors.neutral.text
                  }}>
                    {o.year} {o.brand} {o.model}
                  </p>
                  <p style={{
                    fontSize: '0.75rem',
                    color: colors.neutral.textSecondary
                  }}>
                    {formatBRL(o.listing_price)} → FIPE {formatBRL(o.fipe_price)}
                  </p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm }}>
                  <span style={{
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    color: colors.feedback.success
                  }}>
                    {o.discount_percent.toFixed(1)}% desc.
                  </span>
                  <span style={{
                    borderRadius: borders.radius.full,
                    background: `${colors.brand.primary}15`,
                    padding: `${spacing.xs} ${spacing.sm}`,
                    fontSize: '0.75rem',
                    fontWeight: 500,
                    color: colors.brand.primary
                  }}>
                    Pontuação {o.score}
                  </span>
                  {o.url && (
                    <a
                      href={o.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        color: colors.neutral.textSecondary,
                        transition: `color ${transitions.duration.fast} ${transitions.timing.ease}`
                      }}
                      onMouseOver={(e) => e.currentTarget.style.color = colors.brand.primary}
                      onMouseOut={(e) => e.currentTarget.style.color = colors.neutral.textSecondary}
                    >
                      <ExternalLink size={14} />
                    </a>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
