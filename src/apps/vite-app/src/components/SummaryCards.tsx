import { TrendingDown, Trophy, Target, Car, ExternalLink } from 'lucide-react'
import type { DashboardSummary } from '../types/opportunity'
import { useTheme } from '@packages/design-system-engine'
import { formatBRL } from '@packages/automotive-ui'
import { useBreakpoint } from '../hooks/useBreakpoint'

export function SummaryCards({ summary }: { summary: DashboardSummary }) {
  const { theme } = useTheme()
  const { colors, glass, spacing, borders } = theme
  const { isMobile } = useBreakpoint()

  const cards = [
    {
      label: 'Oportunidades',
      value: summary.total_opportunities,
      icon: Car,
      iconColor: colors.feedback.info,
      iconBg: `${colors.feedback.info}15`,
      href: undefined as string | undefined,
    },
    {
      label: 'Desconto Médio',
      value: `${summary.avg_discount.toFixed(1)}%`,
      icon: TrendingDown,
      iconColor: colors.feedback.success,
      iconBg: colors.feedback.successLight,
      href: undefined as string | undefined,
    },
    {
      label: 'Pontuação Média',
      value: summary.avg_score.toFixed(0),
      icon: Target,
      iconColor: colors.brand.primary,
      iconBg: `${colors.brand.primary}15`,
      href: undefined as string | undefined,
    },
    {
      label: 'Maior Desconto',
      value: summary.best_deal
        ? `${summary.best_deal.brand} ${summary.best_deal.model}`
        : 'N/A',
      subtitle: summary.best_deal
        ? `${formatBRL(summary.best_deal.listing_price)} (${summary.best_deal.discount_percent.toFixed(0)}% desc.)`
        : undefined,
      icon: Trophy,
      iconColor: colors.feedback.warning,
      iconBg: colors.feedback.warningLight,
      href: summary.best_deal?.url ?? undefined,
    },
  ]

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(auto-fit, minmax(220px, 1fr))',
      gap: isMobile ? spacing.sm : spacing.md,
    }}>
      {cards.map((card) => {
        const cardStyle = {
          background: glass.background,
          backdropFilter: glass.blur,
          borderRadius: glass.borderRadius,
          border: glass.border,
          padding: isMobile ? spacing.md : spacing.lg,
          boxShadow: glass.shadow,
          textDecoration: 'none',
          display: 'block',
          cursor: card.href ? 'pointer' : 'default',
        }
        const inner = (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm }}>
              <div style={{
                borderRadius: borders.radius.md,
                padding: spacing.sm,
                background: card.iconBg,
                color: card.iconColor,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <card.icon size={20} />
              </div>
              <span style={{
                fontSize: '0.875rem',
                color: colors.neutral.textSecondary,
                flex: 1,
              }}>{card.label}</span>
              {card.href && <ExternalLink size={14} style={{ color: colors.neutral.textSecondary, flexShrink: 0 }} />}
            </div>
            <p style={{
              marginTop: spacing.sm,
              fontSize: isMobile ? '1.125rem' : '1.5rem',
              fontWeight: 600,
              color: colors.neutral.text,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}>{card.value}</p>
            {card.subtitle && (
              <p style={{
                marginTop: spacing.xs,
                fontSize: '0.875rem',
                color: colors.neutral.textSecondary
              }}>{card.subtitle}</p>
            )}
          </>
        )
        return card.href ? (
          <a
            key={card.label}
            href={card.href}
            target="_blank"
            rel="noopener noreferrer"
            style={cardStyle}
          >
            {inner}
          </a>
        ) : (
          <div key={card.label} style={cardStyle}>
            {inner}
          </div>
        )
      })}
    </div>
  )
}
