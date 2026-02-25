import { ExternalLink, Car, SearchX, Calendar, Gauge, Heart } from 'lucide-react'
import { useState } from 'react'
import type { Opportunity } from '../types/opportunity'
import { useFilterStore } from '../store/filters'
import { useFavoritesStore } from '../store/favorites'
import { useToggleFavorite } from '../hooks/useFavorites'
import { useTheme } from '@packages/design-system-engine'
import { formatBRL } from '@packages/automotive-ui'

function DiscountBadge({ value }: { value: number }) {
  // Color grading: Red < 0%, Yellow 0-24%, Green 25%+
  const getColors = () => {
    if (value < 0) {
      // Red - Overpriced
      return {
        background: '#ef4444',
        border: '#f87171',
        shadow: '0 0 8px rgba(239, 68, 68, 0.5)'
      }
    } else if (value >= 25) {
      // Green - Great deal
      return {
        background: '#22c55e',
        border: '#4ade80',
        shadow: '0 0 8px rgba(34, 197, 94, 0.5)'
      }
    } else {
      // Yellow - Okay deal
      return {
        background: '#eab308',
        border: '#facc15',
        shadow: '0 0 8px rgba(234, 179, 8, 0.5)'
      }
    }
  }

  const colors = getColors()
  const arrow = value < 0 ? '↑' : '↓'

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '2px',
      borderRadius: '8px',
      border: `1px solid ${colors.border}`,
      background: colors.background,
      boxShadow: colors.shadow,
      padding: '2px 8px',
      fontSize: '11px',
      fontWeight: '700',
      color: '#fff'
    }}>
      {arrow} {Math.abs(value).toFixed(1)}%
    </span>
  )
}

function ScoreBadge({ score }: { score: number }) {
  if (!score) return null

  const bg =
    score >= 70 ? '#2563eb'
    : score >= 45 ? '#60a5fa'
    : '#9ca3af'

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: '9999px',
      width: '28px',
      height: '28px',
      fontSize: '11px',
      fontWeight: 700,
      background: bg,
      color: '#fff',
      boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
      flexShrink: 0,
    }}>
      {score}
    </span>
  )
}

function OpportunityCard({ opportunity: o }: { opportunity: Opportunity }) {
  const { theme } = useTheme()
  const { glass, colors } = theme
  const [imageError, setImageError] = useState(false)
  const isFavorited = useFavoritesStore((s) => s.favoriteIds.has(o.id))
  const toggleFavorite = useToggleFavorite()

  return (
    <div style={{
      position: 'relative',
      borderRadius: glass.borderRadius,
      background: glass.background,
      backdropFilter: glass.blur,
      WebkitBackdropFilter: glass.blur,
      border: glass.border,
      boxShadow: glass.shadowGlass,
      overflow: 'hidden',
      transition: 'all 0.3s ease',
    }}>
      {/* Image */}
      <div style={{
        position: 'relative',
        aspectRatio: '16/10',
        background: glass.backgroundSecondary,
        overflow: 'hidden'
      }}>
        {o.image_url && !imageError ? (
          <img
            key={o.image_url}
            src={`/api/proxy/image?url=${encodeURIComponent(o.image_url)}`}
            alt={`${o.brand} ${o.model}`}
            referrerPolicy="no-referrer"
            onError={() => setImageError(true)}
            style={{
              height: '100%',
              width: '100%',
              objectFit: 'cover',
              transition: 'transform 0.5s ease',
            }}
          />
        ) : (
          <div style={{
            display: 'flex',
            height: '100%',
            alignItems: 'center',
            justifyContent: 'center',
            color: colors.neutral.textSecondary
          }}>
            <Car size={48} strokeWidth={1} />
          </div>
        )}

        {/* Source badge - top left */}
        <div style={{
          position: 'absolute',
          top: '12px',
          left: '12px',
          borderRadius: '8px',
          background: 'rgba(0, 0, 0, 0.5)',
          backdropFilter: 'blur(8px)',
          padding: '4px 8px',
          fontSize: '10px',
          fontWeight: '600',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          color: '#fff'
        }}>
          {o.source}
        </div>

        {/* Heart button - top right, left of score badge */}
        <button
          onClick={(e) => {
            e.stopPropagation()
            toggleFavorite.mutate({ id: o.id, wasFavorited: isFavorited })
          }}
          style={{
            position: 'absolute',
            top: '10px',
            right: o.score ? '48px' : '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '28px',
            height: '28px',
            borderRadius: '50%',
            background: 'rgba(0,0,0,0.45)',
            backdropFilter: 'blur(6px)',
            border: 'none',
            cursor: 'pointer',
            padding: 0,
          }}
          title={isFavorited ? 'Remover dos favoritos' : 'Adicionar aos favoritos'}
        >
          <Heart
            size={14}
            fill={isFavorited ? '#ef4444' : 'transparent'}
            color={isFavorited ? '#ef4444' : '#fff'}
          />
        </button>

        {/* Score badge - top right */}
        <div style={{ position: 'absolute', top: '12px', right: '12px' }}>
          <ScoreBadge score={o.score} />
        </div>
      </div>

      {/* Content */}
      <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>

        {/* Title + meta */}
        <div>
          <h3 style={{
            margin: 0,
            fontSize: '15px',
            fontWeight: 800,
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
            color: colors.neutral.text,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            lineHeight: 1.2,
          }}>
            {o.brand} {o.model}
          </h3>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            marginTop: '6px',
          }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: colors.neutral.textMuted }}>
              <Calendar size={11} />
              {o.year}
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: colors.neutral.textMuted }}>
              <Gauge size={11} />
              {o.mileage_km.toLocaleString('pt-BR')} km
            </span>
          </div>
        </div>

        {/* Price block */}
        <div>
          <p style={{
            margin: 0,
            fontSize: '10px',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.07em',
            color: colors.neutral.textMuted,
            marginBottom: '2px',
          }}>
            Preço anunciado
          </p>
          <p style={{
            margin: 0,
            fontSize: '22px',
            fontWeight: 800,
            color: colors.neutral.text,
            lineHeight: 1,
          }}>
            {formatBRL(o.listing_price)}
          </p>

          {/* FIPE comparison + discount */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '6px' }}>
            <span style={{ fontSize: '12px', color: colors.neutral.textMuted }}>
              FIPE{' '}
              <span style={{ textDecoration: 'line-through' }}>
                {formatBRL(o.fipe_price)}
              </span>
            </span>
            <DiscountBadge value={o.discount_percent} />
          </div>
        </div>

        {/* CTA — inverted button */}
        <a
          href={o.url}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            borderRadius: '12px',
            background: colors.neutral.text,
            padding: '12px',
            fontSize: '14px',
            fontWeight: 700,
            letterSpacing: '0.02em',
            color: colors.neutral.background,
            transition: 'opacity 0.2s ease',
            cursor: 'pointer',
            textDecoration: 'none',
          }}
          onMouseOver={(e) => e.currentTarget.style.opacity = '0.85'}
          onMouseOut={(e) => e.currentTarget.style.opacity = '1'}
        >
          <ExternalLink size={14} />
          Ver Anúncio
        </a>
      </div>
    </div>
  )
}

export function OpportunityTable({ opportunities }: { opportunities: Opportunity[] }) {
  const { searchQuery, minScore, minDiscount, sortBy, sortOrder} = useFilterStore()
  const { theme } = useTheme()
  const { glass, colors } = theme

  const filtered = opportunities
    .filter((o) => {
      if (searchQuery) {
        const q = searchQuery.toLowerCase()
        const txt = `${o.brand} ${o.model}`.toLowerCase()
        if (!txt.includes(q)) return false
      }
      return o.score >= minScore && o.discount_percent >= minDiscount
    })
    .sort((a, b) => {
      const mult = sortOrder === 'asc' ? 1 : -1
      return (a[sortBy] - b[sortBy]) * mult
    })

  if (filtered.length === 0) {
    return (
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
        textAlign: 'center'
      }}>
        <SearchX size={48} strokeWidth={1} style={{ color: colors.neutral.textSecondary, marginBottom: '16px' }} />
        <p style={{ fontSize: '14px', fontWeight: '500', color: colors.neutral.textSecondary }}>
          Nenhuma oportunidade corresponde aos seus filtros
        </p>
        <p style={{ fontSize: '12px', color: colors.neutral.textSecondary, marginTop: '4px' }}>
          Tente ajustar seus critérios de busca ou limpar os filtros
        </p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 md:gap-5">
      {filtered.map((o) => (
        <OpportunityCard key={o.id} opportunity={o} />
      ))}
    </div>
  )
}
