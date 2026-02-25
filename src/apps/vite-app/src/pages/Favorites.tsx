import { Heart, Loader2 } from 'lucide-react'
import { useFavorites } from '../hooks/useFavorites'
import { OpportunityTable } from '../components/OpportunityTable'
import { useTheme } from '@packages/design-system-engine'

export function Favorites() {
  const { data, isLoading, error } = useFavorites()
  const { theme } = useTheme()
  const { colors, glass, spacing, borders } = theme

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.lg }}>
      {/* Page Header */}
      <div>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: colors.neutral.text }}>
          Favoritos
        </h2>
        <p style={{ fontSize: '0.875rem', color: colors.neutral.textMuted, marginTop: '0.125rem' }}>
          Oportunidades marcadas com ♥ — salvas neste dispositivo
        </p>
      </div>

      {isLoading && (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: `${spacing['4xl']} 0`,
          color: colors.neutral.textMuted,
        }}>
          <Loader2 size={28} className="animate-spin" style={{ marginBottom: spacing.md }} />
          <p style={{ fontSize: '0.875rem' }}>Carregando favoritos...</p>
        </div>
      )}

      {error && (
        <div style={{
          borderRadius: borders.radius['2xl'],
          border: `1px solid ${colors.feedback.warning}`,
          background: colors.feedback.warningLight,
          padding: `${spacing.sm} ${spacing.md}`,
          fontSize: '0.875rem',
          color: colors.feedback.warning,
        }}>
          Falha ao carregar favoritos. Tente novamente.
        </div>
      )}

      {!isLoading && !error && data && data.length === 0 && (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: glass.borderRadius,
          border: glass.border,
          borderStyle: 'dashed',
          borderWidth: '2px',
          background: glass.backgroundLight,
          backdropFilter: glass.blur,
          padding: '64px 32px',
          textAlign: 'center',
        }}>
          <Heart size={48} strokeWidth={1} style={{ color: colors.neutral.textSecondary, marginBottom: '16px' }} />
          <p style={{ fontSize: '14px', fontWeight: '500', color: colors.neutral.textSecondary }}>
            Nenhum favorito ainda
          </p>
          <p style={{ fontSize: '12px', color: colors.neutral.textMuted, marginTop: '4px' }}>
            Marque carros com ♥ nas Oportunidades
          </p>
        </div>
      )}

      {!isLoading && !error && data && data.length > 0 && (
        <>
          <p style={{ fontSize: '0.875rem', color: colors.neutral.textSecondary }}>
            <span style={{ fontWeight: 600, color: colors.neutral.text }}>{data.length}</span>{' '}
            {data.length !== 1 ? 'favoritos' : 'favorito'}
          </p>
          <OpportunityTable opportunities={data} />
        </>
      )}
    </div>
  )
}
