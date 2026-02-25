import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTheme } from '@packages/design-system-engine'
import { adminLogin } from '../services/api'
import { useAdminAuthStore } from '../store/adminAuth'

export function AdminLogin() {
  const { theme } = useTheme()
  const { glass, colors, spacing, borders } = theme
  const navigate = useNavigate()
  const setToken = useAdminAuthStore((s) => s.setToken)

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const { access_token } = await adminLogin(username, password)
      setToken(access_token)
      navigate('/app/monitoring', { replace: true })
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: glass.gradient,
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          width: '100%',
          maxWidth: '22rem',
          background: glass.background,
          backdropFilter: `blur(${glass.blur})`,
          border: glass.border,
          borderRadius: borders.radius.lg,
          padding: spacing.xl,
          display: 'flex',
          flexDirection: 'column',
          gap: spacing.md,
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 600, color: colors.neutral.text }}>
            Acesso Admin
          </h1>
          <p style={{ margin: '0.25rem 0 0', fontSize: '0.8125rem', color: colors.neutral.textSecondary }}>
            FIPE Hunter — área restrita
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.sm }}>
          <input
            type="text"
            placeholder="Usuário"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoComplete="username"
            style={inputStyle(colors, borders)}
          />
          <input
            type="password"
            placeholder="Senha"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            style={inputStyle(colors, borders)}
          />
        </div>

        {error && (
          <p style={{ margin: 0, fontSize: '0.8125rem', color: '#ef4444' }}>{error}</p>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{
            padding: `${spacing.sm} ${spacing.md}`,
            borderRadius: borders.radius.md,
            border: 'none',
            background: colors.brand.primary,
            color: colors.neutral.textInverse,
            fontWeight: 600,
            fontSize: '0.875rem',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.7 : 1,
          }}
        >
          {loading ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
    </div>
  )
}

function inputStyle(colors: Record<string, any>, borders: Record<string, any>) {
  return {
    padding: '0.5rem 0.75rem',
    borderRadius: borders.radius.md,
    border: `1px solid ${colors.neutral.border}`,
    background: colors.neutral.surface,
    color: colors.neutral.text,
    fontSize: '0.875rem',
    outline: 'none',
    width: '100%',
    boxSizing: 'border-box' as const,
  }
}
