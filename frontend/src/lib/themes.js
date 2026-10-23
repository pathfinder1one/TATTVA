/**
 * TATTVA Design Tokens — Navy / Purple / Blue / Teal palette
 * Theme switching support with CSS custom properties
 */

/* ============================================================
   THEME DEFINITIONS
   ============================================================ */
export const THEMES = {
  tattva: {
    name: 'TATTVA Core',
    label: 'Deep Obsidian Space',
    // Backgrounds: Clean, deep, pure pitch-black obsidian space (NO murky blue)
    bgDeep: '#030406',
    bgPrimary: '#06070a',
    bgSecondary: '#0c0d12',
    bgCard: 'rgba(12, 13, 17, 0.88)',
    bgCardHover: 'rgba(18, 20, 26, 0.95)',
    bgSurface: 'rgba(10, 11, 15, 0.85)',
    bgOverlay: 'rgba(2, 2, 4, 0.96)',
    bgSidebar: '#030406',

    // Accent colors
    accentPrimary: '#00f0ff',
    accentSecondary: '#38bdf8',
    accentTertiary: '#0ea5e9',
    accentBright: '#7dd3fc',
    accentGlow: 'rgba(0, 240, 255, 0.35)',

    // Status
    statusVerified: '#10b981',
    statusDisputed: '#f43f5e',
    statusPending: '#f59e0b',
    statusUnresolved: '#a855f7',
    statusInfo: '#00f0ff',
    statusActive: '#00f0ff',

    // Text
    textPrimary: '#f8fafc',
    textSecondary: '#94a3b8',
    textMuted: '#64748b',
    textBright: '#ffffff',

    // Borders
    borderPrimary: 'rgba(255, 255, 255, 0.1)',
    borderSecondary: 'rgba(0, 240, 255, 0.25)',
    borderSubtle: 'rgba(255, 255, 255, 0.07)',

    // 3D Core colors (for Three.js)
    core3d: {
      core: '#ffeedd',
      bright: '#ffaa33',
      primary: '#ff5500',
      secondary: '#06070a',
      hudHex: '#00f0ff',
      bgGrad: 'radial-gradient(circle at center, #0a0b10 0%, #030406 70%, #000000 100%)',
    },

    // Gradients
    gradientPrimary: 'linear-gradient(135deg, #00f0ff 0%, #0284c7 100%)',
    gradientCard: 'linear-gradient(180deg, rgba(14, 15, 20, 0.9) 0%, rgba(6, 7, 10, 0.96) 100%)',
    gradientSidebar: 'linear-gradient(180deg, #030406 0%, #000000 100%)',
  },

  sentinel: {
    name: 'Sentinel',
    label: 'Tactical Cyan',
    bgDeep: '#020409',
    bgPrimary: '#061222',
    bgSecondary: '#0a1a30',
    bgCard: 'rgba(10, 26, 48, 0.65)',
    bgCardHover: 'rgba(10, 26, 48, 0.85)',
    bgSurface: 'rgba(6, 18, 34, 0.45)',
    bgOverlay: 'rgba(2, 4, 9, 0.92)',
    bgSidebar: '#040e1c',

    accentPrimary: '#00e5ff',
    accentSecondary: '#0088aa',
    accentTertiary: '#55ffff',
    accentBright: '#c8f8ff',
    accentGlow: '#00e5ff',

    statusVerified: '#22c55e',
    statusDisputed: '#ef4444',
    statusPending: '#f59e0b',
    statusUnresolved: '#a855f7',
    statusInfo: '#00e5ff',
    statusActive: '#00e5ff',

    textPrimary: '#d8f0f8',
    textSecondary: '#8ab8c8',
    textMuted: '#4a7888',
    textBright: '#ffffff',

    borderPrimary: 'rgba(0, 229, 255, 0.3)',
    borderSecondary: 'rgba(0, 136, 170, 0.3)',
    borderSubtle: 'rgba(85, 255, 255, 0.15)',

    core3d: {
      core: '#c8f8ff',
      bright: '#55ffff',
      primary: '#00c8ff',
      secondary: '#0048aa',
      hudHex: '#00e5ff',
      bgGrad: 'radial-gradient(circle at center, #061222 0%, #020409 68%, #000000 100%)',
    },

    gradientPrimary: 'linear-gradient(135deg, #00e5ff 0%, #0088aa 100%)',
    gradientCard: 'linear-gradient(180deg, rgba(10, 26, 48, 0.8) 0%, rgba(4, 14, 28, 0.9) 100%)',
    gradientSidebar: 'linear-gradient(180deg, #040e1c 0%, #020409 100%)',
  },

  overwatch: {
    name: 'Overwatch',
    label: 'Solar Red-Gold',
    bgDeep: '#080200',
    bgPrimary: '#1c0702',
    bgSecondary: '#2a0e05',
    bgCard: 'rgba(42, 14, 5, 0.65)',
    bgCardHover: 'rgba(42, 14, 5, 0.85)',
    bgSurface: 'rgba(28, 7, 2, 0.45)',
    bgOverlay: 'rgba(8, 2, 0, 0.92)',
    bgSidebar: '#120400',

    accentPrimary: '#ff5500',
    accentSecondary: '#991100',
    accentTertiary: '#ffbb22',
    accentBright: '#fff099',
    accentGlow: '#ff5500',

    statusVerified: '#22c55e',
    statusDisputed: '#ef4444',
    statusPending: '#f59e0b',
    statusUnresolved: '#a855f7',
    statusInfo: '#ff5500',
    statusActive: '#ffbb22',

    textPrimary: '#f8e8d8',
    textSecondary: '#c8a888',
    textMuted: '#885848',
    textBright: '#ffffff',

    borderPrimary: 'rgba(255, 85, 0, 0.3)',
    borderSecondary: 'rgba(153, 17, 0, 0.3)',
    borderSubtle: 'rgba(255, 187, 34, 0.15)',

    core3d: {
      core: '#fff099',
      bright: '#ffbb22',
      primary: '#ff3b08',
      secondary: '#991100',
      hudHex: '#ff5500',
      bgGrad: 'radial-gradient(circle at center, #1c0702 0%, #080200 68%, #000000 100%)',
    },

    gradientPrimary: 'linear-gradient(135deg, #ff5500 0%, #991100 100%)',
    gradientCard: 'linear-gradient(180deg, rgba(42, 14, 5, 0.8) 0%, rgba(18, 4, 0, 0.9) 100%)',
    gradientSidebar: 'linear-gradient(180deg, #120400 0%, #080200 100%)',
  },

  stealth: {
    name: 'Aegis Stealth',
    label: 'Deep Emerald',
    bgDeep: '#010704',
    bgPrimary: '#03160d',
    bgSecondary: '#052018',
    bgCard: 'rgba(5, 32, 24, 0.65)',
    bgCardHover: 'rgba(5, 32, 24, 0.85)',
    bgSurface: 'rgba(3, 22, 13, 0.45)',
    bgOverlay: 'rgba(1, 7, 4, 0.92)',
    bgSidebar: '#021008',

    accentPrimary: '#00ff88',
    accentSecondary: '#00522b',
    accentTertiary: '#55ffaa',
    accentBright: '#c8ffee',
    accentGlow: '#00ff88',

    statusVerified: '#22c55e',
    statusDisputed: '#ef4444',
    statusPending: '#f59e0b',
    statusUnresolved: '#a855f7',
    statusInfo: '#00ff88',
    statusActive: '#00ff88',

    textPrimary: '#d8f8e8',
    textSecondary: '#88c8a8',
    textMuted: '#487858',
    textBright: '#ffffff',

    borderPrimary: 'rgba(0, 255, 136, 0.3)',
    borderSecondary: 'rgba(0, 82, 43, 0.3)',
    borderSubtle: 'rgba(85, 255, 170, 0.15)',

    core3d: {
      core: '#c8ffee',
      bright: '#55ffaa',
      primary: '#00d670',
      secondary: '#00522b',
      hudHex: '#00ff88',
      bgGrad: 'radial-gradient(circle at center, #03160d 0%, #010704 68%, #000000 100%)',
    },

    gradientPrimary: 'linear-gradient(135deg, #00ff88 0%, #00522b 100%)',
    gradientCard: 'linear-gradient(180deg, rgba(5, 32, 24, 0.8) 0%, rgba(2, 16, 8, 0.9) 100%)',
    gradientSidebar: 'linear-gradient(180deg, #021008 0%, #010704 100%)',
  },
};

export const DEFAULT_THEME = 'tattva';

// Entity type colors for the graph
export const ENTITY_COLORS = {
  person: '#4a8ed6',
  organization: '#6b4d8e',
  phone: '#22c55e',
  email: '#f59e0b',
  address: '#ef4444',
  vehicle: '#a855f7',
  account: '#00e5ff',
  event: '#ec4899',
  location: '#f97316',
  device: '#8b5cf6',
  other: '#64748b',
};

// Finding type icons/colors
export const FINDING_COLORS = {
  relationship: '#4a8ed6',
  contradiction: '#ef4444',
  pattern: '#a855f7',
  hypothesis: '#f59e0b',
};

// Run status colors
export const RUN_STATUS_COLORS = {
  queued: '#64748b',
  running: '#00e5ff',
  awaiting_review: '#f59e0b',
  completed: '#22c55e',
  completed_with_warnings: '#f59e0b',
  failed: '#ef4444',
  cancel_requested: '#f97316',
  cancelled: '#94a3b8',
};

// Document status colors
export const DOC_STATUS_COLORS = {
  uploaded: '#64748b',
  indexing: '#00e5ff',
  indexed: '#22c55e',
  indexing_failed: '#ef4444',
  quarantined: '#f97316',
};
