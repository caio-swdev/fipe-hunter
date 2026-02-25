import { Clock, Bell, Store, Target } from 'lucide-react'

function PlaceholderCard({ icon: Icon, title, description }: { icon: typeof Clock; title: string; description: string }) {
  return (
    <div className="rounded-xl border border-dashed border-gray-300 bg-white p-8 text-center">
      <Icon size={32} className="mx-auto mb-3 text-gray-300" />
      <h3 className="text-sm font-medium text-gray-600">{title}</h3>
      <p className="mt-1 text-xs text-gray-400">{description}</p>
    </div>
  )
}

export function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Configurações</h2>
        <p className="text-sm text-gray-500">Configure coleta de dados, alertas e fontes de marketplace</p>
        <span className="mt-1 inline-block rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
          Apenas Admin
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <PlaceholderCard
          icon={Clock}
          title="Agenda de Coleta"
          description="Frequência (horária/diária), alternância de fontes, horário de início, dias da semana"
        />
        <PlaceholderCard
          icon={Bell}
          title="Limites de Alerta"
          description="Telegram pontuação > 75, limiar de pontuação configurável"
        />
        <PlaceholderCard
          icon={Store}
          title="Fontes de Marketplace"
          description="Ativar/desativar OLX, WebMotors com opções por fonte"
        />
        <PlaceholderCard
          icon={Target}
          title="Filtros de Desconto"
          description="Desconto mín/máx %, alerta de suspeita para > 50%"
        />
      </div>
    </div>
  )
}
