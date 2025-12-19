import os, sys
from libraries import *

class HighDimDataset(Dataset):
    
    def __init__(self, data_path, conds_path, num_files=False, aug='yes'):
        self.aug = aug
        self.num_files  = num_files
        self.data_path  = data_path
        self.conds_path = conds_path
        self.data_box   = np.load(self.data_path)
        self.conds_box  = np.load(self.conds_path)

        rand_idx = np.arange(0,len(self.data_box),1)
        np.random.shuffle(rand_idx)
        self.data_box  = self.data_box[rand_idx]
        self.conds_box = self.conds_box[rand_idx]

        if self.num_files:
            self.data_box  = self.data_box[:self.num_files]
            self.conds_box = self.conds_box[:self.num_files]
        
    
    def __getitem__(self, index):
        dat, cond = self.data_box[index], self.conds_box[index]

        if self.aug=='yes':
            seed = np.random.rand()
            if 0.25 < seed < 0.5:
                dat = dat[:,::-1]
            elif 0.50 < seed < 0.75:
                dat = dat[::-1,:]
            elif 0.75 < seed < 1.0:
                dat = dat[::-1,::-1]
            
            if seed<0.5:
                shift_y = np.random.randint(0, dat.shape[0])
                shift_x = np.random.randint(0, dat.shape[1])
                dat = np.roll(dat, shift_y, axis=0)
                dat = np.roll(dat, shift_x, axis=1)
            
        dat = dat[np.newaxis,:,:] #----In shape 1,256,256
        return torch.from_numpy(dat.copy()), torch.from_numpy(np.array([cond]).copy())
            
    def __len__(self):
        return len(self.data_box)

def draw_latent_z(prior='gaussian', sample_shape=(100,100), device='cpu', df=None):
    if prior=='studentT':
        z = torch.distributions.StudentT(df=df,loc=0.0,scale=1.0).rsample(sample_shape=sample_shape).float().to(device)
    elif prior=='uniform':
        z = torch.rand(sample_shape).float().to(device)
    elif prior=='gaussian':
        z = torch.randn(sample_shape).float().to(device)
    elif prior=='beta':
        z = 2*torch.distributions.Beta(2,3).rsample(sample_shape=(sample_shape)).float().to(device)-1
    return z
    
def dir_path(path):
    return path

def weights_init(m):
    classname = m.__class__.__name__
    if classname.find('Conv') != -1:
        nn.init.normal_(m.weight.data, 0.0, 0.02)
    elif classname.find('BatchNorm') != -1:
        nn.init.normal_(m.weight.data, 1.0, 0.02)
        nn.init.constant_(m.bias.data, 0.0)
        
def get_runtime(t):
    t = round(t)
    values = []
    if divmod(t,3600)[0]==0: #if no hours in time
        if divmod(t,60)[0]==0: #if no minutes 
            secs = divmod(t,60)[1] #get seconds only
            values.append(secs)
        else:
            mins, secs = divmod(t,60) #else get minutes and seconds
            values.append(mins)
            values.append(secs)
    else:
        hours, mins_secs = divmod(t,3600) #else get hours and minutes_seconds together
        mins, secs = divmod(mins_secs, 60) #get minutes and seconds separately
        values.append(hours)
        values.append(mins)
        values.append(secs)
    
    if len(values)==1: #if only seconds
        msg = "{} secs".format(values[0])
    elif len(values)==2: #if mins and secs
        msg = "{} mins, {} secs".format(values[0],values[1])
    else: #if hours, mins and secs
        msg = "{} hours, {} mins, {} secs".format(values[0], values[1], values[2])
    
    return msg

def compute_gradient_penalty(D, real_samples, params, mchn, fake_samples, device):
    
    """Calculates the gradient penalty loss for WGAN GP"""
    
    # Random weight term for interpolation between real and fake samples
    if real_samples.ndim==5:
        alpha = torch.Tensor(np.random.random((real_samples.size(0), 1, 1, 1, 1))).to(device)#; print(alpha.shape)
    elif real_samples.ndim==4:
        alpha = torch.Tensor(np.random.random((real_samples.size(0), 1, 1, 1))).to(device)#; print(alpha.shape)
    #print('alpha       :', alpha.shape)#.get_device())
    #print('real_samples:', real_samples.shape)#.get_device())
    #print('fake_samples:', fake_samples.shape)#.get_device())
    #print('params      :', params.shape)#.get_device())
    
    # Get random interpolation between real and fake samples
    interpolates = (alpha * real_samples + ((1 - alpha) * fake_samples)).requires_grad_(True)#.to(collector_device)
    d_interpolates = D(interpolates, params, mchn)
    d_interpolates = d_interpolates.view(real_samples.shape[0],-1) #----CAUTION HERE#.to(collector_device)
    fake = Variable(torch.Tensor(real_samples.shape[0], 1).fill_(1.0), requires_grad=False).to(device)
    
    
    #print('d_int:', d_interpolates.shape)#.get_device())
    #print('inter:', interpolates.shape)#.get_device())
    #print('fake_samples:', fake_samples.shape)#.get_device())
    # Get gradient w.r.t. interpolates

    #d_interpolates = torch.randn(32,1,256,256).to(device)
    
    gradients = torch.autograd.grad(
        outputs=d_interpolates,
        inputs=interpolates,
        grad_outputs=fake,
        create_graph=True,
        retain_graph=True,
        only_inputs=True,
    )[0] #.to(collector_device)
    gradients = gradients.view(gradients.size(0), -1)
    gradient_penalty = ((gradients.norm(2, dim=1) - 1) ** 2).mean()
    return gradient_penalty

def get_stats(x):
    return x.min(), x.max(), x.mean(), x.std()

def get_torch_stats(x):
    return torch.min(x).item(), torch.max(x).item(), torch.mean(x).item(), torch.std(x).item()

def spectral_loss_2d(real, fake, eps=1e-6):
    """
    real, fake: (B, 1, H, W) weighted
    """
    B, C, H, W = real.shape

    Fr = torch.fft.fftn(real, dim=(-2, -1))
    Ff = torch.fft.fftn(fake, dim=(-2, -1))

    Pr = (Fr.real**2 + Fr.imag**2)
    Pf = (Ff.real**2 + Ff.imag**2)

    # build k-grid
    ky = torch.fft.fftfreq(H, d=1.0).to(real.device)
    kx = torch.fft.fftfreq(W, d=1.0).to(real.device)
    ky, kx = torch.meshgrid(ky, kx, indexing="ij")
    k = torch.sqrt(kx**2 + ky**2)  # (H, W)

    # avoid k=0 blow-up; give it same weight as smallest nonzero k
    k[0,0] = k[k>0].min()

    # example weighting ~ 1/k (emphasizes large-scale power)
    w = 1.0 / k
    w = w / w.mean()              # normalize so weights are O(1)
    w = w.unsqueeze(0).unsqueeze(0)   # (1,1,H,W)

    # average over batch
    Pr = Pr.mean(dim=0, keepdim=True)
    Pf = Pf.mean(dim=0, keepdim=True)

    logPr = torch.log(Pr + eps)
    logPf = torch.log(Pf + eps)

    diff = torch.abs(logPf - logPr)
    return (w * diff).mean()

def spectral_loss_2d_robust(real, fake, eps=1e-6, weighting='uniform'):
    """
    Compute weighted spectral loss between real and fake data.
    
    Args:
        real: (B, C, H, W) tensor of real data
        fake: (B, C, H, W) tensor of fake data
        eps: Small constant for numerical stability
        weighting: 'uniform', '1/k', '1/sqrt_k', or 'log'
    
    Returns:
        Scalar loss value
    """
    # Detach fake to prevent gradients to generator when used in D loss
    if fake.requires_grad:
        fake = fake.detach()
    
    B, C, H, W = real.shape

    # Compute FFT
    Fr = torch.fft.fftn(real, dim=(-2, -1))
    Ff = torch.fft.fftn(fake, dim=(-2, -1))

    # Compute power spectra
    Pr = Fr.real**2 + Fr.imag**2
    Pf = Ff.real**2 + Ff.imag**2

    # Build k-grid
    ky = torch.fft.fftfreq(H, d=1.0, device=real.device)
    kx = torch.fft.fftfreq(W, d=1.0, device=real.device)
    ky, kx = torch.meshgrid(ky, kx, indexing="ij")
    k = torch.sqrt(kx**2 + ky**2)

    # Handle k=0 mode
    k_min = k[k > 0].min()
    k = torch.where(k > 0, k, k_min)

    # Apply weighting scheme
    if weighting == 'uniform':
        w = torch.ones_like(k)
    elif weighting == '1/k':
        w = 1.0 / k
    elif weighting == '1/sqrt_k':
        w = 1.0 / torch.sqrt(k)
    elif weighting == 'log':
        w = 1.0 / torch.log(k + 2.0)
    else:
        raise ValueError(f"Unknown weighting: {weighting}")
    
    # Normalize weights
    w = w / w.mean()
    w = w.unsqueeze(0).unsqueeze(0)  # (1, 1, H, W)

    # Average over batch
    Pr = Pr.mean(dim=0, keepdim=True)
    Pf = Pf.mean(dim=0, keepdim=True)

    # Log-space comparison for numerical stability
    logPr = torch.log(Pr + eps)
    logPf = torch.log(Pf + eps)

    # Weighted L1 loss
    diff = torch.abs(logPf - logPr)
    return (w * diff).mean()

def scaling(x):
    return 2*x/(x+4)-1

def inverse_scaling(x):
    return 4*(1+x)/(1-x)

def get_mass_indices(cosmo_params, allowed_masses=[0.0, 0.1, 0.4, 0.8, 1.2]):
    """
    Maps floating-point mass values to integer class indices using scaling & rounding.

    Args:
        cosmo_params (Tensor): [B, 1] or [B] tensor of float values (e.g. [0.4, 0.1])
        allowed_masses (list): List of valid mass values (must be exactly representable)

    Returns:
        Tensor: LongTensor of class indices matching each mass to an index in allowed_masses
    """
    # Build the mapping dict
    mass_value_to_index = {round(m, 3): i for i, m in enumerate(allowed_masses)}

    # Round input values using scaling
    rounded = torch.round(cosmo_params.view(-1) * 10) / 10  # e.g., 0.40000001 → 0.4

    # Map each rounded value to its corresponding index
    index_list = [mass_value_to_index[round(m.item(), 3)] for m in rounded]
    return torch.tensor(index_list, dtype=torch.long, device=cosmo_params.device)

def get_binned_2D(k, pk, nbins):
    kbins = np.linspace(k[0], k[-1], nbins)
    pkbins = np.zeros(nbins)  # Initialize with zeros
    for i in range(len(kbins)-1):
        mask = (k >= kbins[i]) & (k < kbins[i+1])
        if mask.any():
            pkbins[i] = pk[mask].mean()  # Use mean, not sum!
    # Handle last bin
    mask = (k >= kbins[-2]) & (k <= kbins[-1])
    if mask.any():
        pkbins[-1] = pk[mask].mean()
    return pkbins

def get_avg_pk_loss(real, fake, nbins=100):
    real = real.detach().cpu().numpy()
    fake = fake.detach().cpu().numpy()
    tot_pk_loss = 0
    for i in range(real.shape[0]):
        Pk2D = PKL.Pk_plane(real[i].squeeze(), BoxSize=500, MAS='CIC', threads=32, verbose=False)
        pkbins_r = get_binned_2D(Pk2D.k, Pk2D.Pk, nbins)

        Pk2D = PKL.Pk_plane(fake[i].squeeze(), BoxSize=500, MAS='CIC', threads=32, verbose=False)
        pkbins_f = get_binned_2D(Pk2D.k, Pk2D.Pk, nbins)

        tot_pk_loss += np.abs(pkbins_r - pkbins_f).sum()

    val = tot_pk_loss/real.shape[0]
    return val




def get_binned_2D_robust(k, pk, nbins):
    """
    Bin 2D power spectrum into nbins logarithmic bins.
    
    Args:
        k: Array of k values
        pk: Array of P(k) values
        nbins: Number of bins
    
    Returns:
        pkbins: Binned power spectrum (mean in each bin)
    """
    # Use logarithmic binning for better coverage
    k_min = k[k > 0].min()
    k_max = k.max()
    kbins = np.logspace(np.log10(k_min), np.log10(k_max), nbins + 1)
    
    pkbins = np.zeros(nbins)
    
    for i in range(nbins):
        mask = (k >= kbins[i]) & (k < kbins[i+1])
        if mask.any():
            pkbins[i] = pk[mask].mean()  # Use mean, not sum
        else:
            # If bin is empty, interpolate
            pkbins[i] = np.nan
    
    # Fill NaN values with interpolation
    if np.isnan(pkbins).any():
        valid = ~np.isnan(pkbins)
        if valid.any():
            pkbins[~valid] = np.interp(
                np.arange(nbins)[~valid],
                np.arange(nbins)[valid],
                pkbins[valid]
            )
    return pkbins

def get_avg_pk_loss_robust(real, fake, nbins=100, a_scale=4):
    """
    Compute average P(k) loss between real and fake data.
    
    Args:
        real: (B, 1, H, W) tensor in Rodriguez-scaled space [-1, 1]
        fake: (B, 1, H, W) tensor in Rodriguez-scaled space [-1, 1]
        nbins: Number of k-bins
        a_scale: Rodriguez scaling parameter (default=4)
    
    Returns:
        Average P(k) loss across batch
    """
    real = real.detach().cpu().numpy()
    fake = fake.detach().cpu().numpy()
    
    tot_pk_loss = 0
    
    for i in range(real.shape[0]):
        
        # Inverse Rodriguez scaling back to physical units
        real_phys = inverse_scaling(real[i].squeeze())
        fake_phys = inverse_scaling(fake[i].squeeze())
        
        # Ensure non-negative (overdensity should be >= 0)
        real_phys = np.maximum(real_phys, 0)
        fake_phys = np.maximum(fake_phys, 0)
        
        # Convert to density contrast: δ = ρ/ρ̄ - 1
        real_delta = real_phys - 1.0
        fake_delta = fake_phys - 1.0
        
        # Compute P(k) using Pylians
        try:
            Pk2D_real = PKL.Pk_plane(real_delta, BoxSize=500, MAS='CIC', threads=8, verbose=False)
            Pk2D_fake = PKL.Pk_plane(fake_delta, BoxSize=500, MAS='CIC', threads=8, verbose=False)
            
            # Bin the power spectra
            pkbins_r = get_binned_2D_robust(Pk2D_real.k, Pk2D_real.Pk, nbins)
            pkbins_f = get_binned_2D_robust(Pk2D_fake.k, Pk2D_fake.Pk, nbins)
            
            # Compute loss (use relative error to handle different scales)
            pk_loss = np.abs((pkbins_f - pkbins_r) / (pkbins_r + 1e-8)).sum()
            tot_pk_loss += pk_loss
            
        except Exception as e:
            print(f"Warning: P(k) computation failed for sample {i}: {e}")
            continue
    
    val = tot_pk_loss / real.shape[0]
    #chi2_pk   = float(np.mean((Pk2D_real_all - Pk2D_fake_all)**2 / (Pk2D_real**2 + 1e-10)))

    return val

def get_avg_pk_loss_chi2_pk(pk_gen, pk_targ, eps=1e-10):
    """Reduced chi^2 between generated and target P(k)"""
    return float(np.mean((pk_gen - pk_targ)**2 / (pk_targ**2 + eps)))