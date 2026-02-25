import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { buildTheme, ThemeProvider } from '@packages/design-system-engine'
import { themeConfig } from './theme.config'
import './index.css'
import App from './App.tsx'

const lightTheme = buildTheme(themeConfig, 'light');
const darkTheme = buildTheme(themeConfig, 'dark');

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider appName="fipe-hunter" lightTheme={lightTheme} darkTheme={darkTheme}>
      <App />
    </ThemeProvider>
  </StrictMode>,
)
