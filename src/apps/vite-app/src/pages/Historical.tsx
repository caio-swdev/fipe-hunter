import { Archive, TrendingUp, Download } from 'lucide-react'

function PlaceholderCard({ icon: Icon, title, description }: { icon: typeof Archive; title: string; description: string }) {
  return (
    <div className="rounded-xl border border-dashed border-gray-300 bg-white p-8 text-center">
      <Icon size={32} className="mx-auto mb-3 text-gray-300" />
      <h3 className="text-sm font-medium text-gray-600">{title}</h3>
      <p className="mt-1 text-xs text-gray-400">{description}</p>
    </div>
  )
}

export function Historical() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Histórico</h2>
        <p className="text-sm text-gray-500">Oportunidades arquivadas e evolução de preços</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <PlaceholderCard
          icon={Archive}
          title="Oportunidades Arquivadas"
          description="Itens comprados e arquivados com status, data, observações"
        />
        <PlaceholderCard
          icon={TrendingUp}
          title="Evolução de Preços"
          description="Gráfico de preços de 90 dias para veículos específicos com análise de tendência"
        />
        <PlaceholderCard
          icon={Download}
          title="Exportar Dados Históricos"
          description="CSV, Excel multi-planilha, relatório resumo em PDF"
        />
      </div>
    </div>
  )
}
