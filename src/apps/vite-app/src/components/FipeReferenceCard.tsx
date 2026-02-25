import { DollarSign, Tag, Hash } from 'lucide-react'
import { formatBRL } from '@packages/automotive-ui'
import { useTheme } from '@packages/design-system-engine'
import { useBreakpoint } from '../hooks/useBreakpoint'

export interface FipeReference {
  brand: string
  model: string
  year: number
  reference_price: number
  fipe_code: string
  reference_month: string
}

export function FipeReferenceCard({ fipe }: { fipe: FipeReference }) {
  const { theme } = useTheme()
  const { colors, glass, spacing, borders } = theme
  const { isMobile } = useBreakpoint()

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: isMobile ? '1fr' : 'auto 1px auto 1px auto',
      alignItems: 'center',
      gap: isMobile ? spacing.sm : spacing.xl,
      borderRadius: glass.borderRadius,
      background: glass.background,
      backdropFilter: `blur(${glass.blur})`,
      border: glass.border,
      boxShadow: glass.shadowGlass,
      padding: isMobile ? spacing.md : `${spacing.md} ${spacing.lg}`,
    }}>
      {/* Referência FIPE */}
      <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm }}>
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          width: '2.25rem', height: '2.25rem', flexShrink: 0,
          borderRadius: borders.radius.xl,
          background: colors.feedback.successLight,
        }}>
          <DollarSign size={18} style={{ color: colors.feedback.success }} />
        </div>
        <div>
          <p style={{ fontSize: '0.688rem', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em', color: colors.feedback.success }}>
            Referência FIPE
          </p>
          <p style={{ fontSize: isMobile ? '1rem' : '1.25rem', fontWeight: 700, color: colors.neutral.text }}>
            {formatBRL(fipe.reference_price)}
          </p>
        </div>
      </div>

      {!isMobile && <div style={{ width: '1px', height: '2.5rem', background: colors.neutral.borderMuted }} />}

      {/* Veículo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm }}>
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          width: '2.25rem', height: '2.25rem', flexShrink: 0,
          borderRadius: borders.radius.xl,
          background: colors.neutral.backgroundLight,
        }}>
          <Tag size={16} style={{ color: colors.neutral.textSecondary }} />
        </div>
        <div style={{ minWidth: 0 }}>
          <p style={{ fontSize: '0.688rem', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em', color: colors.neutral.textMuted }}>
            Veículo
          </p>
          <p style={{ fontSize: '0.875rem', fontWeight: 600, color: colors.neutral.text, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {fipe.brand} {fipe.model} {fipe.year}
          </p>
        </div>
      </div>

      {!isMobile && <div style={{ width: '1px', height: '2.5rem', background: colors.neutral.borderMuted }} />}

      {/* Código FIPE */}
      <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm }}>
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          width: '2.25rem', height: '2.25rem', flexShrink: 0,
          borderRadius: borders.radius.xl,
          background: colors.neutral.backgroundLight,
        }}>
          <Hash size={16} style={{ color: colors.neutral.textSecondary }} />
        </div>
        <div>
          <p style={{ fontSize: '0.688rem', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em', color: colors.neutral.textMuted }}>
            Código FIPE
          </p>
          <p style={{ fontSize: '0.875rem', color: colors.neutral.textSecondary }}>
            {fipe.fipe_code} &middot; {fipe.reference_month}
          </p>
        </div>
      </div>
    </div>
  )
}
