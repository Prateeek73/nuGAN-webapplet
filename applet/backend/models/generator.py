"""nuGAN Generator Architecture

Source: https://github.com/neeravkaushal/nuGAN/blob/main/models.py
Citation: Kaushal, N. (2025). νGAN: A Deep Learning Emulator for Cosmic Web 
Simulations with Massive Neutrinos [Data set]. Zenodo. 
https://doi.org/10.5281/zenodo.18224158

This is the Generator architecture used in the nuGAN paper for generating
2D cosmological density maps conditioned on neutrino mass parameters.
"""

import torch
import torch.nn as nn


class nuGANGenerator(nn.Module):
    """
    Conditional Generator for nuGAN.
    
    Generates 256x256 2D density maps conditioned on neutrino mass parameters.
    Uses transposed convolutions with batch normalization and ReLU activations.
    
    Args:
        nz (int): Dimension of the latent vector (default: 200)
        MCHN (int): Number of conditioning channels to concatenate (default: 2)
    """
    
    def __init__(self, nz: int, MCHN: int):
        super(nuGANGenerator, self).__init__()
        self.nz = nz
        self.mchn = MCHN
        
        # Linear layer: maps concatenated [params, z, params] to feature map
        self.linear = nn.Linear(MCHN + nz + MCHN, 512 * 16 * 16)
        
        # Deconvolution layers
        self.deconvs = self._main_module(512)
    
    def _main_module(self, inchn: int) -> nn.Sequential:
        """Build the main deconvolution module."""
        return nn.Sequential(
            # 512x16x16 -> 256x32x32
            nn.ConvTranspose2d(inchn, 256, 5, 2, 2, output_padding=1, bias=False),
            nn.BatchNorm2d(256),
            nn.ReLU(True),
            
            # 256x32x32 -> 128x64x64
            nn.ConvTranspose2d(256, 128, 5, 2, 2, output_padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(True),
            
            # 128x64x64 -> 128x64x64 (same spatial size)
            nn.ConvTranspose2d(128, 128, 3, 1, 1, output_padding=0, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(True),
            
            # 128x64x64 -> 64x128x128
            nn.ConvTranspose2d(128, 64, 5, 2, 2, output_padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(True),
            
            # 64x128x128 -> 64x128x128 (same spatial size)
            nn.ConvTranspose2d(64, 64, 3, 1, 1, output_padding=0, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(True),
            
            # 64x128x128 -> 1x256x256
            nn.ConvTranspose2d(64, 1, 5, 2, 2, output_padding=1, bias=False),
            nn.Tanh(),
        )
    
    def forward(self, z: torch.Tensor, params: torch.Tensor, MCHN: int) -> torch.Tensor:
        """
        Generate density maps from latent vectors and conditioning parameters.
        
        Args:
            z: Latent vector of shape (batch_size, nz)
            params: Neutrino mass parameters of shape (batch_size,) or (batch_size, 1)
            MCHN: Number of times to repeat the conditioning parameter
            
        Returns:
            Generated density maps of shape (batch_size, 1, 256, 256)
        """
        if len(z.shape) != 2:
            z = z.squeeze()
        assert len(z.shape) == 2, "check latent vector dimensions"
        
        BS = z.shape[0]
        
        # Repeat params MCHN times and concatenate: [params, z, params]
        params = params.view(-1, 1).repeat(1, MCHN)
        z = torch.cat((params, z, params), dim=1)
        
        # Linear transformation to feature map
        z = self.linear(z)
        z = z.view(BS, 512, 16, 16)
        
        # Apply deconvolutions
        z = self.deconvs(z)
        
        return z
