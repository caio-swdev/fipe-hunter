import { useTheme } from '@packages/design-system-engine'
import { useAdminHealth } from '../hooks/useAdminHealth'
import type { ServiceHealth } from '../services/api'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts'

function StatusDot({ status }: { status: ServiceHealth['status'] }) {
  const ok = status === 'ok'
  return (
    <span
      style={{
        display: 'inline-block',
        width: '0.625rem',
        height: '0.625rem',
        borderRadius: '50%',
        background: ok ? '#22c55e' : '#ef4444',
        marginRight: '0.375rem',
        flexShrink: 0,
      }}
    />
  )
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  const { theme } = useTheme()
  const { glass, colors, spacing, borders } = theme
  return (
    <div
      style={{
        background: glass.background,
        backdropFilter: `blur(${glass.blur})`,
        border: glass.border,
        borderRadius: borders.radius.lg,
        padding: spacing.lg,
      }}
    >
      <h3
        style={{
          margin: '0 0 0.75rem',
          fontSize: '0.875rem',
          fontWeight: 600,
          color: colors.neutral.text,
        }}
      >
        {title}
      </h3>
      {children}
    </div>
  )
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  const { theme } = useTheme()
  const { colors } = theme
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '0.25rem 0',
        borderBottom: `1px solid ${colors.neutral.border}`,
      }}
    >
      <span style={{ fontSize: '0.8125rem', color: colors.neutral.textSecondary }}>{label}</span>
      <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: colors.neutral.text }}>{value}</span>
    </div>
  )
}

const fmt = (v: string | null | undefined) => v ?? '—'

function streakToTtlLabel(streak: number): string {
  if (streak >= 10) return '30 dias'
  if (streak >= 6)  return '7 dias'
  if (streak >= 3)  return '1 dia'
  if (streak >= 1)  return '6h'
  return '1h'
}

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
}

export function Monitoring() {
  const { theme } = useTheme()
  const { colors } = theme
  const { data, isError, error } = useAdminHealth()

  const svc = data?.services
  const alerts = data?.alerts
  const scraping = data?.scraping
  const cache = data?.cache
  const searchCache = data?.search_cache
  const catalogCache = data?.catalog_cache
  const apiHits = data?.api_hits
  const cacheStats = data?.cache_stats

  
  const hitSeries = (() => {
    const fipeSeries = apiHits?.fipe.series ?? []
    const olxSeries = apiHits?.olx.series ?? []
    const wmSeries = apiHits?.webmotors.series ?? []
    const byHour: Record<string, { fipe: number; olx: number; webmotors: number }> = {}
    fipeSeries.forEach(({ hour, count }) => { byHour[hour] = { ...(byHour[hour] ?? { fipe: 0, olx: 0, webmotors: 0 }), fipe: count } })
    olxSeries.forEach(({ hour, count }) => { byHour[hour] = { ...(byHour[hour] ?? { fipe: 0, olx: 0, webmotors: 0 }), olx: count } })
    wmSeries.forEach(({ hour, count }) => { byHour[hour] = { ...(byHour[hour] ?? { fipe: 0, olx: 0, webmotors: 0 }), webmotors: count } })
    return Object.entries(byHour)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([hour, counts]) => ({ hour: hour.slice(11, 16), ...counts })) 
  })()

  const serviceLabel = (s: ServiceHealth | undefined) =>
    s ? (s.status === 'ok' ? 'Saudável' : 'Rate limited') : '—'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h2 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 600, color: colors.neutral.text }}>
          Monitoramento
        </h2>
        <p style={{ margin: '0.25rem 0 0', fontSize: '0.875rem', color: colors.neutral.textSecondary }}>
          Saúde do sistema, logs de coleta e status dos serviços
        </p>
        <span
          style={{
            marginTop: '0.25rem',
            display: 'inline-block',
            borderRadius: '0.25rem',
            background: '#fef3c7',
            padding: '0.125rem 0.5rem',
            fontSize: '0.75rem',
            fontWeight: 500,
            color: '#92400e',
          }}
        >
          Apenas Admin
        </span>
      </div>

      {isError && (
        <p style={{ color: '#ef4444', fontSize: '0.875rem' }}>
          Erro ao carregar dados: {(error as Error)?.message}
        </p>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(20rem, 1fr))', gap: '1.5rem' }}>
        {}
        <Card title="Saúde das APIs">
          {(['fipe', 'olx', 'webmotors'] as const).map((key) => {
            const s = svc?.[key]
            return (
              <div key={key} style={{ marginBottom: '0.625rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.125rem' }}>
                  {s && <StatusDot status={s.status} />}
                  <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: colors.neutral.text, textTransform: 'uppercase' }}>
                    {key}
                  </span>
                  <span
                    style={{
                      marginLeft: 'auto',
                      fontSize: '0.75rem',
                      color: s?.status === 'rate_limited' ? '#ef4444' : colors.neutral.textSecondary,
                    }}
                  >
                    {serviceLabel(s)}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', paddingLeft: '1rem' }}>
                  <span style={{ fontSize: '0.75rem', color: colors.neutral.textSecondary }}>
                    Último 429: {formatDate(s?.last_429_at ?? null)}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: colors.neutral.textSecondary }}>
                    24h: {s?.count_24h ?? '—'}
                  </span>
                </div>
              </div>
            )
          })}
        </Card>

        {}
        <Card title="Atividade de Coleta">
          <Row label="Oportunidades hoje" value={fmt(scraping?.opportunities_today?.toString())} />
          <Row label="Anúncios coletados hoje" value={fmt(scraping?.listings_today?.toString())} />
        </Card>

        {}
        <Card title="Cache Preços FIPE">
          <Row label="Entradas ativas" value={fmt(cache?.active?.toString())} />
          <Row label="Expiradas" value={fmt(cache?.expired?.toString())} />
          <Row label="Total" value={fmt(cache?.total?.toString())} />
          <Row label="TTL" value="Mensal (ref. FIPE)" />
        </Card>

        {}
        <Card title="Cache Buscas (OLX/WebMotors)">
          <Row label="Entradas ativas" value={fmt(searchCache?.active?.toString())} />
          <Row label="Expiradas" value={fmt(searchCache?.expired?.toString())} />
          <Row label="Total" value={fmt(searchCache?.total?.toString())} />
          <Row label="TTL" value="Fixo 2h" />
        </Card>

        {}
        <Card title="Fila de Mensagens">
          <Row label="Pendentes" value={fmt(alerts?.pending?.toString())} />
          <Row label="Falharam" value={fmt(alerts?.failed?.toString())} />
          <Row label="Enviadas hoje" value={fmt(alerts?.sent_today?.toString())} />
        </Card>

        {}
        <Card title="Cache Catálogo MMY">
          <Row label="Entradas ativas" value={fmt(catalogCache?.active?.toString())} />
          <Row label="Expiradas" value={fmt(catalogCache?.expired?.toString())} />
          <Row
            label="Streak médio"
            value={
              catalogCache
                ? `${catalogCache.avg_streak} (TTL ~${streakToTtlLabel(Math.round(catalogCache.avg_streak))})`
                : '—'
            }
          />
          <Row
            label="Streak máximo"
            value={
              catalogCache
                ? `${catalogCache.max_streak} (TTL ${streakToTtlLabel(catalogCache.max_streak)})`
                : '—'
            }
          />
        </Card>
      </div>

      {}
      <div
        style={{
          background: 'rgba(255,255,255,0.04)',
          border: `1px solid ${colors.neutral.border}`,
          borderRadius: '0.75rem',
          padding: '1.25rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '1.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
          <h3 style={{ margin: 0, fontSize: '0.875rem', fontWeight: 600, color: colors.neutral.text }}>
            Chamadas a APIs Externas — últimas 24h
          </h3>
          {apiHits && (
            <div style={{ display: 'flex', gap: '1rem' }}>
              {(['fipe', 'olx', 'webmotors'] as const).map((key) => (
                <span key={key} style={{ fontSize: '0.75rem', color: colors.neutral.textSecondary }}>
                  {key.toUpperCase()}: <strong style={{ color: colors.neutral.text }}>{apiHits[key].total_24h}</strong>
                </span>
              ))}
            </div>
          )}
          {cacheStats && cacheStats.requests > 0 && (
            <span style={{ fontSize: '0.75rem', color: colors.neutral.textSecondary }}>
              Cache FIPE: <strong style={{ color: colors.neutral.text }}>{cacheStats.hit_rate_pct}%</strong>{' '}
              ({cacheStats.hits}/{cacheStats.requests})
            </span>
          )}
        </div>
        {hitSeries.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={hitSeries} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
              <XAxis
                dataKey="hour"
                tick={{ fontSize: 11, fill: colors.neutral.textSecondary }}
                interval="preserveStartEnd"
              />
              <YAxis
                allowDecimals={false}
                tick={{ fontSize: 11, fill: colors.neutral.textSecondary }}
              />
              <Tooltip
                contentStyle={{
                  background: '#1a1a2e',
                  border: `1px solid ${colors.neutral.border}`,
                  borderRadius: '0.375rem',
                  fontSize: '0.75rem',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '0.75rem' }} />
              <Line type="monotone" dataKey="fipe" stroke="#60a5fa" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="olx" stroke="#34d399" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="webmotors" stroke="#f59e0b" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: 200,
              color: colors.neutral.textSecondary,
              fontSize: '0.875rem',
            }}
          >
            Sem dados — chamadas serão registradas automaticamente
          </div>
        )}
      </div>
    </div>
  )
}
