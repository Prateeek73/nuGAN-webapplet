# Frontend Documentation

React-based UI for nuGAN density map generation with dark cosmic theme.

## Features

- **Single & Grid Mode**: Generate maps for single mass or compare multiple masses
- **Real-time Colormap**: Apply 5 different colormaps with client-side switching
- **Batch Download**: Download all generated maps as ZIP
- **Image Navigation**: Arrow key navigation in full-screen viewer
- **Request Cancellation**: Cancel long-running generation requests
- **Dark Space Theme**: Animated stars and nebula background in output panel
- **Responsive Design**: Adapts to desktop and mobile layouts

## Structure

```
frontend/
├── package.json
├── vite.config.js              # Vite configuration
├── index.html                  # Entry HTML (root level)
└── src/
    ├── main.jsx                    # Entry point
    ├── index.css                   # Global styles + dark theme
    ├── App.jsx                     # Main orchestrator (~300 lines)
    ├── App.css
    ├── config.js                   # Centralized configuration
    ├── hooks/
    │   ├── index.js                # Barrel export
    │   ├── useModelLoader.js       # Model loading logic
    │   ├── useGeneration.js        # Map generation with cancellation
    │   └── useColormap.js          # Client-side colormap switching
    ├── components/
    │   ├── Header.jsx              # App header with title/description
    │   ├── Footer.jsx              # App footer
    │   ├── ImageViewer.jsx         # Full-screen modal with navigation
    │   ├── ErrorBoundary.jsx       # Error boundary wrapper
    │   ├── ControlPanel/
    │   │   ├── index.js            # Barrel export
    │   │   ├── ModelLoader.jsx     # Load model button + status
    │   │   ├── ModeToggle.jsx      # Single/Grid mode switch
    │   │   ├── SingleModeControls.jsx  # Slider + num maps chips
    │   │   ├── GridModeControls.jsx    # Mass selection + rows
    │   │   └── GenerateButton.jsx  # Generate/Cancel buttons
    │   └── OutputPanel/
    │       ├── index.js            # Barrel export
    │       ├── OutputHeader.jsx    # Colormap selector, download btn
    │       ├── SingleModeResults.jsx   # Single mode image grid
    │       ├── GridModeResults.jsx     # Grid mode results display
    │       ├── EmptyState.jsx      # No results placeholder
    │       └── LoadingState.jsx    # Loading spinner
    ├── services/
    │   └── api.js                  # API layer with cancellation
    └── utils/
        └── colormaps.js            # Client-side colormap utilities
```

## Setup

```bash
cd frontend
npm install
npm run dev
```

App runs at http://localhost:3000

### Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server with HMR |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `/api` | Backend API URL |

Create `.env` file for custom settings:
```
VITE_API_URL=http://localhost:5000/api
```

## Dependencies

```json
{
  "react": "^18.3.1",
  "react-dom": "^18.3.1",
  "axios": "^1.7.0",
  "jszip": "^3.10.1",
  "file-saver": "^2.0.5"
}
```

### Dev Dependencies

```json
{
  "vite": "^5.4.0",
  "@vitejs/plugin-react": "^4.2.1"
}
```

## Component Structure

```
App.jsx (Orchestrator)
├─ useModelLoader()      # Hook: model loading state
├─ useGeneration()       # Hook: map generation logic
├─ useColormap()         # Hook: colormap switching
│
├── Header
│   └── Title + Subtitle + Description
├── ControlPanel
│   ├── ModelLoader
│   │   ├── LoadModelButton
│   │   └── StatusIndicator
│   ├── ModeToggle (Single/Grid)
│   ├── SingleModeControls
│   │   ├── NuValueSlider (0.0-1.2 eV)
│   │   └── NumMapsChips
│   ├── GridModeControls
│   │   ├── MassPresetChips
│   │   ├── CustomMassInput
│   │   └── NumRowsSelector
│   ├── SeedInput
│   └── GenerateButton
│       ├── Generate
│       └── Cancel
├── OutputPanel (Dark Space Theme)
│   ├── OutputHeader
│   │   ├── ColormapSelector
│   │   └── DownloadAllButton
│   ├── ErrorBanner
│   ├── LoadingState (spinner)
│   ├── EmptyState (placeholder)
│   ├── SingleModeResults (ImageGrid)
│   └── GridModeResults
│       ├── GridHeader (mass labels)
│       └── GridRows (samples)
├── Footer
└── ImageViewer (Modal)
    ├── NavButtons (prev/next)
    ├── TopInfo (sample/mass)
    ├── FullSizeImage
    ├── StatsPanel
    └── SeedInfo
```

## Custom Hooks

### useModelLoader

Manages model loading state and API interactions.

| Return | Type | Description |
|--------|------|-------------|
| `modelLoaded` | boolean | Model is ready |
| `isLoading` | boolean | Loading in progress |
| `isCheckingModel` | boolean | Checking status on mount |
| `error` | string \| null | Error message |
| `setError` | function | Update error state |
| `handleLoadModel` | function | Trigger model loading |

### useGeneration

Handles map generation with cancellation support.

| Return | Type | Description |
|--------|------|-------------|
| `isGenerating` | boolean | Generation in progress |
| `generatedImages` | array | Single mode results |
| `gridData` | object \| null | Grid mode results |
| `rawImages` | array | Unprocessed single images |
| `rawGridData` | object \| null | Unprocessed grid data |
| `generateTime` | number | Generation duration |
| `usedSeed` | number \| null | Seed used |
| `setGeneratedImages` | function | Update single mode results |
| `setGridData` | function | Update grid mode results |
| `handleGenerate` | function | Start generation |
| `handleCancelGeneration` | function | Cancel request |

### useColormap

Client-side colormap application to generated images.

| Return | Type | Description |
|--------|------|-------------|
| `colormap` | string | Current colormap ID |
| `setColormap` | function | Change colormap |
| `isApplyingColormap` | boolean | Processing in progress |

## Configuration (config.js)

| Export | Type | Description |
|--------|------|-------------|
| `API_CONFIG` | object | `{ baseUrl, timeout }` |
| `NU_VALUES` | array | Preset masses: `[0.0, 0.1, 0.4, 0.8, 1.2]` |
| `MASS_LIMITS` | object | `{ min: 0.0, max: 1.2, step: 0.01 }` |
| `MAX_MASSES` | number | Max grid columns: `8` |
| `NUM_MAPS_OPTIONS` | array | `[1, 3, 5, 10, 20, ..., 100]` |
| `COLORMAPS` | array | 5 colormaps with id/name/color |
| `DEFAULTS` | object | Default values for all inputs |
| `GRID_CONFIG` | object | Grid display settings |
| `VIEWER_CONFIG` | object | Image viewer settings |

## API Service (services/api.js)

| Function | Description |
|----------|-------------|
| `loadModel()` | POST /api/model/load |
| `getModelStatus()` | GET /api/model/status |
| `generateMaps(params)` | POST /api/generate |
| `generateGrid(params)` | POST /api/generate/grid |
| `createCancelToken(key)` | Create AbortController |
| `cancelRequest(key)` | Cancel specific request |
| `cancelAllRequests()` | Cancel all active requests |

## ImageViewer Component

Full-screen modal for viewing generated maps in detail.

### Props

| Prop | Type | Description |
|------|------|-------------|
| `image` | object | Image data with stats, index, nuValue |
| `onClose` | function | Callback to close viewer |
| `onPrev` | function | Navigate to previous image |
| `onNext` | function | Navigate to next image |
| `hasPrev` | boolean | Has previous image |
| `hasNext` | boolean | Has next image |
| `currentIndex` | number | Current image index |
| `totalCount` | number | Total image count |

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Escape` | Close viewer |
| `←` | Previous image |
| `→` | Next image |

## State Management

State is distributed across custom hooks for separation of concerns:

### Model State (useModelLoader)

| State | Type | Description |
|-------|------|-------------|
| `modelLoaded` | boolean | Model load status |
| `isLoading` | boolean | Loading model in progress |
| `isCheckingModel` | boolean | Checking model status |
| `error` | string \| null | Error message |

### Generation State (useGeneration)

| State | Type | Description |
|-------|------|-------------|
| `isGenerating` | boolean | Generation in progress |
| `generatedImages` | array | Generated images (single mode) |
| `gridData` | object | Generated grid data |
| `rawImages` | array | Raw grayscale images (single) |
| `rawGridData` | object | Raw grayscale grid data |
| `generateTime` | number | Last generation time (seconds) |
| `usedSeed` | number | Seed used for generation |

### Colormap State (useColormap)

| State | Type | Description |
|-------|------|-------------|
| `colormap` | string | Selected colormap ID |
| `isApplyingColormap` | boolean | Colormap change in progress |

### Local State (App.jsx)

| State | Type | Description |
|-------|------|-------------|
| `nuValue` | number | Selected neutrino mass (single mode) |
| `numMaps` | number | Number of maps (single mode) |
| `seed` | string | Optional seed value |
| `gridMode` | boolean | Grid mode enabled |
| `selectedMasses` | array | Selected masses (grid mode) |
| `numRows` | number | Samples per mass (grid mode) |
| `selectedImage` | object \| null | Image for full view |

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        App.jsx                              │
│              (Orchestrator - ~300 lines)                    │
├─────────────────────────────────────────────────────────────┤
│  Hooks Initialization                                       │
│       │                                                     │
│       ├─► useModelLoader() → model state                   │
│       ├─► useGeneration() → generation state               │
│       └─► useColormap() → colormap state                   │
├─────────────────────────────────────────────────────────────┤
│  Component Mount                                            │
│       │                                                     │
│       ▼                                                     │
│  useModelLoader.useEffect → getModelStatus()                │
│       └─► Check if model already loaded                    │
├─────────────────────────────────────────────────────────────┤
│  User clicks "Load Model" (ModelLoader component)           │
│       │                                                     │
│       ▼                                                     │
│  handleLoadModel() → loadModel()                            │
│       ├─► setIsLoading(true)                               │
│       ├─► API downloads model from Zenodo (first time)     │
│       └─► setModelLoaded(true)                             │
├─────────────────────────────────────────────────────────────┤
│  User clicks "Generate" (GenerateButton component)          │
│       │                                                     │
│       ▼                                                     │
│  handleGenerate()                                           │
│       ├─► createCancelToken('generate')                    │
│       ├─► setIsGenerating(true)                            │
│       ├─► gridMode ? generateGrid() : generateMaps()       │
│       ├─► setRawImages() or setRawGridData()               │
│       └─► setGenerateTime()                                │
├─────────────────────────────────────────────────────────────┤
│  User changes colormap (OutputHeader component)             │
│       │                                                     │
│       ▼                                                     │
│  useColormap.useEffect → applyColormap()                    │
│       ├─► Takes rawImages/rawGridData                      │
│       └─► Client-side colormap → setGeneratedImages()      │
├─────────────────────────────────────────────────────────────┤
│  User clicks "Download All" (OutputHeader component)        │
│       │                                                     │
│       ▼                                                     │
│  handleDownloadAll()                                        │
│       ├─► Create JSZip archive                             │
│       ├─► Add all images with metadata JSON                │
│       └─► saveAs() to download ZIP                         │
├─────────────────────────────────────────────────────────────┤
│  User clicks image (SingleModeResults/GridModeResults)      │
│       │                                                     │
│       ▼                                                     │
│  setSelectedImage() → <ImageViewer />                       │
│       ├─► Full-size image + stats                          │
│       ├─► Arrow key navigation                             │
│       └─► ESC to close                                     │
└─────────────────────────────────────────────────────────────┘
```

## Styling

### Theme: Dark Space (Output Panel)

| Element | Style |
|---------|-------|
| Background | `#050810` (deep space) |
| Stars | Animated white/blue dots, 60s drift |
| Nebula | Blue gradients, 8s pulse animation |
| Text | `#e0e7ff` (light blue-white) |
| Accents | `rgba(100, 181, 246, *)` (sky blue) |

### Color Palette (CSS Variables)

| Variable | Value | Usage |
|----------|-------|-------|
| `--primary-400` | #60a5fa | Primary blue |
| `--primary-500` | #3b82f6 | Buttons |
| `--primary-600` | #2563eb | Hover states |
| `--primary-700` | #1d4ed8 | Header gradient |
| `--gray-100` | #f1f5f9 | Page background |
| `--gray-800` | #1e293b | Text |
| `--border-radius` | 8px | Rounded corners |

### Colormaps

| ID | Name | Preview Color |
|----|------|---------------|
| `afm` | AFM Hot | #ff6b35 |
| `jet` | Jet | #00bcd4 |
| `viridis` | Viridis | #4caf50 |
| `ocean` | Ocean | #1976d2 |
| `hot` | Hot | #f44336 |

## Valid Input Values

| Input | Range | Notes |
|-------|-------|-------|
| `nuValue` | 0.0 - 1.2 eV | Slider with 0.01 step |
| `numMaps` | 1 - 100 | Preset chips |
| `selectedMasses` | Up to 8 values | Preset + custom |
| `numRows` | 1 - 100 | Samples per mass |
| `seed` | Any integer | Optional, for reproducibility |

## Responsive Design

| Breakpoint | Layout |
|------------|--------|
| Desktop (>900px) | Two-column (control + output side by side) |
| Mobile (<900px) | Single column, stacked layout |

## Error Handling

- **ErrorBoundary**: Catches React errors with fallback UI
- **API errors**: Displayed in error banner with message
- **Validation**: Input validation with error messages
- **Cancellation**: User can cancel long-running requests
