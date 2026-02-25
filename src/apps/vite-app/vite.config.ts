import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'
import { createRequire } from 'module'

const require = createRequire(import.meta.url)

// Custom plugin: when a file inside /packages/* imports a bare npm module,
// Rollup's node resolution walks up /packages/ looking for node_modules and
// never reaches /frontend/node_modules. This plugin redirects those bare
// imports back to the project root's node_modules.
function resolvePackageDepsFromRoot(rootDir: string) {
  return {
    name: 'resolve-package-deps-from-root',
    resolveId(source: string, importer: string | undefined) {
      if (
        importer &&
        importer.startsWith('/packages/') &&
        !source.startsWith('.') &&
        !source.startsWith('/')
      ) {
        try {
          return require.resolve(source, { paths: [rootDir] })
        } catch {
          return null
        }
      }
    },
  }
}

export default defineConfig({
  plugins: [react(), tailwindcss(), resolvePackageDepsFromRoot(path.resolve(__dirname))],
  resolve: {
    alias: {
      // Monorepo packages resolved as source via Vite aliases.
      // Works both locally (5 levels up to monorepo root) and in Docker
      // (5 levels up from /frontend/ reaches /, so /packages/* is found).
      '@packages/automotive-ui': path.resolve(__dirname, '../../../../../packages/automotive-ui/src'),
      '@packages/design-system-engine': path.resolve(__dirname, '../../../../../packages/design-system-engine'),
      '@packages/ui': path.resolve(__dirname, '../../../../../packages/ui/src'),
      '@': path.resolve(__dirname, '../../../../../packages/ui/src'),
    },
    dedupe: ['react', 'react-dom'],
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
