# Backend Documentation

Flask API server for nuGAN model inference with automatic model download from Zenodo.

## Features

- **Automatic Model Download**: Weights automatically downloaded from Zenodo and cached locally
- **Rate Limiting**: Built-in request rate limiting with flask-limiter
- **Colormap Support**: 5 colormaps (AFM Hot, Jet, Viridis, Ocean, Hot)
- **Grid Generation**: Generate comparison grids across multiple neutrino masses
- **Reproducible Seeds**: Optional seed parameter for reproducible generation

## Structure

```
backend/
├── app.py                  # Flask routes with rate limiting
├── requirements.txt        # Python dependencies
├── models/
│   └── nuGANGenerator      # Model architecture
├── services/
│   ├── __init__.py
│   └── model_service.py    # Model service with Zenodo download
└── tests/
    ├── __init__.py
    ├── test_api.py
    └── test_model_service.py
```

## Setup

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Server runs at http://localhost:5000

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 5000 | Server port |
| `FLASK_DEBUG` | false | Enable debug mode |
| `ALLOWED_ORIGINS` | * | CORS allowed origins (comma-separated) |
| `NUGAN_SEED` | 42 | Master seed for reproducibility |

## Requirements

```
flask>=2.0.0
flask-cors>=3.0.10
flask-limiter>=3.0.0
numpy>=1.24.0
torch>=2.0.0
Pillow>=9.0.0
matplotlib>=3.0.0
```

## API Endpoints

### Health Check
```
GET /api/health
Response: { "status": "healthy", "message": "nuGAN API is running" }
```

### Load Model
```
POST /api/model/load
Rate Limit: 10/minute
Body: { "model_path": "optional/path/to/model.pt" }  // Omit to auto-download from Zenodo
Response: { "status": "success", "model_loaded": true }
```

### Model Status
```
GET /api/model/status
Response: { "model_loaded": true, "device": "cuda:0" }
```

### Get Colormaps
```
GET /api/colormaps
Response: { "colormaps": ["viridis", "jet", "hot", "ocean", "afm"] }
```

### Generate Maps (Single Mass)
```
GET/POST /api/generate
Rate Limit: 30/minute

Query params (GET) or JSON body (POST):
{
  "nu_value": 0.4,       // Neutrino mass (0.0-1.2 eV)
  "num_maps": 5,         // Number of maps (1-100)
  "colormap": "afm",     // Colormap to apply
  "seed": 42             // Optional seed for reproducibility
}

Response:
{
  "status": "success",
  "nu_value": 0.4,
  "num_maps": 5,
  "colormap": "afm",
  "seed": 42,
  "images": [{
    "index": 0,
    "image": "data:image/png;base64,...",
    "grayscale": "data:image/png;base64,...",
    "stats": { "min": -0.95, "max": 0.87, "mean": 0.02, "std": 0.34 }
  }]
}
```

### Generate Grid (Multiple Masses)
```
POST /api/generate/grid
Rate Limit: 20/minute

Body:
{
  "nu_values": [0.0, 0.4, 0.8],  // Up to 8 masses
  "num_rows": 3,                  // Samples per mass (1-100)
  "colormap": "viridis",
  "base_seed": 42                 // Optional base seed
}

Response:
{
  "status": "success",
  "nu_values": [0.0, 0.4, 0.8],
  "num_rows": 3,
  "colormap": "viridis",
  "base_seed": 42,
  "grid": [{
    "row_index": 0,
    "seed": 42,
    "maps": [{
      "nu_value": 0.0,
      "image": "data:image/png;base64,...",
      "grayscale": "data:image/png;base64,...",
      "stats": { "min": -0.95, "max": 0.87, "mean": 0.02, "std": 0.34 },
      "seed": 42
    }]
  }]
}
```

### Generate Maps (Raw)
```
POST /api/generate/raw
Body: { "nu_value": 0.4, "num_maps": 5 }
Response: {
  "status": "success",
  "maps": [[[...]]],
  "shape": [256, 256]
}
```

## Model Weights

Model weights are automatically downloaded from Zenodo on first use:

| Property | Value |
|----------|-------|
| Source | [Zenodo Record 18224158](https://zenodo.org/records/18224158) |
| File | `best_model_state_dict.pt` |
| Size | 125.4 MB |
| MD5 | `a5fcc8c5d35e6422fc76a5c04c01ac0d` |
| License | CC-BY 4.0 |

**Cache locations:**
- Windows: `%LOCALAPPDATA%\nugan\cache\`
- Linux/Mac: `~/.cache/nugan/`

## Data Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    Flask App (app.py)                            │
│                    + Rate Limiting (flask-limiter)               │
├──────────────────────────────────────────────────────────────────┤
│  POST /api/model/load                                            │
│       │                                                          │
│       ▼                                                          │
│  ModelService.load_model()                                       │
│       │                                                          │
│       ├─► Check cache for weights                                │
│       ├─► If not cached: download from Zenodo                    │
│       ├─► Verify MD5 checksum                                    │
│       ├─► torch.load(state_dict)                                 │
│       ├─► nuGANGenerator(nz=200, mchn=2)                         │
│       └─► model.eval()                                           │
├──────────────────────────────────────────────────────────────────┤
│  POST /api/generate                                              │
│       │                                                          │
│       ▼                                                          │
│  Validate: nu_value ∈ [0.0, 1.2]                                │
│  Validate: num_maps ∈ [1, 100]                                  │
│       │                                                          │
│       ▼                                                          │
│  ModelService.generate_maps(nu_value, num_maps, seed)            │
│       │                                                          │
│       ├─► Set random seed (if provided)                          │
│       ├─► z = torch.randn(num_maps, 200)  # Latent vectors      │
│       ├─► params = torch.Tensor([nu] * num_maps)                 │
│       ├─► maps = model(z, params, mchn=2)                        │
│       └─► return maps.cpu().numpy()                              │
│       │                                                          │
│       ▼                                                          │
│  Apply colormap (matplotlib)                                     │
│  Convert to Base64 PNG (grayscale + colored)                     │
│       │                                                          │
│       ▼                                                          │
│  JSON Response with images + stats                               │
├──────────────────────────────────────────────────────────────────┤
│  POST /api/generate/grid                                         │
│       │                                                          │
│       ▼                                                          │
│  For each row (sample):                                          │
│    For each nu_value (column):                                   │
│      ├─► Use same seed for row (consistent latent z)            │
│      ├─► Generate single map                                     │
│      └─► Apply colormap                                          │
│       │                                                          │
│       ▼                                                          │
│  JSON Response with grid structure                               │
└──────────────────────────────────────────────────────────────────┘
```

## ModelService Class

| Method | Parameters | Returns |
|--------|------------|---------|
| `load_model` | `model_path: Optional[str]` | `bool` |
| `is_loaded` | - | `bool` |
| `get_device` | - | `str` |
| `draw_latent_z` | `num_samples: int, prior: str` | `torch.Tensor` |
| `generate_maps` | `nu_value: float, num_maps: int, seed: Optional[int]` | `np.ndarray` |
| `generate_single_map` | `nu_value: float, seed: Optional[int]` | `np.ndarray` |
| `get_model_info` | - | `dict` |

## Constants

| Constant | Value |
|----------|-------|
| `NZ` | 200 (latent dimension) |
| `MCHN` | 2 (model channel param) |
| `VALID_NU_VALUES` | [0.0, 0.1, 0.4, 0.8, 1.2] (preset values) |
| `NU_RANGE` | 0.0 - 1.2 eV (model interpolates) |
| `MAX_MAPS` | 100 per request |
| `MAX_MASSES` | 8 (grid mode columns) |

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| Default | 200/day, 50/hour |
| `/api/model/load` | 10/minute |
| `/api/generate` | 30/minute |
| `/api/generate/grid` | 20/minute |

## Running Tests

```bash
# All tests
python -m unittest discover tests -v

# Specific test file
python -m unittest tests.test_model_service -v
python -m unittest tests.test_api -v
```

## Error Handling

| Status | Condition |
|--------|-----------|
| 400 | Model not loaded before generate |
| 400 | Invalid nu_value (outside 0.0-1.2) |
| 400 | Invalid num_maps (outside 1-100) |
| 429 | Rate limit exceeded |
| 500 | Model loading failure |
| 500 | Generation error |

## Citation

```bibtex
@dataset{kaushal_2025_nugan,
  author    = {Kaushal, Neerav},
  title     = {νGAN: A Deep Learning Emulator for Cosmic Web Simulations with Massive Neutrinos},
  year      = {2025},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.18224158}
}
```
