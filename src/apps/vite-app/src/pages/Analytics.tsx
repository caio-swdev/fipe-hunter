import { BarChart3, TrendingUp, Factory, GitCompare } from 'lucide-react'

function PlaceholderCard({ icon: Icon, title, description }: { icon: typeof BarChart3; title: string; description: string }) {
  return (
    <div className="rounded-xl border border-dashed border-gray-300 bg-white p-8 text-center">
      <Icon size={32} className="mx-auto mb-3 text-gray-300" />
      <h3 className="text-sm font-medium text-gray-600">{title}</h3>
      <p className="mt-1 text-xs text-gray-400">{description}</p>
    </div>
  )
}

export function Analytics() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Análises</h2>
        <p className="text-sm text-gray-500">Insights de mercado e tendências de oportunidades</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <PlaceholderCard
          icon={BarChart3}
          title="Distribuição de Descontos"
          description="Histograma mostrando faixas de desconto % (0-10%, 10-20%, etc.)"
        />
        <PlaceholderCard
          icon={TrendingUp}
          title="Tendências de Mercado"
          description="Tendências de 30 dias: desconto médio %, pontuação média, anúncios/dia"
        />
        <PlaceholderCard
          icon={Factory}
          title="Principais Marcas"
          description="Top 10 marcas por oportunidades, pontuação média, desconto médio"
        />
        <PlaceholderCard
          icon={GitCompare}
          title="Comparação de Marketplaces"
          description="OLX vs WebMotors: total de oportunidades, desconto médio, taxa de sucesso"
        />
      </div>
    </div>
  )
}
