import { NavLink, Outlet } from 'react-router-dom'
import {
  LayoutDashboard,
  Search,
  Heart,
  Activity,
  Menu,
  X,
  Sun,
  Moon,
} from 'lucide-react'
import { useState, useEffect } from 'react'
import { useTheme } from '@packages/design-system-engine'
import { useBreakpoint } from '../hooks/useBreakpoint'
import { useFavorites } from '../hooks/useFavorites'
import { useFavoritesStore } from '../store/favorites'
import { useAdminAuthStore } from '../store/adminAuth'

const publicNavItems = [
  { to: '/app', label: 'Painel', icon: LayoutDashboard },
  { to: '/app/opportunities', label: 'Oportunidades', icon: Search },
  { to: '/app/favorites', label: 'Favoritos', icon: Heart },
]

const adminNavItem = { to: '/app/monitoring', label: 'Monitoramento', icon: Activity }

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { isMobile, isTablet } = useBreakpoint()
  const { data: favoriteData } = useFavorites()
  const setFavoriteIds = useFavoritesStore((s) => s.setFavoriteIds)
  const isAdmin = useAdminAuthStore((s) => !!s.token)
  const navItems = isAdmin ? [...publicNavItems, adminNavItem] : publicNavItems

  useEffect(() => {
    if (favoriteData) {
      setFavoriteIds(favoriteData.map((o) => o.id))
    }
  }, [favoriteData, setFavoriteIds])
  const { theme, themeName, toggleTheme } = useTheme()
  const { colors, glass, spacing, transitions, borders } = theme

  const showSidebar = !isMobile // tablet + desktop get sidebar

  return (
    <div style={{ display: 'flex', height: '100vh', background: glass.gradient }}>
      {/* Overlay for tablet slide-in */}
      {sidebarOpen && isTablet && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 20,
            background: 'rgba(0, 0, 0, 0.3)',
          }}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar — tablet (slide-in) + desktop (static) */}
      {showSidebar && (
        <aside
          style={{
            position: isTablet ? 'fixed' : 'static',
            top: 0,
            bottom: 0,
            left: 0,
            zIndex: 30,
            width: '14rem',
            transform: isTablet ? (sidebarOpen ? 'translateX(0)' : 'translateX(-100%)') : 'none',
            transition: `transform ${transitions.duration.normal} ${transitions.timing.ease}`,
            background: glass.background,
            backdropFilter: `blur(${glass.blur})`,
            border: glass.border,
            borderLeft: 'none',
            borderTop: 'none',
            borderBottom: 'none',
          }}
        >
          <div style={{
            display: 'flex',
            height: '3.5rem',
            alignItems: 'center',
            gap: spacing.sm,
            borderBottom: `1px solid ${colors.neutral.border}`,
            padding: `0 ${spacing.md}`
          }}>
            <span style={{ fontSize: '1.25rem' }}>🏎️</span>
            <span style={{
              fontSize: '0.875rem',
              fontWeight: 600,
              color: colors.brand.primary
            }}>FIPE Hunter</span>
          </div>

          <nav style={{
            marginTop: spacing.md,
            padding: `0 ${spacing.sm}`,
            display: 'flex',
            flexDirection: 'column',
            gap: spacing.xs
          }}>
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setSidebarOpen(false)}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: spacing.sm,
                  borderRadius: borders.radius.md,
                  padding: `${spacing.sm} ${spacing.md}`,
                  fontSize: '0.875rem',
                  transition: `all ${transitions.duration.fast} ${transitions.timing.ease}`,
                  background: isActive ? colors.brand.primaryHover : 'transparent',
                  color: isActive ? colors.neutral.textInverse : colors.neutral.textSecondary,
                  textDecoration: 'none',
                  cursor: 'pointer',
                })}
                onMouseOver={(e) => {
                  const target = e.currentTarget as HTMLAnchorElement
                  if (!target.classList.contains('active')) {
                    target.style.background = colors.neutral.surfaceHover
                    target.style.color = colors.neutral.text
                  }
                }}
                onMouseOut={(e) => {
                  const target = e.currentTarget as HTMLAnchorElement
                  if (!target.classList.contains('active')) {
                    target.style.background = 'transparent'
                    target.style.color = colors.neutral.textSecondary
                  }
                }}
                end={item.to === '/app'}
              >
                <item.icon size={18} />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>
        </aside>
      )}

      {/* Main content */}
      <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
        {/* Top bar */}
        <header style={{
          display: 'flex',
          height: '3.5rem',
          alignItems: 'center',
          gap: spacing.sm,
          borderBottom: `1px solid ${colors.neutral.border}`,
          background: glass.background,
          backdropFilter: `blur(${glass.blur})`,
          padding: `0 ${spacing.md}`,
          flexShrink: 0,
        }}>
          {/* Hamburger — tablet only */}
          {isTablet && (
            <button
              onClick={() => setSidebarOpen((v) => !v)}
              style={{
                borderRadius: borders.radius.md,
                padding: spacing.xs,
                color: colors.neutral.textSecondary,
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          )}

          {/* Mobile logo */}
          {isMobile && (
            <span style={{ fontSize: '1.1rem' }}>🏎️</span>
          )}

          <h1 style={{
            fontSize: isMobile ? '0.8rem' : '0.875rem',
            fontWeight: 500,
            color: colors.neutral.textSecondary,
            flex: 1,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}>
            {isMobile ? 'FIPE Hunter' : 'Buscador de Oportunidades de Veículos'}
          </h1>

          <button
            onClick={toggleTheme}
            title={themeName === 'dark' ? 'Mudar para claro' : 'Mudar para escuro'}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: borders.radius.md,
              padding: spacing.xs,
              color: colors.neutral.textSecondary,
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              transition: `background ${transitions.duration.fast} ${transitions.timing.ease}`,
            }}
            onMouseOver={(e) => e.currentTarget.style.background = colors.neutral.surfaceHover}
            onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
          >
            {themeName === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </header>

        {/* Page content */}
        <main style={{
          flex: 1,
          overflowY: 'auto',
          overflowX: 'hidden',
          padding: isMobile ? spacing.md : spacing.xl,
          paddingBottom: isMobile ? '5rem' : (isTablet ? spacing.xl : spacing.xl),
        }}>
          <div style={{ maxWidth: '80rem', margin: '0 auto' }}>
            <Outlet />
          </div>
        </main>
      </div>

      {/* Bottom tab bar — mobile only */}
      {isMobile && (
        <nav style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          zIndex: 40,
          display: 'flex',
          alignItems: 'stretch',
          background: glass.background,
          backdropFilter: `blur(${glass.blur})`,
          borderTop: glass.border,
          boxShadow: '0 -4px 16px rgba(0,0,0,0.12)',
          height: '4rem',
          paddingBottom: 'env(safe-area-inset-bottom)',
        }}>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/app'}
              style={({ isActive }) => ({
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '2px',
                textDecoration: 'none',
                color: isActive ? colors.brand.primary : colors.neutral.textSecondary,
                transition: `color ${transitions.duration.fast} ${transitions.timing.ease}`,
                paddingTop: '0.25rem',
              })}
            >
              <item.icon size={20} />
              <span style={{ fontSize: '0.625rem', fontWeight: 500 }}>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      )}
    </div>
  )
}
