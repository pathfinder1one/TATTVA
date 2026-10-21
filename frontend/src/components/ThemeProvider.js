'use client';

import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { THEMES, DEFAULT_THEME } from '@/lib/themes';

const ThemeContext = createContext(null);

export function ThemeProvider({ children }) {
  const [themeKey, setThemeKey] = useState(DEFAULT_THEME);
  const theme = THEMES[themeKey];

  const switchTheme = useCallback((key) => {
    if (THEMES[key]) setThemeKey(key);
  }, []);

  // Sync CSS custom properties with active theme
  useEffect(() => {
    const root = document.documentElement;
    const t = theme;
    root.style.setProperty('--bg-deep', t.bgDeep);
    root.style.setProperty('--bg-primary', t.bgPrimary);
    root.style.setProperty('--bg-secondary', t.bgSecondary);
    root.style.setProperty('--bg-card', t.bgCard);
    root.style.setProperty('--bg-card-hover', t.bgCardHover);
    root.style.setProperty('--bg-surface', t.bgSurface);
    root.style.setProperty('--bg-overlay', t.bgOverlay);
    root.style.setProperty('--bg-sidebar', t.bgSidebar);
    root.style.setProperty('--accent-primary', t.accentPrimary);
    root.style.setProperty('--accent-secondary', t.accentSecondary);
    root.style.setProperty('--accent-tertiary', t.accentTertiary);
    root.style.setProperty('--accent-bright', t.accentBright);
    root.style.setProperty('--accent-glow', t.accentGlow);
    root.style.setProperty('--text-primary', t.textPrimary);
    root.style.setProperty('--text-secondary', t.textSecondary);
    root.style.setProperty('--text-muted', t.textMuted);
    root.style.setProperty('--text-bright', t.textBright);
    root.style.setProperty('--border-primary', t.borderPrimary);
    root.style.setProperty('--border-secondary', t.borderSecondary);
    root.style.setProperty('--border-subtle', t.borderSubtle);
    root.style.setProperty('--gradient-primary', t.gradientPrimary);
    root.style.setProperty('--gradient-card', t.gradientCard);
    root.style.setProperty('--gradient-sidebar', t.gradientSidebar);
    document.body.style.background = t.bgDeep;
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, themeKey, switchTheme, allThemes: THEMES }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}
