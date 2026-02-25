import { useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useTheme } from '@packages/design-system-engine'
import { toShadcnCssVars } from '@packages/design-system-engine/adapters/shadcn'
import { Layout } from './components/Layout'
import { AdminGuard } from './components/AdminGuard'
import { Dashboard } from './pages/Dashboard'
import { Opportunities } from './pages/Opportunities'
import { Favorites } from './pages/Favorites'
import { Monitoring } from './pages/Monitoring'
import { AdminLogin } from './pages/AdminLogin'
import LandingPage from './pages/LandingPage'

/** Injects design-system theme tokens as CSS custom properties so that
 *  shadcn-based components (Combobox, etc.) pick up the correct colors. */
function ThemeSyncer() {
  const { theme } = useTheme()

  useEffect(() => {
    const vars = toShadcnCssVars(theme)
    const root = document.documentElement
    for (const [key, value] of Object.entries(vars)) {
      root.style.setProperty(key, value)
      if (!key.includes('radius')) {
        root.style.setProperty(key.replace(/^--/, '--color-'), value)
      }
    }
  }, [theme])

  return null
}

const queryClient = new QueryClient()

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeSyncer />
      <BrowserRouter>
        <Routes>
          {/* Standalone — no Layout */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/admin/login" element={<AdminLogin />} />

          {/* App shell */}
          <Route path="/app" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="opportunities" element={<Opportunities />} />
            <Route path="favorites" element={<Favorites />} />
            <Route
              path="monitoring"
              element={
                <AdminGuard>
                  <Monitoring />
                </AdminGuard>
              }
            />
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
