import { useState } from 'react'
import { Search, Loader2, AlertCircle } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import {
  searchVehicle,
  fetchFipeModels,
  fetchFipeVersions,
  type SearchRequest,
  type SearchResponse,
  type FipeModel,
  type FipeVersion,
} from '../services/api'
import { useTheme } from '@packages/design-system-engine'
import { BrandPicker, ModelPicker, YearPicker, type Brand } from '@packages/automotive-ui'

const BRANDS: Brand[] = [
  { id: 'Chevrolet', name: 'Chevrolet' },
  { id: 'Fiat', name: 'Fiat' },
  { id: 'Ford', name: 'Ford' },
  { id: 'Honda', name: 'Honda' },
  { id: 'Hyundai', name: 'Hyundai' },
  { id: 'Jeep', name: 'Jeep' },
  { id: 'Mitsubishi', name: 'Mitsubishi' },
  { id: 'Nissan', name: 'Nissan' },
  { id: 'Renault', name: 'Renault' },
  { id: 'Toyota', name: 'Toyota' },
  { id: 'Volkswagen', name: 'Volkswagen' },
  { id: 'Peugeot', name: 'Peugeot' },
  { id: 'Citroën', name: 'Citroën' },
  { id: 'Kia', name: 'Kia' },
  { id: 'BMW', name: 'BMW' },
  { id: 'Mercedes-Benz', name: 'Mercedes-Benz' },
  { id: 'Audi', name: 'Audi' },
  { id: 'Land Rover', name: 'Land Rover' },
]

const YEARS = Array.from({ length: 37 }, (_, i) => 2026 - i)

/** Extract base model name — first word only (e.g. "Civic Sed. LXL" → "Civic"). */
function extractBaseModel(fipeName: string): string {
  return fipeName.split(' ')[0]
}

interface SearchFormProps {
  onResults: (response: SearchResponse) => void
  onSearchStart?: () => void
  onSearchError?: () => void
  onSearchParams?: (params: SearchRequest) => void
}

export function SearchForm({ onResults, onSearchStart, onSearchError, onSearchParams }: SearchFormProps) {
  const { theme } = useTheme()
  const { colors, glass, spacing, borders, transitions } = theme

  // Step 1 — Marca
  const [brand, setBrand] = useState('')
  const [fipeBrandId, setFipeBrandId] = useState('')
  const [fipeModels, setFipeModels] = useState<FipeModel[]>([])
  const [modelsLoading, setModelsLoading] = useState(false)
  const [modelsError, setModelsError] = useState<string | null>(null)

  // Step 2 — Modelo
  const [modelBase, setModelBase] = useState('')

  // Step 3 — Ano
  const [year, setYear] = useState<number | null>(null)

  // Step 4 — Versão (filtered by year when set)
  const [filteredVersions, setFilteredVersions] = useState<FipeVersion[]>([])
  const [selectedVersion, setSelectedVersion] = useState<{ id: number; fullName: string; displayName: string; yearCode: string } | null>(null)
  const [versionLoading, setVersionLoading] = useState(false)
  const [versionError, setVersionError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: searchVehicle,
    onSuccess: (data) => onResults(data),
    onError: () => onSearchError?.(),
  })

  // ── Step 1: brand selected → fetch FIPE models
  async function handleBrandChange(brandId: string) {
    setBrand(brandId)
    setFipeBrandId('')
    setFipeModels([])
    setModelBase('')
    setYear(null)
    setFilteredVersions([])
    setSelectedVersion(null)
    setVersionError(null)
    setModelsError(null)

    setModelsLoading(true)
    try {
      const result = await fetchFipeModels(brandId)
      setFipeBrandId(result.brand_id)
      setFipeModels(result.models)
    } catch (err) {
      setModelsError(err instanceof Error ? err.message : 'Falha ao carregar modelos')
    } finally {
      setModelsLoading(false)
    }
  }

  // ── Step 2: modelo selected → if year already set, fetch filtered versions
  async function handleModelBaseChange(base: string) {
    setModelBase(base)
    setSelectedVersion(null)
    setVersionError(null)

    if (year && fipeBrandId && base) {
      await loadFilteredVersions(fipeBrandId, base, year)
    } else {
      setFilteredVersions([])
    }
  }

  // ── Step 3: ano selected → fetch versions filtered by year
  async function handleYearSelect(y: number) {
    setYear(y)
    setSelectedVersion(null)
    setVersionError(null)

    if (fipeBrandId && modelBase) {
      await loadFilteredVersions(fipeBrandId, modelBase, y)
    }
  }

  // ── Shared: fetch versions filtered by year from backend
  async function loadFilteredVersions(brandId: string, base: string, yr: number) {
    setVersionLoading(true)
    setFilteredVersions([])
    try {
      const versions = await fetchFipeVersions(brandId, base, yr)
      setFilteredVersions(versions)
      if (versions.length === 0) {
        setVersionError(`Nenhuma versão disponível em ${yr}`)
      }
    } catch {
      setVersionError('Falha ao buscar versões')
    } finally {
      setVersionLoading(false)
    }
  }

  // ── Step 3: versão selected — year_code comes from the backend
  function handleVersionChange(displayName: string) {
    const found = versionsForPicker.find(v => v.displayName === displayName)
    if (!found) return
    setSelectedVersion(found)
    setVersionError(null)
  }

  // ── Derived: unique base model names
  const baseModelNames: string[] = [...new Set(fipeModels.map(m => extractBaseModel(m.name)))]

  // ── Derived: versions for picker (filtered by year if set, otherwise all from fipeModels)
  const versionsForPicker: { id: number; fullName: string; displayName: string; yearCode: string }[] =
    year && filteredVersions.length > 0
      ? filteredVersions.map(v => ({
          id: v.id,
          fullName: v.name,
          displayName: v.name.replace(new RegExp(`^${modelBase}\\s*`, 'i'), '').trim() || v.name,
          yearCode: v.year_code,
        }))
      : modelBase.length >= 2
        ? fipeModels
            .filter(m => m.name.toLowerCase().startsWith(modelBase.toLowerCase()))
            .map(m => ({
              id: m.id,
              fullName: m.name,
              displayName: m.name.replace(new RegExp(`^${modelBase}\\s*`, 'i'), '').trim() || m.name,
              yearCode: '',
            }))
        : []

  // ── Submit
  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!brand || !modelBase || !selectedVersion) return

    const params: SearchRequest = {
      brand,
      model: modelBase,
      brand_id: fipeBrandId,
      model_id: selectedVersion.id,
      year_code: selectedVersion.yearCode || undefined,
      year: year ?? undefined,
      version: selectedVersion.fullName,
    }

    onSearchParams?.(params)
    onSearchStart?.()
    mutation.mutate(params)
  }

  const canSubmit = !!brand && !!modelBase && !!selectedVersion

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        background: glass.background,
        backdropFilter: `blur(${glass.blur})`,
        borderRadius: glass.borderRadius,
        border: glass.border,
        padding: spacing.lg,
        boxShadow: glass.shadow,
        display: 'flex',
        flexDirection: 'column',
        gap: spacing.lg,
      }}
    >
      {/* Step 1 — Marca */}
      <BrandPicker
        brands={BRANDS}
        value={brand}
        onChange={handleBrandChange}
        title="Marca"
      />

      {modelsLoading && (
        <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm, fontSize: '0.875rem', color: colors.neutral.textMuted }}>
          <Loader2 size={14} className="animate-spin" />
          Carregando modelos...
        </div>
      )}

      {modelsError && (
        <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm, borderRadius: borders.radius.md, background: colors.feedback.errorLight, padding: `${spacing.sm} ${spacing.md}`, fontSize: '0.875rem', color: colors.feedback.error }}>
          <AlertCircle size={14} />
          <span>{modelsError}</span>
        </div>
      )}

      {/* Step 2 — Modelo */}
      <ModelPicker
        models={baseModelNames}
        value={modelBase}
        onChange={handleModelBaseChange}
        title="Modelo"
        placeholder={brand ? 'Selecione um modelo' : 'Selecione uma marca primeiro'}
        disabled={!brand || modelsLoading || baseModelNames.length === 0}
      />

      {/* Step 3 — Ano */}
      <YearPicker
        title="Ano"
        years={YEARS}
        value={year ?? undefined}
        onYearSelect={handleYearSelect}
        defaultExpanded={true}
      />

      {/* Step 3 — Versão */}
      <ModelPicker
        models={versionsForPicker.map(v => v.displayName)}
        value={selectedVersion?.displayName ?? ''}
        onChange={handleVersionChange}
        title={versionLoading ? 'Versão (buscando...)' : 'Versão'}
        placeholder={
          !modelBase ? 'Selecione um modelo primeiro' :
          versionLoading ? 'Carregando versões...' :
          versionsForPicker.length === 0 ? 'Nenhuma versão disponível' :
          'Selecione uma versão'
        }
        disabled={!modelBase || versionsForPicker.length === 0 || versionLoading}
      />

      {versionError && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: spacing.sm,
          borderRadius: borders.radius.md,
          background: colors.feedback.errorLight,
          padding: `${spacing.sm} ${spacing.md}`,
          fontSize: '0.875rem',
          color: colors.feedback.error,
        }}>
          <AlertCircle size={14} />
          <span>{versionError}</span>
        </div>
      )}

      {/* Submit */}
      <button
        type="submit"
        disabled={mutation.isPending || !canSubmit}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: spacing.sm,
          borderRadius: borders.radius.lg,
          background: colors.brand.primary,
          padding: `0.625rem ${spacing.lg}`,
          fontSize: '0.875rem',
          fontWeight: 600,
          color: colors.neutral.textInverse,
          border: 'none',
          cursor: (mutation.isPending || !canSubmit) ? 'not-allowed' : 'pointer',
          opacity: (mutation.isPending || !canSubmit) ? 0.5 : 1,
          boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
          transition: `all ${transitions.duration.fast} ${transitions.timing.ease}`,
          width: '100%',
        }}
        onMouseOver={(e) => {
          if (!mutation.isPending && canSubmit) {
            e.currentTarget.style.background = colors.brand.primaryHover
            e.currentTarget.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }
        }}
        onMouseOut={(e) => {
          e.currentTarget.style.background = colors.brand.primary
          e.currentTarget.style.boxShadow = '0 1px 2px 0 rgba(0, 0, 0, 0.05)'
        }}
      >
        {mutation.isPending ? (
          <>
            <Loader2 size={16} className="animate-spin" />
            Buscando...
          </>
        ) : (
          <>
            <Search size={16} />
            Buscar
          </>
        )}
      </button>

      {mutation.isError && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: spacing.sm,
          borderRadius: borders.radius.md,
          background: colors.feedback.errorLight,
          padding: `${spacing.sm} ${spacing.md}`,
          fontSize: '0.875rem',
          color: colors.feedback.error,
        }}>
          <AlertCircle size={14} />
          <span>{mutation.error.message}</span>
        </div>
      )}
    </form>
  )
}
