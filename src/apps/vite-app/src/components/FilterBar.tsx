import { Search, X, ArrowUpDown, RotateCcw, SlidersHorizontal } from 'lucide-react'
import { useFilterStore } from '../store/filters'
import { useTheme } from '@packages/design-system-engine'
import { useBreakpoint } from '../hooks/useBreakpoint'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@packages/ui'

export function FilterBar({ onApply }: { onApply?: () => void }) {
  const {
    searchQuery,
    minScore,
    minDiscount,
    sortBy,
    sortOrder,
    setSearchQuery,
    setMinScore,
    setMinDiscount,
    setSortBy,
    toggleSortOrder,
    resetFilters,
  } = useFilterStore()

  const { theme } = useTheme()
  const { colors, glass, spacing, borders, transitions } = theme
  const { isMobile } = useBreakpoint()

  return (
    <aside style={{
      width: '100%',
      background: glass.background,
      backdropFilter: `blur(${glass.blur})`,
      borderRadius: glass.borderRadius,
      border: glass.border,
      padding: spacing.lg,
      boxShadow: glass.shadow,
      alignSelf: 'flex-start',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: spacing.lg,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm }}>
          <SlidersHorizontal size={14} style={{ color: colors.neutral.textSecondary }} />
          <span style={{
            fontSize: '0.875rem',
            fontWeight: 700,
            color: colors.neutral.text
          }}>Filtros</span>
        </div>
        {!isMobile && (
          <button
            onClick={resetFilters}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: spacing.xs,
              fontSize: '0.688rem',
              fontWeight: 500,
              color: colors.brand.primary,
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              transition: `color ${transitions.duration.fast} ${transitions.timing.ease}`
            }}
            onMouseOver={(e) => e.currentTarget.style.color = colors.brand.primaryHover}
            onMouseOut={(e) => e.currentTarget.style.color = colors.brand.primary}
          >
            <RotateCcw size={10} />
            Limpar Tudo
          </button>
        )}
      </div>

      {/* Quick Search */}
      <div style={{ marginBottom: spacing.lg }}>
        <label style={{
          marginBottom: spacing.sm,
          display: 'block',
          fontSize: '0.688rem',
          fontWeight: 500,
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          color: colors.neutral.textSecondary
        }}>
          Busca Rápida
        </label>
        <div style={{ position: 'relative' }}>
          <Search size={14} style={{
            position: 'absolute',
            left: spacing.sm,
            top: '50%',
            transform: 'translateY(-50%)',
            color: colors.neutral.textSecondary
          }} />
          <input
            type="text"
            placeholder="Filtrar resultados..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              borderRadius: borders.radius.lg,
              border: `1px solid ${colors.neutral.border}`,
              background: colors.neutral.backgroundLight,
              padding: `${spacing.sm} ${spacing.sm} ${spacing.sm} ${spacing.lg}`,
              paddingRight: searchQuery ? '2rem' : spacing.sm,
              fontSize: '0.875rem',
              color: colors.neutral.text,
              transition: `all ${transitions.duration.fast} ${transitions.timing.ease}`,
              outline: 'none'
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = colors.brand.primary
              e.currentTarget.style.background = colors.neutral.background
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = colors.neutral.border
              e.currentTarget.style.background = colors.neutral.backgroundLight
            }}
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              style={{
                position: 'absolute',
                right: '0.625rem',
                top: '50%',
                transform: 'translateY(-50%)',
                color: colors.neutral.textSecondary,
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                padding: '0.25rem',
                display: 'flex',
                alignItems: 'center'
              }}
            >
              <X size={14} />
            </button>
          )}
        </div>
      </div>

      <div style={{ height: '1px', background: colors.neutral.borderMuted, marginBottom: spacing.lg }} />

      {/* Min Score */}
      <div style={{ marginBottom: spacing.lg }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '0.625rem'
        }}>
          <label style={{
            fontSize: '0.688rem',
            fontWeight: 500,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: colors.neutral.textSecondary
          }}>
            Pontuação Mín.
          </label>
          <span style={{
            borderRadius: borders.radius.sm,
            background: colors.neutral.backgroundLight,
            padding: `${spacing.xs} ${spacing.sm}`,
            fontSize: '0.75rem',
            fontWeight: 700,
            color: colors.neutral.text
          }}>
            {minScore}
          </span>
        </div>
        <input
          type="range"
          min={0}
          max={100}
          value={minScore}
          onChange={(e) => setMinScore(Number(e.target.value))}
          style={{ width: '100%', accentColor: colors.brand.primary }}
        />
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: spacing.xs,
          fontSize: '0.625rem',
          color: colors.neutral.textSecondary
        }}>
          <span>0</span>
          <span>50</span>
          <span>100</span>
        </div>
      </div>

      {/* Min Discount */}
      <div style={{ marginBottom: spacing.lg }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '0.625rem'
        }}>
          <label style={{
            fontSize: '0.688rem',
            fontWeight: 500,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: colors.neutral.textSecondary
          }}>
            Desconto Mín.
          </label>
          <span style={{
            borderRadius: borders.radius.sm,
            background: colors.neutral.backgroundLight,
            padding: `${spacing.xs} ${spacing.sm}`,
            fontSize: '0.75rem',
            fontWeight: 700,
            color: colors.neutral.text
          }}>
            {minDiscount}%
          </span>
        </div>
        <input
          type="range"
          min={-50}
          max={50}
          value={minDiscount}
          onChange={(e) => setMinDiscount(Number(e.target.value))}
          style={{ width: '100%', accentColor: colors.feedback.success }}
        />
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: spacing.xs,
          fontSize: '0.625rem',
          color: colors.neutral.textSecondary
        }}>
          <span>-50%</span>
          <span>0%</span>
          <span>+50%</span>
        </div>
      </div>

      <div style={{ height: '1px', background: colors.neutral.borderMuted, marginBottom: spacing.lg }} />

      {/* Sort By */}
      <div>
        <label style={{
          marginBottom: spacing.sm,
          display: 'block',
          fontSize: '0.688rem',
          fontWeight: 500,
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          color: colors.neutral.textSecondary
        }}>
          Ordenar Por
        </label>
        <Select value={sortBy} onValueChange={(v) => setSortBy(v as typeof sortBy)}>
          <SelectTrigger style={{ width: '100%' }}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="score">Pontuação</SelectItem>
            <SelectItem value="discount_percent">Desconto</SelectItem>
            <SelectItem value="listing_price">Preço</SelectItem>
          </SelectContent>
        </Select>

        <button
          onClick={toggleSortOrder}
          style={{
            marginTop: '0.625rem',
            display: 'flex',
            width: '100%',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.375rem',
            borderRadius: borders.radius.lg,
            border: `1px solid ${colors.neutral.border}`,
            background: colors.neutral.backgroundLight,
            padding: `${spacing.sm} ${spacing.md}`,
            fontSize: '0.75rem',
            fontWeight: 500,
            color: colors.neutral.textSecondary,
            cursor: 'pointer',
            transition: `all ${transitions.duration.fast} ${transitions.timing.ease}`
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.background = colors.neutral.surfaceHover
            e.currentTarget.style.color = colors.neutral.text
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.background = colors.neutral.backgroundLight
            e.currentTarget.style.color = colors.neutral.textSecondary
          }}
        >
          <ArrowUpDown size={12} />
          {sortOrder === 'desc' ? 'Maior primeiro' : 'Menor primeiro'}
        </button>
      </div>

      {/* Mobile: reset + apply row */}
      {isMobile && (
        <div style={{
          marginTop: spacing.lg,
          display: 'flex',
          gap: spacing.sm,
        }}>
          <button
            onClick={resetFilters}
            style={{
              flex: 1,
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: spacing.xs,
              fontSize: '0.75rem',
              fontWeight: 500,
              color: colors.neutral.textSecondary,
              background: colors.neutral.backgroundLight,
              border: `1px solid ${colors.neutral.border}`,
              borderRadius: borders.radius.lg,
              padding: `${spacing.sm} ${spacing.md}`,
              cursor: 'pointer',
            }}
          >
            <RotateCcw size={12} />
            Limpar
          </button>
          <button
            onClick={() => onApply?.()}
            style={{
              flex: 1,
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: spacing.xs,
              fontSize: '0.75rem',
              fontWeight: 600,
              color: colors.neutral.textInverse,
              background: colors.brand.primary,
              border: 'none',
              borderRadius: borders.radius.lg,
              padding: `${spacing.sm} ${spacing.md}`,
              cursor: 'pointer',
            }}
          >
            Aplicar
          </button>
        </div>
      )}
    </aside>
  )
}
