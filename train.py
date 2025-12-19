#!/usr/bin/env python
# coding: utf-8

import os
import time
import random
import numpy as np
import torch
import argparse
from utils import (
    dir_path,
    draw_latent_z,
    HighDimDataset,
    weights_init,
    compute_gradient_penalty,
    spectral_loss_2d,
    get_avg_pk_loss,
    get_runtime,
)
from models import nuGANGenerator as myGenerator
from models import nuGANCritic as myCritic

rseed = 0
random.seed(rseed)
np.random.seed(rseed)
torch.manual_seed(rseed)
torch.cuda.manual_seed_all(rseed)
t1 = time.time()

#################################
# -------Argument parsing--------#
#################################
parser = argparse.ArgumentParser()
parser.add_argument("--ngpu", type=int, default=4, help="number of gpus used")
parser.add_argument(
    "--num_workers", type=int, default=8, help="number of processors used"
)
parser.add_argument(
    "--batch_size",
    type=int,
    default=16,
    help="batch size. try batch_size such that ngpu%batch_size==0",
)
parser.add_argument("--nz", type=int, default=200, help="size of latent vector")
parser.add_argument(
    "--mchn",
    type=int,
    default=2,
    help="size of conditionals to be concatenated to the latent vector",
)
parser.add_argument("--num_epochs", type=int, default=100, help="number of epochs")
parser.add_argument(
    "--num_files",
    type=int,
    default=15000,
    help="number of data files (subboxes) to train on",
)
parser.add_argument(
    "--augmentation",
    type=str,
    default="yes",
    help="augmenting the data files (random rotations and flips)",
)
parser.add_argument(
    "--prior",
    type=str,
    default="gaussian",
    help="probability distribution of the prior latent space",
)
parser.add_argument(
    "--student_df",
    type=int,
    default=10,
    help="degrees of freedom in a student's-T distribution, if student's-T distribution is used as prior",
)
parser.add_argument(
    "--optimizers",
    type=str,
    default="adam",
    help="Optimizers for both generator and discriminator",
)
parser.add_argument("--G_lr", type=float, default=1e-5, help="Generator LR")
parser.add_argument("--G_beta1", type=float, default=0.5, help="Generator beta1")
parser.add_argument("--G_beta2", type=float, default=0.999, help="Generator beta2")
parser.add_argument("--D_lr", type=float, default=1e-5, help="Critic LR")
parser.add_argument("--D_beta1", type=float, default=0.5, help="Critic beta1")
parser.add_argument("--D_beta2", type=float, default=0.999, help="Critic beta2")
parser.add_argument("--GP", type=float, default=10, help="Gradient Penalty factor")
parser.add_argument(
    "--Gsamples",
    type=int,
    default=8,
    help="Number of samples to generate at fixed intervals",
)
parser.add_argument(
    "--G_update_interval",
    type=int,
    default=0,
    help="Update D this times, update G once per this iterations",
)
parser.add_argument(
    "--G_update_freq",
    type=int,
    default=1,
    help="Update G G_update_freq times, update D once per iteration",
)
parser.add_argument(
    "--D_update_threshold",
    type=float,
    default=0.0,
    help="Update D weights only when D(G(z))>this (See DCGAN by Pytorch)",
)
parser.add_argument(
    "--lambda_spec", type=float, default=0.01, help="weight of p(k) loss"
)
parser.add_argument(
    "--spectral_weighting",
    type=str,
    default="uniform",
    help="Type of weighting for different scales in spectral loss function",
)
parser.add_argument(
    "--print_freq",
    type=int,
    default=1000,
    help="printing details after every print_freq",
)
parser.add_argument(
    "--sample_generate_freq",
    type=int,
    default=500,
    help="generating fake samples at fixed noise after every save_freq iterations",
)
parser.add_argument(
    "--loss_save_freq",
    type=int,
    default=200,
    help="saving model after every save_freq iterations",
)
parser.add_argument(
    "--pkloss_save_freq",
    type=int,
    default=500,
    help="saving model on p(k) optimization after each pkloss_save_freq iter",
)
parser.add_argument(
    "--epoch_save",
    type=str,
    default="yes",
    help="saving model after every epoch (consumes more storage space)",
)
parser.add_argument("--scheduling", type=str, default="no", help="decreasing LR")
parser.add_argument(
    "--scheduling_freq",
    type=int,
    default=1000,
    help="decreasing G and D LR after scheduling_freq updates ot the G",
)
parser.add_argument(
    "--lr_multiplier",
    type=float,
    default=0.5,
    help="decreasing the G and D LRs by lr_multiplier times",
)
parser.add_argument(
    "--threshold_save",
    type=str,
    default="yes",
    help="save the model based on loss threshold after every 100 iterations",
)
parser.add_argument(
    "--data_path",
    type=dir_path,
    default="/scratch/gpfs/QUIJOTE/DEV",
    help="path where data is saved",
)
parser.add_argument(
    "--conds_path",
    type=dir_path,
    default="/scratch/gpfs/QUIJOTE/DEV",
    help="path where nu masses are saved",
)
parser.add_argument(
    "--save_path",
    type=dir_path,
    default="/scratch/gpfs/QUIJOTE/DEV2",
    help="path to save results, losses and models",
)
args = parser.parse_args()
print("All arguments parsed")


##########################################
# -----File I/O Operations beforehand-----#
##########################################
if not os.path.exists(args.save_path):
    os.makedirs(args.save_path)
loss_save_path = f"{args.save_path}/saved_losses"
model_save_path = f"{args.save_path}/saved_models"
data_save_path = f"{args.save_path}/saved_data"
if not os.path.exists(loss_save_path):
    os.makedirs(loss_save_path)
if not os.path.exists(model_save_path):
    os.makedirs(model_save_path)
if not os.path.exists(data_save_path):
    os.makedirs(data_save_path)
with open("%s/args.txt" % args.save_path, "w") as wfile:
    wfile.write(str(args))
print("Required directories created")


#########################################
# --Set parameters and get dataloaders---#
#########################################
running_total_G_loss = 1e7
running_total_GD_loss = 1e7
running_total_pk_loss = 1e7
main_collector = torch.device(
    "cuda:0" if (torch.cuda.is_available() and args.ngpu > 0) else "cpu"
)
fixed_noise = draw_latent_z(
    prior=args.prior,
    sample_shape=(args.Gsamples, args.nz, 1, 1),
    device=main_collector,
    df=args.student_df,
)
print("Fixed_noise:", fixed_noise.shape)
params = np.random.choice([0.0, 0.1, 0.4, 0.8, 1.2], args.Gsamples, replace=True)
fixed_params = torch.Tensor.float(torch.from_numpy(params)).view(args.Gsamples, -1)
print(f"Using {args.prior} prior")
print("Hyperparameters set\n")


###########################
# --Dataset & Dataloader--##
###########################
mydataset = HighDimDataset(
    args.data_path, args.conds_path, num_files=args.num_files, aug=args.augmentation
)
if args.augmentation == "yes":
    print("Performing data augmentation")
else:
    print("No augmentation used")
if args.scheduling == "yes":
    print("Scheduling will be used")
else:
    print("No scheduling")
if args.threshold_save == "yes":
    print("Saving model on loss optimization")

mydataloader = torch.utils.data.DataLoader(
    mydataset,
    batch_size=args.batch_size,
    shuffle=True,
    num_workers=args.num_workers,
    drop_last=True,
)
num_batches = len(mydataloader)
print("Dataloaders created")


##########################
# --Instantiate models---##
##########################
Generator = myGenerator(args.nz, args.mchn).to(main_collector)
if (main_collector.type == "cuda") and (args.ngpu > 1):
    Generator = torch.nn.DataParallel(Generator, list(range(args.ngpu)))
Generator.apply(weights_init)

Critic = myCritic(args.mchn).to(main_collector)
if (main_collector.type == "cuda") and (args.ngpu > 1):
    Critic = torch.nn.DataParallel(Critic, list(range(args.ngpu)))
Critic.apply(weights_init)
print("Models instantiated")


############################################
# --Define optimizers and loss containers---#
############################################
if args.optimizers == "rmsprop":
    D_optimizer = torch.optim.RMSprop(Critic.parameters(), lr=args.D_lr)
    G_optimizer = torch.optim.RMSprop(Generator.parameters(), lr=args.G_lr)
elif args.optimizers == "adam":
    D_optimizer = torch.optim.Adam(
        Critic.parameters(), lr=args.D_lr, betas=(args.D_beta1, args.D_beta2)
    )
    G_optimizer = torch.optim.Adam(
        Generator.parameters(), lr=args.G_lr, betas=(args.G_beta1, args.G_beta2)
    )

print("Optimizers defined and loss containers created\n")
print("Total samples :", len(mydataset))
print("Batch size    :", args.batch_size)
print("Total batches :", num_batches)
print("No. of epochs :", args.num_epochs)
print("No. of iterations :", args.num_epochs * num_batches)
print("Saving generated image every %d iterations" % args.sample_generate_freq)
print("Printing training details every %d iterations\n" % args.print_freq)

#########################
##--Define containers--##
#########################
img_list = []
G_losses = []
D_losses_total = []
D_losses_real = []
D_losses_fake = []
pklosses = []

#####################
# --Start training---#
#####################
print("\nStarting Training Loop...\n")
num_iters = 1
G_update_count = 0

for epoch in range(args.num_epochs):
    for i, data in enumerate(mydataloader, 1):
        cbs = data[0].shape[0]
        real_data = data[0].to(main_collector)
        cosmo_params = torch.Tensor.float(data[1])
        cosmo_params = cosmo_params.view(cosmo_params.shape[0], -1).to(main_collector)
        Critic.zero_grad()

        # ----TRAIN D WITH ALL-REAL BATCH
        real_validity = Critic(real_data, cosmo_params, args.mchn).view(-1)
        D_loss_real = torch.mean(real_validity)
        D_losses_real.append(D_loss_real.item())

        # ----TRAIN D WITH ALL-FAKE BATCH
        z = draw_latent_z(
            prior=args.prior,
            sample_shape=(cbs, args.nz, 1, 1),
            device=main_collector,
            df=args.student_df,
        )
        fake_data = Generator(z, cosmo_params, args.mchn)
        fake_validity = Critic(fake_data.detach(), cosmo_params, args.mchn).view(-1)
        D_loss_fake = torch.mean(fake_validity)
        D_losses_fake.append(D_loss_fake.item())

        # ----TOTAL D LOSS
        grad_penalty = compute_gradient_penalty(
            Critic, real_data, cosmo_params, args.mchn, fake_data, main_collector
        )
        if num_iters > 5000:  # Start after 5000 iterations
            spec_loss = spectral_loss_2d(
                real_data, fake_data, weighting=args.spectral_weighting
            )
        else:
            spec_loss = torch.tensor(0.0, device=main_collector)
        D_loss_total = (
            D_loss_fake
            - D_loss_real
            + args.GP * grad_penalty
            + args.lambda_spec * spec_loss
        )
        D_losses_total.append(D_loss_total.item())

        # ----D LOSS BACKPROPAGATION and PARAMETER UPDATION
        D_loss_total.backward()
        torch.nn.utils.clip_grad_norm_(Critic.parameters(), max_norm=1.0)
        if (
            abs(D_loss_fake.item()) >= args.D_update_threshold
            or args.D_update_threshold == 0.0
        ):
            D_optimizer.step()

        # ----Update generator after G_update_interval updates to the discriminator
        if args.G_update_interval != 0:
            if num_iters % args.G_update_interval == 0:
                z = draw_latent_z(
                    prior=args.prior,
                    sample_shape=(cbs, args.nz, 1, 1),
                    device=main_collector,
                    df=args.student_df,
                )
                Generator.zero_grad()
                fake_data = Generator(z, cosmo_params, args.mchn)
                output = Critic(fake_data, cosmo_params, args.mchn).view(-1)
                G_loss = -torch.mean(output)
                G_loss.backward()
                G_optimizer.step()
                G_update_count += 1
                G_losses.append(G_loss.item())

        # ----Update generator G_update_freq times during each discriminator update in a single batch pass
        if args.G_update_freq != 0:
            for _ in range(args.G_update_freq):
                z = draw_latent_z(
                    prior=args.prior,
                    sample_shape=(cbs, args.nz, 1, 1),
                    device=main_collector,
                    df=args.student_df,
                )
                Generator.zero_grad()
                fake_data = Generator(z, cosmo_params, args.mchn)
                output = Critic(fake_data, cosmo_params, args.mchn).view(-1)
                G_loss = -torch.mean(output)
                G_loss.backward()
                G_optimizer.step()
                G_update_count += 1
                G_losses.append(G_loss.item())

        # ----Decrease generator and discriminator LRs after G_scheduling_freq updates to the generator
        if args.scheduling == "yes" and num_iters >= 12000:
            if num_iters % args.scheduling_freq == 0:
                for g in G_optimizer.param_groups:
                    old_lr = g["lr"]
                    new_lr = old_lr * args.lr_multiplier
                    g["lr"] = new_lr
                    print(
                        "count:%d, freq:%d, OLD LR:%f, NEW LR:%f"
                        % (G_update_count, args.scheduling_freq, old_lr, new_lr)
                    )

                for g in D_optimizer.param_groups:
                    old_lr = g["lr"]
                    new_lr = old_lr * args.lr_multiplier
                    g["lr"] = new_lr
                    print(
                        "count:%d, freq:%d, OLD LR:%f, NEW LR:%f"
                        % (G_update_count, args.scheduling_freq, old_lr, new_lr)
                    )

        # ----Save model every loss_save_freq iterations
        if num_iters % args.loss_save_freq == 0:
            # ----Save model on lowest running loss on generator
            new_loss_G = G_loss.item()
            if new_loss_G < running_total_G_loss:
                torch.save(
                    Generator, "{}/best_model_on_G_loss.pt".format(model_save_path)
                )
                running_total_G_loss = new_loss_G

            # ----Save model on lowest running loss on generator+discriminator
            new_loss_GD = D_loss_total.item() + new_loss_G
            if new_loss_GD < running_total_GD_loss:
                torch.save(
                    Generator, "{}/best_model_on_GD_loss.pt".format(model_save_path)
                )
                running_total_GD_loss = new_loss_GD

            np.savetxt(
                "%s/G_losses.csv" % loss_save_path, np.array(G_losses), delimiter=","
            )
            np.savetxt(
                "%s/D_losses.csv" % loss_save_path,
                np.array(D_losses_total),
                delimiter=",",
            )
            np.savetxt(
                "%s/D_losses_real.csv" % loss_save_path,
                np.array(D_losses_real),
                delimiter=",",
            )
            np.savetxt(
                "%s/D_losses_fake.csv" % loss_save_path,
                np.array(D_losses_fake),
                delimiter=",",
            )

        # ----Save model every pkloss_save_freq iterations
        if num_iters % args.pkloss_save_freq == 0:
            z = draw_latent_z(
                prior=args.prior,
                sample_shape=(cbs, args.nz, 1, 1),
                device=main_collector,
                df=args.student_df,
            )
            Generator.zero_grad()
            fake_data = Generator(z, cosmo_params, args.mchn)
            pkloss = get_avg_pk_loss(real_data, fake_data, nbins=100)
            pklosses.append(pkloss)
            # ----Save model on lowest running loss pkloss
            new_loss_pk = pkloss
            if new_loss_pk < running_total_pk_loss:
                torch.save(
                    Generator, "{}/best_model_on_pk_loss.pt".format(model_save_path)
                )
                running_total_pk_loss = new_loss_pk
            np.savetxt(
                "%s/pk_losses.csv" % loss_save_path, np.array(pklosses), delimiter=","
            )

        # ----Save generator output at fixed intervals
        if num_iters % args.sample_generate_freq == 0:
            with torch.no_grad():
                fake_data = (
                    Generator(fixed_noise, fixed_params, args.mchn)
                    .detach()
                    .cpu()
                    .numpy()
                )
            img_list.append(fake_data)
            np.save("%s/img_list.npy" % data_save_path, np.array(img_list))

        # ----PRINTING DETAILS AND SAVING PROGRESS
        if num_iters % args.print_freq == 0:
            try:
                print(
                    f"Epoch: {epoch+1}/{args.num_epochs} \tIteration: {num_iters}/{int(args.num_epochs*num_batches)}"
                )
                print(
                    f"D_loss_fake: {D_loss_fake.item()}, D_loss_real: {D_loss_real.item()}, D_loss_total: {D_loss_total.item()}, G_loss: {G_loss.item()}",
                    "\n\n",
                )
            except Exception as e:
                print(f"Can not print right now! {e}")
                pass

        num_iters += 1

    # ----IN ADDITION, SAVE MODEL AFTER EVERY EPOCH
    if args.epoch_save == "yes":
        torch.save(Generator, "{}/model_epoch_{}.pt".format(model_save_path, epoch))


print(
    "TOTAL TIME TO RUN SCRIPT (minus loading libraries and modules) is ",
    get_runtime(time.time() - t1),
)
