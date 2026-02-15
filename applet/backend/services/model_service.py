"""Model Service for nuGAN Generator

Downloads and caches pretrained model weights from Zenodo.
Citation: Kaushal, N. (2025). νGAN: A Deep Learning Emulator for Cosmic Web 
Simulations with Massive Neutrinos [Data set]. Zenodo. 
https://doi.org/10.5281/zenodo.18224158
License: CC-BY 4.0
"""
import os
import sys
import hashlib
import urllib.request
import numpy as np
import torch
from collections import OrderedDict
from typing import Optional, List

# Add parent directory to path for local model imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models import nuGANGenerator


# Zenodo download configuration for pretrained weights
ZENODO_RECORD_ID = "18224158"
MODEL_FILENAME = "best_model_state_dict.pt"
MODEL_URL = f"https://zenodo.org/records/{ZENODO_RECORD_ID}/files/{MODEL_FILENAME}"
MODEL_MD5 = "a5fcc8c5d35e6422fc76a5c04c01ac0d"
MODEL_SIZE_MB = 125.4


def get_cache_dir() -> str:
    """Get the cache directory for storing downloaded model weights"""
    # Use standard cache locations
    if os.name == 'nt':  # Windows
        cache_base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        cache_dir = os.path.join(cache_base, 'nugan', 'cache')
    else:  # Linux/Mac
        cache_base = os.environ.get('XDG_CACHE_HOME', os.path.expanduser('~/.cache'))
        cache_dir = os.path.join(cache_base, 'nugan')
    
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def verify_md5(filepath: str, expected_md5: str) -> bool:
    """Verify file integrity using MD5 checksum"""
    md5_hash = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5_hash.update(chunk)
    return md5_hash.hexdigest() == expected_md5


def download_model_weights(force_download: bool = False) -> str:
    """
    Download pretrained model weights from Zenodo if not cached.
    
    Args:
        force_download: If True, download even if file exists in cache
        
    Returns:
        Path to the cached model file
    """
    cache_dir = get_cache_dir()
    cached_path = os.path.join(cache_dir, MODEL_FILENAME)
    
    # Check if already cached and valid
    if not force_download and os.path.exists(cached_path):
        if verify_md5(cached_path, MODEL_MD5):
            print(f"Using cached model weights: {cached_path}")
            return cached_path
        else:
            print("Cached file corrupted, re-downloading...")
    
    # Download from Zenodo
    print(f"Downloading nuGAN model weights ({MODEL_SIZE_MB} MB) from Zenodo...")
    print(f"URL: {MODEL_URL}")
    print(f"This is a one-time download. Weights will be cached at: {cached_path}")
    
    try:
        def _progress_hook(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, downloaded * 100 / total_size)
                print(f"\rDownloading: {percent:.1f}%", end='', flush=True)
        
        urllib.request.urlretrieve(MODEL_URL, cached_path, reporthook=_progress_hook)
        print()  # newline after progress
        
        # Verify download
        if not verify_md5(cached_path, MODEL_MD5):
            os.remove(cached_path)
            raise RuntimeError("Downloaded file failed MD5 verification")
        
        print(f"Model weights downloaded and verified successfully!")
        return cached_path
        
    except Exception as e:
        if os.path.exists(cached_path):
            os.remove(cached_path)
        raise RuntimeError(f"Failed to download model weights: {e}")


class ModelService:
    """Service class for nuGAN model operations
    
    Model weights are automatically downloaded from Zenodo and cached locally.
    """
    
    NZ = 200
    MCHN = 2
    VALID_NU_VALUES: List[float] = [0.0, 0.1, 0.4, 0.8, 1.2]
    VALID_NUM_MAPS: List[int] = [1, 2, 3, 5, 10, 20]
    
    def __init__(self, device: Optional[str] = None):
        self.model: Optional[nuGANGenerator] = None
        self._is_loaded = False
        
        if device is None:
            self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        print(f"ModelService initialized with device: {self.device}")
    
    def load_model(self, model_path: Optional[str] = None) -> bool:
        """Load the nuGAN generator model
        
        If no model_path is provided, weights are automatically downloaded
        from Zenodo and cached locally.
        """
        try:
            if model_path is None:
                # Auto-download from Zenodo if not cached
                model_path = download_model_weights()
            
            self.model = nuGANGenerator(self.NZ, self.MCHN).to(self.device)
            state_dict = torch.load(model_path, weights_only=True, map_location=self.device)
            
            new_state_dict = OrderedDict()
            for k, v in state_dict.items():
                new_state_dict[k.replace("module.", "")] = v
            
            self.model.load_state_dict(new_state_dict)
            self.model.eval()
            self._is_loaded = True
            print(f"Model loaded successfully from: {model_path}")
            return True
            
        except Exception as e:
            print(f"Error loading model: {e}")
            self._is_loaded = False
            self.model = None
            return False
    
    def is_loaded(self) -> bool:
        return self._is_loaded
    
    def get_device(self) -> str:
        return str(self.device)
    
    def draw_latent_z(self, num_samples: int, prior: str = "gaussian") -> torch.Tensor:
        """Draw latent vectors from prior distribution"""
        sample_shape = (num_samples, self.NZ)
        
        if prior == "gaussian":
            z = torch.randn(sample_shape).float().to(self.device)
        elif prior == "uniform":
            z = torch.rand(sample_shape).float().to(self.device)
        elif prior == "beta":
            z = (2 * torch.distributions.Beta(2, 3)
                 .rsample(sample_shape=sample_shape)
                 .float().to(self.device) - 1)
        else:
            raise ValueError(f"Unknown prior: {prior}")
        
        return z
    
    def generate_maps(self, nu_value: float, num_maps: int = 1, seed: Optional[int] = None) -> np.ndarray:
        """Generate density maps for a given neutrino mass parameter"""
        if not self._is_loaded or self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Allow any nu_value in valid range (model interpolates)
        if nu_value < 0.0 or nu_value > 1.2:
            raise ValueError(f"nu_value must be between 0.0 and 1.2, got {nu_value}")
        
        # Allow any num_maps 1-100
        if num_maps < 1 or num_maps > 100:
            raise ValueError(f"num_maps must be between 1 and 100, got {num_maps}")
        
        if seed is not None:
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
            np.random.seed(seed)
        
        with torch.no_grad():
            params = torch.Tensor([nu_value] * num_maps).to(self.device)
            z = self.draw_latent_z(num_maps)
            generated = self.model(z, params, self.MCHN)
            maps = generated.cpu().squeeze(1).numpy()
        
        return maps
    
    def generate_single_map(self, nu_value: float, seed: Optional[int] = None) -> np.ndarray:
        """Generate a single density map"""
        return self.generate_maps(nu_value, num_maps=1, seed=seed)[0]
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model"""
        if not self._is_loaded or self.model is None:
            return {'loaded': False, 'device': str(self.device)}
        
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        
        return {
            'loaded': True,
            'device': str(self.device),
            'nz': self.NZ,
            'mchn': self.MCHN,
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'valid_nu_values': self.VALID_NU_VALUES,
            'valid_num_maps': self.VALID_NUM_MAPS
        }


_model_service_instance: Optional[ModelService] = None


def get_model_service() -> ModelService:
    """Get singleton ModelService instance"""
    global _model_service_instance
    if _model_service_instance is None:
        _model_service_instance = ModelService()
    return _model_service_instance
