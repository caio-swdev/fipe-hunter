import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import type { Opportunity } from '../types/opportunity'
import { useFilterStore } from '../store/filters'
import { useTheme } from '@packages/design-system-engine'

export function DiscountChart({ opportunities }: { opportunities: Opportunity[] }) {
  const { searchQuery, minScore, minDiscount } = useFilterStore()
  const { theme } = useTheme()
  const { colors, glass, spacing } = theme

  const truncate = (str: string, max: number) =>
    str.length > max ? str.slice(0, max - 1) + '…' : str

  const data = opportunities
    .filter((o) => {
      if (searchQuery) {
        const q = searchQuery.toLowerCase()
        if (!`${o.brand} ${o.model}`.toLowerCase().includes(q)) return false
      }
      return o.score >= minScore && o.discount_percent >= minDiscount
    })
    .slice()
    .sort((a, b) => b.discount_percent - a.discount_percent)
    .map((o) => ({
      name: truncate(`${o.brand} ${o.model}`, 20),
      fullName: `${o.brand} ${o.model} ${o.year}`,
      discount: Number(o.discount_percent.toFixed(1)),
      score: o.score,
      year: o.year,
    }))

  const getBarColor = (discount: number) => {
    if (discount >= 20) return colors.feedback.success
    if (discount > 0) return colors.feedback.warning
    return colors.feedback.error
  }

  const lowestDiscount = Math.min(...data.map((d) => d.discount), 0)
  const highestDiscount = Math.max(...data.map((d) => d.discount), 50)
  const domainMin = Math.floor(lowestDiscount / 10) * 10
  const domainMax = Math.ceil(highestDiscount / 10) * 10

  const chartHeight = Math.max(280, data.length * 45)

  return (
    <div style={{
      background: glass.background,
      backdropFilter: glass.blur,
      borderRadius: glass.borderRadius,
      border: glass.border,
      padding: spacing.lg,
      boxShadow: glass.shadow,
    }}>
      <h3 style={{
        marginBottom: spacing.md,
        fontSize: '0.875rem',
        fontWeight: 500,
        color: colors.neutral.text
      }}>Desconto por Veículo</h3>
      <ResponsiveContainer width="100%" height={chartHeight}>
        <BarChart data={data} layout="vertical" margin={{ left: 20, right: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={colors.neutral.borderMuted} />
          <XAxis
            type="number"
            domain={[domainMin, domainMax]}
            unit="%"
            fontSize={12}
            tick={{ fill: colors.neutral.textSecondary }}
          />
          <YAxis
            type="category"
            dataKey="name"
            fontSize={11}
            width={140}
            tick={{ fill: colors.neutral.text }}
          />
          <Tooltip
            formatter={(value, _name, props: any) => [
              `${value ?? 0}%`,
              props.payload.fullName,
            ] as any}
            contentStyle={{
              borderRadius: '8px',
              border: `1px solid ${colors.neutral.border}`,
              background: glass.background,
              backdropFilter: glass.blur,
              color: colors.neutral.text
            }}
          />
          <Bar dataKey="discount" radius={[0, 4, 4, 0]}>
            {data.map((entry, i) => (
              <Cell key={i} fill={getBarColor(entry.discount)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
