/**
 * Application Configuration
 * Environment-aware settings for the nuGAN web applet
 */

// API Configuration
export const API_CONFIG = {
  // Use relative URL in production (proxied by nginx), localhost in development
  baseUrl: import.meta.env.VITE_API_URL || '/api',
  timeout: 300000, // 5 minutes for large batch generations
};

// Neutrino Mass Values (eV)
export const NU_VALUES = [0.0, 0.1, 0.4, 0.8, 1.2];

// Mass validation
export const MASS_LIMITS = {
  min: 0.0,
  max: 1.2,
  step: 0.01,
};

// Maximum number of masses allowed in grid mode
export const MAX_MASSES = 8;

// Number of maps options
export const NUM_MAPS_OPTIONS = [1, 3, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100];

// Available colormaps
export const COLORMAPS = [
  { id: 'afm', name: 'AFM Hot', color: '#ff6b35' },
  { id: 'jet', name: 'Jet', color: '#00bcd4' },
  { id: 'viridis', name: 'Viridis', color: '#4caf50' },
  { id: 'ocean', name: 'Ocean', color: '#1976d2' },
  { id: 'hot', name: 'Hot', color: '#f44336' },
];

// Default values
export const DEFAULTS = {
  nuValue: 0.0,
  numMaps: 5,
  colormap: 'afm',
  numRows: 3,
  selectedMasses: [0.0, 0.4, 0.8],
};

// Grid display settings
export const GRID_CONFIG = {
  columns: 5,
  gap: 12,
};

// Image viewer settings
export const VIEWER_CONFIG = {
  maxHeightVh: 60,
  shortcuts: {
    close: 'Escape',
    prev: 'ArrowLeft',
    next: 'ArrowRight',
  },
};
