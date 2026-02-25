import type { ThemeConfig } from '@packages/design-system-engine';
import designTokens from './theme.json';

/**
 * FIPE Hunter theme configuration.
 *
 * Design tokens (hue, chroma, colorScheme, glassBorderRadius) live in theme.json.
 * To update: export a new theme.json from Storybook and replace the file.
 *
 * Only appName is app-specific — it controls the localStorage key for theme persistence.
 */
export const themeConfig: ThemeConfig = {
  ...designTokens,
  appName: 'fipe-hunter',
};
