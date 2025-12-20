import os
import time
import numpy as np
import torch
import matplotlib.pyplot as plt
from utils import get_stats, draw_latent_z
from models import nuGANGenerator
from collections import OrderedDict
t1 = time.time()

nu = 0.4 #--neutrino mass
num_maps = 75 #--number of 2D maps to generate
save_array = True #--whether to save maps in numpy array
save_plots = True #--whether to save maps in images
num_maps_to_save = 5 #--number of maps to save plots of
map_type = 'hot' #---map type
model_path = "./checkpoints/best_model_on_pk_loss.pt"
save_path = f"./results/generated_maps/nu_{nu}"
os.makedirs(save_path, exist_ok=True)
device = "cuda:0" #---gpu device

model = nuGANGenerator(nz=200, mchn=2).to(device)
state_dict = torch.load(model_path, weights_only=True)
new_state_dict = OrderedDict()
for k, v in state_dict.items():
    new_key = k.replace("module.", "")
    new_state_dict[new_key] = v
model.load_state_dict(new_state_dict)
model.eval()
print("Model loaded")

#----generate maps
params = torch.Tensor(num_maps*[nu])
z = draw_latent_z(prior="gaussian",
                  sample_shape=(len(params),200),
                  device=device,
                  df=None)
gen_maps = model(z, params, 2).cpu().detach().squeeze().numpy()
min, max, mean, std = get_stats(gen_maps[0])
print("Stats of a sample map:", min, max, mean, std)

#----save plots
if save_plots:
    rand_idx = np.random.choice(num_maps+1, size=num_maps_to_save, replace=False)
    for i in range(len(rand_idx)):
        fig, ax = plt.subplots(1,1,figsize=(5,5))
        im = ax.imshow(gen_maps[rand_idx[i]], cmap=map_type, vmin=-1, vmax=1)
        fig.colorbar(im, ax=ax)
        fig.savefig(f"{save_path}/map_{i+1}.png", dpi=100)
    print(f"Maps saved to images")

#----save images
if save_array:
    np.save(f"{save_path}/nu-{nu}__{len(gen_maps)}-maps.npy", gen_maps)
    print("Maps saved to array")