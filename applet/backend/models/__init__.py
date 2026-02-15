"""nuGAN Model Architectures

Model architecture from: https://github.com/neeravkaushal/nuGAN
Citation: Kaushal, N. (2025). νGAN: A Deep Learning Emulator for Cosmic Web 
Simulations with Massive Neutrinos [Data set]. Zenodo. 
https://doi.org/10.5281/zenodo.18224158
"""

from .generator import nuGANGenerator

__all__ = ['nuGANGenerator']
