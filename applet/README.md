# nuGAN Web Applet

A web-based interface for generating cosmic density maps using the nuGAN (Neutrino GAN) model.

## Features

- Retro notebook style UI with terminal aesthetic
- Interactive neutrino mass slider (0.0, 0.1, 0.4, 0.8, 1.2 eV)
- Batch generation (1, 2, 3, 5, 10, 20 maps)
- Real-time progress feedback
- Generated map statistics display
- Full-screen image viewer with detailed stats (click any image)

## Project Structure

```
web-applet/
├── backend/          → Flask API + PyTorch model service
├── frontend/         → React UI
└── README.md
```


## Quick Start

### 1. One Command (Recommended)

```bash
python run.py --setup           # First time: sets up Python/Node envs
python run.py                   # Start both servers (development)
python run.py --prod            # Start both servers (production)
```

### 2. Manual Setup

```bash
# Backend (Flask dev)
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python app.py

# Backend (Production)
pip install gunicorn python-dotenv
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app

# Frontend (Dev)
cd frontend
npm install
npm run dev

# Frontend (Production)
npm run build
# Serve static: (from project root)
python run.py --prod --frontend-only
```

### Run Script Options

| Command | Description |
|---------|-------------|
| `python run.py` | Start both servers (dev mode) |
| `python run.py --setup` | Setup Python/Node envs |
| `python run.py --backend-only` | Only backend |
| `python run.py --frontend-only` | Only frontend |
| `python run.py --prod` | Production mode (Gunicorn + static build) |

- Backend: http://localhost:5000
- Frontend: http://localhost:3000 (dev) or http://localhost:3000 (static build)

## Environment Configuration

- Backend: `backend/.env.dev` (dev), `backend/.env.prod` (prod)
- Frontend: `frontend/.env.dev` (dev), `frontend/.env.prod` (prod)

Edit these files to set environment variables (ports, debug, API URLs, etc).

## Deployment (Production)

1. Build frontend: `cd frontend && npm run build`
2. Start backend: `gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app`
3. Serve frontend: `python -m http.server 3000 --directory frontend/build`
4. (Recommended) Use Nginx to reverse proxy `/api` to backend and serve static files.

See README in backend/frontend for more details.

## Documentation

| Document | Description |
|----------|-------------|
| [Backend Documentation](backend/README.md) | API endpoints, model service, data flow |
| [Frontend Documentation](frontend/README.md) | React components, styling, state management |

## Data Flow Overview

```
┌─────────────┐    HTTP/JSON    ┌─────────────┐    PyTorch    ┌─────────────┐
│   React UI  │ ◄─────────────► │  Flask API  │ ◄───────────► │  nuGAN Model│
└─────────────┘                 └─────────────┘               └─────────────┘
     │                                │                              │
     │ 1. Load Model Request          │ 2. Initialize Generator      │
     │ 3. Generate Request            │ 4. Forward Pass              │
     │ 5. Base64 Images Response      │ 6. NumPy → PIL → Base64      │
     │ 7. Click Image → ImageViewer   │                              │
     └────────────────────────────────┴──────────────────────────────┘
```

## Current Restrictions

| Restriction | Details |
|-------------|---------|
| Fixed ν values | Only 0.0, 0.1, 0.4, 0.8, 1.2 eV supported |
| Batch limits | Maximum 20 maps per request |
| Single model | No model switching at runtime |
| CPU/GPU | Uses available device, no manual selection |
| No persistence | Generated maps not saved server-side |
| No authentication | Open API, no user management |

## Future Recommendations

### High Priority
- [ ] Add colormap selection for generated images (viridis, plasma, etc.)
- [ ] Implement image download functionality (PNG, NumPy)
- [ ] Add seed input for reproducible generation

### Medium Priority
- [ ] WebSocket for real-time generation progress
- [ ] Gallery view with history of generated maps
- [ ] Side-by-side comparison of different ν values
- [ ] Power spectrum visualization in frontend

### Low Priority
- [ ] Model versioning and selection
- [ ] User authentication and saved sessions
- [ ] Docker containerization
- [ ] Batch export to HDF5/FITS formats

## Dependencies

**Backend**: Flask, Flask-CORS, PyTorch, NumPy, Pillow  
**Frontend**: React 18, Axios

## License

Part of the nuGAN project for neutrino mass cosmological simulations.
