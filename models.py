import torch


# ---GENERATORS
class nuGANGenerator(torch.nn.Module):
    def main_module(self, inchn):
        return torch.nn.Sequential(
            torch.nn.ConvTranspose2d(
                inchn, 256, 5, 2, 2, output_padding=1, bias=False
            ),  # ---256,4,4
            torch.nn.BatchNorm2d(256),
            torch.nn.ReLU(True),
            torch.nn.ConvTranspose2d(
                256, 128, 5, 2, 2, output_padding=1, bias=False
            ),  # ---128,8,8
            torch.nn.BatchNorm2d(128),
            torch.nn.ReLU(True),
            torch.nn.ConvTranspose2d(
                128, 128, 3, 1, 1, output_padding=0, bias=False
            ),  # ---128,8,8
            torch.nn.BatchNorm2d(128),
            torch.nn.ReLU(True),
            torch.nn.ConvTranspose2d(
                128, 64, 5, 2, 2, output_padding=1, bias=False
            ),  # ---64,16,16
            torch.nn.BatchNorm2d(64),
            torch.nn.ReLU(True),
            torch.nn.ConvTranspose2d(
                64, 64, 3, 1, 1, output_padding=0, bias=False
            ),  # ---64,16,16
            torch.nn.BatchNorm2d(64),
            torch.nn.ReLU(True),
            torch.nn.ConvTranspose2d(
                64, 1, 5, 2, 2, output_padding=1, bias=False
            ),  # ---32,32,32
            torch.nn.Tanh(),
        )

    def __init__(self, nz, MCHN):
        super(nuGANGenerator, self).__init__()
        self.linear = torch.nn.Linear(MCHN + nz + MCHN, 512 * 16 * 16)
        self.deconvs = self.main_module(512)

    def forward(self, z, params, MCHN):
        if len(z.shape) != 2:
            z = z.squeeze()
        assert len(z.shape) == 2, "check latent vector dimensions"
        BS = z.shape[0]
        params = params.view(-1, 1).repeat(1, MCHN)
        z = torch.cat((params, z, params), dim=1)
        z = self.linear(z)
        z = z.view(BS, 512, 16, 16)
        z = self.deconvs(z)
        return z


# ---DISCRIMINATORS
class nuGANCritic(torch.nn.Module):
    def main_module(self, inchn):
        return torch.nn.Sequential(
            torch.nn.Conv2d(inchn, 64, 5, 2, 2, bias=False),  # ---128^2
            torch.nn.BatchNorm2d(64),
            torch.nn.LeakyReLU(0.2),
            torch.nn.Conv2d(64, 128, 5, 2, 2, bias=False),  # ---64^2
            torch.nn.BatchNorm2d(128),
            torch.nn.LeakyReLU(0.2),
            torch.nn.Conv2d(128, 256, 5, 2, 2, bias=False),  # ---32^2
            torch.nn.BatchNorm2d(256),
            torch.nn.LeakyReLU(0.2),
            torch.nn.Conv2d(256, 512, 5, 2, 2, bias=False),  # ---16^2
            torch.nn.BatchNorm2d(512),
            torch.nn.LeakyReLU(0.2),
        )

    def __init__(self, MCHN):
        super(nuGANCritic, self).__init__()
        self.convs = self.main_module(1)
        self.linear = torch.nn.Linear(MCHN + 512 * 16 * 16 + MCHN, 1)

    def forward(self, x, params, MCHN):
        assert len(x.shape) == 4, "check data dimensions"
        BS = x.shape[0]
        x = self.convs(x)
        x = x.view(BS, 512 * 16 * 16)

        params = params.view(-1, 1).repeat(1, MCHN)
        x = torch.cat((params, x, params), dim=1)
        x = self.linear(x)
        return x