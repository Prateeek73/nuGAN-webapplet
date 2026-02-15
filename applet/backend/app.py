"""
Flask API for nuGAN model inference
"""
import os
import sys
import random
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import numpy as np
import base64
from io import BytesIO

# Add parent directory to path for model imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from services.model_service import ModelService

app = Flask(__name__)

# CORS configuration - restrict origins in production
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*').split(',')
if ALLOWED_ORIGINS == ['*']:
    CORS(app)
else:
    CORS(app, origins=ALLOWED_ORIGINS)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# Global model service instance
model_service = None

# Available colormaps
COLORMAPS = ['viridis', 'jet', 'hot', 'ocean', 'afm']

# Seed for reproducibility
MASTER_SEED = int(os.environ.get('NUGAN_SEED', 42))


def get_model_service():
    """Get or create model service singleton"""
    global model_service
    if model_service is None:
        model_service = ModelService()
    return model_service


def apply_colormap(data, colormap='viridis'):
    """Apply a colormap to normalized data array"""
    try:
        import matplotlib.pyplot as plt
        
        # Normalize data to 0-1
        data_norm = (data - data.min()) / (data.max() - data.min() + 1e-8)
        
        # Get colormap
        cmap_name = colormap.lower()
        if cmap_name == 'afm':
            cmap_name = 'afmhot'
        
        cmap = plt.get_cmap(cmap_name)
        
        # Apply colormap (returns RGBA)
        colored = cmap(data_norm)
        
        # Convert to RGB uint8
        rgb = (colored[:, :, :3] * 255).astype(np.uint8)
        return rgb
        
    except ImportError:
        # Fallback: grayscale
        gray = ((data - data.min()) / (data.max() - data.min() + 1e-8) * 255).astype(np.uint8)
        return np.stack([gray, gray, gray], axis=-1)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'nuGAN API is running'})


@app.route('/api/model/load', methods=['POST'])
@limiter.limit("10 per minute")
def load_model():
    """Load the nuGAN model"""
    try:
        service = get_model_service()
        
        # Get model path from request or use default
        data = request.get_json(silent=True) or {}
        model_path = data.get('model_path', None)
        
        success = service.load_model(model_path)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Model loaded successfully',
                'model_loaded': True
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to load model',
                'model_loaded': False
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'model_loaded': False
        }), 500


@app.route('/api/model/status', methods=['GET'])
def model_status():
    """Check if model is loaded"""
    service = get_model_service()
    return jsonify({
        'model_loaded': service.is_loaded(),
        'device': service.get_device()
    })


@app.route('/api/colormaps', methods=['GET'])
def get_colormaps():
    """Get available colormaps"""
    return jsonify({
        'colormaps': COLORMAPS
    })


@app.route('/api/generate', methods=['GET', 'POST'])
@limiter.limit("30 per minute")
def generate_maps():
    """Generate density maps using the nuGAN model
    
    Accepts either:
    - GET with query params: /api/generate?nu_value=0.4&num_maps=5&colormap=viridis
    - POST with JSON body: {"nu_value": 0.4, "num_maps": 5, "colormap": "viridis", "seed": 42}
    """
    try:
        service = get_model_service()
        
        if not service.is_loaded():
            return jsonify({
                'status': 'error',
                'message': 'Model not loaded. Please load the model first.'
            }), 400
        
        # Get parameters from query string (GET) or JSON body (POST)
        if request.method == 'GET':
            nu_value = float(request.args.get('nu_value', 0.0))
            num_maps = int(request.args.get('num_maps', 1))
            colormap = request.args.get('colormap', 'viridis')
            seed = request.args.get('seed')
            seed = int(seed) if seed else None
        else:
            data = request.get_json() or {}
            nu_value = float(data.get('nu_value', 0.0))
            num_maps = int(data.get('num_maps', 1))
            colormap = data.get('colormap', 'viridis')
            seed = data.get('seed')
        
        # Validate nu_value (allow any value 0.0-1.2)
        nu_value = round(nu_value, 2)
        if nu_value < 0.0 or nu_value > 1.2:
            nu_value = max(0.0, min(1.2, nu_value))
        
        # Validate num_maps (allow 1-100)
        num_maps = max(1, min(100, num_maps))
        
        # Auto-generate seed if not provided (reproducible with master seed)
        if seed is None:
            # Use master seed combined with nu_value for reproducibility
            rng = random.Random(MASTER_SEED + int(nu_value * 10000))
            seed = rng.randint(0, 999999)
        
        # Validate colormap (normalize to lowercase)
        colormap = colormap.lower()
        if colormap not in COLORMAPS:
            colormap = 'viridis'
        
        # Generate maps
        maps = service.generate_maps(nu_value, num_maps, seed=seed)
        
        # Convert to base64 encoded images with colormap
        images = []
        from PIL import Image
        
        for i, map_data in enumerate(maps):
            # Normalize data to 0-255 for grayscale
            data_norm = (map_data - map_data.min()) / (map_data.max() - map_data.min() + 1e-8)
            gray_data = (data_norm * 255).astype(np.uint8)
            
            # Create grayscale image
            gray_img = Image.fromarray(gray_data, mode='L')
            gray_buffer = BytesIO()
            gray_img.save(gray_buffer, format='PNG')
            gray_base64 = base64.b64encode(gray_buffer.getvalue()).decode('utf-8')
            
            # Apply colormap for initial display
            rgb_data = apply_colormap(map_data, colormap)
            
            # Convert to PIL Image
            img = Image.fromarray(rgb_data, mode='RGB')
            
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            images.append({
                'index': i,
                'image': f'data:image/png;base64,{img_base64}',
                'grayscale': f'data:image/png;base64,{gray_base64}',
                'stats': {
                    'min': float(map_data.min()),
                    'max': float(map_data.max()),
                    'mean': float(map_data.mean()),
                    'std': float(map_data.std())
                }
            })
        
        return jsonify({
            'status': 'success',
            'nu_value': nu_value,
            'num_maps': num_maps,
            'colormap': colormap,
            'seed': seed,
            'images': images
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/generate/grid', methods=['POST'])
@limiter.limit("20 per minute")
def generate_grid():
    """Generate a grid of density maps for multiple masses
    
    POST body: {
        "nu_values": [0.0, 0.4, 0.8],
        "num_rows": 3,
        "colormap": "viridis",
        "base_seed": 42
    }
    
    Returns a grid where:
    - Columns = different nu values (masses)
    - Rows = different samples
    - Same seed used for each row across columns (same latent z)
    """
    try:
        service = get_model_service()
        
        if not service.is_loaded():
            return jsonify({
                'status': 'error',
                'message': 'Model not loaded. Please load the model first.'
            }), 400
        
        data = request.get_json() or {}
        nu_values = data.get('nu_values', [0.0, 0.4, 0.8])
        num_rows = int(data.get('num_rows', 3))
        colormap = data.get('colormap', 'viridis')
        base_seed = data.get('base_seed')
        
        # Validate nu_values (allow any value 0.0-1.2)
        nu_values = [round(max(0.0, min(1.2, v)), 2) for v in nu_values]
        num_rows = max(1, min(100, num_rows))
        
        # Auto-generate base_seed if not provided
        if base_seed is None:
            import random
            base_seed = random.randint(1, 99999)
        
        # Validate colormap (normalize to lowercase)
        colormap = colormap.lower()
        if colormap not in COLORMAPS:
            colormap = 'viridis'
        
        from PIL import Image
        
        # Generate grid: each row uses same seed across different nu values
        grid = []
        for row_idx in range(num_rows):
            row_seed = (base_seed + row_idx) if base_seed is not None else None
            row_data = []
            
            for nu_val in nu_values:
                # Generate single map with specific seed
                map_data = service.generate_single_map(nu_val, seed=row_seed)
                
                # Normalize data to 0-255 for grayscale
                data_norm = (map_data - map_data.min()) / (map_data.max() - map_data.min() + 1e-8)
                gray_data = (data_norm * 255).astype(np.uint8)
                
                # Create grayscale image
                gray_img = Image.fromarray(gray_data, mode='L')
                gray_buffer = BytesIO()
                gray_img.save(gray_buffer, format='PNG')
                gray_base64 = base64.b64encode(gray_buffer.getvalue()).decode('utf-8')
                
                # Apply colormap
                rgb_data = apply_colormap(map_data, colormap)
                img = Image.fromarray(rgb_data, mode='RGB')
                
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                row_data.append({
                    'nu_value': nu_val,
                    'image': f'data:image/png;base64,{img_base64}',
                    'grayscale': f'data:image/png;base64,{gray_base64}',
                    'stats': {
                        'min': float(map_data.min()),
                        'max': float(map_data.max()),
                        'mean': float(map_data.mean()),
                        'std': float(map_data.std())
                    },
                    'seed': row_seed
                })
            
            grid.append({
                'row_index': row_idx,
                'seed': row_seed,
                'maps': row_data
            })
        
        return jsonify({
            'status': 'success',
            'nu_values': nu_values,
            'num_rows': num_rows,
            'colormap': colormap,
            'base_seed': base_seed,
            'grid': grid
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/generate/raw', methods=['POST'])
def generate_maps_raw():
    """Generate density maps and return raw numpy arrays as JSON"""
    try:
        service = get_model_service()
        
        if not service.is_loaded():
            return jsonify({
                'status': 'error',
                'message': 'Model not loaded. Please load the model first.'
            }), 400
        
        data = request.get_json()
        
        nu_value = float(data.get('nu_value', 0.0))
        num_maps = int(data.get('num_maps', 1))
        
        # Generate maps
        maps = service.generate_maps(nu_value, num_maps)
        
        # Convert to list for JSON serialization
        maps_list = [m.tolist() for m in maps]
        
        return jsonify({
            'status': 'success',
            'nu_value': nu_value,
            'num_maps': num_maps,
            'maps': maps_list,
            'shape': list(maps[0].shape)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    # Use environment variables for production configuration
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
